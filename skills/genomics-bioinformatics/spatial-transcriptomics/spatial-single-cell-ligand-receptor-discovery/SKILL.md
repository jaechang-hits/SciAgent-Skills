---
name: "spatial-single-cell-ligand-receptor-discovery"
description: "Ligand-receptor candidate discovery and evidence building for scRNA-seq and spatial transcriptomics: put CellPhoneDB or LIANA results into one long table, query pathway families (immune checkpoints, chemokines, growth factors, Notch, Wnt, TGF-beta) by exact genes or symbol prefixes, flag secreted vs contact-dependent pairs, test sender-receiver co-location with squidpy, and count PubMed co-mentions per pair to build a ranked evidence table. Use after an LR inference run when the question is about specific pathways or which interactions to follow up. To run the inference itself use cellphonedb-cell-cell-interaction or liana-spatial-cell-cell-communication; for the standard spatial LR workflow use spatial-transcriptomics-cell-cell-communication."
license: "CC-BY-4.0"
---

# Ligand-Receptor Candidate Discovery

## Overview

Inference tools return thousands of LR x cell type pair rows. This skill
narrows them to a biological question and attaches evidence (statistics,
spatial co-location, literature) so the reader can decide which interactions
to report or validate. The judgment is made from the evidence table, not by
the code. Output: a ranked evidence table per candidate interaction and a dot
plot of the top candidates.

## When to Use

- Asking about a specific pathway (immune checkpoints, chemokines, Notch, Wnt, TGF-beta) after an LR inference run
- Deciding which predicted interactions to report or validate experimentally
- Separating contact-dependent pairs that need neighbouring cells from secreted ones
- Checking whether a candidate pair is already described in the literature
- Combining CellPhoneDB or LIANA output with spatial co-location into one table
- Use `cellphonedb-cell-cell-interaction` or `spatial-transcriptomics-cell-cell-communication` instead when no LR inference has been run yet
- For multi-sample tensor decomposition, use `liana-spatial-cell-cell-communication`

## Prerequisites

- **Data**: annotated AnnData (`obs` cell type column; `obsm["spatial"]` for Step 4)
- **Results** from one of:
  - `cellphonedb-cell-cell-interaction` (`res` dict or `significant_long.csv`)
  - LIANA `rank_aggregate` (`liana_results.csv`; Step 2 of
    `spatial-transcriptomics-cell-cell-communication`)
- **Genes**: human symbols (map mouse first; see `cellphonedb-cell-cell-interaction` Step 2)
- **Network**: NCBI E-utilities for Step 5 (no key needed below 3 requests/second)
- **Python packages**: `squidpy`, `requests`, `scanpy`

```bash
pip install squidpy requests scanpy
```

## Workflow

1. Check inputs
2. Harmonise results into one long table
3. Query pathways of interest
4. Spatial co-location of sender and receiver
5. Literature co-mentions
6. Evidence table and plot

### Step 1: Check Inputs

```python
import numpy as np
import pandas as pd
import scanpy as sc

adata = sc.read_h5ad("celltype_annotated.h5ad")
CELL_TYPE_KEY = "cell_type"
adata.obs[CELL_TYPE_KEY] = adata.obs[CELL_TYPE_KEY].astype("category")
print(adata.obs[CELL_TYPE_KEY].value_counts())
print("sample genes:", adata.var_names[:10].tolist())   # expect ACTB-style human symbols
```

Labels must be biologically meaningful (not raw cluster numbers); otherwise
annotate first with `spatial-transcriptomics-cell-type-annotation`.

### Step 2: Harmonise Results

One row per (sender, receiver, ligand, receptor) with a score and a p-value
or rank, from either tool:

```python
SOURCE = "liana"            # or "cellphonedb"

if SOURCE == "liana":
    r = pd.read_csv("liana_results.csv")
    lr = pd.DataFrame({
        "sender": r["source"], "receiver": r["target"],
        "ligand": r["ligand_complex"], "receptor": r["receptor_complex"],
        "score": r["lr_means"], "p_or_rank": r["magnitude_rank"], "specificity": r["specificity_rank"]})
else:
    r = pd.read_csv("cellphonedb/significant_long.csv")
    r["partner_a"] = r["partner_a"].str.replace(r"^(simple|complex):", "", regex=True)
    r["partner_b"] = r["partner_b"].str.replace(r"^(simple|complex):", "", regex=True)
    # Orient ligand -> receptor: if partner A is the receptor, swap sides.
    swap = r["receptor_a"].astype(bool) & ~r["receptor_b"].astype(bool)
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
print(f"{len(lr)} rows, {lr[['ligand', 'receptor']].drop_duplicates().shape[0]} LR pairs")
```

For LIANA, lower `p_or_rank` / `specificity` is better; for CellPhoneDB
`p_or_rank` is a p-value and `specificity` the 0-100 interaction score (higher
is better). CellPhoneDB complex names (e.g. `integrin_a4b1_complex`) are not
gene symbols; the code adds their subunit genes from the `genes` column of
`significant_long.csv`.

### Step 3: Query Pathways of Interest

Exact symbols or prefixes (a prefix ending in `*` matches a family):

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
QUERY = ["immune_checkpoint", "chemokine"]          # the user's question
SENDERS, RECEIVERS = None, None                     # e.g. {"Tumor cell"}, {"T cell"}
q = lr[lr[QUERY].any(axis=1)]
if SENDERS: q = q[q["sender"].isin(SENDERS)]
if RECEIVERS: q = q[q["receiver"].isin(RECEIVERS)]
print(q.groupby("pathway").size())
```

Matching is per gene symbol, so `CD4` does not hit `CD40` as a substring
search on the pair name would.

### Step 4: Spatial Co-location

Contact-dependent pairs (membrane ligands, e.g. `CD274`-`PDCD1`, `JAG1`-`NOTCH1`)
require neighbouring cells; secreted ligands (chemokines, growth factors)
can act over tens of microns. Score each sender-receiver pair:

```python
import squidpy as sq

if "spatial" in adata.obsm:
    sq.gr.spatial_neighbors(adata, coord_type="generic", n_neighs=10)   # Visium: coord_type="grid", n_rings=1
    sq.gr.nhood_enrichment(adata, cluster_key=CELL_TYPE_KEY, n_perms=1000, seed=0)
    cats = adata.obs[CELL_TYPE_KEY].cat.categories
    z = pd.DataFrame(adata.uns[f"{CELL_TYPE_KEY}_nhood_enrichment"]["zscore"], index=cats, columns=cats)
    q = q.assign(neighbour_z=[z.loc[s, t] if s in z.index and t in z.columns else np.nan
                              for s, t in zip(q["sender"], q["receiver"])])
else:
    q = q.assign(neighbour_z=np.nan)
print(q[["sender", "receiver", "neighbour_z"]].drop_duplicates().sort_values("neighbour_z", ascending=False).head(15))
```

Visium spots are mixtures; there, use local co-expression instead
(`spatial-transcriptomics-cell-cell-communication` Step 4).

### Step 5: Literature Co-mentions

Count PubMed records mentioning both partners (NCBI E-utilities, no key
needed for < 3 requests/second):

```python
import time
import requests

EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
CONTEXT = ""        # optional, e.g. "lung cancer" to count context-specific co-mentions

def pubmed_count(ligand, receptor):
    a, b = ligand.split("_")[0], receptor.split("_")[0]   # first subunit for complexes
    term = f"{a}[tiab] AND {b}[tiab]" + (f" AND ({CONTEXT})" if CONTEXT else "")
    r = requests.get(EUTILS, params={"db": "pubmed", "term": term, "retmode": "json", "retmax": 0}, timeout=30)
    r.raise_for_status()
    time.sleep(0.4)
    return int(r.json()["esearchresult"]["count"])

pairs = q[["ligand", "receptor"]].drop_duplicates().head(50)      # cap the number of requests
pairs["pubmed_n"] = [pubmed_count(l, r) for l, r in zip(pairs["ligand"], pairs["receptor"])]
q = q.merge(pairs, on=["ligand", "receptor"], how="left")
print(pairs.sort_values("pubmed_n", ascending=False).head(15))
```

A high count supports that the pair is a known interaction; a zero count with
strong statistics is a novelty candidate, not an error. To read the papers,
fetch titles/abstracts with `efetch.fcgi?db=pubmed&id=...&rettype=abstract`.

### Step 6: Evidence Table and Plot

```python
import matplotlib.pyplot as plt

ev = q.drop(columns=["genes"]).sort_values(["p_or_rank", "score"], ascending=[True, False])
ev.to_csv("lr_candidate_evidence.csv", index=False)
print(ev.head(20)[["sender", "receiver", "ligand", "receptor", "pathway", "score", "p_or_rank",
                   "neighbour_z", "pubmed_n"]].to_string())

top = ev.head(30).copy()
top["lr"] = top["ligand"] + " -> " + top["receptor"]
top["pair"] = top["sender"] + " -> " + top["receiver"]
fig, ax = plt.subplots(figsize=(max(8, 0.4 * top["pair"].nunique()), max(6, 0.3 * top["lr"].nunique())))
s = ax.scatter(top["pair"], top["lr"], c=top["neighbour_z"], cmap="coolwarm", vmin=-5, vmax=5,
               s=30 + 200 * top["score"] / top["score"].max())
plt.colorbar(s, label="neighbourhood z (sender-receiver)"); plt.xticks(rotation=90)
plt.tight_layout(); plt.savefig("lr_candidates.png", dpi=150); plt.close()
```

Read each candidate across the columns and classify it in the report:

| Evidence pattern | Interpretation |
|---|---|
| Significant, co-located (z > 2), literature support | Strong candidate, known biology |
| Significant, co-located, no literature | Novel candidate; prioritise for validation |
| Significant, not co-located, secreted ligand | Possible paracrine signal; weaker |
| Significant, not co-located, contact-dependent | Unlikely in this tissue |
| Only one partner above `expr_prop` | Not supported |

Expression does not prove signalling; state validation routes (spatial
protein staining, receptor blocking, perturbation) for the top candidates.

## Key Parameters

| Parameter | Default | Effect |
|---|---|---|
| `QUERY` | from the user | Which pathways are examined |
| `SENDERS` / `RECEIVERS` | all | Restrict the direction of signalling |
| `n_neighs` | 10 | Neighbourhood size for co-location |
| neighbour z cutoff | 2 | What counts as co-located |
| `CONTEXT` | empty | Restricts literature counts to a disease/tissue |
| pairs queried | 50 | Number of PubMed requests |

## Common Recipes

### Recipe: Are Ligand and Receptor Actually Expressed?

Aggregated scores can hide that only a few cells express a partner. Report
the fraction of sender cells expressing the ligand and receiver cells
expressing the receptor:

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

### Recipe: Read the Papers Behind a Candidate

Fetch titles and abstracts for the top hits of one pair:

```python
EFETCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
LIGAND, RECEPTOR = "CD274", "PDCD1"
term = f"{LIGAND}[tiab] AND {RECEPTOR}[tiab]" + (f" AND ({CONTEXT})" if CONTEXT else "")
ids = requests.get(EUTILS, params={"db": "pubmed", "term": term, "retmode": "json", "retmax": 5,
                                   "sort": "relevance"}, timeout=30).json()["esearchresult"]["idlist"]
time.sleep(0.4)
text = requests.get(EFETCH, params={"db": "pubmed", "id": ",".join(ids), "rettype": "abstract",
                                    "retmode": "text"}, timeout=30).text
print(text[:3000])
```

### Recipe: Classify Candidates by Evidence Pattern

Apply the interpretation table above as rules, so every candidate carries an
explicit evidence class the report can cite:

```python
CONTACT = {"CD274", "PDCD1", "PDCD1LG2", "CTLA4", "CD28", "CD80", "CD86", "JAG1", "JAG2",
           "DLL1", "DLL3", "DLL4", "NOTCH1", "NOTCH2", "NOTCH3", "NOTCH4", "TIGIT", "PVR", "NECTIN2"}

def evidence_class(row):
    co = row["neighbour_z"] > 2 if pd.notna(row["neighbour_z"]) else None
    lit = (row.get("pubmed_n") or 0) > 0
    contact = row["ligand"].split("_")[0] in CONTACT
    if co is None:
        return "no spatial data"
    if co:
        return "strong, known" if lit else "novel, co-located"
    return "unlikely (contact, not co-located)" if contact else "possible paracrine"

ev["evidence_class"] = ev.apply(evidence_class, axis=1)
ev.to_csv("lr_candidate_evidence.csv", index=False)
print(ev["evidence_class"].value_counts())
```

`CONTACT` is a starting list of membrane-bound partners; extend it for the
pathways in `QUERY`.

## Expected Outputs

- `lr_candidate_evidence.csv` - candidates with statistics, pathway, co-location z, PubMed count
- `lr_candidates.png` - dot plot of top candidates

## Troubleshooting

| Problem | Cause | Fix |
|---|---|---|
| Pathway query returns nothing | Mouse symbols or the pathway genes are not in the panel | Map to human; check `adata.var_names` for the genes |
| Complex pairs never match | CellPhoneDB complex names instead of genes | Use the `genes` column from `significant_long.csv` |
| `KeyError` in neighbour z | Label spelling differs between results and `adata` | Use the same label column for inference and here |
| PubMed HTTP 429 | Too many requests | Increase `time.sleep`; lower the number of pairs |
| Literature counts inflated | Gene symbol is a common word (e.g. `MET`, `KIT`) | Add `CONTEXT` or check abstracts |

## Related Skills

- `cellphonedb-cell-cell-interaction` - produces `significant_long.csv`
- `liana-spatial-cell-cell-communication` - LIANA consensus, multi-sample and spatial methods
- `spatial-transcriptomics-cell-cell-communication` - standard spatial LR workflow
- `spatial-transcriptomics-analysis-squidpy` - other spatial statistics (co-occurrence, Ripley)
- `spatial-transcriptomics-cell-type-annotation` - cell type labels

## References

- Dimitrov et al. (2024) LIANA+, Nature Cell Biology: https://doi.org/10.1038/s41556-024-01469-w
- Troule et al. (2025) CellPhoneDB v5, Nature Protocols: https://doi.org/10.1038/s41596-024-01137-1
- Palla et al. (2022) Squidpy, Nature Methods: https://doi.org/10.1038/s41592-021-01358-2
- NCBI E-utilities documentation: https://www.ncbi.nlm.nih.gov/books/NBK25501/
