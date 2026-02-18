---
name: "gseapy-gene-enrichment"
description: "Gene set enrichment analysis (GSEA) and over-representation analysis (ORA) for RNA-seq and proteomics data. Wraps Enrichr API for ORA against MSigDB, KEGG, GO, and 200+ gene set databases; implements preranked GSEA for ranked gene lists from differential expression. Outputs enrichment tables and GSEA running-score plots. Use after DESeq2 or edgeR for pathway-level interpretation of differential expression results."
license: "MIT"
---

# GSEApy — Gene Set Enrichment Analysis in Python

## Overview

GSEApy provides Python implementations of GSEA and over-representation analysis (ORA) for interpreting gene expression changes at the pathway level. The `enrich` module queries the Enrichr API to test a gene list against 200+ databases (GO, KEGG, MSigDB Hallmarks, Reactome, WikiPathways). The `prerank` and `gsea` modules run the GSEA algorithm on a pre-ranked gene list or expression matrix — computing normalized enrichment scores (NES) and FDR values for each gene set. GSEApy integrates directly with pandas DataFrames from DESeq2 or scanpy differential expression output, making it the standard Python tool for pathway analysis in RNA-seq workflows.

## When to Use

- Interpreting DESeq2 or edgeR differential expression results at pathway/GO-term level
- Running fast ORA (over-representation analysis) against Enrichr's 200+ databases including GO, KEGG, and MSigDB Hallmarks
- Performing GSEA prerank analysis on a log2-fold-change-ranked gene list without an expression matrix
- Identifying enriched pathways in scRNA-seq cluster marker genes
- Generating publication-ready enrichment dot plots and GSEA running-score plots
- Use **GSEA Java application** for the official GUI-based analysis with full GSEA desktop interface
- Use **fgsea** (R) as an alternative with fast permutation-based p-values; GSEApy is preferred for Python-native pipelines

## Prerequisites

- **Python packages**: `gseapy`, `pandas`, `matplotlib`
- **Internet access**: `enrich` module queries the Enrichr API (requires connection)

```bash
pip install gseapy

# Verify
python -c "import gseapy; print(gseapy.__version__)"
# 1.1.3
```

## Quick Start

```python
import gseapy as gp

# ORA: test a gene list against GO Biological Process
gene_list = ["TP53", "BRCA1", "CDK2", "CCND1", "MYC", "EGFR", "KRAS", "PTEN"]

enr = gp.enrichr(gene_list=gene_list,
                 gene_sets=["GO_Biological_Process_2023"],
                 organism="human",
                 outdir=None)
print(enr.results.head(5)[["Term", "P-value", "Adjusted P-value", "Genes"]])
```

## Workflow

### Step 1: Over-Representation Analysis with Enrichr (ORA)

Test a gene list against pathway databases via the Enrichr API.

```python
import gseapy as gp
import pandas as pd

# Gene list from DESeq2 (significant upregulated genes)
sig_genes = ["TP53", "BRCA1", "CDK2", "CCND1", "MYC", "EGFR",
             "KRAS", "PTEN", "RB1", "AKT1", "PIK3CA", "MDM2"]

# Run ORA against multiple databases
enr = gp.enrichr(
    gene_list=sig_genes,
    gene_sets=[
        "GO_Biological_Process_2023",
        "KEGG_2021_Human",
        "MSigDB_Hallmark_2020",
        "Reactome_2022",
    ],
    organism="human",
    outdir="enrichr_results/",
    cutoff=0.05,
)

# Display top results
results = enr.results
print(f"Enriched terms: {len(results[results['Adjusted P-value'] < 0.05])}")
print(results[results["Adjusted P-value"] < 0.05].sort_values("Adjusted P-value")
      .head(10)[["Gene_set", "Term", "Adjusted P-value", "Combined Score"]])
```

### Step 2: List Available Gene Set Databases

Discover the 200+ databases available through Enrichr.

```python
import gseapy as gp

# List all available gene set libraries
libraries = gp.get_library_name(organism="human")
print(f"Available databases: {len(libraries)}")
print("Selected databases:")
for lib in sorted(libraries):
    if any(kw in lib for kw in ["GO_Bio", "KEGG", "Hallmark", "Reactome"]):
        print(f"  {lib}")

# Mouse databases
mouse_libs = gp.get_library_name(organism="mouse")
print(f"\nMouse databases: {len(mouse_libs)}")
```

### Step 3: GSEA Prerank — Ranked Gene List Analysis

Run GSEA on a log2 fold-change ranked gene list from differential expression.

```python
import gseapy as gp
import pandas as pd
import numpy as np

# Load DESeq2 results (or create example ranked list)
# deseq_results = pd.read_csv("deseq2_results.tsv", sep="\t", index_col=0)
# ranked = deseq_results["log2FoldChange"].dropna().sort_values(ascending=False)

# Example ranked gene list (gene → log2FC)
np.random.seed(42)
gene_names = [f"GENE_{i}" for i in range(1000)]
log2fc = np.random.normal(0, 2, 1000)
ranked = pd.Series(log2fc, index=gene_names).sort_values(ascending=False)

# Run preranked GSEA against MSigDB Hallmarks
pre_res = gp.prerank(
    rnk=ranked,
    gene_sets="MSigDB_Hallmark_2020",
    threads=4,
    min_size=15,
    max_size=500,
    permutation_num=1000,
    outdir="gsea_results/prerank/",
    seed=42,
    verbose=True,
)

# View results
res_df = pre_res.res2d
sig = res_df[res_df["FDR q-val"] < 0.25]
print(f"Significant gene sets (FDR < 0.25): {len(sig)}")
print(sig.sort_values("NES", ascending=False)[["Term", "NES", "NOM p-val", "FDR q-val"]].head(10))
```

### Step 4: Plot GSEA Running Score

Visualize the enrichment score curve for a specific gene set.

```python
import gseapy as gp
from gseapy.plot import gseaplot
import matplotlib.pyplot as plt

# Re-use pre_res from Step 3 (or load saved results)
# Select the top enriched gene set
top_term = pre_res.res2d.sort_values("NES", ascending=False).index[0]
print(f"Top enriched gene set: {top_term}")

# Plot running enrichment score
ax = gseaplot(
    rank_metric=pre_res.ranking,
    term=top_term,
    **pre_res.results[top_term],
    ofname="gsea_results/top_geneset_enrichment.pdf",
)
plt.tight_layout()
plt.savefig("gsea_enrichment_plot.png", dpi=150)
print("Saved: gsea_enrichment_plot.png")
```

### Step 5: Enrichment Dot Plot for Multiple Terms

Generate a dot plot showing enrichment significance and gene ratio across top pathways.

```python
import gseapy as gp
import matplotlib.pyplot as plt
from gseapy.plot import dotplot

# Run ORA and plot results
enr = gp.enrichr(
    gene_list=["TP53", "BRCA1", "CDK2", "CCND1", "MYC", "EGFR",
               "KRAS", "PTEN", "RB1", "AKT1", "PIK3CA", "MDM2",
               "BCL2", "CDKN1A", "E2F1", "CCNE1"],
    gene_sets=["KEGG_2021_Human"],
    organism="human",
    outdir=None,
    cutoff=0.05,
)

# Dot plot: x=gene ratio, size=-log10(p), color=adjusted p-value
ax = dotplot(
    enr.results,
    column="Adjusted P-value",
    x="Gene_set",
    title="KEGG Enrichment",
    cmap="viridis_r",
    size=10,
    top_term=15,
    figsize=(6, 8),
    ofname="enrichment_dotplot.pdf",
)
plt.tight_layout()
plt.savefig("enrichment_dotplot.png", dpi=150, bbox_inches="tight")
print("Saved: enrichment_dotplot.png")
```

### Step 6: Integrate with DESeq2 / scanpy Output

Use GSEApy directly on differential expression results.

```python
import gseapy as gp
import pandas as pd

# From DESeq2 output loaded into Python
# deseq_df = pd.read_csv("deseq2_results.tsv", sep="\t", index_col=0)
# deseq_df = deseq_df.dropna(subset=["log2FoldChange", "padj"])

# Simulate DESeq2 output
import numpy as np
np.random.seed(0)
n = 500
deseq_df = pd.DataFrame({
    "log2FoldChange": np.random.normal(0, 1.5, n),
    "padj": np.random.uniform(0, 1, n),
}, index=[f"GENE{i}" for i in range(n)])

# Significant up/down gene lists for ORA
up_genes = deseq_df[(deseq_df["padj"] < 0.05) & (deseq_df["log2FoldChange"] > 1)].index.tolist()
dn_genes = deseq_df[(deseq_df["padj"] < 0.05) & (deseq_df["log2FoldChange"] < -1)].index.tolist()
print(f"Upregulated: {len(up_genes)}, Downregulated: {len(dn_genes)}")

# ORA on upregulated genes
if up_genes:
    enr_up = gp.enrichr(gene_list=up_genes,
                         gene_sets=["GO_Biological_Process_2023", "KEGG_2021_Human"],
                         organism="human", outdir=None)
    sig_up = enr_up.results[enr_up.results["Adjusted P-value"] < 0.05]
    print(f"Enriched terms (upregulated): {len(sig_up)}")
    print(sig_up.sort_values("Adjusted P-value").head(5)[["Term", "Adjusted P-value"]])

# Preranked GSEA on full ranked list
ranked = deseq_df["log2FoldChange"].sort_values(ascending=False)
pre = gp.prerank(rnk=ranked, gene_sets="MSigDB_Hallmark_2020",
                 threads=4, permutation_num=500, outdir="gsea_out/", seed=42)
print(pre.res2d[pre.res2d["FDR q-val"] < 0.25].sort_values("NES", ascending=False)
      .head(5)[["Term", "NES", "FDR q-val"]])
```

## Key Parameters

| Parameter | Default | Range/Options | Effect |
|-----------|---------|---------------|--------|
| `gene_sets` (enrichr) | required | string or list | Database name(s) from Enrichr; use `gp.get_library_name()` to list |
| `organism` (enrichr) | `"human"` | `"human"`, `"mouse"`, `"fly"`, `"fish"`, `"worm"`, `"yeast"` | Species for gene set lookup |
| `cutoff` (enrichr) | `0.05` | 0–1 | Adjusted p-value cutoff for filtering results |
| `rnk` (prerank) | required | pd.Series | Gene → score mapping; sorted descending (log2FC recommended) |
| `permutation_num` (prerank) | `1000` | 100–10000 | Permutations for p-value estimation; 1000 for publication |
| `min_size` (prerank) | `15` | 5–50 | Minimum gene set size; filters small/poorly characterized sets |
| `max_size` (prerank) | `500` | 100–2000 | Maximum gene set size; filters very large generic sets |
| `threads` (prerank) | `4` | 1–64 | CPU threads for permutation |
| `seed` (prerank) | `None` | integer | Random seed for reproducibility |
| `weighted_score_type` (prerank) | `1` | 0, 1, 1.5 | GSEA weighting; 1 = standard weighted GSEA |

## Common Recipes

### Recipe 1: Compare Enrichment Between Two Conditions

```python
import gseapy as gp
import pandas as pd

conditions = {
    "treated_vs_ctrl": ["TP53", "BRCA1", "CDK2", "CCND1", "MYC"],
    "treated2_vs_ctrl": ["EGFR", "KRAS", "PTEN", "RB1", "AKT1"],
}

results = {}
for label, genes in conditions.items():
    enr = gp.enrichr(gene_list=genes,
                     gene_sets=["MSigDB_Hallmark_2020"],
                     organism="human",
                     outdir=None)
    sig = enr.results[enr.results["Adjusted P-value"] < 0.05]
    results[label] = set(sig["Term"])
    print(f"{label}: {len(sig)} significant Hallmark terms")

# Overlap
shared = results["treated_vs_ctrl"] & results["treated2_vs_ctrl"]
print(f"Shared terms: {shared}")
```

### Recipe 2: Batch Prerank for Multiple Comparisons

```python
import gseapy as gp
import pandas as pd
from pathlib import Path

# Load multiple DESeq2 result files
comparisons = {
    "treat_vs_ctrl": "deseq_treat_vs_ctrl.tsv",
    "drug_vs_ctrl": "deseq_drug_vs_ctrl.tsv",
}

for name, file in comparisons.items():
    # df = pd.read_csv(file, sep="\t", index_col=0)
    # ranked = df["log2FoldChange"].dropna().sort_values(ascending=False)
    
    # Example: generate synthetic ranked list
    import numpy as np
    ranked = pd.Series(np.random.normal(0, 1, 800),
                       index=[f"G{i}" for i in range(800)]).sort_values(ascending=False)
    
    pre = gp.prerank(
        rnk=ranked,
        gene_sets=["MSigDB_Hallmark_2020", "KEGG_2021_Human"],
        threads=4,
        permutation_num=500,
        outdir=f"gsea_results/{name}/",
        seed=42,
    )
    sig = pre.res2d[pre.res2d["FDR q-val"] < 0.25]
    print(f"{name}: {len(sig)} significant gene sets")
    pre.res2d.to_csv(f"gsea_results/{name}/all_results.tsv", sep="\t")
```

## Expected Outputs

| Output | Format | Description |
|--------|--------|-------------|
| `enr.results` | DataFrame | ORA results: Term, P-value, Adjusted P-value, Combined Score, Genes |
| `pre_res.res2d` | DataFrame | Prerank results: Term, ES, NES, NOM p-val, FDR q-val, Gene % |
| `gsea_results/*.csv` | CSV | Saved enrichment tables per database |
| `gsea_results/*.pdf` | PDF | GSEA running-score plots (one per gene set) |
| `enrichment_dotplot.png` | PNG | Dot plot of top enriched terms |
| `gseaplot output` | PNG/PDF | Running enrichment score + ranked list plot |

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `ConnectionError` in `enrichr` | No internet or Enrichr API down | Check https://maayanlab.cloud/Enrichr/; use local gene sets with `gene_sets="path/to/gmt"` |
| No significant terms returned | Gene list too small or wrong gene ID format | Use ≥10 genes; ensure HGNC symbols (not Ensembl IDs); convert with `pyensembl` |
| Prerank returns all NES ≈ 0 | Ranked list not sorted or too few genes | Verify `rnk` is sorted descending; check `min_size ≤` gene set sizes |
| `KeyError` in gene set | Gene set name misspelled | Use `gp.get_library_name()` to get exact database names |
| Low NES with FDR > 0.25 | Signal is weak or permutation count too low | Increase `permutation_num` to 1000; check raw p-values in `NOM p-val` |
| GSEA plot shows flat line | Gene set has no intersection with ranked list | Check gene naming; confirm gene set species matches data |
| Memory error during prerank | Large expression matrix + high permutations | Reduce `permutation_num`; use `prerank` instead of `gsea` when possible |
| Enrichr results differ from Java GSEA | Different gene set versions | Specify exact database version string from `gp.get_library_name()` |

## References

- [GSEApy documentation](https://gseapy.readthedocs.io/) — official usage guide and API reference
- [GSEApy GitHub: zqfang/GSEApy](https://github.com/zqfang/GSEApy) — source code and examples
- Fang Z et al. (2023) "GSEApy: a comprehensive package for performing gene set enrichment analysis in Python" — *Bioinformatics* 39(1):btac757. [DOI:10.1093/bioinformatics/btac757](https://doi.org/10.1093/bioinformatics/btac757)
- Subramanian A et al. (2005) "Gene set enrichment analysis: A knowledge-based approach for interpreting genome-wide expression profiles" — *PNAS* 102(43):15545-15550. [DOI:10.1073/pnas.0506580102](https://doi.org/10.1073/pnas.0506580102)
- [Enrichr gene set databases](https://maayanlab.cloud/Enrichr/) — full list of 200+ available gene set libraries
