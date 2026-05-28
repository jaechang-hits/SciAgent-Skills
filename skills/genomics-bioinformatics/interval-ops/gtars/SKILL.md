---
name: "gtars"
description: "Rust-backed Python library for fast genomic token arithmetic and BED processing. High-performance BED I/O, interval set ops (intersect, merge, complement, subtract), region tokenization against a universe, universe construction. Use for preprocessing large BED collections and ML token vocabularies."
license: "MIT"
---

# GTARS: Fast Genomic Token Arithmetic and BED File Processing

## Overview

GTARS is a Python library with a Rust-backed core for high-performance genomic interval operations. It provides BED file I/O, set-theoretic interval operations (intersection, union, merge, complement, subtract), genomic region tokenization against a reference universe, and utilities for building consensus universe BED files. GTARS is designed for workflows that process hundreds to thousands of BED files efficiently, serving as a preprocessing engine for ML pipelines (including geniml) and general bioinformatics pipelines.

## When to Use

- Read and write large BED files efficiently, leveraging Rust-backed parsing for speed over pure Python alternatives
- Compute genomic interval intersections, merges, complements, or subtracts between BED file pairs or sets
- Tokenize a collection of genomic regions against a fixed universe vocabulary for ML input preparation
- Build consensus universe BED files from a collection of sample BED files
- Count overlap statistics between two BED files without launching bedtools processes
- Preprocess ATAC-seq, ChIP-seq, or ENCODE peak files before feeding into geniml or other ML tools
- For full BED/BAM/SAM reading with CIGAR-level detail, use `pysam-genomic-files` instead

## Prerequisites

- **Python packages**: `gtars`, `numpy` (optional, for array conversion)
- **Data requirements**: BED format files (3+ columns: chr, start, end); optionally a universe BED file for tokenization
- **Environment**: Python 3.8+; Rust toolchain not required (pre-built wheels available on PyPI)

```bash
pip install gtars
```

## Quick Start

```python
from gtars import GenomicIntervalSet

# Load a BED file and inspect
gis = GenomicIntervalSet("peaks.bed")
print(f"Loaded {len(gis)} intervals")
print(f"First interval: {gis[0]}")
# First interval: chr1:1000-2000

# Intersect two BED files
gis2 = GenomicIntervalSet("other_peaks.bed")
overlap = gis.intersect(gis2)
print(f"Overlapping intervals: {len(overlap)}")
```

## Core API

### Module 1: GenomicIntervalSet — BED File I/O

Primary data structure for loading, indexing, and writing genomic intervals.

```python
from gtars import GenomicIntervalSet

# Load from file
gis = GenomicIntervalSet("peaks.bed")
print(f"Intervals loaded: {len(gis)}")
print(f"Chromosomes present: {gis.chromosomes}")

# Access by index
interval = gis[0]
print(f"chr={interval.chr}, start={interval.start}, end={interval.end}")

# Iterate all intervals
for iv in gis:
    width = iv.end - iv.start
    if width > 5000:
        print(f"Wide interval: {iv.chr}:{iv.start}-{iv.end} ({width} bp)")
        break
```

```python
from gtars import GenomicIntervalSet, GenomicInterval

# Create from a list of GenomicInterval objects
intervals = [
    GenomicInterval("chr1", 100, 500),
    GenomicInterval("chr1", 600, 1200),
    GenomicInterval("chr2", 300, 800),
]
gis = GenomicIntervalSet(intervals)
print(f"Created GenomicIntervalSet with {len(gis)} intervals")

# Write to BED file
gis.to_bed("output_intervals.bed")
print("Saved output_intervals.bed")
```

### Module 2: Interval Set Operations

Compute intersections, unions, merges, subtracts, and complements between BED sets.

```python
from gtars import GenomicIntervalSet

peaks_a = GenomicIntervalSet("condition_A.bed")
peaks_b = GenomicIntervalSet("condition_B.bed")

# Intersection: intervals present in both sets
shared = peaks_a.intersect(peaks_b)
print(f"Shared intervals: {len(shared)}")

# Subtraction: intervals in A not overlapping B
a_only = peaks_a.subtract(peaks_b)
print(f"A-specific intervals: {len(a_only)}")

# Union (merge both sets, then merge overlapping)
combined = peaks_a.union(peaks_b)
print(f"Union intervals: {len(combined)}")
```

```python
from gtars import GenomicIntervalSet

# Merge overlapping/adjacent intervals within a single set
gis = GenomicIntervalSet("fragmented_peaks.bed")
print(f"Before merge: {len(gis)} intervals")

merged = gis.merge()
print(f"After merge:  {len(merged)} intervals")

# Complement: genome-wide intervals NOT covered by peaks
# Requires chromosome sizes
chrom_sizes = {"chr1": 248956422, "chr2": 242193529, "chrX": 156040895}
complement = gis.complement(chrom_sizes)
print(f"Complement (uncovered) intervals: {len(complement)}")
```

### Module 3: Tokenization

Convert genomic intervals to integer token IDs against a reference universe vocabulary.

```python
from gtars import Tokenizer

# Initialize tokenizer with a universe BED file
tokenizer = Tokenizer("universe.bed")
print(f"Universe vocabulary size: {len(tokenizer)}")

# Tokenize a single BED file → list of token IDs
from gtars import GenomicIntervalSet
gis = GenomicIntervalSet("sample_peaks.bed")
tokens = tokenizer.tokenize(gis)
print(f"Token IDs: {tokens[:10]} ...")
print(f"Total tokens: {len(tokens)}")
```

```python
from gtars import Tokenizer, GenomicIntervalSet

tokenizer = Tokenizer("universe.bed")

# Tokenize and convert to numpy array for ML
import numpy as np
gis = GenomicIntervalSet("sample_peaks.bed")
tokens = tokenizer.tokenize(gis)
token_array = np.array(tokens)
print(f"Token array shape: {token_array.shape}, dtype: {token_array.dtype}")

# Build a binary presence/absence vector over the full universe
vocab_size = len(tokenizer)
presence_vector = np.zeros(vocab_size, dtype=np.float32)
presence_vector[token_array] = 1.0
print(f"Presence vector shape: {presence_vector.shape}")
print(f"Fraction of universe covered: {presence_vector.mean():.4f}")
```

### Module 4: Universe Building

Construct a consensus non-overlapping universe from a collection of BED files.

```python
from gtars import UniverseBuilder

# Build universe from multiple BED files
bed_files = ["sample_1.bed", "sample_2.bed", "sample_3.bed", "sample_4.bed"]
builder = UniverseBuilder()
universe = builder.build(bed_files)

print(f"Universe regions: {len(universe)}")
universe.to_bed("consensus_universe.bed")
print("Saved consensus_universe.bed")
```

```python
from gtars import UniverseBuilder

# Build with coverage threshold (region must appear in >= N% of samples)
bed_files = [f"chip_{i}.bed" for i in range(1, 21)]
builder = UniverseBuilder(fraction=0.25)   # present in >= 25% of samples
universe = builder.build(bed_files)
print(f"Universe (fraction>=0.25): {len(universe)} regions")

# Compare thresholds
for frac in [0.1, 0.25, 0.5]:
    b = UniverseBuilder(fraction=frac)
    u = b.build(bed_files)
    print(f"  fraction={frac}: {len(u)} regions")
```

### Module 5: Interval Statistics and Utilities

Compute coverage, overlap counts, and basic statistics over BED files.

```python
from gtars import GenomicIntervalSet

gis = GenomicIntervalSet("peaks.bed")

# Basic statistics
widths = [iv.end - iv.start for iv in gis]
import numpy as np
print(f"Interval count:       {len(gis)}")
print(f"Mean width (bp):      {np.mean(widths):.1f}")
print(f"Median width (bp):    {np.median(widths):.1f}")
print(f"Total coverage (bp):  {sum(widths):,}")

# Per-chromosome counts
from collections import Counter
chrom_counts = Counter(iv.chr for iv in gis)
for chrom, count in sorted(chrom_counts.items())[:5]:
    print(f"  {chrom}: {count} intervals")
```

```python
from gtars import GenomicIntervalSet

# Overlap count matrix between two sets
peaks_a = GenomicIntervalSet("condition_A.bed")
peaks_b = GenomicIntervalSet("condition_B.bed")

# Count how many intervals in A overlap at least one interval in B
overlapping_a = peaks_a.intersect(peaks_b)
pct_overlap = len(overlapping_a) / len(peaks_a) * 100
print(f"A intervals overlapping B: {len(overlapping_a)}/{len(peaks_a)} ({pct_overlap:.1f}%)")

# Filter peaks by minimum width
min_width = 200
filtered = GenomicIntervalSet([iv for iv in peaks_a if (iv.end - iv.start) >= min_width])
print(f"Peaks >= {min_width} bp: {len(filtered)}/{len(peaks_a)}")
filtered.to_bed("filtered_peaks.bed")
```

## Key Concepts

### Tokenization and Universe Vocabulary

GTARS tokenization maps genomic regions to integer indices by finding the universe region that best overlaps each query interval. If a query interval does not overlap any universe region, it receives a special out-of-vocabulary (OOV) token. This vocabulary approach is analogous to NLP tokenization and enables treating genomic intervals as discrete tokens for transformer- and embedding-based models.

```python
from gtars import Tokenizer, GenomicIntervalSet

tokenizer = Tokenizer("universe.bed")
# OOV token index is typically 0 or len(tokenizer)
print(f"OOV token ID: {tokenizer.unknown_token}")
gis = GenomicIntervalSet("test.bed")
tokens = tokenizer.tokenize(gis)
oov_count = sum(1 for t in tokens if t == tokenizer.unknown_token)
print(f"OOV rate: {oov_count}/{len(tokens)} ({oov_count/len(tokens)*100:.1f}%)")
```

## Common Workflows

### Workflow 1: BED File Preprocessing Pipeline

**Goal**: Load raw ATAC-seq peaks, filter by width, merge overlaps, and tokenize for ML.

```python
from gtars import GenomicIntervalSet, GenomicInterval, Tokenizer
import numpy as np

# Step 1: Load peaks
peaks = GenomicIntervalSet("atac_peaks_raw.bed")
print(f"Raw peaks: {len(peaks)}")

# Step 2: Filter by minimum width (remove very short noise peaks)
min_width = 150
filtered_intervals = [iv for iv in peaks if (iv.end - iv.start) >= min_width]
peaks_filtered = GenomicIntervalSet(filtered_intervals)
print(f"After width filter (>={min_width} bp): {len(peaks_filtered)}")

# Step 3: Merge overlapping peaks
peaks_merged = peaks_filtered.merge()
print(f"After merge: {len(peaks_merged)}")
peaks_merged.to_bed("atac_peaks_processed.bed")

# Step 4: Tokenize against universe
tokenizer = Tokenizer("universe.bed")
tokens = tokenizer.tokenize(peaks_merged)
token_array = np.array(tokens)
print(f"Token array: {token_array.shape}, OOV rate: {(token_array == tokenizer.unknown_token).mean():.3f}")

# Step 5: Build presence vector for ML input
vocab_size = len(tokenizer)
presence = np.zeros(vocab_size, dtype=np.float32)
valid_tokens = token_array[token_array != tokenizer.unknown_token]
presence[valid_tokens] = 1.0
np.save("sample_presence_vector.npy", presence)
print(f"Saved presence vector: {presence.shape}, coverage={presence.mean():.4f}")
```

### Workflow 2: Batch BED File Statistics

**Goal**: Compute overlap and coverage statistics across a collection of BED files.

```python
from gtars import GenomicIntervalSet
from pathlib import Path
import pandas as pd
import numpy as np

bed_dir = Path("chip_peaks/")
bed_files = sorted(bed_dir.glob("*.bed"))
reference = GenomicIntervalSet("reference_regions.bed")

records = []
for bed_file in bed_files:
    gis = GenomicIntervalSet(str(bed_file))
    widths = [iv.end - iv.start for iv in gis]
    overlap = gis.intersect(reference)
    records.append({
        "sample":          bed_file.stem,
        "n_peaks":         len(gis),
        "mean_width_bp":   np.mean(widths),
        "total_coverage_bp": sum(widths),
        "overlap_with_ref": len(overlap),
        "pct_overlap":     len(overlap) / len(gis) * 100 if len(gis) > 0 else 0,
    })

df = pd.DataFrame(records)
print(df.to_string(index=False))
df.to_csv("bed_file_statistics.csv", index=False)
print(f"\nSaved bed_file_statistics.csv ({len(df)} samples)")
```

### Workflow 3: Build Universe and Tokenize Corpus

**Goal**: From scratch — build a universe from a BED corpus and tokenize all files.

```python
from gtars import UniverseBuilder, Tokenizer, GenomicIntervalSet
from pathlib import Path
import numpy as np

bed_dir = Path("atac_peaks/")
bed_files = [str(f) for f in sorted(bed_dir.glob("*.bed"))]
print(f"Building universe from {len(bed_files)} BED files...")

# Build universe
builder = UniverseBuilder(fraction=0.2)
universe = builder.build(bed_files)
universe.to_bed("corpus_universe.bed")
print(f"Universe: {len(universe)} regions → corpus_universe.bed")

# Tokenize all BED files
tokenizer = Tokenizer("corpus_universe.bed")
vocab_size = len(tokenizer)
print(f"Tokenizer vocab size: {vocab_size}")

presence_matrix = []
for f in bed_files:
    gis = GenomicIntervalSet(f)
    tokens = np.array(tokenizer.tokenize(gis))
    presence = np.zeros(vocab_size, dtype=np.float32)
    valid = tokens[tokens != tokenizer.unknown_token]
    presence[valid] = 1.0
    presence_matrix.append(presence)

X = np.stack(presence_matrix)
print(f"Presence matrix: {X.shape}  (samples × universe_regions)")
np.save("corpus_presence_matrix.npy", X)
print("Saved corpus_presence_matrix.npy")
```

## Key Parameters

| Parameter | Module | Default | Range / Options | Effect |
|-----------|--------|---------|-----------------|--------|
| `fraction` | UniverseBuilder | `0.5` | `0.0`–`1.0` | Minimum fraction of samples a region must appear in to enter universe |
| `merge_dist` | merge() | `0` | `≥0` bp | Merge intervals within this distance; `0` merges only overlapping/touching |
| `min_overlap` | intersect() | `1` bp | `1`–region width | Minimum overlap length required to count as an intersection |
| OOV token | Tokenizer | `tokenizer.unknown_token` | — | Token ID for regions not overlapping any universe region |
| Chromosome sizes | complement() | required dict | `{chr: length}` | Genome-wide sizes used to compute uncovered complement intervals |

## Common Recipes

### Recipe: Filter BED File by Chromosome List

When to use: Remove non-canonical chromosomes (patches, alternative contigs) before analysis.

```python
from gtars import GenomicIntervalSet, GenomicInterval

gis = GenomicIntervalSet("raw_peaks.bed")
canonical_chroms = {f"chr{i}" for i in list(range(1, 23)) + ["X", "Y", "M"]}
filtered = GenomicIntervalSet([iv for iv in gis if iv.chr in canonical_chroms])
filtered.to_bed("canonical_peaks.bed")
print(f"Canonical peaks: {len(filtered)}/{len(gis)}")
```

### Recipe: Compute Pairwise Jaccard Similarity Between BED Sets

When to use: Measure similarity between two peak sets without external tools.

```python
from gtars import GenomicIntervalSet

def jaccard(a: GenomicIntervalSet, b: GenomicIntervalSet) -> float:
    intersection = len(a.intersect(b))
    union = len(a.union(b))
    return intersection / union if union > 0 else 0.0

peaks_a = GenomicIntervalSet("sample_a.bed")
peaks_b = GenomicIntervalSet("sample_b.bed")
j = jaccard(peaks_a, peaks_b)
print(f"Jaccard similarity: {j:.4f}")
```

## Expected Outputs

- **GenomicIntervalSet**: iterable of `GenomicInterval` objects with `.chr`, `.start`, `.end`
- **BED files**: written via `.to_bed()` — 3-column tab-separated (chr, start, end)
- **Token arrays**: `list[int]` from `tokenizer.tokenize()` — convert with `np.array(tokens)`
- **Presence vectors**: `np.ndarray` of shape `(vocab_size,)` built from token IDs
- **Universe BED**: non-overlapping consensus regions written via `universe.to_bed()`

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `ImportError: gtars` | Package not installed | `pip install gtars`; check Python version ≥ 3.8 |
| All intervals report OOV token | BED coordinate system mismatch | Verify both BED and universe use same genome assembly and `chr` prefix convention |
| `intersect` returns empty set | Non-overlapping chromosomes or shifted coordinates | Check chromosome names match exactly (e.g., `chr1` vs `1`) |
| Very large universe (>5M regions) | Low `fraction` threshold with many short samples | Increase `fraction` to 0.3–0.5; pre-filter BED files to remove noise peaks |
| `to_bed()` produces unsorted output | Intervals added in arbitrary order | Sort output: `sorted_gis = GenomicIntervalSet(sorted(gis, key=lambda r: (r.chr, r.start)))` |
| Memory error on large BED collections | Holding all intervals in memory | Process files in batches; use streaming/chunked loading if available |

## Related Skills

- **geniml** — uses GTARS-built universes and tokenizers for region2vec training and BEDSpace indexing
- **pysam-genomic-files** — for BAM/SAM/VCF-level access with CIGAR and read-level detail

## References

- [GTARS GitHub repository](https://github.com/databio/gtars) — source, issue tracker, and changelog
- [PyPI: gtars](https://pypi.org/project/gtars/) — installation instructions and version history
- [Geniml documentation](https://geniml.databio.org/) — ecosystem context; GTARS is the preprocessing engine for geniml
