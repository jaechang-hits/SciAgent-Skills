---
name: "neurokit2"
description: "Python toolkit for neurophysiological signal processing: ECG (HR, HRV, R-peaks), EEG (complexity, PSD), EMG (activation onset), EDA/GSR (SCR decomposition), PPG, and RSP. Includes synthetic signal simulation. Alternatives: BioSPPy (less maintained), MNE (EEG/MEG specialist), heartpy (ECG only), scipy.signal (raw DSP)."
license: "MIT"
---

# NeuroKit2

## Overview

NeuroKit2 provides a unified, high-level API for physiological signal processing. Each modality (ECG, EEG, EMG, EDA, PPG, RSP) follows the same `nk.{signal}_process()` → `nk.{signal}_analyze()` workflow: raw signal in, cleaned signal + features out. The library handles detrending, filtering, peak detection, artifact correction, and feature extraction automatically, with parameters tuned to biosignal characteristics. Results are returned as pandas DataFrames, making downstream statistics straightforward. NeuroKit2 also provides `nk.{signal}_simulate()` functions for generating synthetic test signals.

## When to Use

- Extracting HRV (heart rate variability) features from ECG recordings for stress or autonomic nervous system analysis
- Detecting R-peaks in ECG and computing RR intervals, SDNN, RMSSD, pNN50, LF/HF ratio
- Processing EDA/GSR signals to separate tonic (SCL) and phasic (SCR) components for psychophysiology research
- Cleaning and segmenting EMG signals for muscle onset/offset detection in biomechanics
- Processing PPG signals from wearable sensors as ECG surrogates for heart rate and SpO2
- Generating synthetic physiological signals for algorithm validation and unit tests
- Use MNE instead when working with multichannel EEG/MEG and source localization; use scipy.signal for raw low-level DSP

## Prerequisites

- **Python packages**: `neurokit2`, `numpy`, `pandas`, `matplotlib`
- **Data requirements**: 1D NumPy array or pandas Series of the physiological signal; known sampling rate (Hz)
- **Typical sampling rates**: ECG 250–1000 Hz, EEG 256–2048 Hz, EDA 4–64 Hz, EMG 1000–2000 Hz

```bash
pip install neurokit2 numpy pandas matplotlib scipy
```

## Quick Start

```python
import neurokit2 as nk
import matplotlib.pyplot as plt

# Generate and process synthetic ECG (10 seconds at 500 Hz)
ecg_signal = nk.ecg_simulate(duration=10, sampling_rate=500, heart_rate=70)
signals, info = nk.ecg_process(ecg_signal, sampling_rate=500)

# Plot processed ECG
nk.ecg_plot(signals, info)
plt.savefig("ecg_processed.pdf", bbox_inches="tight")
print(f"R-peaks detected: {len(info['ECG_R_Peaks'])}")
print(signals[["ECG_Clean", "ECG_Rate", "ECG_Quality"]].describe())
```

## Core API

### Module 1: ECG Processing

Full pipeline from raw ECG to cleaned signal, R-peaks, and instantaneous heart rate.

```python
import neurokit2 as nk
import numpy as np

# Load real data (example: CSV with one ECG column at 250 Hz)
# ecg_raw = pd.read_csv("ecg_recording.csv")["ecg"].values
# Or use synthetic:
ecg_raw = nk.ecg_simulate(duration=60, sampling_rate=250, heart_rate=72, noise=0.05)

# Full processing pipeline
signals, info = nk.ecg_process(ecg_raw, sampling_rate=250)

# signals: DataFrame with columns ECG_Raw, ECG_Clean, ECG_Rate, ECG_R_Peaks, ...
# info: dict with R-peak indices, P/Q/S/T wave locations

print(f"R-peaks: {len(info['ECG_R_Peaks'])} detected")
print(f"Mean heart rate: {signals['ECG_Rate'].mean():.1f} bpm")
print(f"ECG quality (0-1): {signals['ECG_Quality'].mean():.2f}")

# Get delineated waves (P, Q, S, T)
_, waves_dict = nk.ecg_delineate(signals["ECG_Clean"], info["ECG_R_Peaks"],
                                   sampling_rate=250, method="dwt")
print(f"P-wave peaks found: {np.sum(~np.isnan(waves_dict['ECG_P_Peaks']))}")
```

```python
# HRV analysis from ECG
hrv_time = nk.hrv_time(info["ECG_R_Peaks"], sampling_rate=250)
hrv_freq = nk.hrv_frequency(info["ECG_R_Peaks"], sampling_rate=250)
hrv_nonlinear = nk.hrv_nonlinear(info["ECG_R_Peaks"], sampling_rate=250)

print("Time-domain HRV:")
print(f"  SDNN  : {hrv_time['HRV_SDNN'].values[0]:.2f} ms")
print(f"  RMSSD : {hrv_time['HRV_RMSSD'].values[0]:.2f} ms")
print(f"  pNN50 : {hrv_time['HRV_pNN50'].values[0]:.2f}%")

print("\nFrequency-domain HRV:")
print(f"  LF power  : {hrv_freq['HRV_LF'].values[0]:.4f} ms²")
print(f"  HF power  : {hrv_freq['HRV_HF'].values[0]:.4f} ms²")
print(f"  LF/HF     : {hrv_freq['HRV_LFHF'].values[0]:.3f}")
```

### Module 2: EDA / GSR Processing

Electrodermal activity (EDA) / galvanic skin response (GSR) decomposition into tonic and phasic components.

```python
import neurokit2 as nk

# Simulate EDA signal (10 min at 4 Hz with 3 events)
eda_raw = nk.eda_simulate(duration=600, sampling_rate=4, scr_number=10, noise=0.01)

# Process: detrend, filter, decompose into SCL (tonic) + SCR (phasic)
signals, info = nk.eda_process(eda_raw, sampling_rate=4)

print(f"SCR peaks detected: {len(info['SCR_Peaks'])}")
print(f"SCR recovery times (mean): {signals['SCR_RecoveryTime'].mean():.2f} s")
print(f"SCL (tonic) mean: {signals['EDA_Tonic'].mean():.4f} μS")
print(f"SCR (phasic) amplitude mean: {signals['EDA_Phasic'].mean():.4f} μS")

# Analyze epochs around events
events = nk.events_create(event_onsets=[60, 120, 240], event_durations=3,
                           desired_length=len(eda_raw))
epoch_df = nk.epochs_create(signals, events, sampling_rate=4,
                              epochs_start=-5, epochs_end=10)
```

### Module 3: EMG Processing

Muscle activation detection from surface EMG.

```python
import neurokit2 as nk

# Simulate EMG with 3 activations at 1000 Hz
emg_raw = nk.emg_simulate(duration=10, sampling_rate=1000, burst_number=3)

# Process: rectify, envelope, detect activation periods
signals, info = nk.emg_process(emg_raw, sampling_rate=1000)

print(f"EMG activation onsets: {len(info['EMG_Onsets'])}")
print(f"EMG activation offsets: {len(info['EMG_Offsets'])}")

# Activation periods
for onset, offset in zip(info["EMG_Onsets"], info["EMG_Offsets"]):
    duration_ms = (offset - onset) / 1000 * 1000  # samples → ms
    print(f"  Activation: {onset/1000:.2f}s – {offset/1000:.2f}s ({duration_ms:.0f} ms)")

# Plot
nk.emg_plot(signals)
import matplotlib.pyplot as plt
plt.savefig("emg_processed.pdf", bbox_inches="tight")
```

### Module 4: EEG / Complexity Analysis

Signal complexity measures applicable to EEG and other biosignals.

```python
import neurokit2 as nk
import numpy as np

# Generate EEG-like signal
eeg = nk.eeg_simulate(duration=30, sampling_rate=256, brain_information=0.7)

# Band power (delta, theta, alpha, beta, gamma)
bands = nk.eeg_power(eeg, sampling_rate=256,
                      frequency_band=["Delta", "Theta", "Alpha", "Beta", "Gamma"])
print("EEG Band Power:")
for band, power in bands.items():
    print(f"  {band}: {power:.4f}")

# Complexity measures (for any 1D biosignal)
signal = np.random.randn(1000)  # test signal

entropy_sample = nk.entropy_sample(signal, order=2, r=0.2 * np.std(signal))
entropy_fuzzy = nk.entropy_fuzzy(signal, order=2)
dfa = nk.fractal_dfa(signal)

print(f"Sample entropy: {entropy_sample[0]:.4f}")
print(f"Fuzzy entropy: {entropy_fuzzy[0]:.4f}")
print(f"DFA exponent: {dfa[0]:.4f}")
```

### Module 5: PPG Processing

Photoplethysmography (PPG) from wearable sensors.

```python
import neurokit2 as nk

# Simulate PPG at 100 Hz (common wearable sampling rate)
ppg_raw = nk.ppg_simulate(duration=30, sampling_rate=100, heart_rate=65, noise=0.01)

# Process: clean, detect peaks
signals, info = nk.ppg_process(ppg_raw, sampling_rate=100)

print(f"PPG peaks detected: {len(info['PPG_Peaks'])}")
print(f"Mean heart rate: {signals['PPG_Rate'].mean():.1f} bpm")

# Compute HRV from PPG peaks (as ECG surrogate)
hrv = nk.hrv(info["PPG_Peaks"], sampling_rate=100)
print(f"RMSSD from PPG: {hrv['HRV_RMSSD'].values[0]:.2f} ms")
```

### Module 6: Signal Simulation

Generate synthetic physiological signals for testing and algorithm validation.

```python
import neurokit2 as nk
import matplotlib.pyplot as plt

fig, axes = plt.subplots(5, 1, figsize=(12, 10))

signals_dict = {
    "ECG":  nk.ecg_simulate(duration=5, sampling_rate=500, heart_rate=70),
    "EDA":  nk.eda_simulate(duration=5, sampling_rate=64, scr_number=2),
    "EMG":  nk.emg_simulate(duration=5, sampling_rate=1000, burst_number=2),
    "PPG":  nk.ppg_simulate(duration=5, sampling_rate=100, heart_rate=70),
    "RSP":  nk.rsp_simulate(duration=5, sampling_rate=100, respiratory_rate=15),
}

for ax, (name, signal) in zip(axes, signals_dict.items()):
    sr = {"ECG": 500, "EDA": 64, "EMG": 1000, "PPG": 100, "RSP": 100}[name]
    import numpy as np
    t = np.arange(len(signal)) / sr
    ax.plot(t, signal, lw=0.8)
    ax.set_ylabel(name)

axes[-1].set_xlabel("Time (s)")
plt.tight_layout()
plt.savefig("physiological_signals.pdf", bbox_inches="tight")
print("Synthetic signals plotted")
```

## Key Concepts

### Event-Related Analysis (Epochs)

NeuroKit2 uses `nk.events_create()` to mark stimulus onsets, then `nk.epochs_create()` to segment the continuous signal into fixed-length windows around each event. This enables ERP (event-related potential) and SCR (skin conductance response) analysis locked to stimulus timing.

### Signal Quality Index (SQI)

ECG and PPG processing includes a quality index (0–1) per sample. Quality below 0.5 indicates noisy or artifactual segments. Use `signals["ECG_Quality"] > 0.5` to mask unreliable regions before computing HRV features.

## Common Workflows

### Workflow 1: Multi-Signal Physiological Recording Analysis

```python
import neurokit2 as nk
import pandas as pd
import numpy as np

# Simulate 5-minute multi-modal recording
sr_ecg, sr_eda, sr_ppg = 250, 4, 100
duration = 300  # seconds

ecg = nk.ecg_simulate(duration=duration, sampling_rate=sr_ecg, heart_rate=72)
eda = nk.eda_simulate(duration=duration, sampling_rate=sr_eda, scr_number=15)
ppg = nk.ppg_simulate(duration=duration, sampling_rate=sr_ppg, heart_rate=72)

# Process each modality
ecg_signals, ecg_info = nk.ecg_process(ecg, sampling_rate=sr_ecg)
eda_signals, eda_info = nk.eda_process(eda, sampling_rate=sr_eda)
ppg_signals, ppg_info = nk.ppg_process(ppg, sampling_rate=sr_ppg)

# Extract HRV from ECG
hrv = nk.hrv(ecg_info["ECG_R_Peaks"], sampling_rate=sr_ecg, show=False)

# Summary table
summary = pd.Series({
    "HR_mean_bpm":       ecg_signals["ECG_Rate"].mean(),
    "HRV_RMSSD_ms":     hrv["HRV_RMSSD"].values[0],
    "HRV_LF_HF":        hrv["HRV_LFHF"].values[0],
    "SCL_mean_uS":      eda_signals["EDA_Tonic"].mean(),
    "SCR_count":        len(eda_info["SCR_Peaks"]),
    "PPG_HR_mean_bpm":  ppg_signals["PPG_Rate"].mean(),
})
print(summary.to_string())
```

### Workflow 2: Stress Detection Feature Extraction

```python
import neurokit2 as nk
import pandas as pd
import numpy as np

def extract_stress_features(ecg_array, eda_array, sr_ecg=250, sr_eda=4):
    """Extract HRV + EDA features for stress classification."""
    # ECG features
    ecg_signals, ecg_info = nk.ecg_process(ecg_array, sampling_rate=sr_ecg)
    hrv_time = nk.hrv_time(ecg_info["ECG_R_Peaks"], sampling_rate=sr_ecg)
    hrv_freq = nk.hrv_frequency(ecg_info["ECG_R_Peaks"], sampling_rate=sr_ecg)

    # EDA features
    eda_signals, eda_info = nk.eda_process(eda_array, sampling_rate=sr_eda)

    return {
        "HR_mean":    ecg_signals["ECG_Rate"].mean(),
        "RMSSD":      hrv_time["HRV_RMSSD"].values[0],
        "SDNN":       hrv_time["HRV_SDNN"].values[0],
        "LF_HF":      hrv_freq["HRV_LFHF"].values[0],
        "SCL_mean":   eda_signals["EDA_Tonic"].mean(),
        "SCR_count":  len(eda_info["SCR_Peaks"]),
        "SCR_amp_mean": eda_signals["EDA_Phasic"].mean(),
    }

# Test with simulated data
ecg = nk.ecg_simulate(duration=120, sampling_rate=250, heart_rate=85)  # elevated HR
eda = nk.eda_simulate(duration=120, sampling_rate=4, scr_number=8)

features = extract_stress_features(ecg, eda)
df = pd.DataFrame([features])
print(df.T.to_string(header=False))
```

## Key Parameters

| Parameter | Module/Function | Default | Range / Options | Effect |
|-----------|----------------|---------|-----------------|--------|
| `sampling_rate` | All `*_process` | required | 64–2048 Hz (modality-dependent) | Must match actual recording rate for correct timing |
| `method` | `ecg_peaks` | `"neurokit"` | `"neurokit"`, `"pantompkins1985"`, `"hamilton2002"`, `"elgendi2010"` | R-peak detection algorithm; "neurokit" is most robust |
| `heart_rate` | `ecg_simulate` | 70 | 30–200 bpm | Simulated ECG heart rate |
| `noise` | `ecg_simulate` | 0.01 | 0–0.5 | Gaussian noise amplitude added to simulation |
| `scr_number` | `eda_simulate` | 1 | 0–50 | Number of SCR events in simulated EDA |
| `order` | `entropy_sample` | 2 | 1–5 | Embedding dimension for entropy calculation |
| `r` | `entropy_sample` | 0.2×SD | 0.1–0.5×SD | Tolerance for sample entropy |
| `epochs_start` | `epochs_create` | -1 | negative float (s) | Seconds before event onset for epoch start |
| `epochs_end` | `epochs_create` | 3 | positive float (s) | Seconds after event onset for epoch end |

## Common Recipes

### Recipe: Batch Process Multiple ECG Files

```python
import neurokit2 as nk
import pandas as pd
from pathlib import Path
import numpy as np

results = []
for ecg_file in Path("ecg_data").glob("*.csv"):
    try:
        ecg = pd.read_csv(ecg_file)["ecg"].values
        _, info = nk.ecg_process(ecg, sampling_rate=250)
        hrv = nk.hrv_time(info["ECG_R_Peaks"], sampling_rate=250)
        results.append({
            "file": ecg_file.stem,
            "RMSSD": hrv["HRV_RMSSD"].values[0],
            "SDNN":  hrv["HRV_SDNN"].values[0],
            "pNN50": hrv["HRV_pNN50"].values[0],
        })
    except Exception as e:
        print(f"FAILED {ecg_file.name}: {e}")

df = pd.DataFrame(results)
df.to_csv("hrv_results.csv", index=False)
print(df.describe())
```

### Recipe: Artifact Rejection by Quality Index

```python
import neurokit2 as nk
import numpy as np

ecg = nk.ecg_simulate(duration=60, sampling_rate=250, noise=0.1)
signals, info = nk.ecg_process(ecg, sampling_rate=250)

# Identify low-quality R-peaks
r_peaks = info["ECG_R_Peaks"]
quality_at_peaks = signals["ECG_Quality"].iloc[r_peaks].values

good_peaks = r_peaks[quality_at_peaks > 0.5]
print(f"R-peaks before cleaning: {len(r_peaks)}")
print(f"High-quality R-peaks  : {len(good_peaks)}")

# Recompute HRV on clean peaks only
hrv_clean = nk.hrv_time(good_peaks, sampling_rate=250)
print(f"RMSSD (cleaned): {hrv_clean['HRV_RMSSD'].values[0]:.2f} ms")
```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| R-peaks detected at wrong locations | `sampling_rate` incorrect | Double-check recording metadata; wrong SR shifts all peak times |
| Extremely high HRV RMSSD (>200 ms) | Missed beats or extra detections | Switch detection method: try `method="pantompkins1985"`; inspect raw signal |
| `ecg_delineate` returns all NaN for P/Q/S/T | Recording too short (<5 seconds) or very noisy | Use ≥10 s recordings; reduce noise before calling delineate |
| EDA shows no SCR peaks in real data | Low-pass filter cutoff too aggressive or EDA sampled at wrong rate | Verify EDA sampling rate; set `phasic_method="cvx"` in `eda_phasic()` |
| Entropy functions return `NaN` | Signal too short or constant (zero variance) | Minimum 200–500 samples; ensure non-constant signal |
| EMG onset detection misses activations | Threshold auto-set too high for low-amplitude signals | Pass custom threshold: `nk.emg_activation(signal, threshold=0.5)` |
| Memory error on long recordings | DataFrame with millions of rows | Process in 60-second windows; concatenate HRV epoch results |

## Related Skills

- `matplotlib-scientific-plotting` — plotting processed neurokit2 signals and HRV Poincaré plots
- `statsmodels-statistical-modeling` — ANOVA and mixed-effects models on extracted HRV/EDA features
- `scikit-learn-machine-learning` — stress/emotion classification using extracted features

## References

- [NeuroKit2 documentation](https://neuropsychology.github.io/NeuroKit/) — API reference, tutorials, and comparison of algorithms
- [NeuroKit2 paper: Makowski et al. (2021), Behavior Research Methods](https://doi.org/10.3758/s13428-020-01516-y) — methodology and validation
- [HRV standards: Task Force (1996), Circulation](https://doi.org/10.1161/01.CIR.93.5.1043) — authoritative definitions of HRV time and frequency domain measures
- [NeuroKit2 GitHub](https://github.com/neuropsychology/NeuroKit) — source, examples, and community
- [EDA review: Boucsein (2012), Electrodermal Activity](https://doi.org/10.1007/978-1-4614-1126-0) — reference text for EDA signal interpretation
