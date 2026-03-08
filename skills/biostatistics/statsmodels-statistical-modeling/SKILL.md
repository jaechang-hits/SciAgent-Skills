---
name: "statsmodels-statistical-modeling"
description: "Statistical modeling library for Python. Use for regression (OLS, WLS, GLM), discrete outcomes (Logit, Poisson, NegBin), time series (ARIMA, SARIMAX, VAR), and rigorous inference with detailed diagnostics, coefficient tables, and hypothesis tests. For ML-focused classification/regression use scikit-learn; for guided test selection use statistical-analysis."
license: "BSD-3-Clause"
---

# statsmodels

## Overview

Statsmodels provides classical statistical modeling with rigorous inference for Python. It covers linear models, generalized linear models, discrete choice, time series, and comprehensive diagnostics. Unlike scikit-learn (prediction-focused), statsmodels emphasizes coefficient interpretation, p-values, confidence intervals, and model diagnostics.

## When to Use

- Fitting linear regression (OLS, WLS, GLS) with detailed coefficient tables and diagnostics
- Running logistic regression with odds ratios and marginal effects for clinical/epidemiological studies
- Analyzing count data with Poisson or negative binomial regression
- Time series forecasting with ARIMA, SARIMAX, or exponential smoothing
- Performing ANOVA, t-tests, or non-parametric tests with proper corrections
- Testing model assumptions (heteroskedasticity, autocorrelation, normality of residuals)
- Model comparison using AIC/BIC or likelihood ratio tests
- Using R-style formula interface (`y ~ x1 + x2 + C(group)`) for intuitive model specification
- For prediction-focused ML with cross-validation and hyperparameter tuning, use `scikit-learn` instead
- For Bayesian modeling with posterior inference, use `pymc` instead

## Prerequisites

- **Python packages**: `statsmodels`, `numpy`, `pandas`, `scipy`
- **Optional**: `matplotlib` (for diagnostic plots), `patsy` (for formula API, included with statsmodels)
- **Data**: Tabular data as pandas DataFrames or NumPy arrays

```bash
pip install statsmodels numpy pandas matplotlib
```

## Quick Start

```python
import statsmodels.api as sm
import statsmodels.formula.api as smf
import pandas as pd
import numpy as np

# Generate sample data
np.random.seed(42)
n = 100
df = pd.DataFrame({
    "x1": np.random.randn(n),
    "x2": np.random.randn(n),
    "group": np.random.choice(["A", "B"], n)
})
df["y"] = 2 + 3 * df["x1"] - 1.5 * df["x2"] + np.random.randn(n)

# OLS with formula API (R-style)
results = smf.ols("y ~ x1 + x2 + C(group)", data=df).fit()
print(results.summary())
print(f"R²: {results.rsquared:.3f}, AIC: {results.aic:.1f}")
```

## Core API

### Module 1: Linear Regression (OLS, WLS, GLS)

Standard linear models with comprehensive diagnostics.

```python
import statsmodels.api as sm
import numpy as np

# Generate data
np.random.seed(42)
X = np.random.randn(200, 3)
y = 1 + 2*X[:, 0] - 0.5*X[:, 1] + np.random.randn(200)

# ALWAYS add constant for intercept
X_const = sm.add_constant(X)
results = sm.OLS(y, X_const).fit()

print(results.summary())
print(f"\nCoefficients: {results.params}")
print(f"P-values: {results.pvalues}")
print(f"R²: {results.rsquared:.4f}")

# Predictions with confidence intervals
pred = results.get_prediction(X_const[:5])
print(pred.summary_frame())
```

```python
# Robust standard errors (heteroskedasticity-consistent)
results_robust = sm.OLS(y, X_const).fit(cov_type="HC3")
print("Robust SEs:", results_robust.bse)

# Weighted Least Squares
weights = 1 / np.abs(results.resid + 0.1)  # Example weights
results_wls = sm.WLS(y, X_const, weights=weights).fit()
print(f"WLS R²: {results_wls.rsquared:.4f}")
```

### Module 2: Generalized Linear Models (GLM)

Extend regression to non-normal outcomes (binary, count, continuous-positive).

```python
import statsmodels.api as sm
import numpy as np

# Poisson regression for count data
np.random.seed(42)
X = np.random.randn(200, 2)
X_const = sm.add_constant(X)
y_counts = np.random.poisson(np.exp(0.5 + 0.3*X[:, 0]))

model = sm.GLM(y_counts, X_const, family=sm.families.Poisson())
results = model.fit()
print(results.summary())

# Rate ratios
rate_ratios = np.exp(results.params)
print(f"Rate ratios: {rate_ratios}")

# Check overdispersion
overdispersion = results.pearson_chi2 / results.df_resid
print(f"Overdispersion ratio: {overdispersion:.2f}")
if overdispersion > 1.5:
    print("→ Consider Negative Binomial model")
```

### Module 3: Discrete Choice Models (Logit, Probit, Count)

Binary, multinomial, and count outcome models.

```python
import statsmodels.api as sm
import numpy as np

# Logistic regression
np.random.seed(42)
X = np.random.randn(300, 2)
X_const = sm.add_constant(X)
prob = 1 / (1 + np.exp(-(0.5 + X[:, 0] - 0.5*X[:, 1])))
y_binary = np.random.binomial(1, prob)

logit_results = sm.Logit(y_binary, X_const).fit()
print(logit_results.summary())

# Odds ratios
odds_ratios = np.exp(logit_results.params)
print(f"Odds ratios: {odds_ratios}")

# Marginal effects (at means)
margeff = logit_results.get_margeff()
print(margeff.summary())

# Predicted probabilities
probs = logit_results.predict(X_const[:5])
print(f"Predicted P(Y=1): {probs}")
```

### Module 4: Time Series (ARIMA, SARIMAX)

Univariate and multivariate time series modeling and forecasting.

```python
import statsmodels.api as sm
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.stattools import adfuller
import numpy as np
import pandas as pd

# Generate time series
np.random.seed(42)
dates = pd.date_range("2020-01-01", periods=200, freq="D")
y = np.cumsum(np.random.randn(200)) + 50
ts = pd.Series(y, index=dates)

# Stationarity test
adf_result = adfuller(ts)
print(f"ADF statistic: {adf_result[0]:.4f}, p-value: {adf_result[1]:.4f}")
print("Stationary" if adf_result[1] < 0.05 else "Non-stationary → difference")

# Fit ARIMA
model = ARIMA(ts, order=(1, 1, 1))
results = model.fit()
print(results.summary())

# Forecast with confidence intervals
forecast = results.get_forecast(steps=30)
forecast_df = forecast.summary_frame()
print(f"30-day forecast:\n{forecast_df.head()}")
```

```python
# Seasonal ARIMA (SARIMAX)
from statsmodels.tsa.statespace.sarimax import SARIMAX

# Monthly data with yearly seasonality
model_sarima = SARIMAX(ts, order=(1, 1, 1), seasonal_order=(1, 1, 1, 12))
results_sarima = model_sarima.fit(disp=False)
print(f"AIC: {results_sarima.aic:.1f}")

# Diagnostic plots
results_sarima.plot_diagnostics(figsize=(12, 8))
```

### Module 5: Statistical Tests and Diagnostics

Assumption tests, hypothesis tests, and model validation.

```python
import statsmodels.api as sm
from statsmodels.stats.diagnostic import het_breuschpagan, acorr_ljungbox
from statsmodels.stats.stattools import jarque_bera
import numpy as np

# Fit a model first
np.random.seed(42)
X = sm.add_constant(np.random.randn(200, 2))
y = 1 + 2*X[:, 1] + np.random.randn(200) * X[:, 1]  # Heteroskedastic
results = sm.OLS(y, X).fit()

# Heteroskedasticity test (Breusch-Pagan)
bp_stat, bp_p, _, _ = het_breuschpagan(results.resid, X)
print(f"Breusch-Pagan p-value: {bp_p:.4f} {'→ heteroskedastic' if bp_p < 0.05 else '→ OK'}")

# Normality test (Jarque-Bera)
jb_stat, jb_p, _, _ = jarque_bera(results.resid)
print(f"Jarque-Bera p-value: {jb_p:.4f} {'→ non-normal' if jb_p < 0.05 else '→ OK'}")

# Autocorrelation test (Ljung-Box)
lb_result = acorr_ljungbox(results.resid, lags=[10], return_df=True)
print(f"Ljung-Box p-value (lag 10): {lb_result['lb_pvalue'].values[0]:.4f}")
```

```python
# Variance Inflation Factor (multicollinearity)
from statsmodels.stats.outliers_influence import variance_inflation_factor

vif_data = pd.DataFrame({
    "Variable": [f"x{i}" for i in range(X.shape[1])],
    "VIF": [variance_inflation_factor(X, i) for i in range(X.shape[1])]
})
print(vif_data)  # VIF > 10 suggests multicollinearity
```

### Module 6: Formula API (R-style)

Intuitive model specification using formulas with automatic dummy coding.

```python
import statsmodels.formula.api as smf
import pandas as pd
import numpy as np

np.random.seed(42)
df = pd.DataFrame({
    "y": np.random.randn(100),
    "x1": np.random.randn(100),
    "x2": np.random.randn(100),
    "group": np.random.choice(["A", "B", "C"], 100),
})

# Formula with categoricals (auto dummy-coded)
res = smf.ols("y ~ x1 + x2 + C(group)", data=df).fit()
print(res.summary())

# Interactions
res2 = smf.ols("y ~ x1 * x2", data=df).fit()  # x1 + x2 + x1:x2
print(f"Interaction term p-value: {res2.pvalues['x1:x2']:.4f}")

# Logit via formula
df["binary"] = (df["y"] > 0).astype(int)
logit_res = smf.logit("binary ~ x1 + x2 + C(group)", data=df).fit()
print(f"Logit AIC: {logit_res.aic:.1f}")
```

## Common Workflows

### Workflow 1: Complete Regression Analysis

**Goal**: Fit OLS, validate assumptions, use robust SEs if needed.

```python
import statsmodels.api as sm
import statsmodels.formula.api as smf
from statsmodels.stats.diagnostic import het_breuschpagan
from statsmodels.stats.outliers_influence import variance_inflation_factor
import numpy as np
import pandas as pd

# 1. Fit initial model
np.random.seed(42)
df = pd.DataFrame({"y": np.random.randn(200), "x1": np.random.randn(200), "x2": np.random.randn(200)})
df["y"] = 2 + 3*df["x1"] - df["x2"] + np.random.randn(200)

results = smf.ols("y ~ x1 + x2", data=df).fit()

# 2. Check heteroskedasticity
bp_stat, bp_p, _, _ = het_breuschpagan(results.resid, results.model.exog)
print(f"Breusch-Pagan p: {bp_p:.4f}")

# 3. If heteroskedastic, use robust SEs
if bp_p < 0.05:
    results = smf.ols("y ~ x1 + x2", data=df).fit(cov_type="HC3")
    print("Using HC3 robust standard errors")

# 4. Check multicollinearity
X = results.model.exog
for i in range(1, X.shape[1]):  # skip constant
    print(f"VIF x{i}: {variance_inflation_factor(X, i):.2f}")

# 5. Final results
print(results.summary())
print(f"\nAIC: {results.aic:.1f}, BIC: {results.bic:.1f}")
```

### Workflow 2: Model Comparison

**Goal**: Compare nested and non-nested models using appropriate criteria.

```python
import statsmodels.formula.api as smf
from scipy import stats
import pandas as pd
import numpy as np

np.random.seed(42)
df = pd.DataFrame({"y": np.random.randn(200), "x1": np.random.randn(200),
                    "x2": np.random.randn(200), "x3": np.random.randn(200)})
df["y"] = 1 + 2*df["x1"] - df["x2"] + 0.1*df["x3"] + np.random.randn(200)

# Fit nested models
m1 = smf.ols("y ~ x1", data=df).fit()
m2 = smf.ols("y ~ x1 + x2", data=df).fit()
m3 = smf.ols("y ~ x1 + x2 + x3", data=df).fit()

# Compare via AIC/BIC (lower = better)
comparison = pd.DataFrame({
    "R²": [m.rsquared for m in [m1, m2, m3]],
    "AIC": [m.aic for m in [m1, m2, m3]],
    "BIC": [m.bic for m in [m1, m2, m3]],
}, index=["y~x1", "y~x1+x2", "y~x1+x2+x3"])
print(comparison)

# Likelihood ratio test (nested: m2 vs m3)
lr_stat = 2 * (m3.llf - m2.llf)
p_val = 1 - stats.chi2.cdf(lr_stat, df=m3.df_model - m2.df_model)
print(f"\nLR test (m3 vs m2): stat={lr_stat:.2f}, p={p_val:.4f}")
```

### Workflow 3: Time Series Forecasting Pipeline

**Goal**: Test stationarity, identify model order, forecast.

```python
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.stattools import adfuller
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Generate data
np.random.seed(42)
ts = pd.Series(np.cumsum(np.random.randn(200)) + 100,
               index=pd.date_range("2020-01-01", periods=200, freq="D"))

# 1. Test stationarity
adf_p = adfuller(ts)[1]
print(f"ADF p-value: {adf_p:.4f} → {'stationary' if adf_p < 0.05 else 'non-stationary'}")

# 2. Identify order from ACF/PACF (on differenced series)
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 6))
plot_acf(ts.diff().dropna(), lags=20, ax=ax1)
plot_pacf(ts.diff().dropna(), lags=20, ax=ax2)
plt.savefig("acf_pacf.png", dpi=150, bbox_inches="tight")

# 3. Fit and forecast
model = ARIMA(ts[:180], order=(1, 1, 1))
results = model.fit()
forecast = results.get_forecast(steps=20)
fc_df = forecast.summary_frame()
print(f"ARIMA AIC: {results.aic:.1f}")
print(f"Forecast (first 5 days):\n{fc_df.head()}")
```

## Key Parameters

| Parameter | Module | Default | Range / Options | Effect |
|-----------|--------|---------|-----------------|--------|
| `cov_type` | OLS/WLS/GLM | `"nonrobust"` | `"HC0"`-`"HC3"`, `"HAC"`, `"cluster"` | Robust covariance estimator |
| `family` | GLM | required | `Poisson()`, `Binomial()`, `Gamma()`, etc. | Distribution family |
| `order` | ARIMA | required | `(p, d, q)` tuple | AR order, differencing, MA order |
| `seasonal_order` | SARIMAX | `(0,0,0,0)` | `(P, D, Q, s)` tuple | Seasonal ARIMA parameters |
| `alpha` | `summary()`, `conf_int()` | `0.05` | `0.01`-`0.10` | Significance level for CIs |
| `maxiter` | All `.fit()` | `35`-`100` | `50`-`1000` | Max optimization iterations |
| `method` | `.fit()` | model-dependent | `"newton"`, `"bfgs"`, `"lbfgs"`, `"powell"` | Optimization algorithm |
| `lags` | ACF/PACF | `None` | `10`-`50` | Number of lags to display |

## Best Practices

1. **Always add a constant** for OLS/GLM: `sm.add_constant(X)` or use formula API (adds intercept automatically)

2. **Match model to outcome type**: Binary → Logit/Probit, Counts → Poisson/NegBin, Continuous → OLS/WLS, Time series → ARIMA

3. **Check diagnostics before interpreting**: Run Breusch-Pagan (heteroskedasticity), Jarque-Bera (normality), Ljung-Box (autocorrelation) on residuals

4. **Use robust SEs when assumptions fail**: `results = model.fit(cov_type="HC3")` for heteroskedasticity-robust inference

5. **Report effect sizes, not just p-values**: Include coefficients, confidence intervals, and R² alongside significance tests

6. **Prefer formula API for exploratory work**: `smf.ols("y ~ x1 * x2 + C(group)", data=df)` is more readable and handles categoricals automatically

7. **Test stationarity before time series modeling**: Use ADF test; difference if non-stationary

## Common Recipes

### Recipe: ANOVA with Post-hoc Tests

When to use: Comparing means across 3+ groups.

```python
import statsmodels.formula.api as smf
from statsmodels.stats.multicomp import pairwise_tukeyhsd
import pandas as pd
import numpy as np

np.random.seed(42)
df = pd.DataFrame({"value": np.concatenate([np.random.normal(m, 1, 30) for m in [5, 6, 7]]),
                    "group": np.repeat(["A", "B", "C"], 30)})

# One-way ANOVA
anova = smf.ols("value ~ C(group)", data=df).fit()
print(sm.stats.anova_lm(anova))

# Post-hoc Tukey HSD
tukey = pairwise_tukeyhsd(df["value"], df["group"], alpha=0.05)
print(tukey)
```

### Recipe: Power Analysis for Sample Size

When to use: Determining required sample size before a study.

```python
from statsmodels.stats.power import TTestIndPower

analysis = TTestIndPower()
# What sample size for medium effect (d=0.5), 80% power, alpha=0.05?
n = analysis.solve_power(effect_size=0.5, alpha=0.05, power=0.8)
print(f"Required n per group: {n:.0f}")

# Power for given sample size
power = analysis.solve_power(effect_size=0.5, alpha=0.05, nobs1=50)
print(f"Power with n=50: {power:.3f}")
```

### Recipe: Mixed Effects Model

When to use: Hierarchical/clustered data (patients within hospitals, students within schools).

```python
import statsmodels.formula.api as smf
import pandas as pd
import numpy as np

np.random.seed(42)
df = pd.DataFrame({
    "y": np.random.randn(100), "x": np.random.randn(100),
    "group": np.repeat(range(10), 10)
})

# Random intercept model
model = smf.mixedlm("y ~ x", data=df, groups=df["group"])
results = model.fit()
print(results.summary())
```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `MissingDataError` | NaN values in data | Drop NAs: `df.dropna()` or impute before fitting |
| No intercept in results | Forgot `sm.add_constant()` | Always add constant, or use `smf.ols()` formula API |
| `ConvergenceWarning` | Optimization failed | Increase `maxiter`, try different `method`, or scale variables |
| Overdispersion in Poisson | Variance > mean | Switch to `NegativeBinomial` or use `GLM(family=NegativeBinomial())` |
| Non-stationary time series | Trend or unit root | Difference the series (`ts.diff()`) or increase `d` in ARIMA |
| Singular matrix error | Perfect multicollinearity | Remove redundant variables; check VIF > 10 |
| Different results from R | Default settings differ | Check: constant term, link function, optimizer, SE type |
| `PerfectSeparationError` in Logit | Predictor perfectly separates classes | Use regularized logistic (penalized MLE) or Firth's method |

## References

- [statsmodels documentation](https://www.statsmodels.org/stable/) — official docs
- [statsmodels User Guide](https://www.statsmodels.org/stable/user-guide.html) — tutorials
- [statsmodels API Reference](https://www.statsmodels.org/stable/api.html) — complete API
- Seabold, S. & Perktold, J. (2010). Statsmodels: Econometric and Statistical Modeling with Python. *Proceedings of the 9th Python in Science Conference*.
