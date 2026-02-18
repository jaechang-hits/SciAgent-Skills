# Identification and Metabolomics Reference

## Part 1: Peptide/Protein Identification

### Supported Search Engines

Comet (fast, open-source), Mascot (commercial), MSGFPlus (spectral probability), XTandem, OMSSA, Myrimatch, MSFragger (ultra-fast, open search).

### Reading Identification Data

```python
import pyopenms as ms
protein_ids, peptide_ids = [], []
ms.IdXMLFile().load("identifications.idXML", protein_ids, peptide_ids)
# Also supported: MzIdentMLFile (mzIdentML), PepXMLFile (pepXML)
```

### Accessing Peptide Hits and Scores

```python
for peptide_id in peptide_ids:
    print(f"RT: {peptide_id.getRT():.2f}, m/z: {peptide_id.getMZ():.4f}")
    for hit in peptide_id.getHits():
        seq = hit.getSequence()
        print(f"  {seq.toString()}, score={hit.getScore()}, charge={hit.getCharge()}")
        if seq.isModified():
            for i in range(seq.size()):
                res = seq.getResidue(i)
                if res.isModified():
                    print(f"    Mod at {i}: {res.getModificationName()}")
```

### Accessing Protein Identifications

```python
for pid in protein_ids:
    print(f"Engine: {pid.getSearchEngine()}, DB: {pid.getSearchParameters().db}")
    for hit in pid.getHits():
        print(f"  {hit.getAccession()}: score={hit.getScore()}, coverage={hit.getCoverage():.1f}%")
```

### FDR Filtering and Q-Value Transformation

```python
fdr = ms.FalseDiscoveryRate()
fdr.apply(peptide_ids)  # adds q-values to hits

filtered = []
for peptide_id in peptide_ids:
    good_hits = [h for h in peptide_id.getHits() if h.getMetaValue("q-value") <= 0.01]
    if good_hits:
        peptide_id.setHits(good_hits)
        filtered.append(peptide_id)
print(f"Peptides passing 1% FDR: {len(filtered)}")
```

### Protein Inference

**IDMapper** -- map peptide identifications to features by RT and m/z proximity:

```python
mapper = ms.IDMapper()
feature_map = ms.FeatureMap()
ms.FeatureXMLFile().load("features.featureXML", feature_map)
mapper.annotate(feature_map, peptide_ids, protein_ids)
# Check annotations
for f in feature_map:
    pids = f.getPeptideIdentifications()
    if pids:
        for pid in pids:
            for hit in pid.getHits():
                print(f"Feature {f.getMZ():.4f}: {hit.getSequence().toString()}")
```

**BasicProteinInferenceAlgorithm** -- group proteins by shared peptides:

```python
inference = ms.BasicProteinInferenceAlgorithm()
inference.run(peptide_ids, protein_ids)
for pid in protein_ids:
    hits = pid.getHits()
    if len(hits) > 1:
        print("Protein group:", [h.getAccession() for h in hits])
```

### Peptide Handling: AASequence and Modifications

```python
seq = ms.AASequence.fromString("PEPTIDE")
print(f"Mono mass: {seq.getMonoWeight():.4f}, Length: {seq.size()}")

# Modifications: Oxidation, Phospho, Carbamidomethyl
mod_seq = ms.AASequence.fromString("PEPTIDEM(Oxidation)K")
print(f"Modified mass: {mod_seq.getMonoWeight():.4f}")

# Terminal modifications
term_seq = ms.AASequence.fromString("(Acetyl)PEPTIDE(Amidated)")
```

### Enzymatic Digestion (ProteaseDigestion)

```python
enzyme = ms.ProteaseDigestion()
enzyme.setEnzyme("Trypsin")  # also: Chymotrypsin, GluC, LysC, AspN
enzyme.setMissedCleavages(2)
peptides = []
enzyme.digest(ms.AASequence.fromString(protein_sequence), peptides)
print(f"Generated {len(peptides)} peptides")
for pep in peptides[:5]:
    print(f"  {pep.toString()}, mass: {pep.getMonoWeight():.2f}")
```

### Theoretical Spectrum Generation

```python
peptide = ms.AASequence.fromString("PEPTIDE")
fragments = ms.MSSpectrum()
ms.TheoreticalSpectrumGenerator().getSpectrum(fragments, peptide, 1, 1)
mz, intensity = fragments.get_peaks()  # b and y ions
```

### Spectral Library Search

```python
library_spectra = []
ms.MSPFile().load("spectral_library.msp", library_spectra)
compare = ms.SpectraSTSimilarityScore()
for exp_spec in exp:
    if exp_spec.getMSLevel() == 2:
        best_score = max(compare.operator()(exp_spec, lib) for lib in library_spectra)
        if best_score > 0.7:
            print(f"Match: score {best_score:.3f}")
```

### Decoy Database Generation

```python
decoy_gen = ms.DecoyGenerator()
fasta_entries = []
ms.FASTAFile().load("target.fasta", fasta_entries)
decoys = [decoy_gen.reverseProtein(e) for e in fasta_entries]
ms.FASTAFile().store("target_decoy.fasta", fasta_entries + decoys)
```

---

## Part 2: Untargeted Metabolomics

### Pipeline Overview (7 Steps)

1. Peak picking and feature detection
2. Adduct detection and grouping
3. RT alignment across runs
4. Feature linking across samples
5. Gap filling for missing values
6. Compound identification
7. Export and statistical analysis

### Complete Pipeline

```python
def metabolomics_pipeline(input_files, output_dir):
    feature_maps = []
    for f in input_files:
        exp = ms.MSExperiment()
        ms.MzMLFile().load(f, exp)
        ff = ms.FeatureFinder()
        params = ff.getParameters("centroided")
        params.setValue("mass_trace:mz_tolerance", 5.0)
        params.setValue("isotopic_pattern:charge_high", 2)
        features = ms.FeatureMap()
        ff.run("centroided", exp, features, params, ms.FeatureMap())
        features.setPrimaryMSRunPath([f.encode()])
        feature_maps.append(features)

    # Adduct detection
    ad = ms.MetaboliteAdductDecharger()
    p = ad.getParameters()
    p.setValue("potential_adducts", "[M+H]+,[M+Na]+,[M+K]+,[M+NH4]+,[M-H]-,[M+Cl]-")
    ad.setParameters(p)
    grouped = [ms.FeatureMap() for _ in feature_maps]
    for fm, out in zip(feature_maps, grouped):
        ad.compute(fm, out, ms.ConsensusMap())

    # RT alignment + feature linking
    aligner = ms.MapAlignmentAlgorithmPoseClustering()
    aligned, trans = [], []
    aligner.align(grouped, aligned, trans)
    grouper = ms.FeatureGroupingAlgorithmQT()
    p = grouper.getParameters()
    p.setValue("distance_RT:max_difference", 60.0)
    p.setValue("distance_MZ:max_difference", 5.0)
    p.setValue("distance_MZ:unit", "ppm")
    grouper.setParameters(p)
    consensus = ms.ConsensusMap()
    grouper.group(aligned, consensus)
    consensus.get_df().to_csv(f"{output_dir}/metabolite_table.csv", index=False)
    return consensus
```

### Adduct Configuration

```python
# Positive mode
positive = ["[M+H]+", "[M+Na]+", "[M+K]+", "[M+NH4]+", "[2M+H]+", "[M+H-H2O]+"]
# Negative mode
negative = ["[M-H]-", "[M+Cl]-", "[M+FA-H]-", "[2M-H]-"]
# Access annotations
for f in feature_map_out:
    if f.metaValueExists("adduct"):
        print(f"m/z: {f.getMZ():.4f}, adduct: {f.getMetaValue('adduct')}")
```

### Compound Identification (Mass-Based)

```python
compound_db = [{"name": "Glucose", "mass": 180.0634}, {"name": "Citric acid", "mass": 192.0270}]
for feature in feature_map:
    neutral_mass = feature.getMZ() - 1.007276  # assuming [M+H]+
    for c in compound_db:
        err = abs(neutral_mass - c["mass"]) / c["mass"] * 1e6
        if err <= 5.0:  # ppm
            print(f"Match: {c['name']}, error: {err:.2f} ppm")
```

### TIC Normalization

```python
import numpy as np
n = len(consensus_map.getColumnHeaders())
tic = np.zeros(n)
for cf in consensus_map:
    for h in cf.getFeatureList():
        tic[h.getMapIndex()] += h.getIntensity()
factors = np.median(tic) / tic
for cf in consensus_map:
    for h in cf.getFeatureList():
        h.setIntensity(h.getIntensity() * factors[h.getMapIndex()])
```

### QC: CV Filtering and Blank Filtering

```python
import pandas as pd
df = consensus_map.get_df()
# CV filtering on QC samples
qc_cols = [c for c in df.columns if 'QC' in c]
if qc_cols:
    cv = (df[qc_cols].std(axis=1) / df[qc_cols].mean(axis=1)) * 100
    df = df[cv < 30]
# Blank filtering
blank_cols = [c for c in df.columns if 'Blank' in c]
sample_cols = [c for c in df.columns if 'Sample' in c]
if blank_cols and sample_cols:
    df = df[df[sample_cols].mean(axis=1) / (df[blank_cols].mean(axis=1) + 1) > 3]
```

### Missing Value Imputation

```python
df = df.replace(0, np.nan)
for col in df.select_dtypes(include=[np.number]).columns:
    df[col].fillna(df[col].min() / 2, inplace=True)  # half-minimum
```

### Metabolite Table Export

```python
def create_metabolite_table(cmap, output_file):
    headers = cmap.getColumnHeaders()
    data = {'mz': [], 'rt': [], 'feature_id': []}
    for m, h in headers.items():
        data[h.label or f"Sample_{m}"] = []
    for idx, cf in enumerate(cmap):
        data['mz'].append(cf.getMZ()); data['rt'].append(cf.getRT())
        data['feature_id'].append(f"F{idx:06d}")
        intens = {m: 0.0 for m in headers}
        for handle in cf.getFeatureList():
            intens[handle.getMapIndex()] = handle.getIntensity()
        for m, h in headers.items():
            data[h.label or f"Sample_{m}"].append(intens[m])
    pd.DataFrame(data).sort_values('rt').to_csv(output_file, index=False)
```

### MetaboAnalyst Export

```python
def export_for_metaboanalyst(df, output_file):
    sample_cols = [c for c in df.columns if c not in ['mz', 'rt', 'feature_id']]
    df[sample_cols].T.to_csv(output_file)
```

### Parameter Optimization

Test on QC samples before full batch:

```python
for tol in [3.0, 5.0, 10.0]:
    for min_spec in [3, 5, 7]:
        ff = ms.FeatureFinder()
        params = ff.getParameters("centroided")
        params.setValue("mass_trace:mz_tolerance", tol)
        params.setValue("mass_trace:min_spectra", min_spec)
        features = ms.FeatureMap()
        ff.run("centroided", exp, features, params, ms.FeatureMap())
        print(f"tol={tol}, min_spec={min_spec}: {features.size()} features")
```

### Complete Identification Workflow

```python
def identification_workflow(spectrum_file, id_file, output_file):
    # Load pre-computed search results
    protein_ids, peptide_ids = [], []
    ms.IdXMLFile().load(id_file, protein_ids, peptide_ids)
    # FDR filtering
    fdr = ms.FalseDiscoveryRate()
    fdr.apply(peptide_ids)
    filtered = []
    for pid in peptide_ids:
        good = [h for h in pid.getHits() if h.getMetaValue("q-value") <= 0.01]
        if good:
            pid.setHits(good)
            filtered.append(pid)
    # Protein inference
    inference = ms.BasicProteinInferenceAlgorithm()
    inference.run(filtered, protein_ids)
    # Save
    ms.IdXMLFile().store(output_file, protein_ids, filtered)
    return protein_ids, filtered
```

### Best Practices

1. **QC samples**: pooled QC every 5-10 injections
2. **Blanks**: run blank samples to identify contamination
3. **Replicates**: at least 3 biological replicates per group
4. **Randomize**: injection order to reduce batch effects
5. **RT windows**: 30s for 10-min gradient, 90s for 60-min gradient
6. **Target-decoy**: always use target-decoy approach for FDR calculation
7. **Adduct awareness**: configure adducts for your ionization mode (positive/negative)

---

> **Condensation note:** Condensed from originals: identification.md (423 lines) + metabolomics.md (483 lines) = 906 lines. Retained: search engine integration, FDR/protein inference, peptide handling, spectral library search, theoretical spectrum generation, decoy generation, complete metabolomics pipeline (7 steps), adduct detection, compound ID, normalization, QC, export. Relocated to SKILL.md: FDR filtering + protein inference (Core API Module 4); metabolomics pipeline steps (Core API Module 5). Omitted from identification.md: per-search-engine configuration -- engine-specific; detailed score interpretation tables -- varies by engine. Omitted from metabolomics.md: MetaboAnalyst export format details -- external tool documentation.
