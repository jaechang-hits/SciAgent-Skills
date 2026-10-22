---
name: "spatial-transcriptomics-cell-cell-communication"
description: "Spatial cell-cell communication / ligand-receptor (LR) interaction analysis, one skill for every route: LIANA consensus ranking between annotated cell types, CellPhoneDB v5 permutation p-values, DEG method and spatial microenvironments, squidpy neighbourhood enrichment to keep spatially adjacent sender-receiver pairs, LIANA bivariate local LR scores on the tissue (works on Visium spots without labels), pathway-focused candidate evidence tables (immune checkpoints, chemokines, Notch, Wnt, TGF-beta) with contact vs secreted classes and PubMed co-mentions, and multi-sample Tensor-cell2cell and MISTy models. Xenium/MERFISH/CosMx cells, Visium spots, scRNA-seq. Route-specific steps follow the main workflow. Needs cell type labels first (spatial-transcriptomics-cell-type-annotation or a deconvolution skill)."
license: "CC-BY-4.0"
---

# Spatial Cell-Cell Communication

## Overview

Expression-based ligand-receptor (LR) inference ranks pairs that *could*
signal; spatial data adds whether sender and receiver actually sit next to
each other. This skill runs one inference (LIANA consensus by default, or
CellPhoneDB statistics), puts the result into one table, keeps interactions
whose cell types are spatial neighbours, scores LR co-expression at each
location, and narrows the table to the user's question with an evidence class
per candidate. Expression of both partners never proves signalling: every
result is a candidate.

| Question | Route |
|---|---|
| Which LR pairs between my cell types, and are the types neighbours | Workflow Steps 1-6 |
| Permutation p-values per pair, DEG-driven or microenvironment-restricted tests | Route: CellPhoneDB v5 Statistics, in place of Step 2 |
| Where on the tissue an LR pair is co-expressed (labels not needed) | Step 5; p-value/category layers in Route: LIANA Multi-sample |
| Communication differences across samples or conditions | Route: LIANA Multi-sample (by-sample ranking, Tensor-cell2cell) |
| What in the neighbourhood explains cell type composition | Route: LIANA Multi-sample (MISTy) |
| Literature support and which candidates to validate | After Step 6, Route: Literature Evidence |

All routes are in `## Task Routes` below the Workflow.

## When to Use

- Finding which annotated cell types may signal to each other in a spatial section
- Separating interactions between neighbouring cell types from those between distant ones
- Testing which LR pairs are specific to a sender-receiver pair with CellPhoneDB p-values
- Mapping where on the tissue a ligand and its receptor are co-expressed, also on Visium spots
- Asking about one pathway family (immune checkpoints, chemokines, Notch, Wnt, TGF-beta) after inference
- Comparing communication programs across samples or conditions
- For neighbourhood enrichment or co-occurrence alone, without LR pairs, use `spatial-transcriptomics-analysis-squidpy`

## Prerequisites

- **Input**: log-normalised expression in `X` (not z-scored) and `obsm["spatial"]`
- **Labels**: a cell type column in `obs` for Steps 2-4 and 6
  (`spatial-transcriptomics-cell-type-annotation`). Visium spots have no labels:
  Step 5 works without them; Steps 2-4 need a deconvolution first
  (`spatial-transcriptomics-deconvolution-cell2location`)
- **Genes**: gene symbols; CellPhoneDB is human-only (mouse via orthologs, see its reference)
- **Python packages**: `liana`, `squidpy`, `scanpy`; `cellphonedb`, `cell2cell` only for their routes

```bash
# Install only what `import` reports missing. `--pypi` keeps the env's scanpy/numba
# stack; a conda add can swap it and bare pip can shadow it.
pixi add --pypi liana squidpy scanpy
```

## Pre-flight Interview

```yaml
decisions:
  - id: D1
    param: CELL_TYPE_KEY
    kind: required
    source: data
    ask: "Which column holds the cell types whose communication you want to study?"
    default: null

  - id: D2
    param: RESOURCE
    kind: required
    source: data
    ask: "The gene symbols look <human/mouse>: use the <human/mouse> ligand-receptor database?"
    default: "consensus for human symbols, mouseconsensus for mouse symbols"

  - id: D3
    param: METHOD
    kind: required
    source: user
    ask: "Rank interactions by agreement across several methods (LIANA consensus, recommended), or do you need CellPhoneDB permutation p-values per pair (slower, human symbols)?"
    default: "LIANA consensus"

  - id: D4
    param: QUERY
    kind: optional
    source: user
    ask: "Is there a pathway (immune checkpoints, chemokines, growth factors, Notch, Wnt, TGF-beta) or a sender -> receiver direction you care about?"
    default: "all pathways and all cell type pairs"

  - id: D5
    param: SAMPLE_KEY
    kind: required
    source: data
    skip_if: "the data holds a single sample"
    ask: "Which column identifies the samples, and which one the condition to compare?"
    default: null

  - id: D6
    param: expr_prop
    kind: optional
    source: user
    ask: "Minimum fraction of a cell type that must express each partner gene?"
    default: "0.1"

  - id: D7
    param: NEIGHBOUR_Z
    kind: optional
    source: user
    ask: "How strongly must two cell types co-locate to count as neighbours?"
    default: "neighbourhood z > 2 over 15 nearest neighbours"

  - id: D8
    param: BANDWIDTH
    kind: optional_conditional
    source: data
    ask: "The coordinates are in <microns/pixels>; how wide should the local neighbourhood be?"
    default: "from li.pp.query_bandwidth: a few to tens of neighbours per location"

  - id: D9
    param: REGION_KEY
    kind: optional_conditional
    source: data
    depends_on: [D3]
    skip_if: "METHOD is LIANA consensus"
    ask: "Should CellPhoneDB only test cell types that share a tissue region? If so, which region/niche column?"
    default: "no restriction"

  - id: D10
    param: n_perms
    kind: optional
    source: user
    ask: "How many permutations for p-values?"
    default: "1000 for neighbourhood/CellPhoneDB tests, 100 for local LR scores"
```

Ask D1-D3 together, with D5 when `obs` has a sample-like column. Offer the
`obs` columns that look like cell type labels for D1; if none exist on
single-cell-resolution data, stop and annotate first. On Visium without a
deconvolution, say that only Step 5 can run.

## Workflow

1. Inputs, organism and panel coverage
2. Rank LR pairs between cell types
3. Harmonise results into one table
4. Keep spatially adjacent pairs
5. Local LR co-expression on the tissue
6. Focus on the question and classify candidates

### Step 1: Inputs and Panel Coverage

```python
import liana as li
import numpy as np
import pandas as pd
import scanpy as sc

adata = sc.read_h5ad("celltype_annotated.h5ad")
CELL_TYPE_KEY = "cell_type"                         # D1
adata.obs[CELL_TYPE_KEY] = adata.obs[CELL_TYPE_KEY].astype("category")
print(adata.obs[CELL_TYPE_KEY].value_counts())

head = adata.var_names[:200]                         # mouse "Actb" vs human "ACTB"
n_mouse = sum(len(g) > 1 and g[0].isupper() and g[1:].islower() for g in head)
RESOURCE = "mouseconsensus" if n_mouse > len(head) / 2 else "consensus"   # D2
print(f"resource: {RESOURCE}; max X = {adata.X.max():.1f} (expect < ~15 for log data)")

resource = li.rs.select_resource(RESOURCE)
genes = set(adata.var_names)
def present(complex_):
    return all(g in genes for g in complex_.split("_"))
covered = resource[resource["ligand"].map(present) & resource["receptor"].map(present)]
print(f"LR pairs measurable: {len(covered)} of {len(resource)}")
```

A targeted panel (Xenium ~400 genes) measures only a small share of the
resource. Report that coverage with the results: absent pairs were not
measured, not ruled out.

### Step 2: Rank LR Pairs Between Cell Types

LIANA consensus (`magnitude_rank`, `specificity_rank`; lower = stronger,
aggregated over CellPhoneDB, CellChat, NATMI, Connectome and others). For
CellPhoneDB statistics, run Route: CellPhoneDB v5 Statistics instead and continue
at Step 3 with `SOURCE = "cellphonedb"`.

```python
li.mt.rank_aggregate(adata, groupby=CELL_TYPE_KEY, resource_name=RESOURCE,
                     expr_prop=0.1, use_raw=False, key_added="liana_res", verbose=True)
res = adata.uns["liana_res"]
res.to_csv("liana_results.csv", index=False)
print(res.sort_values("magnitude_rank").head(15)[
    ["source", "target", "ligand_complex", "receptor_complex", "magnitude_rank", "specificity_rank"]])
```

```python
p = li.pl.dotplot(adata=adata, colour="magnitude_rank", size="specificity_rank",
                  inverse_colour=True, inverse_size=True, top_n=20,
                  orderby="magnitude_rank", orderby_ascending=True, figure_size=(10, 8),
                  return_fig=True)          # restrict with source_labels=[...], target_labels=[...]
p.save("liana_dotplot.png", dpi=150)
```

| Column | Meaning |
|---|---|
| `source` / `target` | Sender (ligand) / receiver (receptor) cell type |
| `ligand_complex` / `receptor_complex` | Genes; complexes joined by `_` |
| `lr_means` | Mean of ligand and receptor expression |
| `magnitude_rank` / `specificity_rank` | Consensus ranks of strength / cell type specificity |

### Step 3: Harmonise Results

One row per (sender, receiver, ligand, receptor) with a score and a p-value
or rank, from either tool, so Steps 4 and 6 run the same way:

```python
SOURCE = "liana"            # or "cellphonedb" (significant_long.csv from its reference)
TOP_RANK = 0.05             # LIANA magnitude_rank cutoff for "top" interactions

if SOURCE == "liana":
    r = res[res["magnitude_rank"] <= TOP_RANK]
    lr = pd.DataFrame({
        "sender": r["source"], "receiver": r["target"],
        "ligand": r["ligand_complex"], "receptor": r["receptor_complex"],
        "score": r["lr_means"], "p_or_rank": r["magnitude_rank"], "specificity": r["specificity_rank"]})
else:
    r = pd.read_csv("cellphonedb/significant_long.csv")
    r = r[r["pval"] < 0.05]
    for c in ("partner_a", "partner_b"):
        r[c] = r[c].str.replace(r"^(simple|complex):", "", regex=True)
    swap = r["receptor_a"].astype(bool) & ~r["receptor_b"].astype(bool)   # orient ligand -> receptor
    lr = pd.DataFrame({
        "sender": np.where(swap, r["cell_b"], r["cell_a"]), "receiver": np.where(swap, r["cell_a"], r["cell_b"]),
        "ligand": np.where(swap, r["partner_b"], r["partner_a"]),
        "receptor": np.where(swap, r["partner_a"], r["partner_b"]),
        "score": r["mean"], "p_or_rank": r["pval"], "specificity": r.get("score")})

lr["genes"] = (lr["ligand"] + "_" + lr["receptor"]).str.upper().str.split("_").map(set)
if SOURCE == "cellphonedb" and "genes" in r:      # subunit genes of complexes (saved as "{'ITGA4', ...}")
    import ast
    lr["genes"] = [g | (ast.literal_eval(x) if isinstance(x, str) and x.startswith("{") else set())
                   for g, x in zip(lr["genes"], r["genes"])]
lr = lr.reset_index(drop=True)
print(f"{len(lr)} rows, {lr[['ligand', 'receptor']].drop_duplicates().shape[0]} LR pairs")
```

For LIANA lower `p_or_rank` / `specificity` is better; for CellPhoneDB
`p_or_rank` is a p-value and `specificity` the 0-100 interaction score
(higher is better). CellPhoneDB complex names (e.g. `integrin_a4b1_complex`)
are not symbols; the code adds their subunit genes.

### Step 4: Keep Spatially Adjacent Pairs

```python
import squidpy as sq

sq.gr.spatial_neighbors(adata, coord_type="generic", n_neighs=15)   # Visium: coord_type="grid", n_rings=1
sq.gr.nhood_enrichment(adata, cluster_key=CELL_TYPE_KEY, n_perms=1000, seed=0)
cats = adata.obs[CELL_TYPE_KEY].cat.categories
z = pd.DataFrame(adata.uns[f"{CELL_TYPE_KEY}_nhood_enrichment"]["zscore"], index=cats, columns=cats)
z.to_csv("nhood_enrichment_z.csv")

NEIGHBOUR_Z = 2                                                     # D7
lr["neighbour_z"] = [z.loc[s, t] if s in z.index and t in z.columns else np.nan
                     for s, t in zip(lr["sender"], lr["receiver"])]
lr["autocrine"] = lr["sender"] == lr["receiver"]
adjacent = lr[(lr["neighbour_z"] > NEIGHBOUR_Z) | lr["autocrine"]].sort_values("p_or_rank")
adjacent.drop(columns=["genes"]).to_csv("lr_adjacent_pairs.csv", index=False)
print(f"{len(adjacent)} of {len(lr)} top interactions are between neighbouring (or the same) cell types")
```

Autocrine pairs are always adjacent; read them separately. On Visium spots
the label-based test is coarse; prefer Step 5 there. Show the co-location
matrix the filter is based on:

```python
sq.pl.nhood_enrichment(adata, cluster_key=CELL_TYPE_KEY, cmap="coolwarm", vmin=-10, vmax=10,
                       figsize=(7, 6), save="nhood_enrichment.png")
```

### Step 5: Local LR Co-expression on the Tissue

Scores each LR pair at every location, so it also works on Visium spots
without labels. Pick the bandwidth from the coordinate scale first:

```python
spatial_neighbors = li.pp.spatial_neighbors if hasattr(li, "pp") else li.ut.spatial_neighbors  # li.ut in older liana
plot, bw_table = li.pp.query_bandwidth(coordinates=adata.obsm["spatial"], start=0, end=500, interval_n=20)
plot.save("liana_bandwidth.png", dpi=150)
print(bw_table.head(10))      # average neighbours per bandwidth: aim for a few to tens

BANDWIDTH = 100               # D8; coordinate units: ~50-100 um Xenium; Visium full-res px ~2-3 spot spacings
spatial_neighbors(adata, bandwidth=BANDWIDTH, cutoff=0.1, kernel="gaussian", set_diag=True)
lrdata = li.mt.bivariate(adata, resource_name=RESOURCE, local_name="cosine", global_name="morans",
                         n_perms=100, mask_negatives=False, add_categories=True, nz_prop=0.1,
                         use_raw=False, verbose=True)
summary = lrdata.var.sort_values("morans", ascending=False)
summary.to_csv("liana_bivariate_summary.csv")
lrdata.write_h5ad("liana_bivariate.h5ad")
print(summary.head(10))
sc.pl.embedding(lrdata, basis="spatial", color=summary.index[:4].tolist(), cmap="coolwarm", save="_lr_local.png")
```

`var["morans"]` is the global spatial co-pattern of ligand and receptor; the
per-location p-values (`layers["pvals"]`) and categories (`layers["cats"]`:
both high / one high / both low) are read in Route: LIANA Multi-sample.

### Step 6: Focus and Classify Candidates

Narrow the table to the user's question (D4) and give each candidate an
evidence class. Matching is per gene symbol, so `CD4` does not hit `CD40`.

```python
PATHWAYS = {
    "immune_checkpoint": ["PDCD1", "CD274", "PDCD1LG2", "CTLA4", "CD28", "CD80", "CD86",
                          "LAG3", "HAVCR2", "LGALS9", "TIGIT", "PVR", "NECTIN2"],
    "chemokine": ["CXCL*", "CCL*", "CX3CL1", "XCL*", "CXCR*", "CCR*", "CX3CR1", "XCR1", "ACKR*"],
    "growth_factor": ["EGF", "EGFR", "ERBB*", "VEGF*", "KDR", "FLT1", "FLT4", "FGF*", "FGFR*",
                      "PDGF*", "HGF", "MET", "IGF1", "IGF1R"],
    "notch": ["NOTCH*", "JAG1", "JAG2", "DLL1", "DLL3", "DLL4"],
    "wnt": ["WNT*", "FZD*", "LRP5", "LRP6", "RSPO*", "LGR*"],
    "tgfb_bmp": ["TGFB*", "TGFBR*", "BMP*", "BMPR*", "ACVR*", "GDF*"],
}
def matches(genes, patterns):
    return any(g.startswith(p[:-1]) if p.endswith("*") else g == p for g in genes for p in patterns)
for name, pats in PATHWAYS.items():
    lr[name] = lr["genes"].map(lambda g: matches(g, pats))
lr["pathway"] = lr[list(PATHWAYS)].apply(lambda row: ",".join(k for k, v in row.items() if v), axis=1)

QUERY = list(PATHWAYS)                               # D4, e.g. ["immune_checkpoint", "chemokine"]
SENDERS, RECEIVERS = None, None                      # e.g. {"Tumor cell"}, {"T cell"}
q = lr[lr[QUERY].any(axis=1)]
if SENDERS: q = q[q["sender"].isin(SENDERS)]
if RECEIVERS: q = q[q["receiver"].isin(RECEIVERS)]

CONTACT = {"CD274", "PDCD1", "PDCD1LG2", "CTLA4", "CD28", "CD80", "CD86", "JAG1", "JAG2",
           "DLL1", "DLL3", "DLL4", "NOTCH1", "NOTCH2", "NOTCH3", "NOTCH4", "TIGIT", "PVR", "NECTIN2"}
def evidence_class(row):
    if pd.isna(row["neighbour_z"]):
        return "no spatial test"
    if row["neighbour_z"] > NEIGHBOUR_Z or row["autocrine"]:
        return "co-located"
    return "unlikely (contact, not co-located)" if row["ligand"].split("_")[0] in CONTACT else "possible paracrine"
q = q.assign(evidence_class=q.apply(evidence_class, axis=1))
ev = q.drop(columns=["genes"]).sort_values(["p_or_rank", "score"], ascending=[True, False])
ev.to_csv("lr_candidate_evidence.csv", index=False)
print(ev.groupby(["pathway", "evidence_class"]).size())
```

`CONTACT` is a starting list of membrane-bound partners; extend it for the
pathways in `QUERY`. Plot the top candidates:

```python
import matplotlib.pyplot as plt

top = ev.head(30).copy()
top["lr"] = top["ligand"] + " -> " + top["receptor"]
top["pair"] = top["sender"].astype(str) + " -> " + top["receiver"].astype(str)
fig, ax = plt.subplots(figsize=(max(8, 0.4 * top["pair"].nunique()), max(6, 0.3 * top["lr"].nunique())))
s = ax.scatter(top["pair"], top["lr"], c=top["neighbour_z"], cmap="coolwarm", vmin=-5, vmax=5,
               s=30 + 200 * top["score"] / top["score"].max())
plt.colorbar(s, label="neighbourhood z (sender-receiver)"); plt.xticks(rotation=90)
plt.tight_layout(); plt.savefig("lr_candidates.png", dpi=150); plt.close()
```

| Evidence pattern | Interpretation |
|---|---|
| Top-ranked / significant, co-located | Strong candidate; check literature (Route: Literature Evidence) |
| Top-ranked, not co-located, secreted ligand | Possible paracrine signal; weaker |
| Top-ranked, not co-located, contact-dependent | Unlikely in this tissue |
| Only one partner above `expr_prop` | Not supported |

State validation routes (spatial protein staining, receptor blocking,
perturbation) for the top candidates.

## Task Routes

Each route continues the Workflow session (same variable names). Only the calls
that differ from the Workflow, or that fail silently when written another way,
are shown.

### Route: CellPhoneDB v5 Statistics

Scores each curated LR pair, including multi-subunit complexes, for every
ordered pair of cell types; the statistical method tests specificity by
shuffling labels. Run it in place of Step 2, write `cellphonedb/significant_long.csv`,
then continue at Step 3 with `SOURCE = "cellphonedb"`. Install
`pixi add --pypi cellphonedb`.

| Method | Call | Use when |
|---|---|---|
| Simple | `cpdb_analysis_method` | Quick look, no statistics |
| Statistical | `cpdb_statistical_analysis_method` | Discovery; permutation p-values |
| DEG-based | `cpdb_degs_analysis_method` | Interactions driven by genes up in one cell type; result has `relevant_interactions` instead of `pvalues` |

Inputs and gotchas:

- Database: without GitHub access, download `cellphonedb.zip` from the
  `ventolab/cellphonedb-data` releases by hand into `CPDB_DIR`.
- `counts.h5ad` holds normalised (log) expression, not z-scored, with human HGNC
  symbols. Cell type names must not contain `|`, the result separator.
- Mouse: map symbols 1:1 to human first:
  `li.rs.get_hcop_orthologs(target_organism="mouse", columns=["human_symbol", "mouse_symbol"], min_evidence=3)`,
  keep rows unique on both columns, rename `var_names`.
- Microenvironments (D9): a `cell_type` / `microenvironment` table built from a
  region column, a type counting as present above ~2% of the region's cells;
  only pairs of co-located types are tested.
- DEG method: `degs.tsv` with `cluster` / `gene` columns of up-regulated genes
  (e.g. `rank_genes_groups`, adj p < 0.05, logFC > 0.25).

```python
import os
from cellphonedb.src.core.methods import cpdb_statistical_analysis_method
from cellphonedb.utils import db_utils

CPDB_DIR = os.path.abspath("ref_cache/cellphonedb/v5.0.0")
CPDB_ZIP = os.path.join(CPDB_DIR, "cellphonedb.zip")
if not os.path.exists(CPDB_ZIP):
    os.makedirs(CPDB_DIR, exist_ok=True)
    db_utils.download_database(CPDB_DIR, "v5.0.0")
OUT = "cellphonedb"
os.makedirs(OUT, exist_ok=True)
sc.AnnData(X=adata.X, obs=pd.DataFrame(index=adata.obs_names),
           var=pd.DataFrame(index=adata.var_names)).write_h5ad(f"{OUT}/counts.h5ad")
pd.DataFrame({"barcode_sample": adata.obs_names, "cell_type": adata.obs[CELL_TYPE_KEY].astype(str).values}
             ).to_csv(f"{OUT}/meta.tsv", sep="\t", index=False)

res = cpdb_statistical_analysis_method.call(
    cpdb_file_path=CPDB_ZIP, meta_file_path=f"{OUT}/meta.tsv", counts_file_path=f"{OUT}/counts.h5ad",
    counts_data="hgnc_symbol", microenvs_file_path=None,      # or f"{OUT}/microenvs.tsv"
    score_interactions=True, iterations=1000, threshold=0.1, threads=4, debug_seed=42, pvalue=0.05,
    subsampling=False,             # >~100k cells: True + subsampling_num_cells, subsampling_log=False
    output_path=OUT, output_suffix="stat")
```

Long table read by Step 3 (`cell_a` expresses `partner_a`; Step 3 orients
ligand -> receptor from `receptor_a` / `receptor_b`):

```python
sig = res["significant_means"]
labels = set(adata.obs[CELL_TYPE_KEY].astype(str))
pair_cols = [c for c in sig.columns if c.count("|") == 1 and set(c.split("|")) <= labels]
meta_cols = [c for c in ["id_cp_interaction", "interacting_pair", "partner_a", "partner_b", "secreted",
                         "receptor_a", "receptor_b"] if c in sig.columns]
long = sig.melt(id_vars=meta_cols, value_vars=pair_cols, var_name="pair", value_name="mean").dropna(subset=["mean"])
pv = res["pvalues"].melt(id_vars=["id_cp_interaction"], value_vars=pair_cols, var_name="pair", value_name="pval")
long = long.merge(pv, on=["id_cp_interaction", "pair"], how="left")
long[["cell_a", "cell_b"]] = long["pair"].str.split("|", expand=True)
if "interaction_scores" in res:
    sc_long = res["interaction_scores"].melt(id_vars=["id_cp_interaction"], value_vars=pair_cols,
                                             var_name="pair", value_name="score")
    long = long.merge(sc_long, on=["id_cp_interaction", "pair"], how="left")
long["genes"] = long["id_cp_interaction"].map(
    res["deconvoluted"].groupby("id_cp_interaction")["gene_name"].apply(lambda s: set(s.dropna())))
long.to_csv(f"{OUT}/significant_long.csv", index=False)
```

| Signal | Meaning |
|---|---|
| Low p-value, high mean | Expressed and specific to this cell type pair - strongest candidates |
| High mean, p >= 0.05 | Broadly expressed; not specific to this pair |
| High `interaction_scores` (0-100) | Partners specific to these two types relative to all types |
| `secreted == True` | Ligand can act at a distance; membrane-bound pairs need contact |

Two conditions: run the statistical method per condition with the same database
and parameters and compare the significant sets; this is descriptive, since cell
numbers per type differ between conditions and change each test's power.
`ktplotspy` (`plot_cpdb_heatmap`, `plot_cpdb`) draws publication-style figures
from `res`.

### Route: LIANA Multi-sample, Local Score Layers, MISTy

Uses `adata`, `CELL_TYPE_KEY`, `RESOURCE`, `BANDWIDTH` and `lrdata` from the
Workflow. Functions follow the current `li.pp` / `li.ms` namespaces (older
releases: `li.ut` / `li.multi`).

- **Per sample and condition (D5)**: `li.mt.rank_aggregate.by_sample(adata, groupby=CELL_TYPE_KEY,
  sample_key=SAMPLE_KEY, resource_name=RESOURCE, expr_prop=0.1, use_raw=False, n_perms=None,
  return_all_lrs=True)`, then pivot `magnitude_rank` by condition (median per
  interaction). With few samples per condition this is descriptive; no p-values.
- **Tensor-cell2cell** (`pixi add --pypi cell2cell`, several samples per
  condition): factorises samples x LR x sender x receiver into patterns. Test a
  factor's context loadings between conditions across samples (Mann-Whitney)
  before calling it condition-specific; with few samples, exploratory.
- **Local score layers** of `lrdata` (Step 5): `X` local score per location
  (`ligand^receptor`), `layers["pvals"]` per-location permutation p-value,
  `layers["cats"]` 1 = both high, -1 = one high one low, 0 = both low;
  `var["morans"]` / `var["morans_pvals"]` global co-pattern. Plot `layer="cats"`
  to separate true co-localisation (1) from one-partner regions (-1).
- **MISTy**: for each target (e.g. cell2location proportions) how well it is
  predicted by the same spot (intra), direct neighbours (juxta) and the wider
  area (para). `gain_R2` = what the spatial views add over intra; `interactions`
  with `view` juxta/para name the predicting neighbours. Pass
  `extra=lrdata[:, top_lr]` to ask whether local LR activity predicts
  composition beyond composition itself.
- **One method instead of the consensus**: `li.mt.cellphonedb(adata, groupby=CELL_TYPE_KEY,
  resource_name=RESOURCE, expr_prop=0.1, use_raw=False, n_perms=1000, seed=0,
  key_added="cpdb_res")` gives `cellphone_pvals` without installing `cellphonedb`.

```python
import cell2cell as c2c
from collections import defaultdict

SAMPLE_KEY, CONDITION_KEY = "sample", "condition"          # D5
li.mt.rank_aggregate.by_sample(adata, groupby=CELL_TYPE_KEY, sample_key=SAMPLE_KEY, resource_name=RESOURCE,
                               expr_prop=0.1, use_raw=False, n_perms=None, return_all_lrs=True)
tensor = li.ms.to_tensor_c2c(adata, sample_key=SAMPLE_KEY, score_key="magnitude_rank", how="outer_cells")
ctx = adata.obs[[SAMPLE_KEY, CONDITION_KEY]].drop_duplicates()
context_dict = defaultdict(lambda: "Unknown", zip(ctx[SAMPLE_KEY], ctx[CONDITION_KEY]))
meta = c2c.tensor.generate_tensor_metadata(interaction_tensor=tensor, metadata_dicts=[context_dict, None, None, None],
                                           fill_with_order_elements=True)
tensor = c2c.analysis.run_tensor_cell2cell_pipeline(
    tensor, meta, copy_tensor=True, rank=None, tf_optimization="regular", random_state=0, device="cpu",
    elbow_metric="error", upper_rank=15, tf_init="random", sample_col="Element", group_col="Category",
    output_fig=False)                         # rank=None: elbow search (slow); or fix e.g. 6
contexts = tensor.factors["Contexts"]         # also "Ligand-Receptor Pairs", "Sender Cells", "Receiver Cells"
```

```python
from liana.method import genericMistyData
from liana.method.sp import LinearModel

adata.obsm["compositions"] = pd.read_csv("cell2location_proportions.csv", index_col=0).loc[adata.obs_names]
comps = li.pp.obsm_to_adata(adata, "compositions")
misty = genericMistyData(intra=comps, cutoff=0.05, bandwidth=BANDWIDTH, n_neighs=6)
misty(model=LinearModel, k_cv=10, seed=1337, bypass_intra=False, verbose=True)   # or RandomForestModel
misty.uns["target_metrics"].to_csv("misty_target_metrics.csv", index=False)       # intra_R2, multi_R2, gain_R2
misty.uns["interactions"].to_csv("misty_interactions.csv", index=False)           # target, predictor, view, importances
```

### Route: Literature Evidence for Candidates

Adds PubMed support to the Step 6 candidate table (`ev`). NCBI E-utilities need
no key below 3 requests per second; cap the number of pairs queried. The judgment
is made from the evidence table, not by the code.

```python
import time
import requests

EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
CONTEXT = ""        # optional, e.g. "lung cancer" to count context-specific co-mentions

def pubmed_count(ligand, receptor):
    a, b = ligand.split("_")[0], receptor.split("_")[0]   # first subunit for complexes
    term = f"{a}[tiab] AND {b}[tiab]" + (f" AND ({CONTEXT})" if CONTEXT else "")
    r = requests.get(EUTILS, params={"db": "pubmed", "term": term, "retmode": "json", "retmax": 0}, timeout=30)
    r.raise_for_status(); time.sleep(0.4)
    return int(r.json()["esearchresult"]["count"])

pairs = ev[["ligand", "receptor"]].drop_duplicates().head(50)
pairs["pubmed_n"] = [pubmed_count(l, r) for l, r in zip(pairs["ligand"], pairs["receptor"])]
ev = ev.merge(pairs, on=["ligand", "receptor"], how="left")
ev["final_class"] = [("strong, known" if (n or 0) > 0 else "novel, co-located") if c == "co-located" else c
                     for c, n in zip(ev["evidence_class"], ev["pubmed_n"])]
ev.to_csv("lr_candidate_evidence.csv", index=False)
```

A zero count with strong statistics is a novelty candidate, not an error. To read
the papers, fetch abstracts with `efetch.fcgi?db=pubmed&id=<ids>&rettype=abstract&retmode=text`
for the ids of an `esearch` with `retmax=5&sort=relevance`.

## Key Parameters

| Parameter | Default | Effect |
|---|---|---|
| `expr_prop` | 0.1 | Min fraction of a cell type expressing each gene |
| `TOP_RANK` | 0.05 | LIANA `magnitude_rank` cutoff for top interactions |
| `NEIGHBOUR_Z` | 2 | How strongly two types must co-locate |
| `n_neighs` | 15 | Size of the spatial neighbourhood (cells) |
| `BANDWIDTH` | 100 | Spatial kernel for local scores, in coordinate units |
| `nz_prop` | 0.1 | Min fraction of locations expressing each partner (local scores) |
| `QUERY` / `SENDERS` / `RECEIVERS` | all | Restricts the candidate table to the question |
| `threshold` (CellPhoneDB) | 0.1 | Min fraction of a cell type expressing each partner gene |
| `iterations` (CellPhoneDB) | 1000 | Label permutations; fewer = coarser p-values |
| `pvalue` | 0.05 | Significance cutoff for `significant_means` |
| `MIN_FRAC` (microenvs) | 0.02 | Presence cutoff for a type in a region |
| DEG cutoffs (CellPhoneDB DEG method) | adj p < 0.05, logFC > 0.25 | Which genes count as up-regulated |
| `subsampling_num_cells` | 1/3 of cells | Geometric sketching size for large datasets |
| `rank` (Tensor-cell2cell) | None (elbow) | Number of communication patterns; fix 3-6 when the elbow search is slow |
| `how` (Tensor-cell2cell) | `"outer_cells"` | Keep cell types missing in some samples |
| `bandwidth` (MISTy) | `BANDWIDTH` | Para view kernel width, in coordinate units |
| `k_cv` (MISTy) | 10 | Cross-validation folds per target |
| `CONTEXT` | empty | Restricts literature counts to a disease/tissue |
| Pairs queried | 50 | Number of PubMed requests |
| Request delay | 0.4 s | Stays under the 3 requests/second limit |

## Common Recipes

### Recipe: Sender-Receiver Count Map

```python
import seaborn as sns

topn = res[(res["magnitude_rank"] <= 0.05) & (res["specificity_rank"] <= 0.05)]
counts = topn.groupby(["source", "target"]).size().unstack(fill_value=0)
fig, ax = plt.subplots(figsize=(9, 8))
sns.heatmap(counts, cmap="YlOrRd", annot=True, fmt="d", ax=ax)
ax.set_xlabel("receiver"); ax.set_ylabel("sender")
plt.tight_layout(); plt.savefig("liana_sender_receiver_counts.png", dpi=150); plt.close()
```

### Recipe: Distance Range of One Cell Type Pair

Neighbourhood enrichment is a yes/no at one scale; co-occurrence shows over
which distance two types stay together:

```python
ANCHOR = "Macrophage"                                  # a category of CELL_TYPE_KEY
sub = adata[np.random.default_rng(0).choice(adata.n_obs, min(adata.n_obs, 20000), replace=False)].copy()
occ, interval = sq.gr.co_occurrence(sub, cluster_key=CELL_TYPE_KEY, interval=50, copy=True)
sub_cats = list(sub.obs[CELL_TYPE_KEY].cat.categories)
dist = interval[1:] if len(interval) == occ.shape[2] + 1 else interval
curve = pd.DataFrame(occ[sub_cats.index(ANCHOR)].T, index=np.round(dist, 1), columns=sub_cats)
print(curve.iloc[:10].round(2))          # ratio > 1 at short distance = attraction
```

### Recipe: Visium - Link Local LR Scores to Deconvolved Cell Types

```python
abund = pd.read_csv("cell2location_abundance.csv", index_col=0).loc[lrdata.obs_names]
lr_top = summary.index[:20]
local = pd.DataFrame(np.asarray(lrdata[:, lr_top].X.todense()) if hasattr(lrdata.X, "todense")
                     else lrdata[:, lr_top].X, index=lrdata.obs_names, columns=lr_top)
corr = pd.DataFrame({ct: local.corrwith(abund[ct]) for ct in abund.columns}).round(2)
corr.to_csv("lr_local_vs_abundance.csv")
print(corr.apply(lambda r: ", ".join(f"{k} {v}" for k, v in r.nlargest(3).items()), axis=1))
```

### Recipe: Are Ligand and Receptor Actually Expressed?

Aggregated scores can hide that only a few cells express a partner:

```python
def frac_expr(cell_type, gene):
    if gene not in adata.var_names:
        return np.nan
    x = adata[adata.obs[CELL_TYPE_KEY] == cell_type, gene].X
    x = x.toarray() if hasattr(x, "toarray") else np.asarray(x)
    return float((x > 0).mean())

ev_top = ev.head(30).copy()
ev_top["ligand_frac_sender"] = [frac_expr(s, l.split("_")[0]) for s, l in zip(ev_top["sender"], ev_top["ligand"])]
ev_top["receptor_frac_receiver"] = [frac_expr(r, rc.split("_")[0]) for r, rc in zip(ev_top["receiver"], ev_top["receptor"])]
print(ev_top[["sender", "receiver", "ligand", "receptor", "ligand_frac_sender", "receptor_frac_receiver"]].round(2))
```

## Expected Outputs

- `liana_results.csv`, `liana_dotplot.png` - LR ranking per sender-receiver pair
- `nhood_enrichment_z.csv`, `nhood_enrichment.png` - cell type co-location z-scores
- `lr_adjacent_pairs.csv` - top interactions whose cell types are neighbours
- `liana_bandwidth.png`, `liana_bivariate_summary.csv`, `liana_bivariate.h5ad` - local LR scores
- `lr_candidate_evidence.csv`, `lr_candidates.png` - candidates with pathway and evidence class
- CellPhoneDB: `ref_cache/cellphonedb/v5.0.0/cellphonedb.zip` (cached database), `cellphonedb/meta.tsv` and `counts.h5ad` (inputs), `cellphonedb/statistical_analysis_*_stat.txt` (means, pvalues, significant_means, deconvoluted, interaction_scores), `cellphonedb/significant_long.csv` (read by Step 3)
- LIANA multi-sample / MISTy: `tensor.factors` (context, LR, sender, receiver loadings), `misty_target_metrics.csv`, `misty_interactions.csv`
- Literature: `pubmed_n` and `final_class` columns added to `lr_candidate_evidence.csv`

## Troubleshooting

| Problem | Cause | Fix |
|---|---|---|
| Very few results | Targeted panel lacks LR genes | Report coverage (Step 1); do not extrapolate |
| `KeyError` on cell type | Column not categorical, or label spelling differs between results and `adata` | `astype("category")`; use the same label column for inference and Step 4 |
| All local scores near 0 | Bandwidth smaller than spot/cell spacing | Re-read the `query_bandwidth` table; raise `BANDWIDTH` |
| Mouse genes not matched | Human resource | `RESOURCE = "mouseconsensus"` |
| Results dominated by housekeeping-like pairs | Data was z-scored or not normalised | Use normalised (log) expression |
| Slow permutations | Many cells | Lower `n_perms` for exploration, report it |
| `AttributeError: module 'liana' has no attribute 'pp'` / `ms` | Older liana | Step 5 falls back to `li.ut`; elsewhere use `li.ut.*` / `li.multi.*`, or upgrade liana |
| Pathway query returns nothing | Pathway genes not on the panel, or mouse symbols | Check `adata.var_names`; `genes` are upper-cased for matching |
| Almost no interactions | Mouse or Ensembl IDs in `var_names` | Map to human HGNC symbols (ortholog step of the CellPhoneDB route) |
| `Some clusters/cell_types in microenvironments file are not present in metadata` | Label mismatch between files | Build both files from the same cell type column |
| Very slow / out of memory | Many cells | `subsampling=True` with `subsampling_num_cells`; raise `threads` |
| `download_database` fails | No network access to GitHub | Download `cellphonedb.zip` from the release page manually into `CPDB_DIR` |
| Pair columns missing a cell type | Type below `threshold` for all genes or absent from microenvs | Check `value_counts`; lower `MIN_FRAC` |
| Tensor factorization fails | Too few samples or cell types missing in many samples | `how="outer_cells"`, fix `rank` low (3-4), add samples |
| MISTy juxta view error | squidpy missing | `pixi add --pypi squidpy` |
| `KeyError` aligning compositions | Spot IDs differ between files | Align on `adata.obs_names` before `obsm` |
| PubMed HTTP 429 | Too many requests | Increase `time.sleep`; lower the number of pairs |
| Literature counts inflated | Gene symbol is a common word (e.g. `MET`, `KIT`) | Add `CONTEXT` or check abstracts |
| Complex pairs never match | CellPhoneDB complex names instead of genes | Use the subunit `genes` from Step 3 |

## Bundled Resources

Merged from four former skills: `spatial-transcriptomics-cell-cell-communication`
(Steps 1-2, 4-5, recipes), `cellphonedb-cell-cell-interaction` (Route: CellPhoneDB
v5 Statistics; its adjacency recipe is Step 4), `liana-spatial-cell-cell-communication`
(Steps 1-2 and 5, Route: LIANA Multi-sample) and
`spatial-single-cell-ligand-receptor-discovery` (Steps 3, 4, 6, expression-fraction
recipe, Route: Literature Evidence).

## Related Skills

- `spatial-transcriptomics-cell-type-annotation` - labels for Steps 2-4
- `spatial-transcriptomics-deconvolution-cell2location` - abundances for Visium
- `spatial-mapping-tangram` - per-spot proportions or per-nucleus labels from a reference
- `spatial-domain-detection` - region labels for CellPhoneDB microenvironments
- `spatial-transcriptomics-analysis-squidpy` - further spatial statistics and squidpy `ligrec`

## References

- Dimitrov et al. (2024) LIANA+, Nature Cell Biology: https://doi.org/10.1038/s41556-024-01469-w
- LIANA+ documentation: https://liana.readthedocs.io/
- Troule et al. (2025) CellPhoneDB v5, Nature Protocols: https://doi.org/10.1038/s41596-024-01137-1
- Palla et al. (2022) Squidpy, Nature Methods: https://doi.org/10.1038/s41592-021-01358-2
- squidpy documentation: https://squidpy.readthedocs.io/en/stable/
