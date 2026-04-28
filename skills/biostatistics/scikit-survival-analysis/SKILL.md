---
name: scikit-survival-analysis
description: "Time-to-event modeling with scikit-survival: Cox PH (elastic net), Random Survival Forests, Boosting, SVMs for censored data. C-index, Brier, time-dependent AUC; Kaplan-Meier, Nelson-Aalen, competing risks. Pipeline/GridSearchCV compatible. Use statsmodels for frequentist, pymc for Bayesian, lifelines for parametric."
license: GPL-3.0
---

# scikit-survival -- Survival Analysis

## Overview

scikit-survival is a Python library for time-to-event analysis built on scikit-learn. It handles right-censored data (observations where the event has not yet occurred) using Cox models, ensemble methods, survival SVMs, and non-parametric estimators. All models follow the scikit-learn `fit/predict` API and integrate with Pipelines, cross-validation, and GridSearchCV.

## When to Use

- Modeling time-to-event outcomes with right-censored data (clinical trials, reliability)
- Fitting Cox proportional hazards models (standard or elastic net penalized)
- Building ensemble survival models (Random Survival Forest, Gradient Boosting)
- Training survival SVMs for margin-based learning on medium-sized datasets
- Evaluating survival predictions with censoring-aware metrics (C-index, Brier score, AUC)
- Estimating non-parametric survival curves (Kaplan-Meier, Nelson-Aalen)
- Analyzing competing risks with cumulative incidence functions
- High-dimensional survival data with automatic feature selection (CoxNet L1/L2)
- For **simpler parametric models** (Weibull, log-normal AFT) or statistical tests (log-rank), use `lifelines`
- For **deep learning survival models**, use `pycox` or `torchlife`

## Prerequisites

```bash
pip install scikit-survival scikit-learn pandas numpy matplotlib
```

**Python**: >= 3.9. **Dependencies**: scikit-learn, numpy, scipy, pandas, joblib, osqp (for some SVM solvers).

**Data format**: Survival outcomes are NumPy structured arrays with `(event, time)` fields. Events are boolean (True = event occurred, False = censored). Times are positive floats.

## Quick Start

```python
from sksurv.datasets import load_breast_cancer
from sksurv.ensemble import RandomSurvivalForest
from sksurv.metrics import concordance_index_ipcw
from sklearn.model_selection import train_test_split

X, y = load_breast_cancer()
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

rsf = RandomSurvivalForest(n_estimators=100, random_state=42)
rsf.fit(X_train, y_train)

risk_scores = rsf.predict(X_test)
c_index = concordance_index_ipcw(y_train, y_test, risk_scores)[0]
print(f"C-index: {c_index:.3f}")  # e.g., 0.68

# Individual survival curves
surv_fns = rsf.predict_survival_function(X_test[:2])
for fn in surv_fns:
    print(f"5-year survival: {fn(365 * 5):.3f}")
```

## Core API

### Module 1: Data Preparation

Create structured survival arrays and preprocess features.

```python
import numpy as np
import pandas as pd
from sksurv.util import Surv
from sksurv.preprocessing import OneHotEncoder, encode_categorical
from sksurv.datasets import load_gbsg2, load_breast_cancer
from sklearn.preprocessing import StandardScaler

# Create survival outcome from arrays
event = np.array([True, False, True, True, False])
time = np.array([120.0, 365.0, 200.0, 90.0, 400.0])
y = Surv.from_arrays(event=event, time=time)
print(y.dtype)  # [('event', '?'), ('time', '<f8')]

# From DataFrame columns
# y = Surv.from_dataframe("event_col", "time_col", df)

# Load built-in datasets
# Available: load_gbsg2, load_breast_cancer, load_veterans_lung_cancer,
#            load_whas500, load_aids, load_flchain
X, y = load_gbsg2()
print(f"Shape: {X.shape}, Events: {y['event'].sum()}, "
      f"Censoring rate: {1 - y['event'].mean():.1%}")

# Encode categoricals (survival-aware one-hot)
X_encoded = encode_categorical(X)  # auto-detect and encode all categorical cols

# Standardize (critical for Cox and SVM models)
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X_encoded)
```

```python
from sksurv.io import loadarff

# Load ARFF format (Weka format)
data = loadarff("survival_data.arff")
X_arff, y_arff = data[0], data[1]  # DataFrame, structured array
```

### Module 2: Cox Proportional Hazards

Semi-parametric model: h(t|x) = h_0(t) * exp(beta^T x). Interpretable coefficients as log hazard ratios.

```python
from sksurv.linear_model import CoxPHSurvivalAnalysis, CoxnetSurvivalAnalysis, IPCRidge

# Standard Cox PH model
cox = CoxPHSurvivalAnalysis(alpha=0.0, ties="breslow")
cox.fit(X_train, y_train)
print(f"Coefficients: {cox.coef_}")  # log hazard ratios
# Hazard ratio interpretation: exp(coef) = HR for 1-unit increase
risk_scores = cox.predict(X_test)  # Higher = higher risk

# Survival function for individual patients
surv_funcs = cox.predict_survival_function(X_test[:3])
for fn in surv_funcs:
    print(f"5-year survival: {fn(365 * 5):.3f}")
```

```python
# Penalized Cox (elastic net) -- for high-dimensional data (p > n)
coxnet = CoxnetSurvivalAnalysis(
    l1_ratio=0.9,           # 0=Ridge, 1=Lasso, between=Elastic Net
    alpha_min_ratio=0.01,   # smallest alpha / largest alpha ratio
    n_alphas=100,           # steps in regularization path
)
coxnet.fit(X_train, y_train)

# Feature selection: non-zero coefficients
selected = np.where(coxnet.coef_ != 0)[0]
print(f"Selected {len(selected)} / {X_train.shape[1]} features")

# IPCRidge: accelerated failure time model (predicts log survival time)
ipcridge = IPCRidge(alpha=1.0)
ipcridge.fit(X_train, y_train)
log_survival_time = ipcridge.predict(X_test)
```

### Module 3: Ensemble Methods

Non-parametric tree-based models for complex non-linear relationships.

```python
from sksurv.ensemble import (
    RandomSurvivalForest,
    GradientBoostingSurvivalAnalysis,
    ComponentwiseGradientBoostingSurvivalAnalysis,
    ExtraSurvivalTrees,
)

# Random Survival Forest -- robust, minimal tuning
rsf = RandomSurvivalForest(
    n_estimators=200, min_samples_split=10, min_samples_leaf=15,
    max_features="sqrt", random_state=42, n_jobs=-1,
)
rsf.fit(X_train, y_train)
risk = rsf.predict(X_test)

# Gradient Boosting -- best performance, needs tuning
gbs = GradientBoostingSurvivalAnalysis(
    loss="coxph",           # "coxph" or "ipcwls" (AFT)
    n_estimators=300, learning_rate=0.05, max_depth=3,
    subsample=0.8, dropout_rate=0.1, random_state=42,
)
gbs.fit(X_train, y_train)

# ComponentwiseGB -- linear model with automatic feature selection
cgbs = ComponentwiseGradientBoostingSurvivalAnalysis(
    n_estimators=100, learning_rate=0.1,
)
cgbs.fit(X_train, y_train)
print(f"Non-zero coefficients: {np.sum(cgbs.coef_ != 0)}")

# ExtraSurvivalTrees -- more regularized than RSF, faster training
est = ExtraSurvivalTrees(n_estimators=100, random_state=42)
est.fit(X_train, y_train)

# Survival curves from any ensemble model
surv_funcs = rsf.predict_survival_function(X_test[:1])
chf_funcs = rsf.predict_cumulative_hazard_function(X_test[:1])
```

### Module 4: Survival SVMs

Margin-based learning for survival ranking. **Always standardize features**.

```python
from sksurv.svm import FastSurvivalSVM, FastKernelSurvivalSVM, HingeLossSurvivalSVM

# Linear SVM -- fast, for linear relationships
lsvm = FastSurvivalSVM(alpha=1.0, rank_ratio=1.0, max_iter=100, random_state=42)
lsvm.fit(X_train_scaled, y_train)
risk = lsvm.predict(X_test_scaled)

# Kernel SVM -- for non-linear relationships (rbf, poly, sigmoid)
ksvm = FastKernelSurvivalSVM(
    alpha=1.0, kernel="rbf", gamma="scale",
    max_iter=50, random_state=42,
)
ksvm.fit(X_train_scaled, y_train)

# Hinge loss variant
hsvm = HingeLossSurvivalSVM(alpha=1.0, random_state=42)
hsvm.fit(X_train_scaled, y_train)
# NaiveSurvivalSVM also available but slower (O(n^3))
```

```python
from sksurv.kernels import ClinicalKernelTransform

# Clinical kernel: combines clinical + molecular features
# Weighs clinical variables separately from high-dimensional molecular data
transform = ClinicalKernelTransform(fit_once=True)
transform.prepare(X_train)  # auto-detect clinical features
X_kern = transform.fit_transform(X_train)
```

### Module 5: Non-Parametric Estimation

Estimate survival and hazard curves without model assumptions.

```python
from sksurv.nonparametric import kaplan_meier_estimator, nelson_aalen_estimator
import matplotlib.pyplot as plt

# Kaplan-Meier survival curve
time_km, surv_prob = kaplan_meier_estimator(y["event"], y["time"])
plt.step(time_km, surv_prob, where="post")
plt.xlabel("Time (days)")
plt.ylabel("Survival probability")
plt.title("Kaplan-Meier Estimate")
plt.savefig("km_curve.png", dpi=150)

# With confidence intervals
time_km, surv_prob, conf_int = kaplan_meier_estimator(
    y["event"], y["time"], conf_type="log-log",
)

# Nelson-Aalen cumulative hazard
time_na, cum_hazard = nelson_aalen_estimator(y["event"], y["time"])

# Stratified KM by group
for group_name, mask in [("Treated", treated_mask), ("Control", control_mask)]:
    t, s = kaplan_meier_estimator(y[mask]["event"], y[mask]["time"])
    plt.step(t, s, where="post", label=group_name)
plt.legend()
```

### Module 6: Evaluation Metrics

Censoring-aware metrics for discrimination and calibration.

```python
from sksurv.metrics import (
    concordance_index_censored,
    concordance_index_ipcw,
    cumulative_dynamic_auc,
    integrated_brier_score,
    brier_score,
    as_concordance_index_ipcw_scorer,
    as_integrated_brier_score_scorer,
)
import numpy as np

risk_scores = model.predict(X_test)

# Harrell's C-index (simple, biased with high censoring)
c_harrell = concordance_index_censored(
    y_test["event"], y_test["time"], risk_scores
)[0]

# Uno's C-index (recommended -- robust to censoring)
c_uno = concordance_index_ipcw(y_train, y_test, risk_scores)[0]
print(f"C-index (Harrell): {c_harrell:.3f}, (Uno): {c_uno:.3f}")

# Time-dependent AUC at clinically relevant timepoints
times = np.array([365, 730, 1095])  # 1, 2, 3 years
auc, mean_auc = cumulative_dynamic_auc(y_train, y_test, risk_scores, times)
print(f"AUC at 1/2/3yr: {auc}, Mean: {mean_auc:.3f}")

# Integrated Brier Score (measures discrimination + calibration)
surv_funcs = model.predict_survival_function(X_test)
preds = np.row_stack([fn(times) for fn in surv_funcs])
ibs = integrated_brier_score(y_train, y_test, preds, times)
print(f"IBS: {ibs:.3f}")  # Lower is better; compare vs KM baseline
```

### Module 7: Competing Risks

Multiple mutually exclusive event types (e.g., death from cancer vs cardiovascular).

```python
from sksurv.nonparametric import cumulative_incidence_competing_risks
from sksurv.linear_model import CoxPHSurvivalAnalysis
from sksurv.util import Surv
import numpy as np

# Cumulative Incidence Function (CIF) estimation
# y_competing: structured array with integer event codes
# (0=censored, 1=relapse, 2=death_in_remission)
time_pts, cif_relapse, cif_death = cumulative_incidence_competing_risks(y_competing)

import matplotlib.pyplot as plt
plt.step(time_pts, cif_relapse, where="post", label="Relapse")
plt.step(time_pts, cif_death, where="post", label="Death in remission")
plt.xlabel("Time")
plt.ylabel("Cumulative Incidence")
plt.legend()

# Cause-specific hazard models: fit separate Cox per event type
event_types = np.array([0, 1, 2, 1, 0, 2, 1])
times = np.array([10.2, 5.3, 8.1, 3.7, 12.5, 6.8, 4.2])

# Model for relapse (event type 1); treat type 2 as censored
y_relapse = Surv.from_arrays(event=(event_types == 1), time=times)
cox_relapse = CoxPHSurvivalAnalysis()
cox_relapse.fit(X, y_relapse)

# Model for death (event type 2); treat type 1 as censored
y_death = Surv.from_arrays(event=(event_types == 2), time=times)
cox_death = CoxPHSurvivalAnalysis()
cox_death.fit(X, y_death)
print(f"Relapse HR (age): {np.exp(cox_relapse.coef_[0]):.3f}")
print(f"Death HR (age): {np.exp(cox_death.coef_[0]):.3f}")
```

## Key Concepts

### Model Selection Guide

```
High-dimensional (p > n)?
├── Yes → CoxnetSurvivalAnalysis (elastic net)
└── No
    ├── Need interpretable coefficients?
    │   ├── Yes → CoxPHSurvivalAnalysis or ComponentwiseGB
    │   └── No
    │       ├── Large data (n > 1000) → GradientBoostingSurvivalAnalysis
    │       ├── Medium data → RandomSurvivalForest or FastKernelSurvivalSVM
    │       └── Small data → RandomSurvivalForest
    └── For max performance → compare multiple models
```

### Censoring Types

scikit-survival primarily handles **right-censoring** (event not observed by end of study). Left-censoring and interval-censoring require other tools (e.g., lifelines). Censoring rate affects metric choice: >40% censoring favors Uno's C-index over Harrell's.

### Concordance Index Interpretation

- **0.5** = random prediction (no discrimination)
- **0.6-0.7** = moderate discrimination
- **0.7-0.8** = good discrimination (typical for clinical models)
- **0.8+** = excellent (rare for clinical survival data)
- C-index measures ranking ability, not calibration. Always pair with Brier score.

### Evaluation Metric Decision Table

| Metric | Measures | Best For |
|--------|----------|----------|
| Harrell's C-index | Ranking only | Quick development, low censoring |
| Uno's C-index | Ranking (censoring-adjusted) | Publication, any censoring rate |
| Time-dependent AUC | Discrimination at fixed t | Clinical decision at specific horizons |
| Brier Score (single t) | Calibration at fixed t | Probability accuracy at timepoint |
| Integrated Brier Score | Overall calibration | Comprehensive model assessment |

## Common Workflows

### Workflow 1: Standard Survival Pipeline

**Goal**: End-to-end analysis with preprocessing, model fitting, and evaluation.

```python
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import GridSearchCV, train_test_split
from sksurv.datasets import load_breast_cancer
from sksurv.ensemble import GradientBoostingSurvivalAnalysis
from sksurv.metrics import (
    concordance_index_ipcw, cumulative_dynamic_auc,
    integrated_brier_score, as_concordance_index_ipcw_scorer,
)
import numpy as np

X, y = load_breast_cancer()
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Build pipeline
pipe = Pipeline([
    ("scaler", StandardScaler()),
    ("model", GradientBoostingSurvivalAnalysis(random_state=42)),
])

# Hyperparameter search
param_grid = {
    "model__learning_rate": [0.01, 0.05, 0.1],
    "model__n_estimators": [100, 200],
    "model__max_depth": [3, 5],
}
cv = GridSearchCV(pipe, param_grid, cv=5,
                  scoring=as_concordance_index_ipcw_scorer(), n_jobs=-1)
cv.fit(X_train, y_train)
print(f"Best CV C-index: {cv.best_score_:.3f}, Params: {cv.best_params_}")

# Final evaluation on test set
best = cv.best_estimator_
risk = best.predict(X_test)
c_uno = concordance_index_ipcw(y_train, y_test, risk)[0]
times = np.percentile(y_test["time"][y_test["event"]], [25, 50, 75])
auc, mean_auc = cumulative_dynamic_auc(y_train, y_test, risk, times)
print(f"Test C-index: {c_uno:.3f}, Mean AUC: {mean_auc:.3f}")
```

### Workflow 2: Model Comparison

**Goal**: Compare multiple model families and select the best.

```python
from sksurv.linear_model import CoxPHSurvivalAnalysis
from sksurv.ensemble import RandomSurvivalForest, GradientBoostingSurvivalAnalysis
from sksurv.svm import FastSurvivalSVM
from sksurv.metrics import concordance_index_ipcw, integrated_brier_score
from sklearn.preprocessing import StandardScaler
import numpy as np

scaler = StandardScaler()
X_train_s = scaler.fit_transform(X_train)
X_test_s = scaler.transform(X_test)

models = {
    "CoxPH": CoxPHSurvivalAnalysis(),
    "RSF": RandomSurvivalForest(n_estimators=200, random_state=42),
    "GBS": GradientBoostingSurvivalAnalysis(n_estimators=200, random_state=42),
    "LinearSVM": FastSurvivalSVM(alpha=1.0, random_state=42),
}

times = np.percentile(y_test["time"][y_test["event"]], [25, 50, 75])
for name, model in models.items():
    X_tr = X_train_s if name in ("CoxPH", "LinearSVM") else X_train
    X_te = X_test_s if name in ("CoxPH", "LinearSVM") else X_test
    model.fit(X_tr, y_train)
    risk = model.predict(X_te)
    c = concordance_index_ipcw(y_train, y_test, risk)[0]
    print(f"{name:12s}: C-index = {c:.3f}")
```

### Workflow 3: High-Dimensional Feature Selection

1. Fit CoxnetSurvivalAnalysis with l1_ratio=0.9 (Lasso-dominant)
2. Use GridSearchCV over alpha_min_ratio values with C-index scorer
3. Extract non-zero coefficients from best model
4. Refit standard CoxPH or RSF on selected features for final model
5. Evaluate on held-out test set with Uno's C-index

## Key Parameters

| Parameter | Module | Default | Range | Effect |
|-----------|--------|---------|-------|--------|
| `alpha` | CoxPH | 0.0 | >= 0 | Regularization (0 = none) |
| `l1_ratio` | CoxNet | 0.5 | 0-1 | L1 vs L2 penalty (1=Lasso, 0=Ridge) |
| `n_estimators` | RSF, GBS | 100 | 50-1000 | Number of trees/iterations |
| `max_depth` | RSF, GBS | None/3 | 1-20 | Tree depth (GBS: 3-5 recommended) |
| `learning_rate` | GBS | 0.1 | 0.001-0.3 | Step size shrinkage per iteration |
| `subsample` | GBS | 1.0 | 0.5-1.0 | Fraction of samples per tree |
| `dropout_rate` | GBS | 0.0 | 0-0.3 | Drop previous learners during training |
| `max_features` | RSF | None | "sqrt","log2",int | Features per split |
| `alpha` | FastSurvivalSVM | 1.0 | 0.01-100 | SVM regularization |
| `kernel` | FastKernelSVM | "rbf" | "linear","rbf","poly","sigmoid" | Kernel function |
| `gamma` | FastKernelSVM | "scale" | "scale","auto",float | Kernel coefficient |

## Best Practices

1. **Always standardize features for Cox and SVM models**: Coefficients and margins are scale-dependent. Use `StandardScaler` inside a Pipeline to prevent leakage.

2. **Use Uno's C-index over Harrell's**: More robust to censoring distribution differences; required for comparing models across datasets. Pass `y_train` as the first argument.

3. **Anti-pattern -- using built-in RSF feature importance**: It is biased toward continuous and high-cardinality features. Use `sklearn.inspection.permutation_importance()` instead.

4. **Report multiple metrics**: C-index alone measures only discrimination. Add Brier score for calibration and time-dependent AUC for time-specific performance.

5. **Anti-pattern -- ignoring proportional hazards assumption**: Cox models assume constant hazard ratios over time. Validate with Schoenfeld residuals (available in lifelines) or use non-parametric alternatives (RSF, GBS).

6. **Ensure sufficient events per feature**: Rule of thumb: 10+ events per feature for Cox. With fewer events, use CoxNet (l1_ratio=0.9) or ensemble methods.

7. **Use scikit-learn Pipelines**: Wrapping preprocessing + model prevents data leakage and simplifies cross-validation and deployment.

8. **Anti-pattern -- treating competing events as censored for KM**: Kaplan-Meier overestimates event probability when competing risks exist. Use `cumulative_incidence_competing_risks()` instead.

9. **GBS early stopping**: For GradientBoosting, set `n_estimators=1000` with `n_iter_no_change=10` to automatically stop when validation performance plateaus.

## Common Recipes

### Recipe: Hyperparameter Tuning with Cross-Validation

```python
from sklearn.model_selection import GridSearchCV
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sksurv.ensemble import RandomSurvivalForest
from sksurv.metrics import as_concordance_index_ipcw_scorer

pipe = Pipeline([
    ("scaler", StandardScaler()),
    ("model", RandomSurvivalForest(random_state=42)),
])
param_grid = {
    "model__n_estimators": [100, 300, 500],
    "model__min_samples_split": [6, 10, 20],
    "model__max_depth": [None, 10, 20],
}
cv = GridSearchCV(pipe, param_grid, cv=5,
                  scoring=as_concordance_index_ipcw_scorer(), n_jobs=-1)
cv.fit(X, y)
print(f"Best: {cv.best_score_:.3f}, Params: {cv.best_params_}")
```

### Recipe: Permutation Feature Importance

```python
from sklearn.inspection import permutation_importance
from sksurv.metrics import as_concordance_index_ipcw_scorer

result = permutation_importance(
    rsf, X_test, y_test, n_repeats=15,
    scoring=as_concordance_index_ipcw_scorer(), random_state=42, n_jobs=-1,
)
sorted_idx = result.importances_mean.argsort()[::-1]
for i in sorted_idx[:10]:
    print(f"{X.columns[i]:20s}: {result.importances_mean[i]:.4f} "
          f"+/- {result.importances_std[i]:.4f}")
```

### Recipe: Kaplan-Meier with Confidence Bands

```python
from sksurv.nonparametric import kaplan_meier_estimator
import matplotlib.pyplot as plt

time, surv, conf_int = kaplan_meier_estimator(
    y["event"], y["time"], conf_type="log-log",
)
plt.step(time, surv, where="post", label="KM estimate")
plt.fill_between(time, conf_int[0], conf_int[1], alpha=0.25, step="post")
plt.xlabel("Time")
plt.ylabel("Survival probability")
plt.legend()
plt.savefig("km_with_ci.png", dpi=150)
```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `ValueError: y must be a structured array` | Wrong outcome format | Use `Surv.from_arrays(event, time)` -- event must be bool, time must be float |
| `concordance_index_ipcw` raises error | Missing `y_train` argument | IPCW requires training set for censoring distribution; pass `y_train` as first arg |
| Cox model won't converge | Correlated or unstandardized features | Standardize with `StandardScaler`; switch to `CoxnetSurvivalAnalysis` |
| Very low C-index (< 0.5) | Wrong sign or non-predictive features | Verify event/time coding; check feature engineering |
| `as_concordance_index_ipcw_scorer` error in CV | Time range mismatch between folds | Ensure all folds contain events at evaluated timepoints |
| SVM extremely slow | Large dataset with kernel SVM | Use `FastSurvivalSVM` (linear, O(np)) for large n; subsample for kernel |
| RSF feature importance misleading | Built-in impurity importance biased | Use `permutation_importance()` from scikit-learn |
| Kaplan-Meier overestimates | Competing events treated as censoring | Use `cumulative_incidence_competing_risks()` instead |

## Bundled Resources

### references/models_evaluation.md

**Covers**: Detailed Cox model family (CoxPH, CoxNet, IPCRidge with parameter guidance and interpretation), ensemble methods (RSF, GBS, ComponentwiseGB, ExtraSurvivalTrees with hyperparameter tuning, early stopping, loss functions), SVM models (FastSurvivalSVM, FastKernelSurvivalSVM, HingeLossSurvivalSVM, NaiveSurvivalSVM, MinlipSurvivalAnalysis with kernel selection), evaluation metrics (Harrell vs Uno C-index selection, time-dependent AUC plotting, Brier score with null model comparison, comprehensive evaluation pipeline), model comparison tables.

**Relocated inline**: Core usage patterns for all model families consolidated into Core API Modules 2-4 and Module 6. Model selection decision tree relocated to Key Concepts.

**Omitted**: CoxNet cross-validation alpha selection via scoring string (not a valid sklearn scorer usage -- use `as_concordance_index_ipcw_scorer()` as shown in Core API). NaiveSurvivalSVM detailed usage (slow, primarily for benchmarking). MinlipSurvivalAnalysis detailed usage (research-only). Redundant "when to use" prose duplicated across original reference files.

Consolidates 4 originals: `cox-models.md` (182 lines), `ensemble-models.md` (327 lines), `svm-models.md` (411 lines), `evaluation-metrics.md` (378 lines). Total: 1,298 lines.

### references/data_competing_risks.md

**Covers**: Complete data preprocessing workflows (Surv arrays, loading custom CSV, ARFF I/O, categorical encoding methods, standardization, missing data imputation strategies, feature selection), data validation checks (negative times, censoring rate, events-per-feature), train-test splitting (random and stratified by event/time), complete preprocessing pipeline with sklearn, competing risks analysis (CIF estimation, data format with event types, stratified group comparison, cause-specific hazard modeling, complete practical example with simulated data).

**Relocated inline**: Core Surv array creation, encode_categorical, StandardScaler usage consolidated into Core API Module 1. CIF estimation and cause-specific Cox models relocated to Core API Module 7.

**Omitted**: Custom preprocessing function with docstring (duplicates sklearn Pipeline pattern shown in Workflow 1). Time-varying covariates note (scikit-survival does not support them -- mentioned only as a 1-line note in original). Fine-Gray sub-distribution model (not available in scikit-survival; noted as lifelines alternative).

Consolidates 2 originals: `data-handling.md` (494 lines), `competing-risks.md` (397 lines). Total: 891 lines.

## Related Skills

- **scikit-learn-machine-learning** -- general ML with same Pipeline/GridSearchCV API; non-survival tasks
- **statsmodels-statistical-modeling** -- frequentist regression (OLS, GLM); non-censored outcomes
- **pymc-bayesian-modeling** -- Bayesian survival models with prior specification
- **matplotlib-scientific-plotting** -- customize Kaplan-Meier curves and survival plots
- **statistical-analysis** -- test selection framework and reporting guidelines

## References

- [scikit-survival documentation](https://scikit-survival.readthedocs.io/) -- official API reference
- [scikit-survival GitHub](https://github.com/sebp/scikit-survival) -- source code and examples
- [API reference](https://scikit-survival.readthedocs.io/en/stable/api/index.html) -- complete class/function list
- Polsterl (2020) "scikit-survival: A Library for Time-to-Event Analysis Built on Top of scikit-learn" -- [JMLR 21(212):1-6](https://jmlr.org/papers/v21/20-729.html)
