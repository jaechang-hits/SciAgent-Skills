---
name: "maxquant-proteomics"
description: "MaxQuant + Perseus proteomics pipeline: configure and run MaxQuant for label-free quantification (LFQ) and SILAC; parse proteinGroups.txt in Python; filter contaminants/reverse decoys; log2-transform and median-normalize LFQ intensities; impute MNAR missing values; t-test with FDR correction; volcano plot; GO/pathway enrichment. Use Proteome Discoverer for Thermo instrument-native processing; FragPipe/MSFragger for GPU-accelerated database search."
license: "Apache-2.0"
---

# MaxQuant + Perseus — Proteomics Analysis Pipeline

## Overview

MaxQuant is the community-standard software for label-free quantification (LFQ) and SILAC proteomics. It performs database search, protein grouping, and intensity-based quantification from raw LC-MS/MS files, producing `proteinGroups.txt` as the primary output. Downstream statistical analysis — filtering, normalization, imputation, differential abundance testing, and visualization — is performed in Python using pandas, scipy, and matplotlib/seaborn, mirroring the Perseus workflow in a reproducible scripting environment.

## When to Use

- Performing label-free quantification (LFQ) of proteins across multiple biological conditions — MaxQuant's MaxLFQ algorithm is the community benchmark
- Running SILAC (stable isotope labeling) experiments with light/heavy or triple-label designs
- Processing iTRAQ or TMT isobaric labeling experiments via MaxQuant's reporter ion quantification
- Identifying and quantifying proteins when you need the widely-cited MaxQuant output format (`proteinGroups.txt`) for comparison with published datasets
- Performing statistical differential abundance analysis on MaxQuant outputs without installing Perseus (GUI-only, Windows)
- Generating publication-quality volcano plots and GO enrichment from proteomics data in a reproducible Python workflow
- Use **Proteome Discoverer** instead when working with Thermo raw files requiring instrument-native processing or Sequest HT
- Use **FragPipe/MSFragger** instead for GPU-accelerated database search (3–10× faster) or when processing DIA (data-independent acquisition) data

## Prerequisites

- **MaxQuant**: Windows software; download from https://maxquant.org/ (v2.4+); requires .NET 6 runtime
- **Python packages**: `pandas`, `numpy`, `scipy`, `matplotlib`, `seaborn`, `statsmodels`, `gseapy`
- **Data requirements**: Thermo `.raw` files or mzML-converted files; FASTA protein database (UniProt reviewed + contaminant database)
- **Environment**: MaxQuant runs on Windows (GUI or CLI); Python analysis runs cross-platform

```bash
pip install pandas numpy scipy matplotlib seaborn statsmodels gseapy
```

```bash
# Install pyMaxQuant for programmatic mqpar.xml configuration
pip install pymaxquant
```

## Quick Start

```python
import pandas as pd
import numpy as np

# Load MaxQuant output
df = pd.read_csv("combined/txt/proteinGroups.txt", sep="\t", low_memory=False)
print(f"Raw protein groups: {len(df)}")

# Filter contaminants, reverse decoys, only-by-site
mask = (
    (df["Potential contaminant"] != "+") &
    (df["Reverse"] != "+") &
    (df["Only identified by site"] != "+")
)
df = df[mask].copy()
print(f"After filtering: {len(df)} protein groups")

# Extract LFQ intensity columns
lfq_cols = [c for c in df.columns if c.startswith("LFQ intensity ")]
print(f"LFQ columns: {lfq_cols}")

# Log2-transform (0 → NaN)
lfq = df[lfq_cols].replace(0, np.nan)
lfq = np.log2(lfq)
print(f"Valid values per sample:\n{lfq.notna().sum()}")
```

## Workflow

### Step 1: Configure MaxQuant Parameters via mqpar.xml

MaxQuant is controlled by an XML parameter file (`mqpar.xml`). Edit it programmatically to set file paths, enzyme, modifications, and quantification type before running the search.

```python
import xml.etree.ElementTree as ET

def update_mqpar(template_path: str, output_path: str,
                 raw_files: list[str], fasta_path: str,
                 experiment_names: list[str]) -> None:
    """Update mqpar.xml with sample-specific file paths."""
    tree = ET.parse(template_path)
    root = tree.getroot()

    # Set raw file paths
    file_paths_node = root.find(".//filePaths")
    file_paths_node.clear()
    for rf in raw_files:
        elem = ET.SubElement(file_paths_node, "string")
        elem.text = rf

    # Set experiment names (maps files to conditions)
    experiments_node = root.find(".//experiments")
    experiments_node.clear()
    for name in experiment_names:
        elem = ET.SubElement(experiments_node, "string")
        elem.text = name

    # Set FASTA database
    fasta_node = root.find(".//fastaFiles/FastaFileInfo/fastaFilePath")
    fasta_node.text = fasta_path

    tree.write(output_path, xml_declaration=True, encoding="utf-8")
    print(f"Written: {output_path}")

# Example usage
raw_files = [
    r"C:\Data\ctrl_rep1.raw",
    r"C:\Data\ctrl_rep2.raw",
    r"C:\Data\treat_rep1.raw",
    r"C:\Data\treat_rep2.raw",
]
update_mqpar(
    template_path="mqpar_template.xml",
    output_path="mqpar.xml",
    raw_files=raw_files,
    fasta_path=r"C:\Databases\human_uniprot_contaminants.fasta",
    experiment_names=["ctrl", "ctrl", "treat", "treat"],
)
```

Key `mqpar.xml` parameters (set in template or edit directly):

```xml
<!-- Enzyme and search settings -->
<enzymes>
  <string>Trypsin/P</string>
</enzymes>
<maxMissedCleavages>2</maxMissedCleavages>
<variableModifications>
  <string>Oxidation (M)</string>
  <string>Acetyl (Protein N-term)</string>
</variableModifications>
<fixedModifications>
  <string>Carbamidomethyl (C)</string>
</fixedModifications>

<!-- LFQ settings -->
<lfqMode>1</lfqMode>                     <!-- 1 = LFQ enabled -->
<lfqMinRatioCount>2</lfqMinRatioCount>   <!-- minimum peptides for LFQ -->
<matchBetweenRuns>True</matchBetweenRuns>

<!-- FDR thresholds -->
<peptideFdr>0.01</peptideFdr>
<proteinFdr>0.01</proteinFdr>
```

### Step 2: Run MaxQuant from Command Line (Windows)

MaxQuant can be run headlessly from the Windows command prompt using the bundled `MaxQuantCmd.exe`.

```bat
REM Windows Command Prompt — run MaxQuant with configured mqpar.xml
REM Adjust path to match your MaxQuant installation directory

set MQ_PATH=C:\Program Files\MaxQuant\bin\MaxQuantCmd.exe
set MQPAR=C:\Projects\proteomics\mqpar.xml

"%MQ_PATH%" "%MQPAR%"

REM For specific workflow steps only (useful for reruns):
REM Step IDs: 0=write tables, 1=feature detection, 7=peptide identification
"%MQ_PATH%" "%MQPAR%" --steps 1,7,11
```

```bash
# Cross-platform: run MaxQuant under Wine on Linux/macOS (CI/server use)
wine MaxQuantCmd.exe mqpar.xml

# Monitor progress log
tail -f combined/proc/#runningTimes.txt
```

### Step 3: Load and Filter proteinGroups.txt

Filter out reverse decoys, potential contaminants, and proteins only identified by modification site.

```python
import pandas as pd
import numpy as np

def load_protein_groups(path: str) -> pd.DataFrame:
    """Load MaxQuant proteinGroups.txt with quality filters applied."""
    df = pd.read_csv(path, sep="\t", low_memory=False)
    print(f"Total protein groups: {len(df)}")

    # Remove reverse decoys, contaminants, and only-by-site hits
    n_before = len(df)
    df = df[
        (df.get("Reverse", pd.Series("")) != "+") &
        (df.get("Potential contaminant", pd.Series("")) != "+") &
        (df.get("Only identified by site", pd.Series("")) != "+")
    ].copy()
    print(f"After quality filter: {len(df)} ({n_before - len(df)} removed)")

    # Parse gene names (take first entry for multi-gene groups)
    df["Gene names"] = df["Gene names"].fillna("Unknown").str.split(";").str[0]

    # Set unique index on majority protein ID
    df = df.set_index("Majority protein IDs")
    return df

# Load output
pg = load_protein_groups("combined/txt/proteinGroups.txt")

# Identify LFQ intensity columns
lfq_cols = [c for c in pg.columns if c.startswith("LFQ intensity ")]
print(f"LFQ samples ({len(lfq_cols)}): {lfq_cols}")
# Output: LFQ samples (6): ['LFQ intensity ctrl_1', 'LFQ intensity ctrl_2', ...]
```

### Step 4: Log2 Transform and Median Normalize LFQ Intensities

Replace zero intensities with NaN (missing values in MaxQuant are exported as 0), log2-transform, then apply per-sample median centering.

```python
def prepare_lfq_matrix(df: pd.DataFrame, lfq_cols: list[str]) -> pd.DataFrame:
    """Extract, transform, and normalize LFQ intensity matrix."""
    # Extract and rename columns (strip 'LFQ intensity ' prefix)
    lfq = df[lfq_cols].copy()
    lfq.columns = [c.replace("LFQ intensity ", "") for c in lfq_cols]

    # Replace 0 with NaN (MaxQuant encodes missing as 0)
    lfq = lfq.replace(0, np.nan)

    # Log2 transform
    lfq = np.log2(lfq)

    # Median centering per sample (subtract per-column median of valid values)
    col_medians = lfq.median(axis=0)
    global_median = col_medians.median()
    lfq = lfq.subtract(col_medians, axis=1).add(global_median)

    print(f"Matrix shape: {lfq.shape}")
    print(f"Missing values per sample:\n{lfq.isna().sum()}")
    print(f"Valid values per sample:\n{lfq.notna().sum()}")
    return lfq

lfq_matrix = prepare_lfq_matrix(pg, lfq_cols)
# Matrix shape: (3241, 6)
# Missing values per sample: ctrl_1: 421, ctrl_2: 389, ...
```

### Step 5: Impute Missing Values (MNAR Strategy)

Missing-not-at-random (MNAR) values arise from proteins below the detection limit. Impute from the low end of the observed intensity distribution — the standard Perseus approach.

```python
def impute_mnar(lfq: pd.DataFrame,
                width: float = 0.3,
                downshift: float = 1.8,
                random_state: int = 42) -> pd.DataFrame:
    """
    Impute MNAR missing values from a downshifted Gaussian.

    Parameters
    ----------
    width      : std of imputation distribution (fraction of sample std)
    downshift  : downshift in units of sample std below mean
    random_state : for reproducibility
    """
    rng = np.random.default_rng(random_state)
    lfq_imp = lfq.copy()

    for col in lfq_imp.columns:
        col_data = lfq_imp[col].dropna()
        col_mean = col_data.mean()
        col_std = col_data.std()

        n_missing = lfq_imp[col].isna().sum()
        if n_missing > 0:
            imputed = rng.normal(
                loc=col_mean - downshift * col_std,
                scale=width * col_std,
                size=n_missing,
            )
            lfq_imp.loc[lfq_imp[col].isna(), col] = imputed

    print(f"Imputed {lfq.isna().sum().sum()} missing values")
    return lfq_imp

lfq_imputed = impute_mnar(lfq_matrix)
# Imputed 2847 missing values
```

### Step 6: Statistical Testing — t-test with FDR Correction

Perform two-sample t-tests for each protein between conditions, then apply Benjamini-Hochberg FDR correction.

```python
from scipy import stats
from statsmodels.stats.multitest import multipletests

def differential_abundance(lfq: pd.DataFrame,
                            group_a: list[str],
                            group_b: list[str],
                            alpha: float = 0.05) -> pd.DataFrame:
    """
    Two-sample t-test + BH FDR correction for all proteins.

    Parameters
    ----------
    group_a, group_b : sample name lists for each condition
    alpha : FDR threshold
    """
    results = []
    for protein_id, row in lfq.iterrows():
        a_vals = row[group_a].dropna().values
        b_vals = row[group_b].dropna().values

        if len(a_vals) >= 2 and len(b_vals) >= 2:
            t_stat, p_val = stats.ttest_ind(a_vals, b_vals, equal_var=False)
            log2fc = b_vals.mean() - a_vals.mean()
        else:
            t_stat, p_val, log2fc = np.nan, np.nan, np.nan

        results.append({
            "protein_id": protein_id,
            "log2FC": log2fc,
            "pvalue": p_val,
            "t_stat": t_stat,
        })

    res_df = pd.DataFrame(results).set_index("protein_id")

    # BH FDR correction on valid p-values
    valid = res_df["pvalue"].notna()
    _, padj, _, _ = multipletests(res_df.loc[valid, "pvalue"], method="fdr_bh")
    res_df.loc[valid, "padj"] = padj

    # Add significance flag
    res_df["significant"] = (res_df["padj"] < alpha) & (res_df["pvalue"].notna())
    sig_count = res_df["significant"].sum()
    print(f"Significant proteins (FDR < {alpha}): {sig_count}")

    return res_df.sort_values("padj")

# Define sample groups
group_ctrl  = ["ctrl_1",  "ctrl_2",  "ctrl_3"]
group_treat = ["treat_1", "treat_2", "treat_3"]

results = differential_abundance(lfq_imputed, group_ctrl, group_treat)
print(results[results["significant"]].head(10))
# Significant proteins (FDR < 0.05): 312
```

### Step 7: Volcano Plot Visualization

Generate a publication-quality volcano plot showing log2 fold change vs. -log10(p-value) with significance thresholds highlighted.

```python
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

def plot_volcano(results: pd.DataFrame,
                 gene_names: pd.Series,
                 fc_threshold: float = 1.0,
                 pval_threshold: float = 0.05,
                 top_n_labels: int = 10,
                 save_path: str = "volcano_plot.pdf") -> None:
    """Volcano plot: log2FC vs -log10(adjusted p-value)."""
    df = results.copy()
    df["gene"] = gene_names.reindex(df.index).fillna("Unknown")
    df["-log10p"] = -np.log10(df["padj"].clip(lower=1e-300))

    # Classify regulation
    df["regulation"] = "ns"
    df.loc[(df["log2FC"] >  fc_threshold) & (df["padj"] < pval_threshold), "regulation"] = "up"
    df.loc[(df["log2FC"] < -fc_threshold) & (df["padj"] < pval_threshold), "regulation"] = "down"

    color_map = {"up": "#D62728", "down": "#1F77B4", "ns": "#AAAAAA"}

    fig, ax = plt.subplots(figsize=(7, 6))
    for reg, grp in df.groupby("regulation"):
        ax.scatter(grp["log2FC"], grp["-log10p"],
                   c=color_map[reg], s=12, alpha=0.7, linewidths=0, label=reg)

    # Threshold lines
    ax.axhline(-np.log10(pval_threshold), color="k", lw=0.8, ls="--", alpha=0.5)
    ax.axvline( fc_threshold,  color="k", lw=0.8, ls="--", alpha=0.5)
    ax.axvline(-fc_threshold, color="k", lw=0.8, ls="--", alpha=0.5)

    # Label top significant proteins by -log10p
    top = df[df["regulation"] != "ns"].nlargest(top_n_labels, "-log10p")
    for _, row in top.iterrows():
        ax.text(row["log2FC"], row["-log10p"] + 0.1, row["gene"],
                fontsize=6, ha="center", va="bottom")

    # Counts in legend
    up_n   = (df["regulation"] == "up").sum()
    down_n = (df["regulation"] == "down").sum()
    patches = [
        mpatches.Patch(color="#D62728", label=f"Up ({up_n})"),
        mpatches.Patch(color="#1F77B4", label=f"Down ({down_n})"),
        mpatches.Patch(color="#AAAAAA", label="ns"),
    ]
    ax.legend(handles=patches, fontsize=8, frameon=False)
    ax.set_xlabel("log₂ Fold Change (treat / ctrl)", fontsize=11)
    ax.set_ylabel("-log₁₀(adjusted p-value)", fontsize=11)
    ax.set_title("Differential Protein Abundance", fontsize=12)
    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches="tight")
    plt.show()
    print(f"Saved: {save_path}")

plot_volcano(results, pg["Gene names"])
```

### Step 8: GO/Pathway Enrichment of Significant Proteins

Run over-representation analysis (ORA) on significantly up- and down-regulated proteins using gseapy's Enrichr API.

```python
import gseapy as gp

def run_enrichment(results: pd.DataFrame,
                   gene_names: pd.Series,
                   gene_sets: list[str] | None = None,
                   top_n: int = 20) -> dict[str, pd.DataFrame]:
    """
    ORA enrichment for up- and down-regulated proteins via Enrichr.

    Parameters
    ----------
    gene_sets : Enrichr gene set libraries (default: GO BP + KEGG)
    top_n     : top results to display per direction
    """
    if gene_sets is None:
        gene_sets = ["GO_Biological_Process_2023", "KEGG_2021_Human"]

    results_out = {}
    gene_map = gene_names.reindex(results.index).fillna("Unknown")

    for direction in ("up", "down"):
        sig = results[
            (results["significant"]) &
            (results["log2FC"] > 0 if direction == "up" else results["log2FC"] < 0)
        ]
        gene_list = gene_map.reindex(sig.index).tolist()
        print(f"{direction.capitalize()}-regulated: {len(gene_list)} proteins")

        if len(gene_list) < 5:
            print(f"  Too few proteins for enrichment (n={len(gene_list)}), skipping")
            continue

        enr = gp.enrichr(
            gene_list=gene_list,
            gene_sets=gene_sets,
            organism="Human",
            outdir=f"enrichment_{direction}",
            cutoff=0.05,
        )
        top_results = enr.results.sort_values("Adjusted P-value").head(top_n)
        results_out[direction] = top_results
        print(top_results[["Term", "Adjusted P-value", "Overlap"]].to_string(index=False))

    return results_out

enr_results = run_enrichment(results, pg["Gene names"])
```

## Key Parameters

| Parameter | Default | Range / Options | Effect |
|-----------|---------|-----------------|--------|
| `matchBetweenRuns` | `False` | `True` / `False` | Transfers identifications across runs by retention time matching; increases quantified protein count 10–30% |
| `lfqMinRatioCount` | `2` | `1`–`5` | Minimum peptide pairs required for LFQ normalization; lower values increase coverage but reduce accuracy |
| `maxMissedCleavages` | `2` | `0`–`4` | Tryptic missed cleavages allowed; increase for samples with poor digestion |
| `peptideFdr` / `proteinFdr` | `0.01` | `0.001`–`0.05` | FDR thresholds for peptide and protein identifications |
| MNAR `downshift` | `1.8` | `1.5`–`2.5` | Shifts imputation distribution below detection limit in units of column std; larger = more conservative imputation |
| MNAR `width` | `0.3` | `0.1`–`0.5` | Width of imputed distribution relative to column std |
| t-test `alpha` | `0.05` | `0.01`–`0.1` | FDR significance threshold for differential abundance |
| `fc_threshold` (volcano) | `1.0` | `0.5`–`2.0` | log2 fold-change cutoff for "significant" label in volcano plot |

## Key Concepts

### MaxQuant Output Files

| File | Content |
|------|---------|
| `proteinGroups.txt` | Primary output: one row per protein group with LFQ/SILAC intensities, peptide counts, sequence coverage |
| `peptides.txt` | Peptide-level quantification with charge states and modifications |
| `evidence.txt` | Individual MS/MS identifications (one row per peptide-spectrum match) |
| `msms.txt` | Full MS/MS scan data including fragment ions and scores |
| `summary.txt` | Per-raw-file statistics: identifications, MS/MS counts, calibration |

### LFQ Intensity vs. iBAQ

- **LFQ (Label-Free Quantification)**: MaxLFQ algorithm normalizes intensities across samples based on razor+unique peptide ratios. Use for cross-sample comparisons (fold changes). Stored in `LFQ intensity <sample>` columns.
- **iBAQ (intensity-Based Absolute Quantification)**: Divides summed peptide intensities by the number of theoretically observable peptides. Use for estimating copy numbers and comparing absolute abundance between proteins within a sample. Stored in `iBAQ` column.
- **SILAC ratio**: Direct H/L ratio from isotope-labeled pairs. More accurate than LFQ for small fold changes.

### Perseus Equivalent Operations in Python

| Perseus step | Python equivalent |
|--------------|-------------------|
| Filter rows by categorical column | `df[df["Reverse"] != "+"]` |
| Replace 0 with NaN | `df.replace(0, np.nan)` |
| Log2 transform | `np.log2(df)` |
| Median normalization | `df.subtract(df.median()).add(global_median)` |
| MNAR imputation (normal distribution) | `impute_mnar()` function above |
| Two-sample t-test | `scipy.stats.ttest_ind()` + `multipletests()` |
| Volcano plot | `matplotlib.pyplot` scatter + threshold lines |
| Hierarchical clustering | `seaborn.clustermap()` |

## Common Recipes

### Recipe: SILAC Ratio Analysis

When to use: SILAC experiments with H/L or H/M/L labeling instead of LFQ.

```python
import pandas as pd
import numpy as np

# Load proteinGroups.txt for SILAC experiment
df = pd.read_csv("combined/txt/proteinGroups.txt", sep="\t", low_memory=False)

# Filter contaminants and decoys
df = df[(df["Reverse"] != "+") & (df["Potential contaminant"] != "+")].copy()

# Extract H/L ratio columns (log2-transformed)
ratio_cols = [c for c in df.columns if c.startswith("Ratio H/L ") and "normalized" in c.lower()]
if not ratio_cols:
    # Fall back to non-normalized
    ratio_cols = [c for c in df.columns if c.startswith("Ratio H/L")]

print(f"SILAC ratio columns: {ratio_cols}")
ratios = df[ratio_cols].copy().replace(0, np.nan)

# Log2 transform ratios
log2_ratios = np.log2(ratios)
log2_ratios.columns = [c.replace("Ratio H/L normalized ", "") for c in ratio_cols]

# Summary statistics per sample
print(log2_ratios.describe().round(3))
```

### Recipe: Hierarchical Clustering Heatmap

When to use: visualizing patterns across all significant proteins simultaneously.

```python
import seaborn as sns
import matplotlib.pyplot as plt

def plot_heatmap(lfq_imputed: pd.DataFrame,
                 results: pd.DataFrame,
                 gene_names: pd.Series,
                 top_n: int = 50,
                 save_path: str = "heatmap.pdf") -> None:
    """Hierarchical clustering heatmap of top significant proteins."""
    sig_proteins = results[results["significant"]].nlargest(top_n, "-log10p" if "-log10p" in results else "padj").index
    # Recalculate if needed
    sig_proteins = results[results["significant"]].nsmallest(top_n, "padj").index

    heatmap_data = lfq_imputed.loc[sig_proteins].copy()
    heatmap_data.index = gene_names.reindex(sig_proteins).fillna(sig_proteins)

    # Z-score per row for visualization
    heatmap_z = heatmap_data.subtract(heatmap_data.mean(axis=1), axis=0).divide(
        heatmap_data.std(axis=1).replace(0, 1), axis=0
    )

    g = sns.clustermap(
        heatmap_z,
        cmap="RdBu_r",
        center=0,
        vmin=-2.5, vmax=2.5,
        figsize=(8, 10),
        yticklabels=True,
        xticklabels=True,
        dendrogram_ratio=(0.15, 0.1),
        cbar_kws={"label": "Z-score (log₂ LFQ)"},
    )
    g.ax_heatmap.set_yticklabels(g.ax_heatmap.get_yticklabels(), fontsize=6)
    plt.savefig(save_path, dpi=300, bbox_inches="tight")
    print(f"Saved: {save_path}")

plot_heatmap(lfq_imputed, results, pg["Gene names"])
```

### Recipe: STRING-db Network Enrichment for Significant Proteins

When to use: protein-protein interaction network analysis and enrichment without downloading gene sets locally.

```python
import requests
import pandas as pd

def string_enrichment(gene_list: list[str],
                      species: int = 9606,
                      fdr_threshold: float = 0.05) -> pd.DataFrame:
    """Query STRING /enrichment endpoint for GO/KEGG enrichment."""
    url = "https://string-db.org/api/json/enrichment"
    params = {
        "identifiers": "\r".join(gene_list),
        "species": species,
        "caller_identity": "maxquant_proteomics_skill",
    }
    response = requests.post(url, data=params)
    response.raise_for_status()

    enr_df = pd.DataFrame(response.json())
    if enr_df.empty:
        print("No enrichment results returned")
        return enr_df

    enr_df = enr_df[enr_df["fdr"].astype(float) < fdr_threshold]
    enr_df = enr_df.sort_values("fdr")
    print(f"Enriched terms (FDR < {fdr_threshold}): {len(enr_df)}")
    print(enr_df[["category", "term", "description", "fdr", "number_of_genes"]].head(15).to_string(index=False))
    return enr_df

# Significant up-regulated gene names
up_genes = pg.loc[
    results[(results["significant"]) & (results["log2FC"] > 1)].index, "Gene names"
].tolist()

string_enr = string_enrichment(up_genes)
```

### Recipe: Parse MaxQuant Output with pyMaxQuant

When to use: reading and filtering MaxQuant text files with a higher-level API.

```python
# pyMaxQuant provides typed accessors for MaxQuant output files
# Install: pip install pymaxquant
from maxquant.io import read_protein_groups

# Load with built-in contaminant filtering
pg_clean = read_protein_groups(
    "combined/txt/proteinGroups.txt",
    filter_invalid=True,      # removes reverse, contaminant, only-by-site
)
print(f"Loaded {len(pg_clean)} filtered protein groups")

# Access LFQ columns via helper
lfq_df = pg_clean.filter(like="LFQ intensity")
print(f"LFQ matrix: {lfq_df.shape}")
```

## Expected Outputs

| File | Description |
|------|-------------|
| `combined/txt/proteinGroups.txt` | Main MaxQuant output: protein groups with LFQ intensities, peptide counts, unique peptides, iBAQ |
| `combined/txt/peptides.txt` | Peptide-level quantification with modifications and charge states |
| `combined/txt/summary.txt` | Per-raw-file QC statistics: identification rates, MS/MS counts |
| `results_differential.csv` | Differential abundance table: `log2FC`, `pvalue`, `padj`, `significant` per protein |
| `volcano_plot.pdf` | Volcano plot with up/down-regulated proteins colored and top proteins labeled |
| `heatmap.pdf` | Hierarchical clustering heatmap of top significant proteins (Z-score normalized) |
| `enrichment_up/` | gseapy output directory: GO/KEGG enrichment for up-regulated proteins |
| `enrichment_down/` | gseapy output directory: GO/KEGG enrichment for down-regulated proteins |

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| MaxQuant produces 0 protein identifications | Wrong FASTA database or enzyme settings; raw file path not found | Verify `.raw` file paths in `mqpar.xml` are absolute Windows paths; confirm enzyme matches experiment (Trypsin/P vs Trypsin); check `summary.txt` for identification rate |
| All LFQ intensities are 0 after filtering | `matchBetweenRuns` off + sparse data, or wrong column selection | Check `combined/txt/proteinGroups.txt` directly; use `pg.filter(like="LFQ intensity")` to confirm column names; lower `lfqMinRatioCount` to 1 |
| Too many missing values after log2 transform | Insufficient replicates, inconsistent sample loading, or undetected peptides | Enable `matchBetweenRuns`; verify equal protein loading (Bradford/BCA); consider stricter valid-value filter (require 3/3 per group) before imputation |
| Memory error loading `proteinGroups.txt` | File is large (>500 MB for DDA with many samples) | Use `pd.read_csv(..., low_memory=False, usecols=[...])` to select only needed columns; or use `pd.read_csv(..., chunksize=...)` |
| gseapy Enrichr returns empty results | Gene symbols unrecognized or network timeout | Ensure gene list uses HGNC symbols (not UniProt IDs); check internet connectivity; use `gp.enrichr(..., timeout=60)` |
| Volcano plot: all proteins in "ns" | FDR threshold too stringent or `padj` not calculated | Verify `multipletests` returned valid FDR values; try relaxing `alpha` to 0.1; check sample group assignments are correct |
| MaxQuant run hangs at "Feature detection" | Low memory (MaxQuant needs 4–8 GB RAM per 3–4 raw files) | Process files in smaller batches; increase system RAM; close other applications |
| Imputation inflates false positives | Imputing too aggressively (low `downshift`) | Increase `downshift` to 2.0–2.5; alternatively, filter to proteins with ≥ 2 valid values per group before testing |

## References

- [MaxQuant software and documentation](https://maxquant.org/) — official MaxQuant download, manual, and parameter guide
- [Perseus computational platform](https://maxquant.net/perseus/) — MaxQuant companion statistical analysis tool; basis for the Python workflow above
- [Cox et al. (2008) *Nature Biotechnology* — MaxQuant paper](https://doi.org/10.1038/nbt.1511) — original MaxQuant publication describing the MaxLFQ algorithm
- [Tyanova et al. (2016) *Nature Methods* — Perseus paper](https://doi.org/10.1038/nmeth.3901) — Perseus statistical framework reference; all workflow steps above mirror Perseus operations
- [pyMaxQuant GitHub](https://github.com/cshukai/pyMaxquant) — Python library for parsing MaxQuant output files
- [gseapy documentation](https://gseapy.readthedocs.io/) — gene set enrichment analysis library used in Step 8
- [STRING API enrichment](https://string-db.org/help/api/) — protein network enrichment endpoint used in Common Recipes
