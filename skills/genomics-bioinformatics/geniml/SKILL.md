---
name: "geniml"
description: "Geniml is a Python library for genomic interval machine learning. Train and apply region2vec embeddings to convert BED file regions into numeric vectors, load and index genomic interval datasets for ML pipelines, search embedding spaces with BEDSpace, and evaluate embedding quality. Use for chromatin accessibility clustering, regulatory element classification, cross-sample region comparison, and building ML models on genomic intervals."
license: "BSD-2-Clause"
---

# Geniml: Genomic Interval Machine Learning

## Overview

Geniml is a Python library that bridges genomic interval biology and machine learning. It provides region2vec for learning dense vector representations of genomic regions from BED files, BEDSpace for nearest-neighbor search in embedding space, dataset classes for ML-ready genomic interval loading, and evaluation utilities for embedding quality. Geniml is designed for researchers who want to apply modern ML techniques to chromatin accessibility, histone modification, or other region-based genomic data.

## When to Use

- Learn dense embeddings of genomic regions from a collection of BED files to enable ML-based analysis (region2vec)
- Cluster chromatin accessibility peaks or histone modification sites by embedding similarity
- Search for genomic regions similar to a query region using approximate nearest-neighbor search (BEDSpace)
- Build training datasets for ML models from BED-format genomic intervals with a PyTorch-compatible interface
- Compare embedding quality across training runs or datasets using quantitative metrics
- Integrate genomic region representations into custom neural network architectures
- For basic BED file parsing and set operations without ML, use `gtars` or `pysam-genomic-files` instead

## Prerequisites

- **Python packages**: `geniml`, `torch`, `numpy`, `pandas`, `anndata`
- **Data requirements**: BED files (minimum 3 columns: chr, start, end); optionally a pre-built universe file
- **Environment**: Python 3.8+; GPU optional but recommended for region2vec training on large datasets

```bash
pip install geniml torch numpy pandas anndata
```

## Quick Start

```python
from geniml.region2vec import Region2VecExModel
from geniml.io import RegionSet

# Load a collection of BED files and train region2vec embeddings
region_sets = [RegionSet("sample1.bed"), RegionSet("sample2.bed"), RegionSet("sample3.bed")]
model = Region2VecExModel("path/to/universe.bed")
model.train(region_sets, epochs=10, batch_size=32)

# Get embedding for a specific region
embedding = model.encode("chr1", 1000000, 1500000)
print(f"Embedding shape: {embedding.shape}")
# Embedding shape: (100,)
```

## Core API

### Module 1: RegionSet — Genomic Interval I/O

Load BED files into geniml's primary data structure for downstream operations.

```python
from geniml.io import RegionSet

# Load a BED file
rs = RegionSet("peaks.bed")
print(f"Loaded {len(rs)} regions")
print(f"First region: {rs[0]}")          # Region object: chr, start, end
print(f"Chromosomes: {set(r.chr for r in rs)}")

# Convert to list of Region objects
regions = list(rs)
for r in regions[:3]:
    print(f"  {r.chr}:{r.start}-{r.end}")
```

```python
from geniml.io import RegionSet

# Create RegionSet from a list of (chr, start, end) tuples
regions_data = [
    ("chr1", 100000, 101000),
    ("chr1", 200000, 201500),
    ("chr2",  50000,  51200),
]
rs = RegionSet(regions_data)
print(f"RegionSet with {len(rs)} regions from list")

# Access by index
r = rs[0]
print(f"chr={r.chr}, start={r.start}, end={r.end}, width={r.end - r.start}")
```

### Module 2: Universe Building

A universe defines the set of consensus regions used as the vocabulary for region2vec. Build it from a collection of BED files.

```python
from geniml.universe import UniverseBuilder
from geniml.io import RegionSet

# Collect BED files representing diverse samples
bed_files = ["sample1.bed", "sample2.bed", "sample3.bed", "sample4.bed"]
region_sets = [RegionSet(f) for f in bed_files]

# Build universe (consensus non-overlapping regions)
builder = UniverseBuilder()
universe = builder.build(region_sets)

# Save universe to BED file
universe.to_bed("universe.bed")
print(f"Universe size: {len(universe)} consensus regions")
```

```python
from geniml.universe import UniverseBuilder
from geniml.io import RegionSet

# Build universe with custom parameters
builder = UniverseBuilder(
    fraction=0.5,    # Region must appear in >= 50% of samples to be included
    merge_dist=0,    # Merge adjacent regions within this distance (bp)
)
bed_files = [f"sample_{i}.bed" for i in range(1, 11)]
region_sets = [RegionSet(f) for f in bed_files]
universe = builder.build(region_sets)
print(f"Filtered universe: {len(universe)} regions (fraction >= 0.5)")
```

### Module 3: Region2Vec — Training Embeddings

Train word2vec-style embeddings on genomic regions, treating each BED file as a "document" and each region as a "word."

```python
from geniml.region2vec import Region2VecExModel
from geniml.io import RegionSet

# Initialize model with a pre-built universe
model = Region2VecExModel(universe="universe.bed", embedding_dim=100)

# Load training data (collection of BED files = corpus)
bed_files = [f"atac_{i}.bed" for i in range(1, 51)]
region_sets = [RegionSet(f) for f in bed_files]

# Train
model.train(
    region_sets,
    epochs=20,
    batch_size=64,
    window_size=5,
    min_count=1,
)
print("Training complete")

# Save trained model
model.save("region2vec_model/")
print("Model saved to region2vec_model/")
```

```python
from geniml.region2vec import Region2VecExModel

# Load a pre-trained model
model = Region2VecExModel.load("region2vec_model/")

# Encode a single genomic region
embedding = model.encode("chr1", 1_000_000, 1_500_000)
print(f"Single region embedding shape: {embedding.shape}")
# Single region embedding shape: (100,)

# Encode an entire BED file → matrix of region embeddings
from geniml.io import RegionSet
rs = RegionSet("query_peaks.bed")
embeddings = model.encode_region_set(rs)
print(f"BED file embeddings shape: {embeddings.shape}")
# BED file embeddings shape: (N_regions, 100)
```

### Module 4: BEDSpace — Embedding Nearest-Neighbor Search

Index a corpus of BED file embeddings for fast similarity search.

```python
from geniml.bedspace import BEDSpace
from geniml.region2vec import Region2VecExModel
from geniml.io import RegionSet

# Build a BEDSpace index from a set of BED files
model = Region2VecExModel.load("region2vec_model/")
bed_files = [f"dataset_{i}.bed" for i in range(1, 101)]
region_sets = [RegionSet(f) for f in bed_files]

bedspace = BEDSpace(model)
bedspace.fit(region_sets, labels=[f"dataset_{i}" for i in range(1, 101)])
bedspace.save("bedspace_index/")
print(f"BEDSpace index built with {len(region_sets)} datasets")
```

```python
from geniml.bedspace import BEDSpace
from geniml.io import RegionSet

# Load index and query
bedspace = BEDSpace.load("bedspace_index/")
query = RegionSet("query_sample.bed")

# Find top-k most similar datasets
results = bedspace.query(query, k=5)
for rank, (label, score) in enumerate(results, 1):
    print(f"  Rank {rank}: {label}  similarity={score:.4f}")
```

### Module 5: Genomic Interval Datasets for ML

PyTorch-compatible Dataset classes for training ML models on genomic intervals.

```python
from geniml.datasets import TokenizedBEDDataset
from torch.utils.data import DataLoader

# Create a tokenized dataset from multiple BED files + labels
bed_files = ["condition_A_rep1.bed", "condition_A_rep2.bed",
             "condition_B_rep1.bed", "condition_B_rep2.bed"]
labels   = [0, 0, 1, 1]

dataset = TokenizedBEDDataset(
    bed_files=bed_files,
    universe="universe.bed",
    labels=labels,
)
print(f"Dataset size: {len(dataset)} samples")

# Use with PyTorch DataLoader
loader = DataLoader(dataset, batch_size=8, shuffle=True)
for batch_tokens, batch_labels in loader:
    print(f"Batch tokens shape: {batch_tokens.shape}")
    print(f"Batch labels: {batch_labels}")
    break
```

```python
from geniml.datasets import RegionEmbeddingDataset
from geniml.region2vec import Region2VecExModel
import torch

# Pre-embed BED files and create a dataset for a classifier
model = Region2VecExModel.load("region2vec_model/")
bed_files = ["pos_1.bed", "pos_2.bed", "neg_1.bed", "neg_2.bed"]
labels    = [1, 1, 0, 0]

emb_dataset = RegionEmbeddingDataset(
    bed_files=bed_files,
    model=model,
    labels=labels,
    aggregation="mean",    # aggregate region embeddings per sample
)
X, y = emb_dataset[0]
print(f"Sample embedding shape: {X.shape}, label: {y}")
# Sample embedding shape: (100,), label: 1
```

### Module 6: Embedding Evaluation

Assess embedding quality using neighborhood overlap and intrinsic metrics.

```python
from geniml.eval import EmbeddingEvaluator
from geniml.region2vec import Region2VecExModel
from geniml.io import RegionSet

model = Region2VecExModel.load("region2vec_model/")
bed_files = [f"sample_{i}.bed" for i in range(1, 21)]
region_sets = [RegionSet(f) for f in bed_files]

evaluator = EmbeddingEvaluator(model)
metrics = evaluator.evaluate(region_sets)

print(f"Neighborhood overlap score: {metrics['neighborhood_overlap']:.4f}")
print(f"Silhouette score:           {metrics.get('silhouette', 'N/A')}")
# Higher neighborhood overlap → more biologically coherent embeddings
```

## Key Concepts

### region2vec Training Analogy

Region2vec treats each BED file as a "sentence" (a document of co-occurring genomic regions) and each genomic region token (from the universe) as a "word." Word2vec's skip-gram objective is applied: regions that frequently co-occur in BED files are learned to have similar embeddings. This means two regions that tend to be open/active in the same set of samples will have nearby embeddings, enabling meaningful similarity search without explicit labels.

```python
# Conceptual analogy: universe regions = vocabulary tokens
# BED file = sentence = [region_token_1, region_token_2, ...]
# Training: predict co-occurring regions within a sliding window
from geniml.io import RegionSet
rs = RegionSet("sample.bed")
print(f"This BED file contains {len(rs)} 'words' (tokens) from the universe vocabulary")
```

### Universe as Vocabulary

The universe is a non-overlapping, genome-wide set of consensus regions that serves as the token vocabulary for region2vec. A well-chosen universe should cover the genomic regions present in your dataset while being compact enough for efficient training. Regions in a BED file that do not overlap the universe are ignored during training.

## Common Workflows

### Workflow 1: Train and Search Embeddings from ATAC-seq Peaks

**Goal**: Embed ATAC-seq peak sets, then find samples most similar to a query.

```python
from geniml.universe import UniverseBuilder
from geniml.region2vec import Region2VecExModel
from geniml.bedspace import BEDSpace
from geniml.io import RegionSet
from pathlib import Path

# Step 1: Collect BED files
bed_dir = Path("atac_peaks/")
bed_files = sorted(bed_dir.glob("*.bed"))
region_sets = [RegionSet(str(f)) for f in bed_files]
labels = [f.stem for f in bed_files]
print(f"Loaded {len(region_sets)} ATAC-seq peak sets")

# Step 2: Build universe
builder = UniverseBuilder(fraction=0.3)
universe = builder.build(region_sets)
universe.to_bed("atac_universe.bed")
print(f"Universe: {len(universe)} regions")

# Step 3: Train region2vec
model = Region2VecExModel(universe="atac_universe.bed", embedding_dim=100)
model.train(region_sets, epochs=15, batch_size=64, window_size=5)
model.save("atac_region2vec/")

# Step 4: Build BEDSpace index
bedspace = BEDSpace(model)
bedspace.fit(region_sets, labels=labels)
bedspace.save("atac_bedspace/")

# Step 5: Query with a new sample
query = RegionSet("new_sample.bed")
results = bedspace.query(query, k=5)
print("Top 5 most similar samples:")
for rank, (label, score) in enumerate(results, 1):
    print(f"  {rank}. {label}  (similarity={score:.4f})")
```

### Workflow 2: ML Classification on Genomic Intervals

**Goal**: Train a logistic regression classifier on region2vec embeddings to classify cell types.

```python
from geniml.region2vec import Region2VecExModel
from geniml.datasets import RegionEmbeddingDataset
from geniml.io import RegionSet
from torch.utils.data import DataLoader
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_score
import numpy as np

model = Region2VecExModel.load("atac_region2vec/")

# Prepare labeled dataset (e.g., T-cell vs B-cell ATAC peaks)
bed_files = ["tcell_1.bed", "tcell_2.bed", "tcell_3.bed",
             "bcell_1.bed", "bcell_2.bed", "bcell_3.bed"]
labels    = [0, 0, 0, 1, 1, 1]

dataset = RegionEmbeddingDataset(
    bed_files=bed_files, model=model, labels=labels, aggregation="mean"
)

# Collect embeddings
X = np.array([dataset[i][0].numpy() for i in range(len(dataset))])
y = np.array([dataset[i][1]         for i in range(len(dataset))])
print(f"Feature matrix: {X.shape}, labels: {y}")

# Cross-validate a simple classifier
clf = LogisticRegression(max_iter=1000)
scores = cross_val_score(clf, X, y, cv=3, scoring="accuracy")
print(f"Cross-val accuracy: {scores.mean():.3f} ± {scores.std():.3f}")
```

## Key Parameters

| Parameter | Module | Default | Range / Options | Effect |
|-----------|--------|---------|-----------------|--------|
| `embedding_dim` | Region2Vec | `100` | `50`–`512` | Dimensionality of region embeddings; higher = more expressive but slower |
| `window_size` | Region2Vec training | `5` | `2`–`20` | Context window for skip-gram co-occurrence; larger = broader co-occurrence |
| `epochs` | Region2Vec training | `10` | `5`–`100` | Training iterations; increase for large datasets |
| `batch_size` | Region2Vec training | `32` | `16`–`512` | Mini-batch size; larger batches improve stability |
| `fraction` | UniverseBuilder | `0.5` | `0.0`–`1.0` | Minimum fraction of samples a region must appear in to enter the universe |
| `aggregation` | RegionEmbeddingDataset | `"mean"` | `"mean"`, `"sum"`, `"max"` | How per-region embeddings are pooled into a sample-level vector |
| `k` | BEDSpace query | `10` | `1`–corpus size | Number of nearest neighbors to return |

## Common Recipes

### Recipe: Load a Pre-Trained Hugging Face region2vec Model

When to use: Apply a community-trained model without local training.

```python
from geniml.region2vec import Region2VecExModel

# Load a pre-trained model from HuggingFace Hub
model = Region2VecExModel("databio/r2v-ChIP-atlas-hg38-v2")
print(f"Model embedding dim: {model.embedding_dim}")

from geniml.io import RegionSet
rs = RegionSet("my_peaks.bed")
embeddings = model.encode_region_set(rs)
print(f"Embeddings shape: {embeddings.shape}")
```

### Recipe: UMAP Visualization of Sample Embeddings

When to use: Visually inspect clustering of samples in embedding space.

```python
from geniml.region2vec import Region2VecExModel
from geniml.io import RegionSet
import numpy as np

model = Region2VecExModel.load("atac_region2vec/")

bed_files = [f"sample_{i}.bed" for i in range(1, 21)]
sample_embeddings = []
for f in bed_files:
    rs = RegionSet(f)
    emb = model.encode_region_set(rs)
    sample_embeddings.append(emb.mean(axis=0))   # mean-pool regions

X = np.array(sample_embeddings)
print(f"Sample embedding matrix: {X.shape}")

try:
    import umap
    import matplotlib.pyplot as plt
    reducer = umap.UMAP(n_components=2, random_state=42)
    X_2d = reducer.fit_transform(X)
    plt.figure(figsize=(6, 5))
    plt.scatter(X_2d[:, 0], X_2d[:, 1], s=40)
    for i, f in enumerate(bed_files):
        plt.annotate(f, (X_2d[i, 0], X_2d[i, 1]), fontsize=7)
    plt.title("Sample embeddings (UMAP)")
    plt.savefig("sample_umap.png", dpi=150, bbox_inches="tight")
    print("Saved sample_umap.png")
except ImportError:
    print("Install umap-learn for UMAP visualization")
```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `FileNotFoundError` on universe | Universe BED path incorrect or not built yet | Run `UniverseBuilder.build()` and save with `.to_bed()` before training |
| All embeddings identical or near-zero | Universe has no overlap with training BED files | Verify BED coordinate system matches universe (hg38 vs hg19, chr prefix) |
| `RuntimeError: CUDA out of memory` | Batch size too large for GPU | Reduce `batch_size` or use CPU training |
| Very low neighborhood overlap score | Too few training samples or too many epochs (overfitting) | Use ≥20 BED files; tune `epochs`; try smaller `embedding_dim` |
| BEDSpace query returns no results | Query regions not present in index universe | Check query BED overlaps universe; use `fraction` parameter to broaden universe |
| Slow training | Large universe + many BED files | Reduce universe size with higher `fraction` threshold; use GPU |

## Related Skills

- **gtars** — fast BED file I/O and interval operations for preprocessing before geniml training
- **scanpy-scrna-seq** — downstream clustering and UMAP visualization of embeddings stored in AnnData

## References

- [Geniml documentation](https://geniml.databio.org/) — official docs and tutorials
- [Geniml GitHub repository](https://github.com/databio/geniml) — source code and examples
- [PyPI: geniml](https://pypi.org/project/geniml/) — installation and version info
- [HuggingFace: databio region2vec models](https://huggingface.co/databio) — pre-trained region2vec model collection
