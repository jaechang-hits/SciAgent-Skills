# Shared Spatial QC Assessment and Filtering Policy

Read this reference after the platform-specific metric engine has finished. It
is shared by `spatial-transcriptomics-spot-qc` and
`spatial-transcriptomics-imaging-qc`. The engine-specific Skill owns metric
calculation; this reference owns interpretation, recommendation, visualization,
impact validation, approval, and reporting.

## Fixed stage order

```text
metric and package flags
-> integrated evidence assessment
-> candidate rule recommendation
-> cutoff/flag visualization
-> expected-impact validation
-> conditional D2
-> optional filtered copy
-> report
```

Do not report QC as complete when metrics ran but integrated assessment or
impact validation did not. A package flag, robust fence, 3-MAD rule, or one
metric cutoff is evidence, not a filtering decision.

## Observation accounting

Use one schema for loader, join, analysis-view, polygon-matching and final
filtering transitions:

```text
stage,input_count,output_count,lost_count,loss_type,reason,user_approved,id_evidence
```

Allowed loss types include `input_or_join_loss`, `loader_loss`,
`analysis_view`, `polygon_matching_loss`, and `intentional_filtering`. Only the
last may represent D2-approved removal.

```python
from pathlib import Path
import pandas as pd

def record_transition(stage, before_ids, after_ids, loss_type, reason,
                      user_approved=False):
    before = pd.Index(before_ids.astype(str), name="observation_id")
    after = pd.Index(after_ids.astype(str), name="observation_id")
    lost = before.difference(after)
    evidence = ""
    if len(lost):
        evidence = f"qc_lost_ids_{stage}.tsv"
        lost.to_frame().to_csv(evidence, sep="\t", index=False)
    row = pd.DataFrame([{"stage": stage, "input_count": len(before),
        "output_count": len(after), "lost_count": len(lost),
        "loss_type": loss_type, "reason": reason,
        "user_approved": bool(user_approved), "id_evidence": evidence}])
    path = Path("qc_observation_accounting.tsv")
    row.to_csv(path, sep="\t", index=False, mode="a",
               header=not path.exists())
```

Preserve the complete ID denominator for impact calculations. Never relabel a
loader or polygon-matching loss as intentional filtering.

## Evidence domains

Group correlated measurements before judging concordance:

| Domain | Examples | Interpretation constraint |
|---|---|---|
| signal amount | total counts, detected genes, signal density | correlated; do not count as three independent reasons |
| controls/background | negative probes, unassigned codewords, control ratio | requires validated control annotation |
| geometry | cell/spot area, aspect ratio, multipolygon state | may reflect biology or segmentation |
| spatial context | local outlier, coherent region, FOV border | coherent biology is not automatically an artifact |
| model score | QScore and its low-score flag | one evidence domain, never two votes |
| morphology/labels | image, tissue region, cell type | use only when actually present |

For every proposed rule, record which domains agree, which are missing, and
whether a biological explanation remains. If evidence conflicts or a plausible
biological alternative is unresolved, classify the observation as `Review`,
not `Exclude candidate`.

## Single recommendation configuration

Use `qc_cutoff_recommendations.tsv` as the one configuration used by plots,
classification, impact calculations, D2, and reporting. Required columns:

```text
rule_set_id,revision,rule_id,recommendation_type,recommendation_status,
metric,flag_column,method,direction,transformation,threshold,
lower_threshold,upper_threshold,grouping,group_value,package,function,
version,parameters,evidence_domains,component_rule_ids,rationale,caveat,
biological_loss_risk,validation_status
```

Allowed `recommendation_type` values:

- `metric_cutoff`: supporting numeric threshold or interval.
- `metric_flag`: package-derived evidence without an exposed numeric fence.
- `integrated_filtering_rule`: documented combination of evidence domains that
  may propose `Review` or `Exclude candidate`.

A numeric row marked `recommended` must contain its actual plotting-scale
value. If no defensible cutoff exists, leave threshold fields empty and set the
recommendation to `inconclusive`. Never silently substitute 3-MAD, a package
default, or a fixed number of flags as the final rule.

## Candidate tables, including zero candidates

`qc_candidate_rule_matches.tsv` has this schema:

```text
observation_id,rule_id,proposed_class,evidence_ids,evidence_domains,
rationale,validation_status
```

An empty or header-only match file is valid. A zero-byte file must be normalized
to the declared schema before reading downstream. Absence of a file is not the
same as zero candidates and must be reported as an incomplete assessment.

```python
from pathlib import Path
import pandas as pd

columns = ["observation_id", "rule_id", "proposed_class", "evidence_ids",
           "evidence_domains", "rationale", "validation_status"]
path = Path("qc_candidate_rule_matches.tsv")
if not path.exists():
    raise FileNotFoundError("integrated assessment did not create candidate matches")
matches = (pd.DataFrame(columns=columns) if path.stat().st_size == 0 else
           pd.read_csv(path, sep="\t", dtype={"observation_id": str}))
missing = set(columns) - set(matches.columns)
if missing:
    raise ValueError(f"candidate matches missing columns: {sorted(missing)}")
matches.to_csv(path, sep="\t", index=False, columns=columns)
```

Classify on the complete analysis denominator:

```python
review_ids = set(matches.loc[
    matches["proposed_class"].eq("Review") |
    ~matches["validation_status"].eq("supported"), "observation_id"])
exclude_ids = set(matches.loc[
    matches["proposed_class"].eq("Exclude candidate") &
    matches["validation_status"].eq("supported"), "observation_id"]) - review_ids

adata.obs["qc_class"] = "Retain"
ids = adata.obs_names.astype(str)
adata.obs.loc[ids.isin(exclude_ids), "qc_class"] = "Exclude candidate"
adata.obs.loc[ids.isin(review_ids), "qc_class"] = "Review"
```

Polygon-unmatched, loader-lost, or join-lost observations belong in observation
accounting, not in a metric-derived candidate rule. Their absence from a
package-loaded object is not itself an outlier result.

## Required visualization

Plot every major available metric distribution, including QScore when present.
For each recommended numeric cutoff, show the exact cutoff on the distribution
and map its affected observations in space. For package flags without a numeric
fence, save the package plot and a spatial flag map without inventing a line.

```python
import matplotlib.pyplot as plt
import numpy as np

values = pd.to_numeric(adata.obs[metric], errors="coerce").to_numpy()
finite = np.isfinite(values)
fig, ax = plt.subplots(figsize=(6, 4))
ax.hist(values[finite], bins=60, color="#64748b", alpha=0.85)
if recommendation_type == "metric_cutoff":
    ax.axvline(float(threshold), color="#dc2626", lw=2)
fig.tight_layout()
fig.savefig(distribution_path, dpi=200)
```

```python
xy = np.asarray(adata.obsm["spatial"], dtype=float)
fig, ax = plt.subplots(figsize=(6, 6))
ax.scatter(xy[:, 0], xy[:, 1], s=1, c="#cbd5e1")
ax.scatter(xy[affected, 0], xy[affected, 1], s=3, c="#dc2626")
ax.invert_yaxis(); ax.set_aspect("equal")
fig.tight_layout(); fig.savefig(spatial_path, dpi=200)
```

Keep metric-level affected observations separate from final expected
exclusions in both tables and legends.

## Impact validation

Before D2, calculate all of the following on the full baseline denominator:

- Retain/Review/Exclude-candidate counts and percentages overall.
- The same counts by sample/FOV and, when available, tissue region/cell type.
- Per-metric affected counts separately from final integrated exclusions.
- Spatial distribution of Review and Exclude candidates.
- Expected artifact reduction and plausible biological information loss.
- Effect of unavailable packages, images, controls, polygons, or labels.

```python
class_order = ["Retain", "Review", "Exclude candidate"]
overall = adata.obs["qc_class"].value_counts().reindex(class_order, fill_value=0)
impact = overall.rename("count").to_frame()
impact["percent"] = 100 * impact["count"] / adata.n_obs
impact.to_csv("qc_filtering_impact_overall.tsv", sep="\t")
```

```python
for group in ["sample_id", "fov", "tissue_region", "cell_type"]:
    if group not in adata.obs:
        continue
    table = pd.crosstab(adata.obs[group], adata.obs["qc_class"], dropna=False)
    table = table.reindex(columns=class_order, fill_value=0)
    pct = table.div(table.sum(axis=1), axis=0).mul(100).add_suffix("_percent")
    table.join(pct).to_csv(f"qc_filtering_impact_by_{group}.tsv", sep="\t")
```

Every integrated rule receives `impact_summary`, `biological_loss_risk`,
`missing_evidence`, and `final_decision` (`keep`, `revise`, or `inconclusive`).
Do not proceed to D2 while a proposed exclusion depends only on revised or
inconclusive evidence. Revise and repeat assessment, or move it to Review.

## D2 policy

D2 is required immediately before creating a separately named filtered copy.
It is not required to calculate or visualize expected impact.

- Assessment-only request: record `not_applicable`; do not ask.
- No `Exclude candidate` observations: record `not_applicable`; do not ask.
- Filtering requested with candidates: show the exact final `rule_set_id`,
  rules, plots, expected impact, and biological-loss risk, then ask once.
- A changed effective rule set requires a new `rule_set_id` and a new D2 scope.
- D1 approval for imaging geometry never implies D2 approval.

```python
approval = pd.read_csv("qc_approval_state.tsv", sep="\t")
rule_sets = recommendations["rule_set_id"].dropna().astype(str).unique()
if len(rule_sets) != 1:
    raise ValueError("expected one current rule_set_id")
d2 = approval.loc[approval["decision"].eq("D2") &
                  approval["scope"].astype(str).eq(rule_sets[0])]
if len(d2) != 1 or d2.iloc[0]["status"] != "approved":
    raise PermissionError("filtering requires explicit D2 for this rule set")
keep = ~adata.obs["qc_class"].eq("Exclude candidate")
adata_filtered = adata[keep].copy()
adata_filtered.write_h5ad("spatial_qc_filtered_copy.h5ad")
```

The source object remains unchanged. Record the final transition as the only
`intentional_filtering` row in observation accounting.

## Required report

The report must include:

1. Input type, platform evidence, observation unit, capabilities, and uncertainty.
2. Runtime/package/API/input/execution status and actual function parameters.
3. Metric distributions, maps, package flags, QScore when available, and any
   approved polygon results.
4. Integrated evidence domains, biological alternatives, and missing evidence.
5. Recommendation plots, impact overall/by group, validation decision, and risk.
6. Complete observation accounting, including non-filtering losses.
7. D1/D2 state, whether filtering occurred, and output paths.

Do not label a Python fallback as package execution, call a centroid map a
neighbourhood test, hide a count decrease, or claim filtering without D2.
