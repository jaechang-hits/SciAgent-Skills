# Signal Processing and Feature Detection Reference

## Algorithm Pattern

All PyOpenMS signal processing algorithms follow a 3-step pattern:

```python
import pyopenms as ms
algo = ms.AlgorithmName()
params = algo.getParameters()
params.setValue("parameter_name", value)
algo.setParameters(params)
algo.filterExperiment(exp)  # or filterSpectrum(spec)
```

---

## Signal Processing Algorithms

### GaussFilter (Smoothing)

```python
gaussian = ms.GaussFilter()
params = gaussian.getParameters()
params.setValue("gaussian_width", 0.2)
params.setValue("ppm_tolerance", 10.0)
params.setValue("use_ppm_tolerance", "true")
gaussian.setParameters(params)
gaussian.filterExperiment(exp)
```

### SavitzkyGolayFilter (Smoothing)

Polynomial smoothing that preserves peak shapes.

```python
sg = ms.SavitzkyGolayFilter()
params = sg.getParameters()
params.setValue("frame_length", 11)      # must be odd
params.setValue("polynomial_order", 4)
sg.setParameters(params)
sg.filterExperiment(exp)
```

### PeakPickerHiRes (Preferred)

```python
picker = ms.PeakPickerHiRes()
params = picker.getParameters()
params.setValue("signal_to_noise", 3.0)
params.setValue("spacing_difference", 1.5)
picker.setParameters(params)
exp_picked = ms.MSExperiment()
picker.pickExperiment(exp, exp_picked)
```

### PeakPickerCWT (Wavelet-Based)

```python
cwt = ms.PeakPickerCWT()
params = cwt.getParameters()
params.setValue("signal_to_noise", 1.0)
params.setValue("peak_width", 0.15)
cwt.setParameters(params)
cwt.pickExperiment(exp, exp_picked)
```

### Normalizer

```python
normalizer = ms.Normalizer()
params = normalizer.getParameters()
params.setValue("method", "to_one")   # or "to_TIC"
normalizer.setParameters(params)
normalizer.filterExperiment(exp)
```

### ThresholdMower

Remove peaks below absolute intensity threshold.

```python
mower = ms.ThresholdMower()
params = mower.getParameters()
params.setValue("threshold", 1000.0)
mower.setParameters(params)
mower.filterExperiment(exp)
```

### WindowMower

Keep top N peaks in sliding m/z windows.

```python
wm = ms.WindowMower()
params = wm.getParameters()
params.setValue("windowsize", 50.0)
params.setValue("peakcount", 2)
wm.setParameters(params)
wm.filterExperiment(exp)
```

### NLargest

```python
nl = ms.NLargest()
params = nl.getParameters()
params.setValue("n", 200)
nl.setParameters(params)
nl.filterExperiment(exp)
```

### MorphologicalFilter (Baseline)

```python
morph = ms.MorphologicalFilter()
params = morph.getParameters()
params.setValue("struc_elem_length", 3.0)
params.setValue("method", "tophat")  # tophat, bothat, erosion, dilation
morph.setParameters(params)
morph.filterExperiment(exp)
```

### SpectraMerger

```python
merger = ms.SpectraMerger()
params = merger.getParameters()
params.setValue("average_gaussian:spectrum_type", "profile")
params.setValue("average_gaussian:rt_FWHM", 5.0)
merger.setParameters(params)
merger.mergeSpectraBlockWise(exp)
```

### Charge Deconvolution

```python
deconv = ms.FeatureDeconvolution()
params = deconv.getParameters()
params.setValue("charge_min", 1)
params.setValue("charge_max", 4)
deconv.setParameters(params)
fm_out = ms.FeatureMap()
deconv.compute(exp, feature_map, fm_out, ms.ConsensusMap())
```

### RT Alignment

```python
aligner = ms.MapAlignmentAlgorithmPoseClustering()
transformations = []
aligner.align(exp1, exp2, transformations)
transformer = ms.MapAlignmentTransformer()
transformer.transformRetentionTimes(exp2, transformations[0])
```

### Isotope Deconvolution

```python
iso = ms.IsotopeWaveletTransform()
params = iso.getParameters()
params.setValue("max_charge", 3)
params.setValue("intensity_threshold", 10.0)
iso.setParameters(params)
iso.transform(exp)
```

### Mass Calibration

```python
calibration = ms.InternalCalibration()
reference_masses = [500.0, 1000.0, 1500.0]  # known m/z values
calibration.calibrate(exp, reference_masses)
```

### Spectrum Quality Metrics

```python
spec = exp.getSpectrum(0)
mz, intensity = spec.get_peaks()
tic = sum(intensity)
base_peak_idx = intensity.argmax()
print(f"TIC: {tic:.0f}, Base peak: {mz[base_peak_idx]:.4f} m/z at {intensity[base_peak_idx]:.0f}")
```

### Complete Preprocessing Pipeline

```python
def preprocess(input_file, output_file):
    exp = ms.MSExperiment()
    ms.MzMLFile().load(input_file, exp)
    ms.GaussFilter().filterExperiment(exp)           # smooth
    picker = ms.PeakPickerHiRes()
    exp_p = ms.MSExperiment()
    picker.pickExperiment(exp, exp_p)                 # peak pick
    norm = ms.Normalizer()
    p = norm.getParameters(); p.setValue("method", "to_TIC"); norm.setParameters(p)
    norm.filterExperiment(exp_p)                      # normalize
    mow = ms.ThresholdMower()
    p = mow.getParameters(); p.setValue("threshold", 10.0); mow.setParameters(p)
    mow.filterExperiment(exp_p)                       # filter
    ms.MzMLFile().store(output_file, exp_p)
```

---

## Feature Detection and Linking

### FeatureFinder (Proteomics)

```python
ff = ms.FeatureFinder()
params = ff.getParameters("centroided")
params.setValue("mass_trace:mz_tolerance", 10.0)     # ppm
params.setValue("mass_trace:min_spectra", 7)
params.setValue("isotopic_pattern:charge_low", 1)
params.setValue("isotopic_pattern:charge_high", 4)
features = ms.FeatureMap()
ff.run("centroided", exp, features, params, ms.FeatureMap())
```

### FeatureFinder (Metabolomics)

Optimized for small molecules: tighter m/z tolerance, lower charge states.

```python
params = ff.getParameters("centroided")
params.setValue("mass_trace:mz_tolerance", 5.0)      # tighter for metabolites
params.setValue("mass_trace:min_spectra", 5)
params.setValue("isotopic_pattern:charge_low", 1)
params.setValue("isotopic_pattern:charge_high", 2)   # mostly singly charged
features = ms.FeatureMap()
ff.run("centroided", exp, features, params, ms.FeatureMap())
features.setPrimaryMSRunPath(["sample.mzML".encode()])
```

### Feature Data Access and Export

```python
for f in feature_map:
    print(f"m/z: {f.getMZ():.4f}, RT: {f.getRT():.2f}, quality: {f.getOverallQuality():.3f}")
    for sub in f.getSubordinates():
        print(f"  Isotope: {sub.getMZ():.4f}")
df = feature_map.get_df()
```

### FeatureGroupingAlgorithmQT (Linking)

```python
grouper = ms.FeatureGroupingAlgorithmQT()
params = grouper.getParameters()
params.setValue("distance_RT:max_difference", 30.0)  # seconds
params.setValue("distance_MZ:max_difference", 10.0)  # ppm
params.setValue("distance_MZ:unit", "ppm")
grouper.setParameters(params)
consensus_map = ms.ConsensusMap()
grouper.group([fm1, fm2, fm3], consensus_map)
```

### Feature Filtering

```python
# By quality, intensity, or m/z range
filtered = ms.FeatureMap()
for f in feature_map:
    if f.getOverallQuality() > 0.5 and f.getIntensity() >= 10000:
        if 200.0 <= f.getMZ() <= 800.0:
            filtered.push_back(f)
```

### IDMapper (Feature Annotation)

```python
mapper = ms.IDMapper()
mapper.annotate(feature_map, peptide_ids, protein_ids)
for f in feature_map:
    for pid in f.getPeptideIdentifications():
        for hit in pid.getHits():
            print(f"Feature {f.getMZ():.4f}: {hit.getSequence().toString()}")
```

### MetaboliteAdductDecharger

```python
ad = ms.MetaboliteAdductDecharger()
params = ad.getParameters()
params.setValue("potential_adducts", "[M+H]+,[M+Na]+,[M+K]+,[M-H]-")
params.setValue("charge_min", 1)
params.setValue("charge_max", 1)
ad.setParameters(params)
fm_out = ms.FeatureMap()
ad.compute(feature_map, fm_out, ms.ConsensusMap())
```

---

### Feature Visualization

```python
import matplotlib.pyplot as plt
df = feature_map.get_df()
plt.figure(figsize=(10, 6))
plt.scatter(df['RT'], df['mz'], s=df['intensity']/df['intensity'].max()*50, alpha=0.5)
plt.xlabel('Retention Time (s)')
plt.ylabel('m/z')
plt.title('Feature Map')
plt.show()
```

### End-to-End Feature Detection Workflow

```python
def detect_and_link(input_files, output_consensus):
    fmaps = []
    for f in input_files:
        exp = ms.MSExperiment()
        ms.MzMLFile().load(f, exp)
        ff = ms.FeatureFinder()
        params = ff.getParameters("centroided")
        params.setValue("mass_trace:mz_tolerance", 10.0)
        features = ms.FeatureMap()
        ff.run("centroided", exp, features, params, ms.FeatureMap())
        features.setPrimaryMSRunPath([f.encode()])
        fmaps.append(features)
    # Align
    aligner = ms.MapAlignmentAlgorithmPoseClustering()
    aligned, trans = [], []
    aligner.align(fmaps, aligned, trans)
    # Link
    grouper = ms.FeatureGroupingAlgorithmQT()
    p = grouper.getParameters()
    p.setValue("distance_RT:max_difference", 30.0)
    p.setValue("distance_MZ:max_difference", 10.0)
    p.setValue("distance_MZ:unit", "ppm")
    grouper.setParameters(p)
    cmap = ms.ConsensusMap()
    grouper.group(aligned, cmap)
    ms.ConsensusXMLFile().store(output_consensus, cmap)
    return cmap
```

---

## Best Practices

1. **Preserve originals**: Copy before processing (`ms.MSExperiment(exp)`)
2. **Check data type**: Profile vs centroid before applying algorithms
3. **Parameter discovery**: `algo.getParameters()` lists all available parameters
4. **Pipeline order**: Smooth -> Peak pick -> Normalize -> Filter -> Feature find -> Link
5. **Align before linking**: Always align RT across runs before feature grouping
6. **Test parameters**: Try different values on representative data before full batch processing

---

> **Condensation note:** Condensed from originals: signal_processing.md (434 lines) + feature_detection.md (411 lines) = 845 lines. Retained: all major algorithms (smoothing, peak picking, normalization, filtering, baseline, merging, deconvolution, calibration, feature finding, linking, annotation, adduct detection). Relocated to SKILL.md: GaussFilter, PeakPickerHiRes, Normalizer, ThresholdMower (Core API Module 2); FeatureFinder, MapAlignment, FeatureGroupingAlgorithmQT (Core API Module 3). Omitted from signal_processing.md: CWT peak picker detailed parameters -- HiRes preferred in modern workflows. Omitted from feature_detection.md: per-parameter optimization tables -- use getParameters() discovery instead.
