# PyMC — Advanced Workflows Reference

## Model Comparison (LOO, WAIC, Pareto-k, Model Averaging)

Compare candidate models using information criteria. Ensure all models are sampled with `idata_kwargs={"log_likelihood": True}`.

```python
import pymc as pm
import arviz as az
import numpy as np

# Assume multiple models fitted with log_likelihood=True
# idatas = {"linear": idata_linear, "interaction": idata_interaction, "hierarchical": idata_hier}

# LOO-CV comparison (preferred over WAIC)
comparison = az.compare(idatas, ic="loo")
print(comparison)

# WAIC comparison (alternative)
comparison_waic = az.compare(idatas, ic="waic")

# Visualize comparison — ELPD differences with standard errors
az.plot_compare(comparison)
plt.show()
```

### Pareto-k Reliability Checks

Pareto-k diagnostics indicate LOO estimate reliability per observation. Values > 0.7 signal unreliable LOO estimates.

```python
for name, idata in idatas.items():
    loo = az.loo(idata, pointwise=True)
    high_pareto_k = (loo.pareto_k > 0.7).sum().item()
    moderate_k = ((loo.pareto_k > 0.5) & (loo.pareto_k <= 0.7)).sum().item()
    if high_pareto_k > 0:
        print(f"Warning: {name} has {high_pareto_k} observations with Pareto-k > 0.7")
        print(f"  Consider: moment matching, WAIC, or k-fold CV for these points")
    if moderate_k > 0:
        print(f"Note: {name} has {moderate_k} observations with Pareto-k in (0.5, 0.7]")
    else:
        print(f"OK: {name} — all Pareto-k values acceptable")
```

### Model Averaging with Weighted Predictions

Combine predictions from multiple models using pseudo-BMA or stacking weights.

```python
# Extract model weights from comparison table
weights = comparison["weight"].values

print("Model probabilities:")
for name, weight in zip(comparison.index, weights):
    print(f"  {name}: {weight:.2%}")

# Weighted prediction averaging
def weighted_predictions(idatas, weights):
    """Average posterior predictions across models using comparison weights."""
    preds = []
    for (name, idata), weight in zip(idatas.items(), weights):
        pred = idata.posterior_predictive["y_obs"].mean(dim=["chain", "draw"])
        preds.append(weight * pred)
    return sum(preds)

averaged_pred = weighted_predictions(idatas, weights)
```

## Diagnostic Report Generation

Comprehensive diagnostic visualization beyond the basic checks in Workflow Step 5.

### Trace Plots and Rank Plots

```python
import matplotlib.pyplot as plt

# Trace plots — chain mixing; healthy chains look like "fuzzy caterpillars"
az.plot_trace(idata, var_names=["alpha", "beta", "sigma"])
plt.tight_layout()
plt.show()

# Rank plots — uniform histograms indicate good mixing across chains
az.plot_rank(idata, var_names=["alpha", "beta", "sigma"])
plt.tight_layout()
plt.show()
```

### Autocorrelation, Energy, and ESS Evolution

```python
# Autocorrelation — should decay quickly to zero
az.plot_autocorr(idata, var_names=["alpha", "beta", "sigma"])
plt.tight_layout()
plt.show()

# Energy plot — overlapping marginal/transition energy distributions = good exploration
az.plot_energy(idata)
plt.show()

# ESS evolution — ESS should grow linearly with draws
az.plot_ess(idata, var_names=["alpha", "beta", "sigma"], kind="evolution")
plt.tight_layout()
plt.show()
```

### Comprehensive Diagnostic Function

```python
def diagnose_sampling(idata, var_names=None):
    """Comprehensive sampling diagnostics report."""
    summary = az.summary(idata, var_names=var_names)
    bad_rhat = summary[summary["r_hat"] > 1.01]
    low_ess = summary[summary["ess_bulk"] < 400]
    divergences = idata.sample_stats.diverging.sum().item()
    max_td = idata.sample_stats.tree_depth.max().item()
    hits_max = (idata.sample_stats.tree_depth == max_td).sum().item()

    print(f"R-hat > 1.01: {len(bad_rhat)} vars | ESS < 400: {len(low_ess)} vars")
    print(f"Divergences: {divergences} | Max treedepth hits: {hits_max} (max={max_td})")
    if len(bad_rhat): print(bad_rhat[["r_hat"]])
    if divergences: print("  Fix: increase target_accept, reparameterize, or stronger priors")
    return summary

diagnose_sampling(idata, var_names=["alpha", "beta", "sigma"])
```

## Prior-Posterior Comparison

Compare prior and posterior distributions to assess how much the data updated beliefs.

```python
with model:
    prior_pred = pm.sample_prior_predictive(samples=1000, random_seed=42)

# Overlay prior vs posterior for each parameter
fig, axes = plt.subplots(1, 3, figsize=(15, 4))
for i, var in enumerate(["alpha", "beta", "sigma"]):
    axes[i].hist(prior_pred.prior[var].values.flatten(), bins=50, alpha=0.5, density=True, label="Prior")
    axes[i].hist(idata.posterior[var].values.flatten(), bins=50, alpha=0.5, density=True, label="Posterior")
    axes[i].set_title(var)
    axes[i].legend()
plt.tight_layout()
plt.show()
```

## Data Preparation Best Practices

### Standardization with Back-Transformation

```python
X_mean, X_std = X.mean(axis=0), X.std(axis=0)
X_scaled = (X - X_mean) / X_std

with pm.Model() as model:
    beta_scaled = pm.Normal("beta_scaled", 0, 1, shape=X.shape[1])
    alpha = pm.Normal("alpha", 0, 1)
    sigma = pm.HalfNormal("sigma", 1)
    mu = alpha + pm.math.dot(X_scaled, beta_scaled)
    y_obs = pm.Normal("y_obs", mu=mu, sigma=sigma, observed=y)
# Back-transform: beta_original = beta_scaled / X_std
# alpha_original = alpha - sum(beta_scaled * X_mean / X_std)
```

### Centering for Simpler Priors

```python
X_centered, y_centered = X - X.mean(axis=0), y - y.mean()

with pm.Model() as model:
    alpha = pm.Normal("alpha", mu=0, sigma=1)  # Near 0 when centered
    beta = pm.Normal("beta", mu=0, sigma=1, shape=X.shape[1])
    mu = alpha + pm.math.dot(X_centered, beta)
    sigma = pm.HalfNormal("sigma", sigma=1)
    y_obs = pm.Normal("y_obs", mu=mu, sigma=sigma, observed=y_centered)
```

### Missing Data Imputation

```python
missing_idx = np.isnan(X)
X_observed = np.where(missing_idx, 0, X)  # Placeholder for observed positions

with pm.Model() as model:
    # Prior for missing values — impute as latent parameters
    X_missing = pm.Normal("X_missing", mu=0, sigma=1, shape=missing_idx.sum())
    X_complete = pm.math.switch(missing_idx.flatten(), X_missing, X_observed.flatten())
    # ... rest of model using X_complete ...
```

## Prior Selection Guidelines

### Weakly Informative Priors

Use when you have limited domain knowledge. These constrain the posterior to a plausible range without imposing strong opinions.

```python
# For standardized predictors — unit scale
beta = pm.Normal("beta", mu=0, sigma=1)

# For scale parameters — positive, weakly constrained
sigma = pm.HalfNormal("sigma", sigma=1)

# For probabilities — slight preference for middle values
p = pm.Beta("p", alpha=2, beta=2)
```

### Informative Priors from Domain Knowledge

Use when literature or expert knowledge constrains parameters.

```python
# Effect size from literature: Cohen's d ~ 0.3
beta = pm.Normal("beta", mu=0.3, sigma=0.1)

# Physical constraint: probability between 0.7-0.9
p = pm.Beta("p", alpha=8, beta=2)  # Always validate with prior predictive check!

# Prior predictive validation
with model:
    prior_pred = pm.sample_prior_predictive(samples=1000)
print(f"Prior range: [{prior_pred.prior_predictive['y'].min():.2f}, "
      f"{prior_pred.prior_predictive['y'].max():.2f}]")
print(f"Observed range: [{y_obs.min():.2f}, {y_obs.max():.2f}]")
```

## Named Dimensions (`dims`) with xarray Subsetting

Using `dims` instead of `shape` enables labeled access via xarray for readable analysis.

```python
import pandas as pd

coords = {
    "predictors": ["age", "income", "education"],
    "groups": ["A", "B", "C"],
}

with pm.Model(coords=coords) as model:
    beta = pm.Normal("beta", mu=0, sigma=1, dims="predictors")
    alpha = pm.Normal("alpha", mu=0, sigma=1, dims="groups")
    # ... likelihood with dims=["groups", "obs_id"] ...

idata = pm.sample()

# xarray subsetting — select by label, not index
beta_age = idata.posterior["beta"].sel(predictors="age")
group_A = idata.posterior["alpha"].sel(groups="A")
group_means = idata.posterior["alpha"].mean(dim=["chain", "draw"])
```

## Save/Load Patterns

### NetCDF (Recommended for InferenceData)

```python
# Save full InferenceData (posterior, prior, diagnostics, etc.)
idata.to_netcdf("results.nc")

# Load later for continued analysis
loaded_idata = az.from_netcdf("results.nc")
print(az.summary(loaded_idata))
```

### Pickle (Model + InferenceData for Predictions)

```python
import pickle

# Save model object + results for later predictions
with open("model.pkl", "wb") as f:
    pickle.dump({"model": model, "idata": idata}, f)

# Load model for new predictions
with open("model.pkl", "rb") as f:
    saved = pickle.load(f)
    model = saved["model"]
    idata = saved["idata"]
```

## Mixture Models

Fit finite mixture models with Dirichlet-distributed component weights.

```python
n_components = 3

with pm.Model() as mixture_model:
    # Component weights — Dirichlet prior (uniform over simplex)
    w = pm.Dirichlet("w", a=np.ones(n_components))

    # Component parameters
    mu = pm.Normal("mu", mu=0, sigma=10, shape=n_components)
    sigma = pm.HalfNormal("sigma", sigma=1, shape=n_components)

    # Mixture likelihood
    components = [
        pm.Normal.dist(mu=mu[i], sigma=sigma[i]) for i in range(n_components)
    ]
    y = pm.Mixture("y", w=w, comp_dists=components, observed=y_obs)

    idata_mix = pm.sample(2000, tune=2000, target_accept=0.95, random_seed=42)

print(az.summary(idata_mix, var_names=["w", "mu", "sigma"]))
# Note: component labels may switch across chains (label switching).
# Use ordered mu or post-processing to resolve.
```

---

Condensed from workflows.md (526 lines). Retained: model comparison workflow (LOO, WAIC, Pareto-k reliability, model averaging with weighted predictions), comprehensive diagnostic report generation (trace, rank, autocorrelation, energy, ESS evolution plots + diagnostic function), prior-posterior comparison patterns, data preparation (standardization with back-transformation, centering, missing data imputation), prior selection guidelines (weakly informative vs informative with domain knowledge), named dimensions with xarray subsetting, save/load patterns (NetCDF, pickle), mixture model pattern. Omitted: complete monolithic workflow template (lines 9-136, redundant with SKILL.md 8-step Workflow section), linear/logistic/hierarchical/Poisson/time-series model code (lines 142-226, relocated to SKILL.md Common Recipes and Workflow), core diagnostic checking logic (lines 69-89, relocated to SKILL.md Workflow Step 5), basic model comparison (lines 354-378, relocated to SKILL.md Workflow Step 7), prior predictive check (lines 43-51, relocated to SKILL.md Workflow Step 3).
