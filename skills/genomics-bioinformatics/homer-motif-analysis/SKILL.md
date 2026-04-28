---
name: "homer-motif-analysis"
description: "De novo and known TF motif enrichment in ChIP-seq/ATAC-seq peaks via HOMER. findMotifsGenome.pl finds over-represented patterns vs background; annotatePeaks.pl assigns context (TSS distance, gene, repeat). Use after MACS3 to identify enriched TFs, annotate peaks with nearest genes, and validate ChIP-seq via the target motif."
license: "GPL-3.0"
---

# HOMER — Motif Analysis and Peak Annotation

## Overview

HOMER (Hypergeometric Optimization of Motif EnRichment) is a suite of Perl/C++ tools for analyzing genomic regulatory elements. Its two primary commands are `findMotifsGenome.pl`, which performs de novo motif discovery and known motif enrichment against JASPAR/HOMER databases, and `annotatePeaks.pl`, which maps each peak to the nearest gene, distance to TSS, and genomic feature class (promoter, intron, intergenic, repeat). HOMER takes BED-format peak files from MACS3 or similar peak callers and a reference genome assembly as input, and outputs HTML/text reports ranking enriched motifs by p-value and fold enrichment over a matched background.

## When to Use

- Identifying which transcription factors are bound in a ChIP-seq peak set by enriching their known motifs from JASPAR or the HOMER motif library
- Discovering novel sequence motifs de novo in open chromatin regions from ATAC-seq without prior knowledge of the binding TF
- Comparing motif landscapes between two conditions (e.g., treated vs. untreated peak sets) by running HOMER with one set as target and the other as background
- Annotating genomic peaks with nearest genes and distance to TSS for downstream functional analysis or integration with DESeq2 results
- Validating ChIP-seq experiment quality: a successful pull-down should show the target TF's canonical motif as the top hit
- Use `macs3-peak-calling` first to generate the peak BED files that serve as input to HOMER
- Use `jaspar-database` to cross-reference HOMER-discovered motifs with JASPAR IDs and additional TF metadata
- Use `MEME-CHIP` (web or local) when you need a more probabilistic ZOOPS/TCM model or the MEME Suite ecosystem
- Use `AME` (part of MEME Suite) as a faster alternative for known motif scanning without de novo discovery

## Prerequisites

- **Software**: HOMER (Perl + compiled binaries), conda or manual install
- **Genomes**: must download genome sequence via `installGenome.pl` after HOMER install
- **Input**: BED file of peaks (at minimum: chr, start, end columns); ideally summit-centered peaks from MACS3
- **Python packages** (for parsing/visualization): `pandas`, `matplotlib`, `seaborn`

> **Check before installing**: The tool may already be available in the current environment (e.g., inside a `pixi` / `conda` env). Run `command -v findMotifsGenome.pl` first and skip the install commands below if it returns a path. When running inside a pixi project, invoke the tool via `pixi run findMotifsGenome.pl` rather than bare `findMotifsGenome.pl`.

```bash
# Install HOMER via conda (recommended — handles Perl dependencies)
conda install -c bioconda homer

# Verify installation
findMotifsGenome.pl 2>&1 | head -3
# Usage: findMotifsGenome.pl <peak/BED file> <genome> <output directory> [options]

annotatePeaks.pl 2>&1 | head -3
# Usage: annotatePeaks.pl <peak/BED file> <genome> [options]

# Install reference genomes (downloads 2-way masker + sequence; ~3–10 GB each)
installGenome.pl hg38
installGenome.pl mm10

# Install Python parsing dependencies
pip install pandas matplotlib seaborn
```

## Quick Start

```bash
# Run de novo + known motif enrichment on TF ChIP-seq peaks (hg38, 200 bp window)
findMotifsGenome.pl peaks/tf_chip_summits.bed hg38 motif_output/ \
    -size 200 -mask -p 4

# Annotate peaks with nearest genes and genomic features
annotatePeaks.pl peaks/tf_chip_peaks.narrowPeak hg38 > annotated_peaks.txt

echo "Top known motif:"
head -2 motif_output/knownResults.txt | tail -1 | cut -f1-4

echo "Annotated peaks: $(wc -l < annotated_peaks.txt) lines"
```

## Workflow

### Step 1: Installation and Genome Setup

Install HOMER and download the reference genome sequence required for motif analysis.

```bash
# Activate conda environment (or use existing env)
conda create -n homer_env -c bioconda homer python=3.10 -y
conda activate homer_env

# List available genomes
installGenome.pl list

# Install human (hg38) and mouse (mm10) genomes
# Downloads masked genome sequence and annotation files
installGenome.pl hg38
# Output: Installing hg38... Done. (3-5 min, ~3 GB)

installGenome.pl mm10
# Output: Installing mm10... Done. (3-5 min, ~2.5 GB)

# Verify genome is installed
ls ~/.homer/data/genomes/hg38/
# genome.fa  chrom.sizes  ...

# Check HOMER motif database
ls ~/.homer/data/knownTFs/
# vertebrates.motifs  jaspar.motifs  ...
```

### Step 2: Prepare Input Peak File

Prepare a summit-centered BED file from MACS3 output for optimal motif resolution.

```bash
# Option A: Use MACS3 summit file directly (already 1 bp summit positions)
# Expand summits to ±100 bp (200 bp total) centered on summit
awk 'BEGIN{OFS="\t"} {
    start = ($2 - 100 < 0) ? 0 : $2 - 100;
    print $1, start, $2 + 100, $4, $5
}' peaks/tf_chip_summits.bed > peaks/tf_chip_200bp.bed

echo "Summit-centered peaks: $(wc -l < peaks/tf_chip_200bp.bed)"
# Summit-centered peaks: 12453

# Option B: Use narrowPeak file directly (HOMER accepts multi-column BED)
# HOMER uses columns 1-3 (chr, start, end) and centers internally with -size
cp peaks/tf_chip_peaks.narrowPeak peaks/input_peaks.bed

# Option C: Prepare a custom background region file (matched GC content)
# HOMER auto-generates background if not provided, but explicit background
# is recommended when comparing two peak sets
# Use the control peak set or random genomic regions as background:
bedtools shuffle -i peaks/tf_chip_peaks.narrowPeak \
    -g ~/.homer/data/genomes/hg38/chrom.sizes \
    -excl peaks/tf_chip_peaks.narrowPeak > peaks/background_regions.bed

echo "Background regions: $(wc -l < peaks/background_regions.bed)"
# Background regions: 12453
```

### Step 3: De Novo Motif Discovery

Run `findMotifsGenome.pl` for de novo motif discovery and known motif enrichment simultaneously.

```bash
mkdir -p motif_output/

# Full run: de novo + known motif enrichment
# -size 200: use 200 bp window centered on peak midpoint
# -mask: mask repetitive elements (recommended for clean motifs)
# -p 4: use 4 CPU threads
# -S 25: find top 25 de novo motifs (default)
findMotifsGenome.pl peaks/tf_chip_200bp.bed hg38 motif_output/ \
    -size 200 \
    -mask \
    -p 4 \
    -S 25

# Check progress output:
# Reading genome sizes for hg38 ...
# Scanning for motifs...
# Optimizing 25 motifs...
# Done! Output in motif_output/

echo "Known results: $(wc -l < motif_output/knownResults.txt) motifs"
echo "De novo motifs: $(ls motif_output/homerResults/*.motif 2>/dev/null | wc -l) motifs"
# Known results: 392 motifs
# De novo motifs: 25 motifs

# For mouse peaks (mm10)
# findMotifsGenome.pl peaks/atac_peaks.bed mm10 motif_output_mm10/ \
#     -size 200 -mask -p 4
```

### Step 4: Known Motif Enrichment Only

Scan peaks for occurrences of a specific known motif or skip de novo discovery for speed.

```bash
# Skip de novo discovery (faster when you only need known motifs)
findMotifsGenome.pl peaks/tf_chip_200bp.bed hg38 motif_output_known/ \
    -size 200 \
    -mask \
    -p 4 \
    -nomotif

echo "Known motif results: $(wc -l < motif_output_known/knownResults.txt)"
# Known motif results: 392

# Find occurrences of a specific motif across peaks (outputs peak-level annotation)
# Extract the motif matrix file for the TF of interest from homerResults/
findMotifsGenome.pl peaks/tf_chip_200bp.bed hg38 motif_scan_out/ \
    -size 200 \
    -mask \
    -find motif_output/homerResults/motif1.motif \
    > peaks_with_motif1.txt

echo "Peaks containing motif1: $(wc -l < peaks_with_motif1.txt)"
# Peaks containing motif1: 8941

# Custom background: compare treated vs. control peak sets
findMotifsGenome.pl peaks/treated_peaks.bed hg38 motif_treated_vs_ctrl/ \
    -size 200 \
    -mask \
    -p 4 \
    -bg peaks/control_peaks.bed
```

### Step 5: Peak Annotation

Use `annotatePeaks.pl` to assign each peak to a genomic feature and nearest gene.

```bash
# Annotate peaks with nearest gene and TSS distance
# Outputs a tab-delimited file with genomic context for each peak
annotatePeaks.pl peaks/tf_chip_peaks.narrowPeak hg38 \
    > annotated_peaks.txt

echo "Annotated peaks: $(($(wc -l < annotated_peaks.txt) - 1)) peaks"
# Annotated peaks: 12453 peaks

# Preview column headers and first peak
head -2 annotated_peaks.txt | cut -f1-10

# Annotate ATAC-seq peaks (same command, different input)
annotatePeaks.pl peaks/atac_sample_peaks.narrowPeak hg38 \
    > annotated_atac.txt

# Generate TSS-distance histogram (for tag density plots)
# annotatePeaks.pl can compute read density around peaks with -d flag
# annotatePeaks.pl tss hg38 -size 4000 -hist 10 \
#     -d chip_tagdir/ > tss_histogram.txt
```

### Step 6: Parse HOMER Results with Python

Read `knownResults.txt` and de novo motif files into pandas for downstream analysis.

```python
import pandas as pd
import subprocess
import io

# --- Parse known motif enrichment results ---
# knownResults.txt columns:
# Motif Name | Consensus | P-value | Log P-value | q-value | # Target Seqs w/ motif | % Target | # Bg Seqs w/ motif | % Bg
known_cols = [
    "motif_name", "consensus", "pvalue", "log_pvalue",
    "qvalue", "n_target_seqs", "pct_target",
    "n_bg_seqs", "pct_bg"
]
known = pd.read_csv(
    "motif_output/knownResults.txt",
    sep="\t", header=0, names=known_cols
)

# Convert string percentages to floats
known["pct_target"] = known["pct_target"].str.rstrip("%").astype(float)
known["pct_bg"] = known["pct_bg"].str.rstrip("%").astype(float)
known["fold_enrichment"] = known["pct_target"] / known["pct_bg"].replace(0, 0.001)
known["-log10_pvalue"] = -known["log_pvalue"] / 2.303  # log10 from natural log

print(f"Total known motifs tested: {len(known)}")
print(f"Significant (p < 1e-5): {(known['pvalue'].astype(float) < 1e-5).sum()}")
print("\nTop 5 enriched motifs:")
print(
    known[["motif_name", "pct_target", "pct_bg", "fold_enrichment", "-log10_pvalue"]]
    .head(5)
    .to_string(index=False)
)
# Total known motifs tested: 391
# Significant (p < 1e-5): 47
# Top 5 enriched motifs:
#  motif_name  pct_target  pct_bg  fold_enrichment  -log10_pvalue
#  CTCF(Zf)/GM12878-CTCF-ChIP-Seq...   78.21    8.32           9.40         312.4
#  ZNF143(Zf)/...                        42.11    5.10           8.26         188.7
#  ...
```

### Step 7: Parse Peak Annotations and Visualize

Read annotated peak output, summarize genomic feature distribution, and plot motif enrichments.

```python
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns

# --- Parse annotated peaks ---
# annotatePeaks.pl output header: PeakID chr start end strand score ...
# Key columns: "Annotation", "Distance to TSS", "Nearest RefSeq", "Gene Name"
annot = pd.read_csv("annotated_peaks.txt", sep="\t", header=0, low_memory=False)
annot.columns = annot.columns.str.strip()

# Simplify annotation categories
def simplify_annotation(ann):
    if pd.isna(ann):
        return "Other"
    ann = str(ann)
    if "promoter" in ann.lower():
        return "Promoter (<2 kb)"
    elif "exon" in ann.lower():
        return "Exon"
    elif "intron" in ann.lower():
        return "Intron"
    elif "tts" in ann.lower() or "downstream" in ann.lower():
        return "Downstream"
    elif "intergenic" in ann.lower():
        return "Intergenic"
    else:
        return "Other"

annot["simple_ann"] = annot["Annotation"].apply(simplify_annotation)
ann_counts = annot["simple_ann"].value_counts()

print("Peak annotation summary:")
print(ann_counts.to_string())
# Peak annotation summary:
# Intron             5832
# Intergenic         3102
# Promoter (<2 kb)   2218
# Exon                891
# Downstream          287
# Other               123

# --- Plot 1: Annotation pie chart ---
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

colors = ["#E41A1C", "#377EB8", "#4DAF4A", "#984EA3", "#FF7F00", "#A65628"]
axes[0].pie(
    ann_counts.values,
    labels=ann_counts.index,
    colors=colors[:len(ann_counts)],
    autopct="%1.1f%%",
    startangle=140,
    textprops={"fontsize": 9}
)
axes[0].set_title("Peak Genomic Annotation\n(n=12,453 peaks)", fontsize=11)

# --- Plot 2: Top known motif enrichments ---
known = pd.read_csv("motif_output/knownResults.txt", sep="\t", header=0)
known.columns = [
    "motif_name", "consensus", "pvalue", "log_pvalue",
    "qvalue", "n_target_seqs", "pct_target", "n_bg_seqs", "pct_bg"
]
known["pct_target"] = known["pct_target"].str.rstrip("%").astype(float)
known["pct_bg"] = known["pct_bg"].str.rstrip("%").astype(float)
known["-log10_p"] = (-known["log_pvalue"].astype(float)) / 2.303
known["short_name"] = known["motif_name"].str.split("/").str[0]

top_motifs = known.head(15).copy()
sns.barplot(
    data=top_motifs,
    x="-log10_p",
    y="short_name",
    palette="Blues_r",
    ax=axes[1]
)
axes[1].set_xlabel("-log10(p-value)", fontsize=10)
axes[1].set_ylabel("Motif", fontsize=10)
axes[1].set_title("Top 15 Enriched Known Motifs\n(HOMER/JASPAR database)", fontsize=11)
axes[1].axvline(x=5, color="red", linestyle="--", linewidth=0.8, label="p=1e-5")
axes[1].legend(fontsize=8)

plt.tight_layout()
plt.savefig("homer_summary.png", dpi=150, bbox_inches="tight")
plt.close()
print("Saved: homer_summary.png")
```

## Key Parameters

| Parameter | Default | Range / Options | Effect |
|-----------|---------|-----------------|--------|
| `-size` | `200` | 50–1000 | Window size (bp) centered on peak midpoint for motif search; 200 for TF ChIP-seq, 150 for ATAC-seq |
| `-mask` | off | flag | Mask repetitive elements (N-mask); strongly recommended to reduce false positives |
| `-p` | `1` | 1–64 | Number of parallel CPU threads; use 4–8 for typical datasets |
| `-S` | `25` | 1–100 | Number of de novo motifs to find; 25 is usually sufficient |
| `-nomotif` | off | flag | Skip de novo motif discovery; only perform known motif enrichment (10× faster) |
| `-bg` | auto-generated | BED file path | Custom background region file; auto-background is GC-matched if omitted |
| `-find` | — | `.motif` file path | Scan peaks for occurrences of a specific motif matrix; outputs per-peak annotation |
| `-mis` | `2` | 0–4 | Maximum mismatches allowed when matching known motifs |
| `-len` | `8,10,12` | comma-separated integers | Motif lengths to try for de novo search; adding `6` finds shorter motifs |
| `genome` | required | `hg38`, `mm10`, `hg19`, `dm6`, `ce11`, etc. | Reference genome assembly; must be installed with `installGenome.pl` |

## Common Recipes

### Recipe 1: Python subprocess Wrapper for findMotifsGenome.pl

Run HOMER from a Python script and capture completion status.

```python
import subprocess
import sys
from pathlib import Path

def run_homer_motifs(
    peaks_bed: str,
    genome: str,
    output_dir: str,
    size: int = 200,
    mask: bool = True,
    cpus: int = 4,
    n_motifs: int = 25,
    denovo: bool = True,
    bg_bed: str = None
) -> int:
    """Run findMotifsGenome.pl and return exit code."""
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    cmd = [
        "findMotifsGenome.pl", peaks_bed, genome, output_dir,
        "-size", str(size),
        "-p", str(cpus),
        "-S", str(n_motifs),
    ]
    if mask:
        cmd.append("-mask")
    if not denovo:
        cmd.append("-nomotif")
    if bg_bed:
        cmd.extend(["-bg", bg_bed])

    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"HOMER stderr:\n{result.stderr[-2000:]}", file=sys.stderr)
        return result.returncode
    print(f"Done. Output in {output_dir}/")
    return 0

# Usage
exit_code = run_homer_motifs(
    peaks_bed="peaks/tf_chip_200bp.bed",
    genome="hg38",
    output_dir="motif_output/",
    size=200, mask=True, cpus=4, n_motifs=25
)
print(f"Exit code: {exit_code}")
# Running: findMotifsGenome.pl peaks/tf_chip_200bp.bed hg38 motif_output/ -size 200 -p 4 -S 25 -mask
# Done. Output in motif_output/
# Exit code: 0
```

### Recipe 2: Batch Motif Analysis Across Multiple Peak Sets

Run HOMER on multiple ChIP-seq samples in a loop.

```bash
#!/bin/bash
# Batch motif analysis for several ChIP-seq experiments (same genome)
GENOME="hg38"
PEAK_DIR="peaks"
MOTIF_DIR="motif_results"
mkdir -p "$MOTIF_DIR"

SAMPLES=(CTCF H3K4me3 FOXA2 RUNX1)

for sample in "${SAMPLES[@]}"; do
    echo "=== Processing $sample ==="
    peak_file="${PEAK_DIR}/${sample}_summits.bed"

    if [ ! -f "$peak_file" ]; then
        echo "  Skipping $sample: $peak_file not found"
        continue
    fi

    # Center on summit ±100 bp
    awk 'BEGIN{OFS="\t"} {s=$2-100<0?0:$2-100; print $1,s,$2+100,$4,$5}' \
        "$peak_file" > "${PEAK_DIR}/${sample}_200bp.bed"

    findMotifsGenome.pl "${PEAK_DIR}/${sample}_200bp.bed" "$GENOME" \
        "${MOTIF_DIR}/${sample}/" \
        -size 200 -mask -p 4 -nomotif \
        2> "${MOTIF_DIR}/${sample}.log"

    n=$(wc -l < "${MOTIF_DIR}/${sample}/knownResults.txt")
    echo "  $sample: $n motifs tested. Top hit: $(sed -n '2p' "${MOTIF_DIR}/${sample}/knownResults.txt" | cut -f1)"
done
# === Processing CTCF ===
#   CTCF: 392 motifs tested. Top hit: CTCF(Zf)/GM12878-CTCF-ChIP-Seq(GSE32465)/Homer
# === Processing FOXA2 ===
#   FOXA2: 392 motifs tested. Top hit: Foxa2(Forkhead)/Liver-Foxa2-ChIP-Seq(GSE25694)/Homer
```

### Recipe 3: Parse De Novo Motif Matrices from homerResults/

Load de novo motif PWM matrices for downstream comparison or plotting.

```python
import os
import re
import pandas as pd

def parse_homer_motif(motif_file: str) -> dict:
    """Parse a HOMER .motif file into name, log_odds_threshold, and PWM."""
    with open(motif_file) as f:
        header = f.readline().strip()  # >motif_name\tlog_odds\tlog_p-value\t0\tnucs
        rows = []
        for line in f:
            line = line.strip()
            if line:
                rows.append([float(x) for x in line.split("\t")])
    parts = header.lstrip(">").split("\t")
    name = parts[0]
    log_odds = float(parts[1]) if len(parts) > 1 else 0.0
    log_p = float(parts[2]) if len(parts) > 2 else 0.0
    pwm = pd.DataFrame(rows, columns=["A", "C", "G", "T"])
    return {"name": name, "log_odds": log_odds, "log_p": log_p, "pwm": pwm}

# Load all de novo motifs
motif_dir = "motif_output/homerResults/"
motifs = []
for fn in sorted(os.listdir(motif_dir)):
    if fn.endswith(".motif"):
        motif = parse_homer_motif(os.path.join(motif_dir, fn))
        motifs.append(motif)
        print(f"{fn}: {motif['name']} ({len(motif['pwm'])} positions, log_p={motif['log_p']:.1f})")

print(f"\nLoaded {len(motifs)} de novo motifs")
# motif1.motif: CTCF-motif (19 positions, log_p=-8234.1)
# motif2.motif: CTCFL-motif (17 positions, log_p=-3421.7)
# ...
# Loaded 25 de novo motifs
```

### Recipe 4: Annotate Peaks and Join with Differential Expression Results

Combine peak annotations with RNA-seq DE results to find regulated genes near peaks.

```python
import pandas as pd

# Load annotated peaks
annot = pd.read_csv("annotated_peaks.txt", sep="\t", header=0, low_memory=False)
annot.columns = annot.columns.str.strip()

# Key columns from HOMER annotation
peak_genes = annot[["PeakID (cmd=annotatePeaks.pl peaks.bed hg38)",
                     "Chr", "Start", "End",
                     "Annotation", "Distance to TSS",
                     "Nearest RefSeq", "Gene Name"]].copy()
peak_genes.columns = ["peak_id", "chr", "start", "end",
                      "annotation", "tss_dist", "refseq", "gene_name"]

# Filter promoter-proximal peaks (within 2 kb of TSS)
promoter_peaks = peak_genes[peak_genes["tss_dist"].abs() < 2000].copy()
print(f"Promoter-proximal peaks (|TSS| < 2kb): {len(promoter_peaks)}")
# Promoter-proximal peaks (|TSS| < 2kb): 2218

# Load DESeq2 results (gene_name, log2FC, padj)
de_results = pd.read_csv("deseq2_results.csv")
de_sig = de_results[de_results["padj"] < 0.05].copy()

# Merge: find DE genes with a nearby peak
merged = promoter_peaks.merge(de_sig, on="gene_name", how="inner")
print(f"DE genes with promoter-proximal peak: {len(merged)}")
print(merged[["gene_name", "tss_dist", "annotation", "log2FC", "padj"]].head())
# DE genes with promoter-proximal peak: 347
```

## Expected Outputs

| Output | Format | Description |
|--------|--------|-------------|
| `motif_output/knownResults.txt` | TSV | All known motifs tested: name, p-value, q-value, % target, % background; primary result file |
| `motif_output/knownResults.html` | HTML | Interactive HTML report with motif logos, statistics, and links |
| `motif_output/homerResults/` | Directory | De novo motifs: `motifN.motif` (PWM matrix), `motifN.logo.png`, `similar.motifs.txt` |
| `motif_output/homerResults.html` | HTML | Interactive HTML report for de novo motifs |
| `annotated_peaks.txt` | TSV | One row per peak: chr, start, end, annotation, TSS distance, nearest gene, RefSeq ID |
| `peaks_with_motif1.txt` | TSV | Per-peak motif occurrence scores (from `-find` mode) |

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `ERROR: Genome not found` | Genome not installed via `installGenome.pl` | Run `installGenome.pl hg38`; confirm `~/.homer/data/genomes/hg38/` exists |
| `command not found: findMotifsGenome.pl` | HOMER binaries not in `$PATH` | Add HOMER bin directory to PATH: `export PATH=~/.homer/bin:$PATH` (or activate conda env) |
| Poor de novo motif quality (GC-rich artifacts) | Unmasked repetitive elements | Always use `-mask`; also try increasing `-size` to 300 or reducing to 150 |
| No significant known motifs (all p > 0.01) | Too few peaks or wrong peak size | Ensure ≥500 peaks; check `-size` matches expected binding footprint (150–200 for TFs) |
| Conda HOMER conflicts (Perl module errors) | HOMER's Perl scripts conflict with conda environment Perl | Install HOMER in a dedicated conda env: `conda create -n homer_only -c bioconda homer` |
| `annotatePeaks.pl` gives all "Intergenic" | Genome annotation not installed | HOMER annotation requires `installGenome.pl` which downloads GTF; check `~/.homer/data/genomes/hg38/` contains `*.ann` files |
| Very slow run time (>2 hr) | Single-threaded or large peak set | Add `-p 8`; reduce `-S` to 10 for speed; use `-nomotif` for known-only runs |
| `-bg` custom background gives poor motifs | Background regions have very different GC content | Use a GC-matched background; run `bedtools shuffle` with `-noOverlapping` to generate random same-size regions |

## References

- [HOMER official documentation](http://homer.ucsd.edu/homer/) — comprehensive guide to all HOMER commands, parameters, and output formats
- Heinz S et al. (2010) "Simple Combinations of Lineage-Determining Transcription Factors Prime cis-Regulatory Elements Required for Macrophage and B Cell Identities." *Molecular Cell* 38(4):576–589. [DOI:10.1016/j.molcel.2010.05.004](https://doi.org/10.1016/j.molcel.2010.05.004)
- [HOMER GitHub: samtools/homer](https://github.com/samtools/homer) — source code and issue tracker
- [JASPAR 2024 database](https://jaspar.elixir.no/) — curated TF binding motif database used by HOMER for known motif enrichment
