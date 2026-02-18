---
name: matchms-spectral-matching
description: Mass spectrometry spectral matching and metabolite identification with matchms. Use for importing spectra (mzML, MGF, MSP, JSON), filtering/normalizing peaks, computing spectral similarity (cosine, modified cosine, fingerprint), building reproducible processing pipelines, and identifying unknown metabolites from spectral libraries. For full LC-MS/MS proteomics pipelines, use pyopenms instead.
license: Apache-2.0
---

# Matchms — Spectral Matching & Metabolite Identification

## Overview

Matchms is a Python library for mass spectrometry data processing focused on spectral similarity calculation and compound identification. It provides multi-format I/O, 50+ spectrum filters for metadata harmonization and peak processing, 8 similarity scoring functions, and a pipeline framework for reproducible analytical workflows.

## When to Use

- Identifying unknown metabolites by matching MS/MS spectra against reference libraries
- Computing spectral similarity scores (cosine, modified cosine, fingerprint-based)
- Processing and standardizing mass spectral data from multiple formats (mzML, MGF, MSP, JSON)
- Building reproducible spectral processing pipelines for quality control
- Harmonizing metadata across spectral databases (compound names, SMILES, InChI, adducts)
- Large-scale spectral library comparisons and duplicate detection
- For full LC-MS/MS proteomics workflows (feature detection, protein ID), use **pyopenms** instead
- For chemical structure similarity without mass spectra, use **rdkit** fingerprint comparison

## Prerequisites

```bash
uv pip install matchms numpy pandas
# For chemical structure processing (SMILES, InChI, fingerprints):
uv pip install matchms[chemistry]
```

- Python 3.8+; NumPy for peak array operations
- Input: spectral data in MGF, MSP, mzML, mzXML, JSON, or pickle format
- Reference library in any supported format for matching

## Quick Start

```python
from matchms.importing import load_from_mgf
from matchms.filtering import default_filters, normalize_intensities
from matchms.filtering import select_by_relative_intensity, require_minimum_number_of_peaks
from matchms import calculate_scores
from matchms.similarity import CosineGreedy

# Load and process query spectra
queries = list(load_from_mgf("queries.mgf"))
queries = [default_filters(s) for s in queries]
queries = [normalize_intensities(s) for s in queries if s is not None]
queries = [require_minimum_number_of_peaks(s, n_required=5) for s in queries if s is not None]

# Load reference library
refs = list(load_from_mgf("library.mgf"))
refs = [default_filters(s) for s in refs]
refs = [normalize_intensities(s) for s in refs if s is not None]

# Calculate similarity scores
scores = calculate_scores(references=refs, queries=queries,
                          similarity_function=CosineGreedy(tolerance=0.1))
# Get best matches for first query
best = scores.scores_by_query(queries[0], sort=True)[:5]
for match, score_tuple in best:
    print(f"Score: {score_tuple['score']:.3f}, Matches: {score_tuple['matches']}")
```

## Core API

### Module 1: Spectrum I/O

Import spectra from multiple file formats and export processed data.

```python
from matchms.importing import (load_from_mgf, load_from_mzml, load_from_msp,
                                load_from_json, load_from_mzxml, load_from_pickle,
                                load_from_usi)
from matchms.exporting import save_as_mgf, save_as_msp, save_as_json, save_as_pickle

# Import from various formats (returns generators)
spectra_mgf = list(load_from_mgf("library.mgf"))
spectra_mzml = list(load_from_mzml("data.mzML"))
spectra_msp = list(load_from_msp("nist_library.msp"))
spectra_json = list(load_from_json("gnps_spectra.json"))
print(f"Loaded: MGF={len(spectra_mgf)}, mzML={len(spectra_mzml)}")

# Export processed spectra
save_as_mgf(spectra_mgf, "processed.mgf")
save_as_json(spectra_mgf, "processed.json")
save_as_pickle(spectra_mgf, "spectra.pickle")  # Fast for intermediate results

# Pickle for large datasets (fastest I/O)
from matchms.importing import load_from_pickle
spectra = list(load_from_pickle("spectra.pickle"))
```

```python
from matchms import Spectrum
import numpy as np

# Create spectrum manually
mz = np.array([100.0, 150.0, 200.0, 250.0, 300.0])
intensities = np.array([0.1, 0.5, 0.9, 0.3, 0.7])
metadata = {
    "precursor_mz": 325.5,
    "ionmode": "positive",
    "compound_name": "Caffeine",
    "smiles": "CN1C=NC2=C1C(=O)N(C(=O)N2C)C"
}
spectrum = Spectrum(mz=mz, intensities=intensities, metadata=metadata)

# Access spectrum data
print(f"Peaks: {spectrum.peaks.mz}")
print(f"Precursor: {spectrum.get('precursor_mz')}")
print(f"Name: {spectrum.get('compound_name')}")

# Visualize
spectrum.plot()
```

### Module 2: Spectrum Filtering & Processing

Apply metadata harmonization and peak processing filters. Matchms provides 50+ filters.

```python
from matchms.filtering import (
    default_filters, normalize_intensities,
    select_by_relative_intensity, select_by_mz,
    require_minimum_number_of_peaks, reduce_to_number_of_peaks,
    remove_peaks_around_precursor_mz, add_losses
)

# default_filters applies: metadata cleanup, charge correction, adduct parsing
spectrum = default_filters(spectrum)

# Peak normalization (max intensity → 1.0)
spectrum = normalize_intensities(spectrum)

# Filter peaks by relative intensity (remove noise below 1%)
spectrum = select_by_relative_intensity(spectrum, intensity_from=0.01, intensity_to=1.0)

# Filter peaks by m/z range
spectrum = select_by_mz(spectrum, mz_from=50.0, mz_to=500.0)

# Keep top N peaks only
spectrum = reduce_to_number_of_peaks(spectrum, n_max=50)

# Remove peaks near precursor (common contaminants)
spectrum = remove_peaks_around_precursor_mz(spectrum, mz_tolerance=17.0)

# Require minimum peaks for matching
spectrum = require_minimum_number_of_peaks(spectrum, n_required=5)

# Add neutral losses (useful for NeutralLossesCosine)
spectrum = add_losses(spectrum)

if spectrum is not None:
    print(f"After filtering: {len(spectrum.peaks.mz)} peaks")
```

```python
# Chemical annotation filters (require matchms[chemistry])
from matchms.filtering import (
    derive_inchi_from_smiles, derive_inchikey_from_inchi,
    derive_smiles_from_inchi, add_fingerprint,
    repair_inchi_inchikey_smiles, require_valid_annotation
)

# Derive chemical identifiers from SMILES
spectrum = derive_inchi_from_smiles(spectrum)
spectrum = derive_inchikey_from_inchi(spectrum)

# Add molecular fingerprint for structural similarity
spectrum = add_fingerprint(spectrum, fingerprint_type="morgan", nbits=2048)

# Validate annotations
spectrum = require_valid_annotation(spectrum)
if spectrum is not None:
    print(f"InChIKey: {spectrum.get('inchikey')}")
```

### Module 3: Similarity Scoring

Compare spectra using multiple similarity metrics.

```python
from matchms import calculate_scores
from matchms.similarity import (
    CosineGreedy, CosineHungarian, ModifiedCosine,
    NeutralLossesCosine, FingerprintSimilarity,
    MetadataMatch, PrecursorMzMatch
)

# CosineGreedy — fast peak matching (greedy algorithm)
scores = calculate_scores(references=library, queries=unknowns,
                          similarity_function=CosineGreedy(tolerance=0.1))

# ModifiedCosine — accounts for precursor mass differences (best for analog search)
scores = calculate_scores(references=library, queries=unknowns,
                          similarity_function=ModifiedCosine(tolerance=0.1))

# CosineHungarian — optimal peak matching (slower but more accurate)
scores = calculate_scores(references=library, queries=unknowns,
                          similarity_function=CosineHungarian(tolerance=0.1))

# NeutralLossesCosine — similarity based on neutral loss patterns
scores = calculate_scores(references=library, queries=unknowns,
                          similarity_function=NeutralLossesCosine(tolerance=0.1))

# Access results
for i, query in enumerate(unknowns[:3]):
    best_matches = scores.scores_by_query(query, sort=True)[:3]
    print(f"\nQuery {i}: precursor_mz={query.get('precursor_mz')}")
    for ref, score_tuple in best_matches:
        print(f"  {ref.get('compound_name', 'Unknown')}: "
              f"score={score_tuple['score']:.3f}, matches={score_tuple['matches']}")
```

```python
# FingerprintSimilarity — structural similarity (requires fingerprints)
from matchms.similarity import FingerprintSimilarity
scores = calculate_scores(references=library, queries=unknowns,
                          similarity_function=FingerprintSimilarity(
                              similarity_measure="jaccard"))

# PrecursorMzMatch — fast mass-based pre-filtering
from matchms.similarity import PrecursorMzMatch
scores = calculate_scores(references=library, queries=unknowns,
                          similarity_function=PrecursorMzMatch(tolerance=0.1))

# Multi-metric scoring: combine peak + structural similarity
cosine_scores = calculate_scores(references=library, queries=unknowns,
                                  similarity_function=CosineGreedy(tolerance=0.1))
fp_scores = calculate_scores(references=library, queries=unknowns,
                              similarity_function=FingerprintSimilarity())
```

### Module 4: Processing Pipelines

Build reusable, reproducible multi-step processing workflows.

```python
from matchms import SpectrumProcessor
from matchms.filtering import (
    default_filters, normalize_intensities,
    select_by_relative_intensity, require_minimum_number_of_peaks,
    remove_peaks_around_precursor_mz, add_losses
)

# Define reusable pipeline
pipeline = SpectrumProcessor([
    default_filters,
    normalize_intensities,
    lambda s: select_by_relative_intensity(s, intensity_from=0.01),
    lambda s: remove_peaks_around_precursor_mz(s, mz_tolerance=17.0),
    lambda s: require_minimum_number_of_peaks(s, n_required=5),
    add_losses
])

# Apply to all spectra (filters returning None remove the spectrum)
processed = [pipeline(s) for s in raw_spectra]
processed = [s for s in processed if s is not None]
print(f"Processed: {len(processed)}/{len(raw_spectra)} spectra retained")
```

## Key Concepts

### Similarity Function Comparison

| Function | Speed | Accuracy | Best For |
|----------|-------|----------|----------|
| `CosineGreedy` | Fast | Good | General library matching |
| `CosineHungarian` | Slow | Best | Small comparisons, validation |
| `ModifiedCosine` | Fast | Good | Analog search (different precursors) |
| `NeutralLossesCosine` | Medium | Good | Structural class identification |
| `FingerprintSimilarity` | Fast | Moderate | Structure-based pre-filtering |
| `PrecursorMzMatch` | Fastest | N/A | Mass-based pre-filtering |

### Filter Categories

| Category | Examples | Purpose |
|----------|----------|---------|
| **Metadata cleanup** | `default_filters`, `clean_compound_name`, `clean_adduct` | Standardize metadata fields |
| **Chemical derivation** | `derive_inchi_from_smiles`, `add_fingerprint` | Compute chemical identifiers |
| **Mass/charge** | `add_precursor_mz`, `correct_charge`, `add_parent_mass` | Fix and validate mass info |
| **Peak normalization** | `normalize_intensities`, `select_by_relative_intensity` | Scale and filter peaks |
| **Peak reduction** | `reduce_to_number_of_peaks`, `remove_peaks_around_precursor_mz` | Remove noise/artifacts |
| **Quality control** | `require_minimum_number_of_peaks`, `require_precursor_mz` | Enforce minimum quality |
| **Neutral losses** | `add_losses` | Compute precursor-fragment losses |

### Score Tuple Structure

All similarity functions return `(score, matches)`:
- `score`: float 0.0–1.0 (cosine similarity value)
- `matches`: int (number of matched peaks between query and reference)

Higher scores and more matched peaks indicate better matches. Typical thresholds: score > 0.7 and matches > 6 for confident identifications.

## Common Workflows

### Workflow 1: Library Matching for Metabolite Identification

```python
from matchms.importing import load_from_mgf
from matchms.filtering import default_filters, normalize_intensities
from matchms.filtering import select_by_relative_intensity, require_minimum_number_of_peaks
from matchms import calculate_scores
from matchms.similarity import ModifiedCosine
import pandas as pd

# Load and process both queries and library identically
def process_spectra(spectra):
    processed = []
    for s in spectra:
        s = default_filters(s)
        if s is None: continue
        s = normalize_intensities(s)
        s = select_by_relative_intensity(s, intensity_from=0.01)
        s = require_minimum_number_of_peaks(s, n_required=5)
        if s is not None:
            processed.append(s)
    return processed

queries = process_spectra(load_from_mgf("unknowns.mgf"))
library = process_spectra(load_from_mgf("reference_library.mgf"))
print(f"Queries: {len(queries)}, Library: {len(library)}")

# Score all query-reference pairs
scores = calculate_scores(references=library, queries=queries,
                          similarity_function=ModifiedCosine(tolerance=0.1))

# Extract best matches
results = []
for query in queries:
    best = scores.scores_by_query(query, sort=True)[:1]
    if best:
        ref, score_tuple = best[0]
        results.append({
            "query_precursor_mz": query.get("precursor_mz"),
            "match_name": ref.get("compound_name", "Unknown"),
            "match_smiles": ref.get("smiles", ""),
            "score": score_tuple["score"],
            "matched_peaks": score_tuple["matches"]
        })

df = pd.DataFrame(results)
confident = df[df["score"] > 0.7]
print(f"Confident matches (score>0.7): {len(confident)}/{len(df)}")
df.to_csv("identification_results.csv", index=False)
```

### Workflow 2: Quality Control and Data Cleaning

```python
from matchms.importing import load_from_msp
from matchms.exporting import save_as_mgf
from matchms import SpectrumProcessor
from matchms.filtering import (
    default_filters, normalize_intensities,
    select_by_relative_intensity, require_minimum_number_of_peaks,
    require_precursor_mz, add_parent_mass
)

# Define QC pipeline
qc_pipeline = SpectrumProcessor([
    default_filters,
    require_precursor_mz,
    add_parent_mass,
    normalize_intensities,
    lambda s: select_by_relative_intensity(s, intensity_from=0.001),
    lambda s: require_minimum_number_of_peaks(s, n_required=3)
])

# Process and filter
raw = list(load_from_msp("raw_library.msp"))
cleaned = [qc_pipeline(s) for s in raw]
cleaned = [s for s in cleaned if s is not None]

print(f"Input: {len(raw)}, Output: {len(cleaned)} ({len(cleaned)/len(raw)*100:.1f}% retained)")
save_as_mgf(cleaned, "cleaned_library.mgf")
```

### Workflow 3: Format Conversion

1. Load spectra from source format (Core API Module 1 — `load_from_mzml`)
2. Apply `default_filters` for metadata harmonization (Core API Module 2)
3. Export to target format (Core API Module 1 — `save_as_mgf`)

## Key Parameters

| Parameter | Function/Module | Default | Range/Options | Effect |
|-----------|----------------|---------|---------------|--------|
| `tolerance` | CosineGreedy/ModifiedCosine | 0.1 | 0.005–0.5 Da | m/z tolerance for peak matching |
| `mz_power` | CosineGreedy | 0.0 | 0.0–2.0 | Weight of m/z in scoring (0=ignore) |
| `intensity_power` | CosineGreedy | 1.0 | 0.0–2.0 | Weight of intensity in scoring |
| `intensity_from` | select_by_relative_intensity | 0.0 | 0.0–1.0 | Minimum relative intensity to keep |
| `n_required` | require_minimum_number_of_peaks | 10 | 1–100 | Minimum peaks to retain spectrum |
| `n_max` | reduce_to_number_of_peaks | 100 | 10–500 | Maximum peaks to retain |
| `mz_tolerance` | remove_peaks_around_precursor_mz | 17.0 | 0.5–50 Da | Window around precursor to remove |
| `fingerprint_type` | add_fingerprint | "daylight" | "daylight"/"morgan"/"maccs" | Molecular fingerprint type |
| `nbits` | add_fingerprint | 2048 | 256–4096 | Fingerprint bit vector length |

## Best Practices

1. **Always process queries and references identically** — apply the same filtering pipeline to both sets to avoid systematic bias in similarity scores
2. **Save intermediate results in pickle** — pickle format is fastest for re-loading; use MGF/MSP for sharing with other tools
3. **Pre-filter by precursor mass** — for large libraries, use `PrecursorMzMatch` first to reduce the comparison space, then score with `CosineGreedy`
4. **Combine multiple metrics** — use both CosineGreedy (peak matching) and FingerprintSimilarity (structure) for more robust identification
5. **Check for None after filtering** — filters return `None` when a spectrum fails quality requirements. Always filter: `[s for s in processed if s is not None]`
6. **Use ModifiedCosine for analog search** — when querying against libraries that may not have the exact compound, ModifiedCosine handles precursor mass differences

## Common Recipes

### Recipe 1: Precursor-Filtered Library Search (Efficient)

```python
from matchms import calculate_scores
from matchms.similarity import PrecursorMzMatch, CosineGreedy

# Step 1: Fast mass filter
mass_scores = calculate_scores(references=library, queries=unknowns,
                                similarity_function=PrecursorMzMatch(tolerance=0.5))

# Step 2: Detailed scoring only for mass-matched pairs
cosine = CosineGreedy(tolerance=0.1)
for query in unknowns:
    candidates = mass_scores.scores_by_query(query, sort=True)
    mass_matched = [ref for ref, score in candidates if score["score"] > 0]
    if mass_matched:
        detailed = calculate_scores(references=mass_matched, queries=[query],
                                     similarity_function=cosine)
        best = detailed.scores_by_query(query, sort=True)[:3]
        for ref, s in best:
            print(f"{ref.get('compound_name')}: {s['score']:.3f}")
```

### Recipe 2: Ion Mode-Specific Processing

```python
from matchms.importing import load_from_mgf
from matchms.filtering import default_filters, normalize_intensities

spectra = list(load_from_mgf("mixed_library.mgf"))
spectra = [default_filters(s) for s in spectra]
spectra = [s for s in spectra if s is not None]

# Separate by ion mode
positive = [s for s in spectra if s.get("ionmode") == "positive"]
negative = [s for s in spectra if s.get("ionmode") == "negative"]
print(f"Positive: {len(positive)}, Negative: {len(negative)}")

# Process each mode with mode-specific filtering
positive = [normalize_intensities(s) for s in positive]
negative = [normalize_intensities(s) for s in negative]
```

### Recipe 3: Metadata Enrichment Report

```python
import pandas as pd
from matchms.importing import load_from_mgf
from matchms.filtering import default_filters

spectra = [default_filters(s) for s in load_from_mgf("library.mgf")]
spectra = [s for s in spectra if s is not None]

# Extract metadata summary
rows = []
for s in spectra:
    rows.append({
        "compound_name": s.get("compound_name", ""),
        "precursor_mz": s.get("precursor_mz"),
        "ionmode": s.get("ionmode", ""),
        "smiles": s.get("smiles", ""),
        "inchikey": s.get("inchikey", ""),
        "num_peaks": len(s.peaks.mz)
    })

df = pd.DataFrame(rows)
print(f"Library: {len(df)} spectra")
print(f"Named: {(df.compound_name != '').sum()}")
print(f"With SMILES: {(df.smiles != '').sum()}")
print(f"Ion modes: {df.ionmode.value_counts().to_dict()}")
```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| All scores are 0.0 | No matching peaks within tolerance | Increase `tolerance` (try 0.2–0.5 Da); verify both spectra have peaks |
| Low scores despite same compound | Different fragmentation conditions | Use `ModifiedCosine` instead of `CosineGreedy`; check ion mode consistency |
| Many spectra filtered to None | Too strict quality filters | Lower `n_required` in `require_minimum_number_of_peaks`; relax intensity thresholds |
| `KeyError` on metadata field | Field name not harmonized | Apply `default_filters` first to harmonize metadata keys |
| Memory error with large library | All-vs-all comparison | Pre-filter by precursor mass (`PrecursorMzMatch`) before detailed scoring |
| `add_fingerprint` fails | RDKit not installed | Install chemistry extras: `pip install matchms[chemistry]` |
| Import returns empty list | Wrong file format or path | Verify format matches loader (MGF for `.mgf`, MSP for `.msp`); check file is not empty |
| Inconsistent scores between runs | Different processing pipelines | Use `SpectrumProcessor` to ensure identical processing for queries and references |

## Bundled Resources

- **references/filtering_catalog.md** — Complete catalog of 50+ matchms filter functions organized by category (metadata processing, chemical structure, mass/charge, peak processing, quality control).
  - Covers: all filter function signatures with parameters and brief descriptions, common filter combinations
  - Relocated inline: key filters (default_filters, normalize_intensities, select_by_relative_intensity, reduce_to_number_of_peaks, remove_peaks_around_precursor_mz, add_fingerprint) in Core API Module 2; filter category summary in Key Concepts
  - Omitted: individual filter examples duplicating Core API patterns

- **references/workflows_similarity.md** — Extended workflows and detailed similarity function documentation consolidated from two original references.
  - Covers: all 8 similarity functions with parameter tables, large-scale comparison strategies, multi-metric scoring patterns, 7 extended workflows (library matching, QC, multi-metric, format conversion, metadata enrichment, large-scale comparison, automated identification report), performance considerations
  - Relocated inline: CosineGreedy/ModifiedCosine/CosineHungarian/FingerprintSimilarity usage in Core API Module 3; similarity comparison table in Key Concepts; library matching + QC workflows in Common Workflows
  - Omitted: network-based spectral clustering workflow — requires external tool (spec2vec); spectra visualization tutorial — covered by `spectrum.plot()` in Core API Module 1

**Disposition of original reference files:**
- importing_exporting.md (417 lines) → fully consolidated into Core API Module 1 (I/O functions, format list, Spectrum creation, pickle usage). Retained: all 7 import functions, 4 export functions, Spectrum class creation, format selection guidance. Omitted: USI detailed examples — niche use case
- filtering.md (289 lines) → migrated as references/filtering_catalog.md with key filters relocated to Core API Module 2
- similarity.md (381 lines) → consolidated into references/workflows_similarity.md with core functions in Core API Module 3
- workflows.md (648 lines) → consolidated into references/workflows_similarity.md with top workflows in Common Workflows

## Related Skills

- **pyopenms-mass-spectrometry** — full LC-MS/MS proteomics and metabolomics pipelines (feature detection, protein ID)
- **rdkit-cheminformatics** — molecular fingerprint generation and chemical structure similarity

## References

- matchms documentation: https://matchms.readthedocs.io
- Huber et al. (2020) matchms — processing and similarity scoring of mass spectrometry data. *Journal of Open Source Software*, DOI: 10.21105/joss.02411
- GitHub: https://github.com/matchms/matchms
