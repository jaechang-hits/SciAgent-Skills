---
name: "roary-pangenome"
description: "Compute the bacterial pan-genome from Prokka/Bakta GFF3 annotations with Roary's CD-HIT + BLAST + MCL clustering pipeline. Builds gene presence/absence matrices, core/soft-core/shell/cloud partitions, multi-FASTA core gene alignments (with `-e`), and a pan-genome reference. Use Panaroo for higher-accuracy pan-genomes from highly fragmented assemblies, PIRATE for paralog-aware clustering, or PPanGGOLiN for graph-based partitioning."
license: "GPL-3.0"
---

# Roary Pan-Genome Pipeline

## Overview

Roary is a high-throughput pan-genome pipeline for prokaryotes that takes per-sample GFF3 annotations (typically from Prokka or Bakta) and produces a clustered gene presence/absence matrix across the entire input set. It first reduces redundancy with CD-HIT iterative clustering, then performs an all-vs-all BLASTP within each pre-cluster, and finally applies MCL graph clustering to define orthologous gene families. The output partitions the gene space into core (≥ 99 %), soft-core (95–99 %), shell (15–95 %), and cloud (< 15 %) genes and optionally builds a concatenated core-gene alignment suitable for phylogenetic inference.

## When to Use

- Computing a pan-genome from a set of bacterial isolate annotations (10–10,000 genomes)
- Producing a `gene_presence_absence.csv` matrix for downstream GWAS, accessory-gene mining, or core-gene phylogenetics
- Building a concatenated core-gene multi-FASTA alignment for ML/Bayesian phylogenetic trees
- Generating a pan-genome reference FASTA to use as a non-redundant gene catalog
- Comparative genomics across closely related strains where >95 % nucleotide identity is expected
- Use **Panaroo** instead when assemblies are highly fragmented or annotations are noisy (Panaroo aggressively cleans annotation errors)
- Use **PIRATE** instead when paralog-aware clustering with multiple identity thresholds is needed
- Use **PPanGGOLiN** instead when graph-based, statistically grounded gene-family partitioning is preferred over fixed-frequency cutoffs

## Prerequisites

- **Software**: Roary ≥ 3.13, Perl 5, BLAST+, CD-HIT, MCL, BEDTools, PRANK or MAFFT (for `-e` core alignment), FastTree (optional)
- **Python packages** (for output parsing): `pandas`, `matplotlib`, `seaborn`, `biopython`, `dendropy`
- **Input**: per-sample GFF3 files with embedded FASTA at the end (Prokka/Bakta default output)
- **Hardware**: ≥ 8 GB RAM for ~50 genomes; 32 GB+ recommended for ~500 genomes
- **Naming**: each GFF3 filename becomes the sample column header in the output matrix; use `sample_id.gff` style

> **Check before installing**: The tool may already be available in the current environment (e.g., inside a `pixi` / `conda` env). Run `command -v roary` first and skip the install commands below if it returns a path. When running inside a pixi project, invoke the tool via `pixi run roary` rather than bare `roary`.

```bash
# Install Roary via conda/mamba (recommended)
mamba install -c conda-forge -c bioconda roary

# Verify installation
roary --version
# 3.13.0

# Verify dependent tools
which cd-hit blastp mcl bedtools mafft
# /opt/conda/bin/cd-hit
# /opt/conda/bin/blastp
# /opt/conda/bin/mcl
# /opt/conda/bin/bedtools
# /opt/conda/bin/mafft

# Install Python parsing dependencies
pip install pandas matplotlib seaborn biopython dendropy
```

## Quick Start

```bash
# Run Roary on all GFF3 files in current directory; emit core gene alignment
roary -e --mafft -p 8 -o pangenome -f roary_out/ *.gff

# Inspect summary statistics
cat roary_out/summary_statistics.txt
# Core genes        (99% <= strains <= 100%) 2823
# Soft core genes   (95% <= strains <  99%)   78
# Shell genes       (15% <= strains <  95%)  1542
# Cloud genes       ( 0% <= strains <  15%)  3104
# Total genes                                 7547
```

## Workflow

### Step 1: Install Roary and Verify Dependencies

Install Roary in a dedicated environment to avoid Perl module conflicts.

```bash
# Create a dedicated conda environment
mamba create -n roary_env -c conda-forge -c bioconda roary mafft fasttree python=3.11 -y
mamba activate roary_env

# Verify Roary
roary --version
# 3.13.0

# Confirm pipeline dependencies are reachable
for tool in cd-hit blastp mcl bedtools mafft FastTree; do
    if command -v $tool >/dev/null; then
        echo "OK: $tool"
    else
        echo "MISSING: $tool"
    fi
done

# Install Python parsing tools
pip install pandas matplotlib seaborn biopython dendropy
```

### Step 2: Prepare Per-Sample GFF3 Files from Prokka or Bakta

Roary requires GFF3 files with an embedded FASTA section (the `##FASTA` block). Both Prokka `.gff` and Bakta `.gff3` outputs satisfy this format.

```bash
# Verify GFF3 files include the embedded FASTA section
mkdir -p roary_input/
cp annotations/*/sample*.gff roary_input/

for GFF in roary_input/*.gff; do
    if grep -q "^##FASTA" "$GFF"; then
        echo "OK: $GFF"
    else
        echo "MISSING ##FASTA in: $GFF"
    fi
done

# Roary uses GFF filename (without .gff) as the sample column name.
# Rename or symlink to ensure unique, descriptive names.
cd roary_input/
ls *.gff | head
# strain_A.gff  strain_B.gff  strain_C.gff
```

```python
# Sanity-check sample size and unique names
from pathlib import Path

gff_files = sorted(Path("roary_input/").glob("*.gff"))
print(f"GFF files: {len(gff_files)}")

names = [g.stem for g in gff_files]
duplicates = [n for n in names if names.count(n) > 1]
assert not duplicates, f"Duplicate sample names: {set(duplicates)}"

# Show first 5
for g in gff_files[:5]:
    size_mb = g.stat().st_size / 1e6
    print(f"  {g.name}: {size_mb:.1f} MB")
```

### Step 3: Run Roary with Core Gene Alignment

The `-e --mafft` combination produces the concatenated core-gene alignment used downstream for phylogenetics.

```bash
# Run Roary on the prepared GFF directory
# -e: extract core gene alignment per gene, then concatenate
# --mafft: use MAFFT for alignment (faster than default PRANK)
# -p 8: 8 parallel processes
# -i 95: min BLASTP percentage identity (default 95)
# -cd 99: % isolates a gene must be in to be "core" (default 99)
roary -e --mafft \
    -p 8 \
    -i 95 \
    -cd 99 \
    -o pangenome \
    -f roary_out/ \
    roary_input/*.gff

# Expected runtime:
#   ~50 genomes:  10–20 min
#   ~500 genomes: 4–8 hours

ls roary_out/
# accessory_binary_genes.fa            gene_presence_absence.csv
# accessory_binary_genes.fa.newick     gene_presence_absence.Rtab
# accessory.header.embl                number_of_conserved_genes.Rtab
# accessory.tab                        number_of_genes_in_pan_genome.Rtab
# blast_identity_frequency.Rtab        number_of_new_genes.Rtab
# clustered_proteins                   number_of_unique_genes.Rtab
# core_accessory.header.embl           pan_genome_reference.fa
# core_accessory.tab                   summary_statistics.txt
# core_gene_alignment.aln
```

### Step 4: Parse the Gene Presence/Absence Matrix

The CSV output is the canonical pan-genome matrix: rows are gene families, columns include metadata and one column per sample (filled with locus tags or empty).

```python
import pandas as pd
import numpy as np

df = pd.read_csv("roary_out/gene_presence_absence.csv", low_memory=False)
print(f"Gene families: {len(df)}")
print(f"Columns: {len(df.columns)}")
# Standard metadata columns end with 'Inference', then sample columns follow
metadata_cols = list(df.columns[:14])
sample_cols = list(df.columns[14:])
print(f"Samples: {len(sample_cols)}")

# Build a binary presence/absence matrix (1 = locus tag present, 0 = empty)
binary = df[sample_cols].notna().astype(int)
binary.index = df["Gene"]
print(f"Binary matrix shape: {binary.shape}")

# Pan-genome partition by frequency
n_samples = len(sample_cols)
freq = binary.sum(axis=1) / n_samples
core      = freq[freq >= 0.99]
soft_core = freq[(freq >= 0.95) & (freq < 0.99)]
shell     = freq[(freq >= 0.15) & (freq < 0.95)]
cloud     = freq[freq < 0.15]

print(f"\nPan-genome partition (n={n_samples} genomes):")
print(f"  Core      (>=99 %): {len(core):>5}")
print(f"  Soft-core (95–99 %): {len(soft_core):>5}")
print(f"  Shell    (15–95 %): {len(shell):>5}")
print(f"  Cloud      (<15 %): {len(cloud):>5}")
print(f"  Total            : {len(freq):>5}")
```

### Step 5: Visualize the Pan-Genome Frequency Distribution

A frequency histogram exposes whether the input set has a U-shaped (open) or core-skewed (closed) pan-genome.

```python
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

df = pd.read_csv("roary_out/gene_presence_absence.csv", low_memory=False)
sample_cols = list(df.columns[14:])
n = len(sample_cols)
binary = df[sample_cols].notna().astype(int)
freq = binary.sum(axis=1)

fig, axes = plt.subplots(1, 2, figsize=(11, 4))

# Histogram of gene frequencies
axes[0].hist(freq, bins=range(1, n + 2), color="#2980B9", edgecolor="white")
axes[0].axvline(0.99 * n, color="red", linestyle="--", label="99 % core cutoff")
axes[0].axvline(0.15 * n, color="orange", linestyle="--", label="15 % shell cutoff")
axes[0].set_xlabel("Number of genomes containing the gene")
axes[0].set_ylabel("Number of gene families")
axes[0].set_title("Pan-genome frequency distribution")
axes[0].legend()

# Pie chart of pan-genome partition
freqp = freq / n
core_n      = (freqp >= 0.99).sum()
soft_n      = ((freqp >= 0.95) & (freqp < 0.99)).sum()
shell_n     = ((freqp >= 0.15) & (freqp < 0.95)).sum()
cloud_n     = (freqp < 0.15).sum()
axes[1].pie([core_n, soft_n, shell_n, cloud_n],
            labels=[f"Core ({core_n})", f"Soft-core ({soft_n})",
                    f"Shell ({shell_n})", f"Cloud ({cloud_n})"],
            colors=["#27AE60", "#3498DB", "#F39C12", "#95A5A6"],
            autopct="%1.1f%%", startangle=90)
axes[1].set_title(f"Pan-genome partition (n={n} genomes)")

plt.tight_layout()
plt.savefig("pangenome_distribution.png", dpi=150, bbox_inches="tight")
print(f"Saved pangenome_distribution.png  (total families: {len(freq)})")
```

### Step 6: Build a Phylogenetic Tree from the Core Gene Alignment

Use FastTree on the concatenated core-gene alignment to recover strain relationships.

```bash
# FastTree expects an aligned multi-FASTA; Roary produces this with `-e`
FastTree -nt -gtr -nosupport \
    < roary_out/core_gene_alignment.aln \
    > roary_out/core_gene_tree.nwk

echo "Tree built: roary_out/core_gene_tree.nwk"
# (Optional) IQ-TREE for support values:
# iqtree -s core_gene_alignment.aln -m GTR+G -bb 1000 -nt 8
```

```python
# Visualize the FastTree result alongside the gene presence/absence matrix
import dendropy
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

tree = dendropy.Tree.get(path="roary_out/core_gene_tree.nwk", schema="newick")
leaves = [leaf.taxon.label for leaf in tree.leaf_node_iter()]
print(f"Tree leaves: {len(leaves)}")
print(f"Tree length: {tree.length():.4f} substitutions/site")

# Print first 10 leaves with their root-to-tip distances
for leaf in list(tree.leaf_node_iter())[:10]:
    dist = leaf.distance_from_root()
    print(f"  {leaf.taxon.label:<25}  d={dist:.4f}")
```

### Step 7: Produce Roary's Built-in Summary Plots

Roary ships with a `roary_plots.py` companion that builds a tree-anchored matrix figure.

```bash
# Use the bundled python helper from the Roary install
# (download from: https://github.com/sanger-pathogens/Roary/blob/master/contrib/roary_plots/roary_plots.py)
python roary_plots.py \
    roary_out/core_gene_tree.nwk \
    roary_out/gene_presence_absence.csv \
    --format png \
    --labels

ls *.png
# pangenome_frequency.png
# pangenome_matrix.png
# pangenome_pie.png
```

### Step 8: Compute Per-Genome Accessory Gene Counts

Identify which genomes carry the most unique (cloud) genes — useful for strain-specific gene investigation.

```python
import pandas as pd

df = pd.read_csv("roary_out/gene_presence_absence.csv", low_memory=False)
sample_cols = list(df.columns[14:])
n = len(sample_cols)
binary = df[sample_cols].notna().astype(int)
binary.index = df["Gene"]

freq = binary.sum(axis=1)
cloud_mask = freq < (0.15 * n)
shell_mask = (freq >= 0.15 * n) & (freq < 0.95 * n)

per_genome = pd.DataFrame({
    "genes_total":   binary.sum(axis=0),
    "cloud_genes":   binary.loc[cloud_mask].sum(axis=0),
    "shell_genes":   binary.loc[shell_mask].sum(axis=0),
})
per_genome = per_genome.sort_values("cloud_genes", ascending=False)
print(per_genome.head(10).to_string())

per_genome.to_csv("per_genome_accessory_counts.csv")
print("\nSaved per_genome_accessory_counts.csv")
```

## Key Parameters

| Parameter | Default | Range / Options | Effect |
|-----------|---------|-----------------|--------|
| `-i` | `95` | `70`–`99` (% identity) | Minimum BLASTP percentage identity for clustering |
| `-cd` | `99` | `90`–`100` (%) | Minimum % of isolates a gene must be in to be called "core" |
| `-p` | `1` | `1`–CPU count | Number of parallel processes for BLAST and MCL stages |
| `-e` | off | flag | Extract concatenated core gene multi-FASTA alignment (per-gene MSA + concat) |
| `--mafft` | off | flag (with `-e`) | Use MAFFT for alignment (faster than default PRANK) |
| `-s` | off | flag | Do not split paralogs into separate gene families |
| `-n` | off | flag | Use fast core gene alignment with MAFFT (skips per-gene PRANK) |
| `-g` | `50000` | any integer | Maximum number of clusters expected (cap on output size) |
| `-iv` | `1.5` | `1.2`–`5.0` | MCL inflation value; higher = tighter clusters |
| `-r` | off | flag | Generate R plots (presence/absence heatmap, pan-genome curves) |
| `-o` | `clustered_proteins` | string | Output prefix for clustered proteins file |
| `-f` | `.` | path | Output directory |
| `-z` | off | flag | Don't delete intermediate files (useful for debugging) |

## Common Recipes

### Recipe: Core Gene Alignment from Existing Roary Output

When to use: You already ran Roary without `-e` and now need a phylogenetic alignment.

```bash
# Re-run only the alignment step using the extracted core genes
# query_pan_genome from the Roary suite extracts gene-family multi-FASTAs
query_pan_genome -a intersection \
    -g roary_out/clustered_proteins \
    -o core_gene_list.txt \
    roary_input/*.gff

echo "Core genes: $(wc -l < core_gene_list.txt)"
# Then re-run Roary with -e to materialize the alignment:
# roary -e --mafft -p 8 -f roary_out2/ roary_input/*.gff
```

### Recipe: Lower Identity Threshold for Diverse Genus-Level Sets

When to use: Comparing genomes across multiple closely related species (e.g., genus-level pan-genome).

```bash
# Drop identity to 70 % to capture orthologs across species boundaries
roary -e --mafft \
    -p 8 \
    -i 70 \
    -cd 99 \
    -f roary_genus/ \
    roary_input/*.gff

cat roary_genus/summary_statistics.txt
# Expect a smaller core and a much larger shell + cloud
```

### Recipe: Roary on a Subset of Strains

When to use: You want a pan-genome of a specific subclade without re-annotating all genomes.

```bash
# Stage GFF files for the subset
mkdir -p subset/
for SAMPLE in strain_A strain_B strain_E strain_K; do
    cp roary_input/${SAMPLE}.gff subset/
done

roary -e --mafft -p 4 -f roary_subset/ subset/*.gff
echo "Subset pan-genome:"
cat roary_subset/summary_statistics.txt
```

### Recipe: Cross-Tabulate Accessory Genes Against Strain Metadata

When to use: You want to find genes enriched in a specific phenotype or geographic group.

```python
import pandas as pd
from scipy.stats import fisher_exact

# Load presence/absence and strain metadata
pa = pd.read_csv("roary_out/gene_presence_absence.csv", low_memory=False)
sample_cols = list(pa.columns[14:])
binary = pa[sample_cols].notna().astype(int)
binary.index = pa["Gene"]
binary.columns = sample_cols

# Metadata: sample_id, phenotype (e.g., "resistant" / "susceptible")
meta = pd.read_csv("strain_metadata.csv").set_index("sample_id")
group_resistant = meta[meta["phenotype"] == "resistant"].index
group_susceptible = meta[meta["phenotype"] == "susceptible"].index
group_resistant = [g for g in group_resistant if g in binary.columns]
group_susceptible = [g for g in group_susceptible if g in binary.columns]

# Fisher's exact test per gene family
results = []
for gene, row in binary.iterrows():
    a = int(row[group_resistant].sum())
    b = len(group_resistant) - a
    c = int(row[group_susceptible].sum())
    d = len(group_susceptible) - c
    if a + c == 0 or a + c == len(group_resistant) + len(group_susceptible):
        continue  # skip invariant genes
    odds, pval = fisher_exact([[a, b], [c, d]])
    results.append({"gene": gene, "n_resistant": a, "n_susceptible": c,
                    "odds_ratio": odds, "pvalue": pval})

results_df = pd.DataFrame(results).sort_values("pvalue")
print(f"Gene-phenotype associations (top 10):")
print(results_df.head(10).to_string(index=False))
results_df.to_csv("phenotype_associated_genes.csv", index=False)
```

## Expected Outputs

| Output File | Format | Description |
|-------------|--------|-------------|
| `gene_presence_absence.csv` | CSV | Pan-genome matrix; rows = gene families, columns = sample locus tags |
| `gene_presence_absence.Rtab` | TSV | Binary 0/1 matrix in R-friendly format |
| `summary_statistics.txt` | Text | Counts of core / soft-core / shell / cloud / total gene families |
| `pan_genome_reference.fa` | FASTA | Non-redundant nucleotide reference of one representative per gene family |
| `clustered_proteins` | Text | Cluster definitions: cluster name → constituent locus tags |
| `core_gene_alignment.aln` | FASTA (aligned) | Concatenated multi-FASTA of core gene alignments (only with `-e`) |
| `accessory_binary_genes.fa` | FASTA | Binary 0/1 sequences of accessory presence (input to FastTree) |
| `accessory_binary_genes.fa.newick` | Newick | Accessory gene phylogeny (built from binary FASTA) |
| `number_of_conserved_genes.Rtab` | TSV | Rarefaction curve of core genes vs. genome count |
| `number_of_genes_in_pan_genome.Rtab` | TSV | Rarefaction curve of pan-genome growth |
| `number_of_new_genes.Rtab` | TSV | New genes added per genome |
| `number_of_unique_genes.Rtab` | TSV | Per-genome unique gene counts |
| `blast_identity_frequency.Rtab` | TSV | Distribution of BLAST identities used during clustering |

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `GFF file does not contain ##FASTA` | Annotation file is not a Prokka/Bakta-style GFF3 with embedded sequences | Re-export from Prokka/Bakta; do not strip the FASTA tail |
| `Could not run blastp` | BLAST+ missing from the conda env | `mamba install -c bioconda blast` and re-activate the env |
| Roary produces 0 core genes | One sample has very different annotations or is misidentified | Inspect `gene_presence_absence.csv`; remove outlier with `roary --check_input` style sanity checks |
| Job runs out of memory on > 200 genomes | Default identity (95 %) creates many BLAST jobs | Increase `-i` to 90 if accuracy permits; split into batches; use Panaroo on RAM-tight machines |
| Paralogs split into many tiny clusters | MCL inflation too high or duplicate locus tags across samples | Add `-s` to keep paralogs together, or rerun Prokka/Bakta with unique `--locus-tag` per sample |
| `FastTree: bad alignment` on `core_gene_alignment.aln` | Alignment built with PRANK was truncated | Re-run with `--mafft` for MAFFT-based alignment |
| Output column names look mangled or missing | GFF filenames had spaces or special characters | Rename input GFFs to `[a-zA-Z0-9_]+.gff` before running |
| Same genome counted twice | Duplicate GFF filenames (e.g., copied symlinks) | Run `ls roary_input/*.gff | sort -u` to confirm unique filenames |
| Pan-genome size grows linearly without saturation | Truly open pan-genome (expected for many bacteria) | This is biological, not a bug; report rarefaction curves and use Heaps' law for confirmation |

## References

- [Roary GitHub: sanger-pathogens/Roary](https://github.com/sanger-pathogens/Roary) — source code, parameter reference, and roary_plots.py helper
- [Page et al. (2015) Bioinformatics 31(22):3691–3693](https://doi.org/10.1093/bioinformatics/btv421) — original Roary publication describing the CD-HIT + MCL pipeline
- [Roary tutorial](https://sanger-pathogens.github.io/Roary/) — step-by-step worked example with sample data
- [Panaroo (alternative tool)](https://github.com/gtonkinhill/panaroo) — graph-based pan-genome with stricter annotation cleaning
- [PIRATE (alternative tool)](https://github.com/SionBayliss/PIRATE) — paralog-aware pan-genome at multiple identity thresholds
- [PPanGGOLiN (alternative tool)](https://github.com/labgem/PPanGGOLiN) — graph-based statistical partitioning of pan-genomes
- [FastTree documentation](http://www.microbesonline.org/fasttree/) — reference for ML phylogenetic inference from core gene alignments
