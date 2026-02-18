---
name: "remap-database"
description: "Query the ReMap 2022 TF ChIP-seq binding peak database via REST API and BED file downloads. Retrieve all TF binding peaks overlapping a genomic region (chr:start-end), find TF peaks near a gene by name, list TFs available for a species, filter peaks by regulatory biotype (promoter, enhancer), and download peak BED files for a TF-cell type pair. Use for TF co-occupancy analysis, regulatory region annotation, and building TF binding atlases. For JASPAR motif matrices use jaspar-database; for ENCODE regulatory tracks use encode-database."
license: "CC-BY-4.0"
---

# ReMap Database

## Overview

ReMap 2022 is an integrative database of transcription factor (TF), cofactor, and chromatin regulator binding sites derived from uniformly reprocessed ChIP-seq experiments. The 2022 release catalogs 165 million non-redundant peaks from 8,113 ChIP-seq datasets covering 1,210 TFs across human (hg38/hg19), mouse (mm10), Drosophila, and Arabidopsis genomes. All peaks are called with a consistent pipeline from public GEO/ArrayExpress experiments. Access is via the ReMap 2022 REST API at `https://remap2022.univ-amu.fr/api/` and bulk BED file downloads; no authentication required.

## When to Use

- Finding all TFs with ChIP-seq peaks overlapping a genomic region of interest (e.g., a GWAS SNP locus or candidate enhancer)
- Retrieving TF peaks near a gene's transcription start site to map its proximal regulatory landscape
- Listing all TFs available in ReMap for human or mouse with their peak and dataset counts
- Filtering ChIP-seq peaks by regulatory biotype annotation (promoter, enhancer, exon, intron, intergenic) for a TF in a specific cell line
- Downloading a BED file of all binding peaks for a TF across all cell types for offline analysis
- Identifying co-binding TFs at a locus by querying all overlapping peaks and grouping by TF name
- Use `jaspar-database` instead when you need PWM/PFM sequence models of TF binding specificity rather than ChIP-seq peak locations
- For ENCODE-specific regulatory tracks and accessibility data use `encode-database`; ReMap aggregates TF binding peaks from many sources including ENCODE

## Prerequisites

- **Python packages**: `requests`, `pandas`, `matplotlib`
- **Data requirements**: genomic coordinates (GRCh38/hg38 or hg19), gene names, or TF names
- **Environment**: internet connection; no API key required
- **Rate limits**: no official published limits; use `time.sleep(0.5)` between batch requests to avoid server overload
- **Note**: The ReMap API is a research API; endpoint availability may vary. All examples include a BED download fallback.

```bash
pip install requests pandas matplotlib
```

## Quick Start

```python
import requests

REMAP_API = "https://remap2022.univ-amu.fr/api/v1"

# Query TF peaks overlapping a genomic region
r = requests.get(f"{REMAP_API}/peaks/overlap/", params={
    "chr": "chr17",
    "start": 7_670_000,
    "end": 7_690_000,
    "assembly": "hg38"
}, timeout=30)
r.raise_for_status()
peaks = r.json()
print(f"Peaks overlapping TP53 locus: {len(peaks)}")
tfs = set(p.get("name", "").split(":")[0] for p in peaks)
print(f"Unique TFs: {len(tfs)}")
print(f"TF names (first 10): {sorted(tfs)[:10]}")
```

## Core API

### Query 1: Region Overlap

Find all TF ChIP-seq peaks overlapping a specified genomic window. Returns peak records including TF name, cell type, coordinates, and score.

```python
import requests, time, pandas as pd

REMAP_API = "https://remap2022.univ-amu.fr/api/v1"

def query_region(chrom, start, end, assembly="hg38", timeout=30):
    """Return all ReMap peaks overlapping [chrom:start-end]."""
    r = requests.get(f"{REMAP_API}/peaks/overlap/", params={
        "chr": chrom, "start": start, "end": end, "assembly": assembly
    }, timeout=timeout)
    r.raise_for_status()
    return r.json()

# Query 100 kb window on chr17 around TP53
peaks = query_region("chr17", 7_670_000, 7_690_000, assembly="hg38")
print(f"Total peaks: {len(peaks)}")

# Parse name field: format is "TF:experiment_id:cell_type"
rows = []
for p in peaks:
    parts = p.get("name", "::").split(":")
    tf   = parts[0] if len(parts) > 0 else ""
    exp  = parts[1] if len(parts) > 1 else ""
    cell = parts[2] if len(parts) > 2 else ""
    rows.append({
        "chr": p.get("chr", p.get("chrom", "")),
        "start": p.get("start", 0),
        "end": p.get("end", 0),
        "tf_name": tf,
        "experiment_id": exp,
        "cell_type": cell,
        "score": p.get("score", 0),
    })

df = pd.DataFrame(rows)
print(f"\nUnique TFs: {df['tf_name'].nunique()}")
print(f"Top TFs by peak count:\n{df['tf_name'].value_counts().head(10).to_string()}")
```

```python
# Fallback: if API is unavailable, use a locally downloaded BED file
# Download from: https://remap2022.univ-amu.fr/download_page
# e.g., remap2022_all_macs2_hg38_v1_0.bed.gz

import pandas as pd

def query_region_from_bed(bed_file, chrom, start, end):
    """Filter a ReMap BED file for overlapping peaks."""
    cols = ["chr", "start", "end", "name", "score", "strand",
            "thick_start", "thick_end", "color"]
    df = pd.read_csv(bed_file, sep="\t", header=None, names=cols,
                     compression="infer")
    mask = (df["chr"] == chrom) & (df["end"] > start) & (df["start"] < end)
    return df[mask].reset_index(drop=True)

# Usage (requires downloaded BED):
# df = query_region_from_bed("remap2022_all_macs2_hg38_v1_0.bed.gz",
#                             "chr17", 7_670_000, 7_690_000)
```

### Query 2: Gene-Centric Query

Retrieve all TF ChIP-seq peaks near a gene's TSS, providing a promoter-proximal regulatory landscape for the gene.

```python
import requests, time, pandas as pd

REMAP_API = "https://remap2022.univ-amu.fr/api/v1"

def query_gene_peaks(gene_name, assembly="hg38", timeout=30):
    """Return all ReMap peaks near a gene TSS."""
    r = requests.get(f"{REMAP_API}/peaks/gene/", params={
        "gene": gene_name, "assembly": assembly
    }, timeout=timeout)
    r.raise_for_status()
    return r.json()

peaks = query_gene_peaks("MYC", assembly="hg38")
print(f"Peaks near MYC TSS: {len(peaks)}")

rows = []
for p in peaks:
    parts = p.get("name", "::").split(":")
    rows.append({
        "tf_name": parts[0] if parts else "",
        "cell_type": parts[2] if len(parts) > 2 else "",
        "chr": p.get("chr", p.get("chrom", "")),
        "start": p.get("start", 0),
        "end": p.get("end", 0),
        "score": p.get("score", 0),
        "biotype": p.get("biotype", ""),
    })

df = pd.DataFrame(rows)
print(f"\nTFs near MYC TSS ({df['tf_name'].nunique()} unique):")
print(df["tf_name"].value_counts().head(10).to_string())
print(f"\nCell types represented: {df['cell_type'].nunique()}")
```

### Query 3: TF Browser

List all TFs available in ReMap for a given genome assembly, with peak and experiment counts.

```python
import requests, time, pandas as pd

REMAP_API = "https://remap2022.univ-amu.fr/api/v1"

def list_tfs(assembly="hg38", timeout=30):
    """Return all TFs in ReMap for the given assembly with statistics."""
    r = requests.get(f"{REMAP_API}/tfbs/list/", params={"assembly": assembly}, timeout=timeout)
    r.raise_for_status()
    return r.json()

def get_database_stats(assembly="hg38", timeout=30):
    """Return overall database statistics for the assembly."""
    r = requests.get(f"{REMAP_API}/stats/", params={"assembly": assembly}, timeout=timeout)
    r.raise_for_status()
    return r.json()

# Database overview
try:
    stats = get_database_stats("hg38")
    print(f"ReMap 2022 hg38 statistics:")
    for k, v in stats.items():
        print(f"  {k}: {v}")
except Exception as e:
    print(f"Stats endpoint unavailable: {e}")
    print("ReMap 2022 hg38: 165M peaks, 1,210 TFs, 8,113 datasets (from publication)")

# TF list
try:
    tfs = list_tfs("hg38")
    df_tfs = pd.DataFrame(tfs)
    print(f"\nTFs available (hg38): {len(df_tfs)}")
    if "peak_count" in df_tfs.columns:
        top = df_tfs.nlargest(10, "peak_count")[["name", "peak_count", "dataset_count"]]
        print("Top 10 TFs by peak count:")
        print(top.to_string(index=False))
except Exception as e:
    print(f"TF list endpoint unavailable: {e}")
    print("Use TF name queries directly (Query 4) or download TF-specific BED files.")
```

### Query 4: TF-Specific Peak Query

Retrieve all peaks for a named TF in a given assembly, optionally filtered by cell type.

```python
import requests, time, pandas as pd

REMAP_API = "https://remap2022.univ-amu.fr/api/v1"

def query_tf_peaks(tf_name, assembly="hg38", timeout=30):
    """Return all ChIP-seq peaks for a TF across all cell types."""
    r = requests.get(f"{REMAP_API}/tfbs/name/", params={
        "name": tf_name, "assembly": assembly
    }, timeout=timeout)
    r.raise_for_status()
    return r.json()

peaks = query_tf_peaks("CTCF", assembly="hg38")
print(f"CTCF peaks (all cell types): {len(peaks)}")

# Parse and summarize
rows = []
for p in peaks:
    parts = p.get("name", "::").split(":")
    rows.append({
        "tf_name": parts[0] if parts else "",
        "cell_type": parts[2] if len(parts) > 2 else "",
        "chr":   p.get("chr",   p.get("chrom", "")),
        "start": p.get("start", 0),
        "end":   p.get("end",   0),
        "score": p.get("score", 0),
        "biotype": p.get("biotype", ""),
    })

df = pd.DataFrame(rows)
print(f"Cell types: {df['cell_type'].nunique()}")
print(f"Chromosomes: {df['chr'].nunique()}")
print(f"Peak width stats (bp):")
df["width"] = df["end"] - df["start"]
print(f"  Median: {df['width'].median():.0f}  Mean: {df['width'].mean():.0f}  "
      f"Min: {df['width'].min()}  Max: {df['width'].max()}")
```

### Query 5: Biotype Filter and Regulatory Annotation

Filter peaks by regulatory biotype annotation to identify binding at promoters, enhancers, or intergenic regions.

```python
import requests, pandas as pd, matplotlib.pyplot as plt

REMAP_API = "https://remap2022.univ-amu.fr/api/v1"

def get_biotypes(assembly="hg38", timeout=30):
    """List all regulatory biotype categories available."""
    r = requests.get(f"{REMAP_API}/biotypes/", params={"assembly": assembly}, timeout=timeout)
    r.raise_for_status()
    return r.json()

def query_tf_by_biotype(tf_name, biotype, assembly="hg38", timeout=30):
    """Retrieve TF peaks filtered by regulatory biotype."""
    r = requests.get(f"{REMAP_API}/peaks/biotype/", params={
        "name": tf_name, "biotype": biotype, "assembly": assembly
    }, timeout=timeout)
    r.raise_for_status()
    return r.json()

# List available biotypes
try:
    biotypes = get_biotypes("hg38")
    print(f"Available biotypes: {biotypes}")
except Exception:
    biotypes = ["promoter", "enhancer", "exon", "intron", "intergenic", "UTR"]
    print(f"Using known biotypes: {biotypes}")

# Query CTCF peaks and plot biotype distribution
peaks = query_tf_peaks("CTCF", assembly="hg38")  # from Query 4 function above

def query_tf_peaks(tf_name, assembly="hg38", timeout=30):
    r = requests.get(f"https://remap2022.univ-amu.fr/api/v1/tfbs/name/",
                     params={"name": tf_name, "assembly": assembly}, timeout=timeout)
    r.raise_for_status()
    return r.json()

peaks = query_tf_peaks("CTCF")
rows = [{"biotype": p.get("biotype", "unknown"),
         "cell_type": p.get("name", "::").split(":")[2] if len(p.get("name","").split(":")) > 2 else ""}
        for p in peaks]
df = pd.DataFrame(rows)

biotype_counts = df["biotype"].value_counts()
biotype_counts = biotype_counts[biotype_counts > 0]
print(f"\nCTCF peak biotype distribution:")
print(biotype_counts.to_string())

# Stacked bar chart across top 5 cell types
top_cells = df["cell_type"].value_counts().head(5).index.tolist()
pivot = (df[df["cell_type"].isin(top_cells)]
         .groupby(["cell_type", "biotype"])
         .size()
         .unstack(fill_value=0))

fig, ax = plt.subplots(figsize=(9, 5))
pivot.plot(kind="bar", stacked=True, ax=ax, colormap="tab10", edgecolor="white")
ax.set_xlabel("Cell Type")
ax.set_ylabel("Peak Count")
ax.set_title("CTCF ChIP-seq Peak Biotype Distribution by Cell Type (ReMap 2022, hg38)")
ax.legend(title="Biotype", bbox_to_anchor=(1.01, 1), loc="upper left", fontsize=8)
plt.tight_layout()
plt.savefig("CTCF_biotype_distribution.png", dpi=150, bbox_inches="tight")
print("Saved CTCF_biotype_distribution.png")
```

## Key Concepts

### Peak Name Field Format

The `name` field in every ReMap peak record encodes three pieces of information as a colon-separated string:

```
TF_NAME:EXPERIMENT_ID:CELL_TYPE
```

For example: `CTCF:GSE30263.SRX028592:GM12878`

Always parse with `.split(":")` and guard against missing parts. Some records may have fewer than three components if metadata is incomplete.

### Assemblies

| Assembly code | Organism | Notes |
|---------------|----------|-------|
| `hg38` | Homo sapiens (GRCh38) | Primary human assembly in ReMap 2022 |
| `hg19` | Homo sapiens (GRCh37) | Legacy human assembly; fewer datasets |
| `mm10` | Mus musculus | Primary mouse assembly |
| `dm6` | Drosophila melanogaster | Smaller dataset collection |
| `tair10` | Arabidopsis thaliana | Plant TF dataset |

### BED File Download (API Fallback)

When the REST API is unavailable or for offline bulk analysis, ReMap provides pre-built BED files at `https://remap2022.univ-amu.fr/download_page`. Key files:

- `remap2022_all_macs2_hg38_v1_0.bed.gz` — all peaks, hg38 (large, ~5 GB)
- `remap2022_{TF}_macs2_hg38_v1_0.bed.gz` — per-TF peak files
- `remap2022_crm_macs2_hg38_v1_0.bed.gz` — cis-regulatory modules (merged peaks)

```python
import pandas as pd

def load_remap_bed(bed_path, chrom=None, start=None, end=None):
    """
    Load a ReMap BED file with optional region filter.
    Columns: chr, start, end, name (TF:exp:cell), score, strand,
             thick_start, thick_end, itemRgb
    """
    cols = ["chr", "start", "end", "name", "score", "strand",
            "thick_start", "thick_end", "itemRgb"]
    df = pd.read_csv(bed_path, sep="\t", header=None, names=cols,
                     compression="infer", low_memory=False)
    if chrom:
        df = df[df["chr"] == chrom]
    if start is not None and end is not None:
        df = df[(df["end"] > start) & (df["start"] < end)]
    # Parse name field
    parts = df["name"].str.split(":", expand=True)
    df["tf_name"]       = parts[0]
    df["experiment_id"] = parts[1] if 1 in parts.columns else ""
    df["cell_type"]     = parts[2] if 2 in parts.columns else ""
    return df.reset_index(drop=True)

# Usage example (offline):
# df = load_remap_bed("remap2022_CTCF_macs2_hg38_v1_0.bed.gz",
#                     chrom="chr17", start=7_670_000, end=7_690_000)
# print(df.head())
```

## Common Workflows

### Workflow 1: TF Co-occupancy Analysis at a Locus

**Goal**: Identify all TFs with ChIP-seq evidence at a genomic locus and rank by peak count, then export a co-occupancy matrix.

```python
import requests, time, pandas as pd, matplotlib.pyplot as plt

REMAP_API = "https://remap2022.univ-amu.fr/api/v1"

def query_region(chrom, start, end, assembly="hg38", timeout=30):
    r = requests.get(f"{REMAP_API}/peaks/overlap/", params={
        "chr": chrom, "start": start, "end": end, "assembly": assembly
    }, timeout=timeout)
    r.raise_for_status()
    return r.json()

def parse_peaks(peaks):
    rows = []
    for p in peaks:
        parts = p.get("name", "::").split(":")
        rows.append({
            "tf_name":  parts[0] if len(parts) > 0 else "unknown",
            "cell_type": parts[2] if len(parts) > 2 else "unknown",
            "chr":   p.get("chr",   p.get("chrom", "")),
            "start": p.get("start", 0),
            "end":   p.get("end",   0),
            "score": p.get("score", 0),
        })
    return pd.DataFrame(rows)

# BRCA1 promoter region (GRCh38)
peaks = query_region("chr17", 43_044_000, 43_050_000, assembly="hg38")
df = parse_peaks(peaks)
print(f"Peaks at BRCA1 promoter: {len(df)}")

# TF occupancy summary
tf_summary = (df.groupby("tf_name")
                .agg(peak_count=("tf_name", "count"),
                     cell_types=("cell_type", "nunique"),
                     mean_score=("score", "mean"))
                .sort_values("peak_count", ascending=False))
print(f"\nTop TFs at BRCA1 promoter:")
print(tf_summary.head(15).to_string())
tf_summary.to_csv("BRCA1_promoter_TF_occupancy.csv")

# Horizontal bar chart
top = tf_summary.head(20)
fig, ax = plt.subplots(figsize=(8, 6))
ax.barh(top.index[::-1], top["peak_count"][::-1], color="#1f77b4", edgecolor="white")
ax.set_xlabel("Number of ChIP-seq Peaks")
ax.set_title("TF Co-occupancy at BRCA1 Promoter (ReMap 2022, hg38)")
plt.tight_layout()
plt.savefig("BRCA1_promoter_TF_cooccupancy.png", dpi=150, bbox_inches="tight")
print("Saved BRCA1_promoter_TF_cooccupancy.png")
```

### Workflow 2: Gene Regulatory Profile — TSS-Proximal TF Binding Atlas

**Goal**: For a list of genes, retrieve their promoter-proximal TF binding profiles and compare the TF repertoires across genes.

```python
import requests, time, pandas as pd

REMAP_API = "https://remap2022.univ-amu.fr/api/v1"

def query_gene_peaks(gene_name, assembly="hg38", timeout=30):
    try:
        r = requests.get(f"{REMAP_API}/peaks/gene/", params={
            "gene": gene_name, "assembly": assembly
        }, timeout=timeout)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"  Warning: {gene_name} failed — {e}")
        return []

genes_of_interest = ["MYC", "TP53", "BRCA1", "EGFR", "CDK4"]
gene_tf_profiles = {}

for gene in genes_of_interest:
    peaks = query_gene_peaks(gene, assembly="hg38")
    if peaks:
        tfs = set()
        for p in peaks:
            parts = p.get("name", "").split(":")
            if parts:
                tfs.add(parts[0])
        gene_tf_profiles[gene] = tfs
        print(f"{gene}: {len(peaks)} peaks, {len(tfs)} unique TFs")
    time.sleep(0.5)

# Build binary TF presence matrix
all_tfs = sorted(set().union(*gene_tf_profiles.values()))
matrix = pd.DataFrame(
    {gene: [1 if tf in gene_tf_profiles.get(gene, set()) else 0 for tf in all_tfs]
     for gene in genes_of_interest},
    index=all_tfs
)
print(f"\nTF × Gene matrix: {matrix.shape}")
print(f"TFs shared by all genes: {(matrix.sum(axis=1) == len(genes_of_interest)).sum()}")
matrix.to_csv("gene_TF_binding_atlas.csv")
print("Saved gene_TF_binding_atlas.csv")
```

### Workflow 3: Download and Analyze TF Peak BED File

**Goal**: Download a TF-specific ReMap BED file and analyze its genomic distribution with pandas.

```python
import requests, gzip, io, pandas as pd, time

# ReMap provides per-TF BED files. For large-scale offline analysis:
REMAP_DOWNLOAD_BASE = "https://remap2022.univ-amu.fr/storage/remap2022/hg38/MACS2"

def download_tf_bed(tf_name, assembly="hg38", save_path=None):
    """
    Attempt to download TF-specific BED file from ReMap.
    Falls back to API region query if download unavailable.
    """
    filename = f"remap2022_{tf_name}_macs2_{assembly}_v1_0.bed.gz"
    url = f"{REMAP_DOWNLOAD_BASE}/{filename}"
    print(f"Attempting download: {url}")
    r = requests.get(url, stream=True, timeout=60)
    if r.status_code == 200:
        if save_path:
            with open(save_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"Saved: {save_path}")
            return save_path
        else:
            # Read directly into DataFrame
            content = b"".join(r.iter_content(chunk_size=8192))
            cols = ["chr", "start", "end", "name", "score", "strand",
                    "thick_start", "thick_end", "itemRgb"]
            with gzip.open(io.BytesIO(content), "rt") as gz:
                df = pd.read_csv(gz, sep="\t", header=None, names=cols)
            return df
    else:
        print(f"Download returned {r.status_code}; use API query as fallback")
        return None

# Analyze a downloaded BED file
def analyze_remap_bed(df):
    """Compute summary statistics for a ReMap peak DataFrame."""
    parts = df["name"].str.split(":", expand=True)
    df = df.copy()
    df["tf_name"]   = parts[0]
    df["cell_type"] = parts[2] if 2 in parts.columns else "unknown"
    df["width"] = df["end"] - df["start"]

    print(f"Total peaks: {len(df):,}")
    print(f"Unique TFs: {df['tf_name'].nunique()}")
    print(f"Unique cell types: {df['cell_type'].nunique()}")
    print(f"\nPeak width (bp): median={df['width'].median():.0f}  "
          f"mean={df['width'].mean():.0f}  range=[{df['width'].min()}, {df['width'].max()}]")
    print(f"\nChromosome distribution:")
    chr_counts = df["chr"].value_counts().head(5)
    print(chr_counts.to_string())
    return df

# Example usage (requires BED download or substitute with API results):
# df_raw = download_tf_bed("CTCF", save_path="CTCF_hg38.bed.gz")
# if df_raw is not None:
#     df_analyzed = analyze_remap_bed(df_raw)
```

## Key Parameters

| Parameter | Endpoint | Default | Range / Options | Effect |
|-----------|----------|---------|-----------------|--------|
| `chr` | `/peaks/overlap/` | — | `chr1`–`chrX`, `chrY`, `chrM` | Chromosome for region query (include `chr` prefix) |
| `start` | `/peaks/overlap/` | — | Integer genomic coordinate | Region start (0-based) |
| `end` | `/peaks/overlap/` | — | Integer genomic coordinate | Region end (exclusive) |
| `assembly` | All endpoints | — | `hg38`, `hg19`, `mm10`, `dm6`, `tair10` | Genome assembly for coordinates and peak lookup |
| `gene` | `/peaks/gene/` | — | HGNC gene symbol (e.g., `TP53`, `MYC`) | Queries peaks near the gene's annotated TSS |
| `name` | `/tfbs/name/` | — | TF name as in ReMap (e.g., `CTCF`, `SP1`) | TF name is case-sensitive; match ReMap TF naming |
| `biotype` | `/peaks/biotype/` | — | `promoter`, `enhancer`, `exon`, `intron`, `intergenic`, `UTR` | Filters peaks by Ensembl regulatory biotype |
| `timeout` | All requests | 30 | Integer seconds | Increase to 60–120 for large gene/TF queries |

## Best Practices

1. **Parse the `name` field defensively**: The `TF:experiment:cell_type` format may have fewer than three components for some records. Always guard with `parts[n] if len(parts) > n else ""`.

2. **Use BED downloads for genome-wide analyses**: Querying large genomic regions or all peaks for a TF via the REST API can time out. For whole-genome or per-chromosome scans, download the per-TF or per-assembly BED files from the ReMap download page and filter locally with pandas or bedtools.

3. **Cross-reference with JASPAR for sequence evidence**: ReMap peaks show where TF binding was detected by ChIP-seq (positional evidence); JASPAR PWMs show what sequence the TF prefers (motif evidence). For robust regulatory annotation, require both: a ReMap peak in the region AND a JASPAR motif hit within the peak.

4. **Use `time.sleep(0.5)` in batch loops**: The ReMap API serves a research community; polite request pacing prevents throttling.

5. **Validate assembly coordinates**: ReMap 2022 hg38 peaks use 0-based half-open BED coordinates (`[start, end)`). When comparing with VCF or 1-based GFF coordinates, add 1 to `start`.

## Common Recipes

### Recipe: Find TFs Binding at a GWAS SNP

When to use: Prioritize functional candidates from a GWAS hit by identifying which TFs bind at the SNP location.

```python
import requests

REMAP_API = "https://remap2022.univ-amu.fr/api/v1"

def tfs_at_snp(chrom, pos, window=500, assembly="hg38"):
    """Find TFs with ChIP-seq peaks overlapping a SNP position ± window bp."""
    r = requests.get(f"{REMAP_API}/peaks/overlap/", params={
        "chr": chrom, "start": pos - window, "end": pos + window,
        "assembly": assembly
    }, timeout=30)
    r.raise_for_status()
    peaks = r.json()
    tfs = {}
    for p in peaks:
        parts = p.get("name", "::").split(":")
        tf = parts[0] if parts else "unknown"
        tfs[tf] = tfs.get(tf, 0) + 1
    return dict(sorted(tfs.items(), key=lambda x: -x[1]))

# Example: rs2736100 (TERT locus, chr5:1,286,401)
snp_tfs = tfs_at_snp("chr5", 1_286_401, window=500, assembly="hg38")
print(f"TFs at TERT GWAS SNP (±500 bp): {len(snp_tfs)}")
for tf, count in list(snp_tfs.items())[:10]:
    print(f"  {tf:<20s} {count:3d} peaks")
```

### Recipe: Compare TF Binding Profiles of Two Genes

When to use: Check whether two co-regulated genes share the same upstream TF binding landscape.

```python
import requests, time

REMAP_API = "https://remap2022.univ-amu.fr/api/v1"

def get_gene_tfs(gene, assembly="hg38"):
    try:
        r = requests.get(f"{REMAP_API}/peaks/gene/", params={"gene": gene, "assembly": assembly}, timeout=30)
        r.raise_for_status()
        peaks = r.json()
        return set(p.get("name", "").split(":")[0] for p in peaks if p.get("name", ""))
    except Exception as e:
        print(f"Warning: {gene} → {e}")
        return set()

gene_a, gene_b = "MYC", "MYCN"
tfs_a = get_gene_tfs(gene_a)
time.sleep(0.5)
tfs_b = get_gene_tfs(gene_b)

shared = tfs_a & tfs_b
only_a = tfs_a - tfs_b
only_b = tfs_b - tfs_a

print(f"{gene_a} TFs: {len(tfs_a)}  |  {gene_b} TFs: {len(tfs_b)}")
print(f"Shared: {len(shared)}  |  {gene_a}-only: {len(only_a)}  |  {gene_b}-only: {len(only_b)}")
print(f"\nShared TFs (first 15): {sorted(shared)[:15]}")
print(f"\n{gene_a}-only (first 10): {sorted(only_a)[:10]}")
```

### Recipe: Export Region Peaks as BED

When to use: Export ReMap query results to BED format for downstream bedtools intersection or IGV visualization.

```python
import requests, pandas as pd

REMAP_API = "https://remap2022.univ-amu.fr/api/v1"

def export_region_as_bed(chrom, start, end, outfile, assembly="hg38"):
    """Query ReMap region and save as 6-column BED file."""
    r = requests.get(f"{REMAP_API}/peaks/overlap/", params={
        "chr": chrom, "start": start, "end": end, "assembly": assembly
    }, timeout=30)
    r.raise_for_status()
    peaks = r.json()
    rows = [{
        "chr":   p.get("chr",   p.get("chrom", "")),
        "start": p.get("start", 0),
        "end":   p.get("end",   0),
        "name":  p.get("name",  "."),
        "score": p.get("score", 0),
        "strand": p.get("strand", "."),
    } for p in peaks]
    df = pd.DataFrame(rows)
    df = df.sort_values(["chr", "start"])
    df.to_csv(outfile, sep="\t", header=False, index=False)
    print(f"Saved {len(df)} peaks to {outfile}")
    return df

export_region_as_bed("chr17", 7_670_000, 7_690_000, "TP53_locus_remap.bed")
```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `404 Not Found` from API | Endpoint path changed or unavailable | Check `https://remap2022.univ-amu.fr/api/` for current endpoint list; fall back to BED download |
| Empty JSON list `[]` from region query | No peaks in region, or assembly mismatch | Verify coordinates are on the correct assembly; try a wider window (±10 kb) |
| Gene query returns empty | Gene symbol not recognized by ReMap | Try Ensembl gene symbol; some aliases are not mapped — verify with HGNC |
| `requests.exceptions.Timeout` | Large region or slow server | Increase `timeout=60`; for regions >1 Mb use BED file download instead |
| `name` field has only one component | Incomplete metadata in ReMap for that experiment | Guard with `parts[n] if len(parts) > n else "unknown"` |
| BED download 404 | Per-TF files use exact ReMap TF naming | Check TF name case and spelling at `https://remap2022.univ-amu.fr/download_page` |
| Duplicate peaks for same TF | Multiple experiments per TF in a cell type | Group by `tf_name` and count unique experiments; deduplicate peaks with bedtools merge |

## Related Skills

- `jaspar-database` — TF binding motif matrices (PWMs/PFMs); use alongside ReMap peak evidence for sequence-level validation
- `encode-database` — ENCODE regulatory tracks including TF ChIP-seq, DNase-seq, and ATAC-seq; partially overlaps with ReMap
- `homer-motif-analysis` — de novo motif discovery in ChIP-seq peak sets from ReMap or MACS3
- `macs3-peak-calling` — call peaks from raw ChIP-seq BAM files; ReMap provides pre-called peaks from the same approach
- `regulomedb-database` — regulatory variant scoring that integrates TF binding evidence similar to ReMap

## References

- [ReMap 2022 API documentation](https://remap2022.univ-amu.fr/api/) — REST API endpoint reference and interactive explorer
- [Hammal et al., Nucleic Acids Research 2022](https://doi.org/10.1093/nar/gkab996) — ReMap 2022 paper describing the 2022 release (165M peaks, 1,210 TFs)
- [ReMap portal and download page](https://remap2022.univ-amu.fr/) — web browser, download page for BED files and cis-regulatory modules
- [Chèneby et al., Nucleic Acids Research 2020](https://doi.org/10.1093/nar/gkz945) — ReMap 2020 paper describing the reprocessing pipeline and quality control methodology
