---
name: "pymc-bayesian-modeling"
description: "Bayesian modeling with PyMC 5. 8-step workflow: define model, set priors, define likelihood, sample (NUTS/ADVI), diagnose (R-hat, ESS, divergences), interpret posteriors, compare models (LOO/WAIC), predict. Hierarchical, logistic, GP model variants. Prior/posterior predictive checks."
license: "Apache-2.0"
---

# PyMC Bayesian Modeling

## Overview

PyMC is a Python library for Bayesian statistical modeling and probabilistic programming. It provides an expressive syntax for defining probabilistic models and efficient inference via MCMC (NUTS) and variational methods (ADVI). This skill covers the full Bayesian modeling cycle from model specification through diagnostics, comparison, and prediction.

## When to Use

- Estimating parameters with full uncertainty quantification (credible intervals, not just point estimates)
- Fitting hierarchical/multilevel models to grouped or nested data
- Performing prior and posterior predictive checks to validate model assumptions
- Comparing candidate models using information criteria (LOO-CV, WAIC)
- Building regression models (linear, logistic, Poisson) in a Bayesian framework
- Handling missing data or measurement error as latent parameters
- Modeling time series with autoregressive or random walk priors
- Generating posterior predictions for new observations with uncertainty bounds
- Use **Stan/PyStan** instead for compiled, more scalable Bayesian inference on large models; use **statsmodels** for frequentist statistical tests

## Prerequisites

- **Python packages**: `pymc >= 5.0`, `arviz`, `numpy`, `matplotlib`
- **Data**: NumPy arrays or pandas DataFrames with numeric columns
- **Environment**: CPU sufficient for most models; GPU via JAX backend for large models

```bash
pip install pymc arviz numpy matplotlib
# Optional: JAX backend for GPU acceleration
pip install pymc[jax]
```

## Quick Start

```python
import pymc as pm
import arviz as az
import numpy as np

# Simulate data
np.random.seed(42)
X = np.random.randn(100)
y = 2.5 + 1.3 * X + np.random.randn(100) * 0.5

# Build and fit model
with pm.Model() as model:
    alpha = pm.Normal("alpha", mu=0, sigma=5)
    beta = pm.Normal("beta", mu=0, sigma=5)
    sigma = pm.HalfNormal("sigma", sigma=1)
    mu = alpha + beta * X
    y_obs = pm.Normal("y_obs", mu=mu, sigma=sigma, observed=y)
    idata = pm.sample(1000, tune=1000, chains=4, random_seed=42)

print(az.summary(idata, var_names=["alpha", "beta", "sigma"]))
# Expected: alpha ~ 2.5, beta ~ 1.3, sigma ~ 0.5
```

## Workflow

### Step 1: Prepare Data

Standardize continuous predictors for better sampling efficiency. Use named coordinates for readable models and ArviZ integration.

```python
import pymc as pm
import arviz as az
import numpy as np

# Load data
X = np.random.randn(200, 3)  # 200 obs, 3 predictors
y = X @ np.array([1.0, -0.5, 0.3]) + np.random.randn(200) * 0.8

# Standardize predictors
X_mean, X_std = X.mean(axis=0), X.std(axis=0)
X_scaled = (X - X_mean) / X_std

# Define coordinates for named dimensions
coords = {
    "predictors": ["var1", "var2", "var3"],
    "obs_id": np.arange(len(y)),
}
print(f"Data shape: X={X_scaled.shape}, y={y.shape}")
```

### Step 2: Define Model and Set Priors

Specify the model structure inside a `pm.Model()` context. Use weakly informative priors, `dims` for named dimensions, and `HalfNormal` or `Exponential` for scale parameters.

```python
with pm.Model(coords=coords) as model:
    # Priors — weakly informative, not flat
    alpha = pm.Normal("alpha", mu=0, sigma=1)
    beta = pm.Normal("beta", mu=0, sigma=1, dims="predictors")
    sigma = pm.HalfNormal("sigma", sigma=1)

    # Linear predictor
    mu = alpha + pm.math.dot(X_scaled, beta)

    # Likelihood
    y_obs = pm.Normal("y_obs", mu=mu, sigma=sigma, observed=y, dims="obs_id")

# Inspect model variables
print(model.basic_RVs)  # Lists: [alpha, beta, sigma, y_obs]
```

### Step 3: Prior Predictive Check

Validate that priors produce plausible data ranges before fitting. Adjust priors if simulated data is unreasonable.

```python
with model:
    prior_pred = pm.sample_prior_predictive(samples=1000, random_seed=42)

# Check prior-implied data range
prior_y = prior_pred.prior_predictive["y_obs"].values.flatten()
print(f"Prior predictive range: [{prior_y.min():.1f}, {prior_y.max():.1f}]")
print(f"Observed data range:    [{y.min():.1f}, {y.max():.1f}]")

az.plot_ppc(prior_pred, group="prior", num_pp_samples=100)
```

### Step 4: Sample Posterior (MCMC)

Run NUTS sampling with multiple chains. Include `log_likelihood=True` if you plan model comparison later.

```python
with model:
    idata = pm.sample(
        draws=2000,
        tune=1000,
        chains=4,
        target_accept=0.9,
        random_seed=42,
        idata_kwargs={"log_likelihood": True},
    )

print(f"Posterior shape: {idata.posterior['beta'].shape}")
# Expected: (4 chains, 2000 draws, 3 predictors)
```

### Step 5: Diagnose Sampling

Check convergence before interpreting results. All three diagnostics (R-hat, ESS, divergences) must pass.

```python
# Summary with convergence diagnostics
summary = az.summary(idata, var_names=["alpha", "beta", "sigma"])
print(summary[["mean", "sd", "hdi_3%", "hdi_97%", "r_hat", "ess_bulk"]])

# R-hat convergence check
bad_rhat = summary[summary["r_hat"] > 1.01]
if len(bad_rhat) > 0:
    print(f"WARNING: {len(bad_rhat)} parameters with R-hat > 1.01")
    print(bad_rhat[["r_hat"]])

# Effective sample size check
low_ess = summary[summary["ess_bulk"] < 400]
if len(low_ess) > 0:
    print(f"WARNING: {len(low_ess)} parameters with ESS < 400")

# Divergence check
n_div = idata.sample_stats.diverging.sum().item()
total = len(idata.posterior.draw) * len(idata.posterior.chain)
print(f"Divergences: {n_div}/{total} ({n_div / total * 100:.2f}%)")

# Visual diagnostics — trace plots and rank plots
az.plot_trace(idata, var_names=["alpha", "beta", "sigma"])
az.plot_rank(idata, var_names=["alpha", "beta", "sigma"])
```

### Step 6: Posterior Predictive Check

Validate model fit by comparing simulated data from the posterior to observed data.

```python
with model:
    pm.sample_posterior_predictive(idata, extend_inferencedata=True, random_seed=42)

az.plot_ppc(idata, num_pp_samples=100)
# Blue = observed data, grey = posterior simulations
# Systematic deviations indicate model misspecification
```

### Step 7: Compare Models

Use LOO-CV or WAIC to compare candidate models. Lower information criterion is better.

```python
# Fit multiple models with log_likelihood=True, then compare
# Example: compare linear vs a second model
idatas = {"linear": idata}  # add more fitted models here

comparison = az.compare(idatas, ic="loo")
print(comparison[["rank", "elpd_loo", "p_loo", "d_loo", "weight"]])

# Check LOO reliability via Pareto-k diagnostics
loo_result = az.loo(idata, pointwise=True)
high_k = (loo_result.pareto_k > 0.7).sum().item()
print(f"Observations with Pareto-k > 0.7: {high_k}")
# Interpretation: Dloo < 2 = similar models; Dloo > 10 = strong evidence

az.plot_compare(comparison)
```

### Step 8: Generate Predictions

Produce posterior predictions for new data with full uncertainty propagation.

```python
X_new = np.array([[0.5, -1.0, 0.2]])
X_new_scaled = (X_new - X_mean) / X_std

with model:
    pm.set_data({"X_scaled": X_new_scaled})
    post_pred = pm.sample_posterior_predictive(
        idata.posterior, var_names=["y_obs"], random_seed=42
    )

y_pred = post_pred.posterior_predictive["y_obs"]
print(f"Predicted mean: {y_pred.mean().item():.3f}")
print(f"94% HDI: {az.hdi(y_pred, hdi_prob=0.94).values}")
```

## Key Parameters

| Parameter | Default | Range / Options | Effect |
|-----------|---------|-----------------|--------|
| `draws` | `1000` | `500`-`10000` | Number of posterior samples per chain |
| `tune` | `1000` | `500`-`5000` | Warmup iterations (discarded); increase for complex posteriors |
| `chains` | `4` | `2`-`8` | Number of independent chains; minimum 4 for reliable R-hat |
| `cores` | all CPUs | `1`-`N` | Parallel chains; set equal to `chains` for full parallelism |
| `target_accept` | `0.8` | `0.8`-`0.99` | NUTS acceptance rate; increase to reduce divergences |
| `init` | `"auto"` | `"adapt_diag"`, `"jitter+adapt_diag"`, `"advi"` | Initialization strategy for sampler |
| `random_seed` | `None` | any int | Seed for reproducibility |
| `idata_kwargs` | `{}` | `{"log_likelihood": True}` | Store log-likelihood for LOO/WAIC model comparison |
| `method` (pm.fit) | `"advi"` | `"advi"`, `"fullrank_advi"`, `"svgd"` | Variational inference algorithm |
| `n` (pm.fit) | `10000` | `5000`-`100000` | VI optimization iterations |
| `samples` (prior pred) | `500` | `100`-`5000` | Prior predictive samples for validation |

## Key Concepts

### Prior/Distribution Selection Guide

| Distribution | Use When | Key Parameters |
|-------------|----------|----------------|
| `Normal(mu, sigma)` | Unbounded real-valued parameter (standardized data) | `mu`: center, `sigma`: spread |
| `HalfNormal(sigma)` | Scale/standard deviation parameter (positive) | `sigma`: spread of positive half |
| `Exponential(lam)` | Scale parameter, alternative to HalfNormal | `lam`: rate (1/mean) |
| `StudentT(nu, mu, sigma)` | Robust alternative to Normal (outlier-resistant) | `nu`: degrees of freedom (<10 = heavier tails) |
| `Beta(alpha, beta)` | Probability or proportion in [0,1] | `alpha=beta=2`: weakly informative |
| `Gamma(alpha, beta)` | Positive parameter (rate, concentration) | `alpha`: shape, `beta`: rate |
| `LogNormal(mu, sigma)` | Positive parameter with multiplicative effects | `mu`, `sigma`: of underlying Normal |
| `LKJCorr(n, eta)` | Correlation matrix prior | `eta=1`: uniform; `eta>1`: prefer identity |
| `Dirichlet(a)` | Probability vector (sums to 1) | `a`: concentration; uniform if all equal |
| `Bernoulli(p / logit_p)` | Binary outcome likelihood | Use `logit_p` for numerical stability |
| `Poisson(mu)` | Count data (equidispersed) | `mu`: rate; use NegBinomial if overdispersed |
| `NegativeBinomial(mu, alpha)` | Overdispersed count data | `alpha`: dispersion (smaller = more overdispersion) |

### Diagnostic Thresholds

| Metric | Threshold | Interpretation | Action if Failed |
|--------|-----------|---------------|------------------|
| R-hat | < 1.01 | Chains converged | Run longer chains; check multimodality |
| ESS bulk | > 400 | Sufficient independent samples | Increase `draws`; reparameterize |
| ESS tail | > 400 | Reliable tail estimates | Increase `draws` |
| Divergences | 0 | NUTS explored successfully | Increase `target_accept`; non-centered param. |
| Pareto-k (LOO) | < 0.7 | LOO estimate reliable | Use WAIC or k-fold CV |
| Max tree depth | < 10 | No trajectory truncation | Reparameterize or increase `max_treedepth` |

### Model Variants Overview

| Problem Type | Recipe | Likelihood | Key Feature |
|-------------|--------|------------|-------------|
| Grouped/nested data | Hierarchical Model | Normal (varies) | Non-centered parameterization, partial pooling |
| Binary outcome | Logistic Regression | Bernoulli | `logit_p` link function |
| Nonlinear/spatial | Gaussian Process | Normal | Kernel-based covariance, flexible shape |
| Count data | (use Poisson in Workflow) | Poisson / NegBinomial | Log link; NegBinomial for overdispersion |
| Time series | (see references) | AR / GaussianRandomWalk | Autoregressive coefficients |
| Mixture/clustering | (see references) | Mixture / NormalMixture | Component weights via Dirichlet |

## Common Recipes

### Recipe: Hierarchical Model

When to use: data has natural grouping (patients within hospitals, students within schools). Non-centered parameterization avoids divergences from funnel geometry.

```python
import pymc as pm
import arviz as az
import numpy as np

n_groups, n_per_group = 5, 30
group_idx = np.repeat(np.arange(n_groups), n_per_group)
group_names = [f"group_{i}" for i in range(n_groups)]

# Simulated grouped data
true_alphas = np.random.normal(3.0, 1.5, n_groups)
y_obs = np.random.normal(true_alphas[group_idx], 0.5)

with pm.Model(coords={"groups": group_names}) as hierarchical_model:
    # Hyperpriors (population level)
    mu_alpha = pm.Normal("mu_alpha", mu=0, sigma=5)
    sigma_alpha = pm.HalfNormal("sigma_alpha", sigma=2)

    # Non-centered parameterization
    alpha_offset = pm.Normal("alpha_offset", mu=0, sigma=1, dims="groups")
    alpha = pm.Deterministic(
        "alpha", mu_alpha + sigma_alpha * alpha_offset, dims="groups"
    )

    # Observation level
    sigma = pm.HalfNormal("sigma", sigma=1)
    y = pm.Normal("y", mu=alpha[group_idx], sigma=sigma, observed=y_obs)

    idata_hier = pm.sample(2000, tune=1000, target_accept=0.95, random_seed=42)

print(az.summary(idata_hier, var_names=["mu_alpha", "sigma_alpha", "alpha", "sigma"]))
```

### Recipe: Logistic Regression

When to use: binary outcome variable (success/failure, disease/healthy). Use `logit_p` for numerical stability instead of computing probabilities directly.

```python
import pymc as pm
import arviz as az
import numpy as np

# Simulated binary outcome
np.random.seed(42)
n, p = 200, 3
X_lr = np.random.randn(n, p)
true_beta = np.array([1.0, -0.5, 0.3])
prob = 1 / (1 + np.exp(-(0.2 + X_lr @ true_beta)))
y_binary = np.random.binomial(1, prob)

with pm.Model() as logistic_model:
    alpha = pm.Normal("alpha", mu=0, sigma=2)
    beta = pm.Normal("beta", mu=0, sigma=2, shape=p)
    logit_p = alpha + pm.math.dot(X_lr, beta)
    y = pm.Bernoulli("y", logit_p=logit_p, observed=y_binary)

    idata_logit = pm.sample(2000, tune=1000, target_accept=0.9, random_seed=42)

summary = az.summary(idata_logit, var_names=["alpha", "beta"])
print(summary[["mean", "sd", "hdi_3%", "hdi_97%"]])
# Odds ratios
beta_samples = idata_logit.posterior["beta"].values.reshape(-1, p)
print(f"Odds ratios (median): {np.median(np.exp(beta_samples), axis=0)}")
```

### Recipe: Gaussian Process

When to use: modeling unknown nonlinear functions, spatial data, or smooth latent processes. Computationally expensive for n > 1000; consider sparse approximations for larger datasets.

```python
import pymc as pm
import arviz as az
import numpy as np

# Simulated nonlinear data
np.random.seed(42)
X_gp = np.sort(np.random.uniform(0, 10, 60))[:, None]
y_gp = np.sin(X_gp[:, 0]) + np.random.randn(60) * 0.3

with pm.Model() as gp_model:
    # GP hyperparameters
    ls = pm.Gamma("lengthscale", alpha=2, beta=1)
    eta = pm.HalfNormal("amplitude", sigma=2)
    sigma_noise = pm.HalfNormal("noise", sigma=0.5)

    # Covariance function
    cov = eta**2 * pm.gp.cov.Matern52(1, ls=ls)
    gp = pm.gp.Marginal(cov_func=cov)

    # Marginal likelihood
    y_ = gp.marginal_likelihood("y", X=X_gp, y=y_gp, sigma=sigma_noise)
    idata_gp = pm.sample(1000, tune=1000, target_accept=0.9, random_seed=42)

# Predict on new points
X_new_gp = np.linspace(0, 10, 100)[:, None]
with gp_model:
    f_pred = gp.conditional("f_pred", X_new_gp)
    pred_samples = pm.sample_posterior_predictive(idata_gp, var_names=["f_pred"])

print(f"GP predictions shape: {pred_samples.posterior_predictive['f_pred'].shape}")
```

## Expected Outputs

- **Trace plots** (`az.plot_trace`) -- chain mixing visualization; healthy chains look like "fuzzy caterpillars"
- **Posterior summary** (`az.summary`) -- mean, SD, HDI, R-hat, ESS per parameter
- **Prior/posterior predictive plots** (`az.plot_ppc`) -- simulated vs observed data distributions
- **Forest plots** (`az.plot_forest`) -- coefficient estimates with credible intervals
- **Model comparison table** (`az.compare`) -- ranked models with LOO/WAIC, weights, warnings
- **Rank plots** (`az.plot_rank`) -- uniform histograms indicate good mixing
- **Energy plot** (`az.plot_energy`) -- HMC energy transition diagnostics
- **InferenceData file** (`idata.to_netcdf("results.nc")`) -- serialized results for later analysis

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| Divergent transitions | Posterior geometry difficult for NUTS (funnels, ridges) | Increase `target_accept=0.95`; use non-centered parameterization; add stronger priors |
| Low ESS (< 400) | High autocorrelation between samples | Increase `draws=5000`; reparameterize to reduce correlation; try QR decomposition for correlated predictors |
| R-hat > 1.01 | Chains have not converged | Increase `tune=2000, draws=5000`; check for multimodality; initialize with ADVI |
| Slow sampling | Complex posterior or large dataset | Use ADVI for initialization; reduce model complexity; increase `cores`; try JAX backend |
| Pareto-k > 0.7 in LOO | Influential observations affecting LOO estimate | Use WAIC instead; investigate influential points; consider k-fold CV |
| Hit max tree depth | Model geometry requires long trajectories | Reparameterize model; increase `max_treedepth` parameter |
| `SamplingError` at start | Poor initialization | Try `init="adapt_diag"` or `init="jitter+adapt_diag"`; provide `initvals` via MAP |
| Biased posterior (prior dominates) | Priors too strong relative to data | Weaken priors (increase sigma); check prior predictive; verify data is correctly passed |
| `ValueError: logp = -inf` | Parameter hit impossible region | Check data for NaN/Inf; ensure positive params use `HalfNormal`/`Gamma`; verify likelihood matches data type |

## Best Practices

1. **Use weakly informative priors**, not flat priors. Flat priors (Uniform over large ranges) cause sampling difficulties and are rarely appropriate.
2. **Always run prior predictive checks** before fitting. If prior-implied data is implausible, adjust priors before sampling.
3. **Standardize continuous predictors** to mean=0, sd=1 for better NUTS geometry and faster sampling.
4. **Use non-centered parameterization** for hierarchical models: `offset ~ Normal(0,1); param = mu + sigma * offset` instead of `param ~ Normal(mu, sigma)`.
5. **Run at least 4 chains** for reliable R-hat and ESS diagnostics. Never trust a single chain.
6. **Check all three diagnostics** (R-hat < 1.01, ESS > 400, 0 divergences) before interpreting posteriors.
7. **Include `log_likelihood=True`** when fitting if you plan to compare models via LOO or WAIC.
8. **Use `dims` instead of `shape`** for named dimensions -- integrates with ArviZ for labeled summaries and subsetting.
9. **Report credible intervals** (HDI), not just point estimates. The posterior distribution is the result, not a single number.
10. **Save results** with `idata.to_netcdf("results.nc")` for reproducibility and later re-analysis.

## Bundled Resources

Two reference files provide deeper detail for on-demand consultation:

- **`references/distributions_inference.md`** -- Distribution catalog organized by category (continuous, discrete, multivariate, mixture, time series, special/modifiers) with full parameter signatures, support, and common uses. Sampling and inference methods (NUTS, Metropolis, Slice, CompoundStep, SMC, ADVI, fullrank ADVI, SVGD, MAP) with code examples and a method selection guide table. Reparameterization tricks (non-centered, QR decomposition) with code.
  Covers: consolidated from original `references/distributions.md` (320 lines) and `references/sampling_inference.md` (424 lines).
  Relocated inline: core distribution selection guide table (Key Concepts), diagnostic threshold table (Key Concepts), basic ADVI usage (Recipe: Variational Inference in original, covered in references here).
  Omitted: shape broadcasting examples (trivial NumPy-style `shape=5`), basic `dims` usage (covered in Workflow Step 2), prior predictive sampling (covered in Workflow Step 3).

- **`references/advanced_workflows.md`** -- Model comparison workflow (LOO, WAIC, Pareto-k reliability checks, model averaging with weighted predictions), comprehensive diagnostic report generation (trace plots, rank plots, autocorrelation, energy, ESS evolution), prior-posterior comparison patterns, data preparation best practices (standardization, centering, missing data imputation), prior selection guidelines (weakly informative vs informative with domain knowledge), named dimensions (`dims`) usage with xarray subsetting, save/load patterns (NetCDF, pickle). Mixture model pattern.
  Covers: consolidated from original `references/workflows.md` (526 lines).
  Relocated inline: core diagnostic checking logic (Workflow Step 5), model comparison basics (Workflow Step 7), prior predictive check (Workflow Step 3), linear/logistic/hierarchical model code (Recipes).
  Omitted: complete monolithic workflow template (redundant with 8-step Workflow section).

### Per-reference-file disposition (all originals)

**Original `references/` (3 files):**
1. `distributions.md` (320 lines) -> consolidated with `sampling_inference.md` into new `references/distributions_inference.md`
2. `sampling_inference.md` (424 lines) -> consolidated with `distributions.md` into new `references/distributions_inference.md`
3. `workflows.md` (526 lines) -> migrated as new `references/advanced_workflows.md`

**Original `scripts/` (2 files):**
1. `model_diagnostics.py` (350 lines) -> `check_diagnostics()` logic (R-hat, ESS, divergences, tree depth checks) inlined in Workflow Step 5; `create_diagnostic_report()` plot generation patterns described in Expected Outputs and referenced in `references/advanced_workflows.md`; `compare_prior_posterior()` utility covered in `references/advanced_workflows.md`
2. `model_comparison.py` (387 lines) -> `compare_models()` and `check_loo_reliability()` patterns inlined in Workflow Step 7 (using `az.compare` and `az.loo` directly); `model_averaging()` pattern covered in `references/advanced_workflows.md`; `cross_validation_comparison()` guidance covered in `references/advanced_workflows.md`; `plot_model_comparison()` is a thin wrapper around `az.plot_compare` (inlined in Step 7)

## Related Skills

- **arviz (planned)** -- posterior visualization and diagnostics; PyMC returns ArviZ InferenceData objects
- **bambi (planned)** -- formula-based interface to PyMC (R-style `y ~ x1 + x2` syntax); simpler API for standard GLMs
- **numpyro (planned)** -- JAX-based probabilistic programming; faster NUTS via hardware acceleration
- **statsmodels-statistical-modeling** -- frequentist regression and GLMs; use when Bayesian framework is not needed
- **scikit-learn-machine-learning** -- ML classification/regression; use when prediction accuracy matters more than uncertainty quantification

## References

- [PyMC documentation](https://www.pymc.io/projects/docs/en/stable/) -- official API reference and tutorials
- [PyMC GitHub](https://github.com/pymc-devs/pymc) -- source code and issue tracker
- [ArviZ documentation](https://python.arviz.org/en/stable/) -- posterior analysis and visualization
- [Bayesian Modeling and Computation in Python](https://bayesiancomputationbook.com/) -- textbook using PyMC
- [PyMC examples gallery](https://www.pymc.io/projects/examples/en/latest/) -- curated notebook collection
