---
name: "bakta-genome-annotation"
description: "Annotate bacterial and archaeal genomes and plasmids with Bakta's Prodigal/HMM/diamond pipeline. Identifies CDS, ncRNA, tRNA, rRNA, tmRNA, sORFs, CRISPR arrays, oriC/oriV/oriT, and gaps against a curated UniRef-derived database. Produces NCBI-compatible GFF3, GenBank, EMBL, JSON, FASTA, TSV, and a circular genome plot. Use Prokka for legacy pipelines or non-bacterial kingdoms; PGAP for NCBI GenBank submission."
license: "GPL-3.0"
---

# Bakta Genome Annotation

## Overview

Bakta is a command-line pipeline for rapid, standardized annotation of bacterial and archaeal genomes and plasmids. It combines Prodigal for CDS prediction, tRNAscan-SE/Aragorn/Barrnap/Infernal for non-coding RNA, PILER-CR/PILERCR for CRISPR detection, and a tiered DIAMOND/HMM search against a curated UniRef100 + IPS/UPS database to assign gene names, EC numbers, GO terms, and COG categories. Bakta produces NCBI-compatible outputs (GFF3, GenBank, EMBL, INSDC-formatted FASTA, plus a JSON summary and a circular Circos plot) for a typical 5 Mb genome in 5–15 minutes on 8 CPUs.

## When to Use

- Annotating bacterial or archaeal genome assemblies (Illumina, PacBio, Nanopore) with NCBI-compatible locus tags and product names
- Annotating plasmids and other circular replicons separately with `--plasmid` and `--complete` flags
- Producing JSON-structured annotation outputs that can be parsed without GenBank or GFF3 detours
- Generating a publication-ready circular genome plot via the bundled `bakta_plot` command
- Annotating MAGs (metagenome-assembled genomes) with `--meta` to disable Prodigal training
- Use **Prokka** instead when you need viral/mitochondrial kingdoms or when you must reproduce a legacy Prokka pipeline exactly
- Use **PGAP** instead when submitting to NCBI GenBank with full standards compliance
- Use **Bakta** when you want faster runs, regularly updated UniRef-derived databases, AMRFinderPlus integration, and a JSON summary out of the box

## Prerequisites

- **Software**: Bakta ≥ 1.9, Python 3.8+, Prodigal, tRNAscan-SE, Aragorn, Barrnap, Infernal, DIAMOND, HMMER3, PILER-CR, BLAST+, AMRFinderPlus
- **Database**: Bakta DB (full ~70 GB, or light ~3 GB) downloaded once with `bakta_db download`
- **Python packages** (for output parsing): `biopython`, `pandas`, `matplotlib`
- **Input**: assembled genome in FASTA format (one or more contigs)
- **Hardware**: ≥ 16 GB RAM for full DB, ≥ 4 GB RAM for light DB; ≥ 8 CPUs recommended

> **Check before installing**: The tool may already be available in the current environment (e.g., inside a `pixi` / `conda` env). Run `command -v bakta` first and skip the install commands below if it returns a path. When running inside a pixi project, invoke the tool via `pixi run bakta` rather than bare `bakta`.

```bash
# Install Bakta via conda/mamba (recommended)
mamba install -c conda-forge -c bioconda bakta

# Verify installation
bakta --version
# bakta 1.9.4

# Download the light database (~3 GB, faster, fewer functional hits)
bakta_db download --output db/ --type light

# Or full database (~70 GB, comprehensive UniRef100 coverage)
# bakta_db download --output db/ --type full

# Install Python parsing dependencies
pip install biopython pandas matplotlib
```

## Quick Start

```bash
# Annotate a bacterial genome — results in results/ directory
bakta genome.fasta \
    --db db/bakta_db_light \
    --output results/ \
    --prefix sample1 \
    --threads 8

# Inspect the JSON summary for feature counts
python -c "
import json
with open('results/sample1.json') as f:
    d = json.load(f)
print('Genus:', d['genome'].get('genus'))
print('Length:', d['genome']['size'], 'bp')
print('CDS:', sum(1 for f in d['features'] if f['type'] == 'cds'))
print('tRNA:', sum(1 for f in d['features'] if f['type'] == 'tRNA'))
"
```

## Workflow

### Step 1: Install Bakta and Download the Database

Install Bakta and prepare the reference database. The database download is one-time and reused across runs.

```bash
# Create a dedicated conda environment (avoids dependency conflicts)
mamba create -n bakta_env -c conda-forge -c bioconda bakta python=3.11 -y
mamba activate bakta_env

# Verify Bakta and its dependencies
bakta --version
# bakta 1.9.4

bakta --help | head -20

# Download the light database (sufficient for routine annotation)
mkdir -p db/
bakta_db download --output db/ --type light
# Downloads ~3 GB; expands to ~5 GB on disk

# Verify the database was extracted correctly
ls db/bakta_db_light/
# antifam.h3f  bakta.db  expert  oric.fna  pfam.h3f  rfam-go.tsv  ...

# (Optional) Update AMRFinderPlus DB used by Bakta for AMR gene calling
amrfinder -u

# Install Python parsing tools
pip install biopython pandas matplotlib
```

### Step 2: Prepare the Input Assembly

Bakta requires clean FASTA headers without spaces or special characters. Pre-clean and optionally filter short contigs.

```python
from Bio import SeqIO
import re

input_fasta = "genome.fasta"
records = list(SeqIO.parse(input_fasta, "fasta"))
print(f"Input assembly: {len(records)} contigs")
total_bases = sum(len(r) for r in records)
print(f"Total bases: {total_bases:,}")
print(f"Largest contig: {max(len(r) for r in records):,} bp")

# Bakta preferred: short, alphanumeric, unique IDs
cleaned = []
for i, rec in enumerate(records, 1):
    new_id = f"contig_{i:04d}"
    new_rec = rec.__class__(rec.seq, id=new_id, description="")
    cleaned.append(new_rec)

SeqIO.write(cleaned, "genome_clean.fasta", "fasta")
print(f"Wrote genome_clean.fasta with {len(cleaned)} contigs")
```

```bash
# Filter out short contigs (<200 bp) which contribute little to annotation
awk 'BEGIN{RS=">"; ORS=""} NR>1 {n=split($0, a, "\n"); seq=""; for(i=2;i<=n;i++) seq=seq a[i]; if (length(seq) >= 200) print ">" $0}' \
    genome_clean.fasta > genome_filtered.fasta

echo "Filtered assembly: $(grep -c '>' genome_filtered.fasta) contigs"
```

### Step 3: Run Standard Bakta Annotation

Run Bakta with genus/species hints. Locus tags are auto-generated from the strain field.

```bash
# Standard annotation for a draft bacterial genome
bakta genome_clean.fasta \
    --db db/bakta_db_light \
    --output annotation/ \
    --prefix E_coli_K12 \
    --genus Escherichia \
    --species coli \
    --strain K12 \
    --locus-tag ECOLI \
    --threads 8 \
    --keep-contig-headers

# Expected runtime: 5–15 min for ~5 Mb genome on 8 CPUs (light DB)

echo "Bakta annotation outputs:"
ls annotation/
# E_coli_K12.embl   E_coli_K12.faa     E_coli_K12.ffn
# E_coli_K12.fna    E_coli_K12.gbff    E_coli_K12.gff3
# E_coli_K12.hypotheticals.faa  E_coli_K12.hypotheticals.tsv
# E_coli_K12.json   E_coli_K12.log     E_coli_K12.png
# E_coli_K12.svg    E_coli_K12.tsv     E_coli_K12.txt
```

### Step 4: Parse the JSON Summary

Bakta's JSON output is the canonical, machine-readable annotation. Parse it directly for downstream pipelines.

```python
import json
import pandas as pd
from collections import Counter

with open("annotation/E_coli_K12.json") as f:
    bakta = json.load(f)

# Genome-level metadata
genome = bakta["genome"]
print(f"Organism: {genome.get('genus')} {genome.get('species')} {genome.get('strain')}")
print(f"Size: {genome['size']:,} bp across {len(bakta['sequences'])} sequences")
print(f"GC content: {genome['gc']:.2%}")

# Feature type counts
features = bakta["features"]
type_counts = Counter(f["type"] for f in features)
print("\nFeature counts:")
for ftype, n in sorted(type_counts.items(), key=lambda x: -x[1]):
    print(f"  {ftype:>10}: {n}")

# Build a tidy CDS DataFrame
cds_rows = []
for f in features:
    if f["type"] != "cds":
        continue
    cds_rows.append({
        "locus_tag": f.get("locus", ""),
        "contig":    f.get("contig", ""),
        "start":     f.get("start"),
        "stop":      f.get("stop"),
        "strand":    f.get("strand"),
        "gene":      f.get("gene", ""),
        "product":   f.get("product", ""),
        "length_aa": len(f.get("aa", "")),
    })

cds_df = pd.DataFrame(cds_rows)
print(f"\nTotal CDS: {len(cds_df)}")
print(cds_df.head(5).to_string(index=False))
```

### Step 5: Parse the TSV Feature Table

The TSV output is convenient for spreadsheet workflows and quick filtering.

```python
import pandas as pd

# Bakta TSV begins with comment lines starting with '#'
df = pd.read_csv("annotation/E_coli_K12.tsv", sep="\t", comment="#",
                 names=["sequence_id", "type", "start", "stop", "strand",
                        "locus_tag", "gene", "product", "dbxrefs"])
print(f"Total features: {len(df)}")
print(f"Feature types: {df['type'].value_counts().to_dict()}")

# Hypothetical vs annotated CDS
cds = df[df["type"] == "cds"].copy()
hypothetical = cds["product"].str.contains("hypothetical", case=False, na=True)
print(f"\nCDS with assigned function: {(~hypothetical).sum()} / {len(cds)}")
print(f"Hypothetical proteins: {hypothetical.sum()}")

# Cross-references (UniRef, KEGG, EC, GO, etc.) parsed from the dbxrefs column
def split_xrefs(xref_str):
    if not isinstance(xref_str, str) or xref_str in ("", "-"):
        return []
    return [x.strip() for x in xref_str.split(",")]

cds["dbxref_list"] = cds["dbxrefs"].apply(split_xrefs)
ec_hits = cds[cds["dbxref_list"].apply(lambda xs: any(x.startswith("EC:") for x in xs))]
print(f"CDS with EC numbers: {len(ec_hits)}")
print(ec_hits[["locus_tag", "gene", "product"]].head(5).to_string(index=False))
```

### Step 6: Render the Circular Genome Plot

Bakta emits a Circos-style PNG/SVG by default. Regenerate with custom styling using `bakta_plot`.

```bash
# Re-render the plot from the existing JSON with a different style
bakta_plot --output annotation/ \
           --prefix E_coli_K12_replot \
           --type cog \
           --dpi 300 \
           annotation/E_coli_K12.json

ls annotation/E_coli_K12_replot.*
# E_coli_K12_replot.png  E_coli_K12_replot.svg

# Display the rendered PNG inline in a Jupyter notebook
python <<'PY'
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

img = mpimg.imread("annotation/E_coli_K12.png")
fig, ax = plt.subplots(figsize=(6, 6))
ax.imshow(img)
ax.axis("off")
ax.set_title("Bakta circular genome annotation")
plt.savefig("bakta_circular_thumbnail.png", dpi=120, bbox_inches="tight")
print("Saved bakta_circular_thumbnail.png")
PY
```

### Step 7: Compute Annotation Quality Statistics

Summarize hypothetical-protein rate, gene density, and feature coverage to assess annotation quality.

```python
import json
import pandas as pd
import matplotlib.pyplot as plt

with open("annotation/E_coli_K12.json") as f:
    bakta = json.load(f)

genome_size = bakta["genome"]["size"]
features = bakta["features"]

# Per-feature-type counts and density (per Mb)
counts = {}
for f in features:
    counts[f["type"]] = counts.get(f["type"], 0) + 1
density = {k: v / (genome_size / 1e6) for k, v in counts.items()}

cds = [f for f in features if f["type"] == "cds"]
n_cds = len(cds)
n_hypo = sum(1 for f in cds if "hypothetical" in (f.get("product") or "").lower())
n_known = n_cds - n_hypo
coding_density = sum(abs(f["stop"] - f["start"] + 1) for f in cds) / genome_size

print(f"Genome: {genome_size:,} bp")
print(f"CDS: {n_cds}  ({density.get('cds', 0):.1f} per Mb)")
print(f"  Known function: {n_known}  Hypothetical: {n_hypo}")
print(f"Coding density: {coding_density:.1%}")
print(f"tRNA: {counts.get('tRNA', 0)}   rRNA: {counts.get('rRNA', 0)}")
print(f"ncRNA: {counts.get('ncRNA', 0)}  CRISPR: {counts.get('crispr', 0)}")

# Bar plot of feature type counts
fig, ax = plt.subplots(figsize=(8, 4))
items = sorted(counts.items(), key=lambda x: -x[1])
labels = [k for k, _ in items]
values = [v for _, v in items]
bars = ax.bar(labels, values, color="#2980B9", edgecolor="white")
for bar, v in zip(bars, values):
    ax.text(bar.get_x() + bar.get_width() / 2, v + max(values) * 0.01,
            str(v), ha="center", fontsize=9)
ax.set_ylabel("Count")
ax.set_title("Bakta feature counts by type")
plt.xticks(rotation=20)
plt.tight_layout()
plt.savefig("bakta_feature_counts.png", dpi=150, bbox_inches="tight")
print("Saved bakta_feature_counts.png")
```

### Step 8: Batch Annotation Across Multiple Genomes

Run Bakta over a directory of assemblies and aggregate per-sample summary statistics.

```bash
#!/bin/bash
# batch_bakta.sh — annotate all FASTA files in a directory
INPUT_DIR="genomes/"
OUTPUT_DIR="annotations/"
DB="db/bakta_db_light"
mkdir -p "$OUTPUT_DIR"

for FASTA in "$INPUT_DIR"/*.fasta; do
    SAMPLE=$(basename "$FASTA" .fasta)
    echo "Annotating: $SAMPLE"
    bakta "$FASTA" \
        --db "$DB" \
        --output "${OUTPUT_DIR}/${SAMPLE}" \
        --prefix "$SAMPLE" \
        --threads 4 \
        --skip-plot \
        --force
done

echo "Batch annotation complete."
```

```python
# Aggregate per-genome summaries from each sample's JSON file
from pathlib import Path
import json
import pandas as pd

annotation_dir = Path("annotations/")
rows = []
for json_file in sorted(annotation_dir.glob("*/*.json")):
    with open(json_file) as f:
        bakta = json.load(f)
    sample = json_file.stem
    counts = {}
    for feat in bakta["features"]:
        counts[feat["type"]] = counts.get(feat["type"], 0) + 1
    rows.append({
        "sample":  sample,
        "size":    bakta["genome"]["size"],
        "gc":      bakta["genome"]["gc"],
        "CDS":     counts.get("cds", 0),
        "tRNA":    counts.get("tRNA", 0),
        "rRNA":    counts.get("rRNA", 0),
        "ncRNA":   counts.get("ncRNA", 0),
        "crispr":  counts.get("crispr", 0),
    })

summary_df = pd.DataFrame(rows)
print(f"Annotated genomes: {len(summary_df)}")
print(summary_df.to_string(index=False))
summary_df.to_csv("batch_bakta_summary.csv", index=False)
print("Saved: batch_bakta_summary.csv")
```

## Key Parameters

| Parameter | Default | Range / Options | Effect |
|-----------|---------|-----------------|--------|
| `--db` | — | path to Bakta DB directory | Required; selects light or full reference DB |
| `--genus` | — | any genus name string | Sets organism metadata in GenBank/EMBL output |
| `--species` | — | any species name string | Combined with `--genus` for organism qualifier |
| `--strain` | — | any string | Adds strain qualifier to organism metadata |
| `--locus-tag` | auto | 3–24 alphanumeric chars | Prefix for locus tags (e.g., `ECOLI_00001`) |
| `--complete` | off | flag | Treat all input contigs as complete circular replicons |
| `--plasmid` | off | flag | Treat all input contigs as plasmids (circular) |
| `--meta` | off | flag | Disable Prodigal training (use for MAGs / metagenomic bins) |
| `--translation-table` | `11` | NCBI table IDs (1, 4, 11, 25, …) | Genetic code used by Prodigal for CDS translation |
| `--min-contig-length` | `1` | any integer (bp) | Skip contigs shorter than this length |
| `--threads` | `1` | `1`–CPU count | Parallel threads for DIAMOND/HMMER searches |
| `--skip-plot` | off | flag | Skip the slow circular plot rendering step |
| `--keep-contig-headers` | off | flag | Preserve original contig IDs instead of renaming |
| `--proteins` | — | path to GenBank or FASTA file | Custom expert protein DB used before UniRef search |

## Common Recipes

### Recipe: Plasmid-only Annotation

When to use: A finished circular plasmid sequence that should be annotated without chromosome assumptions.

```bash
bakta plasmid.fasta \
    --db db/bakta_db_light \
    --output plasmid_annotation/ \
    --prefix pBR322 \
    --plasmid \
    --complete \
    --threads 4

# Inspect plasmid-typing results (incompatibility group, replication initiator)
grep -E "rep|inc" plasmid_annotation/pBR322.tsv | head -10
```

### Recipe: MAG (Metagenome-Assembled Genome) Annotation

When to use: Annotating a bin from metagenomic assembly where Prodigal cannot train on the full sequence.

```bash
bakta MAG_bin_42.fasta \
    --db db/bakta_db_light \
    --output mag_annotation/ \
    --prefix MAG_bin_42 \
    --meta \
    --min-contig-length 500 \
    --skip-plot \
    --threads 8

cat mag_annotation/MAG_bin_42.txt | head -20
```

### Recipe: Annotation with Custom Expert Protein Database

When to use: You have curated reference proteins (e.g., a virulence factor catalog) that should take priority over UniRef.

```bash
# Custom proteins are searched before the bundled UniRef DB
bakta genome.fasta \
    --db db/bakta_db_light \
    --proteins virulence_factors.faa \
    --output annotation_custom/ \
    --prefix novel_strain \
    --threads 8

echo "Annotations referencing custom DB:"
grep "User-provided" annotation_custom/novel_strain.tsv | head
```

### Recipe: Convert Bakta GFF3 to a Pandas DataFrame

When to use: You need feature coordinates and qualifiers for downstream coordinate-overlap analyses.

```python
import pandas as pd

def parse_gff3(gff_file):
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
            attrs = {}
            for item in parts[8].split(";"):
                if "=" in item:
                    k, v = item.split("=", 1)
                    attrs[k] = v
            rows.append({
                "seqname":   parts[0],
                "feature":   parts[2],
                "start":     int(parts[3]),
                "end":       int(parts[4]),
                "strand":    parts[6],
                "locus_tag": attrs.get("locus_tag", attrs.get("ID", "")),
                "gene":      attrs.get("gene", ""),
                "product":   attrs.get("product", ""),
            })
    return pd.DataFrame(rows)

gff_df = parse_gff3("annotation/E_coli_K12.gff3")
print(f"Features parsed: {len(gff_df)}")
print(gff_df[gff_df["feature"] == "CDS"].head(5).to_string(index=False))
```

## Expected Outputs

| Output File | Format | Description |
|-------------|--------|-------------|
| `{prefix}.gff3` | GFF3 | Genome annotation with feature coordinates and attributes; INSDC-compliant |
| `{prefix}.gbff` | GenBank Flat File | Annotated GenBank record for use in Geneious, BioPython, NCBI submission prep |
| `{prefix}.embl` | EMBL | EMBL-format annotation for ENA submission |
| `{prefix}.fna` | FASTA | Nucleotide sequences of the input contigs |
| `{prefix}.ffn` | FASTA | Nucleotide sequences of all annotated features |
| `{prefix}.faa` | FASTA | Protein sequences for all CDS features |
| `{prefix}.hypotheticals.faa` | FASTA | Protein sequences flagged as hypothetical (for further investigation) |
| `{prefix}.hypotheticals.tsv` | TSV | Detailed table for hypothetical CDS with low-confidence hits |
| `{prefix}.tsv` | TSV | Full feature table: seqid, type, start, stop, strand, locus_tag, gene, product, dbxrefs |
| `{prefix}.json` | JSON | Machine-readable summary with genome metadata + every feature with full qualifiers |
| `{prefix}.png` / `.svg` | Image | Circos circular genome plot colored by COG category |
| `{prefix}.txt` | Text | Plain-text summary of feature counts and per-replicon stats |
| `{prefix}.log` | Text | Full Bakta run log including timing per step |

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `Error: database not found at <path>` | DB path incorrect, or DB not extracted | Re-run `bakta_db download --output db/ --type light`; pass full path to `--db` |
| `KILLED` during DIAMOND step | Out of memory on full DB | Switch to `--type light`, reduce `--threads`, or run on a host with ≥ 32 GB RAM |
| Very high hypothetical-protein rate (>60 %) | Divergent strain or light DB without close hits | Re-run with the full DB or supply a curated `--proteins` reference set |
| `tRNAscan-SE: Error opening file` | Missing tRNAscan-SE installation in conda env | `mamba install -c bioconda trnascan-se` and rerun |
| Bakta complains about contig headers | Spaces or special characters in FASTA IDs | Pre-clean headers with `awk '/^>/{print ">contig_"++i; next}{print}'` |
| Plot generation hangs or fails | Circos / matplotlib backend issue | Re-run with `--skip-plot`; render later via `bakta_plot` from the JSON file |
| `AMRFinderPlus: database not up-to-date` warning | AMRFinderPlus DB stale | `amrfinder -u` to refresh, or pass `--skip-amr` to bypass |
| Different locus tag prefix than expected | `--locus-tag` not set, default uses random prefix | Explicitly pass `--locus-tag MYORG` to control prefix |
| Run is much slower than reported | Default `--threads 1` | Set `--threads` to physical core count; use `--skip-plot` for batch jobs |

## References

- [Bakta GitHub: oschwengers/bakta](https://github.com/oschwengers/bakta) — source code, installation, parameter reference, and changelog
- [Schwengers et al. (2021) Microb Genom 7(11):000685](https://doi.org/10.1099/mgen.0.000685) — original Bakta publication with benchmarks vs. Prokka and PGAP
- [Bakta database releases on Zenodo](https://doi.org/10.5281/zenodo.4247252) — versioned light/full database archives
- [Prodigal documentation](https://github.com/hyattpd/Prodigal/wiki) — gene prediction engine used by Bakta for CDS calling
- [BioPython GenBank parsing tutorial](https://biopython.org/wiki/SeqIO) — reference for parsing Bakta `.gbff` output in Python
- [DIAMOND aligner](https://github.com/bbuchfink/diamond) — protein search engine used for the UniRef-derived database lookups
