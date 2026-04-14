---
name: "prokka-genome-annotation"
description: "Annotate prokaryotic genome assemblies (bacteria, archaea, viruses) with Prokka's BLAST/HMM-based pipeline. Identifies CDS, rRNA, tRNA, tmRNA, and signal peptides against Pfam, TIGRFAMs, and RefSeq databases. Produces GFF3, GenBank, protein FASTA, and TSV outputs. Use PGAP instead when submitting to NCBI GenBank; use Bakta for faster annotation with NCBI-compatible outputs on modern assemblies."
license: "GPL-3.0"
---

# Prokka Genome Annotation

## Overview

Prokka is a command-line pipeline for rapid annotation of prokaryotic genomes (bacteria, archaea, and viruses). It uses a tiered search strategy: protein-coding genes (CDS) are predicted with Prodigal and searched first against a genus-specific database, then RefSeq proteins, then Pfam/TIGRFAMs HMMs. Non-coding RNA genes (rRNA, tRNA, tmRNA) are identified with Barrnap, Aragorn, and Infernal. Prokka processes a single FASTA assembly in minutes and outputs a comprehensive annotation in GFF3, GenBank, FASTA, and tabular formats.

## When to Use

- Annotating a newly assembled bacterial or archaeal genome from Illumina, PacBio, or Nanopore assemblies
- Getting functional protein annotations (CDS with product names, EC numbers, GO terms) from a draft or complete genome
- Preparing annotation files for downstream comparative genomics (Roary pan-genome, OrthoFinder)
- Annotating viral or phage genomes when kingdom-specific databases are important
- Performing metagenome-assembled genome (MAG) annotation with the `--metagenome` flag
- Parsing annotated outputs in Python with BioPython for downstream sequence or feature analysis
- Use **PGAP** (NCBI Prokaryotic Genome Annotation Pipeline) instead when the goal is NCBI GenBank submission with standards compliance
- Use **Bakta** instead for faster annotation with built-in NCBI-compatible outputs and a more regularly updated database

## Prerequisites

- **Software**: Prokka ≥ 1.14, Perl 5, Prodigal, Barrnap, HMMER3, BLAST+, Aragorn, Infernal, tbl2asn
- **Python packages** (for output parsing): `biopython`, `pandas`, `matplotlib`
- **Input**: assembled genome in FASTA format (complete or draft with multiple contigs)
- **Environment**: conda strongly recommended to handle the Perl and C dependency stack

> **Check before installing**: The tool may already be available in the current environment (e.g., inside a `pixi` / `conda` env). Run `command -v prokka` first and skip the install commands below if it returns a path. When running inside a pixi project, invoke the tool via `pixi run prokka` rather than bare `prokka`.

```bash
# Install Prokka via conda/mamba (recommended)
conda install -c conda-forge -c bioconda prokka

# Or with mamba (faster)
mamba install -c conda-forge -c bioconda prokka

# Verify installation and database setup
prokka --version
# prokka 1.14.6

# Check that required tools are on PATH
prokka --depends
# prokka needs: awk, sed, grep, makeblastdb, blastp, hmmscan, ...

# Install Python parsing dependencies
pip install biopython pandas matplotlib
```

## Quick Start

```bash
# Annotate a bacterial genome assembly — results in results/ directory
prokka genome.fasta \
    --outdir results/ \
    --prefix sample1 \
    --kingdom Bacteria \
    --cpus 4

# Check output summary
cat results/sample1.txt
# Organism: Genus species strain
# Contigs: 1
# Bases: 4639675
# CDS: 4140
# rRNA: 22
# tRNA: 86

echo "Annotation complete. Key output files:"
ls results/sample1.{gff,gbk,faa,ffn,tsv}
```

## Workflow

### Step 1: Install and Verify Prokka

Install Prokka and confirm all dependent tools are accessible in the current environment.

```bash
# Create a dedicated conda environment
conda create -n prokka_env -c conda-forge -c bioconda prokka python=3.10 -y
conda activate prokka_env

# Verify Prokka version and all tool dependencies
prokka --version
# prokka 1.14.6

prokka --depends
# Checking that required tools are installed...
# OK: makeblastdb is installed (2.13.0+)
# OK: blastp is installed (2.13.0+)
# OK: hmmscan is installed (3.3.2)
# OK: prodigal is installed (2.6.3)
# OK: barrnap is installed (0.9)

# Check available genus-specific databases bundled with Prokka
ls $(conda info --base)/envs/prokka_env/db/genus/
# Archaea  Bacteria  Mitochondria  Viruses

# Install Python parsing tools
pip install biopython pandas matplotlib
```

### Step 2: Prepare the Input Genome

Clean and rename contigs to comply with Prokka's header requirements before annotation.

```python
from Bio import SeqIO
import re

# Load and inspect assembly
input_fasta = "genome.fasta"
records = list(SeqIO.parse(input_fasta, "fasta"))
print(f"Input assembly: {len(records)} contigs")
total_bases = sum(len(r) for r in records)
print(f"Total bases: {total_bases:,}")
print(f"Largest contig: {max(len(r) for r in records):,} bp")
print(f"N50 approx: see assembly stats tool")

# Rename contigs to short IDs compatible with Prokka (max 37 chars)
# Prokka requires: no spaces, no special characters in header
cleaned = []
for i, rec in enumerate(records, 1):
    new_id = f"contig_{i:04d}"
    new_rec = rec.__class__(rec.seq, id=new_id, description=f"len={len(rec.seq)}")
    cleaned.append(new_rec)

SeqIO.write(cleaned, "genome_clean.fasta", "fasta")
print(f"\nWrote genome_clean.fasta with {len(cleaned)} renamed contigs")
# genome_clean.fasta: contig_0001 through contig_NNNN
```

```bash
# Alternatively, clean headers with a simple bash one-liner
awk '/^>/{print ">contig_" ++i; next}{print}' genome.fasta > genome_clean.fasta

# Filter out short contigs (< 200 bp) to reduce annotation noise
awk '/^>/{header=$0; next} length($0) >= 200 {print header; print}' \
    genome_clean.fasta > genome_filtered.fasta

echo "Filtered assembly ready: $(grep -c '>' genome_filtered.fasta) contigs"
```

### Step 3: Run Basic Prokka Annotation

Run Prokka with standard options for a bacterial genome, specifying genus/species for database selection.

```bash
# Basic annotation with genus/species hint (uses genus-specific protein database first)
prokka genome_clean.fasta \
    --outdir annotation/ \
    --prefix E_coli_K12 \
    --kingdom Bacteria \
    --genus Escherichia \
    --species coli \
    --strain K12 \
    --cpus 8 \
    --mincontiglen 200

# Expected runtime: 2–10 minutes for a typical 4–6 Mb bacterial genome

echo "Prokka annotation output files:"
ls annotation/
# E_coli_K12.err   E_coli_K12.faa   E_coli_K12.ffn
# E_coli_K12.fna   E_coli_K12.gbk   E_coli_K12.gff
# E_coli_K12.log   E_coli_K12.sqn   E_coli_K12.tbl
# E_coli_K12.tsv   E_coli_K12.txt
```

### Step 4: Parse Annotation Summary (TSV)

Load the TSV output for a quick overview of annotated features and their functional assignments.

```python
import pandas as pd

# Load the annotation TSV (tab-delimited feature table)
tsv_file = "annotation/E_coli_K12.tsv"
df = pd.read_csv(tsv_file, sep="\t")
print(f"Total features: {len(df)}")
print(f"Columns: {list(df.columns)}")
# Columns: [locus_tag, ftype, length_bp, gene, EC_number, COG, product]

# Feature type summary
print("\nFeature type counts:")
print(df["ftype"].value_counts().to_string())
# CDS     4140
# tRNA      86
# rRNA      22
# tmRNA      1

# Functional gene annotations (non-hypothetical CDS)
cds_df = df[df["ftype"] == "CDS"].copy()
hypothetical = cds_df["product"].str.contains("hypothetical", case=False, na=True)
print(f"\nCDS with known function: {(~hypothetical).sum()}")
print(f"Hypothetical proteins: {hypothetical.sum()}")

# Genes with EC numbers (enzymes)
ec_annotated = cds_df[cds_df["EC_number"].notna() & (cds_df["EC_number"] != "")]
print(f"CDS with EC numbers: {len(ec_annotated)}")
print(ec_annotated[["locus_tag", "gene", "EC_number", "product"]].head(5).to_string(index=False))
```

### Step 5: Parse GenBank Output with BioPython

Read the GenBank file to access per-gene sequences, qualifiers, and feature coordinates.

```python
from Bio import SeqIO
import pandas as pd

# Parse GenBank file
gbk_file = "annotation/E_coli_K12.gbk"
records = list(SeqIO.parse(gbk_file, "genbank"))
print(f"Contigs in GenBank: {len(records)}")

# Iterate over CDS features and extract details
rows = []
for rec in records:
    for feat in rec.features:
        if feat.type != "CDS":
            continue
        qualifiers = feat.qualifiers
        rows.append({
            "contig":      rec.id,
            "locus_tag":   qualifiers.get("locus_tag", ["?"])[0],
            "gene":        qualifiers.get("gene", [""])[0],
            "product":     qualifiers.get("product", ["hypothetical protein"])[0],
            "EC_number":   qualifiers.get("EC_number", [""])[0],
            "protein_id":  qualifiers.get("protein_id", [""])[0],
            "start":       int(feat.location.start),
            "end":         int(feat.location.end),
            "strand":      feat.location.strand,
            "aa_length":   len(qualifiers.get("translation", [""])[0]),
        })

features_df = pd.DataFrame(rows)
print(f"CDS features extracted: {len(features_df)}")
print(features_df.head(3).to_string(index=False))

# Retrieve protein sequence for a specific gene
gene_name = "dnaA"
gene_feat = features_df[features_df["gene"] == gene_name]
if not gene_feat.empty:
    idx = gene_feat.index[0]
    print(f"\n{gene_name}: {features_df.loc[idx, 'aa_length']} aa")
```

### Step 6: Visualize Annotation Statistics

Generate a summary barplot of feature types and functional annotation coverage.

```python
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

tsv_file = "annotation/E_coli_K12.tsv"
df = pd.read_csv(tsv_file, sep="\t")

cds = df[df["ftype"] == "CDS"].copy()
n_cds = len(cds)
n_known = (~cds["product"].str.contains("hypothetical", case=False, na=True)).sum()
n_hypo = n_cds - n_known
n_ec = cds["EC_number"].notna().sum()
n_rrna = (df["ftype"] == "rRNA").sum()
n_trna = (df["ftype"] == "tRNA").sum()

fig, axes = plt.subplots(1, 2, figsize=(11, 4))

# Left panel: feature type counts
types = df["ftype"].value_counts()
colors_left = ["#2980B9", "#27AE60", "#E74C3C", "#F39C12"] + ["#95A5A6"] * len(types)
axes[0].bar(types.index, types.values, color=colors_left[:len(types)], edgecolor="white")
axes[0].set_title("Annotated Feature Counts")
axes[0].set_xlabel("Feature Type")
axes[0].set_ylabel("Count")
for i, (label, val) in enumerate(types.items()):
    axes[0].text(i, val + 5, str(val), ha="center", fontsize=9)

# Right panel: CDS functional annotation breakdown
labels = ["Known function", "Hypothetical protein", "Enzyme (EC number)"]
sizes  = [n_known, n_hypo, n_ec]
colors_right = ["#2980B9", "#BDC3C7", "#E74C3C"]
bars = axes[1].bar(labels, sizes, color=colors_right, edgecolor="white")
axes[1].set_title(f"CDS Functional Annotation\n(n={n_cds} total CDS)")
axes[1].set_ylabel("Count")
axes[1].tick_params(axis="x", rotation=15)
for bar, val in zip(bars, sizes):
    axes[1].text(bar.get_x() + bar.get_width() / 2,
                 val + 10, str(val), ha="center", fontsize=9)

plt.suptitle("Prokka Genome Annotation Summary", fontsize=12, fontweight="bold")
plt.tight_layout()
plt.savefig("prokka_annotation_summary.png", dpi=150, bbox_inches="tight")
print(f"Saved prokka_annotation_summary.png")
print(f"CDS: {n_cds}  |  Known function: {n_known}  |  Hypothetical: {n_hypo}")
print(f"rRNA: {n_rrna}  |  tRNA: {n_trna}  |  EC-annotated CDS: {n_ec}")
```

### Step 7: Batch Annotation Across Multiple Genomes

Annotate multiple genome assemblies sequentially and collect summary statistics.

```bash
#!/bin/bash
# batch_prokka.sh — annotate all FASTA files in a directory

INPUT_DIR="genomes/"
OUTPUT_DIR="annotations/"
mkdir -p "$OUTPUT_DIR"

for FASTA in "$INPUT_DIR"/*.fasta; do
    SAMPLE=$(basename "$FASTA" .fasta)
    echo "Annotating: $SAMPLE"
    prokka "$FASTA" \
        --outdir "${OUTPUT_DIR}/${SAMPLE}" \
        --prefix "$SAMPLE" \
        --kingdom Bacteria \
        --cpus 4 \
        --mincontiglen 200 \
        --quiet
    echo "  Done: ${OUTPUT_DIR}/${SAMPLE}/${SAMPLE}.txt"
done

echo "Batch annotation complete."
```

```python
# Collect summary statistics from all Prokka .txt files
from pathlib import Path
import pandas as pd

annotation_dir = Path("annotations/")
rows = []

for txt_file in sorted(annotation_dir.glob("*/*.txt")):
    sample = txt_file.stem
    stats = {}
    with open(txt_file) as f:
        for line in f:
            line = line.strip()
            if ": " in line:
                key, val = line.split(": ", 1)
                stats[key.strip()] = val.strip()
    rows.append({
        "sample":   sample,
        "contigs":  int(stats.get("Contigs", 0)),
        "bases":    int(stats.get("Bases", 0)),
        "CDS":      int(stats.get("CDS", 0)),
        "rRNA":     int(stats.get("rRNA", 0)),
        "tRNA":     int(stats.get("tRNA", 0)),
    })

summary_df = pd.DataFrame(rows)
print(f"Annotated genomes: {len(summary_df)}")
print(summary_df.to_string(index=False))
summary_df.to_csv("batch_annotation_summary.csv", index=False)
print("\nSaved: batch_annotation_summary.csv")
```

### Step 8: Compare Annotations Between Strains

Use the protein FASTA outputs for cross-strain comparison with identity-based clustering.

```python
from Bio import SeqIO, pairwise2
import pandas as pd

# Load protein sequences from two strains
def load_proteins(faa_file):
    """Return dict of locus_tag -> protein sequence."""
    return {rec.id: str(rec.seq)
            for rec in SeqIO.parse(faa_file, "fasta")}

strain_a = load_proteins("annotation_A/strain_A.faa")
strain_b = load_proteins("annotation_B/strain_B.faa")

print(f"Strain A proteins: {len(strain_a)}")
print(f"Strain B proteins: {len(strain_b)}")

# Compare gene counts and size distributions
import matplotlib.pyplot as plt
import numpy as np

len_a = [len(seq) for seq in strain_a.values()]
len_b = [len(seq) for seq in strain_b.values()]

fig, ax = plt.subplots(figsize=(8, 4))
bins = np.linspace(0, 1500, 50)
ax.hist(len_a, bins=bins, alpha=0.6, label=f"Strain A (n={len(len_a)})", color="#2980B9")
ax.hist(len_b, bins=bins, alpha=0.6, label=f"Strain B (n={len(len_b)})", color="#E74C3C")
ax.set_xlabel("Protein Length (aa)")
ax.set_ylabel("Count")
ax.set_title("Protein Length Distribution by Strain")
ax.legend()
plt.tight_layout()
plt.savefig("strain_protein_length_comparison.png", dpi=150, bbox_inches="tight")
print("Saved strain_protein_length_comparison.png")

# Find proteins unique to each strain by size/count difference
print(f"\nSize difference: {abs(len(strain_a) - len(strain_b))} proteins")
print("→ Use Roary or OrthoFinder for formal pan-genome analysis")
```

## Key Parameters

| Parameter | Default | Range / Options | Effect |
|-----------|---------|-----------------|--------|
| `--kingdom` | `Bacteria` | `Bacteria`, `Archaea`, `Viruses`, `Mitochondria` | Selects gene prediction model and default databases |
| `--genus` | — | any genus name string | Prioritizes genus-specific protein database for CDS annotation |
| `--species` | — | any species name string | Combined with `--genus` for locus_tag prefix and organism metadata |
| `--strain` | — | any string | Added to organism metadata in GenBank output |
| `--proteins` | — | path to FASTA file | Custom protein database prepended before RefSeq search |
| `--hmms` | — | path to HMM file | Additional custom HMM database for specialized annotation |
| `--evalue` | `1e-6` | `1e-4`–`1e-9` | E-value cutoff for BLAST and HMMER hits |
| `--cpus` | `8` | `1`–CPU count | Parallel processes for BLAST and HMMER searches |
| `--mincontiglen` | `1` | any integer | Skip contigs shorter than this length (bp) |
| `--metagenome` | off | flag | Disables Prodigal training on this genome (for MAGs) |
| `--rfam` | off | flag | Enable Infernal rRNA/ncRNA search against Rfam (slower) |
| `--norrna` | off | flag | Skip rRNA prediction (use when assembly has no rRNA genes) |
| `--notrna` | off | flag | Skip tRNA prediction |

## Common Recipes

### Recipe: Annotation with Custom Protein Database

When to use: You have closely related reference proteins (e.g., characterized isolate) to improve annotation accuracy.

```bash
# Use a custom protein database to enhance annotation of a novel strain
# Custom proteins are searched first, before internal Prokka databases
prokka genome.fasta \
    --proteins reference_proteins.faa \
    --outdir custom_annotation/ \
    --prefix novel_strain \
    --kingdom Bacteria \
    --cpus 4

echo "Custom DB annotation complete:"
grep "CDS" custom_annotation/novel_strain.txt
```

### Recipe: Metagenome-Assembled Genome (MAG) Annotation

When to use: Annotating a MAG where Prodigal cannot train on the full genome sequence.

```bash
# --metagenome disables Prodigal model training (uses meta mode)
# --mincontiglen 500 discards short, potentially chimeric contigs
prokka MAG_bin_42.fasta \
    --metagenome \
    --kingdom Bacteria \
    --outdir mag_annotation/ \
    --prefix MAG_bin_42 \
    --mincontiglen 500 \
    --cpus 4

echo "MAG annotation complete:"
cat mag_annotation/MAG_bin_42.txt
```

### Recipe: Extract Specific Gene Sequences

When to use: Retrieve nucleotide or protein sequences for a target gene or pathway from the annotation.

```python
from Bio import SeqIO

# Extract all sequences for a specific gene name from protein FASTA
faa_file = "annotation/E_coli_K12.faa"
target_gene = "dnaA"

matches = []
for rec in SeqIO.parse(faa_file, "fasta"):
    # Prokka FASTA header: >locus_tag gene product
    if target_gene in rec.description:
        matches.append(rec)

print(f"Proteins matching '{target_gene}': {len(matches)}")
for rec in matches:
    print(f"  {rec.id}: {len(rec.seq)} aa — {rec.description}")

# Save matching sequences
if matches:
    SeqIO.write(matches, f"{target_gene}_proteins.faa", "fasta")
    print(f"Saved: {target_gene}_proteins.faa")
```

### Recipe: Convert GFF to Pandas DataFrame

When to use: Work with genomic coordinates for feature overlap analysis or visualization.

```python
import pandas as pd

def parse_gff(gff_file):
    """Parse Prokka GFF3 file into a DataFrame (skips sequence section)."""
    rows = []
    with open(gff_file) as f:
        for line in f:
            if line.startswith("##FASTA"):
                break
            if line.startswith("#") or not line.strip():
                continue
            parts = line.rstrip("\n").split("\t")
            if len(parts) < 9:
                continue
            attr_dict = {}
            for item in parts[8].split(";"):
                if "=" in item:
                    k, v = item.split("=", 1)
                    attr_dict[k] = v
            rows.append({
                "seqname":  parts[0],
                "source":   parts[1],
                "feature":  parts[2],
                "start":    int(parts[3]),
                "end":      int(parts[4]),
                "score":    parts[5],
                "strand":   parts[6],
                "frame":    parts[7],
                "locus_tag": attr_dict.get("ID", ""),
                "gene":     attr_dict.get("gene", ""),
                "product":  attr_dict.get("product", ""),
            })
    return pd.DataFrame(rows)

gff_df = parse_gff("annotation/E_coli_K12.gff")
print(f"GFF features: {len(gff_df)}")
print(gff_df[gff_df["feature"] == "CDS"].head(5)[
    ["seqname", "start", "end", "strand", "gene", "product"]
].to_string(index=False))
```

## Expected Outputs

| Output File | Format | Description |
|-------------|--------|-------------|
| `{prefix}.gff` | GFF3 | Genome annotation with feature coordinates and attributes; includes FASTA sequence at the end |
| `{prefix}.gbk` | GenBank | Full GenBank-format annotation for use in Geneious, BioPython, and submission prep |
| `{prefix}.faa` | FASTA | Predicted protein sequences for all CDS features |
| `{prefix}.ffn` | FASTA | Nucleotide sequences for all annotated features (CDS, rRNA, tRNA) |
| `{prefix}.fna` | FASTA | Nucleotide FASTA of the complete assembly (contigs) |
| `{prefix}.tsv` | TSV | Tab-delimited summary table: locus_tag, ftype, length_bp, gene, EC_number, COG, product |
| `{prefix}.txt` | Text | One-line summary counts: Contigs, Bases, CDS, rRNA, tRNA, tmRNA |
| `{prefix}.tbl` | TBL | Feature table format for tbl2asn GenBank submission |
| `{prefix}.sqn` | SQN | ASN.1 format for NCBI submission (generated by tbl2asn) |
| `{prefix}.err` | Text | Warnings and errors from tbl2asn validation step |
| `{prefix}.log` | Text | Full Prokka run log with timing per step |

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `FATAL: Can't find any tRNA genes` | No tRNA detected on short or highly fragmented assembly | Add `--notrna` flag; check if assembly is too fragmented (N50 < 1 kb) |
| `Can't exec "makeblastdb"` | BLAST+ not on PATH | `conda install -c bioconda blast`; ensure prokka env is activated |
| `Contig ID too long (>37 chars)` | Assembler produced long contig headers | Pre-process FASTA to shorten headers: `awk '/^>/{print ">contig_"++i; next}{print}'` |
| Very high hypothetical protein rate (>60%) | Divergent organism with few database matches | Add `--proteins` with closely related strain FAA; consider `--genus` flag |
| `ERROR: Argument --proteins: file does not exist` | Path to custom protein file is incorrect | Use absolute path; verify file exists with `ls -la custom.faa` |
| `tbl2asn error: multiple /product` | Duplicate product qualifiers in annotation | Ignore if exporting for local use; for NCBI submission, use PGAP instead |
| Annotation is very slow (>30 min for ~5 Mb) | `--cpus` not set or set to 1; `--rfam` enabled | Set `--cpus` to available thread count; disable `--rfam` for faster runs |
| rRNA count is 0 for complete genome | `--norrna` flag was set, or barrnap threshold too strict | Remove `--norrna`; check barrnap is installed with `barrnap --version` |

## References

- [Prokka GitHub: tseemann/prokka](https://github.com/tseemann/prokka) — source code, installation instructions, and detailed parameter reference
- [Seemann T (2014) Bioinformatics 30(14):2068–2069](https://doi.org/10.1093/bioinformatics/btu153) — original Prokka paper with benchmarks vs. RAST
- [Prodigal documentation](https://github.com/hyattpd/Prodigal/wiki) — gene prediction engine used by Prokka for CDS calling
- [Barrnap GitHub: tseemann/barrnap](https://github.com/tseemann/barrnap) — rRNA prediction tool bundled with Prokka
- [BioPython GenBank parsing tutorial](https://biopython.org/wiki/SeqIO) — reference for parsing Prokka GenBank output in Python
