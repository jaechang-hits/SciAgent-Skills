---
name: "neuropixels-analysis"
description: "Pipeline for analyzing Neuropixels extracellular electrophysiology recordings. Covers probe geometry loading (ProbeInterface), spike sorting with Kilosort via SpikeInterface, quality metrics computation, unit curation (ISI violations, firing rate, signal-to-noise), and post-sort analysis (PSTH, tuning curves, population decoding) using pandas and matplotlib. Designed for acute and chronic Neuropixels 1.0/2.0/Ultra recordings from rodent and primate experiments."
license: "MIT"
---

# Neuropixels Analysis

## Overview

Neuropixels probes record extracellular voltage from 384 (NP 1.0) or 192 (NP 2.0) simultaneously recorded channels at 30 kHz. Analysis follows a canonical pipeline: raw data → spike sorting (Kilosort) → quality curation → unit analysis. **SpikeInterface** (Python) provides a unified API across 10+ spike sorters, handles data loading from multiple formats (SpikeGLX, OpenEphys, NWB), computes quality metrics, and exports sorted results. **ProbeInterface** manages probe geometry and channel maps. Post-sort analysis (PSTHs, firing rate, decoding) uses standard Python scientific stack.

## When to Use

- Spike-sorting Neuropixels recordings from SpikeGLX (`.bin`) or OpenEphys (`.dat`) to extract single-unit activity
- Applying automatic quality control metrics (ISI violations, SNR, firing rate) to curate sorted units
- Computing peristimulus time histograms (PSTHs) locked to experimental events
- Analyzing population coding: decoding stimulus or behavioral variables from firing rates
- Converting sorted data to NWB (Neurodata Without Borders) format for sharing
- Comparing multiple spike sorters on the same dataset for method validation
- Visualizing unit waveforms, auto-correlograms, and spatial distribution across probe channels

## Prerequisites

- **Python packages**: `spikeinterface[full]`, `probeinterface`, `numpy`, `pandas`, `matplotlib`, `scipy`
- **Spike sorter**: Kilosort4 (Python, `pip install kilosort`); or MATLAB-based Kilosort2/3 (requires MATLAB license)
- **Data requirements**: raw `.bin` (SpikeGLX) or `.dat` (OpenEphys) recording; probe channel map file (`.prb` or from ProbeInterface)
- **Hardware**: NVIDIA GPU (4+ GB VRAM) required for Kilosort; CPU fallback available but ~10× slower

```bash
pip install spikeinterface[full] probeinterface kilosort
# Optional: Phy for manual curation
pip install phy
```

## Workflow

### Step 1: Load Raw Recording

```python
import spikeinterface.full as si
from pathlib import Path

# SpikeGLX recording (most common Neuropixels format)
data_dir = Path("/data/recording/session_001")
recording = si.read_spikeglx(data_dir, stream_name="imec0.ap")

print(f"Probe type:       {recording.get_probe().name}")
print(f"Channels:         {recording.get_num_channels()}")
print(f"Sampling rate:    {recording.get_sampling_frequency()} Hz")
print(f"Duration:         {recording.get_total_duration():.1f} s")
print(f"Total samples:    {recording.get_total_samples()}")
```

### Step 2: Apply Common Reference and Bandpass Filter

```python
import spikeinterface.preprocessing as spre

# Common median reference (removes common noise across all channels)
recording_cmr = spre.common_reference(recording, reference="global", operator="median")

# Bandpass filter: 300–6000 Hz for spikes
recording_filt = spre.bandpass_filter(recording_cmr, freq_min=300, freq_max=6000)

# Remove bad channels automatically
recording_clean, removed_ids = spre.remove_bad_channels(recording_filt)
print(f"Removed {len(removed_ids)} bad channels: {removed_ids}")
print(f"Clean recording: {recording_clean.get_num_channels()} channels")
```

### Step 3: Run Spike Sorting

```python
import spikeinterface.sorters as ss
from pathlib import Path

output_dir = Path("./sorting_output")

# Kilosort4 (recommended for Neuropixels; requires GPU)
sorting = ss.run_sorter(
    "kilosort4",
    recording_clean,
    output_folder=output_dir / "kilosort4",
    remove_existing_folder=True,
    verbose=True,
    # Kilosort4 parameters
    nblocks=5,          # number of drift correction blocks
    Th_learned=8,       # threshold for learned templates
    do_correction=True, # drift correction
)

print(f"Units found: {len(sorting.get_unit_ids())}")
print(f"Spike counts (first 5): {[len(sorting.get_unit_spike_train(u, segment_index=0)) for u in sorting.unit_ids[:5]]}")
```

### Step 4: Compute Waveforms and Quality Metrics

```python
import spikeinterface.full as si
import spikeinterface.qualitymetrics as sqm

# Extract waveforms (snippets around each spike)
waveforms = si.extract_waveforms(
    recording_clean,
    sorting,
    folder="./waveforms",
    ms_before=1.0,      # ms before spike peak
    ms_after=2.0,       # ms after spike peak
    max_spikes_per_unit=1000,
    overwrite=True,
    n_jobs=4,
)

print(f"Waveform shape per unit: {waveforms.get_waveforms(waveforms.unit_ids[0]).shape}")
# (n_spikes, n_samples, n_channels)

# Compute quality metrics
metrics = sqm.compute_quality_metrics(
    waveforms,
    metric_names=["snr", "isi_violation", "firing_rate", "presence_ratio",
                  "amplitude_cutoff", "nearest_neighbor"],
)
print(f"\nQuality metrics summary:")
print(metrics.describe())
```

### Step 5: Curate Units

```python
import pandas as pd

# Curation thresholds (Allen Brain Institute defaults)
thresholds = {
    "snr":                (5.0, None),   # SNR ≥ 5
    "isi_violations_ratio": (None, 0.1), # ISI violation ratio ≤ 10%
    "firing_rate":        (0.1, None),   # firing rate ≥ 0.1 Hz
    "presence_ratio":     (0.9, None),   # present ≥ 90% of recording
    "amplitude_cutoff":   (None, 0.1),   # amplitude cutoff ≤ 10%
}

def apply_thresholds(metrics_df, thresholds):
    mask = pd.Series(True, index=metrics_df.index)
    for metric, (low, high) in thresholds.items():
        if metric not in metrics_df.columns:
            continue
        if low is not None:
            mask &= metrics_df[metric] >= low
        if high is not None:
            mask &= metrics_df[metric] <= high
    return mask

good_units_mask = apply_thresholds(metrics, thresholds)
good_unit_ids = metrics[good_units_mask].index.tolist()

print(f"Total units:   {len(metrics)}")
print(f"Good units:    {len(good_unit_ids)} ({100*len(good_unit_ids)/len(metrics):.0f}%)")

# Filter sorting to good units only
sorting_curated = sorting.select_units(good_unit_ids)
```

### Step 6: Compute PSTHs and Visualize

```python
import numpy as np
import matplotlib.pyplot as plt

def compute_psth(spike_times, event_times, window=(-0.5, 1.0), bin_size=0.01, fs=30000):
    """Compute peri-stimulus time histogram for one unit."""
    bins = np.arange(window[0], window[1] + bin_size, bin_size)
    spike_times_s = spike_times / fs  # samples → seconds
    counts = np.zeros(len(bins) - 1)
    for t_event in event_times:
        rel_times = spike_times_s - t_event
        in_window = rel_times[(rel_times >= window[0]) & (rel_times < window[1])]
        counts += np.histogram(in_window, bins=bins)[0]
    rate = counts / (len(event_times) * bin_size)  # convert to Hz
    return bins[:-1] + bin_size / 2, rate  # bin centers, firing rate

# Example: visual stimulus events at 1.0, 2.5, 4.0, 5.5 s
fs = 30000
event_times_s = np.array([1.0, 2.5, 4.0, 5.5, 7.0, 8.5])

# Plot PSTH for first 4 good units
fig, axes = plt.subplots(2, 2, figsize=(10, 6))
for ax, unit_id in zip(axes.flat, good_unit_ids[:4]):
    spikes = sorting_curated.get_unit_spike_train(unit_id, segment_index=0)
    times, rate = compute_psth(spikes, event_times_s, fs=fs)
    ax.bar(times, rate, width=0.01, color="steelblue", alpha=0.8)
    ax.axvline(0, color="red", lw=1.5, linestyle="--", label="Stimulus")
    ax.set_xlabel("Time from stimulus (s)")
    ax.set_ylabel("Firing rate (Hz)")
    ax.set_title(f"Unit {unit_id}")

plt.tight_layout()
plt.savefig("psth_grid.pdf", bbox_inches="tight")
print("Saved psth_grid.pdf")
```

### Step 7: Export to NWB

```python
import spikeinterface.exporters as sexp

# Export sorted data to Neurodata Without Borders format
nwb_path = "./recording_sorted.nwb"
sexp.export_to_nwb(
    sorting_curated,
    nwb_file_path=nwb_path,
    overwrite=True,
)
print(f"Exported to NWB: {nwb_path}")

# Also export waveforms for Phy manual curation
phy_dir = "./phy_export"
sexp.export_to_phy(
    waveforms,
    output_folder=phy_dir,
    compute_pc_features=True,
    copy_binary=True,
)
print(f"Phy export ready at: {phy_dir}")
print("Launch with: phy template-gui phy_export/params.py")
```

## Key Parameters

| Parameter | Module/Function | Default | Range / Options | Effect |
|-----------|----------------|---------|-----------------|--------|
| `freq_min` / `freq_max` | `bandpass_filter` | 300/6000 Hz | 150–500 / 3000–10000 | Spike band; NP 1.0 standard is 300–6000 Hz |
| `nblocks` | Kilosort4 | 5 | 0–10 | Number of drift correction blocks; 0 disables drift correction |
| `Th_learned` | Kilosort4 | 8 | 6–12 | Detection threshold (× noise level); lower = more spikes, more noise |
| `ms_before` / `ms_after` | `extract_waveforms` | 1.0/2.0 | 0.5–2.0/1.0–3.0 ms | Waveform snippet window around spike peak |
| `max_spikes_per_unit` | `extract_waveforms` | 500 | 100–5000 | Maximum spikes per unit for waveform extraction |
| `snr` threshold | quality metrics | — | 5–10 | Signal-to-noise threshold for unit acceptance |
| `isi_violations_ratio` | quality metrics | — | 0.05–0.2 | Refractory period violation rate; <0.1 is well-isolated |
| `presence_ratio` | quality metrics | — | 0.9 | Fraction of recording where unit is active |
| `bin_size` | PSTH | 0.01 s | 0.001–0.05 s | PSTH temporal resolution; smaller = more detail, noisier |

## Key Concepts

### Spike Sorting Pipeline

Raw voltage → preprocessing (common reference, bandpass) → detection (threshold crossing or learned templates) → clustering (PCA + k-means or Gaussian mixture) → template matching → quality metrics → curation. Kilosort4 adds drift correction, which is critical for chronic NP recordings (tip drift of 5–50 µm over hours degrades unit isolation).

### Quality Metrics

- **SNR**: peak waveform amplitude / noise level. SNR >5 indicates well-isolated unit
- **ISI violation ratio**: fraction of inter-spike intervals shorter than the refractory period (~1.5 ms). Ratio <0.1 indicates single-unit isolation
- **Presence ratio**: fraction of recording epochs where unit fired at least one spike. <0.9 suggests unit disappeared or was lost
- **Amplitude cutoff**: fraction of spikes missing due to detection threshold. <0.1 ensures near-complete detection

## Common Recipes

### Recipe: Compare Two Sorters on Same Recording

```python
import spikeinterface.sorters as ss
import spikeinterface.comparison as sc

# Run two sorters
sorting_ks4 = ss.run_sorter("kilosort4", recording_clean, output_folder="./ks4")
sorting_sc   = ss.run_sorter("spykingcircus2", recording_clean, output_folder="./sc2")

# Compare outputs
comparison = sc.compare_two_sorters(sorting_ks4, sorting_sc,
                                     sorting1_name="Kilosort4",
                                     sorting2_name="SpykingCircus2")
print(comparison.get_performance())
# Shows: agreement fraction, recall, precision per matched unit pair
```

### Recipe: Population Firing Rate Heatmap

```python
import numpy as np
import matplotlib.pyplot as plt

fs = 30000
duration_s = sorting_curated.get_total_duration()
bin_edges = np.arange(0, duration_s, 0.05)  # 50 ms bins

# Build firing rate matrix: (n_units, n_bins)
fr_matrix = np.zeros((len(good_unit_ids), len(bin_edges)-1))
for i, uid in enumerate(good_unit_ids[:50]):
    spikes_s = sorting_curated.get_unit_spike_train(uid, segment_index=0) / fs
    counts, _ = np.histogram(spikes_s, bins=bin_edges)
    fr_matrix[i] = counts / 0.05  # Hz

# Normalize each unit
fr_norm = (fr_matrix - fr_matrix.mean(1, keepdims=True)) / (fr_matrix.std(1, keepdims=True) + 1e-6)

fig, ax = plt.subplots(figsize=(12, 5))
im = ax.imshow(fr_norm, aspect="auto", cmap="RdBu_r",
               extent=[0, duration_s, len(good_unit_ids[:50]), 0], vmin=-2, vmax=2)
ax.set_xlabel("Time (s)")
ax.set_ylabel("Unit #")
ax.set_title("Population Activity Heatmap (z-scored FR)")
plt.colorbar(im, ax=ax, label="z-score")
plt.tight_layout()
plt.savefig("population_heatmap.pdf", bbox_inches="tight")
```

## Expected Outputs

| Output | Format | Typical Content |
|--------|--------|-----------------|
| `sorting/` | SpikeInterface folder | Spike times per unit; template waveforms |
| `waveforms/` | SpikeInterface folder | Waveform snippets `(n_spikes, n_samples, n_channels)` |
| `quality_metrics.csv` | CSV | SNR, ISI violations, firing rate, presence ratio per unit |
| `psth_grid.pdf` | PDF | PSTH plots for curated units |
| `recording_sorted.nwb` | NWB/HDF5 | Portable spike-sorted data for sharing |
| `phy_export/` | Phy format | `.npy` + `params.py` for manual curation GUI |

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| Kilosort GPU memory error | Recording too long or too many channels for VRAM | Process recording in time chunks using `si.SubRecording`; use NP 2.0 (192 ch) settings |
| Zero units found | Threshold too high or preprocessing removed all signal | Lower `Th_learned` to 6; verify `recording_clean` has non-zero channel data |
| Excessive ISI violations (>50%) | Multi-unit activity merged as single unit | Manual curation with Phy; increase `Th_learned` to be more conservative |
| Waveform extraction OOM | Too many spikes × channels × samples | Reduce `max_spikes_per_unit`; increase `n_jobs` for parallel extraction |
| Drift correction fails | Too few spikes or very short recording | Set `nblocks=1` (minimal correction) or `nblocks=0` (disable) |
| NWB export fails | Missing session metadata (subject, date) | Provide `NWBFile` metadata; or use `sexp.export_to_nwb(..., metadata={...})` |
| SpikeGLX file not found | Wrong stream name | List streams: `si.get_neo_streams("spikeglx", data_dir)` |

## References

- [SpikeInterface documentation](https://spikeinterface.readthedocs.io/) — full API, tutorials, and sorter comparison guides
- [Kilosort4 paper: Pachitariu et al. (2024), Nature Methods](https://doi.org/10.1038/s41592-024-02232-7) — drift correction and template learning
- [SpikeInterface paper: Buccino et al. (2020), eLife](https://doi.org/10.7554/eLife.61834) — unified framework for extracellular electrophysiology
- [ProbeInterface documentation](https://probeinterface.readthedocs.io/) — probe geometry and channel map handling
- [Neuropixels documentation](https://www.neuropixels.org/) — hardware specs, imec reference designs
- [NWB documentation](https://www.nwb.org/) — neurophysiology data standard for archiving and sharing
