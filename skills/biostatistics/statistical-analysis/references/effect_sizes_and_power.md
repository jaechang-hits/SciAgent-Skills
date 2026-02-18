# Effect Sizes and Power Analysis

## Why Effect Sizes Matter

1. **Statistical significance does not equal practical significance**: p-values only tell if an effect exists, not how large it is
2. **Sample size dependent**: With large samples, trivial effects become "significant"
3. **Interpretation**: Effect sizes provide magnitude and practical importance
4. **Meta-analysis**: Effect sizes enable combining results across studies
5. **Power analysis**: Required for sample size determination

**Golden rule**: ALWAYS report effect sizes alongside p-values.

## Effect Sizes by Analysis Type

### T-Tests and Mean Differences

#### Cohen's d (Standardized Mean Difference)

**Formula**:
- Independent groups: d = (M1 - M2) / SD_pooled
- Paired groups: d = M_diff / SD_diff

**Interpretation** (Cohen, 1988):
- Small: |d| = 0.20
- Medium: |d| = 0.50
- Large: |d| = 0.80

**Context-dependent interpretation**:
- In education: d = 0.40 is typical for successful interventions
- In psychology: d = 0.40 is considered meaningful
- In medicine: Small effect sizes can be clinically important

```python
import pingouin as pg
import numpy as np

# Independent t-test with effect size
result = pg.ttest(group1, group2, correction=False)
cohens_d = result['cohen-d'].values[0]

# Manual calculation
mean_diff = np.mean(group1) - np.mean(group2)
pooled_std = np.sqrt((np.var(group1, ddof=1) + np.var(group2, ddof=1)) / 2)
cohens_d_manual = mean_diff / pooled_std
```

#### Hedges' g (Bias-Corrected d)

Cohen's d has slight upward bias with small samples (n < 20). Hedges' g corrects this.

**Formula**: g = d * (1 - 3/(4*df - 1))

```python
# pingouin provides Hedges' g directly
result = pg.ttest(group1, group2, correction=False)
hedges_g = result['hedges'].values[0]
```

**Use Hedges' g when**: sample sizes are small (n < 20 per group) or conducting meta-analyses (standard in meta-analysis).

#### Glass's Delta

**When to use**: When one group is a control with known variability, or when treatment affects variability.

**Formula**: delta = (M1 - M2) / SD_control

Use cases: clinical trials (use control group SD as denominator), pre-post designs where treatment may change variability.

### ANOVA Effect Sizes

#### Eta-Squared (eta-squared)

**Formula**: eta-squared = SS_effect / SS_total

**Interpretation**: Proportion of total variance explained by the factor.
- Small: 0.01 | Medium: 0.06 | Large: 0.14

**Limitation**: Biased with multiple factors (sums to > 1.0 in factorial designs). Use partial eta-squared for multi-factor designs.

```python
import pingouin as pg

aov = pg.anova(dv='value', between='group', data=df, detailed=True)
eta_sq = aov['SS'][0] / aov['SS'].sum()
```

#### Partial Eta-Squared (eta-squared partial)

**Formula**: eta-squared_p = SS_effect / (SS_effect + SS_error)

Proportion of variance explained by a factor, controlling for other factors. Standard in factorial designs. Same benchmarks as eta-squared.

```python
aov = pg.anova(dv='value', between=['factor1', 'factor2'], data=df)
partial_eta_sq = aov['np2']  # pingouin reports partial eta-squared by default
```

#### Omega-Squared (omega-squared)

Less biased population estimate than eta-squared. Eta-squared overestimates; omega-squared provides a better population estimate.

**Formula**: omega-squared = (SS_effect - df_effect * MS_error) / (SS_total + MS_error)

```python
def omega_squared(aov_table):
    """Calculate omega-squared from pingouin ANOVA table."""
    ss_effect = aov_table.loc[0, 'SS']
    ss_total = aov_table['SS'].sum()
    ms_error = aov_table.loc[aov_table.index[-1], 'MS']
    df_effect = aov_table.loc[0, 'DF']
    return (ss_effect - df_effect * ms_error) / (ss_total + ms_error)

aov = pg.anova(dv='value', between='group', data=df, detailed=True)
print(f"omega-squared = {omega_squared(aov):.3f}")
```

Interpretation: Same benchmarks as eta-squared, but typically yields smaller values.

#### Cohen's f

**Formula**: f = sqrt(eta-squared / (1 - eta-squared))

| f | Interpretation |
|---|----------------|
| 0.10 | Small |
| 0.25 | Medium |
| 0.40 | Large |

Required for ANOVA power calculations in statsmodels.

```python
eta_sq = 0.06
cohens_f = np.sqrt(eta_sq / (1 - eta_sq))
```

### Correlation

#### Pearson's r / Spearman's rho

r is already an effect size -- no conversion needed.

| |r| | Interpretation |
|-----|----------------|
| 0.10 | Small |
| 0.30 | Medium |
| 0.50 | Large |

**Important**: r-squared = coefficient of determination (proportion of shared variance). r = 0.30 means only 9% shared variance.

```python
import pingouin as pg

# Pearson correlation with CI
result = pg.corr(x, y, method='pearson')
r = result['r'].values[0]
ci = result['CI95%'].values[0]

# Spearman correlation
result_sp = pg.corr(x, y, method='spearman')
```

### Regression Effect Sizes

#### R-Squared (Coefficient of Determination)

Proportion of variance in Y explained by the model.

| R-squared | Interpretation |
|-----------|----------------|
| 0.02 | Small |
| 0.13 | Medium |
| 0.26 | Large |

Context-dependent: physical sciences expect R-squared > 0.90; social sciences consider R-squared > 0.30 good.

**Adjusted R-squared**: Penalizes model complexity. Always report alongside R-squared for multiple regression. Formula: R-squared_adj = 1 - (1 - R-squared) * (n - 1) / (n - k - 1).

```python
import statsmodels.api as sm

model = sm.OLS(y, sm.add_constant(X)).fit()
print(f"R-squared = {model.rsquared:.3f}, Adjusted = {model.rsquared_adj:.3f}")
```

#### Standardized Beta (Regression Coefficients)

Effect of one-SD change in predictor on outcome (in SD units). Allows comparison across predictors with different scales.

| |beta| | Interpretation |
|--------|----------------|
| 0.10 | Small |
| 0.30 | Medium |
| 0.50 | Large |

```python
from scipy import stats

# Standardize variables
X_std = (X - X.mean()) / X.std()
y_std = (y - y.mean()) / y.std()
model = sm.OLS(y_std, sm.add_constant(X_std)).fit()
betas = model.params[1:]  # Exclude intercept
```

#### f-Squared (Cohen's f-squared for Regression)

Effect size for individual predictors or model comparison (nested models).

**Formula**: f-squared = (R-squared_full - R-squared_reduced) / (1 - R-squared_full)

| f-squared | Interpretation |
|-----------|----------------|
| 0.02 | Small |
| 0.15 | Medium |
| 0.35 | Large |

```python
model_full = sm.OLS(y, X_full).fit()
model_reduced = sm.OLS(y, X_reduced).fit()
f_squared = (model_full.rsquared - model_reduced.rsquared) / (1 - model_full.rsquared)
```

### Categorical Data

#### Cramer's V

Association strength for chi-square test (works for any table size).

**Formula**: V = sqrt(chi-squared / (n * (k - 1))), where k = min(rows, columns)

| V (df=1) | V (df=2) | Interpretation |
|----------|----------|----------------|
| 0.10 | 0.07 | Small |
| 0.30 | 0.21 | Medium |
| 0.50 | 0.35 | Large |

#### Phi Coefficient (2x2 tables)

For 2x2 contingency tables, phi is the correlation between two binary variables. Benchmarks same as r (0.10, 0.30, 0.50).

```python
from scipy.stats.contingency import association

# Cramer's V
cramers_v = association(contingency_table, method='cramer')

# Phi coefficient (for 2x2)
phi = association(contingency_table, method='pearson')
```

#### Odds Ratio (OR)

| OR | Interpretation |
|----|----------------|
| 1.0 | No effect |
| 1.5 | Small |
| 2.5 | Medium |
| 4.0+ | Large |

OR from logistic regression: exponentiate coefficients. For 2x2 tables: OR = (a*d)/(b*c).

```python
import statsmodels.api as sm

model = sm.Logit(y, X).fit()
odds_ratios = np.exp(model.params)
ci = np.exp(model.conf_int())
```

## Confidence Intervals for Effect Sizes

Always report CIs -- they convey precision of the estimate.

```python
from pingouin import compute_effsize_from_t

# From t-statistic
d, ci = compute_effsize_from_t(t_stat, nx=len(g1), ny=len(g2), eftype='cohen')
print(f"d = {d:.2f}, 95% CI [{ci[0]:.2f}, {ci[1]:.2f}]")
```

## Power Analysis

### Concepts

**Statistical power**: Probability of detecting an effect if it exists (1 - beta).

**Conventional standards**: Power = 0.80, alpha = 0.05.

**Four interconnected parameters** (given 3, solve for 4th):
1. Sample size (n)
2. Effect size (d, f, etc.)
3. Significance level (alpha)
4. Power (1 - beta)

### A Priori Power Analysis (Before Data Collection)

**Goal**: Determine required sample size.

```python
from statsmodels.stats.power import (
    tt_ind_solve_power,
    FTestAnovaPower,
    GofChisquarePower,
)

# Independent t-test
n = tt_ind_solve_power(
    effect_size=0.5, alpha=0.05, power=0.80,
    ratio=1.0, alternative='two-sided'
)
print(f"Required n per group: {n:.0f}")  # ~64

# One-way ANOVA
anova_power = FTestAnovaPower()
n = anova_power.solve_power(
    effect_size=0.25, ngroups=3, alpha=0.05, power=0.80
)
print(f"Required n per group: {n:.0f}")

# Chi-square
chi_power = GofChisquarePower()
n = chi_power.solve_power(
    effect_size=0.3, alpha=0.05, power=0.80, n_bins=4
)
print(f"Required total n: {n:.0f}")
```

### Correlation Power Analysis

```python
from pingouin import power_corr

# How many subjects needed to detect r = 0.30?
n_required = power_corr(r=0.30, power=0.80, alpha=0.05)
print(f"Required n for r=0.30: {n_required}")

# What correlation is detectable with n=50?
detectable_r = power_corr(n=50, power=0.80, alpha=0.05)
print(f"Detectable r with n=50: {detectable_r:.2f}")
```

### Sensitivity Analysis (After Data Collection)

**Goal**: What effect size could the study detect?

```python
# With n=50 per group, what d is detectable?
detectable_d = tt_ind_solve_power(
    effect_size=None, nobs1=50, alpha=0.05,
    power=0.80, ratio=1.0, alternative='two-sided'
)
print(f"Minimum detectable d = {detectable_d:.2f}")  # ~0.57
```

### Power Curves

```python
import matplotlib.pyplot as plt
import numpy as np
from statsmodels.stats.power import tt_ind_solve_power

effect_sizes = [0.2, 0.5, 0.8]
sample_sizes = np.arange(10, 200, 5)

fig, ax = plt.subplots(figsize=(8, 5))
for d in effect_sizes:
    powers = [tt_ind_solve_power(effect_size=d, nobs1=n, alpha=0.05, ratio=1.0)
              for n in sample_sizes]
    ax.plot(sample_sizes, powers, label=f"d = {d}")

ax.axhline(y=0.80, color='r', linestyle='--', alpha=0.5, label='80% power')
ax.set_xlabel('Sample size per group')
ax.set_ylabel('Power')
ax.set_title('Power Curves for Independent t-test')
ax.legend()
ax.grid(alpha=0.3)
plt.tight_layout()
plt.show()
```

### Converting Between Effect Sizes

| From | To | Formula |
|------|----|---------|
| d | r | r = d / sqrt(d-squared + 4) |
| r | d | d = 2r / sqrt(1 - r-squared) |
| eta-squared | f | f = sqrt(eta-squared / (1 - eta-squared)) |
| f | d (2 groups) | d = 2f |

### Important Notes

- **Post-hoc power** (calculating power after seeing results) is not recommended -- it is a direct function of the p-value and adds no information
- **Effect size from prior literature** is preferred for a priori power analysis
- When no prior information exists, use the smallest effect size of interest (SESOI) -- the smallest effect that would be practically meaningful
- For **equivalence testing** (TOST), power analysis targets the equivalence bounds, not H1

## Quick Reference Table

| Analysis | Effect Size | Small | Medium | Large |
|----------|-------------|-------|--------|-------|
| T-test | Cohen's d | 0.20 | 0.50 | 0.80 |
| T-test (small n) | Hedges' g | 0.20 | 0.50 | 0.80 |
| ANOVA | eta-squared, omega-squared | 0.01 | 0.06 | 0.14 |
| ANOVA | Cohen's f | 0.10 | 0.25 | 0.40 |
| Correlation | r, rho | 0.10 | 0.30 | 0.50 |
| Regression | R-squared | 0.02 | 0.13 | 0.26 |
| Regression | f-squared | 0.02 | 0.15 | 0.35 |
| Regression | Standardized beta | 0.10 | 0.30 | 0.50 |
| Chi-square | Cramer's V | 0.07 | 0.21 | 0.35 |
| Chi-square (2x2) | phi | 0.10 | 0.30 | 0.50 |

## Condensation Note

Condensed from original: 582 lines. Retained: Cohen's d (with manual calculation), Hedges' g, Glass's delta, eta-squared, partial eta-squared, omega-squared (with code), Cohen's f, Pearson/Spearman r, R-squared, adjusted R-squared, standardized beta, f-squared, Cramer's V, phi coefficient, odds ratio, confidence intervals for effect sizes, a priori power analysis (t-test, ANOVA, chi-square), correlation power analysis, sensitivity analysis, power curves, effect size conversion table, reporting guidelines, quick reference table. Omitted: detailed APA reporting examples for each effect size (consolidated into references/reporting_standards.md), Bayes Factor calculation section (consolidated into references/bayesian_statistics.md), effect size pitfalls list (consolidated into KNOWHOW.md Common Pitfalls and Best Practices).
