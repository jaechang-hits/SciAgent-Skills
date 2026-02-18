# PyMC — Distributions & Inference Reference

Consolidated reference for distribution selection and inference method configuration. For basic prior selection, see the Key Concepts table in SKILL.md. For diagnostic thresholds, see Key Concepts in SKILL.md.

---

## Part 1: Distribution Catalog

### Continuous Distributions

| Distribution | Signature | Support | Common Uses |
|-------------|-----------|---------|-------------|
| Normal | `pm.Normal("x", mu, sigma)` | (-inf, inf) | Unbounded parameters, additive noise likelihood |
| HalfNormal | `pm.HalfNormal("x", sigma)` | [0, inf) | Scale/standard deviation priors |
| StudentT | `pm.StudentT("x", nu, mu, sigma)` | (-inf, inf) | Robust alternative to Normal (outlier-resistant) |
| Cauchy | `pm.Cauchy("x", alpha, beta)` | (-inf, inf) | Heavy-tailed alternative to Normal |
| Beta | `pm.Beta("x", alpha, beta)` | [0, 1] | Probabilities and proportions |
| Gamma | `pm.Gamma("x", alpha, beta)` | (0, inf) | Positive parameters, rate parameters |
| Exponential | `pm.Exponential("x", lam)` | [0, inf) | Scale parameters, waiting times |
| LogNormal | `pm.LogNormal("x", mu, sigma)` | (0, inf) | Positive parameters with multiplicative effects |
| Uniform | `pm.Uniform("x", lower, upper)` | [lower, upper] | Bounded weakly informative priors |
| Laplace | `pm.Laplace("x", mu, b)` | (-inf, inf) | Double exponential; sparsity-inducing prior |
| InverseGamma | `pm.InverseGamma("x", alpha, beta)` | (0, inf) | Variance parameters |
| Weibull | `pm.Weibull("x", alpha, beta)` | (0, inf) | Reliability and survival analysis |
| LogitNormal | `pm.LogitNormal("x", mu, sigma)` | (0, 1) | Alternative to Beta for proportions |
| SkewNormal | `pm.SkewNormal("x", mu, sigma, alpha)` | (-inf, inf) | Asymmetric continuous data |
| VonMises | `pm.VonMises("x", mu, kappa)` | [-pi, pi] | Circular/angular data |
| Pareto | `pm.Pareto("x", alpha, m)` | [m, inf) | Power-law phenomena |
| Gumbel | `pm.Gumbel("x", mu, beta)` | (-inf, inf) | Extreme value modeling |
| ExGaussian | `pm.ExGaussian("x", mu, sigma, nu)` | (-inf, inf) | Reaction times, right-skewed data |
| Kumaraswamy | `pm.Kumaraswamy("x", a, b)` | (0, 1) | Closed-form Beta alternative |
| Interpolated | `pm.Interpolated("x", x_points, pdf_points)` | user-defined | Custom empirical distribution |

### Discrete Distributions

| Distribution | Signature | Support | Common Uses |
|-------------|-----------|---------|-------------|
| Bernoulli | `pm.Bernoulli("x", p)` | {0, 1} | Binary outcomes; use `logit_p=` for stability |
| Binomial | `pm.Binomial("x", n, p)` | {0..n} | Successes in fixed trials |
| Poisson | `pm.Poisson("x", mu)` | {0, 1, 2, ...} | Equidispersed count data |
| NegativeBinomial | `pm.NegativeBinomial("x", mu, alpha)` | {0, 1, 2, ...} | Overdispersed count data |
| Categorical | `pm.Categorical("x", p)` | {0..K-1} | Multi-class outcomes |
| DiscreteUniform | `pm.DiscreteUniform("x", lower, upper)` | {lower..upper} | Uniform over finite integers |
| Geometric | `pm.Geometric("x", p)` | {0, 1, 2, ...} | Failures before first success |
| BetaBinomial | `pm.BetaBinomial("x", alpha, beta, n)` | {0..n} | Overdispersed binomial |
| OrderedLogistic | `pm.OrderedLogistic("x", eta, cutpoints)` | {0..K-1} | Ordinal outcome data |
| OrderedProbit | `pm.OrderedProbit("x", eta, cutpoints)` | {0..K-1} | Ordinal data (probit link) |

### Multivariate Distributions

| Distribution | Signature | Common Uses |
|-------------|-----------|-------------|
| MvNormal | `pm.MvNormal("x", mu, cov)` | Correlated continuous variables, GP |
| Dirichlet | `pm.Dirichlet("x", a)` | Probability vectors (simplex) |
| Multinomial | `pm.Multinomial("x", n, p)` | Counts across categories |
| MvStudentT | `pm.MvStudentT("x", nu, mu, cov)` | Robust multivariate modeling |
| LKJCorr | `pm.LKJCorr("x", n, eta)` | Correlation matrix prior (`eta=1`: uniform) |
| LKJCholeskyCov | `pm.LKJCholeskyCov("x", n, eta, sd_dist)` | Covariance via Cholesky decomposition |
| Wishart | `pm.Wishart("x", nu, V)` | Covariance matrix prior |
| MatrixNormal | `pm.MatrixNormal("x", mu, rowcov, colcov)` | Matrix-valued random variables |
| CAR | `pm.CAR("x", mu, W, alpha, tau)` | Conditional autoregressive (spatial) |
| ICAR | `pm.ICAR("x", W, sigma)` | Intrinsic CAR (spatial smoothing) |

### Mixture Distributions

| Distribution | Signature | Common Uses |
|-------------|-----------|-------------|
| Mixture | `pm.Mixture("x", w, comp_dists)` | General mixture; clustering, multi-modal data |
| NormalMixture | `pm.NormalMixture("x", w, mu, sigma)` | Gaussian mixture models |
| ZeroInflatedPoisson | `pm.ZeroInflatedPoisson("x", psi, mu)` | Excess zeros in count data |
| ZeroInflatedBinomial | `pm.ZeroInflatedBinomial("x", psi, n, p)` | Zero-inflated binomial |
| ZeroInflatedNegBinomial | `pm.ZeroInflatedNegativeBinomial("x", psi, mu, alpha)` | Zero-inflated overdispersed counts |
| HurdlePoisson | `pm.HurdlePoisson("x", psi, mu)` | Two-part count model |
| HurdleGamma | `pm.HurdleGamma("x", psi, alpha, beta)` | Two-part positive continuous model |
| HurdleLogNormal | `pm.HurdleLogNormal("x", psi, mu, sigma)` | Two-part log-normal model |

### Time Series Distributions

| Distribution | Signature | Common Uses |
|-------------|-----------|-------------|
| AR | `pm.AR("x", rho, sigma, init_dist)` | Autoregressive process |
| GaussianRandomWalk | `pm.GaussianRandomWalk("x", mu, sigma, init_dist)` | Cumulative/trend processes |
| MvGaussianRandomWalk | `pm.MvGaussianRandomWalk("x", mu, cov, init_dist)` | Multivariate random walk |
| GARCH11 | `pm.GARCH11("x", omega, alpha_1, beta_1)` | Financial volatility modeling |
| EulerMaruyama | `pm.EulerMaruyama("x", dt, sde_fn, sde_pars, init_dist)` | Continuous-time SDE discretization |

### Special Distributions and Modifiers

| Distribution | Signature | Purpose |
|-------------|-----------|---------|
| Deterministic | `pm.Deterministic("x", var)` | Track computed quantities (not sampled) |
| Potential | `pm.Potential("x", logp)` | Add arbitrary log-probability terms or constraints |
| Flat | `pm.Flat("x")` | Improper flat prior (use sparingly) |
| HalfFlat | `pm.HalfFlat("x")` | Improper flat prior on positive reals |
| Truncated | `pm.Truncated("x", dist, lower, upper)` | Truncate any distribution to bounds |
| Censored | `pm.Censored("x", dist, lower, upper)` | Censored observations (survival data) |
| CustomDist | `pm.CustomDist("x", ..., logp, random)` | User-defined log-probability function |
| Simulator | `pm.Simulator("x", fn, params, ...)` | Simulation-based likelihood (likelihood-free inference) |

---

## Part 2: Sampling & Inference Methods

### pm.sample — Primary MCMC Interface

```python
idata = pm.sample(
    draws=2000,       # posterior samples per chain
    tune=1000,        # warmup iterations (discarded)
    chains=4,         # independent chains
    cores=4,          # parallel cores
    target_accept=0.9,  # NUTS acceptance rate
    random_seed=42,
    idata_kwargs={"log_likelihood": True},  # for LOO/WAIC
)
```

### NUTS (No-U-Turn Sampler)

Default for continuous parameters. Hamiltonian Monte Carlo variant with automatic step size and mass matrix tuning.

```python
with model:
    # Default (auto-selected for continuous models)
    idata = pm.sample(target_accept=0.9)

    # Manual specification with high acceptance
    idata = pm.sample(step=pm.NUTS(target_accept=0.95))
```

When to use: smooth, continuous posteriors (default choice). Increase `target_accept` to 0.9-0.99 if divergences occur. Use `init="jitter+adapt_diag"` for difficult initializations.

### Metropolis

General-purpose Metropolis-Hastings. Less efficient than NUTS for continuous models but works with discrete parameters.

```python
with model:
    idata = pm.sample(step=pm.Metropolis())
```

When to use: discrete parameters, non-differentiable models. Requires more samples than NUTS for equivalent ESS.

### Slice Sampler

Univariate slice sampling. No tuning required but slow in high dimensions.

```python
with model:
    idata = pm.sample(step=pm.Slice())
```

When to use: difficult univariate posteriors where NUTS and Metropolis struggle.

### CompoundStep — Mixed Samplers

Combine different samplers for different parameter types.

```python
with model:
    step1 = pm.NUTS([continuous_var1, continuous_var2])
    step2 = pm.Metropolis([discrete_var])
    idata = pm.sample(step=[step1, step2])
```

When to use: models with both continuous and discrete parameters. NUTS handles the continuous block, Metropolis handles discrete.

### Sequential Monte Carlo (SMC)

Particle-based method for complex posteriors and model evidence estimation.

```python
with model:
    idata = pm.sample_smc(draws=2000, chains=4)
```

When to use: multimodal posteriors, likelihood-free inference (with `pm.Simulator`), or when NUTS diverges extensively. Also provides model evidence for Bayes factors.

### ADVI (Automatic Differentiation Variational Inference)

Mean-field Gaussian approximation to the posterior. Much faster than MCMC.

```python
with model:
    approx = pm.fit(n=50000, method="advi")
    idata_vi = approx.sample(1000)  # draw from approximation

    # Use as MCMC initialization
    start = approx.sample(return_inferencedata=False)[0]
    idata = pm.sample(start=start)
```

When to use: quick exploration, large datasets, MCMC initialization. Underestimates uncertainty; not suitable as final inference for publication.

### Full-Rank ADVI

Captures parameter correlations (mean-field ADVI assumes independence).

```python
with model:
    approx = pm.fit(method="fullrank_advi", n=30000)
```

When to use: when parameters are strongly correlated and mean-field ADVI is too inaccurate. Slower than mean-field but more accurate.

### SVGD (Stein Variational Gradient Descent)

Non-parametric variational inference using particle ensemble.

```python
with model:
    approx = pm.fit(method="svgd", n=20000)
```

When to use: multimodal posteriors where ADVI's unimodal assumption fails. More expensive than ADVI.

### MAP (Maximum A Posteriori)

Point estimate at the posterior mode. No uncertainty quantification.

```python
with model:
    map_estimate = pm.find_MAP(method="L-BFGS-B")
    print(map_estimate)

    # Use MAP as MCMC starting point
    idata = pm.sample(start=map_estimate)
```

When to use: quick point estimates, MCMC initialization, or when full posterior is not needed. Can find local optima in multimodal posteriors.

---

## Part 3: Method Selection Guide

| Scenario | Method | Key Setting |
|----------|--------|-------------|
| Standard continuous model | NUTS | `target_accept=0.9` |
| Discrete parameters in model | Metropolis (discrete) + NUTS (continuous) | CompoundStep |
| Hierarchical model with divergences | NUTS + non-centered parameterization | `target_accept=0.95` |
| Large dataset, initial exploration | ADVI | `n=30000-50000` |
| Correlated parameters (VI) | Full-rank ADVI | `method="fullrank_advi"` |
| Multimodal posterior | SMC or SVGD | `pm.sample_smc(draws=2000)` |
| Very large data, mini-batch | Minibatch ADVI | `pm.Minibatch` data wrapper |
| Quick point estimate | MAP | `pm.find_MAP()` |
| Model evidence / Bayes factors | SMC | Returns log marginal likelihood |
| Likelihood-free / simulator | SMC + `pm.Simulator` | Define simulation function |

---

## Part 4: Reparameterization Tricks

### Non-Centered Parameterization

Eliminates funnel geometry in hierarchical models that causes divergences.

```python
# CENTERED (can cause divergences in hierarchical models):
mu = pm.Normal("mu", 0, 10)
sigma = pm.HalfNormal("sigma", 1)
theta = pm.Normal("theta", mu, sigma, shape=n_groups)

# NON-CENTERED (better NUTS geometry):
mu = pm.Normal("mu", 0, 10)
sigma = pm.HalfNormal("sigma", 1)
theta_offset = pm.Normal("theta_offset", 0, 1, shape=n_groups)
theta = pm.Deterministic("theta", mu + sigma * theta_offset)
```

Use when: hierarchical models with few observations per group, or when NUTS reports divergences with the centered parameterization.

### QR Decomposition for Correlated Predictors

Decorrelates the design matrix for faster NUTS sampling in regression.

```python
import numpy as np

# QR decomposition of design matrix
Q, R = np.linalg.qr(X)

with pm.Model() as qr_model:
    # Sample in uncorrelated QR space
    beta_tilde = pm.Normal("beta_tilde", 0, 1, shape=X.shape[1])

    # Transform back to original coefficient scale
    beta = pm.Deterministic("beta", pm.math.solve(R, beta_tilde))

    mu = pm.math.dot(Q, beta_tilde)
    sigma = pm.HalfNormal("sigma", 1)
    y = pm.Normal("y", mu, sigma, observed=y_obs)
```

Use when: regression with correlated predictors causing high autocorrelation or slow sampling. The QR transformation orthogonalizes the parameter space.

---

*Condensed from 2 original files: `distributions.md` (320 lines) + `sampling_inference.md` (424 lines) = 744 original lines. This file retains ~290 lines (~39% standalone). Relocated to SKILL.md: core distribution selection guide table (Key Concepts), diagnostic threshold table (Key Concepts), basic ADVI usage pattern (covered in Workflow Step 4 context). Omitted from distributions.md: shape broadcasting examples (trivial NumPy-style `shape=5`), basic `dims` usage (covered in SKILL.md Workflow Step 2), `ChiSquared`/`Rice`/`Moyal`/`Triangular`/`AsymmetricLaplace` distributions (rarely used; available in PyMC docs). Omitted from sampling_inference.md: prior predictive sampling section (covered in SKILL.md Workflow Step 3), posterior predictive sampling section (covered in SKILL.md Workflow Step 6), predictions for new data (covered in SKILL.md Workflow Step 8), handling sampling issues section (divergence/slow/autocorrelation fixes covered in SKILL.md Troubleshooting), standard workflow section (redundant with SKILL.md 8-step Workflow), energy plot details (mentioned in SKILL.md Expected Outputs). Combined coverage: ~290 retained + ~160 lines of relocated content in SKILL.md = ~450/744 = ~60% combined coverage.*
