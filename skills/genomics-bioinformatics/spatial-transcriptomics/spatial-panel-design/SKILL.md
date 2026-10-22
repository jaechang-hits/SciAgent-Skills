---
name: "spatial-panel-design"
description: "Spatial transcriptomics gene panel design (Xenium, MERFISH, CosMx custom panels) for cell type identification: rank markers on a tissue-matched CELLxGENE scRNA-seq reference, add PanglaoDB and CellMarker 2.0 marker evidence, build a per-gene evidence table, allocate per-cell-type quotas, and check that the panel separates cell types in the reference. Output: final_gene_panel.csv with N genes, cell type and reason. For annotating data from an existing panel use spatial-transcriptomics-cell-type-annotation."
license: "CC-BY-4.0"
---

# Spatial Gene Panel Design

## Overview

Pick exactly N genes that let an imaging-based platform identify every major
cell type of a tissue. Code builds the evidence; you (the agent) make the
final selection from the evidence table and write a reason per gene. Output:
a per-gene evidence table and `final_gene_panel.csv` with N genes, the cell
type each marks, its evidence and a reason.

## When to Use

- Designing a custom Xenium, MERFISH or CosMx gene panel for a tissue and state
- Choosing add-on genes to extend a vendor base panel for missing cell types
- Checking that a proposed panel can separate the cell types the study needs
- Documenting why each panel gene was chosen, with reference and database evidence
- Comparing candidate markers from a reference with PanglaoDB and CellMarker 2.0
- Use `spatial-transcriptomics-cell-type-annotation` instead when the panel already exists and data must be annotated
- For genes the panel will not measure, use the gene imputation route of `spatial-mapping-tangram` after the experiment

## Prerequisites

- **From the user**: organism, tissue, state (healthy or a disease) and panel size N
- **Reference**: tissue- and state-matched; run Steps 3-4 of
  `spatial-transcriptomics-cell-type-annotation` (same code), adding
  `"cell_type_ontology_term_id"` to `obs_column_names`, with `GENES = None`
  (markers are ranked over every gene) and `MAX_PER_TYPE = 300`, to get `reference.h5ad`
- **Literature**: ask the research subagent / literature tools for published panels
  and canonical markers of this tissue; add what they return in Step 5
- **Python packages**: `cellxgene-census`, `scanpy`, `openpyxl`, `scikit-learn`

```bash
# Install only what `import` reports missing. `--pypi` keeps the env's scanpy/numba
# stack; a conda add can swap it and bare pip can shadow it.
pixi add --pypi cellxgene-census scanpy openpyxl scikit-learn
```

## Pre-flight Interview

```yaml
decisions:
  - id: D1
    param: ORGANISM
    kind: required
    source: user
    ask: "Human or mouse tissue?"
    default: null
  - id: D2
    param: TISSUE
    kind: required
    source: user
    ask: "Which tissue will be profiled?"
    default: null
  - id: D3
    param: STATE
    kind: required
    source: user
    ask: "Healthy tissue, or which disease or tumour?"
    default: null
  - id: D4
    param: PANEL_SIZE
    kind: required
    source: user
    ask: "How many genes can the panel hold?"
    default: null
  - id: D5
    param: basePanel
    kind: required
    source: user
    ask: "Is this a standalone custom panel, or add-on genes for a vendor base panel (which one)?"
    default: "standalone panel"
  - id: D6
    param: DATASET_ID
    kind: required
    source: data
    depends_on: [D1, D2, D3]
    ask: "These CELLxGENE datasets match the tissue and state: which one should be the reference?"
    default: null
  - id: D7
    param: cellTypeResolution
    kind: required
    source: data
    depends_on: [D4, D6]
    ask: "These are the reference cell types; for a panel of this size I propose merging <fine states> into <lineages>. Which types must the panel separate?"
    default: "major lineages; merge fine states the panel size cannot resolve"
  - id: D8
    param: requiredGenes
    kind: optional
    source: user
    ask: "Are there genes that must be on the panel (study targets, known markers)?"
    default: "none"
  - id: D9
    param: MIN_PER_TYPE
    kind: optional
    source: user
    ask: "At least how many genes per cell type, so rare but important types are covered?"
    default: "3"
  - id: D10
    param: cancerTypeFilter
    kind: derived
    source: upstream
    depends_on: [D3]
    ask: "Keep tumour-derived CellMarker entries?"
    default: "Normal only for healthy tissue; drop the filter for tumour panels"
```

Ask D1-D5 together. D6 and D7 come in a later round, after the Census search
and the reference's cell types are known; D8 genes join the evidence table as
rows in Step 5.

## Workflow

1. Load the reference and true cell type abundance
2. Rank reference markers per cell type
3. PanglaoDB markers
4. CellMarker 2.0 markers
5. Build the evidence table
6. Allocate quotas and draft the panel
7. Check the panel separates cell types, then save

### Step 1: Reference and Abundance

The Step 4 reference is capped per cell type, so take real abundance from the
full dataset metadata:

```python
import cellxgene_census
import numpy as np
import pandas as pd
import scanpy as sc

ORGANISM, TISSUE, PANEL_SIZE = "Homo sapiens", "liver", 100
DATASET_ID = "<dataset_id used for reference.h5ad>"

ref = sc.read_h5ad("reference.h5ad")          # X = raw counts
ref.layers["counts"] = ref.X.copy()
sc.pp.normalize_total(ref)
sc.pp.log1p(ref)

with cellxgene_census.open_soma(census_version="stable") as census:
    obs = census["census_data"][ORGANISM.lower().replace(" ", "_")].obs.read(
        value_filter=f"dataset_id == '{DATASET_ID}'", column_names=["cell_type"]).concat().to_pandas()
abundance = obs["cell_type"].value_counts(normalize=True)

keep = ref.obs["cell_type"].value_counts()
keep = keep[keep >= 20].index                  # too few cells for stable markers
ref = ref[ref.obs["cell_type"].isin(keep)].copy()
ref.obs["cell_type"] = ref.obs["cell_type"].astype("category").cat.remove_unused_categories()
ct_ids = ref.obs.groupby("cell_type", observed=True)["cell_type_ontology_term_id"].first()
print(pd.DataFrame({"fraction": abundance.reindex(keep).round(4), "cl_id": ct_ids}))
```

Merge or drop types the platform cannot be expected to resolve (e.g. ten T
cell states for a 100-gene panel) before going on:
`ref.obs["cell_type"] = ref.obs["cell_type"].replace({...})`, and apply the
same mapping to `obs["cell_type"]` before computing `abundance`, `keep` and
`ct_ids` (CellMarker then joins on the IDs of the kept fine types only).

### Step 2: Reference Markers

```python
sc.tl.rank_genes_groups(ref, "cell_type", method="wilcoxon", pts=True)
rk = sc.get.rank_genes_groups_df(ref, group=None)
rk = rk.rename(columns={"group": "cell_type", "names": "gene"})
rk = rk[(rk["logfoldchanges"] > 1) & (rk["pvals_adj"] < 0.01) & (rk["pct_nz_group"] >= 0.3)]
rk["specificity"] = rk["pct_nz_group"] - rk["pct_nz_reference"]
ref_markers = rk.sort_values(["cell_type", "scores"], ascending=[True, False]).groupby("cell_type").head(30)
print(ref_markers.groupby("cell_type").head(5)[["cell_type", "gene", "logfoldchanges", "pct_nz_group", "pct_nz_reference"]])
```

### Step 3: PanglaoDB Markers

The PanglaoDB site (panglaodb.se) was unreachable when this guide was
written; Enrichr serves its marker sets as the `PanglaoDB_Augmented_2021`
library (human symbols, cell type names without tissue):

```python
import os
import re
import requests

os.makedirs("ref_cache", exist_ok=True)
PANGLAO = "ref_cache/PanglaoDB_Augmented_2021.txt"
if not os.path.exists(PANGLAO):
    url = "https://maayanlab.cloud/Enrichr/geneSetLibrary?mode=text&libraryName=PanglaoDB_Augmented_2021"
    open(PANGLAO, "w").write(requests.get(url, timeout=300).text)
panglao = {}
for line in open(PANGLAO):
    name, _, *genes = line.rstrip("\n").split("\t")
    panglao[name] = {g.split(",")[0] for g in genes if g}

def norm(s):
    s = re.sub(r"\bcells?\b", "", s.lower())
    return re.sub(r"[^a-z0-9]+", " ", s).strip().rstrip("s")

# Keyword match reference cell types to library names; review and fix by hand.
name_map = {ct: [p for p in panglao if norm(p) and (norm(p) in norm(ct) or norm(ct) in norm(p))]
            for ct in keep}
for ct, hits in name_map.items():
    print(f"{ct:45s} -> {hits}")
```

Edit `name_map` where the match is wrong or empty (e.g. "Kupffer cell" ->
`["Kupffer Cells"]`), then collect:

```python
pang = pd.DataFrame([(ct, g) for ct, names in name_map.items() for n in names for g in panglao[n]],
                    columns=["cell_type", "gene"]).drop_duplicates()
pang["panglao"] = True
if ORGANISM == "Mus musculus":       # library is human; map with an ortholog table, not by case
    print("convert PanglaoDB symbols to mouse orthologs before merging")
print(pang.groupby("cell_type").size())
```

### Step 4: CellMarker 2.0 Markers

CellMarker 2.0 carries Cell Ontology IDs, so it joins the reference by ID, not
by name. The official mirror (NAR 2023) serves the files:

```python
species = "Human" if ORGANISM == "Homo sapiens" else "Mouse"
CM = f"ref_cache/Cell_marker_{species}.xlsx"
if not os.path.exists(CM):
    url = f"http://117.50.127.228/CellMarker/CellMarker_download_files/file/Cell_marker_{species}.xlsx"
    open(CM, "wb").write(requests.get(url, timeout=600).content)
cm = pd.read_excel(CM)
cm = cm[(cm["cancer_type"] == "Normal") & cm["Symbol"].notna()]   # drop for tumour panels
cm["cl_id"] = cm["cellontology_id"].astype(str).str.replace("_", ":")
id_to_ct = {v: k for k, v in ct_ids.items()}
cm["cell_type"] = cm["cl_id"].map(id_to_ct)
cm = cm[cm["cell_type"].notna()]
in_tissue = cm["tissue_class"].str.contains(TISSUE, case=False, na=False)
cmk = (cm.assign(in_tissue=in_tissue).groupby(["cell_type", "Symbol"])
         .agg(cm_pmids=("PMID", "nunique"), cm_in_tissue=("in_tissue", "any")).reset_index()
         .rename(columns={"Symbol": "gene"}))
print(cmk.sort_values("cm_pmids", ascending=False).groupby("cell_type").head(3))
```

Cell types with no ID match fall back to the `cell_name` column with the
`norm()` matching from Step 3.

### Step 5: Evidence Table

One row per (cell type, gene) candidate, measured in the reference:

```python
cand = pd.concat([ref_markers[["cell_type", "gene"]], pang[["cell_type", "gene"]],
                  cmk[["cell_type", "gene"]]]).drop_duplicates()
cand = cand[cand["gene"].isin(ref.var_names)]           # unmeasured genes cannot be checked

X = ref[:, cand["gene"].unique()]
expr = pd.DataFrame(X.X.toarray() if hasattr(X.X, "toarray") else X.X,
                    index=ref.obs_names, columns=X.var_names)
grp = ref.obs["cell_type"]
pct = (expr > 0).groupby(grp, observed=True).mean()
mean = expr.groupby(grp, observed=True).mean()

ev = cand.merge(rk[["cell_type", "gene", "logfoldchanges", "specificity"]], how="left", on=["cell_type", "gene"])
ev = ev.merge(pang, how="left", on=["cell_type", "gene"]).merge(cmk, how="left", on=["cell_type", "gene"])
ev["pct_in"] = [pct.at[c, g] for c, g in zip(ev["cell_type"], ev["gene"])]
ev["pct_out_max"] = [pct.drop(index=c)[g].max() for c, g in zip(ev["cell_type"], ev["gene"])]
ev["mean_log"] = [mean.at[c, g] for c, g in zip(ev["cell_type"], ev["gene"])]
ev["in_reference_de"] = ev["logfoldchanges"].notna()
ev["panglao"] = ev["panglao"].fillna(False).astype(bool)
ev["cm_pmids"] = ev["cm_pmids"].fillna(0).astype(int)
ev["n_sources"] = ev["in_reference_de"].astype(int) + ev["panglao"] + (ev["cm_pmids"] > 0)
ev = ev[ev["pct_in"] >= 0.2].sort_values(["cell_type", "n_sources", "specificity"], ascending=[True, False, False])
ev.to_csv("panel_evidence.csv", index=False)
print(ev.groupby("cell_type").head(5).to_string(max_cols=12))
```

Add literature or user-required genes as rows with a note before Step 6.

### Step 6: Quotas and Draft Panel

Quota grows with the square root of abundance so rare types still get genes:

```python
MIN_PER_TYPE = 3
w = np.sqrt(abundance.reindex(keep).fillna(0) + 1e-3)
quota = (MIN_PER_TYPE + (PANEL_SIZE - MIN_PER_TYPE * len(keep)) * w / w.sum()).round().astype(int)
quota.iloc[0] += PANEL_SIZE - quota.sum()                 # make it sum to N
assert quota.min() >= 1, "too many cell types for this panel size - merge types in Step 1"

picked, used = [], set()
for ct, q in quota.sort_values().items():                 # fill rare types first
    rows = ev[(ev["cell_type"] == ct) & ~ev["gene"].isin(used)].head(q)
    picked.append(rows)
    used.update(rows["gene"])
draft = pd.concat(picked)
print(pd.DataFrame({"quota": quota, "picked": draft["cell_type"].value_counts()}).fillna(0).astype(int))
print(f"draft: {draft['gene'].nunique()} / {PANEL_SIZE} genes")
```

Review `draft` against `panel_evidence.csv`: swap genes with low
`pct_in`, high `pct_out_max` or one weak source; keep canonical markers even
if one source misses them; fill any shortfall from the next rows of the
under-filled types. Very highly expressed genes (top `mean_log`) can crowd
imaging-based assays - check the vendor's panel limits.

### Step 7: Check Separation, then Save

```python
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report
from sklearn.model_selection import cross_val_predict

panel = list(dict.fromkeys(draft["gene"]))
Xp = ref[:, panel].X
Xp = Xp.toarray() if hasattr(Xp, "toarray") else Xp
pred = cross_val_predict(LogisticRegression(max_iter=2000), Xp, ref.obs["cell_type"].astype(str), cv=5)
print(classification_report(ref.obs["cell_type"].astype(str), pred, zero_division=0))

final = draft.drop_duplicates("gene")[["gene", "cell_type", "n_sources", "logfoldchanges", "pct_in", "pct_out_max",
                                       "panglao", "cm_pmids"]].rename(columns={"gene": "Gene"})
final["Reason"] = ""          # fill: cell type marked, function, sources, reference pct_in
assert len(final) == PANEL_SIZE, f"panel has {len(final)} genes, need {PANEL_SIZE}"
final.to_csv("final_gene_panel.csv", index=False)
```

Types with recall below ~0.7 need more or better genes; confused pairs show
which. Write each `Reason` as one or two specific sentences, e.g. "Hepatocyte
marker encoding serum albumin; top reference DE gene (98% of hepatocytes),
also in PanglaoDB and CellMarker 2.0."

## Key Parameters

| Parameter | Default | Effect |
|---|---|---|
| `PANEL_SIZE` | from the user | Number of genes; must be met exactly |
| reference `STATE` | from the user | Healthy vs disease reference changes which types and markers appear |
| `MIN_PER_TYPE` | 3 | Floor per cell type; raise for rare but important types |
| `logfoldchanges` / `pct_nz_group` filters | > 1 / >= 0.3 | Strictness of reference markers |
| `pct_in` floor | 0.2 | Drops markers detected in few cells of their type |
| CellMarker `cancer_type` filter | `Normal` | Remove for tumour panels |

## Common Recipes

### Recipe: Add-on Genes for a Vendor Base Panel

Most imaging panels are a fixed base panel plus custom genes. Count how well
the base already covers each type, then spend the custom budget where it is
thin:

```python
BASE_PANEL = set(pd.read_csv("base_panel.csv")["gene"])     # vendor gene list
ADD_ON_SIZE = 50
covered = ev[ev["gene"].isin(BASE_PANEL)].groupby("cell_type")["gene"].nunique().reindex(keep).fillna(0)
need = (MIN_PER_TYPE + 2 - covered).clip(lower=0)            # aim for ~5 good markers per type
print(pd.DataFrame({"base_markers": covered.astype(int), "need": need.astype(int)}))
add_ev = ev[~ev["gene"].isin(BASE_PANEL)]
add_on = (add_ev[add_ev["cell_type"].isin(need[need > 0].index)]
          .groupby("cell_type", group_keys=False).apply(lambda d: d.head(int(need[d.name]))))
print(f"proposed add-ons: {add_on['gene'].nunique()} (budget {ADD_ON_SIZE})")
add_on.to_csv("addon_candidates.csv", index=False)
```

Trim or extend `add_on` to the budget from the evidence table, as in Step 6.

### Recipe: Which Cell Types the Panel Confuses

The classification report gives recall per type; the confusion matrix says
which pairs are mixed up and so where to add discriminating genes:

```python
from sklearn.metrics import confusion_matrix

labels = sorted(ref.obs["cell_type"].astype(str).unique())
cm_ = pd.DataFrame(confusion_matrix(ref.obs["cell_type"].astype(str), pred, labels=labels, normalize="true"),
                   index=labels, columns=labels)
off = cm_.where(~np.eye(len(labels), dtype=bool)).stack().sort_values(ascending=False)
print(off.head(10).round(2))                     # (true type, predicted type): fraction misassigned
a, b = off.index[0]
diff = pct.loc[a] - pct.loc[b]
print(f"genes separating {a} from {b}:", diff.abs().nlargest(10).index.tolist())
```

## Expected Outputs

- `ref_cache/` - downloaded PanglaoDB and CellMarker files
- `panel_evidence.csv` - candidate genes with reference stats and database support
- `final_gene_panel.csv` - Gene, cell_type, evidence columns, Reason

## Troubleshooting

| Problem | Cause | Fix |
|---|---|---|
| A cell type has no PanglaoDB match | Name differs | Edit `name_map` by hand; leave empty if no equivalent |
| CellMarker download fails | Mirror down or blocked | Retry later; the panel can proceed on reference + PanglaoDB evidence, state it |
| Few CellMarker rows join | Reference uses finer CL terms | Fall back to `cell_name` matching or map to parent types |
| Quota assertion fails | More types than the panel can cover | Merge related types in Step 1 |
| Low recall for one type | Markers shared with a neighbour type | Add genes with low `pct_out_max` against that neighbour |
| Mouse panel with human symbols | PanglaoDB library is human-only | Map orthologs (e.g. Ensembl/BioMart) before merging |

## Related Skills

- `spatial-transcriptomics-cell-type-annotation` - reference search and download (Steps 3-4)
- `scanpy-scrna-seq` - reference preprocessing and marker ranking

## References

- Franzen et al. (2019) PanglaoDB, Database: https://doi.org/10.1093/database/baz046
- Hu et al. (2022) CellMarker 2.0, Nucleic Acids Research: https://doi.org/10.1093/nar/gkac947
- Enrichr libraries (PanglaoDB_Augmented_2021): https://maayanlab.cloud/Enrichr/
- CZ CELLxGENE Census documentation: https://chanzuckerberg.github.io/cellxgene-census/
