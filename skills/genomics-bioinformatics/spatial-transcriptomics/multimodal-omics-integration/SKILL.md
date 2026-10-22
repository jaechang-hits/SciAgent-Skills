---
name: "multimodal-omics-integration"
description: "Multimodal and multi-section integration for spatial and single-cell omics: totalVI joint RNA + protein (Visium CytAssist Gene and Protein, CITE-seq), MultiVI joint RNA + ATAC (10x Multiome, spatial ATAC-RNA), BBKNN integration of several tissue sections, scanpy ingest label transfer between sections, and gene signature scores mapped on tissue. Outputs joint latent spaces, denoised protein maps, integrated clusters, transferred labels. For dissociated CITE-seq and scVI/scANVI use scvi-tools-single-cell; for MOFA+ factor analysis use mofaplus-multi-omics or muon-multiomics-singlecell; for Harmony use harmony-batch-correction."
license: "CC-BY-4.0"
---

# Multimodal Omics Integration

## Overview

Combine modalities measured on the same spots or cells, or several sections of
the same tissue, into one representation. Output: joint latent spaces and
clusters, denoised protein maps, integrated sections, transferred labels and
signature scores on the tissue.

| Question | Method | Module |
|---|---|---|
| RNA + protein on the same spots / cells | totalVI | 1-2 |
| RNA + chromatin accessibility on the same cells | MultiVI | 3 |
| Several sections or samples, one modality | BBKNN | 4 |
| Labels from an annotated section onto a new one | scanpy ingest | 5 |
| Pathway or cell state activity on tissue | `sc.tl.score_genes` | 6 |
| Unsupervised factors across 2+ omics | MOFA+ | `mofaplus-multi-omics` |

## When to Use

- Analysing Visium CytAssist Gene and Protein (or CITE-seq) data with RNA and protein in one model
- Integrating RNA and ATAC measured on the same cells (10x Multiome, spatial ATAC-RNA)
- Clustering several tissue sections together without merging their coordinates
- Copying labels from an annotated section to a new section of the same platform
- Mapping pathway or cell state signatures onto the tissue
- Use `scvi-tools-single-cell` instead for dissociated scVI/scANVI workflows without a spatial angle
- For factor analysis across omics layers, use `mofaplus-multi-omics` or `muon-multiomics-singlecell` instead

## Prerequisites

- **Input**: raw counts for every modality (totalVI and MultiVI model counts)
- **Compute**: scvi-tools pulls torch; GPU recommended for MultiVI, totalVI runs on CPU
  for a few thousand spots
- **Python packages**: `scvi-tools`, `mudata` (Module 3), `bbknn` (Module 4), `scanpy`

```bash
# Install only what `import` reports missing. `--pypi` keeps the env's scanpy/numba
# stack; a conda add can swap it and bare pip can shadow it.
pixi add --pypi scvi-tools mudata bbknn scanpy
```

## Quick Start

Integrate two sections and cluster them jointly:

```python
import bbknn
import scanpy as sc

adata = sc.concat({"s1": sc.read_h5ad("section1.h5ad"), "s2": sc.read_h5ad("section2.h5ad")},
                  label="section", index_unique="-")
sc.pp.normalize_total(adata); sc.pp.log1p(adata); sc.pp.pca(adata, n_comps=30)
bbknn.bbknn(adata, batch_key="section", n_pcs=30)
sc.tl.leiden(adata, key_added="joint_cluster", flavor="igraph", n_iterations=2)
```

## Core API

### Module 1: Load Spatial RNA + Protein (Visium CytAssist)

Demo: 10x human tonsil, FFPE, CytAssist Gene and Protein (~35 antibodies).
For your own data set `OUTS` to the Space Ranger `outs/` folder.

```python
import tarfile
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd
import scanpy as sc

CACHE = Path("data_cache/CytAssist_FFPE_Protein_Expression_Human_Tonsil")
BASE = ("https://cf.10xgenomics.com/samples/spatial-exp/2.1.0/CytAssist_FFPE_Protein_Expression_Human_Tonsil/"
        "CytAssist_FFPE_Protein_Expression_Human_Tonsil_")
CACHE.mkdir(parents=True, exist_ok=True)
for name in ["filtered_feature_bc_matrix.h5", "spatial.tar.gz"]:
    if not (CACHE / name).exists():
        urllib.request.urlretrieve(BASE + name, CACHE / name)          # ~37 MB + ~34 MB
if not (CACHE / "spatial").exists():
    with tarfile.open(CACHE / "spatial.tar.gz") as tar:
        tar.extractall(CACHE, filter="data")
OUTS = CACHE

raw = sc.read_10x_h5(OUTS / "filtered_feature_bc_matrix.h5", gex_only=False)
raw.var_names_make_unique()
print(raw.var["feature_types"].value_counts())   # Gene Expression + Antibody Capture
pos = pd.read_csv(OUTS / "spatial/tissue_positions.csv", index_col=0)
raw.obsm["spatial"] = pos.loc[raw.obs_names, ["pxl_col_in_fullres", "pxl_row_in_fullres"]].to_numpy(float)

rna = raw[:, raw.var["feature_types"] == "Gene Expression"].copy()
prot = raw[:, raw.var["feature_types"] == "Antibody Capture"]
rna.obsm["protein_expression"] = pd.DataFrame(prot.X.toarray(), index=prot.obs_names,
                                              columns=prot.var_names)
sc.pp.filter_cells(rna, min_counts=200)
print(rna, f"\nproteins: {rna.obsm['protein_expression'].shape[1]}")
```

### Module 2: Joint RNA + Protein with totalVI

totalVI separates protein foreground from background binding and learns one
latent space from both modalities.

```python
import scvi

rna.layers["counts"] = rna.X.copy()
tmp = rna.copy()                                 # HVGs on log data; model on counts
sc.pp.normalize_total(tmp)
sc.pp.log1p(tmp)
sc.pp.highly_variable_genes(tmp, n_top_genes=4000)
rna = rna[:, tmp.var["highly_variable"]].copy()

scvi.model.TOTALVI.setup_anndata(rna, layer="counts", protein_expression_obsm_key="protein_expression",
                                 batch_key=None)  # set to the section/sample column for several slides
model = scvi.model.TOTALVI(rna, n_latent=20)
model.train(max_epochs=400, early_stopping=True)

rna.obsm["X_totalVI"] = model.get_latent_representation()
rna_norm, prot_norm = model.get_normalized_expression(n_samples=25, return_mean=True)
rna.obsm["protein_denoised"] = prot_norm         # DataFrame, spots x proteins
sc.pp.neighbors(rna, use_rep="X_totalVI")
sc.tl.umap(rna)
sc.tl.leiden(rna, resolution=0.6, key_added="totalvi_leiden", flavor="igraph", n_iterations=2)

show = list(prot_norm.columns[:4])
for p in show:
    rna.obs[f"prot_{p}"] = np.log1p(prot_norm[p].to_numpy())
sc.pl.embedding(rna, basis="spatial", color=["totalvi_leiden"] + [f"prot_{p}" for p in show],
                size=1.5, show=False, save="_totalvi.png")
model.save("totalvi_model", overwrite=True)
rna.write_h5ad("totalvi_result.h5ad", compression="gzip")
```

Compare raw and denoised protein maps for known markers (CD3, CD20 / MS4A1,
CD21 in tonsil follicles) before trusting clusters. Isotype-control antibodies
should come out near zero after denoising.

### Module 3: Joint RNA + ATAC with MultiVI

Input is a MuData with an RNA and an ATAC modality of the same cells (10x
Multiome; spatial ATAC-RNA-seq has the same layout plus coordinates). Demo: 10x
PBMC 10k Multiome subset from the scvi-tools tutorial.

```python
import mudata as md
import scipy.sparse as sp

path = Path("data_cache/pbmc_10k_preprocessed.h5mu")
if not path.exists():
    path.parent.mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve("https://exampledata.scverse.org/scvi-tools/pbmc_10k_preprocessed.h5mu", path)
mdata = md.read_h5mu(path)
RNA, ATAC = "rna_subset", "atac_subset"          # modality names in your MuData
for m in (RNA, ATAC):
    mdata.mod[m].X = sp.csr_matrix(mdata.mod[m].X)
mdata.update()

scvi.model.MULTIVI.setup_mudata(mdata, modalities={"rna_layer": RNA, "atac_layer": ATAC})
mvi = scvi.model.MULTIVI(mdata, n_genes=mdata.mod[RNA].n_vars, n_regions=mdata.mod[ATAC].n_vars)
mvi.train()                                      # GPU strongly recommended (~100k peaks)

joint = mdata.mod[RNA].copy()
joint.obsm["X_multivi"] = mvi.get_latent_representation()
sc.pp.neighbors(joint, use_rep="X_multivi")
sc.tl.umap(joint)
sc.tl.leiden(joint, key_added="multivi_leiden", flavor="igraph", n_iterations=2)
access = mvi.get_normalized_accessibility()      # imputed accessibility, cells x peaks
joint.write_h5ad("multivi_result.h5ad", compression="gzip")
print(joint.obs["multivi_leiden"].value_counts())
```

For a batch, add `batch_key="<obs column>"` to `setup_mudata` and
`"batch_key": RNA` to `modalities`. On spatial ATAC-RNA data copy the
coordinates into `joint.obsm["spatial"]` and plot `multivi_leiden` on them.

### Module 4: Integrate Several Sections (BBKNN)

BBKNN builds the neighbour graph from k neighbours **per section**, so sections
mix in the graph without changing expression values. Spatial coordinates stay
per section.

```python
import bbknn

PATHS = {"s1": "section1.h5ad", "s2": "section2.h5ad"}   # raw counts + obsm["spatial"] each
combined = sc.concat({k: sc.read_h5ad(v) for k, v in PATHS.items()}, label="section", index_unique="-")
combined.layers["counts"] = combined.X.copy()
sc.pp.normalize_total(combined)
sc.pp.log1p(combined)
sc.pp.highly_variable_genes(combined, n_top_genes=2000, batch_key="section")  # panels: skip
sc.pp.pca(combined, n_comps=30)
bbknn.bbknn(combined, batch_key="section", n_pcs=30, neighbors_within_batch=3)
sc.tl.umap(combined)
sc.tl.leiden(combined, resolution=0.5, key_added="bbknn_leiden", flavor="igraph", n_iterations=2)

mix = pd.crosstab(combined.obs["bbknn_leiden"], combined.obs["section"], normalize="index").round(2)
print(mix)                                       # a cluster from one section only: biology or residual batch
for s in PATHS:
    part = combined[combined.obs["section"] == s]
    sc.pl.embedding(part, basis="spatial", color="bbknn_leiden", size=1.5, show=False, save=f"_bbknn_{s}.png")
combined.write_h5ad("bbknn_result.h5ad", compression="gzip")
```

### Module 5: Transfer Labels Between Sections (ingest)

`sc.tl.ingest` projects a query onto the reference PCA/UMAP and copies labels
from nearest neighbours. It does no batch correction, so use it between
sections of the **same platform and panel**. For an scRNA-seq reference onto
imaging data use the Harmony route in
`spatial-transcriptomics-cell-type-annotation`; for Visium spots use
deconvolution.

```python
ref = sc.read_h5ad("celltype_annotated.h5ad")    # annotated section, log-normalised X
query = sc.read_h5ad("new_section.h5ad")         # log-normalised X
LABELS = ["cell_type"]

common = ref.var_names.intersection(query.var_names)
print(f"shared genes: {len(common)}")
ref, query = ref[:, common].copy(), query[:, common].copy()
sc.pp.pca(ref, n_comps=30)                       # PCA on the shared genes only
sc.pp.neighbors(ref, n_neighbors=15)
sc.tl.umap(ref)
sc.tl.ingest(query, ref, obs=LABELS, embedding_method="umap")
query.obs[LABELS].to_csv("ingest_annotations.csv")
print(query.obs["cell_type"].value_counts())
query.write_h5ad("ingest_result.h5ad", compression="gzip")
```

### Module 6: Score Gene Signatures on the Tissue

```python
adata = sc.read_h5ad("path/to/spatial.h5ad")    # all genes, obsm["spatial"]
X_IS_COUNTS = True                               # False if X is already log-normalised
if X_IS_COUNTS:
    sc.pp.normalize_total(adata)
    sc.pp.log1p(adata)
SIGNATURES = {"T_cell": ["CD3D", "CD3E", "CD2", "CD8A"], "B_cell": ["MS4A1", "CD79A", "CD19"]}

lookup = {g.upper(): g for g in adata.var_names}             # case-insensitive match, names unchanged
for name, genes in SIGNATURES.items():
    found = [lookup[g.upper()] for g in genes if g.upper() in lookup]
    missing = [g for g in genes if g.upper() not in lookup]
    print(f"{name}: {len(found)}/{len(genes)} genes found; missing {missing}")
    if found:
        sc.tl.score_genes(adata, found, score_name=f"{name}_score", ctrl_size=50, n_bins=25)
cols = [c for c in adata.obs if c.endswith("_score")]
adata.obs[cols].to_csv("signature_scores.csv")
sc.pl.embedding(adata, basis="spatial", color=cols, cmap="viridis", size=1.5, show=False, save="_scores.png")
```

Scores are relative to random control genes of similar expression; on a
targeted panel of a few hundred genes lower `ctrl_size` and read scores as
rankings, not absolute activity.

## Common Workflows

### Workflow: Name totalVI Clusters from Denoised Proteins

Modules 1-2, then a protein evidence table per cluster - antibodies are often
the clearest markers on CytAssist data:

```python
prot = pd.DataFrame(np.log1p(prot_norm.to_numpy()), index=prot_norm.index, columns=prot_norm.columns)
by_cluster = prot.groupby(rna.obs["totalvi_leiden"].to_numpy()).mean()
z = (by_cluster - by_cluster.mean()) / by_cluster.std(ddof=0)
top = z.apply(lambda r: ", ".join(r.nlargest(4).index), axis=1)
rna_log = rna.copy(); sc.pp.normalize_total(rna_log); sc.pp.log1p(rna_log)   # rna.X holds counts
sc.tl.rank_genes_groups(rna_log, "totalvi_leiden", method="wilcoxon")
genes = (sc.get.rank_genes_groups_df(rna_log, group=None).groupby("group").head(5)
         .groupby("group")["names"].apply(", ".join))
evidence = pd.DataFrame({"n_spots": rna.obs["totalvi_leiden"].value_counts(), "top_proteins": top,
                         "top_genes": genes})
evidence.to_csv("totalvi_cluster_evidence.csv")
print(evidence)
```

Name each cluster from both columns; a cluster supported by RNA but not by
protein (or the reverse) deserves a note in the report.

### Workflow: Compare Signatures Across Integrated Sections

Modules 4 and 6: integrate sections, score signatures, then compare each
joint cluster's score between sections:

```python
combined = sc.read_h5ad("bbknn_result.h5ad")          # Module 4 output, log-normalised X
lookup = {g.upper(): g for g in combined.var_names}
for name, genes in SIGNATURES.items():
    found = [lookup[g.upper()] for g in genes if g.upper() in lookup]
    if len(found) >= 3:
        sc.tl.score_genes(combined, found, score_name=f"{name}_score")
cols = [c for c in combined.obs if c.endswith("_score")]
table = combined.obs.groupby(["bbknn_leiden", "section"], observed=True)[cols].mean().unstack("section")
table.round(3).to_csv("signature_by_cluster_section.csv")
print(table.round(2))
```

## Key Parameters

| Parameter | Default | Effect |
|---|---|---|
| `n_latent` (totalVI) | 20 | Joint latent dimensions |
| `n_top_genes` (totalVI) | 4000 | RNA genes modelled with the proteins |
| `max_epochs` | 400 (totalVI); scvi default (MultiVI) | Training length; early stopping on validation loss |
| `batch_key` | None | Section/sample column corrected inside the scvi model |
| `neighbors_within_batch` | 3 | BBKNN neighbours taken from each section |
| `ctrl_size` (`score_genes`) | 50 | Control genes per expression bin |

## Common Recipes

### Recipe: Does Protein Agree with RNA?

For markers measured both ways, low correlation flags a weak antibody or
post-transcriptional regulation:

```python
PAIRS = {"CD3": "CD3E", "CD20": "MS4A1", "CD4": "CD4", "CD8": "CD8A"}   # protein name -> gene
norm = rna.copy(); sc.pp.normalize_total(norm); sc.pp.log1p(norm)
rows = []
for protein, gene in PAIRS.items():
    pcol = [c for c in prot_norm.columns if c.upper().startswith(protein.upper())]
    if pcol and gene in norm.var_names:
        g = np.asarray(norm[:, gene].X.todense()).ravel() if hasattr(norm.X, "todense") else norm[:, gene].X.ravel()
        rows.append((protein, gene, np.corrcoef(np.log1p(prot_norm[pcol[0]]), g)[0, 1]))
print(pd.DataFrame(rows, columns=["protein", "gene", "r"]).round(2))
```

### Recipe: totalVI Across Several Sections

Set `batch_key` so the model removes section effects inside the latent space:

```python
sections = sc.concat({"s1": rna_s1, "s2": rna_s2}, label="section", index_unique="-")   # each prepared as in Module 1
sections.obsm["protein_expression"] = pd.concat([rna_s1.obsm["protein_expression"],
                                                 rna_s2.obsm["protein_expression"]]).set_axis(sections.obs_names)
sections.layers["counts"] = sections.X.copy()
scvi.model.TOTALVI.setup_anndata(sections, layer="counts", protein_expression_obsm_key="protein_expression",
                                 batch_key="section")
model = scvi.model.TOTALVI(sections, n_latent=20)
model.train(max_epochs=400, early_stopping=True)
sections.obsm["X_totalVI"] = model.get_latent_representation()
```

Both sections need the same antibody panel; keep the shared proteins only if
they differ.

## Expected Outputs

- `totalvi_result.h5ad`, `totalvi_model/` - joint latent space, denoised protein, clusters
- `multivi_result.h5ad` - RNA+ATAC latent space and clusters
- `bbknn_result.h5ad` - integrated sections with clusters
- `ingest_annotations.csv`, `ingest_result.h5ad` - labels transferred to the new section
- `signature_scores.csv` - per-spot/cell signature scores
- `figures/` - spatial maps of clusters, proteins and scores

## Troubleshooting

| Problem | Cause | Fix |
|---|---|---|
| totalVI `ValueError` on protein data | Proteins in `X`, not `obsm` | Split by `feature_types` into `obsm["protein_expression"]` (Module 1) |
| Denoised protein flat everywhere | Too few epochs or very low antibody counts | Check raw counts per antibody; train longer |
| MultiVI `n_genes`/`n_regions` error | Constructor sizes missing or modalities misnamed | Pass both sizes; check `mdata.mod` keys |
| MultiVI training very slow | CPU with ~100k peaks | Use a GPU, or keep peaks found in > 1-5% of cells |
| BBKNN clusters still split by section | Strong batch effect | Use scVI with `batch_key` (`scvi-tools-single-cell`) or Harmony |
| ingest labels all one type | Different platform / normalisation between sections | Normalise both the same way; use the Harmony route for cross-platform transfer |
| `score_genes` warns about missing genes | Panel lacks them | Report coverage; do not score with < 3 genes |

## Related Skills

- `scvi-tools-single-cell` - scVI/scANVI and totalVI on dissociated cells
- `muon-multiomics-singlecell` - MuData handling, WNN, MOFA through muon
- `mofaplus-multi-omics` - MOFA+ factor analysis across omics layers
- `harmony-batch-correction` - linear batch correction of PCA embeddings
- `spatial-transcriptomics-cell-type-annotation` - reference-based labels for imaging data
- `spatial-transcriptomics-deconvolution-cell2location` - cell type abundance on Visium spots
- `spatial-domain-detection` - tissue domains from the integrated data

## References

- Gayoso et al. (2021) totalVI, Nature Methods: https://doi.org/10.1038/s41592-020-01050-x
- Ashuach et al. (2023) MultiVI, Nature Methods: https://doi.org/10.1038/s41592-023-01909-9
- Polanski et al. (2019) BBKNN, Bioinformatics: https://doi.org/10.1093/bioinformatics/btz625
- scvi-tools documentation: https://docs.scvi-tools.org/en/stable/
- scanpy ingest: https://scanpy.readthedocs.io/en/stable/generated/scanpy.tl.ingest.html
