# Bayesian Statistics Guide

## When to Use Bayesian Methods

- You have **prior information** to incorporate (pilot data, literature, expert knowledge)
- You want **direct probability statements** about parameters ("95% probability the effect is between 3 and 8")
- **Sample size is small** and frequentist tests lack power
- You need to **quantify evidence for the null hypothesis** (Bayes Factors)
- The model is **complex** (hierarchical, missing data, mixture models)
- You want to **update analysis sequentially** as data arrives

**Frequentist may be sufficient when**: standard analysis with large sample, no prior information, computational resources limited, reviewers unfamiliar with Bayesian methods.

## Core Framework

### Bayes' Theorem

```
P(theta | data) = P(data | theta) * P(theta) / P(data)
  posterior     =   likelihood    *   prior    / evidence
```

- **Prior** P(theta): What we believe before seeing data
- **Likelihood** P(data | theta): How well the data fits each parameter value
- **Posterior** P(theta | data): Updated belief after seeing data
- **Evidence** P(data): Normalizing constant (marginal likelihood)

### Prior Specification

| Prior Type | When to Use | Example |
|------------|-------------|---------|
| **Non-informative** | No prior knowledge; want data to dominate | Uniform, Jeffreys |
| **Weakly informative** | Constrain to reasonable range; recommended default | Normal(0, 10), Half-Normal(0, 5) |
| **Informative** | Strong prior knowledge from literature/pilot | Normal(mu_lit, sigma_lit) |

**Best practice**: Use weakly informative priors as default. Non-informative (flat) priors can lead to improper posteriors and non-sensible results; they are generally not recommended in modern Bayesian practice.

Common weakly informative choices:
- Effect size: Normal(0, 1) or Cauchy(0, 0.707)
- Variance: Half-Cauchy(0, 1) or Half-Normal(0, 5)
- Correlation: Uniform(-1, 1) or Beta(2, 2)

### Credible Intervals vs Confidence Intervals

| Credible Interval (Bayesian) | Confidence Interval (Frequentist) |
|-----------------------------|----------------------------------|
| "95% probability parameter is in this interval" | "95% of such intervals contain the true parameter" |
| Direct probability statement | Procedure-level guarantee |
| Width depends on prior + data | Width depends on data only |
| Narrower with informative priors | Fixed for given n |

**Types of credible intervals**:
- **Equal-Tailed Interval (ETI)**: 2.5th to 97.5th percentile. Simple; may not include mode for skewed distributions
- **Highest Density Interval (HDI)**: Narrowest interval containing 95% of distribution. Always includes mode; better for skewed distributions

```python
import arviz as az
import numpy as np

# Equal-tailed interval
eti = np.percentile(posterior_samples, [2.5, 97.5])

# HDI (preferred for skewed posteriors)
hdi = az.hdi(posterior_samples, hdi_prob=0.95)
```

## Prior Sensitivity Analysis

**Always conduct** sensitivity analysis to test how results change with different priors.

**Process**:
1. Fit model with default/planned prior
2. Fit model with more diffuse prior (wider)
3. Fit model with more concentrated prior (narrower)
4. Compare posterior distributions

**Interpretation**:
- If results are similar across priors: evidence is robust, data dominate
- If results differ substantially: data are not strong enough to overwhelm prior; interpret with caution

```python
import pymc as pm
import arviz as az

traces = {}
prior_configs = {
    'weakly_informative': {'mu': 0, 'sigma': 1},
    'diffuse':            {'mu': 0, 'sigma': 10},
    'informative':        {'mu': 0.5, 'sigma': 0.3},
}

for name, cfg in prior_configs.items():
    with pm.Model():
        effect = pm.Normal('effect', mu=cfg['mu'], sigma=cfg['sigma'])
        sigma = pm.HalfNormal('sigma', sigma=5)
        y_obs = pm.Normal('y', mu=effect, sigma=sigma, observed=data)
        traces[name] = pm.sample(2000, tune=1000, return_inferencedata=True)

# Compare posteriors visually
for name, trace in traces.items():
    summary = az.summary(trace, var_names=['effect'])
    print(f"{name}: mean={summary['mean'].values[0]:.3f}, "
          f"hdi_3%={summary['hdi_3%'].values[0]:.3f}, "
          f"hdi_97%={summary['hdi_97%'].values[0]:.3f}")
```

## Bayesian Hypothesis Testing

### Bayes Factors

BF10 = P(data | H1) / P(data | H0)

| BF10 | Evidence for H1 |
|------|-----------------|
| 1-3 | Anecdotal |
| 3-10 | Moderate |
| 10-30 | Strong |
| 30-100 | Very strong |
| > 100 | Extreme / Decisive |

BF01 = 1/BF10 provides evidence for H0. For example, BF10 = 0.10 means H0 is 10x more likely than H1.

**Advantages over p-values**:
1. Can provide evidence for null hypothesis (not just "fail to reject")
2. Not dependent on sampling intentions (no "peeking" problem)
3. Directly quantifies evidence ratio
4. Can be updated with additional data

### Region of Practical Equivalence (ROPE)

ROPE defines a range of negligible effect sizes, directly testing for practical significance rather than just statistical significance.

**Process**:
1. Define ROPE bounds (e.g., d in [-0.1, 0.1] for negligible effects)
2. Calculate percentage of posterior inside ROPE
3. Decision rules:
   - >95% of posterior in ROPE: Accept practical equivalence (effect is negligible)
   - >95% of posterior outside ROPE: Reject equivalence (effect is meaningful)
   - Otherwise: Inconclusive

```python
import numpy as np

# Define ROPE for effect size
rope_lower, rope_upper = -0.1, 0.1

# Calculate % of posterior in ROPE
posterior_d = trace.posterior['effect'].values.flatten()
in_rope = np.mean((posterior_d > rope_lower) & (posterior_d < rope_upper))
outside_rope = 1 - in_rope

print(f"{in_rope*100:.1f}% of posterior in ROPE [{rope_lower}, {rope_upper}]")
print(f"{outside_rope*100:.1f}% of posterior outside ROPE")

if in_rope > 0.95:
    print("Decision: Accept practical equivalence")
elif outside_rope > 0.95:
    print("Decision: Effect is practically meaningful")
else:
    print("Decision: Inconclusive")
```

**ROPE vs. Bayes Factor**: ROPE tests practical significance (is the effect large enough to matter?), while Bayes Factor tests statistical evidence (which hypothesis is better supported?). They address different questions and can be used together.

## Common Bayesian Analyses

### Bayesian t-test

```python
import pymc as pm
import arviz as az
import numpy as np

with pm.Model() as ttest_model:
    # Priors
    mu1 = pm.Normal('mu_group1', mu=0, sigma=10)
    mu2 = pm.Normal('mu_group2', mu=0, sigma=10)
    sigma = pm.HalfNormal('sigma', sigma=10)

    # Likelihood
    y1 = pm.Normal('y1', mu=mu1, sigma=sigma, observed=group_a)
    y2 = pm.Normal('y2', mu=mu2, sigma=sigma, observed=group_b)

    # Derived quantity
    diff = pm.Deterministic('difference', mu1 - mu2)

    # Sample
    trace = pm.sample(2000, tune=1000, return_inferencedata=True)

# Results
print(az.summary(trace, var_names=['mu_group1', 'mu_group2', 'difference']))
prob_greater = np.mean(trace.posterior['difference'].values > 0)
print(f"P(mu1 > mu2 | data) = {prob_greater:.3f}")

az.plot_posterior(trace, var_names=['difference'], ref_val=0)
```

### Bayesian ANOVA (Hierarchical Group Comparison)

```python
import pymc as pm
import arviz as az
import numpy as np

# group_idx: integer array mapping each observation to group (0, 1, ..., n_groups-1)
# data: observed continuous values

with pm.Model() as anova_model:
    # Hyperpriors (partial pooling)
    mu_global = pm.Normal('mu_global', mu=0, sigma=10)
    sigma_between = pm.HalfNormal('sigma_between', sigma=5)
    sigma_within = pm.HalfNormal('sigma_within', sigma=5)

    # Group means (hierarchical)
    group_means = pm.Normal('group_means',
                            mu=mu_global,
                            sigma=sigma_between,
                            shape=n_groups)

    # Likelihood
    y = pm.Normal('y',
                  mu=group_means[group_idx],
                  sigma=sigma_within,
                  observed=data)

    trace = pm.sample(2000, tune=1000, return_inferencedata=True)

# Posterior contrasts (pairwise differences)
means = trace.posterior['group_means']
contrast_0_1 = means[:, :, 0] - means[:, :, 1]
contrast_0_2 = means[:, :, 0] - means[:, :, 2]

print(f"P(group0 > group1) = {np.mean(contrast_0_1.values > 0):.3f}")
print(f"P(group0 > group2) = {np.mean(contrast_0_2.values > 0):.3f}")

az.plot_forest(trace, var_names=['group_means'], combined=True)
```

### Bayesian Correlation

```python
import pymc as pm
import arviz as az
import numpy as np

# Standardize data for numerical stability
x_std = (x - x.mean()) / x.std()
y_std = (y - y.mean()) / y.std()

with pm.Model() as corr_model:
    # Prior on correlation
    rho = pm.Uniform('rho', lower=-1, upper=1)

    # Construct covariance matrix
    cov_matrix = pm.math.stack([[1, rho],
                                [rho, 1]])

    # Bivariate normal likelihood
    obs = pm.MvNormal('obs',
                      mu=[0, 0],
                      cov=cov_matrix,
                      observed=np.column_stack([x_std, y_std]))

    trace = pm.sample(2000, tune=1000, return_inferencedata=True)

print(az.summary(trace, var_names=['rho']))
prob_positive = np.mean(trace.posterior['rho'].values > 0)
print(f"P(rho > 0 | data) = {prob_positive:.3f}")

az.plot_posterior(trace, var_names=['rho'], ref_val=0)
```

### Bayesian Linear Regression

```python
import pymc as pm
import arviz as az

with pm.Model() as regression_model:
    # Priors
    alpha = pm.Normal('intercept', mu=0, sigma=10)
    beta = pm.Normal('slopes', mu=0, sigma=10, shape=n_predictors)
    sigma = pm.HalfNormal('sigma', sigma=10)

    # Expected value
    mu = alpha + pm.math.dot(X, beta)

    # Likelihood
    y_obs = pm.Normal('y_obs', mu=mu, sigma=sigma, observed=y)

    # Sample
    trace = pm.sample(2000, tune=1000, return_inferencedata=True)

# Posterior predictive checks
with regression_model:
    ppc = pm.sample_posterior_predictive(trace)

az.plot_ppc(ppc, num_pp_samples=100)

# Coefficient summary
print(az.summary(trace, var_names=['intercept', 'slopes']))
```

### Hierarchical Model (Partial Pooling)

For nested/clustered data (students within schools, patients within hospitals).

**Key concept**: Partial pooling borrows strength across groups -- estimates for groups with few observations are shrunk toward the global mean, reducing variance without the bias of complete pooling.

```python
with pm.Model() as hierarchical_model:
    # Hyperpriors
    mu_global = pm.Normal('mu_global', mu=0, sigma=10)
    sigma_between = pm.HalfNormal('sigma_between', sigma=5)
    sigma_within = pm.HalfNormal('sigma_within', sigma=5)

    # Group-level intercepts (partial pooling)
    alpha = pm.Normal('alpha', mu=mu_global, sigma=sigma_between, shape=n_groups)

    # Likelihood
    y_obs = pm.Normal('y_obs', mu=alpha[group_idx], sigma=sigma_within, observed=y)

    trace = pm.sample()
```

## Model Comparison

### WAIC and LOO

```python
import arviz as az

# Calculate information criteria
waic = az.waic(trace)
loo = az.loo(trace)

print(f"WAIC: {waic.elpd_waic:.2f} (SE: {waic.se:.2f})")
print(f"LOO:  {loo.elpd_loo:.2f} (SE: {loo.se:.2f})")

# Compare multiple models
comparison = az.compare({
    'model1': trace1,
    'model2': trace2,
    'model3': trace3,
})
print(comparison)
az.plot_compare(comparison)
```

- **WAIC** (Widely Applicable Information Criterion): Bayesian AIC analog. Higher elpd = better fit
- **LOO** (Leave-One-Out CV): Estimates out-of-sample prediction error. More robust than WAIC
- LOO is generally preferred for model comparison
- Both penalize effective number of parameters

## Convergence Diagnostics

### Essential Checks

1. **R-hat (Gelman-Rubin)**: Compares within-chain and between-chain variance
   - R-hat < 1.01: Good convergence
   - R-hat > 1.05: Poor convergence -- increase tuning or reparameterize

2. **Effective Sample Size (ESS)**: Number of independent samples
   - Bulk ESS > 400 per chain: Adequate for central tendency
   - Tail ESS > 400 per chain: Adequate for interval estimates
   - Low ESS: Increase sampling, improve parameterization, or use non-centered parameterization

3. **Trace plots**: Should look like "fuzzy caterpillars" -- no trends, no stuck regions

```python
# Automatic diagnostics
summary = az.summary(trace)  # R-hat and ESS columns
print(summary)

# Visual diagnostics
az.plot_trace(trace)      # Trace plots + posteriors
az.plot_rank(trace)       # Rank plots (better than trace for many chains)
az.plot_energy(trace)     # Energy diagnostic (HMC-specific)
```

### Posterior Predictive Checks

```python
with model:
    ppc = pm.sample_posterior_predictive(trace)

# Visual: does simulated data match observed?
az.plot_ppc(ppc, num_pp_samples=100)

# Quantitative: Bayesian p-value (should be near 0.5 for good fit)
obs_mean = np.mean(observed_data)
pred_means = [np.mean(s) for s in ppc.posterior_predictive['y_obs'].values.reshape(-1, len(observed_data))]
bayesian_p = np.mean(np.array(pred_means) >= obs_mean)
print(f"Bayesian p-value: {bayesian_p:.3f}")
```

## Reporting Bayesian Results

**Example t-test report**:
> "A Bayesian independent samples t-test was conducted using weakly informative priors (Normal(0, 1) for mean difference, Half-Cauchy(0, 1) for pooled SD). The posterior distribution of the mean difference had a mean of 5.2 (95% CI [2.3, 8.1]). BF10 = 23.5 provided strong evidence for a group difference. There was a 99.7% posterior probability that Group A's mean exceeded Group B's mean. Convergence: all R-hat < 1.01, ESS > 1000."

**Example regression report**:
> "A Bayesian linear regression with weakly informative priors (Normal(0, 10) for coefficients, Half-Cauchy(0, 5) for residual SD) showed R-squared = 0.47, 95% CI [0.38, 0.55]. Study hours (beta = 0.52, 95% CI [0.38, 0.66]) and prior GPA (beta = 0.31, 95% CI [0.17, 0.45]) were credible predictors (95% CIs excluded zero). Posterior predictive checks showed good fit. All R-hat < 1.01, ESS > 1000."

## Key Packages

| Package | Purpose |
|---------|---------|
| **PyMC** | Full Bayesian modeling (NUTS sampler) |
| **ArviZ** | Visualization, diagnostics, model comparison |
| **Bambi** | High-level formula interface (like R's brms) |
| **PyStan** | Python interface to Stan |
| **TensorFlow Probability** | Bayesian inference with TF backend |

## Advantages and Limitations

**Advantages**: Intuitive probability statements, incorporates prior knowledge, flexible for complex models, works with small samples, supports null hypothesis via BF, no p-hacking concerns, full uncertainty quantification via posterior distributions.

**Limitations**: Computational cost (MCMC can be slow), requires prior specification and justification, steeper learning curve, fewer automated tools than frequentist methods, may need to educate reviewers.

## Condensation Note

Condensed from original: 662 lines. Retained: Bayesian vs frequentist philosophy table, Bayes' theorem, prior types (informative, weakly informative, non-informative) with example distributions, prior sensitivity analysis with code, Bayes Factor interpretation table with full bidirectional scale, ROPE (Region of Practical Equivalence) with decision rules and code, credible intervals (ETI and HDI) with code, Bayesian t-test with full code, Bayesian ANOVA with hierarchical model and posterior contrasts, Bayesian correlation with bivariate normal model, Bayesian linear regression with posterior predictive checks, hierarchical model (partial pooling), model comparison (WAIC/LOO) with code, convergence diagnostics (R-hat, ESS, trace/rank/energy plots), posterior predictive checks with quantitative Bayesian p-value, reporting examples (t-test and regression), key packages table, advantages and limitations. Omitted: posterior distribution interpretation details (central tendency, shape) -- standard ArviZ knowledge; detailed Bayes Factor calculation from t-statistic (simplified BF function was incomplete in original).
