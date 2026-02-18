---
name: statistical-analysis
description: >-
  Guided statistical analysis: test selection, assumption checking, effect sizes, power analysis, and APA reporting.
  Use when choosing appropriate tests for your data, verifying assumptions, calculating effect sizes,
  or formatting results for publication. Covers frequentist (t-test, ANOVA, chi-square, regression, correlation,
  survival, count models, agreement/reliability) and Bayesian alternatives.
  For implementing specific models use statsmodels or pymc-bayesian-modeling.
license: CC-BY-4.0
---

# Statistical Analysis

## Overview

Statistical analysis is the systematic process of selecting appropriate tests, verifying assumptions, quantifying effect magnitudes, and reporting results. This knowhow guides test selection, assumption diagnostics, and APA-style reporting for frequentist and Bayesian analyses in academic research.

## Key Concepts

### Frequentist vs Bayesian Framework

| Aspect | Frequentist | Bayesian |
|--------|-------------|----------|
| Core output | p-value, confidence interval | Posterior distribution, credible interval |
| Interpretation | "How likely is this data if H0 is true?" | "How likely is H1 given the data?" |
| Null support | Cannot support H0 (only fail to reject) | Can quantify evidence for H0 via Bayes Factor |
| Prior info | Not used | Incorporated via prior distributions |
| Sample size | Requires adequate power | Works with any sample size |
| Best for | Standard analyses, large samples | Small samples, prior info, complex models |

### Statistical vs Practical Significance

A statistically significant result (p < .05) may be trivially small in practice. Always report:
- **Effect size**: Magnitude of the effect (Cohen's d, eta-squared, r, R-squared)
- **Confidence interval**: Precision of the estimate
- **Context**: Clinical/practical relevance in the domain

### Common Effect Sizes

| Test | Effect Size | Small | Medium | Large |
|------|-------------|-------|--------|-------|
| t-test | Cohen's d | 0.20 | 0.50 | 0.80 |
| t-test (small n) | Hedges' g | 0.20 | 0.50 | 0.80 |
| ANOVA | eta-squared partial | 0.01 | 0.06 | 0.14 |
| ANOVA | omega-squared | 0.01 | 0.06 | 0.14 |
| Correlation | r | 0.10 | 0.30 | 0.50 |
| Regression | R-squared | 0.02 | 0.13 | 0.26 |
| Regression | f-squared | 0.02 | 0.15 | 0.35 |
| Chi-square | Cramer's V | 0.07 | 0.21 | 0.35 |
| Chi-square 2x2 | phi coefficient | 0.10 | 0.30 | 0.50 |

Cohen's benchmarks are guidelines, not rigid thresholds -- domain context always matters.

### Assumptions Overview

Most parametric tests require:
1. **Independence**: Observations are independent of each other
2. **Normality**: Data (or residuals) are approximately normally distributed
3. **Homogeneity of variance**: Groups have similar variances (for group comparisons)
4. **Linearity**: Relationship between variables is linear (for regression)

When assumptions are violated:
- **Normality violated, n > 30**: Proceed -- parametric tests are robust with large samples
- **Normality violated, n < 30**: Use non-parametric alternative
- **Variance heterogeneity**: Use Welch's correction (t-test) or Welch's ANOVA
- **Linearity violated**: Add polynomial terms, transform variables, or use GAMs

### Test-Specific Assumption Workflows

**T-test assumptions**: (1) Check normality per group with Shapiro-Wilk + Q-Q plots. (2) Check homogeneity with Levene's test. (3) If normality violated: Mann-Whitney U (independent) or Wilcoxon signed-rank (paired). If variance heterogeneity: use Welch's t-test.

**ANOVA assumptions**: (1) Normality per group. (2) Homogeneity via Levene's test. (3) For repeated measures: check sphericity (Mauchly's test); if violated, apply Greenhouse-Geisser (epsilon < 0.75) or Huynh-Feldt (epsilon > 0.75) correction. (4) If normality violated: Kruskal-Wallis (independent) or Friedman (repeated).

**Linear regression assumptions**: (1) Linearity via residuals-vs-fitted plot. (2) Independence via Durbin-Watson test (1.5-2.5 acceptable). (3) Homoscedasticity via Breusch-Pagan test + scale-location plot. (4) Normality of residuals via Q-Q plot + Shapiro-Wilk. (5) Multicollinearity via VIF (>10 = severe, >5 = moderate).

**Logistic regression assumptions**: (1) Independence. (2) Linearity of log-odds with continuous predictors (Box-Tidwell test). (3) No perfect multicollinearity (VIF). (4) Adequate sample size (10-20 events per predictor minimum).

### Specialized Test Categories

Beyond the main decision flowchart, several specialized test families address specific data types:

**Survival / time-to-event analysis**:
- **Log-rank test**: Compares survival curves between groups (non-parametric)
- **Cox proportional hazards**: Models time-to-event with covariates; assumes proportional hazards
- **Parametric survival models**: Weibull, exponential, log-normal for known distributional forms
- Use when outcome is time until an event (death, relapse, failure) with possible censoring

**Count outcome models**:
- **Poisson regression**: For count data where mean approximately equals variance
- **Negative binomial regression**: For overdispersed counts (variance > mean)
- **Zero-inflated models**: For excess zeros beyond what Poisson/NB predicts
- Use when outcome is a count (number of events, incidents, occurrences)

**Agreement and reliability**:
- **Cohen's kappa**: Inter-rater agreement for categorical ratings (2 raters)
- **Fleiss' kappa / Krippendorff's alpha**: Agreement for >2 raters
- **Intraclass correlation coefficient (ICC)**: Continuous ratings reliability
- **Cronbach's alpha**: Internal consistency of multi-item scales
- **Bland-Altman analysis**: Agreement between two measurement methods (continuous)
- Use when assessing measurement reliability or inter-rater consistency

**Categorical data extensions**:
- **McNemar's test**: Paired binary outcomes (2x2)
- **Cochran's Q test**: Paired binary outcomes (3+ conditions)
- **Cochran-Armitage trend test**: Ordered categories in contingency tables

## Decision Framework

### Test Selection Flowchart

```
What is your research question?
|
+-- Comparing GROUPS on a continuous outcome?
|   |
|   +-- How many groups?
|   |   +-- 2 groups
|   |   |   +-- Independent -> Independent t-test (or Mann-Whitney U)
|   |   |   +-- Paired/repeated -> Paired t-test (or Wilcoxon signed-rank)
|   |   +-- 3+ groups
|   |      +-- Independent -> One-way ANOVA (or Kruskal-Wallis)
|   |      +-- Repeated -> Repeated-measures ANOVA (or Friedman)
|   |
|   +-- Multiple factors? -> Factorial ANOVA / Mixed ANOVA
|   +-- With covariates? -> ANCOVA
|
+-- Testing a RELATIONSHIP between variables?
|   |
|   +-- Both continuous?
|   |   +-- Normal -> Pearson correlation
|   |   +-- Non-normal or ordinal -> Spearman correlation
|   |
|   +-- Predicting continuous outcome?
|   |   +-- 1 predictor -> Simple linear regression
|   |   +-- Multiple predictors -> Multiple linear regression
|   |
|   +-- Predicting categorical outcome?
|   |   +-- Binary -> Logistic regression
|   |   +-- Ordinal -> Ordinal logistic regression
|   |
|   +-- Predicting count outcome?
|   |   +-- Equidispersed -> Poisson regression
|   |   +-- Overdispersed -> Negative binomial regression
|   |   +-- Excess zeros -> Zero-inflated Poisson/NB
|   |
|   +-- Time-to-event outcome?
|       +-- Compare survival curves -> Log-rank test
|       +-- With covariates -> Cox proportional hazards
|
+-- Testing ASSOCIATION between categorical variables?
|   +-- Expected cell count >= 5 -> Chi-square test
|   +-- Expected cell count < 5 -> Fisher's exact test
|   +-- Ordered categories -> Cochran-Armitage trend test
|   +-- Paired categories -> McNemar's test
|
+-- Assessing AGREEMENT / RELIABILITY?
    +-- Categorical, 2 raters -> Cohen's kappa
    +-- Categorical, >2 raters -> Fleiss' kappa
    +-- Continuous ratings -> ICC
    +-- Two measurement methods -> Bland-Altman analysis
    +-- Internal consistency -> Cronbach's alpha
```

### Quick Reference Table

| Research Question | Data Type | Normal? | Test | Non-parametric Alternative |
|-------------------|-----------|---------|------|---------------------------|
| 2 independent groups | Continuous | Yes | Independent t-test | Mann-Whitney U |
| 2 paired groups | Continuous | Yes | Paired t-test | Wilcoxon signed-rank |
| 3+ independent groups | Continuous | Yes | One-way ANOVA | Kruskal-Wallis |
| 3+ repeated groups | Continuous | Yes | Repeated-measures ANOVA | Friedman test |
| 2 variables | Continuous | Yes | Pearson r | Spearman rho |
| Predict continuous | Mixed | -- | Linear regression | -- |
| Predict binary | Mixed | -- | Logistic regression | -- |
| Predict counts | Count | -- | Poisson / Negative binomial | -- |
| Time-to-event | Survival | -- | Cox PH / Log-rank | -- |
| 2 categorical | Categorical | -- | Chi-square / Fisher's exact | -- |
| Rater agreement | Categorical | -- | Cohen's kappa / Fleiss' kappa | -- |
| Method agreement | Continuous | -- | Bland-Altman / ICC | -- |

## Best Practices

1. **Pre-register analyses** when possible to distinguish confirmatory from exploratory findings. Specify primary outcome, tests, and correction methods before data collection
2. **Always check assumptions before interpreting results**. Run normality tests (Shapiro-Wilk), homogeneity tests (Levene's), and residual diagnostics. Document results even when assumptions are met
3. **Report effect sizes with confidence intervals** for every test. p-values alone are insufficient -- effect sizes convey practical importance
4. **Report all planned analyses** including non-significant findings. Selective reporting inflates false positive rates
5. **Use appropriate multiple comparison corrections**. Bonferroni (conservative), Holm (step-down, less conservative), or FDR/Benjamini-Hochberg (for many tests). Choose based on the number of comparisons and acceptable error rate
6. **Visualize data before and after analysis**. Box plots for group comparisons, scatter plots for correlations, residual plots for regression diagnostics
7. **Conduct sensitivity analyses** to assess robustness: re-run with outliers removed, different transformations, or alternative tests
8. **Anti-pattern -- p-hacking**: Testing multiple outcomes, subgroups, or model specifications until p < .05 inflates false positives. Pre-register to avoid
9. **Anti-pattern -- HARKing** (Hypothesizing After Results are Known): Presenting exploratory findings as confirmatory undermines scientific integrity
10. **Anti-pattern -- misinterpreting non-significance**: Failure to reject H0 does not mean H0 is true. Use Bayesian methods or equivalence testing to support null

## Common Pitfalls

1. **Misinterpreting p-values as probability of the hypothesis being true**. p-values measure P(data | H0), not P(H0 | data). *How to avoid*: Use precise language: "If the null hypothesis were true, the probability of observing data this extreme is p = ..."

2. **Confusing statistical significance with practical importance**. A large sample can make trivially small effects significant. *How to avoid*: Always report and interpret effect sizes alongside p-values

3. **Running post-hoc power analysis after a non-significant result**. Post-hoc power is a mathematical function of the p-value and adds no new information. *How to avoid*: Use sensitivity analysis instead -- determine what effect size the study could detect at 80% power

4. **Ignoring assumption violations and proceeding with parametric tests**. *How to avoid*: Run assumption checks systematically. Use Welch's corrections, non-parametric alternatives, or transformations when violated

5. **Multiple comparisons without correction**. Running 20 tests at alpha = .05 gives ~64% chance of at least one false positive. *How to avoid*: Apply Bonferroni, Holm, or FDR correction. Report both corrected and uncorrected p-values

6. **Treating ordinal data as continuous**. Likert scales are ordinal -- means and standard deviations assume equal intervals. *How to avoid*: Use non-parametric tests (Mann-Whitney, Kruskal-Wallis) or ordinal regression

7. **Ignoring missing data patterns**. Listwise deletion assumes MCAR, which is rarely true. *How to avoid*: Assess missingness mechanism (MCAR, MAR, MNAR). Use multiple imputation for MAR data

8. **Confusing correlation with causation**. Observational studies cannot establish causal relationships regardless of effect size. *How to avoid*: Use causal language only for experimental designs with random assignment

9. **Not reporting non-significant results**. Publication bias and file-drawer effect distort the literature. *How to avoid*: Report all pre-registered analyses. Consider registered reports

10. **Using one-tailed tests to "improve" significance**. One-tailed tests should be pre-specified based on strong directional hypotheses. *How to avoid*: Default to two-tailed. Only use one-tailed when justified a priori

## Workflow

### Standard Analysis Pipeline

1. **Define research question and hypotheses**
   - State H0 and H1 explicitly
   - Specify primary outcome and covariates

2. **Select statistical test** (use Decision Framework above)
   - Match test to data type, design, and assumptions
   - Plan multiple comparison corrections if needed

3. **Conduct a priori power analysis**
   - Specify target effect size (from literature or clinical relevance)
   - Set alpha = .05, power = .80 (minimum), determine required n
   - Libraries: `statsmodels.stats.power`, `pingouin`

4. **Inspect and clean data**
   - Check for missing data patterns (MCAR/MAR/MNAR)
   - Identify outliers (IQR method: Q1 - 1.5*IQR / Q3 + 1.5*IQR, or z-scores > 3)
   - Verify variable types and coding
   - The original `assumption_checks.py` script provides automated normality, homogeneity, and outlier detection with visualization

5. **Check assumptions** (see Test-Specific Assumption Workflows above)
   - Normality: Shapiro-Wilk test + Q-Q plots (visual primary for n > 50)
   - Homogeneity: Levene's test + box plots
   - Linearity: Residual plots (for regression)
   - Sphericity: Mauchly's test (for repeated measures)
   - Document results and remedial actions

6. **Run primary analysis**
   - Execute planned test with appropriate library (scipy.stats, pingouin, statsmodels)
   - Calculate effect size and confidence interval
   - For Bayesian analyses: specify priors, run MCMC, check convergence (see `references/bayesian_statistics.md`)

7. **Conduct post-hoc and secondary analyses**
   - Post-hoc pairwise comparisons (Tukey HSD, Bonferroni)
   - Sensitivity analyses (remove outliers, alternative methods)
   - Exploratory analyses (clearly labeled)

8. **Report results in APA format**
   - Descriptive statistics (M, SD, n per group)
   - Test statistic, degrees of freedom, exact p-value
   - Effect size with confidence interval
   - See `references/reporting_standards.md` for templates

## Bundled Resources

- **`references/effect_sizes_and_power.md`** -- Detailed guide to calculating, interpreting, and reporting effect sizes (Cohen's d, Hedges' g, Glass's delta, eta-squared, omega-squared, partial eta-squared, phi coefficient, standardized beta, f-squared, Cramer's V, odds ratio); a priori, sensitivity, and correlation power analysis with code examples. Condensed from 582-line original.

- **`references/bayesian_statistics.md`** -- Comprehensive Bayesian analysis guide: Bayes' theorem, prior specification, ROPE (Region of Practical Equivalence), prior sensitivity analysis, Bayesian t-test/ANOVA/correlation/regression, hierarchical models, model comparison (WAIC/LOO), convergence diagnostics. Condensed from 662-line original.

- **`references/reporting_standards.md`** -- APA-style reporting templates for t-tests, ANOVA, regression, correlation, chi-square, non-parametric, and Bayesian analyses; pre-registration guidance; methods section templates (participants, design, measures); null results reporting; reporting checklist. Condensed from 470-line original.

### Fully-Consolidated Files (no separate reference file)

- **`test_selection_guide.md`** (130 lines original) -- Fully consolidated into Decision Framework (flowchart + Quick Reference Table) and Specialized Test Categories subsection in Key Concepts. Combined coverage: flowchart (~35 lines) + Quick Reference Table (~15 lines) + Specialized Test Categories (~35 lines) = ~85 lines covering all original capabilities. Original content on sample size considerations, multiple comparisons, and missing data was consolidated into Best Practices and Common Pitfalls. Omitted: study design considerations (RCTs, observational, clustered data) -- general guidance covered by statsmodels-statistical-modeling skill.

- **`assumptions_and_diagnostics.md`** (370 lines original) -- Fully consolidated into Key Concepts (Assumptions Overview + Test-Specific Assumption Workflows) and Workflow Steps 4-5. Combined coverage: Assumptions Overview (~12 lines) + Test-Specific Assumption Workflows (~20 lines) + Workflow Steps 4-5 (~16 lines) = ~48 lines. The original contained detailed code blocks for each assumption check; since this is Knowhow (not Skill), code is referenced rather than reproduced. Key diagnostic thresholds preserved (VIF > 10, Durbin-Watson 1.5-2.5, variance ratio < 2-3). Omitted: extensive Python code blocks for individual checks (normality, homogeneity, linearity, logistic regression diagnostics) -- available in scipy.stats and pingouin documentation. Sample size rules of thumb covered in Workflow Step 3.

### Script Disposition

- **`assumption_checks.py`** (540 lines) -- Contains 6 functions: `check_normality()`, `check_normality_per_group()`, `check_homogeneity_of_variance()`, `check_linearity()`, `detect_outliers()`, `comprehensive_assumption_check()`. As Knowhow entry, script functions are referenced in Workflow Step 4 rather than reproduced inline. Key capabilities (Shapiro-Wilk, Levene's, IQR/z-score outlier detection, Q-Q plots) are described in Assumptions Overview and Test-Specific Assumption Workflows. Users needing automated checking should use scipy.stats and pingouin directly following the patterns described.

### Intentional Omissions

- Time series methods (ARIMA, ACF/PACF) -- specialized topic beyond core statistical testing scope
- Mixed-effects models / GEE -- covered by statsmodels-statistical-modeling skill
- Bootstrap and permutation tests -- mentioned in passing; detailed implementation deferred to computational statistics resources

## Further Reading

- Cohen, J. (1988). *Statistical Power Analysis for the Behavioral Sciences* (2nd ed.)
- Field, A. (2013). *Discovering Statistics Using IBM SPSS Statistics* (4th ed.)
- Gelman, A., & Hill, J. (2006). *Data Analysis Using Regression and Multilevel/Hierarchical Models*
- Kruschke, J. K. (2014). *Doing Bayesian Data Analysis* (2nd ed.)
- APA Publication Manual: https://apastyle.apa.org/
- Cross Validated (stats Q&A): https://stats.stackexchange.com/

## Related Skills

- **statsmodels-statistical-modeling** -- Implementing OLS, GLM, Logit, time-series models programmatically
- **pymc-bayesian-modeling** -- Full Bayesian modeling with MCMC sampling
- **scikit-learn-machine-learning** -- Predictive modeling, cross-validation, classification
- **matplotlib-scientific-plotting** -- Creating publication-quality statistical figures
- **hypothesis-generation** -- Structured hypothesis formulation before statistical testing
