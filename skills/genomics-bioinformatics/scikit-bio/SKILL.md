---
name: scikit-bio
description: >-
  Python library for biology: sequence manipulation (DNA/RNA/protein),
  pairwise/multiple alignment, phylogenetic trees (NJ, UPGMA), diversity
  (Shannon, Faith PD, Bray-Curtis, UniFrac), ordination (PCoA, CCA, RDA),
  stats (PERMANOVA, ANOSIM, Mantel), file I/O (FASTA, FASTQ, Newick,
  BIOM). Use for microbiome, community ecology, or phylogenetics.
license: BSD-3-Clause
---

# scikit-bio

## Overview

scikit-bio is a comprehensive Python library for biological data analysis, spanning sequence manipulation, alignment, phylogenetics, microbial ecology, and multivariate statistics. It provides specialized data structures (DNA, RNA, Protein, DistanceMatrix, TreeNode, TabularMSA) that integrate with the broader Python scientific stack.

## When to Use

- Calculating alpha/beta diversity and running PERMANOVA on microbiome data
- Building phylogenetic trees from distance matrices (NJ, UPGMA)
- Performing PCoA ordination on community composition data
- Reading/writing biological formats (FASTA, FASTQ, Newick, BIOM)
- Pairwise sequence alignment (Smith-Waterman, Needleman-Wunsch)
- Computing UniFrac distances for phylogenetic beta diversity
- Statistical testing on ecological distance matrices (ANOSIM, Mantel)
- Working with QIIME 2 artifacts and microbiome pipelines
- For high-throughput NGS alignment/variant calling, use STAR/BWA instead
- For protein structure prediction, use AlphaFold/ESMFold instead

## Prerequisites

```bash
pip install scikit-bio
# Optional: pip install biom-format  — HDF5 BIOM table support
# Optional: pip install matplotlib seaborn  — visualization
```

## Quick Start

```python
import skbio
from skbio.diversity import alpha_diversity, beta_diversity
from skbio.stats.distance import permanova
from skbio.stats.ordination import pcoa
import numpy as np

# Sample OTU counts (samples × features)
counts = np.array([[10, 20, 30], [15, 25, 5], [5, 10, 40], [20, 5, 15]])
sample_ids = ['S1', 'S2', 'S3', 'S4']
grouping = ['control', 'control', 'treatment', 'treatment']

# Alpha diversity
shannon = alpha_diversity('shannon', counts, ids=sample_ids)
print(f"Shannon diversity: {shannon.values}")  # [1.09, 1.04, 0.94, 1.03]

# Beta diversity → PCoA → PERMANOVA
bc_dm = beta_diversity('braycurtis', counts, ids=sample_ids)
pcoa_results = pcoa(bc_dm)
results = permanova(bc_dm, grouping, permutations=999)
print(f"PERMANOVA p-value: {results['p-value']}")
```

## Core API

### 1. Sequence Manipulation

```python
from skbio import DNA, RNA, Protein

# Create and manipulate sequences
dna = DNA('ATCGATCGATCG', metadata={'id': 'gene1', 'description': 'test'})
rc = dna.reverse_complement()
rna = dna.transcribe()
protein = rna.translate()
print(f"DNA: {dna}, RC: {rc}, Protein: {protein}")

# Motif finding and k-mer analysis
motif_positions = dna.find_with_regex('ATG.{3}')
kmer_freqs = dna.kmer_frequencies(k=3)
print(f"3-mer frequencies: {dict(list(kmer_freqs.items())[:3])}")

# Sequence properties
print(f"Has degenerates: {dna.has_degenerates()}")
print(f"GC content: {dna.gc_content():.2f}")
degapped = dna.degap()  # Remove gap characters
```

```python
# Metadata: sequence-level, positional, interval
dna = DNA('ATCGATCG', metadata={'id': 'seq1'},
          positional_metadata={'quality': [30, 35, 40, 38, 32, 36, 34, 33]})
dna.interval_metadata.add([(0, 4)], metadata={'type': 'promoter'})
print(f"Quality scores: {list(dna.positional_metadata['quality'])}")
```

### 2. Sequence Alignment

```python
from skbio import DNA
from skbio.alignment import local_pairwise_align_ssw, TabularMSA

# Pairwise local alignment (Smith-Waterman via SSW)
seq1 = DNA('ACTCGATCGATCGATCGATCG')
seq2 = DNA('ATCGATCGATCGATCGATCGA')
alignment, score, start_end = local_pairwise_align_ssw(seq1, seq2)
print(f"Score: {score}, Positions: {start_end}")

# Multiple sequence alignment from file
msa = TabularMSA.read('alignment.fasta', constructor=DNA)
consensus = msa.consensus()
conservation = msa.conservation()
print(f"Consensus: {consensus[:20]}, Conservation: {conservation[:5]}")
```

### 3. Phylogenetic Trees

```python
from skbio import TreeNode, DistanceMatrix
from skbio.tree import nj, upgma

# Build tree from distance matrix
data = [[0, 5, 9, 9], [5, 0, 10, 10], [9, 10, 0, 8], [9, 10, 8, 0]]
dm = DistanceMatrix(data, ids=['A', 'B', 'C', 'D'])
tree = nj(dm)
print(tree.ascii_art())

# Tree operations
subtree = tree.shear(['A', 'B', 'C'])  # Prune to subset
tips = [node.name for node in tree.tips()]
lca = tree.lowest_common_ancestor(['A', 'B'])
print(f"Tips: {tips}, LCA children: {len(list(lca.children))}")

# Tree comparison
tree2 = upgma(dm)
rf_dist = tree.compare_rfd(tree2)
cophenetic_dm = tree.cophenetic_matrix()
print(f"Robinson-Foulds distance: {rf_dist}")
```

### 4. Diversity Analysis

```python
from skbio.diversity import alpha_diversity, beta_diversity
import numpy as np

counts = np.array([[10, 20, 30, 0], [15, 25, 5, 10], [5, 10, 40, 2]])
sample_ids = ['S1', 'S2', 'S3']

# Alpha diversity (multiple metrics)
for metric in ['shannon', 'simpson', 'observed_otus', 'pielou_e']:
    alpha = alpha_diversity(metric, counts, ids=sample_ids)
    print(f"{metric}: {alpha.values.round(3)}")

# Beta diversity
bc_dm = beta_diversity('braycurtis', counts, ids=sample_ids)
jaccard_dm = beta_diversity('jaccard', counts, ids=sample_ids)
print(f"Bray-Curtis S1-S2: {bc_dm['S1', 'S2']:.3f}")
```

```python
# Phylogenetic diversity (requires tree + OTU IDs)
from skbio.diversity import alpha_diversity, beta_diversity

faith_pd = alpha_diversity('faith_pd', counts, ids=sample_ids,
                           tree=tree, otu_ids=feature_ids)
unifrac_dm = beta_diversity('unweighted_unifrac', counts,
                            ids=sample_ids, tree=tree, otu_ids=feature_ids)
w_unifrac_dm = beta_diversity('weighted_unifrac', counts,
                              ids=sample_ids, tree=tree, otu_ids=feature_ids)
print(f"Faith PD: {faith_pd.values}")
```

### 5. Ordination

```python
from skbio.stats.ordination import pcoa, cca

# PCoA from distance matrix
pcoa_results = pcoa(bc_dm)
pc1 = pcoa_results.samples['PC1']
pc2 = pcoa_results.samples['PC2']
prop = pcoa_results.proportion_explained
print(f"PC1 explains {prop.iloc[0]:.1%}, PC2 explains {prop.iloc[1]:.1%}")

# CCA with environmental variables (constrained ordination)
# species_matrix: samples × species counts
# env_matrix: samples × environmental variables
cca_results = cca(species_matrix, env_matrix)
biplot_scores = cca_results.biplot_scores
print(f"Biplot scores shape: {biplot_scores.shape}")

# Save/load ordination results
pcoa_results.write('pcoa_results.txt')
loaded = skbio.OrdinationResults.read('pcoa_results.txt')
```

### 6. Statistical Testing

```python
from skbio.stats.distance import permanova, anosim, permdisp, mantel

grouping = ['control', 'control', 'treatment']

# PERMANOVA — test group differences
perm_results = permanova(bc_dm, grouping, permutations=999)
print(f"PERMANOVA: F={perm_results['test statistic']:.3f}, "
      f"p={perm_results['p-value']:.4f}")

# ANOSIM — alternative group test
anosim_results = anosim(bc_dm, grouping, permutations=999)
print(f"ANOSIM: R={anosim_results['test statistic']:.3f}, "
      f"p={anosim_results['p-value']:.4f}")

# PERMDISP — test homogeneity of dispersions
permdisp_results = permdisp(bc_dm, grouping, permutations=999)

# Mantel test — correlation between distance matrices
r, p_value, n = mantel(bc_dm, jaccard_dm, method='pearson', permutations=999)
print(f"Mantel: r={r:.3f}, p={p_value:.4f}")
```

### 7. File I/O

```python
import skbio

# Read various formats
seq = skbio.DNA.read('input.fasta', format='fasta')
tree = skbio.TreeNode.read('tree.nwk')
dm = skbio.DistanceMatrix.read('distances.txt')

# Memory-efficient reading (generator for large files)
for seq in skbio.io.read('large.fasta', format='fasta', constructor=skbio.DNA):
    print(f"{seq.metadata['id']}: {len(seq)} bp")

# Write and convert formats
seq.write('output.fasta', format='fasta')
seqs = list(skbio.io.read('input.fastq', format='fastq', constructor=skbio.DNA))
skbio.io.write(seqs, format='fasta', into='output.fasta')
```

### 8. Distance Matrices

```python
from skbio import DistanceMatrix
import numpy as np

# Create from array
data = np.array([[0, 1, 2], [1, 0, 3], [2, 3, 0]])
dm = DistanceMatrix(data, ids=['A', 'B', 'C'])

# Access and slice
print(f"A-B distance: {dm['A', 'B']}")
subset = dm.filter(['A', 'C'])
condensed = dm.condensed_form()  # scipy-compatible
df = dm.to_data_frame()
print(f"Shape: {df.shape}")
```

## Key Concepts

### Data Structures

- **DNA/RNA/Protein**: Validated biological sequence objects with metadata (sequence-level, positional per-base, interval regions)
- **TabularMSA**: Multiple sequence alignment as a table; supports consensus, conservation, position entropy
- **TreeNode**: Phylogenetic tree with traversal, pruning, rerooting, distance calculations
- **DistanceMatrix**: Symmetric distance matrix with ID-based indexing; integrates with ordination and stats
- **Table**: BIOM feature table (samples × features) for microbiome count data; interoperates with pandas, polars, AnnData

### Phylogenetic vs Non-Phylogenetic Diversity

| Metric Type | Non-Phylogenetic | Phylogenetic (requires tree) |
|-------------|-----------------|------------------------------|
| Alpha diversity | Shannon, Simpson, observed_otus, Pielou's evenness | Faith's PD |
| Beta diversity | Bray-Curtis, Jaccard | Unweighted UniFrac, Weighted UniFrac |

### Counts Must Be Integers

Diversity functions require **integer abundance counts**, not relative frequencies. If you have proportions, multiply back:
```python
# Wrong: relative abundance
# counts = np.array([0.1, 0.5, 0.4])
# Correct: integer counts
counts = np.array([10, 50, 40])
```

## Common Workflows

### Workflow 1: Microbiome Diversity Analysis

```python
import skbio
from skbio import TreeNode
from skbio.diversity import alpha_diversity, beta_diversity
from skbio.stats.ordination import pcoa
from skbio.stats.distance import permanova
import numpy as np

# 1. Load data
counts = np.loadtxt('otu_table.tsv', delimiter='\t', dtype=int, skiprows=1)
sample_ids = ['S1', 'S2', 'S3', 'S4', 'S5', 'S6']
feature_ids = ['OTU1', 'OTU2', 'OTU3', 'OTU4']
tree = TreeNode.read('phylogeny.nwk')
grouping = ['control', 'control', 'control', 'treatment', 'treatment', 'treatment']

# 2. Alpha diversity
shannon = alpha_diversity('shannon', counts, ids=sample_ids)
faith = alpha_diversity('faith_pd', counts, ids=sample_ids,
                        tree=tree, otu_ids=feature_ids)
print(f"Mean Shannon - Control: {shannon[:3].mean():.2f}, "
      f"Treatment: {shannon[3:].mean():.2f}")

# 3. Beta diversity + PCoA
unifrac_dm = beta_diversity('unweighted_unifrac', counts,
                            ids=sample_ids, tree=tree, otu_ids=feature_ids)
pcoa_results = pcoa(unifrac_dm)
print(f"PC1: {pcoa_results.proportion_explained.iloc[0]:.1%} variance")

# 4. Statistical testing
results = permanova(unifrac_dm, grouping, permutations=999)
print(f"PERMANOVA p={results['p-value']:.4f}")
```

### Workflow 2: Phylogenetic Tree Construction

```python
from skbio import DNA, DistanceMatrix
from skbio.tree import nj
from skbio.alignment import local_pairwise_align_ssw
import numpy as np

# 1. Read sequences
seqs = list(skbio.io.read('sequences.fasta', format='fasta', constructor=DNA))
n = len(seqs)
print(f"Loaded {n} sequences")

# 2. Compute pairwise distances (Hamming-like via alignment scores)
dist_data = np.zeros((n, n))
for i in range(n):
    for j in range(i+1, n):
        _, score, _ = local_pairwise_align_ssw(seqs[i], seqs[j])
        max_len = max(len(seqs[i]), len(seqs[j]))
        dist_data[i, j] = dist_data[j, i] = 1 - (score / max_len)

# 3. Build tree
ids = [s.metadata.get('id', f'seq{i}') for i, s in enumerate(seqs)]
dm = DistanceMatrix(dist_data, ids=ids)
tree = nj(dm)
print(tree.ascii_art())

# 4. Analyze tree
tree.write('output.nwk', format='newick')
cophenetic = tree.cophenetic_matrix()
print(f"Cophenetic matrix shape: {cophenetic.shape}")
```

### Workflow 3: Sequence Processing Pipeline

1. Read FASTQ sequences using generator (`skbio.io.read` with `constructor=DNA`)
2. Filter by quality scores from `positional_metadata['quality']`
3. Trim adapters using `find_with_regex()` and sequence slicing
4. Find motifs with `find_with_regex('ATG.{3}')`
5. Translate via `dna.transcribe().translate()`
6. Write output FASTA with `skbio.io.write()`

## Key Parameters

| Parameter | Function | Default | Effect |
|-----------|----------|---------|--------|
| `metric` | alpha/beta_diversity | Required | Diversity metric name (e.g., 'shannon', 'braycurtis') |
| `permutations` | permanova/anosim/mantel | 999 | Number of permutations; higher = more precise p-values |
| `tree` | alpha/beta_diversity | None | Required for phylogenetic metrics (Faith PD, UniFrac) |
| `otu_ids` | alpha/beta_diversity | None | Feature IDs mapping counts to tree tips |
| `method` | mantel | 'pearson' | Correlation method: 'pearson' or 'spearman' |
| `constructor` | io.read | None | Sequence class for parsing (DNA, RNA, Protein) |
| `format` | io.read/write | Auto | File format (fasta, fastq, newick, etc.) |
| `genetic_code` | translate | 1 | NCBI genetic code (1=standard, 11=bacterial) |
| `k` | kmer_frequencies | Required | k-mer length for frequency calculation |

## Best Practices

1. **Use generators for large files** — `skbio.io.read()` returns a generator; avoid `list()` on millions of sequences
2. **Use projected CRS for phylogenetic diversity** — always provide matching `tree` and `otu_ids`; prune tree to feature set with `tree.shear(feature_ids)`
3. **Pair PERMANOVA with PERMDISP** — PERMANOVA is sensitive to dispersion differences; run PERMDISP to check group homogeneity
4. **Use 999+ permutations** for publication-quality p-values; 99 only for exploratory analysis
5. **Use HDF5 BIOM format** over JSON for large feature tables (faster I/O, smaller files)
6. **Anti-pattern — relative abundance in diversity functions**: diversity functions require integer counts, not proportions. Convert back if needed
7. **Anti-pattern — small k for k-mer analysis**: k < 3 provides little discriminatory power; use k=5-7 for sequence comparison

## Common Recipes

### Recipe: Rarefaction Before Diversity

```python
from skbio.diversity import subsample_counts, alpha_diversity
import numpy as np

# Rarefy to minimum depth
min_depth = min(counts.sum(axis=1))
rarefied = np.array([subsample_counts(row, n=min_depth) for row in counts])
print(f"Rarefied to {min_depth} counts per sample")

# Calculate diversity on rarefied data
shannon = alpha_diversity('shannon', rarefied, ids=sample_ids)
```

### Recipe: Partial Beta Diversity (Large Datasets)

```python
from skbio.diversity import partial_beta_diversity
import itertools

# Only compute specific pairs (saves time on large matrices)
pairs = list(itertools.combinations(sample_ids[:10], 2))
partial_dm = partial_beta_diversity('braycurtis', counts,
                                    ids=sample_ids, id_pairs=pairs)
print(f"Computed {len(pairs)} pairwise distances")
```

### Recipe: BIOM Table Operations

```python
from skbio import Table
import numpy as np

# Read BIOM table
table = Table.read('feature_table.biom')
print(f"Samples: {table.shape[1]}, Features: {table.shape[0]}")

# Filter low-abundance features
filtered = table.filter(lambda row, id_, md: row.sum() > 10, axis='observation')

# Convert to pandas
df = table.to_dataframe()
# Normalize to relative abundance
rel_abundance = df.div(df.sum(axis=0), axis=1)
```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `ValueError: Ids must be unique` | Duplicate IDs in DistanceMatrix/sequences | Deduplicate IDs: `ids = list(dict.fromkeys(ids))` |
| `ValueError: Counts must be integers` | Relative abundance passed to diversity | Use integer counts; multiply back: `(proportions * 1000).astype(int)` |
| Memory error on large FASTA | Loading all sequences at once | Use generator: `for seq in skbio.io.read(...)` |
| Tree tip / OTU ID mismatch | Phylogenetic diversity fails | Prune tree: `tree = tree.shear(feature_ids)` |
| PERMANOVA p=0.001 but groups overlap in PCoA | Significant dispersion difference | Run `permdisp()` to check; PERMANOVA tests location AND dispersion |
| Wrong translation | Default genetic code (standard) used for bacteria | Set `genetic_code=11` for bacterial/archaeal sequences |
| Slow NJ tree construction | O(n³) for large n | Use GME or BME for >1000 taxa: `from skbio.tree import gme` |

## Bundled Resources

- `references/extended_api.md` — Extended API reference covering advanced alignment parameters (SSW, gap penalties, CIGAR), tree construction algorithms (NJ vs UPGMA vs GME/BME), BIOM table manipulation, protein embeddings, and integration patterns with QIIME 2, pandas, and scikit-learn

Not migrated from original: the original's single `api_reference.md` (749 lines) was condensed into `references/extended_api.md` with focus on capabilities not covered inline. Omitted content: basic examples duplicating Core API, verbose troubleshooting (covered in Troubleshooting table above).

## References

- scikit-bio documentation: https://scikit.bio/docs/latest/
- GitHub: https://github.com/scikit-bio/scikit-bio
- QIIME 2 forum: https://forum.qiime2.org

## Related Skills

- **scanpy-scrna-seq** — single-cell RNA-seq analysis (different data domain but shares ordination concepts)
- **statistical-analysis** — general statistical testing to complement ecological stats
- **matplotlib-scientific-plotting** — visualization of PCoA plots and diversity comparisons
