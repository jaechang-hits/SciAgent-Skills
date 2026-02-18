# APA-Style Statistical Reporting Standards

## Essential Elements

Every statistical report must include:
1. **Descriptive statistics**: M, SD, n for all groups/variables
2. **Test statistic**: Name, value, degrees of freedom
3. **Exact p-value**: Report exact (p = .032), not just thresholds (p < .05). Use p < .001 for very small values
4. **Effect size**: With confidence interval
5. **Assumption checks**: Which checks were done, results, remedial actions

## Pre-Registration Guidance

### What to Report Before Data Collection

1. **Hypotheses**: Clearly stated, directional when appropriate
2. **Sample size justification**: Power analysis with expected effect size, alpha, and power
3. **Data collection stopping rule**: When will you stop collecting data?
4. **Variables**: All variables collected (not just those analyzed)
5. **Exclusion criteria**: Rules for excluding participants/data points
6. **Statistical analyses**: Planned tests, including:
   - Primary and secondary analyses
   - Exploratory analyses (labeled as such)
   - Handling of missing data
   - Multiple comparison corrections
   - Assumption checks planned

**Why pre-register?**
- Prevents HARKing (Hypothesizing After Results are Known)
- Distinguishes confirmatory from exploratory analyses
- Increases credibility and reproducibility

**Platforms**: Open Science Framework (OSF), AsPredicted, ClinicalTrials.gov

## Methods Section Templates

### Participants

Report: Total N (including excluded), relevant demographics, recruitment method, inclusion/exclusion criteria, attrition with reasons.

**Example**:
> "Participants were 150 undergraduate students (98 female, 52 male; M_age = 19.4 years, SD = 1.2, range 18-24) recruited from psychology courses. Five participants were excluded due to incomplete data (n = 3) or failing attention checks (n = 2), resulting in a final sample of 145."

### Design

Report: Study design (between/within/mixed), IVs and levels, DVs, control variables, randomization procedure, blinding.

**Example**:
> "A 2 (feedback: positive vs. negative) x 2 (timing: immediate vs. delayed) between-subjects factorial design was used. Participants were randomly assigned using a computer-generated sequence. The primary outcome was task performance (0-20 correct responses)."

### Measures

Report: Full name of measure, number of items, scale format, scoring method, reliability in current sample.

**Example**:
> "Depression was assessed using the Beck Depression Inventory-II (BDI-II; Beck et al., 1996), a 21-item self-report measure rated on a 4-point scale (0-3). Total scores range from 0-63. The BDI-II demonstrated excellent internal consistency in this sample (alpha = .91)."

### Data Analysis

Report: Software and version, alpha level, tails, assumption checks, missing data handling, outlier treatment, corrections, effect size measures.

**Example**:
> "All analyses were conducted using Python 3.10 with scipy 1.11 and statsmodels 0.14. Alpha was .05 for all tests. Normality and homogeneity were assessed via Shapiro-Wilk and Levene's tests. Missing data (< 2%) were handled via listwise deletion. Outliers beyond 3 SD were winsorized. Partial eta-squared is reported for ANOVA. Post hoc comparisons used Tukey's HSD."

## Reporting Templates

### Independent t-test

```
Group A (n = 48, M = 75.2, SD = 8.5) scored significantly higher than
Group B (n = 52, M = 68.3, SD = 9.2), t(98) = 3.82, p < .001, d = 0.77,
95% CI [0.36, 1.18], two-tailed. Assumptions of normality (Shapiro-Wilk:
Group A W = 0.97, p = .18; Group B W = 0.96, p = .12) and homogeneity
of variance (Levene's F(1, 98) = 1.23, p = .27) were satisfied.
```

### Paired t-test

```
Scores were significantly higher at post-test (M = 82.3, SD = 7.1) than
pre-test (M = 74.5, SD = 8.3), t(39) = 5.12, p < .001, d = 0.81,
95% CI [0.47, 1.15]. The difference scores were approximately normal
(Shapiro-Wilk W = 0.96, p = .21).
```

### Welch's t-test

```
Due to unequal variances (Levene's F(1, 98) = 6.45, p = .013), Welch's
t-test was used. Group A (M = 75.2, SD = 8.5) scored significantly higher
than Group B (M = 68.3, SD = 12.1), t(94.3) = 3.65, p < .001, d = 0.74.
```

### One-Way ANOVA

```
A one-way ANOVA revealed a significant main effect of treatment condition
on test scores, F(2, 147) = 8.45, p < .001, eta-squared_p = .10. Post hoc
comparisons using Tukey's HSD indicated that Condition A (M = 78.2,
SD = 7.3) scored significantly higher than Condition B (M = 71.5,
SD = 8.1, p = .002, d = 0.87) and Condition C (M = 70.1, SD = 7.9,
p < .001, d = 1.07). Conditions B and C did not differ significantly
(p = .52, d = 0.18). Homogeneity of variance was confirmed
(Levene's F(2, 147) = 0.89, p = .41).
```

### Factorial ANOVA

```
A 2 (Gender) x 3 (Treatment) factorial ANOVA was conducted. There was
a significant main effect of treatment, F(2, 114) = 12.3, p < .001,
eta-squared_p = .18, a non-significant main effect of gender, F(1, 114) = 0.45,
p = .50, eta-squared_p = .004, and a significant interaction, F(2, 114) = 4.56,
p = .012, eta-squared_p = .07. Simple effects analysis revealed...
```

### Repeated Measures ANOVA

```
A one-way repeated measures ANOVA revealed a significant effect of time
point on anxiety scores, F(2, 98) = 15.67, p < .001, eta-squared_p = .24.
Mauchly's test indicated sphericity was violated, chi-squared(2) = 8.45,
p = .01, therefore Greenhouse-Geisser corrected values are reported
(epsilon = 0.87). Pairwise comparisons with Bonferroni correction showed...
```

### Linear Regression

```
Multiple linear regression was conducted to predict exam scores from
study hours, prior GPA, and attendance. The overall model was significant,
F(3, 146) = 45.2, p < .001, R-squared = .48, adjusted R-squared = .47. Study hours
(B = 1.80, SE = 0.31, beta = .35, t = 5.78, p < .001, 95% CI [1.18, 2.42])
and prior GPA (B = 8.52, SE = 1.95, beta = .28, t = 4.37, p < .001,
95% CI [4.66, 12.38]) were significant predictors, while attendance was
not (B = 0.15, SE = 0.12, beta = .08, t = 1.25, p = .21,
95% CI [-0.09, 0.39]). Multicollinearity was not a concern (all VIF < 1.5).
Residual analysis confirmed normality and homoscedasticity assumptions.
```

### Logistic Regression

```
Binary logistic regression was conducted to predict recovery (yes/no)
from age, treatment, and baseline severity. The model was significant,
chi-squared(3) = 28.5, p < .001, Nagelkerke R-squared = .31. Treatment was a
significant predictor (B = 1.23, SE = 0.34, Wald = 13.1, p < .001,
OR = 3.42, 95% CI [1.76, 6.64]). For each unit increase in treatment
intensity, the odds of recovery increased by 3.42 times. The model
correctly classified 76% of cases (sensitivity = 81%, specificity = 68%).
```

### Correlation

```
There was a significant positive correlation between study hours and
exam scores, r(98) = .54, p < .001, 95% CI [.39, .66]. The assumption
of bivariate normality was checked using Shapiro-Wilk tests on both
variables (both p > .05). Approximately 29% of the variance in exam
scores was shared with study time (r-squared = .29).
```

### Chi-Square Test

```
A chi-square test of independence revealed a significant association
between treatment group and recovery status, chi-squared(2, N = 150) = 12.34,
p = .002, Cramer's V = .29. Expected cell frequencies were all > 5.
```

### Non-Parametric Tests

**Mann-Whitney U**:
```
A Mann-Whitney U test indicated that scores were significantly higher
for Group A (Mdn = 78.0) than Group B (Mdn = 65.5),
U = 845, z = -3.12, p = .002, r = .31.
```

**Kruskal-Wallis**:
```
A Kruskal-Wallis H test showed a significant difference in scores
across three conditions, H(2) = 15.23, p < .001. Post hoc pairwise
comparisons with Bonferroni correction indicated...
```

**Wilcoxon signed-rank**:
```
A Wilcoxon signed-rank test showed that scores increased significantly
from pretest (Mdn = 65, IQR = 15) to posttest (Mdn = 72, IQR = 14),
z = 3.89, p < .001, r = .39.
```

### Bayesian Analysis

```
A Bayesian independent samples t-test was conducted using weakly
informative priors (Normal(0, 1) for mean difference). The posterior
distribution indicated that Group A scored higher than Group B
(M_diff = 6.8, 95% credible interval [3.2, 10.4]). The Bayes Factor
BF10 = 45.3 provided very strong evidence for a difference between
groups, with a 99.8% posterior probability that Group A's mean exceeded
Group B's mean. Convergence diagnostics were satisfactory (all R-hat < 1.01,
ESS > 1000).
```

## Null Results Reporting

### How to Report Non-Significant Findings

**Do not say**: "There was no effect" or "X and Y are unrelated" or "Groups are equivalent."

**Do say**: "There was no significant difference" or "The effect was not statistically significant" or "We did not find evidence for a relationship."

**Always include** for non-significant results:
- Exact p-value (not just "ns" or "p > .05")
- Effect size (shows magnitude even if not significant)
- Confidence interval (may include meaningful values)
- Power/sensitivity analysis (was study adequately powered?)

**Example**:
> "Contrary to our hypothesis, there was no significant difference in creativity scores between the music (M = 72.1, SD = 8.3) and silence (M = 70.5, SD = 8.9) conditions, t(98) = 0.91, p = .36, d = 0.18, 95% CI [-0.21, 0.57]. A sensitivity analysis revealed that the study had 80% power to detect d >= 0.57, suggesting the null finding may reflect insufficient power to detect small effects."

## Formatting Conventions

### Numbers
- Report exact p-values to 2-3 decimal places: p = .032
- Use p < .001 for very small values (never p = .000)
- Two decimal places for test statistics: t(45) = 2.34
- Two decimal places for effect sizes: d = 0.52
- No leading zero for values bounded by +/-1: r = .45, p = .032

### Tables
- Include M, SD, n for each group
- Bold or italicize significant results
- Include effect sizes in results tables
- Horizontal lines only (not vertical)
- Notes below for clarifications

### Figures
- Error bars should show 95% CI (not SE or SD) -- label clearly
- Include individual data points when feasible (especially for n < 30)
- Use consistent formatting across all figures
- High resolution (>= 300 dpi for publications)
- Colorblind-accessible palettes

## Reporting Checklist

Before submitting, verify:
- [ ] Sample size and demographics reported
- [ ] Study design clearly described
- [ ] All measures described with reliability
- [ ] Software and versions specified
- [ ] Alpha level stated
- [ ] Assumption checks reported with results
- [ ] Descriptive statistics (M, SD, n) for all groups
- [ ] Test statistics with df and exact p-values
- [ ] Effect sizes with confidence intervals
- [ ] All planned analyses reported (including non-significant)
- [ ] Multiple comparison corrections described
- [ ] Missing data handling explained
- [ ] Figures/tables properly formatted and labeled
- [ ] Limitations discussed
- [ ] Data/code availability statement included
- [ ] Pre-registration referenced (if applicable)

## Common Reporting Errors

1. Writing "p = .000" -- use "p < .001"
2. Omitting degrees of freedom -- always include: t(df), F(df1, df2)
3. Reporting only p-values without effect sizes
4. Using "marginally significant" for p values between .05 and .10
5. Not specifying one-tailed vs two-tailed
6. Omitting assumption check results
7. Using "prove" or "confirm" -- use "support" or "consistent with"
8. Inconsistent decimal places throughout the paper
9. Not reporting non-significant results from planned analyses
10. Omitting confidence intervals for effect sizes

## Condensation Note

Condensed from original: 470 lines. Retained: essential reporting elements, pre-registration guidance (what to report, why, platforms), methods section templates (participants, design, measures, data analysis) with examples, all reporting templates (independent t-test, paired t-test, Welch's t-test, one-way ANOVA, factorial ANOVA, repeated measures ANOVA, linear regression, logistic regression, correlation, chi-square, non-parametric tests, Bayesian analysis), null results reporting guidance with example, formatting conventions (numbers, tables, figures), reporting checklist, common reporting errors. Omitted: detailed figure/table guidelines (common figure types list, example table with data) -- standard APA knowledge available in Publication Manual; reproducibility section (data/code sharing platforms) -- general guidance covered by lab-management-reproducibility knowhow.
