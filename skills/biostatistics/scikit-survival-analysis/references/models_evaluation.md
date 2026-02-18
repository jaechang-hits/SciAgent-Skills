# Models & Evaluation Reference

Detailed reference for all scikit-survival model families and evaluation metrics. For quick usage patterns, see Core API in the main SKILL.md.

## Cox Proportional Hazards Models

### CoxPHSurvivalAnalysis

Semi-parametric model: h(t|x) = h_0(t) * exp(beta^T x). The key assumption is that the hazard ratio between any two individuals is constant over time (proportional hazards).

**Parameters**:
- `alpha`: Regularization parameter (default: 0, no regularization)
- `ties`: Method for tied event times ("breslow" or "efron"; Efron is more accurate for many ties)
- `n_iter`: Maximum iterations for optimization (default: 100)

**Interpretation**:
- Positive coefficient: increased hazard (shorter survival)
- Negative coefficient: decreased hazard (longer survival)
- Hazard ratio = exp(beta) for one-unit increase in covariate
- Example: beta=0.693 means HR=2.0 (doubles the hazard)

**When to use**: Standard survival analysis with interpretable coefficients, proportional hazards assumption holds, relatively few features compared to sample size.

```python
from sksurv.linear_model import CoxPHSurvivalAnalysis
from sksurv.datasets import load_gbsg2

X, y = load_gbsg2()
cox = CoxPHSurvivalAnalysis(alpha=0.0, ties="breslow")
cox.fit(X, y)

# Coefficients (log hazard ratios)
for name, coef in zip(X.columns, cox.coef_):
    print(f"{name:15s}: coef={coef:+.3f}, HR={np.exp(coef):.3f}")

# Risk scores (linear predictor)
risk_scores = cox.predict(X)

# Survival function per individual
surv_funcs = cox.predict_survival_function(X[:3])
for fn in surv_funcs:
    print(f"Median survival time approx: {fn.x[fn(fn.x) <= 0.5][0]:.0f} days")
```

### CoxnetSurvivalAnalysis

Cox model with elastic net penalty: alpha * (l1_ratio * ||beta||_1 + (1-l1_ratio) * ||beta||_2^2 / 2).

**Penalty types**:
- **Ridge (L2)**: l1_ratio=0 -- shrinks all coefficients; good when all features are relevant
- **Lasso (L1)**: l1_ratio=1.0 -- sets coefficients to zero for feature selection
- **Elastic Net**: 0 < l1_ratio < 1 -- balances selection and grouping

**Parameters**:
- `l1_ratio`: Balance between L1 and L2 (default: 0.5)
- `alpha_min_ratio`: Ratio of smallest to largest alpha in path (default: 0.0001)
- `n_alphas`: Number of alphas along regularization path (default: 100)
- `fit_baseline_model`: Whether to fit unpenalized baseline (default: True)

```python
from sksurv.linear_model import CoxnetSurvivalAnalysis
import numpy as np

# Elastic net with cross-validation for alpha selection
coxnet = CoxnetSurvivalAnalysis(l1_ratio=0.5, alpha_min_ratio=0.01, n_alphas=100)
coxnet.fit(X_train, y_train)

# Access regularization path
print(f"Alpha range: {coxnet.alphas_[0]:.4f} to {coxnet.alphas_[-1]:.4f}")
print(f"Coefficient path shape: {coxnet.coef_path_.shape}")  # (n_features, n_alphas)

# Predict with specific alpha
risk = coxnet.predict(X_test, alpha=0.1)

# Feature selection: identify non-zero coefficients
nonzero = np.count_nonzero(coxnet.coef_)
print(f"Selected features: {nonzero} / {X_train.shape[1]}")
```

### IPCRidge

Inverse probability of censoring weighted Ridge regression for accelerated failure time (AFT) models. Instead of modeling hazard ratios (Cox), it models how features multiply survival time.

**Key difference from Cox**: AFT assumes features accelerate/decelerate survival time by a constant factor. The model predicts log survival time directly.

**When to use**: AFT framework preferred over proportional hazards, high censoring rates, want regularization with Ridge penalty.

```python
from sksurv.linear_model import IPCRidge

ipcridge = IPCRidge(alpha=1.0)
ipcridge.fit(X_train, y_train)
log_time = ipcridge.predict(X_test)  # Predicts log survival time (not risk)
```

### Checking Proportional Hazards

The proportional hazards assumption should be verified. If violated, consider stratification, time-varying coefficients, or alternative models (RSF, GBS).

Validation methods (available in lifelines, not directly in sksurv):
- Schoenfeld residuals test
- Log-log survival plots
- Statistical tests per covariate

## Ensemble Methods

### RandomSurvivalForest

Extends random forests to survival analysis. Builds multiple trees on bootstrap samples; at terminal nodes, Kaplan-Meier/Nelson-Aalen estimators compute survival functions. Aggregates by averaging across trees.

**Key parameters**:

| Parameter | Default | Recommended | Effect |
|-----------|---------|-------------|--------|
| `n_estimators` | 100 | 200-500 | More = more stable, slower |
| `max_depth` | None | None or 10-20 | Controls tree depth |
| `min_samples_split` | 6 | 10-20 | Larger = more regularization |
| `min_samples_leaf` | 3 | 10-15 | Prevents overfitting to small groups |
| `max_features` | None | "sqrt" | Features per split |
| `n_jobs` | None | -1 | Parallel trees |

**Feature importance**: Built-in impurity-based importance is NOT reliable for survival data. Always use permutation importance:

```python
from sklearn.inspection import permutation_importance
from sksurv.metrics import as_concordance_index_ipcw_scorer

perm = permutation_importance(
    rsf, X_test, y_test, n_repeats=10,
    scoring=as_concordance_index_ipcw_scorer(), random_state=42,
)
for i in perm.importances_mean.argsort()[::-1][:10]:
    print(f"{X.columns[i]:20s}: {perm.importances_mean[i]:.4f}")
```

### GradientBoostingSurvivalAnalysis

Sequential boosting: each iteration adds a weak learner correcting previous errors. f(x) = sum(beta_m * g(x; theta_m)).

**Loss functions**:
- `"coxph"` (default): Cox partial likelihood -- standard proportional hazards framework
- `"ipcwls"`: Accelerated failure time -- models time directly

**Regularization strategies**:
1. **Learning rate** (< 1): Shrinks each tree's contribution. Smaller = better generalization but more iterations. Range: 0.01-0.1
2. **Dropout** (> 0): Randomly drops previous learners. Range: 0.01-0.2
3. **Subsampling** (< 1): Uses random subset per iteration. Range: 0.5-0.9

Recommendation: Combine small learning rate with early stopping.

**Early stopping**:

```python
from sksurv.ensemble import GradientBoostingSurvivalAnalysis

gbs = GradientBoostingSurvivalAnalysis(
    n_estimators=1000, learning_rate=0.01, max_depth=3,
    validation_fraction=0.2, n_iter_no_change=10,
    random_state=42,
)
gbs.fit(X_train, y_train)
print(f"Stopped at iteration {gbs.n_estimators_}")
```

**Hyperparameter tuning grid**:

```python
from sklearn.model_selection import GridSearchCV
from sksurv.metrics import as_concordance_index_ipcw_scorer

param_grid = {
    "learning_rate": [0.01, 0.05, 0.1],
    "n_estimators": [100, 200, 300],
    "max_depth": [3, 5, 7],
    "subsample": [0.8, 1.0],
}
cv = GridSearchCV(
    GradientBoostingSurvivalAnalysis(random_state=42),
    param_grid, scoring=as_concordance_index_ipcw_scorer(),
    cv=5, n_jobs=-1,
)
cv.fit(X, y)
print(f"Best params: {cv.best_params_}, C-index: {cv.best_score_:.3f}")
```

### ComponentwiseGradientBoostingSurvivalAnalysis

Uses component-wise least squares as base learners. Produces sparse linear models with automatic feature selection (similar to Lasso).

**When to use**: Want interpretable linear model with automatic feature selection from high-dimensional data. Produces sparse coefficients.

```python
from sksurv.ensemble import ComponentwiseGradientBoostingSurvivalAnalysis

cgbs = ComponentwiseGradientBoostingSurvivalAnalysis(
    loss="coxph", learning_rate=0.1, n_estimators=100,
)
cgbs.fit(X, y)
selected = [i for i, c in enumerate(cgbs.coef_) if c != 0]
print(f"Selected {len(selected)} features")
```

### ExtraSurvivalTrees

Extremely randomized trees: instead of finding the best split, randomly selects split points, adding more diversity.

**When to use**: More regularization than RSF, limited data, faster training.

### Ensemble Model Comparison

| Model | Complexity | Interpretability | Performance | Speed |
|-------|-----------|------------------|-------------|-------|
| RandomSurvivalForest | Medium | Low | High | Medium |
| GradientBoostingSurvivalAnalysis | High | Low | Highest | Slow |
| ComponentwiseGB | Low | High (linear) | Medium | Fast |
| ExtraSurvivalTrees | Medium | Low | Medium-High | Fast |

## Survival SVMs

### Model Types

**FastSurvivalSVM**: Linear SVM via coordinate descent. O(n*p) per iteration.
- Parameters: `alpha` (regularization, default 1.0), `rank_ratio` (ranking vs regression, default 1.0), `max_iter` (default 20)

**FastKernelSurvivalSVM**: Kernel SVM for non-linear relationships. O(n^2 * p).
- Kernels: "linear", "poly", "rbf" (most common), "sigmoid", custom
- Additional: `gamma` (kernel coefficient), `degree` (polynomial), `coef0` (poly/sigmoid)

**HingeLossSurvivalSVM**: Hinge loss variant, sparse solutions.

**NaiveSurvivalSVM**: Original formulation, O(n^3), for small datasets or benchmarking only.

**MinlipSurvivalAnalysis**: Minimizing Lipschitz constant approach, research applications.

### ClinicalKernelTransform

Specialized kernel combining clinical + molecular features with separate weighting. Useful when mixing low-dimensional clinical variables (age, stage) with high-dimensional genomics.

```python
from sksurv.kernels import ClinicalKernelTransform
from sksurv.svm import FastKernelSurvivalSVM
from sklearn.pipeline import make_pipeline

transform = ClinicalKernelTransform(fit_once=True)
transform.prepare(X_train)
pipe = make_pipeline(transform, FastKernelSurvivalSVM(alpha=1.0))
pipe.fit(X_train, y_train)
```

### SVM Kernel Comparison

```python
from sksurv.svm import FastKernelSurvivalSVM
from sksurv.metrics import concordance_index_ipcw

kernels = ["linear", "poly", "rbf", "sigmoid"]
for kernel in kernels:
    svm = FastKernelSurvivalSVM(kernel=kernel, alpha=1.0, random_state=42)
    svm.fit(X_train_scaled, y_train)
    risk = svm.predict(X_test_scaled)
    c = concordance_index_ipcw(y_train, y_test, risk)[0]
    print(f"{kernel:10s}: C-index = {c:.3f}")
```

### SVM Selection Guide

| Model | Speed | Non-linearity | Scalability |
|-------|-------|---------------|-------------|
| FastSurvivalSVM | Fast | No | High |
| FastKernelSurvivalSVM | Medium | Yes | Medium |
| HingeLossSurvivalSVM | Fast | No | High |
| NaiveSurvivalSVM | Slow | No | Low |

## Evaluation Metrics

### Concordance Index Detail

C-index = P(risk_i > risk_j | T_i < T_j) for concordant pairs.

**Harrell's** (`concordance_index_censored`): Traditional estimator. Biased upward with >40% censoring. Returns tuple: (c_index, concordant, discordant, tied_risk, tied_time).

**Uno's** (`concordance_index_ipcw`): IPCW-corrected, stable even with high censoring. Requires `y_train` for censoring distribution estimation. Returns: (c_index, concordant, discordant, tied_risk).

```python
from sksurv.metrics import concordance_index_censored, concordance_index_ipcw

# Compare both
harrell = concordance_index_censored(y_test["event"], y_test["time"], risk)[0]
uno = concordance_index_ipcw(y_train, y_test, risk)[0]
print(f"Harrell: {harrell:.3f}, Uno: {uno:.3f}")
```

### Time-Dependent AUC

Evaluates discrimination at specific time points: P(risk_i > risk_j | T_i <= t, T_j > t).

```python
from sksurv.metrics import cumulative_dynamic_auc
import matplotlib.pyplot as plt
import numpy as np

times = np.array([365, 730, 1095, 1460, 1825])
auc, mean_auc = cumulative_dynamic_auc(y_train, y_test, risk, times)

plt.plot(times / 365, auc, marker="o")
plt.xlabel("Years")
plt.ylabel("Time-dependent AUC")
plt.title(f"Mean AUC: {mean_auc:.3f}")
plt.grid(True, alpha=0.3)
plt.savefig("td_auc.png", dpi=150)
```

### Brier Score

Extends mean squared error to censored data. Measures both discrimination and calibration: (1/n) * sum(w_i * (S(t|x_i) - I(T_i > t))^2).

**Single timepoint**: `brier_score(y_train, y_test, surv_at_t, time_point)`
**Integrated (summary)**: `integrated_brier_score(y_train, y_test, surv_probs_matrix, times)`

```python
from sksurv.metrics import brier_score, integrated_brier_score
import numpy as np

# Single timepoint
surv_funcs = model.predict_survival_function(X_test)
time_point = 1825  # 5 years
surv_at_t = np.array([fn(time_point) for fn in surv_funcs])
bs = brier_score(y_train, y_test, surv_at_t, time_point)[1]
print(f"Brier Score at 5yr: {bs:.3f}")

# Integrated
times = np.percentile(y_test["time"][y_test["event"]], [25, 50, 75])
preds = np.row_stack([fn(times) for fn in surv_funcs])
ibs = integrated_brier_score(y_train, y_test, preds, times)
print(f"IBS: {ibs:.3f}")
```

### Cross-Validation Scorers

```python
from sksurv.metrics import (
    as_concordance_index_ipcw_scorer,
    as_integrated_brier_score_scorer,
)
from sklearn.model_selection import cross_val_score
import numpy as np

# C-index scorer
scores_c = cross_val_score(model, X, y, cv=5,
                           scoring=as_concordance_index_ipcw_scorer())
print(f"C-index: {scores_c.mean():.3f} +/- {scores_c.std():.3f}")

# IBS scorer (needs time points)
times = np.percentile(y["time"][y["event"]], [25, 50, 75])
scores_ibs = cross_val_score(model, X, y, cv=5,
                             scoring=as_integrated_brier_score_scorer(times))
print(f"IBS: {scores_ibs.mean():.3f} +/- {scores_ibs.std():.3f}")
```

### Comprehensive Evaluation Function

```python
from sksurv.metrics import (
    concordance_index_censored, concordance_index_ipcw,
    cumulative_dynamic_auc, integrated_brier_score,
)
import numpy as np

def evaluate_survival_model(model, X_train, X_test, y_train, y_test):
    """Full evaluation: C-index + AUC + Brier Score."""
    risk = model.predict(X_test)
    surv_funcs = model.predict_survival_function(X_test)
    times = np.percentile(y_test["time"][y_test["event"]], [25, 50, 75])

    c_harrell = concordance_index_censored(y_test["event"], y_test["time"], risk)[0]
    c_uno = concordance_index_ipcw(y_train, y_test, risk)[0]
    auc, mean_auc = cumulative_dynamic_auc(y_train, y_test, risk, times)
    preds = np.row_stack([fn(times) for fn in surv_funcs])
    ibs = integrated_brier_score(y_train, y_test, preds, times)

    print(f"Harrell C-index: {c_harrell:.3f}")
    print(f"Uno C-index:     {c_uno:.3f}")
    print(f"Mean AUC:        {mean_auc:.3f}")
    print(f"IBS:             {ibs:.3f}")
    return {"c_harrell": c_harrell, "c_uno": c_uno, "mean_auc": mean_auc, "ibs": ibs}
```

---

Condensed from originals: `cox-models.md` (182 lines), `ensemble-models.md` (327 lines), `svm-models.md` (411 lines), `evaluation-metrics.md` (378 lines). Total original: 1,298 lines.

Retained: All model types (CoxPH, CoxNet, IPCRidge, RSF, GBS, ComponentwiseGB, ExtraSurvivalTrees, FastSurvivalSVM, FastKernelSurvivalSVM, HingeLossSurvivalSVM, NaiveSurvivalSVM, MinlipSurvivalAnalysis, ClinicalKernelTransform), all evaluation metrics (Harrell/Uno C-index, time-dependent AUC, Brier score, IBS), cross-validation scorers, comprehensive evaluation pipeline, early stopping, hyperparameter tuning, model comparison tables, kernel comparison, regularization strategies, proportional hazards checking guidance.

Omitted from cox-models.md: Detailed Cox "Model Comparison and Selection" prose (duplicates model selection guide in SKILL.md Key Concepts). Omitted from ensemble-models.md: RSF "How They Work" algorithmic detail (4-step internal process), duplicated general recommendations prose. Omitted from svm-models.md: Repeated "Example 1/2/3" practical examples (consolidated into SVM Kernel Comparison code block), "When SVMs May Not Be Best Choice" prose (covered by model selection guide). Omitted from evaluation-metrics.md: "Choosing the Right Metric" prose section (consolidated into Evaluation Metric Decision Table in SKILL.md Key Concepts), repeated metric comparison text.
