---
name: pyopenms-mass-spectrometry
description: MS data processing with PyOpenMS for LC-MS/MS proteomics and metabolomics — mzML/mzXML I/O, signal processing (smoothing, peak picking, centroiding), feature detection/linking, peptide/protein ID with FDR, untargeted metabolomics. Use matchms for simple spectral matching.
license: BSD-3-Clause
---

# PyOpenMS — Mass Spectrometry Analysis

## Overview

PyOpenMS provides Python bindings to the OpenMS C++ library for computational mass spectrometry. It supports proteomics and metabolomics data processing including file I/O for 10+ MS formats, signal processing, feature detection, peptide/protein identification, and quantitative analysis across samples.

## When to Use

- Processing raw LC-MS/MS data (mzML, mzXML) for proteomics or metabolomics
- Detecting chromatographic features and linking them across multiple samples
- Identifying peptides and proteins from MS/MS search engine results with FDR control
- Running untargeted metabolomics workflows (peak picking → feature detection → alignment → annotation)
- Converting between mass spectrometry file formats (mzML, mzXML, featureXML, idXML)
- Smoothing, filtering, and centroiding raw spectral data
- For simple spectral library matching and metabolite identification, use **matchms** instead
- For protein sequence analysis (not mass spec), use **biopython** instead

## Prerequisites

```bash
uv pip install pyopenms numpy pandas matplotlib
```

- Python 3.8+; NumPy for peak array operations
- Input data: mzML files (standard MS format), FASTA databases (for identification)
- All algorithms follow a consistent pattern: `algo = Algorithm(); params = algo.getParameters(); params.setValue(...); algo.setParameters(params)`

## Quick Start

```python
import pyopenms as ms

# Load mzML file
exp = ms.MSExperiment()
ms.MzMLFile().load("sample.mzML", exp)
print(f"Spectra: {exp.getNrSpectra()}, Chromatograms: {exp.getNrChromatograms()}")

# Examine first spectrum
spec = exp.getSpectrum(0)
mz, intensity = spec.get_peaks()
print(f"MS level: {spec.getMSLevel()}, RT: {spec.getRT():.2f}s, Peaks: {len(mz)}")

# Quick preprocessing: smooth + centroid
gauss = ms.GaussFilter()
p = gauss.getParameters(); p.setValue("gaussian_width", 0.1); gauss.setParameters(p)
gauss.filterExperiment(exp)

picker = ms.PeakPickerHiRes()
centroided = ms.MSExperiment()
picker.pickExperiment(exp, centroided)
print(f"Centroided spectra: {centroided.getNrSpectra()}")
```

## Core API

### Module 1: File I/O & Data Access

Read and write mass spectrometry data in multiple formats.

```python
import pyopenms as ms

# Read mzML (standard MS format)
exp = ms.MSExperiment()
ms.MzMLFile().load("data.mzML", exp)

# Indexed access for large files (memory-efficient)
loader = ms.IndexedMzMLFileLoader()
indexed_file = ms.OnDiscMSExperiment()
loader.load("large_data.mzML", indexed_file)
spec = indexed_file.getSpectrum(0)  # Load single spectrum on demand
print(f"Total spectra: {indexed_file.getNrSpectra()}")

# Read identification results (idXML)
protein_ids, peptide_ids = [], []
ms.IdXMLFile().load("results.idXML", protein_ids, peptide_ids)
print(f"Peptide IDs: {len(peptide_ids)}, Protein IDs: {len(protein_ids)}")

# Read feature map
fm = ms.FeatureMap()
ms.FeatureXMLFile().load("features.featureXML", fm)
print(f"Features: {fm.size()}")
```

```python
# Write mzML with compression
exp_out = ms.MSExperiment()
# ... populate experiment ...
ms.MzMLFile().store("output.mzML", exp_out)

# Read FASTA database
entries = []
ms.FASTAFile().load("database.fasta", entries)
print(f"Proteins in DB: {len(entries)}")
for e in entries[:3]:
    print(f"  {e.identifier}: {e.sequence[:30]}...")
```

**Supported formats**: mzML, mzXML, mzData (spectra); featureXML, consensusXML (features); idXML, mzIdentML, pepXML (identifications); TraML (transitions); mzTab (results); FASTA (sequences)

### Module 2: Signal Processing & Peak Picking

Preprocess raw spectral data for downstream analysis.

```python
import pyopenms as ms

exp = ms.MSExperiment()
ms.MzMLFile().load("raw.mzML", exp)

# Gaussian smoothing
gauss = ms.GaussFilter()
p = gauss.getParameters()
p.setValue("gaussian_width", 0.15)  # m/z width
gauss.setParameters(p)
gauss.filterExperiment(exp)

# Savitzky-Golay smoothing (alternative)
sg = ms.SavitzkyGolayFilter()
p = sg.getParameters()
p.setValue("frame_length", 15)  # Must be odd
sg.setParameters(p)
# sg.filterExperiment(exp)  # Use one smoother, not both

# Peak picking (centroiding) — required before feature detection
picker = ms.PeakPickerHiRes()
p = picker.getParameters()
p.setValue("signal_to_noise", 1.0)
picker.setParameters(p)
centroided = ms.MSExperiment()
picker.pickExperiment(exp, centroided)
print(f"Raw peaks in spec 0: {exp.getSpectrum(0).size()}")
print(f"Centroided peaks: {centroided.getSpectrum(0).size()}")
```

```python
# Normalization
normalizer = ms.Normalizer()
p = normalizer.getParameters()
p.setValue("method", "to_one")  # "to_one" or "to_TIC"
normalizer.setParameters(p)
normalizer.filterPeakMap(centroided)

# Peak filtering — remove low-intensity noise
mower = ms.ThresholdMower()
p = mower.getParameters()
p.setValue("threshold", 100.0)  # Minimum intensity
mower.setParameters(p)
mower.filterPeakMap(centroided)

# Baseline reduction
morph = ms.MorphologicalFilter()
p = morph.getParameters()
p.setValue("struc_elem_length", 3.0)  # m/z window
morph.setParameters(p)
morph.filterExperiment(exp)
```

### Module 3: Feature Detection & Linking

Detect chromatographic features and link them across samples.

```python
import pyopenms as ms

# Load centroided data
exp = ms.MSExperiment()
ms.MzMLFile().load("centroided.mzML", exp)

# Feature detection (proteomics — centroided data)
ff = ms.FeatureFinder()
features = ms.FeatureMap()
seeds = ms.FeatureMap()
params = ms.FeatureFinder().getParameters("centroided")
ff.run("centroided", exp, features, params, seeds)
print(f"Detected {features.size()} features")

# Access feature properties
for f in features[:5]:
    print(f"  RT: {f.getRT():.1f}s, m/z: {f.getMZ():.4f}, "
          f"intensity: {f.getIntensity():.0f}, quality: {f.getOverallQuality():.3f}")
```

```python
# Feature linking across samples — align retention times first
aligner = ms.MapAlignmentAlgorithmPoseClustering()
p = aligner.getParameters()
p.setValue("max_num_peaks_considered", 1000)
aligner.setParameters(p)

# Link features into consensus map
linker = ms.FeatureGroupingAlgorithmQT()
p = linker.getParameters()
p.setValue("distance_RT:max_difference", 60.0)  # seconds
p.setValue("distance_MZ:max_difference", 10.0)   # ppm
linker.setParameters(p)

consensus = ms.ConsensusMap()
linker.group([features_sample1, features_sample2, features_sample3], consensus)
print(f"Consensus features: {consensus.size()}")

# Export to pandas for downstream analysis
import pandas as pd
df = consensus.get_df()
print(f"Consensus table: {df.shape}")
```

### Module 4: Peptide & Protein Identification

Process search engine results with FDR control and protein inference.

```python
import pyopenms as ms

# Load search engine results
protein_ids, peptide_ids = [], []
ms.IdXMLFile().load("search_results.idXML", protein_ids, peptide_ids)

# Examine peptide hits
for pep_id in peptide_ids[:3]:
    print(f"Spectrum: RT={pep_id.getRT():.1f}, MZ={pep_id.getMZ():.4f}")
    for hit in pep_id.getHits():
        seq = hit.getSequence()
        print(f"  {seq} score={hit.getScore():.4f} charge={hit.getCharge()}")

# FDR filtering (target-decoy approach)
fdr = ms.FalseDiscoveryRate()
fdr.apply(peptide_ids)

# Filter at 1% FDR
filtered = []
for pep_id in peptide_ids:
    hits = [h for h in pep_id.getHits() if h.getScore() <= 0.01]
    if hits:
        pep_id.setHits(hits)
        filtered.append(pep_id)
print(f"Peptide IDs at 1% FDR: {len(filtered)}")
```

```python
# Protein inference
inference = ms.BasicProteinInferenceAlgorithm()
inference.run(peptide_ids, protein_ids)

for prot_id in protein_ids:
    for hit in prot_id.getHits()[:5]:
        print(f"Protein: {hit.getAccession()}, score: {hit.getScore():.4f}")

# Peptide sequence handling
seq = ms.AASequence.fromString("PEPTIDER")
print(f"Molecular weight: {seq.getMonoWeight():.4f}")
print(f"Formula: {seq.getFormula()}")

# Modified sequence
mod_seq = ms.AASequence.fromString("PEPTM(Oxidation)DER")
print(f"Modified weight: {mod_seq.getMonoWeight():.4f}")

# Enzymatic digestion
digestor = ms.ProteaseDigestion()
digestor.setEnzyme("Trypsin")
digest = []
digestor.digest(ms.AASequence.fromString("MKWVTFISLLLLFSSAYSRGVFRR"), digest)
print(f"Tryptic peptides: {len(digest)}")
```

### Module 5: Metabolomics Pipeline

Complete untargeted metabolomics workflow from raw data to feature table.

```python
import pyopenms as ms

# Step 1: Load and centroid raw data
exp = ms.MSExperiment()
ms.MzMLFile().load("metabolomics_sample.mzML", exp)

picker = ms.PeakPickerHiRes()
centroided = ms.MSExperiment()
picker.pickExperiment(exp, centroided)

# Step 2: Feature detection for metabolomics (small molecules)
ff = ms.FeatureFinder()
features = ms.FeatureMap()
seeds = ms.FeatureMap()
params = ms.FeatureFinder().getParameters("centroided")
params.setValue("isotopic_pattern:charge_low", 1)
params.setValue("isotopic_pattern:charge_high", 3)
ff.run("centroided", centroided, features, params, seeds)
print(f"Detected features: {features.size()}")

# Step 3: Adduct detection (group related adducts)
decharger = ms.MetaboliteAdductDecharger()
p = decharger.getParameters()
p.setValue("potential_adducts", "H:+:0.6;Na:+:0.3;K:+:0.1")  # Positive mode
decharger.setParameters(p)
# decharger.compute(features, feature_map_out, consensus_map_out)
```

```python
# Step 4: RT alignment across samples
import pyopenms as ms
import pandas as pd

# Assuming feature maps from multiple samples
sample_files = ["sample1.featureXML", "sample2.featureXML", "sample3.featureXML"]
feature_maps = []
for f in sample_files:
    fm = ms.FeatureMap()
    ms.FeatureXMLFile().load(f, fm)
    feature_maps.append(fm)

# Align retention times
aligner = ms.MapAlignmentAlgorithmPoseClustering()
aligner.setReference(0)  # Use first sample as reference

# Step 5: Link features to consensus map
linker = ms.FeatureGroupingAlgorithmQT()
p = linker.getParameters()
p.setValue("distance_RT:max_difference", 30.0)
p.setValue("distance_MZ:max_difference", 10.0)
linker.setParameters(p)

consensus = ms.ConsensusMap()
linker.group(feature_maps, consensus)

# Step 6: Export metabolite table
df = consensus.get_df()
print(f"Feature table: {df.shape[0]} features × {df.shape[1]} columns")
print(df[["RT", "mz", "intensity_0", "intensity_1", "intensity_2"]].head())
```

## Key Concepts

### Algorithm Parameter Pattern

All PyOpenMS algorithms follow the same 3-step pattern:

```python
algo = ms.AlgorithmClass()           # 1. Instantiate
params = algo.getParameters()         # 2. Get parameters
params.setValue("param_name", value)   # 3. Set values
algo.setParameters(params)            # 4. Apply
# algo.process(input, output)         # 5. Execute
```

To discover available parameters:
```python
for key in params.keys():
    print(f"{key}: {params.getValue(key)} (type: {params.getDescription(key)})")
```

### Core Data Structures

| Object | Description | Key Methods |
|--------|-------------|-------------|
| `MSExperiment` | Collection of spectra + chromatograms | `getNrSpectra()`, `getSpectrum(i)`, `addSpectrum()` |
| `MSSpectrum` | Single mass spectrum (m/z, intensity) | `get_peaks()`, `getMSLevel()`, `getRT()`, `size()` |
| `MSChromatogram` | Chromatographic trace | `get_peaks()`, `getNativeID()` |
| `Feature` | Detected chromatographic peak | `getRT()`, `getMZ()`, `getIntensity()`, `getOverallQuality()` |
| `FeatureMap` | Collection of features | `size()`, `get_df()`, iteration |
| `ConsensusMap` | Features linked across samples | `size()`, `get_df()` |
| `PeptideIdentification` | Search results for one spectrum | `getHits()`, `getRT()`, `getMZ()` |
| `AASequence` | Amino acid sequence with modifications | `fromString()`, `getMonoWeight()`, `getFormula()` |

### Supported File Formats

| Format | Reader Class | Content |
|--------|-------------|---------|
| mzML | `MzMLFile` | Raw spectra (standard) |
| mzXML | `MzXMLFile` | Raw spectra (legacy) |
| featureXML | `FeatureXMLFile` | Detected features |
| consensusXML | `ConsensusXMLFile` | Linked features |
| idXML | `IdXMLFile` | Peptide/protein IDs |
| mzIdentML | `MzIdentMLFile` | Peptide/protein IDs (standard) |
| FASTA | `FASTAFile` | Protein sequences |
| TraML | `TraMLFile` | MRM transitions |
| mzTab | `MzTabFile` | Quantification results |

## Common Workflows

### Workflow 1: Proteomics Feature Detection Pipeline

```python
import pyopenms as ms

# Load → Smooth → Centroid → Detect → Export
exp = ms.MSExperiment()
ms.MzMLFile().load("proteomics.mzML", exp)

# Preprocessing
gauss = ms.GaussFilter()
p = gauss.getParameters(); p.setValue("gaussian_width", 0.1); gauss.setParameters(p)
gauss.filterExperiment(exp)

picker = ms.PeakPickerHiRes()
centroided = ms.MSExperiment()
picker.pickExperiment(exp, centroided)

# Feature detection
ff = ms.FeatureFinder()
features = ms.FeatureMap()
params = ff.getParameters("centroided")
ff.run("centroided", centroided, features, params, ms.FeatureMap())

# Export to pandas
df = features.get_df()
print(f"Features: {df.shape}")
df.to_csv("proteomics_features.csv", index=False)
```

### Workflow 2: Multi-Sample Metabolomics Comparison

1. Load mzML files for all samples (Core API Module 1)
2. Centroid each sample (Core API Module 2 — `PeakPickerHiRes`)
3. Detect features per sample (Core API Module 3 — `FeatureFinder`)
4. Align retention times (Core API Module 3 — `MapAlignmentAlgorithmPoseClustering`)
5. Link features to consensus map (Core API Module 3 — `FeatureGroupingAlgorithmQT`)
6. Export consensus table to pandas and filter by CV across replicates

### Workflow 3: Identification Results Analysis

```python
import pyopenms as ms
import pandas as pd

# Load and filter identifications
protein_ids, peptide_ids = [], []
ms.IdXMLFile().load("search.idXML", protein_ids, peptide_ids)

# FDR filtering
fdr = ms.FalseDiscoveryRate()
fdr.apply(peptide_ids)

# Build results table
rows = []
for pep_id in peptide_ids:
    for hit in pep_id.getHits():
        if hit.getScore() <= 0.01:  # 1% FDR
            rows.append({
                "sequence": str(hit.getSequence()),
                "score": hit.getScore(),
                "charge": hit.getCharge(),
                "rt": pep_id.getRT(),
                "mz": pep_id.getMZ()
            })

df = pd.DataFrame(rows)
print(f"Identified peptides at 1% FDR: {len(df)}")
print(f"Unique sequences: {df['sequence'].nunique()}")
df.to_csv("peptide_identifications.csv", index=False)
```

## Key Parameters

| Parameter | Module | Default | Range/Options | Effect |
|-----------|--------|---------|---------------|--------|
| `gaussian_width` | GaussFilter | 0.2 | 0.05–1.0 | m/z smoothing window width |
| `frame_length` | SavitzkyGolayFilter | 11 | 5–31 (odd) | Smoothing window points |
| `signal_to_noise` | PeakPickerHiRes | 1.0 | 0.5–10.0 | Minimum S/N for centroiding |
| `isotopic_pattern:charge_low` | FeatureFinder | 1 | 1–6 | Minimum charge state |
| `isotopic_pattern:charge_high` | FeatureFinder | 3 | 1–10 | Maximum charge state |
| `distance_RT:max_difference` | FeatureGroupingAlgorithmQT | 100 | 10–300 s | RT tolerance for feature linking |
| `distance_MZ:max_difference` | FeatureGroupingAlgorithmQT | 10 | 1–50 ppm | m/z tolerance for feature linking |
| `threshold` | ThresholdMower | 0.0 | 0–10000 | Minimum peak intensity |
| `method` | Normalizer | "to_one" | "to_one"/"to_TIC" | Normalization method |

## Best Practices

1. **Always centroid before feature detection** — FeatureFinder requires centroided data. Use `PeakPickerHiRes` first
2. **Use indexed loading for large files** — `OnDiscMSExperiment` loads spectra on demand, avoiding memory issues for files >1 GB
3. **Preserve original data** — Store raw experiment before processing: `orig = ms.MSExperiment(exp)`. Processing is destructive
4. **Profile vs centroid awareness** — Check data type: `spec.getType()` returns 1 (profile) or 2 (centroid). Some algorithms require specific types
5. **Parameter discovery** — Print parameters before tuning: `for k in params.keys(): print(k, params.getValue(k))`
6. **Export to pandas early** — Use `features.get_df()` or `consensus.get_df()` to leverage pandas/numpy for statistical analysis

## Common Recipes

### Recipe 1: Spectrum Statistics and Quality Check

```python
import pyopenms as ms
import numpy as np

exp = ms.MSExperiment()
ms.MzMLFile().load("sample.mzML", exp)

ms1_count = sum(1 for s in exp if s.getMSLevel() == 1)
ms2_count = sum(1 for s in exp if s.getMSLevel() == 2)
rt_range = (exp.getSpectrum(0).getRT(), exp.getSpectrum(exp.getNrSpectra()-1).getRT())
peak_counts = [s.size() for s in exp]
print(f"MS1: {ms1_count}, MS2: {ms2_count}")
print(f"RT range: {rt_range[0]:.1f}–{rt_range[1]:.1f}s")
print(f"Peaks per spectrum: mean={np.mean(peak_counts):.0f}, "
      f"median={np.median(peak_counts):.0f}")
```

### Recipe 2: Theoretical Spectrum Generation

```python
import pyopenms as ms

# Generate theoretical fragment spectrum for a peptide
tsg = ms.TheoreticalSpectrumGenerator()
p = tsg.getParameters()
p.setValue("add_b_ions", "true")
p.setValue("add_y_ions", "true")
p.setValue("add_metainfo", "true")
tsg.setParameters(p)

spec = ms.MSSpectrum()
seq = ms.AASequence.fromString("PEPTIDER")
tsg.getSpectrum(spec, seq, 1, 2)  # charge 1 to 2
mz, intensity = spec.get_peaks()
print(f"Theoretical fragments for PEPTIDER: {len(mz)} ions")
```

### Recipe 3: Format Conversion (mzXML → mzML)

```python
import pyopenms as ms

exp = ms.MSExperiment()
ms.MzXMLFile().load("old_data.mzXML", exp)
ms.MzMLFile().store("converted.mzML", exp)
print(f"Converted {exp.getNrSpectra()} spectra to mzML format")
```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `FileNotFound` on load | Wrong path or format | Verify file exists; use correct reader class (MzMLFile for .mzML) |
| Empty feature map after detection | Profile data instead of centroided | Run `PeakPickerHiRes` before `FeatureFinder` |
| Very few features detected | Too-strict S/N threshold | Lower `signal_to_noise` to 0.5–1.0; adjust `isotopic_pattern` charge range |
| Memory error on large files | Loading entire file at once | Use `OnDiscMSExperiment` for indexed access |
| `setValue` type error | Wrong value type for parameter | Check expected type: `params.getDescription(key)`. Use float for numeric, string for enum |
| RT alignment fails | Too few common features | Increase `max_num_peaks_considered`; verify samples are from same experiment |
| FDR values all 1.0 | No decoy hits in search results | Ensure search was run with target-decoy database; check score orientation |
| Feature linking too aggressive | Large RT/m/z tolerances | Reduce `distance_RT:max_difference` and `distance_MZ:max_difference` |
| Slow processing | Processing all spectra | Filter by MS level first: `[s for s in exp if s.getMSLevel() == 1]` |

## Bundled Resources

- **references/data_structures_reference.md** — Comprehensive documentation of PyOpenMS core objects (MSExperiment, MSSpectrum, Feature, FeatureMap, ConsensusMap, PeptideIdentification, AASequence, Param). Covers: object creation, attribute access, iteration patterns, memory management, type conversions.
  - Covers: all 13+ core data structure classes with creation/access/iteration examples
  - Relocated inline: Core Data Structures summary table in Key Concepts, AASequence usage in Core API Module 4
  - Omitted: exhaustive attribute listings duplicating PyOpenMS API docs

- **references/signal_feature_processing.md** — Signal processing algorithms and feature detection/linking workflows consolidated from two original references.
  - Covers: smoothing (Gaussian, Savitzky-Golay), peak picking (HiRes, CWT), normalization, peak filtering (threshold, window, N-largest), baseline reduction, deconvolution, spectrum merging, RT alignment, mass calibration, feature finding (centroided, metabolomics), feature linking, adduct detection, quality control
  - Relocated inline: GaussFilter, PeakPickerHiRes, Normalizer, ThresholdMower in Core API Module 2; FeatureFinder, MapAlignment, FeatureGroupingAlgorithmQT in Core API Module 3
  - Omitted: CWT peak picker detailed parameters — rarely used vs HiRes; isotope wavelet transform — specialized use case

- **references/identification_metabolomics.md** — Peptide/protein identification and untargeted metabolomics pipelines consolidated from two original references.
  - Covers: search engine integration, FDR calculation, protein inference, enzymatic digestion, spectral library search, theoretical spectrum generation, untargeted metabolomics pipeline (peak picking → feature detection → adduct detection → alignment → linking → gap filling → annotation → export), compound identification (mass-based, MS/MS-based), normalization (TIC), QC (CV filtering, blank filtering), MetaboAnalyst export
  - Relocated inline: FDR filtering, protein inference, AASequence handling in Core API Module 4; metabolomics pipeline in Core API Module 5
  - Omitted: detailed Comet/Mascot parameter configuration — search engine-specific; MetaboAnalyst export format details — external tool

## Related Skills

- **matchms-spectral-matching** — spectral library matching and metabolite identification from MS/MS
- **biopython-molecular-biology** — protein sequence analysis (FASTA parsing, BLAST)

## References

- PyOpenMS documentation: https://pyopenms.readthedocs.io
- OpenMS project: https://www.openms.org
- Röst et al. (2016) OpenMS: a flexible open-source software platform for mass spectrometry data analysis. *Nature Methods*, DOI: 10.1038/nmeth.3959
- GitHub: https://github.com/OpenMS/OpenMS
