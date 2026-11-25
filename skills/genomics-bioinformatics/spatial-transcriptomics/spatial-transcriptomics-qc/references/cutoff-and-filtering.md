# Shared Cutoff Recommendation and Filtering Contract

Read this reference after the platform-specific engine has produced metrics and
package flags. It is the common contract for distribution review, cutoff
recommendation, D2 approval, filtering, and reporting. It deliberately does
not define a mandatory three-class classification or require biological
evidence integration.

## Required order

```text
official package (preferred) or bundled fallback
-> metric/flag table on the complete analysis denominator
-> overall and per-sample distributions plus spatial maps
-> agent reviews the actual plots and recommends cutoffs/rules
-> exact-rule impact calculation
-> completed QC report
-> D2 only when the user requests filtering
-> separately named filtered copy
-> report
```

Never select a final numeric cutoff before reviewing the observed data. Package
defaults, robust fences, local-z cutoffs, and package flags are useful reference
results; none is automatically the final filtering condition.

## Two distinct outputs

Keep these concepts in separate columns and report sections:

1. **Metric/package result**: an individual SpaceTrooper outlier label,
   SpotSweeper local-outlier flag, systematic-position flag, or artifact flag.
2. **Selected filtering match**: a cell/spot satisfies the exact final rule
   recommended by the agent or selected by the user.

An object can have many metric-level flags but only one current
`selected_filter_match` derived from the approved rule set. Never remove an
observation merely because one package flag is true.

## One machine-readable rule source

Store every proposed condition in `qc_filter_rules.tsv`. Give each individual
metric proposal, the agent's final recommendation, and every later user choice
a distinct `rule_set_id`; recommendation rows never become active merely
because their status says `recommended`:

```text
rule_set_id,rule_id,status,metric,operator,threshold,upper_threshold,
rule_kind,package,function,parameters,reason,no_cutoff_reason
```

Allowed `operator` values are `lt`, `le`, `gt`, `ge`, `outside`, `inside`,
`true`, `false`, `is_na`, and `not_na`. Missing values match none of the
numeric/Boolean operators; removal of missing QScore or flag values therefore
requires a separate explicit `is_na` rule. Numeric rows contain the plotting-
scale threshold. Boolean rows identify package flags and leave numeric
threshold fields empty. Set
`status=no_cutoff` when the distribution does not support a defensible cutoff
and explain why.

For a multi-rule final condition, also record:

```text
rule_set_id,logic,expression
qc-final-001,OR,(qscore < 0.31) OR sum_outliers
```

`logic` must be `AND` or `OR`; the readable expression must agree with it.
Do not describe a mixed expression only as “combined QC”.

The calculator supports one flat operator across the named rule set: `A AND B`
or `A OR B OR C`. It does **not** parse parentheses or mixed nested expressions
such as `(A AND B) OR C`. Do not recommend, preview, approve, or apply a nested
condition with this calculator. Select a defensible flat rule set instead; if a
nested expression is scientifically necessary, report it as unsupported rather
than approximating it with a different mask.

Use the bundled deterministic calculator after editing the rule table:

Copy
`/SciAgent-Skills/skills/genomics-bioinformatics/spatial-transcriptomics/spatial-transcriptomics-qc/scripts/qc_apply_rules.py`
unchanged into the analysis workspace, then run:

```bash
python qc_apply_rules.py \
  --metrics qc_metrics.tsv \
  --rules qc_filter_rules.tsv \
  --rule-set-id qc-final-001 \
  --logic OR \
  --mode preview \
  --id-column observation_id \
  --group-column sample_id \
  --output-prefix qc_recommendation
```

This writes per-rule matches, `selected_filter_match`, overall/per-group
counts, the exact selected rows, and a SHA-256 rule-set digest. It ignores all
other rule sets. Re-run preview whenever a threshold, selected rule, or AND/OR
operator changes.

## Distribution review and recommendation

For QScore and every major available numeric metric:

- plot the full distribution and one panel per sample/FOV;
- use the same transform used by the engine and label that transform;
- show package fences/default flags as references when available;
- inspect separation, tails, sample shifts, missing values, and sensitivity of
  removal counts near plausible cutoffs;
- recommend a cutoff and direction only when the observed distribution makes
  it defensible;
- explain `no_cutoff` instead of forcing every metric to have one.

For every recommended cutoff, report the exact value, direction, reason,
overall count/percentage, per-sample count/percentage, and a spatial map of
matched observations. QScore is the preferred imaging final numeric criterion
when it is valid, but its package default `0.5` is not privileged.

For package flags without a raw-metric cutoff, show flag counts and spatial
maps separately. In SpotSweeper, distinguish raw metric cutoffs from
`*_outliers`, `systematic_outliers`, and `artifact`.

## Observation accounting

Maintain the complete input denominator and record non-filtering losses
(loader mismatch, join loss, analysis view, polygon matching) separately from
D2-approved filtering. At minimum, write:

```text
stage,input_count,output_count,lost_count,loss_type,reason,user_approved
```

Only `intentional_filtering` may represent D2-approved removal. Polygon-
unmatched or package-loader-lost cells are not metric outliers.

## D2 choices

If the user requested QC only, provide the completed report and record D2 as
`not_applicable`; do not ask them to choose a filtering rule. Ask D2 only after
the user requests filtering and after showing the exact expected impact.
Offer these choices:

- apply the agent's final recommended rule;
- apply one named metric at its recommended cutoff;
- apply a user-specified condition;
- report QC without filtering.

If the user chooses another condition, update `qc_filter_rules.tsv`, state
AND/OR explicitly, re-run impact calculation, show the revised removal count
and percentage, and obtain approval for that exact revision. Assessment-only
requests may record D2 as `not_applicable` and stop without asking.

Before filtering, require a JSON D2 approval record containing
`approved=true`, the current `rule_set_id`, `logic`, and the preview manifest's
`rule_set_digest`. Run the calculator with `--mode apply --approval-record
d2.json`. Any rule or logic change changes the digest and invalidates the old
approval. Preserve the source object and create a separately named copy.
The applied mask must be the calculator's `selected_filter_match`; do not
re-code the condition ad hoc.

## Report contract

The report contains:

1. tool, package version/commit when known, and official/fallback execution;
2. fallback reason and declared parity limitations;
3. each function's `completed`, `skipped`, or `failed` state, actual
   parameters, and reason; optional failures do not erase completed outputs;
4. overall/per-sample metric and QScore distributions with exact cutoffs;
5. per-cutoff direction, rationale, count, percentage, and spatial map;
6. package outlier/artifact flags separately from numeric cutoff results;
7. final recommended rule with explicit AND/OR and expected impact;
8. D1/D2 state and, if approved, the separately named filtered output;
9. observation accounting and confirmation that the source was preserved.

The cutoff in the rule table, plot annotation, expected-impact table, D2 text,
and applied filtering mask must be identical.
