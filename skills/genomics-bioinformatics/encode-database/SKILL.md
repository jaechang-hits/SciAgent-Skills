---
name: "encode-database"
description: "Query the ENCODE Portal REST API for regulatory genomics data: TF ChIP-seq experiments, ATAC-seq/DNase-seq accessibility peaks, histone mark tracks, and RNA-seq datasets across 1000+ cell types and tissues. Search experiments by assay, biosample, or target protein; download BED/bigWig files; retrieve candidate cis-regulatory elements (cCREs) from ENCODE SCREEN by genomic region or gene. Use for finding regulatory tracks to annotate variants, identifying open chromatin in a cell type of interest, and downloading peak files for ChIP-seq or ATAC-seq analysis. For regulatory variant scoring use regulomedb-database; for GWAS associations use gwas-database."
license: "CC-BY-4.0"
---

# ENCODE Database

## Overview

The ENCODE (Encyclopedia of DNA Elements) Project has generated thousands of functional genomics experiments — TF ChIP-seq, ATAC-seq, DNase-seq, histone ChIP-seq, and RNA-seq — across 1000+ human and mouse cell types and tissues. The ENCODE Portal REST API provides structured JSON access to experiment metadata, file download URLs, and SCREEN cCRE (candidate cis-Regulatory Elements) annotations. All data is freely accessible without authentication for most endpoints.

## When to Use

- Downloading TF ChIP-seq peak files (BED) for a specific transcription factor and cell type to annotate regulatory regions
- Finding ATAC-seq or DNase-seq peaks in a cell type to identify open chromatin regions near a gene of interest
- Retrieving cCREs (candidate cis-Regulatory Elements) overlapping a genomic region from ENCODE SCREEN
- Building reference regulatory tracks for variant annotation pipelines (e.g., annotating VCF variants against ENCODE peak sets)
- Exploring which experiments are available for a biosample (cell line, tissue, developmental stage) before planning a wet-lab experiment
- Querying all ChIP-seq experiments for a transcription factor across multiple cell types for comparative regulatory analysis
- Use `regulomedb-database` instead when you want pre-computed regulatory scores for specific SNPs — RegulomeDB integrates ENCODE data with eQTL and motif evidence into a single score
- Use `deeptools-ngs-analysis` instead when you have your own BAM files and need to generate bigWig coverage tracks; ENCODE database is for retrieving existing deposited data

## Prerequisites

- **Python packages**: `requests`, `pandas`, `matplotlib`
- **Data requirements**: experiment accessions (e.g., `ENCSR000AKC`), biosample names (e.g., `K562`), TF target names (e.g., `CTCF`, `TP53`), or genomic regions (`chr7:117548628-117748628`)
- **Environment**: internet connection; no authentication required for public data; add `Authorization: Bearer {api_key}` header for submitter access
- **Rate limits**: no published hard limit; add `time.sleep(0.5)` for large batch queries to avoid connection resets

```bash
pip install requests pandas matplotlib
```

## Quick Start

```python
import requests

BASE = "https://www.encodeproject.org"

def search_experiments(assay="TF ChIP-seq", target="CTCF", biosample="K562", limit=5):
    """Find ENCODE experiments matching assay type, target, and biosample."""
    params = {
        "type": "Experiment",
        "assay_title": assay,
        "target.label": target,
        "biosample_summary": biosample,
        "status": "released",
        "format": "json",
        "limit": limit,
    }
    r = requests.get(f"{BASE}/search/", params=params, timeout=30)
    r.raise_for_status()
    data = r.json()
    experiments = data.get("@graph", [])
    print(f"Found {data.get('total', 0)} experiments for {target} ChIP-seq in {biosample}")
    for exp in experiments:
        print(f"  {exp['accession']}  {exp.get('biosample_summary', '')}  {exp.get('lab', {}).get('title', '')}")
    return experiments

exps = search_experiments(assay="TF ChIP-seq", target="CTCF", biosample="K562")
```

## Core API

### Query 1: Experiment Search — Find Experiments by Assay, Biosample, Target

Search the ENCODE Portal for experiments matching structured criteria.

```python
import requests, pandas as pd

BASE = "https://www.encodeproject.org"

def search_experiments(assay_title=None, target=None, biosample=None,
                       organism="Homo sapiens", status="released", limit=50):
    """
    Search ENCODE experiments with flexible filters.
    Returns: pd.DataFrame of matching experiments.
    """
    params = {
        "type": "Experiment",
        "status": status,
        "replicates.library.biosample.donor.organism.scientific_name": organism,
        "format": "json",
        "limit": limit,
    }
    if assay_title:
        params["assay_title"] = assay_title
    if target:
        params["target.label"] = target
    if biosample:
        params["biosample_summary"] = biosample

    r = requests.get(f"{BASE}/search/", params=params, timeout=30)
    r.raise_for_status()
    data = r.json()
    total = data.get("total", 0)
    print(f"Total matching experiments: {total} (showing {min(limit, total)})")

    records = []
    for exp in data.get("@graph", []):
        records.append({
            "accession": exp.get("accession"),
            "assay": exp.get("assay_title"),
            "biosample": exp.get("biosample_summary"),
            "target": exp.get("target", {}).get("label", ""),
            "lab": exp.get("lab", {}).get("title", ""),
            "date_released": exp.get("date_released", ""),
        })
    df = pd.DataFrame(records)
    print(df.to_string(index=False))
    return df

# CTCF ChIP-seq in HCT116 colon cancer cells
df = search_experiments(assay_title="TF ChIP-seq", target="CTCF", biosample="HCT116")
```

```python
# ATAC-seq experiments in multiple cell types
df_atac = search_experiments(assay_title="ATAC-seq", limit=20)
print(f"\nUnique cell types: {df_atac['biosample'].nunique()}")
```

### Query 2: File Download — Get Metadata and Download URLs for BED/bigWig Files

Retrieve file metadata for a specific experiment and obtain download URLs.

```python
import requests, pandas as pd

BASE = "https://www.encodeproject.org"

def get_experiment_files(accession, file_format="bed", output_type="peaks",
                         assembly="GRCh38"):
    """
    Get file download URLs for a specific ENCODE experiment.
    accession: experiment accession, e.g. 'ENCSR000AKC'
    file_format: 'bed', 'bigWig', 'fastq', 'bam'
    output_type: 'peaks', 'signal', 'alignments', 'reads'
    Returns: pd.DataFrame of matching files with download URLs.
    """
    params = {
        "type": "File",
        "dataset": f"/experiments/{accession}/",
        "file_format": file_format,
        "output_type": output_type,
        "assembly": assembly,
        "status": "released",
        "format": "json",
        "limit": 50,
    }
    r = requests.get(f"{BASE}/search/", params=params, timeout=30)
    r.raise_for_status()
    data = r.json()
    files = data.get("@graph", [])
    print(f"Found {len(files)} {file_format} files ({output_type}) for {accession}")

    records = []
    for f in files:
        records.append({
            "file_accession": f.get("accession"),
            "file_format": f.get("file_format"),
            "output_type": f.get("output_type"),
            "assembly": f.get("assembly"),
            "file_size_mb": round(f.get("file_size", 0) / 1e6, 2),
            "download_url": BASE + f.get("href", ""),
            "biological_replicate": str(f.get("biological_replicates", [])),
        })
    df = pd.DataFrame(records)
    print(df[["file_accession", "output_type", "assembly", "file_size_mb"]].to_string(index=False))
    return df

# Get peak BED files for a CTCF ChIP-seq experiment
df_files = get_experiment_files("ENCSR000AKC", file_format="bed", output_type="peaks")
```

```python
import urllib.request

def download_encode_file(download_url, output_path):
    """Download an ENCODE file from its href URL."""
    print(f"Downloading {download_url} → {output_path}")
    urllib.request.urlretrieve(download_url, output_path)
    import os
    size_mb = os.path.getsize(output_path) / 1e6
    print(f"Downloaded {size_mb:.1f} MB → {output_path}")

# Download the first peak file
if len(df_files) > 0:
    url = df_files.iloc[0]["download_url"]
    download_encode_file(url, "CTCF_peaks.bed.gz")
```

### Query 3: cCRE Region Query — ENCODE SCREEN Candidate cis-Regulatory Elements

Query ENCODE SCREEN for candidate cis-Regulatory Elements in a genomic region using the SCREEN API.

```python
import requests, pandas as pd

SCREEN_BASE = "https://api.encodeproject.org/screen"

def search_ccres_by_region(chrom, start, end, assembly="GRCh38", limit=500):
    """
    Find candidate cis-Regulatory Elements (cCREs) in a genomic region.
    cCRE groups: PLS (promoter-like), pELS (proximal enhancer-like),
                 dELS (distal enhancer-like), DNase-H3K4me3, CTCF-only.
    Returns: pd.DataFrame of cCREs with scores.
    """
    payload = {
        "assembly": assembly,
        "coord_chrom": chrom,
        "coord_start": start,
        "coord_end": end,
        "limit": limit,
    }
    r = requests.post(f"{SCREEN_BASE}/search/", json=payload, timeout=30)
    r.raise_for_status()
    data = r.json()
    ccres = data.get("results", data.get("cCREs", []))
    print(f"Found {len(ccres)} cCREs in {chrom}:{start}-{end}")

    records = []
    for c in ccres:
        records.append({
            "accession": c.get("accession"),
            "chrom": c.get("chrom"),
            "start": c.get("start"),
            "end": c.get("end"),
            "group": c.get("group"),
            "dnase_zscore": round(c.get("dnase_zscore", 0), 2),
            "h3k4me3_zscore": round(c.get("h3k4me3_zscore", 0), 2),
            "h3k27ac_zscore": round(c.get("h3k27ac_zscore", 0), 2),
            "ctcf_zscore": round(c.get("ctcf_zscore", 0), 2),
        })
    df = pd.DataFrame(records)
    if len(df):
        print(df["group"].value_counts().to_string())
    return df

# cCREs in the TP53 locus (GRCh38)
df_ccres = search_ccres_by_region("chr17", 7_661_779, 7_887_538)
print(f"\nTotal cCREs: {len(df_ccres)}")
print(df_ccres.sort_values("h3k27ac_zscore", ascending=False).head(5).to_string(index=False))
```

### Query 4: Gene cCRE Lookup — Find cCREs Near a Gene

Retrieve cCREs in the vicinity of a specific gene using SCREEN's gene-centric endpoint.

```python
import requests, pandas as pd

SCREEN_BASE = "https://api.encodeproject.org/screen"
ENCODE_BASE = "https://www.encodeproject.org"

def get_gene_ccres(gene_symbol, assembly="GRCh38", window_kb=50):
    """
    Get cCREs near a gene using ENCODE SCREEN gene search.
    Returns: pd.DataFrame of nearby cCREs.
    """
    # Step 1: resolve gene to genomic coordinates via ENCODE gene search
    r = requests.get(
        f"{ENCODE_BASE}/search/",
        params={"type": "Gene", "symbol": gene_symbol, "assembly": assembly,
                "format": "json", "limit": 1},
        timeout=30
    )
    r.raise_for_status()
    genes = r.json().get("@graph", [])
    if not genes:
        print(f"Gene {gene_symbol} not found in ENCODE")
        return pd.DataFrame()
    gene = genes[0]
    chrom = gene.get("locations", [{}])[0].get("chromosome", "")
    start = gene.get("locations", [{}])[0].get("start", 0)
    end = gene.get("locations", [{}])[0].get("end", 0)
    print(f"{gene_symbol}: {chrom}:{start}-{end}")

    # Step 2: search cCREs in expanded window
    window = window_kb * 1000
    df = search_ccres_by_region(chrom, max(0, start - window), end + window, assembly=assembly)
    df["distance_to_gene"] = df.apply(
        lambda row: max(0, max(start - row["end"], row["start"] - end)), axis=1
    )
    return df.sort_values("distance_to_gene")

df_brca1_ccres = get_gene_ccres("BRCA1", window_kb=100)
print(f"\ncCREs near BRCA1: {len(df_brca1_ccres)}")
print(df_brca1_ccres[["accession", "group", "start", "end", "h3k27ac_zscore"]].head(10).to_string(index=False))
```

### Query 5: Biosample Browser — List Available Cell Types and Tissues

Enumerate biosample terms (cell lines, primary tissues, developmental stages) available in ENCODE.

```python
import requests, pandas as pd

BASE = "https://www.encodeproject.org"

def list_biosamples(organism="Homo sapiens", biosample_type=None, limit=200):
    """
    List biosamples available in ENCODE.
    biosample_type: 'cell line', 'primary cell', 'tissue', 'in vitro differentiated cells'
    Returns: pd.DataFrame of biosample terms with experiment counts.
    """
    params = {
        "type": "Biosample",
        "donor.organism.scientific_name": organism,
        "format": "json",
        "limit": limit,
    }
    if biosample_type:
        params["biosample_ontology.classification"] = biosample_type

    r = requests.get(f"{BASE}/search/", params=params, timeout=30)
    r.raise_for_status()
    data = r.json()
    biosamples = data.get("@graph", [])
    print(f"Found {data.get('total', 0)} biosamples (showing {len(biosamples)})")

    records = []
    for bs in biosamples:
        records.append({
            "biosample_name": bs.get("biosample_ontology", {}).get("term_name", bs.get("accession")),
            "classification": bs.get("biosample_ontology", {}).get("classification"),
            "tissue": bs.get("biosample_ontology", {}).get("organ_slims", [""])[0] if bs.get("biosample_ontology", {}).get("organ_slims") else "",
            "accession": bs.get("accession"),
        })
    df = pd.DataFrame(records).drop_duplicates("biosample_name").reset_index(drop=True)
    print(df["classification"].value_counts().to_string())
    return df

df_bs = list_biosamples(organism="Homo sapiens", biosample_type="cell line")
print(f"\nUnique human cell lines: {len(df_bs)}")
print(df_bs.head(10).to_string(index=False))
```

### Query 6: Target/TF Query — All ChIP-seq Experiments for a Transcription Factor

Retrieve all released ChIP-seq experiments for a given TF across all available cell types.

```python
import requests, pandas as pd

BASE = "https://www.encodeproject.org"

def get_tf_experiments(tf_name, assay="TF ChIP-seq", assembly="GRCh38", limit=200):
    """
    Find all ENCODE experiments for a given transcription factor.
    Returns: pd.DataFrame of experiments sorted by biosample.
    """
    params = {
        "type": "Experiment",
        "assay_title": assay,
        "target.label": tf_name,
        "files.assembly": assembly,
        "status": "released",
        "format": "json",
        "limit": limit,
    }
    r = requests.get(f"{BASE}/search/", params=params, timeout=30)
    r.raise_for_status()
    data = r.json()
    total = data.get("total", 0)
    print(f"{tf_name} {assay}: {total} total experiments (assembly {assembly})")

    records = []
    for exp in data.get("@graph", []):
        records.append({
            "accession": exp.get("accession"),
            "biosample": exp.get("biosample_summary"),
            "lab": exp.get("lab", {}).get("title", ""),
            "date_released": exp.get("date_released", ""),
        })
    df = pd.DataFrame(records).sort_values("biosample")
    print(f"Showing {len(df)} experiments across {df['biosample'].nunique()} cell types/tissues")
    print(df.head(10).to_string(index=False))
    return df

df_tp53 = get_tf_experiments("TP53", assay="TF ChIP-seq")
```

### Query 7: Peak Set Retrieval — Get Optimal Peak Set for an Experiment

Retrieve the optimal replicated peak set (IDR-filtered or pooled) from an experiment.

```python
import requests, pandas as pd

BASE = "https://www.encodeproject.org"

def get_optimal_peaks(accession, assembly="GRCh38"):
    """
    Retrieve the optimal peak file (IDR-filtered or pooled) from a ChIP-seq experiment.
    Returns: dict with file accession, download URL, and file metadata.
    """
    r = requests.get(f"{BASE}/experiments/{accession}/?format=json", timeout=30)
    r.raise_for_status()
    exp = r.json()

    # Preferred output types in order of preference
    preferred = ["IDR thresholded peaks", "optimal IDR thresholded peaks",
                 "peaks", "replicated peaks"]

    matching = []
    for f in exp.get("files", []):
        if (f.get("file_format") == "bed"
                and f.get("assembly") == assembly
                and f.get("status") == "released"
                and f.get("output_type") in preferred):
            matching.append({
                "file_accession": f.get("accession"),
                "output_type": f.get("output_type"),
                "file_size_mb": round(f.get("file_size", 0) / 1e6, 2),
                "download_url": BASE + f.get("href", ""),
                "biological_replicates": f.get("biological_replicates"),
            })

    if not matching:
        print(f"No peak BED files found for {accession} ({assembly})")
        return None

    # Pick the highest-preference output type
    for pref in preferred:
        for f in matching:
            if f["output_type"] == pref:
                print(f"Selected: {f['file_accession']}  ({f['output_type']}, {f['file_size_mb']} MB)")
                print(f"URL: {f['download_url']}")
                return f

    best = matching[0]
    print(f"Fallback: {best['file_accession']}  ({best['output_type']})")
    return best

peak_file = get_optimal_peaks("ENCSR000AKC", assembly="GRCh38")
```

## Key Concepts

### ENCODE Data Tiers and File Hierarchy

Each ENCODE experiment has multiple associated files in a hierarchy:

```
Experiment (e.g., ENCSR000AKC: CTCF ChIP-seq in K562)
├── Raw data: FASTQ files (reads, per replicate)
├── Alignments: BAM files (per replicate, GRCh38)
├── Signal tracks: bigWig (fold-change over control, p-value signal)
└── Peak calls (BED):
    ├── Replicate 1 peaks (narrow/broad)
    ├── Replicate 2 peaks
    ├── Pooled peaks
    ├── IDR thresholded peaks  ← optimal for most analyses
    └── Optimal IDR thresholded peaks  ← preferred default
```

For most downstream analyses, use **IDR thresholded peaks** or **optimal IDR thresholded peaks** — these are the reproducibility-filtered, high-confidence peak sets.

### cCRE Classification System

ENCODE SCREEN classifies cCREs into five functional groups based on epigenomic signal z-scores:

| Group | Full Name | Signals | Interpretation |
|-------|-----------|---------|----------------|
| PLS | Promoter-Like Sequence | High DNase + High H3K4me3 + High H3K27ac | Active promoter region |
| pELS | Proximal Enhancer-Like Sequence | High DNase + High H3K27ac, ≤2 kb from TSS | Proximal enhancer |
| dELS | Distal Enhancer-Like Sequence | High DNase + High H3K27ac, >2 kb from TSS | Distal enhancer |
| DNase-H3K4me3 | — | High DNase + High H3K4me3, low H3K27ac | Unusual promoter signature |
| CTCF-only | — | High CTCF, low H3K27ac | Insulator/boundary element |

Z-scores >1.64 (p < 0.05) are considered significant in each signal category.

## Common Workflows

### Workflow 1: Download TF Peak Files for a Cell Type

**Goal**: Retrieve CTCF ChIP-seq peak BED files for a specific cell line and load them into a DataFrame for variant annotation.

```python
import requests, pandas as pd, time, gzip, io

BASE = "https://www.encodeproject.org"

def download_tf_peaks_for_cell_type(tf_name, biosample, assembly="GRCh38"):
    """Find and download IDR peak BED for a TF in a specific cell type."""
    # Step 1: find experiments
    params = {
        "type": "Experiment",
        "assay_title": "TF ChIP-seq",
        "target.label": tf_name,
        "biosample_summary": biosample,
        "files.assembly": assembly,
        "status": "released",
        "format": "json",
        "limit": 5,
    }
    r = requests.get(f"{BASE}/search/", params=params, timeout=30)
    r.raise_for_status()
    exps = r.json().get("@graph", [])
    if not exps:
        print(f"No {tf_name} experiments found for {biosample}")
        return None
    accession = exps[0]["accession"]
    print(f"Using experiment {accession}")

    # Step 2: find optimal peak file
    peak = get_optimal_peaks(accession, assembly=assembly)
    if not peak:
        return None

    # Step 3: download and parse BED
    r2 = requests.get(peak["download_url"], timeout=120, stream=True)
    r2.raise_for_status()
    content = r2.content
    if peak["download_url"].endswith(".gz"):
        content = gzip.decompress(content)
    lines = content.decode("utf-8").strip().split("\n")
    rows = [l.split("\t") for l in lines if l and not l.startswith("#")]

    # Narrow peak BED6+4 columns
    cols = ["chrom", "start", "end", "name", "score", "strand",
            "signalValue", "pValue", "qValue", "peak"]
    df = pd.DataFrame(rows, columns=cols[:len(rows[0])] if rows else cols)
    df["start"] = pd.to_numeric(df["start"])
    df["end"] = pd.to_numeric(df["end"])
    print(f"Loaded {len(df):,} peaks for {tf_name} in {biosample} ({assembly})")
    print(f"Genome coverage: {(df['end'] - df['start']).sum() / 1e6:.1f} Mb")
    return df

df_peaks = download_tf_peaks_for_cell_type("CTCF", "K562")
if df_peaks is not None:
    df_peaks.to_csv("CTCF_K562_peaks.bed", sep="\t", index=False, header=False)
    print("Saved CTCF_K562_peaks.bed")
```

### Workflow 2: cCRE Category Bar Chart for a Genomic Region

**Goal**: Query SCREEN for cCREs in a disease locus and visualize the distribution of regulatory element types.

```python
import requests, pandas as pd
import matplotlib.pyplot as plt

SCREEN_BASE = "https://api.encodeproject.org/screen"

def ccre_category_chart(chrom, start, end, assembly="GRCh38", label="Region"):
    """Query SCREEN cCREs and plot category distribution."""
    payload = {"assembly": assembly, "coord_chrom": chrom,
               "coord_start": start, "coord_end": end, "limit": 1000}
    r = requests.post(f"{SCREEN_BASE}/search/", json=payload, timeout=30)
    r.raise_for_status()
    data = r.json()
    ccres = data.get("results", data.get("cCREs", []))

    if not ccres:
        print(f"No cCREs found in {chrom}:{start}-{end}")
        return pd.DataFrame()

    df = pd.DataFrame(ccres)
    print(f"cCREs in {chrom}:{start}-{end}: {len(df)}")

    # Count by group
    group_counts = df["group"].value_counts()
    group_colors = {
        "PLS": "#d62728",        # red — promoters
        "pELS": "#ff7f0e",       # orange — proximal enhancers
        "dELS": "#1f77b4",       # blue — distal enhancers
        "DNase-H3K4me3": "#9467bd",  # purple
        "CTCF-only": "#2ca02c",  # green — insulators
    }
    colors = [group_colors.get(g, "#aec7e8") for g in group_counts.index]

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    # Bar chart of category counts
    axes[0].bar(group_counts.index, group_counts.values, color=colors, edgecolor="black")
    axes[0].set_xlabel("cCRE Category")
    axes[0].set_ylabel("Count")
    axes[0].set_title(f"cCRE Categories — {label}\n({chrom}:{start}-{end})")
    for i, (cat, cnt) in enumerate(group_counts.items()):
        axes[0].text(i, cnt + 0.3, str(cnt), ha="center", va="bottom", fontsize=9)

    # H3K27ac z-score distribution by category
    if "h3k27ac_zscore" in df.columns:
        groups_present = [g for g in ["PLS", "pELS", "dELS"] if g in df["group"].values]
        data_to_plot = [df.loc[df["group"] == g, "h3k27ac_zscore"].dropna().tolist()
                        for g in groups_present]
        axes[1].boxplot(data_to_plot, labels=groups_present,
                        patch_artist=True,
                        boxprops=dict(facecolor="lightsteelblue"))
        axes[1].set_xlabel("cCRE Group")
        axes[1].set_ylabel("H3K27ac Z-score")
        axes[1].set_title("H3K27ac Signal Strength by cCRE Group")
        axes[1].axhline(1.64, color="red", linestyle="--", label="p<0.05 threshold")
        axes[1].legend()

    plt.tight_layout()
    plt.savefig("ccre_category_chart.png", dpi=150, bbox_inches="tight")
    print(f"Saved ccre_category_chart.png")
    print(group_counts.to_string())
    return df

# BRCA1/BRCA2 locus — chr17 region
df_ccres = ccre_category_chart("chr17", 43_044_295, 43_170_000, label="BRCA1 locus")
```

### Workflow 3: Build a TF Peak Atlas Across Multiple Cell Types

**Goal**: Systematically collect peak BED accessions for one TF across all available cell types for a comparative regulatory analysis.

```python
import requests, pandas as pd, time

BASE = "https://www.encodeproject.org"

def build_tf_peak_atlas(tf_name, assembly="GRCh38", max_experiments=50):
    """
    Collect peak file metadata for a TF across all available cell types.
    Returns: pd.DataFrame with one row per experiment (download URL included).
    """
    params = {
        "type": "Experiment",
        "assay_title": "TF ChIP-seq",
        "target.label": tf_name,
        "files.assembly": assembly,
        "status": "released",
        "format": "json",
        "limit": max_experiments,
    }
    r = requests.get(f"{BASE}/search/", params=params, timeout=30)
    r.raise_for_status()
    exps = r.json().get("@graph", [])
    print(f"{tf_name}: {len(exps)} experiments across {assembly}")

    atlas_records = []
    for exp in exps:
        acc = exp.get("accession")
        peak = get_optimal_peaks(acc, assembly=assembly)
        if peak:
            atlas_records.append({
                "experiment": acc,
                "biosample": exp.get("biosample_summary", ""),
                "lab": exp.get("lab", {}).get("title", ""),
                "file_accession": peak["file_accession"],
                "output_type": peak["output_type"],
                "file_size_mb": peak["file_size_mb"],
                "download_url": peak["download_url"],
            })
        time.sleep(0.3)

    df = pd.DataFrame(atlas_records)
    print(f"Peak files found: {len(df)} / {len(exps)} experiments")
    df.to_csv(f"{tf_name}_peak_atlas_{assembly}.csv", index=False)
    print(f"Saved {tf_name}_peak_atlas_{assembly}.csv")
    return df

# Collect CTCF peak atlas
df_atlas = build_tf_peak_atlas("CTCF", max_experiments=20)
print(f"\nCell types covered: {df_atlas['biosample'].nunique()}")
```

## Key Parameters

| Parameter | Endpoint / Function | Default | Range / Options | Effect |
|-----------|---------------------|---------|-----------------|--------|
| `type` | All search endpoints | required | `"Experiment"`, `"File"`, `"Gene"`, `"Biosample"` | Result type to search |
| `assay_title` | Experiment search | — | `"TF ChIP-seq"`, `"ATAC-seq"`, `"DNase-seq"`, `"Histone ChIP-seq"`, `"RNA-seq"` | Filter by assay type |
| `target.label` | Experiment search | — | TF name string, e.g. `"CTCF"`, `"TP53"` | Filter by target protein |
| `biosample_summary` | Experiment search | — | Cell type string, e.g. `"K562"`, `"HeLa-S3"` | Filter by biosample |
| `files.assembly` | Experiment search | — | `"GRCh38"`, `"GRCh37"`, `"mm10"` | Filter by genome assembly |
| `output_type` | File search | — | `"peaks"`, `"IDR thresholded peaks"`, `"signal"`, `"alignments"` | Filter by file output type |
| `status` | All search endpoints | — | `"released"`, `"in progress"`, `"archived"` | Filter by release status |
| `limit` | All search endpoints | `25` | `1`–`500` | Max results per page |
| `coord_chrom` | SCREEN cCRE search | required | chromosome string, e.g. `"chr17"` | Chromosome for region query |
| `coord_start` | SCREEN cCRE search | required | integer | Region start coordinate |
| `coord_end` | SCREEN cCRE search | required | integer | Region end coordinate |

## Best Practices

1. **Use IDR thresholded peaks for reproducible analyses**: Raw replicate peaks contain many false positives. Always prefer `"output_type": "IDR thresholded peaks"` or `"optimal IDR thresholded peaks"` for any variant annotation or motif analysis.

2. **Filter by `status=released` and specify `assembly`**: ENCODE stores data for multiple genome builds. Always include `files.assembly=GRCh38` (or your target assembly) to avoid mixing coordinate systems from archived experiments.

3. **Add `time.sleep(0.5)` in loops over experiments**: The ENCODE Portal does not publish a hard rate limit, but aggressive sequential requests will trigger connection resets. Polite delays prevent this in atlas-building workflows.

4. **Prefer the SCREEN API for cCRE queries, not the Portal search**: The ENCODE Portal search can find cCRE-related files, but the dedicated SCREEN API (`api.encodeproject.org/screen`) is purpose-built for region-based cCRE lookup and returns structured z-score data.

5. **Check `biosample_summary` vs `biosample_ontology.term_name`**: The `biosample_summary` field (used in search) sometimes differs from the official ontology term name. If a biosample search returns zero results, try browsing ENCODE to find the exact summary string used.

## Common Recipes

### Recipe: Find All ENCODE Assay Types Available

When to use: Explore what assay types are available before planning a targeted search.

```python
import requests

BASE = "https://www.encodeproject.org"

r = requests.get(
    f"{BASE}/search/",
    params={"type": "Experiment", "status": "released", "format": "json",
            "limit": 0, "field": "assay_title"},
    timeout=30
)
r.raise_for_status()
# Facets contain aggregated counts per assay type
for facet in r.json().get("facets", []):
    if facet.get("field") == "assay_title":
        for term in sorted(facet.get("terms", []), key=lambda x: -x["count"])[:20]:
            print(f"  {term['doc_count']:6d}  {term['key']}")
```

### Recipe: Get Experiment Metadata by Accession

When to use: Retrieve full details for a known ENCODE accession (e.g., from a published paper).

```python
import requests, json

BASE = "https://www.encodeproject.org"

def get_experiment_metadata(accession):
    r = requests.get(f"{BASE}/experiments/{accession}/?format=json", timeout=30)
    r.raise_for_status()
    exp = r.json()
    print(f"Accession  : {exp['accession']}")
    print(f"Assay      : {exp.get('assay_title')}")
    print(f"Biosample  : {exp.get('biosample_summary')}")
    print(f"Target     : {exp.get('target', {}).get('label', 'N/A')}")
    print(f"Lab        : {exp.get('lab', {}).get('title')}")
    print(f"Files      : {len(exp.get('files', []))}")
    print(f"Released   : {exp.get('date_released')}")
    return exp

exp = get_experiment_metadata("ENCSR000AKC")
```

### Recipe: List bigWig Signal Files for Visualization

When to use: Download signal bigWig tracks to load into IGV or UCSC Genome Browser.

```python
import requests, pandas as pd

BASE = "https://www.encodeproject.org"

def get_signal_bigwigs(accession, assembly="GRCh38"):
    """Get fold-change and p-value signal bigWig files for an experiment."""
    params = {
        "type": "File",
        "dataset": f"/experiments/{accession}/",
        "file_format": "bigWig",
        "output_type": "fold change over control",
        "assembly": assembly,
        "status": "released",
        "format": "json",
        "limit": 10,
    }
    r = requests.get(f"{BASE}/search/", params=params, timeout=30)
    r.raise_for_status()
    files = r.json().get("@graph", [])
    print(f"Found {len(files)} bigWig signal files for {accession}")
    for f in files:
        print(f"  {f['accession']}  {f['output_type']}  {f.get('biological_replicates')}  "
              f"{round(f.get('file_size', 0)/1e6, 1)} MB")
        print(f"  URL: {BASE}{f['href']}")
    return files

bigwigs = get_signal_bigwigs("ENCSR000AKC")
```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `HTTP 404` on experiment endpoint | Accession does not exist or was revoked | Verify accession on https://www.encodeproject.org; check `status` field in search results |
| Empty `@graph` in search results | Overly restrictive filters or no matching data | Relax one filter at a time; check `total` field to see if data exists before pagination |
| `HTTP 503` or connection timeout | Server overload from rapid sequential requests | Add `time.sleep(0.5)` between requests; retry with exponential backoff |
| cCRE search returns `[]` | SCREEN API endpoint path changed or region on non-canonical chromosome | Verify API URL; use canonical chromosomes (chr1–22, chrX, chrY) only |
| bigWig/BED files not found | Assembly mismatch (GRCh37 vs GRCh38) | Always include `files.assembly` in queries; verify the experiment has files in your target assembly |
| `target.label` filter returns no results | Exact label mismatch (case-sensitive) | Browse ENCODE to find the exact string (e.g., `"eGFP-TP53"` vs `"TP53"`) |
| File download fails mid-transfer | Large file + network timeout | Use `stream=True` in requests with chunked writing; increase `timeout` to 300 |

## Related Skills

- `regulomedb-database` — Pre-computed regulatory scores for variants integrating ENCODE ChIP-seq, DNase-seq, eQTL, and motif data
- `gwas-database` — NHGRI-EBI GWAS Catalog for published SNP-trait associations; combine with ENCODE peaks for functional annotation of GWAS hits
- `macs3-peak-calling` — Call peaks from your own ChIP-seq or ATAC-seq BAM files; use ENCODE peaks as reference comparison sets
- `deeptools-ngs-analysis` — Generate bigWig coverage tracks, correlation heatmaps, and profile plots from your own aligned BAM files

## References

- [ENCODE Portal REST API Documentation](https://www.encodeproject.org/help/rest-api/) — Full API reference with query examples
- [ENCODE SCREEN Browser](https://screen.encodeproject.org/) — Interactive cCRE browser and documentation
- ENCODE Project Consortium. "An integrated encyclopedia of DNA elements in the human genome." *Nature* 489: 57–74 (2012). https://doi.org/10.1038/nature11247
- ENCODE Project Consortium et al. "Perspectives on ENCODE." *Nature* 583: 693–698 (2020). https://doi.org/10.1038/s41586-020-2449-8
- Moore JE et al. "Expanded encyclopaedias of DNA elements in the human and mouse genomes." *Nature* 583: 699–710 (2020). https://doi.org/10.1038/s41586-020-2493-4
