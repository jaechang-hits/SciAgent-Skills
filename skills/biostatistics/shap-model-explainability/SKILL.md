---
name: shap-model-explainability
description: >-
  Model interpretability using SHAP (SHapley Additive exPlanations) based on
  Shapley values from game theory. Covers explainer selection (Tree, Deep,
  Linear, Kernel, Gradient, Permutation), computing feature attributions,
  and visualization (waterfall, beeswarm, bar, scatter, force, heatmap).
  Use when explaining ML model predictions, computing feature importance,
  debugging model behavior, analyzing fairness/bias, or comparing models.
  Works with tree-based, deep learning, linear, and black-box models.
license: MIT
---

# SHAP Model Explainability

## Overview

SHAP (SHapley Additive exPlanations) is a unified framework for explaining machine learning model predictions using Shapley values from cooperative game theory. It quantifies each feature's contribution to individual predictions and provides both local (per-instance) and global (dataset-level) explanations with theoretical guarantees of consistency and additivity.

## When to Use

- Explaining which features drive a model's predictions (global importance)
- Understanding why a model made a specific prediction (local explanation)
- Debugging model behavior and identifying data leakage
- Analyzing model fairness across demographic groups
- Comparing feature importance across multiple models
- Generating interpretable model explanations for stakeholders
- For tree-based model interpretation, prefer SHAP over permutation importance or Gini importance (more accurate, instance-level)
- For deep learning interpretation on images, consider GradCAM; use SHAP for tabular/structured data

## Prerequisites

```bash
pip install shap matplotlib
# Optional: xgboost lightgbm tensorflow torch (depending on model)
```

## Quick Start

```python
import shap
import xgboost as xgb
from sklearn.model_selection import train_test_split

# Load example data
X, y = shap.datasets.adult()
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

# Train model
model = xgb.XGBClassifier(n_estimators=100).fit(X_train, y_train)

# Explain: select explainer → compute → visualize
explainer = shap.TreeExplainer(model)
shap_values = explainer(X_test)

shap.plots.beeswarm(shap_values)   # Global importance
shap.plots.waterfall(shap_values[0])  # Single prediction
print(f"Base value: {shap_values.base_values[0]:.3f}")
print(f"SHAP values shape: {shap_values.values.shape}")  # (n_samples, n_features)
```

## Workflow

### Step 1: Select the Right Explainer

Choose based on model type:

| Model Type | Explainer | Speed | Exactness |
|-----------|-----------|-------|-----------|
| Tree-based (XGBoost, LightGBM, RF, CatBoost) | `TreeExplainer` | Fast | Exact |
| Linear (LogReg, GLM, Ridge) | `LinearExplainer` | Instant | Exact |
| Deep learning (TensorFlow, PyTorch) | `DeepExplainer` | Fast | Approximate |
| Deep learning (gradient-based) | `GradientExplainer` | Fast | Approximate |
| Any model (black-box) | `KernelExplainer` | Slow | Approximate |
| Any model (permutation-based) | `PermutationExplainer` | Very slow | Exact |
| **Unsure?** | `shap.Explainer` | Auto | Auto |

```python
# Tree-based models (most common)
explainer = shap.TreeExplainer(model)

# Linear models
explainer = shap.LinearExplainer(model, X_train)

# Deep learning
explainer = shap.DeepExplainer(model, X_train[:100])

# Any model (model-agnostic, slower)
explainer = shap.KernelExplainer(model.predict, shap.kmeans(X_train, 50))

# Auto-select
explainer = shap.Explainer(model, X_train)
```

### Step 2: Compute SHAP Values

```python
shap_values = explainer(X_test)

# shap_values object contains:
# .values      — SHAP values array (n_samples, n_features)
# .base_values — Expected model output (baseline)
# .data        — Original feature values

# Verify additivity: prediction = base_value + sum(SHAP values)
print(f"  {shap_values.base_values[0]:.3f} + {shap_values.values[0].sum():.3f} = "
      f"{shap_values.base_values[0] + shap_values.values[0].sum():.3f}")
```

### Step 3: Global Explanations

```python
# Beeswarm: feature importance + value distributions (most informative)
shap.plots.beeswarm(shap_values, max_display=15)

# Bar: clean mean |SHAP| importance
shap.plots.bar(shap_values)
```

### Step 4: Local Explanations (Individual Predictions)

```python
# Waterfall: detailed breakdown of one prediction
shap.plots.waterfall(shap_values[0])

# Force: additive force visualization
shap.plots.force(shap_values[0])
```

### Step 5: Feature Relationships

```python
# Scatter: how a feature affects predictions
shap.plots.scatter(shap_values[:, "Age"])

# Colored by interaction feature
shap.plots.scatter(shap_values[:, "Age"], color=shap_values[:, "Education-Num"])
```

### Step 6: Advanced Visualizations

```python
# Heatmap: multi-sample SHAP grid
shap.plots.heatmap(shap_values[:100])

# Decision plot: cumulative SHAP paths
shap.plots.decision(shap_values.base_values[0], shap_values.values[:10],
                     feature_names=X_test.columns.tolist())

# Cohort comparison
import numpy as np
mask_a = X_test["Age"] < 40
shap.plots.bar({
    "Under 40": shap_values[mask_a],
    "40+": shap_values[~mask_a]
})
```

## Key Parameters

| Parameter | Explainer/Function | Default | Effect |
|-----------|-------------------|---------|--------|
| `feature_perturbation` | TreeExplainer | `"tree_path_dependent"` | `"interventional"` for causal interpretation (requires background data) |
| `model_output` | TreeExplainer | `"raw"` | `"probability"` to explain probabilities instead of log-odds |
| `data` (background) | KernelExplainer, DeepExplainer | Required | 100-1000 representative samples; use `shap.kmeans(X, 50)` for efficiency |
| `nsamples` | KernelExplainer | `"auto"` | Higher = more accurate but slower; minimum 2×features |
| `max_display` | All plot functions | 10 | Number of features shown in plots |
| `alpha` | scatter/beeswarm | 1.0 | Point transparency for dense datasets |
| `show` | All plot functions | True | Set `False` to get matplotlib figure for saving |
| `clustering` | beeswarm | None | `shap.utils.hclust(...)` to cluster correlated features |

## Key Concepts

### SHAP Value Properties

SHAP values have three theoretical guarantees (unique among explanation methods):

- **Additivity**: `prediction = base_value + sum(SHAP values)` — exact decomposition
- **Consistency**: If a feature becomes more important in the model, its SHAP value increases
- **Missingness**: Features not present receive zero attribution

**Interpretation**: Positive SHAP → pushes prediction higher; Negative → lower; Magnitude → strength of impact.

### Model Output Types

Understand what your model outputs — SHAP explains the output space:

- **Regression**: SHAP values in target units (e.g., dollars, temperature)
- **Classification (log-odds)**: Default for tree classifiers. Use `model_output="probability"` for probability explanations
- **Classification (probability)**: SHAP values sum to probability deviation from baseline

### SHAP vs Other Methods

| Method | Local | Global | Consistent | Model-agnostic |
|--------|-------|--------|-----------|----------------|
| SHAP | Yes | Yes | Yes | Yes |
| Permutation importance | No | Yes | No | Yes |
| Gini/split importance | No | Yes | No | Trees only |
| LIME | Yes | No | No | Yes |
| Integrated Gradients | Yes | No | Partial | NN only |

### Interaction Values (TreeExplainer only)

```python
shap_interaction = explainer.shap_interaction_values(X_test)
# Shape: (n_samples, n_features, n_features)
# Diagonal = main effects; off-diagonal = pairwise interactions
```

### Background Data Selection

Background data establishes the baseline (expected model output). Selection affects SHAP magnitudes but not relative importance.

- Random sample from training data: 100-500 samples
- Use `shap.kmeans(X_train, 50)` for efficient summarization
- For TreeExplainer with `tree_path_dependent`: no background data needed (uses tree structure)
- For DeepExplainer/KernelExplainer: 100-1000 samples balance accuracy vs speed

## Common Recipes

### Recipe: Model Debugging

```python
import numpy as np

# Find misclassified samples
predictions = model.predict(X_test)
errors = predictions != y_test
error_indices = np.where(errors)[0]

# Explain errors
for idx in error_indices[:3]:
    print(f"Sample {idx}: predicted={predictions[idx]}, actual={y_test.iloc[idx]}")
    shap.plots.waterfall(shap_values[idx])

# Check for data leakage: unexpected high-importance features
mean_abs_shap = np.abs(shap_values.values).mean(0)
top_features = X_test.columns[mean_abs_shap.argsort()[-5:]]
print(f"Top features (check for leakage): {list(top_features)}")
```

### Recipe: Fairness Analysis

```python
# Compare SHAP distributions across groups
group_a = shap_values[X_test["Sex"] == 0]
group_b = shap_values[X_test["Sex"] == 1]

shap.plots.bar({"Female": group_a, "Male": group_b})

# Check protected attribute importance
sex_importance = np.abs(shap_values[:, "Sex"].values).mean()
total_importance = np.abs(shap_values.values).mean()
print(f"Sex contribution: {sex_importance/total_importance:.1%} of total importance")
```

### Recipe: Production Caching

```python
import joblib

# Save explainer for reuse
joblib.dump(explainer, 'explainer.pkl')
explainer = joblib.load('explainer.pkl')

# Batch computation for API responses
def explain_batch(X_batch, explainer, top_n=5):
    sv = explainer(X_batch)
    results = []
    for i in range(len(X_batch)):
        top_idx = np.abs(sv.values[i]).argsort()[-top_n:]
        results.append({
            'prediction': sv.base_values[i] + sv.values[i].sum(),
            'top_features': {X_batch.columns[j]: sv.values[i][j] for j in top_idx}
        })
    return results
```

### Recipe: MLflow Integration

```python
import mlflow
import matplotlib.pyplot as plt

with mlflow.start_run():
    model = xgb.XGBClassifier().fit(X_train, y_train)
    explainer = shap.TreeExplainer(model)
    shap_values = explainer(X_test)

    shap.plots.beeswarm(shap_values, show=False)
    mlflow.log_figure(plt.gcf(), "shap_beeswarm.png")
    plt.close()

    for feat, imp in zip(X_test.columns, np.abs(shap_values.values).mean(0)):
        mlflow.log_metric(f"shap_{feat}", imp)
```

## Expected Outputs

| Output | Type | Description |
|--------|------|-------------|
| `shap_values` | `shap.Explanation` | Object with `.values` `(n_samples, n_features)`, `.base_values` (baseline), `.data` (input features) |
| Waterfall plot | matplotlib figure | Single-instance explanation showing feature contributions from base value to prediction |
| Beeswarm plot | matplotlib figure | Global summary: feature importance × direction for all samples |
| Bar plot | matplotlib figure | Mean absolute SHAP values per feature (global importance ranking) |
| Force plot | HTML/matplotlib | Interactive or static visualization of a single prediction |
| `mean_abs_shap` | `pd.Series` | Per-feature mean absolute SHAP value for ranking and reporting |

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| Very slow computation | Using KernelExplainer for tree model | Use `TreeExplainer` for tree-based models |
| Slow on large dataset | Computing all samples at once | Sample subset: `explainer(X_test[:1000])` or batch |
| SHAP values don't sum to prediction | Wrong model output type | Check `model_output` parameter; verify additivity |
| Log-odds vs probability confusion | Tree classifier defaults to log-odds | Use `TreeExplainer(model, model_output="probability")` |
| Plots too cluttered | Too many features shown | Set `max_display=10` or use feature clustering |
| DeepExplainer error | Background data too small | Use 100-1000 background samples |
| Memory error | Large dataset + many features | Reduce background data with `shap.kmeans(X, 50)` |
| Force plot not rendering | Missing JS in notebook | Run `shap.initjs()` at notebook start |
| Inconsistent importance across runs | KernelExplainer sampling variance | Increase `nsamples` or use deterministic explainer |
| Negative importance for relevant feature | Feature interactions or correlations | Use `feature_perturbation="interventional"` or scatter plots |

## Bundled Resources

- `references/theory.md` — Mathematical foundations: Shapley value formula, key properties (additivity, symmetry, dummy, monotonicity), computation algorithms (Tree SHAP, Kernel SHAP, Deep SHAP, Linear SHAP), conditional expectations (interventional vs observational), comparison with LIME/DeepLIFT/LRP/Integrated Gradients, interaction values, theoretical limitations

Not migrated from original: `references/explainers.md` (340 lines) — detailed constructor parameters, methods, and performance benchmarks for each explainer class. Explainer selection guide and common usage are covered inline in Workflow Step 1 and Key Parameters.

Not migrated from original: `references/plots.md` (508 lines) — comprehensive parameter reference for all 9 plot types with advanced customization (violin, decision, feature clustering). Main plot types are covered inline in Workflow Steps 3-6.

Not migrated from original: `references/workflows.md` (606 lines) — detailed step-by-step workflows for feature engineering, model comparison, deep learning explanation, production deployment, and time series. Core patterns are covered in Common Recipes; consult original for extended workflows.

## Best Practices

1. **Choose specialized explainers first** — `TreeExplainer` > `LinearExplainer` > `DeepExplainer` > `KernelExplainer`. Only use model-agnostic explainers when no specialized one exists
2. **Start global, then go local** — begin with beeswarm/bar for overall importance, then waterfall/scatter for individual predictions and feature relationships
3. **Use multiple visualizations** — different plots reveal different insights; combine global (beeswarm) + local (waterfall) + relationship (scatter)
4. **Select appropriate background data** — 100-500 representative samples from training data; use `shap.kmeans()` for efficiency
5. **Validate with domain knowledge** — unexpectedly high feature importance may indicate data leakage, not true predictive power
6. **Remember SHAP shows association, not causation** — a feature's high SHAP importance means the model uses it, not that it causally affects the outcome
7. **Consider feature correlations** — correlated features share SHAP importance; use `feature_perturbation="interventional"` for causal interpretation or feature clustering for grouped importance

## References

- Lundberg & Lee (2017). "A Unified Approach to Interpreting Model Predictions" (NeurIPS)
- Lundberg et al. (2020). "From local explanations to global understanding with explainable AI for trees" (Nature Machine Intelligence)
- Official documentation: https://shap.readthedocs.io/
- GitHub: https://github.com/shap/shap

## Related Skills

- **scikit-learn-machine-learning** — model training for SHAP analysis
- **matplotlib-scientific-plotting** — custom SHAP plot styling and export
- **statistical-analysis** — statistical testing to complement SHAP interpretation
