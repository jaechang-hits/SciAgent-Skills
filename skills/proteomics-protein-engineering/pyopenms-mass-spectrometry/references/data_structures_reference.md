# PyOpenMS Core Data Structures Reference

## MSExperiment

Container for a complete LC-MS experiment (spectra + chromatograms).

```python
import pyopenms as ms
exp = ms.MSExperiment()
ms.MzMLFile().load("data.mzML", exp)
print(f"Spectra: {exp.getNrSpectra()}, Chromatograms: {exp.getNrChromatograms()}")
```

```python
# Iterate spectra, access by index, get RT range
for spec in exp:
    if spec.getMSLevel() == 2:
        print(f"MS2 at RT {spec.getRT():.2f}")
spec = exp.getSpectrum(0)
rts = [s.getRT() for s in exp]
```

```python
# Metadata
instrument = exp.getExperimentalSettings().getInstrument()
print(f"Instrument: {instrument.getName()}")
```

## MSSpectrum

Individual mass spectrum with m/z and intensity arrays.

```python
spec = ms.MSSpectrum()
print(f"MS level: {spec.getMSLevel()}, RT: {spec.getRT():.2f}, Peaks: {spec.size()}")
mz, intensity = spec.get_peaks()          # numpy arrays
spec.set_peaks(([100.0, 200.0], [1000.0, 2000.0]))  # set peaks
```

**Peak access tips**: `get_peaks()` returns `(mz_array, intensity_array)` as numpy arrays. Use `spec.size()` for peak count. Individual peaks can be indexed from the arrays: `mz[0]`, `intensity[0]`.

```python
# Precursor info (MS2 spectra)
if spec.getMSLevel() == 2:
    precursor = spec.getPrecursors()[0]
    print(f"Precursor m/z: {precursor.getMZ():.4f}, charge: {precursor.getCharge()}")
    print(f"Precursor intensity: {precursor.getIntensity():.0f}")
    # Isolation window
    print(f"Isolation width: {precursor.getIsolationWindowLowerOffset() + precursor.getIsolationWindowUpperOffset():.1f}")
```

## MSChromatogram

Chromatographic trace (TIC, XIC, or SRM transition).

```python
for chrom in exp.getChromatograms():
    rt, intensity = chrom.get_peaks()
    print(f"ID: {chrom.getNativeID()}, points: {len(rt)}, precursor: {chrom.getPrecursor().getMZ():.4f}")
```

## Feature

Detected chromatographic peak with 2D spatial extent (RT-m/z).

```python
feature = feature_map[0]
print(f"m/z: {feature.getMZ():.4f}, RT: {feature.getRT():.2f}")
print(f"Intensity: {feature.getIntensity():.0f}, Charge: {feature.getCharge()}")
print(f"Quality: {feature.getOverallQuality():.3f}, Width: {feature.getWidth():.2f}")
```

```python
# Convex hull bounding box
bbox = feature.getConvexHull().getBoundingBox()
print(f"RT: {bbox.minPosition()[0]:.2f}-{bbox.maxPosition()[0]:.2f}")
# Subordinate features (isotope patterns)
for sub in feature.getSubordinates():
    print(f"Isotope m/z: {sub.getMZ():.4f}, intensity: {sub.getIntensity():.0f}")
# Metadata
if feature.metaValueExists("label"):
    print(f"Label: {feature.getMetaValue('label')}")
```

## FeatureMap

Collection of features from a single LC-MS run. Supports iteration, sorting, filtering, and pandas export.

```python
feature_map = ms.FeatureMap()
ms.FeatureXMLFile().load("features.featureXML", feature_map)
print(f"Total features: {feature_map.size()}")
for feature in feature_map:
    print(f"m/z={feature.getMZ():.4f}, RT={feature.getRT():.2f}")
```

```python
# Add new feature
new_feature = ms.Feature()
new_feature.setMZ(500.0)
new_feature.setRT(300.0)
new_feature.setIntensity(10000.0)
new_feature.setCharge(2)
feature_map.push_back(new_feature)
```

```python
# Sorting, source metadata, and pandas export
feature_map.sortByRT()  # also sortByMZ(), sortByIntensity()
primary_path = feature_map.getPrimaryMSRunPath()
if primary_path:
    print(f"Source: {primary_path[0].decode()}")
df = feature_map.get_df()  # columns: RT, mz, intensity, charge, quality
print(df.head())
```

## ConsensusFeature and ConsensusMap

Features linked across multiple samples.

```python
consensus_map = ms.ConsensusMap()
ms.ConsensusXMLFile().load("consensus.consensusXML", consensus_map)
print(f"Consensus features: {consensus_map.size()}")
```

```python
# Access per-sample handles
cons_feature = consensus_map[0]
for handle in cons_feature.getFeatureList():
    print(f"Map {handle.getMapIndex()}: m/z={handle.getMZ():.4f}, intensity={handle.getIntensity():.0f}")
# Column headers
for map_idx, desc in consensus_map.getColumnHeaders().items():
    print(f"Map {map_idx}: {desc.filename}, label={desc.label}")
df = consensus_map.get_df()
```

## PeptideIdentification and PeptideHit

Identification results for a single spectrum.

```python
protein_ids, peptide_ids = [], []
ms.IdXMLFile().load("identifications.idXML", protein_ids, peptide_ids)
peptide_id = peptide_ids[0]
print(f"RT: {peptide_id.getRT():.2f}, m/z: {peptide_id.getMZ():.4f}")
print(f"Score type: {peptide_id.getScoreType()}")
```

```python
for hit in peptide_id.getHits():
    print(f"Sequence: {hit.getSequence().toString()}, Score: {hit.getScore()}")
    print(f"Charge: {hit.getCharge()}, Rank: {hit.getRank()}")
    for acc in hit.extractProteinAccessionsSet():
        print(f"  Protein: {acc.decode()}")
```

## ProteinIdentification and ProteinHit

Protein-level identification results.

```python
protein_id = protein_ids[0]
print(f"Engine: {protein_id.getSearchEngine()}")
search_params = protein_id.getSearchParameters()
print(f"DB: {search_params.db}, Enzyme: {search_params.digestion_enzyme.getName()}")
for hit in protein_id.getHits():
    print(f"{hit.getAccession()}: score={hit.getScore()}, coverage={hit.getCoverage():.1f}%")
```

## AASequence

Amino acid sequence with modification support.

```python
seq = ms.AASequence.fromString("PEPTIDE")
print(f"Length: {seq.size()}, Mono mass: {seq.getMonoWeight():.4f}")
```

```python
# Modifications
mod_seq = ms.AASequence.fromString("PEPTIDEM(Oxidation)K")
for i in range(mod_seq.size()):
    res = mod_seq.getResidue(i)
    if res.isModified():
        print(f"Position {i}: {res.getModificationName()}")
# Terminal modifications
term_seq = ms.AASequence.fromString("(Acetyl)PEPTIDE(Amidated)")
```

## EmpiricalFormula

Molecular formula representation and calculations.

```python
formula = ms.EmpiricalFormula("C6H12O6")
print(f"Mono mass: {formula.getMonoWeight():.4f}")
print(f"C: {formula.getNumberOf(b'C')}, H: {formula.getNumberOf(b'H')}")
combined = formula + ms.EmpiricalFormula("H2O")
```

## Param

Generic parameter container used by all algorithms.

```python
algo = ms.GaussFilter()
params = algo.getParameters()
for key in params.keys():
    print(f"{key}: {params.getValue(key)}")
params.setValue("gaussian_width", 0.2)
algo.setParameters(params)
```

## Best Practices

**Memory management**: For large files, use indexed access:
```python
indexed_mzml = ms.IndexedMzMLFileLoader()
indexed_mzml.load("large_file.mzML")
spec = indexed_mzml.getSpectrumById(100)  # no full file load
```

**Deep copy**: `exp_copy = ms.MSExperiment(exp)` creates an independent copy. Modifications to the copy do not affect the original.

**Type conversion**: `get_peaks()` returns numpy arrays directly; numpy operations work without conversion.

```python
import numpy as np
mz, intensity = spec.get_peaks()
filtered_mz = mz[intensity > 1000]  # numpy boolean indexing
```

**Param copying**: `params_copy = ms.Param(params)` for independent parameter sets.

**String encoding**: Some methods return byte strings. Use `.decode()` for Python strings (e.g., `accession.decode()`).

---

> **Condensation note:** Condensed from original: data_structures.md (498 lines). Retained: all 13+ core classes with creation/access/iteration examples. Relocated to SKILL.md: Core Data Structures summary table (Key Concepts), AASequence usage (Core API Module 4), Param pattern (Key Concepts). Omitted: exhaustive attribute listings -- consult PyOpenMS API docs for complete attribute references.
