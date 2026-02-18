---
name: "spikeinterface-electrophysiology"
description: "Unified Python framework for extracellular electrophysiology. Load recordings from 20+ formats (SpikeGLX, OpenEphys, NWB, Intan, Maxwell, Blackrock), preprocess signals, run 10+ spike sorters (Kilosort4, SpykingCircus2, Tridesclous, MountainSort5) with a single API, compute quality metrics (SNR, ISI violations, firing rate, amplitude cutoff), compare sorter outputs, and export to NWB or Phy. Use for format-agnostic and multi-sorter workflows. For a Neuropixels-specific Kilosort4 pipeline with PSTH and population decoding, use neuropixels-analysis instead."
license: "MIT"
---

# SpikeInterface — Unified Extracellular Electrophysiology Framework

## Overview

SpikeInterface provides a common Python API to read extracellular recordings from 20+ file formats, preprocess raw voltage traces, run 10+ spike sorters, postprocess and quality-control sorted units, and export results — all without format-specific code. Its modular design lets users swap sorters, formats, and preprocessing steps without rewriting pipelines. SpikeInterface is built around lazy, chainable objects: a `Recording` holds raw data, a `Sorting` holds spike times, and a `SortingAnalyzer` ties them together for waveform and metric computation.

## When to Use

- Loading recordings from multiple acquisition systems (SpikeGLX, OpenEphys, Intan, NWB, Maxwell MEA, Blackrock) with a unified API rather than format-specific parsers
- Running the same preprocessing and sorting pipeline across experiments recorded on different hardware
- Comparing two or more spike sorters on the same recording to assess agreement and choose the best output
- Running containerized sorters (Kilosort, IronClust, MountainSort5) via Docker or Singularity without local installation
- Computing standard quality metrics (SNR, ISI violations, firing rate, presence ratio, amplitude cutoff) and applying threshold-based curation
- Validating spike-sorting accuracy against synthetic or hybrid ground-truth recordings
- Exporting sorted results to NWB for data sharing or to Phy for manual curation
- Use `neuropixels-analysis` instead for a complete Neuropixels-specific Kilosort4 workflow including PSTH computation, tuning curves, and population decoding
- For EEG, ECG, or other biosignal processing (not spike sorting), use `neurokit2` instead

## Prerequisites

- **Python packages**: `spikeinterface[full]>=0.101`, `probeinterface`, `numpy`, `matplotlib`
- **Optional sorter deps**: `kilosort` (pip), or Docker/Singularity for containerized sorters
- **Data requirements**: raw binary recording files plus probe geometry (`.prb`, `.json`, or auto-detected from format)
- **Hardware**: GPU required for Kilosort4; all other sorters run on CPU

```bash
pip install "spikeinterface[full]>=0.101" probeinterface
# Optional: Kilosort4 Python package
pip install kilosort
# Optional: Phy for manual curation
pip install phy
```

## Quick Start

```python
import spikeinterface.full as si
import spikeinterface.preprocessing as spre
import spikeinterface.sorters as ss
import spikeinterface.qualitymetrics as sqm

# Load, preprocess, sort, and inspect quality metrics in 10 lines
recording = si.read_openephys("/data/session_001", stream_name="Signals CH")
recording_pp = spre.bandpass_filter(
    spre.common_reference(recording, reference="global", operator="median"),
    freq_min=300, freq_max=6000,
)
sorting = ss.run_sorter("spykingcircus2", recording_pp, output_folder="./sc2_out")
analyzer = si.create_sorting_analyzer(sorting, recording_pp, folder="./analyzer")
analyzer.compute(["random_spikes", "waveforms", "templates", "noise_levels"])
metrics = sqm.compute_quality_metrics(analyzer, metric_names=["snr", "firing_rate", "isi_violation"])
print(metrics.describe())
```

## Core API

### Module 1: Recording I/O

SpikeInterface wraps every acquisition format behind a common `BaseRecording` interface. Once loaded, all objects expose the same methods regardless of origin format.

```python
import spikeinterface.full as si

# SpikeGLX (.bin + .meta)
recording_sglx = si.read_spikeglx("/data/session_001", stream_name="imec0.ap")

# OpenEphys (binary or classic)
recording_oe = si.read_openephys("/data/oe_session", stream_name="Signals CH")

# NWB file
recording_nwb = si.read_nwb_recording("/data/recording.nwb",
                                       electrical_series_name="ElectricalSeries")

# Intan RHD/RHS
recording_intan = si.read_intan("/data/session.rhd", stream_name="RHn")

# Inspect any recording with the same API
print(f"Format:       {type(recording_sglx).__name__}")
print(f"Channels:     {recording_sglx.get_num_channels()}")
print(f"Sampling rate:{recording_sglx.get_sampling_frequency()} Hz")
print(f"Duration:     {recording_sglx.get_total_duration():.1f} s")
print(f"Probe:        {recording_sglx.get_probe().name}")
```

```python
# List available streams before loading (useful when a file has multiple streams)
streams = si.get_neo_streams("spikeglx", "/data/session_001")
print("Available streams:", streams)
# e.g. ['imec0.ap', 'imec0.lf', 'nidq']

# Select a time slice (lazy, no data loaded until get_traces() is called)
recording_slice = recording_sglx.frame_slice(
    start_frame=0,
    end_frame=int(60 * recording_sglx.get_sampling_frequency()),  # first 60 s
)
print(f"Sliced duration: {recording_slice.get_total_duration():.1f} s")
```

### Module 2: Preprocessing

Preprocessing functions return new `Recording` objects wrapping the original; the chain is applied lazily when data is read. This keeps memory usage low even for multi-hour recordings.

```python
import spikeinterface.preprocessing as spre

# 1. Common median reference — removes shared noise across all channels
recording_cmr = spre.common_reference(recording_sglx,
                                       reference="global",
                                       operator="median")

# 2. Bandpass filter for action potentials (300–6000 Hz typical)
recording_filt = spre.bandpass_filter(recording_cmr,
                                       freq_min=300,
                                       freq_max=6000)

# 3. Remove bad channels automatically (coherence-based detection)
recording_clean, removed_ids = spre.remove_bad_channels(recording_filt,
                                                          method="coherence+psd")
print(f"Removed {len(removed_ids)} bad channels: {removed_ids}")
print(f"Clean channels: {recording_clean.get_num_channels()}")
```

```python
# Whitening — decorrelates channels; recommended before template-matching sorters
recording_white = spre.whiten(recording_clean, mode="local")

# Phase shift correction for Neuropixels (samples acquired with small time offsets)
recording_shifted = spre.phase_shift(recording_clean)

# Inspect a short snippet of preprocessed data
traces = recording_white.get_traces(start_frame=0, end_frame=3000, segment_index=0)
print(f"Trace snippet shape: {traces.shape}")   # (3000, n_channels)
print(f"Trace range: [{traces.min():.2f}, {traces.max():.2f}] µV")
```

### Module 3: Spike Sorting

`ss.run_sorter()` wraps every supported sorter behind a uniform call signature. Sorter-specific parameters are passed as keyword arguments; all other pipeline steps are identical.

```python
import spikeinterface.sorters as ss
from pathlib import Path

# List all sorters available in the current environment
available = ss.available_sorters()
print("Available sorters:", available)

# List sorters that can run without local installation (via container)
installed = ss.installed_sorters()
print("Installed locally:", installed)

# Run SpykingCircus2 (CPU, no external deps)
sorting_sc2 = ss.run_sorter(
    "spykingcircus2",
    recording_clean,
    output_folder=Path("./sorter_output/sc2"),
    remove_existing_folder=True,
    verbose=True,
)
print(f"SpykingCircus2 units: {len(sorting_sc2.get_unit_ids())}")
```

```python
# Run Kilosort4 via Docker container (no local GPU/MATLAB required)
sorting_ks4 = ss.run_sorter(
    "kilosort4",
    recording_clean,
    output_folder=Path("./sorter_output/ks4"),
    singularity_image=False,   # use Docker; set True for Singularity
    docker_image=True,
    remove_existing_folder=True,
    # Kilosort4-specific parameters
    nblocks=5,
    Th_learned=8,
    do_correction=True,
)
print(f"Kilosort4 units: {len(sorting_ks4.get_unit_ids())}")

# Run MountainSort5 (CPU, fast, good for tetrode/low-channel-count probes)
sorting_ms5 = ss.run_sorter(
    "mountainsort5",
    recording_clean,
    output_folder=Path("./sorter_output/ms5"),
    scheme="2",          # scheme 2 is recommended for high-density probes
    detect_threshold=5.5,
)
print(f"MountainSort5 units: {len(sorting_ms5.get_unit_ids())}")
```

### Module 4: Postprocessing (SortingAnalyzer)

`SortingAnalyzer` is the central postprocessing object in SpikeInterface >= 0.101. It replaces the older `WaveformExtractor` and provides a unified interface for waveforms, templates, PCAs, and downstream metrics.

```python
import spikeinterface.full as si
import spikeinterface.postprocessing as spost

# Create analyzer (saves to disk; use format="memory" for in-RAM only)
analyzer = si.create_sorting_analyzer(
    sorting_sc2,
    recording_clean,
    folder="./analyzer_sc2",
    format="binary_folder",
    overwrite=True,
    sparse=True,           # sparse=True: only nearby channels per unit
    ms_before=1.0,
    ms_after=2.0,
)

# Compute extensions in dependency order
analyzer.compute([
    "random_spikes",       # subsample spike indices for waveform extraction
    "waveforms",           # raw waveform snippets per unit
    "templates",           # mean/std template per unit
    "noise_levels",        # per-channel noise estimate
])

# Retrieve templates
templates = analyzer.get_extension("templates").get_data(outputs="Templates")
print(f"Templates object: {templates}")
print(f"Unit 0 template shape: {templates.get_one_template_dense(0).shape}")
# (n_samples, n_channels)
```

```python
# Compute amplitude and PCA extensions (needed for quality metrics)
analyzer.compute([
    "spike_amplitudes",          # amplitude at peak channel per spike
    "principal_components",      # PCA scores (n_components x n_spikes)
    "template_similarity",       # pairwise template correlation matrix
    "correlograms",              # auto- and cross-correlograms
    "unit_locations",            # estimated unit position on probe (center of mass)
])

# Access spike amplitudes for first unit
ext_amp = analyzer.get_extension("spike_amplitudes")
unit_ids = analyzer.unit_ids
amps = ext_amp.get_data()[analyzer.sorting.ids_to_indices([unit_ids[0]])]
print(f"Unit {unit_ids[0]} — median amplitude: {abs(amps).median():.1f} µV")
```

### Module 5: Quality Metrics

Quality metrics summarize unit isolation quality. Metrics requiring only spike times (ISI violations, firing rate) are fast; metrics requiring waveforms (SNR, amplitude cutoff) need the `SortingAnalyzer` to be populated first.

```python
import spikeinterface.qualitymetrics as sqm

# Compute a standard panel of quality metrics
metrics = sqm.compute_quality_metrics(
    analyzer,
    metric_names=[
        "snr",                    # signal-to-noise ratio of template peak
        "isi_violation",          # fraction of ISIs < refractory period
        "firing_rate",            # mean firing rate (Hz) over recording
        "presence_ratio",         # fraction of time windows with ≥1 spike
        "amplitude_cutoff",       # estimated fraction of spikes below threshold
        "nearest_neighbor",       # isolation distance in PCA space
        "silhouette_score",       # cluster separation in PCA space
    ],
)
print(metrics.head())
print(f"\nShape: {metrics.shape}")  # (n_units, n_metrics)
```

```python
import pandas as pd

# Apply threshold-based curation (Allen Brain Institute defaults)
thresholds = {
    "snr":                   (">=", 5.0),
    "isi_violations_ratio":  ("<=", 0.1),
    "firing_rate":           (">=", 0.1),
    "presence_ratio":        (">=", 0.9),
    "amplitude_cutoff":      ("<=", 0.1),
}

keep = pd.Series(True, index=metrics.index)
for col, (op, val) in thresholds.items():
    if col not in metrics.columns:
        continue
    if op == ">=":
        keep &= metrics[col] >= val
    else:
        keep &= metrics[col] <= val

good_unit_ids = metrics[keep].index.tolist()
print(f"Total units:   {len(metrics)}")
print(f"Curated units: {len(good_unit_ids)} ({100*len(good_unit_ids)/len(metrics):.0f}%)")

# Filter analyzer to good units
sorting_curated = sorting_sc2.select_units(good_unit_ids)
```

### Module 6: Comparison and Export

Compare sorters against each other or against ground truth, then export results in shareable formats.

```python
import spikeinterface.comparison as sc

# Compare two sorters — matches units by spike train overlap
comparison = sc.compare_two_sorters(
    sorting_sc2,
    sorting_ks4,
    sorting1_name="SpykingCircus2",
    sorting2_name="Kilosort4",
    match_score=0.5,        # minimum overlap to count as a match
    delta_time=0.4,         # coincidence window (ms)
)

# Performance summary per matched unit pair
perf = comparison.get_performance(method="by_unit")
print(perf.head(10))
# Columns: accuracy, recall, precision, false_discovery_rate, miss_rate

# Agreement score matrix (fraction overlap between all unit pairs)
agreement_matrix = comparison.get_agreement_fraction_table()
print(f"Agreement matrix shape: {agreement_matrix.shape}")
```

```python
import spikeinterface.exporters as sexp

# Export curated sorting to NWB (Neurodata Without Borders)
sexp.export_to_nwb(
    sorting_curated,
    nwb_file_path="./session_sorted.nwb",
    overwrite=True,
)
print("Exported to NWB: session_sorted.nwb")

# Export to Phy for manual curation
sexp.export_to_phy(
    analyzer,
    output_folder="./phy_export",
    compute_pc_features=True,
    copy_binary=True,
    remove_if_exists=True,
)
print("Phy export ready at: ./phy_export")
print("Launch Phy with: phy template-gui phy_export/params.py")
```

## Common Workflows

### Workflow 1: Multi-Sorter Comparison on OpenEphys Data

**Goal**: Load an OpenEphys recording, preprocess, run two sorters, compare their agreement, curate the higher-yield output, and export to NWB.

```python
import spikeinterface.full as si
import spikeinterface.preprocessing as spre
import spikeinterface.sorters as ss
import spikeinterface.comparison as sc
import spikeinterface.qualitymetrics as sqm
import spikeinterface.exporters as sexp
from pathlib import Path

# --- Step 1: Load ---
data_dir = Path("/data/oe_recording")
streams = si.get_neo_streams("openephys", data_dir)
print("Streams:", streams)

recording = si.read_openephys(data_dir, stream_name="Signals CH")
print(f"Loaded: {recording.get_num_channels()} ch, "
      f"{recording.get_sampling_frequency()} Hz, "
      f"{recording.get_total_duration():.1f} s")

# --- Step 2: Preprocess ---
rec = spre.bandpass_filter(recording, freq_min=300, freq_max=6000)
rec = spre.common_reference(rec, reference="global", operator="median")
rec, bad_ids = spre.remove_bad_channels(rec, method="coherence+psd")
print(f"Preprocessing complete. Removed channels: {bad_ids}")

# --- Step 3: Run two sorters ---
out = Path("./sorting_outputs")
sorting_sc2 = ss.run_sorter("spykingcircus2", rec,
                              output_folder=out / "sc2",
                              remove_existing_folder=True)
sorting_tdc = ss.run_sorter("tridesclous2", rec,
                              output_folder=out / "tdc",
                              remove_existing_folder=True)
print(f"SC2 units: {len(sorting_sc2.unit_ids)}, "
      f"TDC units: {len(sorting_tdc.unit_ids)}")

# --- Step 4: Compare ---
cmp = sc.compare_two_sorters(sorting_sc2, sorting_tdc,
                               sorting1_name="SC2",
                               sorting2_name="Tridesclous2",
                               match_score=0.5)
perf = cmp.get_performance(method="pooled_with_average")
print(f"\nAgreement performance:\n{perf}")

# --- Step 5: Quality metrics on SC2 (higher yield) ---
analyzer = si.create_sorting_analyzer(sorting_sc2, rec,
                                        folder="./analyzer_sc2",
                                        overwrite=True, sparse=True)
analyzer.compute(["random_spikes", "waveforms", "templates",
                  "noise_levels", "spike_amplitudes"])
metrics = sqm.compute_quality_metrics(
    analyzer,
    metric_names=["snr", "firing_rate", "isi_violation",
                  "presence_ratio", "amplitude_cutoff"],
)

keep = (metrics["snr"] >= 5) & (metrics["isi_violations_ratio"] <= 0.1) \
     & (metrics["firing_rate"] >= 0.1) & (metrics["presence_ratio"] >= 0.9)
sorting_curated = sorting_sc2.select_units(metrics[keep].index.tolist())
print(f"\nCurated: {len(sorting_curated.unit_ids)} / {len(sorting_sc2.unit_ids)} units")

# --- Step 6: Export winner to NWB ---
sexp.export_to_nwb(sorting_curated,
                    nwb_file_path="./session_sorted.nwb",
                    overwrite=True)
print("Saved: session_sorted.nwb")
```

### Workflow 2: Ground Truth Validation with Synthetic Recordings

**Goal**: Generate a synthetic recording with known spike trains, run a sorter, and measure true accuracy (recall, precision) against ground truth — for benchmarking sorters or testing preprocessing pipelines.

```python
import spikeinterface.full as si
import spikeinterface.preprocessing as spre
import spikeinterface.sorters as ss
import spikeinterface.comparison as sc
import numpy as np

# --- Step 1: Generate ground-truth synthetic recording ---
# Uses a Marsaglia noise model with realistic waveform templates
recording_gt, sorting_gt = si.generate_ground_truth_recording(
    durations=[120.0],             # 120 s recording
    sampling_frequency=30000.0,
    num_channels=32,
    num_units=10,
    noise_kwargs={"noise_level": 10.0, "dtype": "float32"},
    seed=42,
)
print(f"GT recording: {recording_gt.get_num_channels()} ch, "
      f"{recording_gt.get_total_duration():.0f} s")
print(f"GT units: {len(sorting_gt.unit_ids)}")
print(f"GT firing rates: "
      f"{[round(len(sorting_gt.get_unit_spike_train(u, 0))/120, 1) for u in sorting_gt.unit_ids]} Hz")

# --- Step 2: Preprocess ---
rec_pp = spre.bandpass_filter(recording_gt, freq_min=300, freq_max=6000)
rec_pp = spre.common_reference(rec_pp, reference="global", operator="median")

# --- Step 3: Sort with two sorters ---
sorting_sc2 = ss.run_sorter("spykingcircus2", rec_pp,
                              output_folder="./gt_sc2",
                              remove_existing_folder=True)
sorting_ms5 = ss.run_sorter("mountainsort5", rec_pp,
                              output_folder="./gt_ms5",
                              remove_existing_folder=True,
                              scheme="2")

# --- Step 4: Compare each sorter against ground truth ---
for name, sorting_test in [("SC2", sorting_sc2), ("MS5", sorting_ms5)]:
    cmp = sc.compare_sorter_to_ground_truth(sorting_gt, sorting_test,
                                              exhaustive_gt=True)
    perf = cmp.get_performance(method="pooled_with_average")
    print(f"\n{name} vs Ground Truth:")
    print(f"  Accuracy:  {perf['accuracy']:.3f}")
    print(f"  Recall:    {perf['recall']:.3f}")
    print(f"  Precision: {perf['precision']:.3f}")
    print(f"  Well-detected units: {cmp.get_well_detected_units(well_detected_score=0.8)}")
```

### Workflow 3: Batch Processing Multiple Sessions

**Goal**: Apply the same preprocessing + sorting pipeline to multiple recording sessions and collect quality metrics across all sessions.

```python
import spikeinterface.full as si
import spikeinterface.preprocessing as spre
import spikeinterface.sorters as ss
import spikeinterface.qualitymetrics as sqm
import pandas as pd
from pathlib import Path

sessions = list(Path("/data/experiment").glob("session_*/"))
all_metrics = []

for session_dir in sessions:
    print(f"Processing {session_dir.name} ...")
    try:
        streams = si.get_neo_streams("spikeglx", session_dir)
        ap_stream = [s for s in streams if "ap" in s][0]
        rec = si.read_spikeglx(session_dir, stream_name=ap_stream)

        # Preprocess
        rec = spre.bandpass_filter(
            spre.common_reference(rec, reference="global", operator="median"),
            freq_min=300, freq_max=6000,
        )
        rec, _ = spre.remove_bad_channels(rec)

        # Sort
        out_dir = session_dir / "sorting"
        sorting = ss.run_sorter("spykingcircus2", rec,
                                 output_folder=out_dir,
                                 remove_existing_folder=True)

        # Compute metrics
        analyzer = si.create_sorting_analyzer(
            sorting, rec, folder=session_dir / "analyzer", overwrite=True, sparse=True
        )
        analyzer.compute(["random_spikes", "waveforms", "templates",
                          "noise_levels", "spike_amplitudes"])
        m = sqm.compute_quality_metrics(
            analyzer, metric_names=["snr", "firing_rate", "isi_violation"]
        )
        m["session"] = session_dir.name
        all_metrics.append(m)

    except Exception as e:
        print(f"  FAILED: {e}")
        continue

# Combine across sessions
combined = pd.concat(all_metrics)
combined.to_csv("all_sessions_metrics.csv")
print(f"\nSaved metrics: {combined.shape[0]} units across {len(all_metrics)} sessions")
print(combined.groupby("session")[["snr", "firing_rate"]].median())
```

## Key Parameters

| Parameter | Module / Function | Default | Range / Options | Effect |
|-----------|-------------------|---------|-----------------|--------|
| `freq_min` / `freq_max` | `spre.bandpass_filter` | 300 / 6000 Hz | 150–500 / 3000–10000 Hz | Spike band; use 300–6000 Hz for AP activity |
| `reference` | `spre.common_reference` | `"global"` | `"global"`, `"local"`, `"single"` | Channel subset used for median reference subtraction |
| `method` | `spre.remove_bad_channels` | `"coherence+psd"` | `"coherence+psd"`, `"std"`, `"mad"` | Algorithm for bad channel detection |
| `scheme` | `ss.run_sorter("mountainsort5")` | `"2"` | `"1"`, `"2"`, `"3"` | Sorting scheme; scheme 2 recommended for high-density probes |
| `nblocks` | `ss.run_sorter("kilosort4")` | `5` | `0–10` | Number of drift correction blocks; 0 disables drift correction |
| `Th_learned` | `ss.run_sorter("kilosort4")` | `8` | `6–12` | Detection threshold (× noise); lower = more units, more noise |
| `match_score` | `sc.compare_two_sorters` | `0.5` | `0.1–0.9` | Minimum spike-train overlap to declare a unit match |
| `sparse` | `si.create_sorting_analyzer` | `True` | `True`, `False` | Limit waveform extraction to channels near each unit; reduces memory |
| `ms_before` / `ms_after` | `si.create_sorting_analyzer` | `1.0` / `2.0` ms | 0.5–2.0 / 1.0–3.0 ms | Waveform snippet window relative to detected spike peak |
| `snr` threshold | `sqm.compute_quality_metrics` | — | 5–10 recommended | Amplitude / noise ratio; > 5 indicates well-isolated unit |
| `isi_violations_ratio` | `sqm.compute_quality_metrics` | — | ≤ 0.1 recommended | Fraction of ISIs < refractory period (1.5 ms); < 0.1 = single unit |
| `presence_ratio` | `sqm.compute_quality_metrics` | — | ≥ 0.9 recommended | Fraction of recording epochs where unit fires; < 0.9 = drifting unit |

## Best Practices

1. **Always inspect available streams before loading**: Different acquisition systems save AP data, LFP data, and auxiliary channels as separate streams. Loading the wrong stream silently yields valid-looking but incorrect data.
   ```python
   streams = si.get_neo_streams("spikeglx", data_dir)
   print(streams)  # e.g. ['imec0.ap', 'imec0.lf', 'nidq']
   recording = si.read_spikeglx(data_dir, stream_name="imec0.ap")
   ```

2. **Chain preprocessing lazily; do not load to memory early**: Preprocessing objects are lazy and apply transformations at read time. Calling `get_traces()` on the raw recording before preprocessing will load unfiltered data into RAM unnecessarily. Build the full chain before any data access.

3. **Use `sparse=True` when creating a SortingAnalyzer**: For high-channel-count probes (64–384 channels), dense waveform extraction is 10–50× more expensive in RAM and disk than sparse. Sparse mode extracts waveforms only on the channels nearest each unit.

4. **Run containerized sorters to avoid dependency conflicts**: Kilosort2/3 (MATLAB), IronClust, and other sorters have complex dependencies. Use `docker_image=True` in `run_sorter()` to pull the official container and run the sorter in isolation:
   ```python
   sorting = ss.run_sorter("kilosort2_5", recording_clean,
                            output_folder="./ks25_out",
                            docker_image=True)
   ```

5. **Compute metrics extensions in dependency order**: Extensions depend on each other. The canonical order is: `random_spikes` → `waveforms` → `templates` → `noise_levels` → `spike_amplitudes` → `principal_components`. Skipping an earlier step causes a `MissingExtensionError` when a downstream step is requested.

6. **Save the SortingAnalyzer to disk for large recordings**: In-memory analyzers (`format="memory"`) are lost when the process exits. For recordings longer than 30 minutes or with many units, always specify a `folder` path so the analyzer can be reloaded:
   ```python
   analyzer = si.load_sorting_analyzer("./analyzer_sc2")
   ```

7. **Do not compare sorters with mismatched preprocessing**: When benchmarking sorters, run all of them on the same preprocessed `recording_clean` object. Running sorters on different preprocessing chains invalidates the comparison.

## Common Recipes

### Recipe: Load and Inspect a Multi-Stream Recording

When to use: Quickly check what streams are available in an unfamiliar recording and confirm channel counts and duration before committing to a full sort.

```python
import spikeinterface.full as si

data_dir = "/data/recording_session"

# Try SpikeGLX first; if it fails, try OpenEphys
try:
    streams = si.get_neo_streams("spikeglx", data_dir)
    fmt = "spikeglx"
except Exception:
    streams = si.get_neo_streams("openephys", data_dir)
    fmt = "openephys"

print(f"Format: {fmt}")
print(f"Streams: {streams}")

for stream in streams:
    try:
        rec = si.read_spikeglx(data_dir, stream_name=stream) if fmt == "spikeglx" \
              else si.read_openephys(data_dir, stream_name=stream)
        print(f"  {stream}: {rec.get_num_channels()} ch, "
              f"{rec.get_sampling_frequency()} Hz, "
              f"{rec.get_total_duration():.1f} s")
    except Exception as e:
        print(f"  {stream}: could not load ({e})")
```

### Recipe: Export Quality Metrics Report to CSV

When to use: After running quality metrics, save a tidy CSV summarizing all units with their metrics and a pass/fail column for downstream analysis or sharing with collaborators.

```python
import spikeinterface.qualitymetrics as sqm
import pandas as pd

metrics = sqm.compute_quality_metrics(
    analyzer,
    metric_names=["snr", "firing_rate", "isi_violation",
                  "presence_ratio", "amplitude_cutoff"],
)

# Add pass/fail column based on standard thresholds
metrics["pass_qc"] = (
    (metrics["snr"] >= 5) &
    (metrics["isi_violations_ratio"] <= 0.1) &
    (metrics["firing_rate"] >= 0.1) &
    (metrics["presence_ratio"] >= 0.9) &
    (metrics["amplitude_cutoff"] <= 0.1)
)

metrics.to_csv("unit_quality_metrics.csv")
n_pass = metrics["pass_qc"].sum()
print(f"QC report saved: {len(metrics)} total units, {n_pass} pass ({100*n_pass/len(metrics):.0f}%)")
print(metrics[metrics["pass_qc"]].describe())
```

### Recipe: Probe Geometry Visualization

When to use: Verify that the probe channel map loaded correctly before sorting. Incorrect channel maps silently degrade sorting quality on high-density probes.

```python
import spikeinterface.full as si
import matplotlib.pyplot as plt
import probeinterface.plotting as pp

recording = si.read_spikeglx("/data/session_001", stream_name="imec0.ap")
probe = recording.get_probe()
print(f"Probe name: {probe.name}")
print(f"N contacts: {probe.get_contact_count()}")
print(f"Contact positions (first 5):\n{probe.contact_positions[:5]}")

fig, ax = plt.subplots(figsize=(3, 10))
pp.plot_probe(probe, ax=ax, with_channel_index=True)
ax.set_title(f"{probe.name} — channel map")
plt.tight_layout()
plt.savefig("probe_geometry.png", dpi=150)
print("Saved probe_geometry.png")
```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `ValueError: stream_name not found` | Recording has multiple streams; none is specified | Run `si.get_neo_streams(format, path)` to list available streams; pass the correct one to the reader |
| Sorter output has zero units | Detection threshold too high, or preprocessing removed all signal | Verify `recording_clean.get_traces()` returns non-zero data; lower detection threshold (e.g. `Th_learned=6` for Kilosort4) |
| `MissingExtensionError` | Analyzer extension depends on an uncomputed prerequisite | Follow the canonical compute order: `random_spikes` → `waveforms` → `templates` → `noise_levels` → `spike_amplitudes` |
| Docker sorter hangs at startup | Docker daemon not running or image not pulled | Run `docker ps` to confirm Docker is running; pull image manually with `docker pull spikeinterface/kilosort4-compiled-base` |
| `MemoryError` during waveform extraction | Dense extraction on high-channel-count probe | Use `sparse=True` in `create_sorting_analyzer`; reduce `max_spikes_per_unit` (default 500) |
| Bad channel detection removes too many channels | Threshold too aggressive or short recording | Set `method="std"` for a simpler threshold; increase `bad_threshold` parameter |
| Unit comparison shows 0% agreement between sorters | Delta time window too narrow or match score too strict | Increase `delta_time` (default 0.4 ms) and lower `match_score` (try 0.3) |
| NWB export raises `TypeError` on unit properties | Sorting contains non-serializable properties from sorter | Remove problematic properties: `sorting.remove_unit_property("property_name")` before export |
| `read_spikeglx` fails on LF stream | LFP stream uses different file suffix (`.lf.bin`) | Specify `stream_name="imec0.lf"` explicitly; confirm file exists with `ls data_dir/*.lf.bin` |

## Related Skills

- **neuropixels-analysis** — Neuropixels-specific pipeline using SpikeInterface + Kilosort4 with PSTH, tuning curves, and population decoding for rodent and primate experiments
- **neurokit2** — For biosignal processing (ECG, EEG, EDA, EMG, PPG) rather than spike sorting; use when data is not extracellular electrophysiology

## References

- [SpikeInterface documentation](https://spikeinterface.readthedocs.io/) — full API reference, tutorials, and sorter-specific guides
- [SpikeInterface GitHub](https://github.com/SpikeInterface/spikeinterface) — source code, changelogs, and issue tracker
- [Buccino et al. (2020), eLife — SpikeInterface paper](https://doi.org/10.7554/eLife.61834) — unified framework design and benchmarks across sorters
- [ProbeInterface documentation](https://probeinterface.readthedocs.io/) — probe geometry handling and channel map formats
- [SpikeInterface sorter list](https://spikeinterface.readthedocs.io/en/latest/modules/sorters.html) — supported sorters, requirements, and container images
- [NWB documentation](https://www.nwb.org/) — Neurodata Without Borders format for neurophysiology data sharing
