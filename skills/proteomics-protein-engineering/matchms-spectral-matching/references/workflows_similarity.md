# Matchms Similarity Functions & Extended Workflows

Detailed similarity scoring methods and extended workflow examples for mass spectrometry analysis.

## Similarity Functions

### Peak-Based Similarity

#### CosineGreedy

Fast cosine similarity using greedy peak matching. Peaks are matched within a specified tolerance, and similarity is computed based on matched peak intensities. The greedy algorithm matches peaks in order of decreasing intensity product, which is fast but not guaranteed optimal.

**Parameters:**
- `tolerance` (float, default=0.1): Maximum m/z difference for peak matching (Daltons)
- `mz_power` (float, default=0.0): Exponent for m/z weighting (0 = no weighting)
- `intensity_power` (float, default=1.0): Exponent for intensity weighting

**Output:** Tuple of (similarity score 0.0-1.0, number of matched peaks).

**When to use:** General-purpose spectral matching; large datasets where speed is prioritized over mathematically optimal matching.

#### CosineHungarian

Cosine similarity using the Hungarian algorithm for optimal peak matching. Provides mathematically optimal peak assignments but is significantly slower than CosineGreedy. Guarantees the best possible matching score.

**Parameters:** Same as CosineGreedy (`tolerance`, `mz_power`, `intensity_power`).

**Output:** Tuple of (optimal similarity score 0.0-1.0, number of matched peaks).

**When to use:** High-quality reference library comparisons; research requiring reproducible, mathematically rigorous results. Use for smaller datasets or when accuracy is critical over speed.

#### ModifiedCosine

Extends cosine similarity by accounting for precursor m/z differences between spectra. Allows peaks to match after applying a mass shift based on the difference between precursor masses. This is particularly useful for comparing spectra of related compounds such as isotopes, adducts, or structural analogs.

**Parameters:** Same as CosineGreedy (`tolerance`, `mz_power`, `intensity_power`).

**When to use:** Comparing spectra from different precursor masses; identifying structural analogs, derivatives, or isotopes; cross-ionization mode comparisons.

**Requirement:** Both spectra must have valid `precursor_mz` metadata.

#### NeutralLossesCosine

Calculates similarity based on neutral loss patterns rather than fragment m/z values. Neutral losses are derived by subtracting fragment m/z from precursor m/z. This captures fragmentation mechanism similarity even when fragment masses differ due to different precursor masses.

**Parameters:** Same as CosineGreedy (`tolerance`, `mz_power`, `intensity_power`).

**When to use:** Comparing fragmentation patterns across different precursor masses; metabolite identification and classification; complementary to regular cosine scoring.

**Requirements:** Both spectra need valid `precursor_mz`; apply `add_losses()` filter before scoring.

```python
from matchms.filtering import add_losses
from matchms.similarity import NeutralLossesCosine
spectra_with_losses = [add_losses(s) for s in spectra]
scores = calculate_scores(refs_with_losses, queries_with_losses, NeutralLossesCosine(tolerance=0.1))
```

### Structural Similarity

#### FingerprintSimilarity

Compares molecular fingerprints derived from chemical structures (SMILES or InChI). Measures structural rather than spectral similarity, useful for combining with spectral scores or pre-filtering candidates.

**Parameters:**
- `fingerprint_type` (str, default="daylight"): Fingerprint algorithm
  - `"daylight"`: Daylight topological fingerprint
  - `"morgan1"`, `"morgan2"`, `"morgan3"`: Morgan circular fingerprints with radius 1, 2, or 3
- `similarity_measure` (str, default="jaccard"): Similarity metric
  - `"jaccard"`: Jaccard index (intersection / union)
  - `"dice"`: Dice coefficient (2 * intersection / (size1 + size2))
  - `"cosine"`: Cosine similarity between fingerprint vectors

**When to use:** Structural similarity without spectral data; combining structural and spectral similarity; pre-filtering candidates before spectral matching; structure-activity relationship studies.

**Requirements:** Spectra must have valid SMILES or InChI; apply `add_fingerprint()` first; requires rdkit.

```python
from matchms.filtering import add_fingerprint
from matchms.similarity import FingerprintSimilarity
spectra_fp = [add_fingerprint(s, fingerprint_type="morgan2", nbits=2048) for s in spectra]
scores = calculate_scores(refs_fp, queries_fp, FingerprintSimilarity(similarity_measure="jaccard"))
```

### Metadata-Based Similarity

#### MetadataMatch

Compares user-defined metadata fields. Supports exact and tolerance-based matching.

- `field` (str): Metadata field name to compare
- `matching_type` (default="exact"): `"exact"` (returns 1.0/0.0), `"difference"`, `"relative_difference"`
- `tolerance` (float, optional): Maximum difference for numerical matching

```python
from matchms.similarity import MetadataMatch
# Exact: instrument type
scores = calculate_scores(refs, queries, MetadataMatch(field="instrument_type", matching_type="exact"))
# Numerical: retention time within 0.5 min
scores = calculate_scores(refs, queries, MetadataMatch(field="retention_time", matching_type="difference", tolerance=0.5))
```

#### PrecursorMzMatch

Binary matching based on precursor m/z values. Returns True/False based on whether precursor masses match within specified tolerance. Ideal for fast candidate pre-filtering before expensive spectral similarity calculations.

**Parameters:**
- `tolerance` (float, default=0.1): Maximum m/z difference for matching
- `tolerance_type` (str, default="Dalton"): `"Dalton"` (absolute) or `"ppm"` (parts per million, relative)

**Output:** 1.0 (match) or 0.0 (no match). Requires valid `precursor_mz` on both spectra.

```python
from matchms.similarity import PrecursorMzMatch
# Dalton tolerance
scores = calculate_scores(refs, queries, PrecursorMzMatch(tolerance=0.1, tolerance_type="Dalton"))
# PPM tolerance for high-resolution data
scores = calculate_scores(refs, queries, PrecursorMzMatch(tolerance=10, tolerance_type="ppm"))
```

#### ParentMassMatch

Binary matching based on parent mass (neutral mass) values. Similar to PrecursorMzMatch but uses calculated parent mass instead of precursor m/z, making it adduct-independent.

**Parameters:** Same as PrecursorMzMatch (`tolerance`, `tolerance_type`).

**Output:** 1.0 (match) or 0.0 (no match). Requires valid `parent_mass` metadata.

**When to use:** Comparing spectra from different ionization modes; adduct-independent matching; neutral mass-based library searches.

## Score Access Patterns

```python
scores = calculate_scores(references, queries, CosineGreedy())

best_matches = scores.scores_by_query(query_spectrum, sort=True)[:10]   # top 10 per query
matching = scores.scores_by_reference(ref_spectrum, sort=True)[:10]     # top 10 per reference
score_array = scores.scores                                             # full N x M numpy array
df = scores.to_dataframe()                                              # pandas DataFrame
high = [(i, j, s) for i, j, s in scores.to_list() if s > 0.7]         # threshold filter
scores.to_json("scores.json"); scores.to_pickle("scores.pkl")           # persistence
```

## Extended Workflows

### Workflow: Multi-Metric Similarity Scoring

Combine cosine, modified cosine, neutral losses, and fingerprint similarity with weighted scoring.

```python
from matchms import calculate_scores
from matchms.filtering import (default_filters, normalize_intensities,
    derive_inchi_from_smiles, add_fingerprint, add_losses)
from matchms.similarity import (CosineGreedy, ModifiedCosine,
    NeutralLossesCosine, FingerprintSimilarity)

def process_multimetric(spectrum):
    spectrum = default_filters(spectrum)
    spectrum = normalize_intensities(spectrum)
    spectrum = derive_inchi_from_smiles(spectrum)
    spectrum = add_fingerprint(spectrum, fingerprint_type="morgan2", nbits=2048)
    spectrum = add_losses(spectrum, loss_mz_from=5.0, loss_mz_to=200.0)
    return spectrum

proc_lib = [s for s in (process_multimetric(s) for s in library) if s is not None]
proc_qry = [s for s in (process_multimetric(s) for s in queries) if s is not None]

cosine = calculate_scores(proc_lib, proc_qry, CosineGreedy(tolerance=0.1))
mod_cos = calculate_scores(proc_lib, proc_qry, ModifiedCosine(tolerance=0.1))
neutral = calculate_scores(proc_lib, proc_qry, NeutralLossesCosine(tolerance=0.1))
fp = calculate_scores(proc_lib, proc_qry, FingerprintSimilarity(similarity_measure="jaccard"))

# Weighted combination
for i, query in enumerate(proc_qry):
    combined = [(j, 0.4*cosine.scores[j,i] + 0.3*mod_cos.scores[j,i]
                    + 0.2*neutral.scores[j,i] + 0.1*fp.scores[j,i])
                for j in range(len(proc_lib))]
    combined.sort(key=lambda x: x[1], reverse=True)
    for ref_idx, s in combined[:3]:
        print(f"  {query.get('compound_name','?')} -> {proc_lib[ref_idx].get('compound_name','?')}: {s:.4f}")
```

### Workflow: Large-Scale Library Comparison

Chunked processing for memory management when comparing large libraries.

```python
from matchms.importing import load_from_mgf
from matchms.filtering import default_filters, normalize_intensities
from matchms import calculate_scores
from matchms.similarity import CosineGreedy
import pandas as pd

lib1 = [normalize_intensities(default_filters(s)) for s in load_from_mgf("library1.mgf")]
lib2 = [normalize_intensities(default_filters(s)) for s in load_from_mgf("library2.mgf")]

chunk_size, threshold, similar_pairs = 500, 0.8, []
for i0 in range(0, len(lib1), chunk_size):
    for j0 in range(0, len(lib2), chunk_size):
        chunk1, chunk2 = lib1[i0:i0+chunk_size], lib2[j0:j0+chunk_size]
        scores = calculate_scores(chunk1, chunk2, CosineGreedy(tolerance=0.1))
        for i, s1 in enumerate(chunk1):
            for j, s2 in enumerate(chunk2):
                if scores.scores[i, j] >= threshold:
                    similar_pairs.append({'lib1': s1.get("compound_name","?"),
                        'lib2': s2.get("compound_name","?"), 'score': scores.scores[i,j]})
    print(f"  Processed rows {i0}-{i0+len(chunk1)} of {len(lib1)}")

pd.DataFrame(similar_pairs).sort_values('score', ascending=False).to_csv("comparison.csv", index=False)
```

### Workflow: Automated Compound Identification Report

Structured identification report with confidence levels using pandas.

```python
from matchms.importing import load_from_mgf
from matchms.filtering import default_filters, normalize_intensities
from matchms import calculate_scores
from matchms.similarity import CosineGreedy, ModifiedCosine
import pandas as pd

def identify_compounds(query_file, library_file, output_csv="report.csv"):
    queries = [normalize_intensities(default_filters(s)) for s in load_from_mgf(query_file)]
    library = [normalize_intensities(default_filters(s)) for s in load_from_mgf(library_file)]
    cosine = calculate_scores(library, queries, CosineGreedy())
    modified = calculate_scores(library, queries, ModifiedCosine())

    results = []
    for i, q in enumerate(queries):
        for rank, (lib_idx, cos_score) in enumerate(cosine.scores_by_query(q, sort=True)[:5], 1):
            ref = library[lib_idx]
            results.append({'Query': q.get("compound_name", f"Unknown_{i}"),
                'Rank': rank, 'Match': ref.get("compound_name", f"Ref_{lib_idx}"),
                'Cosine': cos_score, 'ModCosine': modified.scores[lib_idx, i],
                'Confidence': 'High' if cos_score >= 0.7 else 'Moderate' if cos_score >= 0.5 else 'Low'})

    df = pd.DataFrame(results)
    df.to_csv(output_csv, index=False)
    for level in ['High', 'Moderate', 'Low']:
        print(f"  {level}: {len(df[df['Confidence'] == level])}")
    return df
```

### Workflow: Ion Mode-Specific Processing

Separate positive/negative mode spectra with mode-specific analysis.

```python
from matchms.importing import load_from_mgf
from matchms.filtering import default_filters, normalize_intensities, derive_ionmode
from matchms.exporting import save_as_mgf
from matchms import calculate_scores
from matchms.similarity import CosineGreedy

spectra = list(load_from_mgf("mixed_modes.mgf"))
groups = {"positive": [], "negative": [], "unknown": []}
for s in spectra:
    s = normalize_intensities(derive_ionmode(default_filters(s)))
    mode = s.get("ionmode", "unknown")
    groups.get(mode, groups["unknown"]).append(s)

for mode in ["positive", "negative"]:
    specs = groups[mode]
    print(f"{mode}: {len(specs)} spectra")
    if len(specs) > 1:
        calculate_scores(specs, specs, CosineGreedy(tolerance=0.1))
    save_as_mgf(specs, f"{mode}_mode.mgf")
```

### Workflow: Metadata Enrichment and Validation

Enrich spectra with chemical annotations and report validation statistics.

```python
from matchms.importing import load_from_mgf
from matchms.exporting import save_as_mgf
from matchms.filtering import (default_filters, derive_inchi_from_smiles,
    derive_inchikey_from_inchi, derive_smiles_from_inchi,
    add_fingerprint, repair_not_matching_annotation, require_valid_annotation)

spectra = list(load_from_mgf("spectra.mgf"))
enriched, failures = [], []
for i, s in enumerate(spectra):
    s = default_filters(s)
    s = derive_inchi_from_smiles(s)
    s = derive_inchikey_from_inchi(s)
    s = derive_smiles_from_inchi(s)
    s = repair_not_matching_annotation(s)
    s = add_fingerprint(s, fingerprint_type="morgan2", nbits=2048)
    v = require_valid_annotation(s)
    (enriched if v else failures).append(v or i)

print(f"Enriched: {len(enriched)}, Failed: {len([f for f in failures if isinstance(f, int)])}")
save_as_mgf([e for e in enriched if e is not None], "enriched_spectra.mgf")
```

## Performance Considerations

**Speed tiers:**
- **Fast** (suitable for large datasets): CosineGreedy, PrecursorMzMatch, ParentMassMatch, MetadataMatch
- **Slow** (use for smaller datasets or high accuracy): CosineHungarian, ModifiedCosine, NeutralLossesCosine, FingerprintSimilarity (requires fingerprint computation)

**Memory management:**
- `calculate_scores` creates an N x M matrix in memory. For large datasets (>10,000 spectra), this can exceed available RAM
- Use chunked processing (see Large-Scale Library Comparison workflow) to manage memory
- Consider pre-filtering candidates by PrecursorMzMatch to reduce the effective matrix size

**Score threshold guidelines:**
- > 0.7: High confidence match -- likely the same compound
- 0.5 - 0.7: Moderate confidence -- manual review recommended, may be structural analog
- < 0.5: Low confidence -- likely different compounds

**Optimization strategy:** For large-scale library searches, use PrecursorMzMatch or ParentMassMatch to pre-filter candidates, then apply CosineGreedy or ModifiedCosine only to filtered results. This can reduce computation by 90%+ for diverse libraries.

## Best Practices

1. **Process queries and references identically** -- same filter pipeline for both sets
2. **Save intermediate results** -- pickle format for fast reloading of processed spectra
3. **Monitor memory** -- generators or chunked processing for large comparisons
4. **Combine multiple metrics** -- multi-metric scoring provides more robust identification
5. **Filter by precursor mass first** -- dramatically speeds up large library searches
6. **Document your pipeline** -- save processing parameters for reproducibility
7. **Choose appropriate methods** -- CosineGreedy for speed, CosineHungarian for accuracy, ModifiedCosine for analogs

---

> **Condensation note**: Condensed from originals: similarity.md (381 lines) + workflows.md (648 lines) = 1,029 lines. Retained: all 8 similarity functions with parameters, score access patterns, 5 extended workflows, performance considerations, best practices. Relocated to SKILL.md: CosineGreedy/ModifiedCosine/CosineHungarian/FingerprintSimilarity core usage (Core API Module 3); similarity comparison table (Key Concepts); library matching + QC workflows (Common Workflows). Omitted from similarity.md: individual similarity function examples duplicating Core API Module 3. Omitted from workflows.md: basic library matching (in SKILL.md Workflow 1), basic QC (in SKILL.md Workflow 2), format conversion (in SKILL.md Workflow 3), network-based spectral clustering (requires external spec2vec tool), spectra visualization tutorial (covered by spectrum.plot() in Core API Module 1).
