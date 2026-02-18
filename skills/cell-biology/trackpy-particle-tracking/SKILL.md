---
name: "trackpy-particle-tracking"
description: "Python library for tracking particles (fluorescent spots, colloids, vesicles, cells) in video microscopy using the Crocker-Grier algorithm. Core modules: locate particles in single frames, batch-process image sequences, link positions into trajectories, filter short-lived tracks, and compute mean squared displacement (MSD) for diffusion analysis. Supports 2D and 3D tracking with subpixel accuracy. Integrates with pims for reading TIF stacks, AVI, and image series. Use when you need quantitative single-particle tracking (SPT) from fluorescence or brightfield video and downstream diffusion coefficient extraction."
license: "BSD-3-Clause"
---

# trackpy

## Overview

trackpy is a Python library for single-particle tracking (SPT) in video microscopy. It implements the Crocker-Grier algorithm to locate bright spots in each frame with subpixel precision, then links those positions across frames into continuous trajectories. From trajectories, trackpy computes mean squared displacement (MSD), diffusion coefficients, and motion classifications (confined, normal, directed). It handles 2D fluorescence videos, 3D confocal z-stacks, and large image sequences via memory-efficient streaming through the pims image reader library.

## When to Use

- You have a fluorescence microscopy video of labeled particles (quantum dots, fluorescent beads, vesicles, receptors) and need to extract individual trajectories and diffusion coefficients.
- You want to measure particle mobility: compute MSD curves and distinguish Brownian diffusion, directed motion, or confined motion from single-particle tracks.
- You are analyzing colloid dynamics, lipid membrane diffusion, intracellular cargo transport, or virus-cell interactions where you need per-particle trajectory data.
- You need 3D tracking from confocal z-stack time series to capture out-of-plane motion of particles or organelles.
- You want to apply drift correction to remove stage drift before computing intrinsic particle motion statistics.
- You need ensemble MSD averaged across hundreds of tracks to extract population-level diffusion behavior with statistical power.
- Use `TrackMate` (Fiji/ImageJ plugin) instead when you need a graphical interface, manual curation of tracks, or integration with biological object segmenters (Cellpose, StarDist).
- Use `napari` with `napari-trackpy` instead when you want interactive visualization and manual editing of trajectories alongside image data.

## Prerequisites

- **Python packages**: `trackpy`, `pims`, `pandas`, `numpy`, `matplotlib`, `scipy`
- **Data requirements**: Grayscale or single-channel image sequence (TIF stack, AVI, or directory of PNG/TIF frames); particles should appear as bright Gaussian spots on a darker background (or use `invert=True` for dark spots on bright background)
- **Environment**: Works in Jupyter notebooks and scripts; `pims` handles most microscopy formats; for ND2 or CZI files install `pims-nd2` or `aicsimageio`

```bash
pip install trackpy pims pandas numpy matplotlib scipy
# For reading multi-channel or proprietary formats:
pip install pims[bioformats]   # Bioformats via JPype
pip install aicsimageio        # ND2, CZI, LIF via AICSImageIO
```

## Quick Start

```python
import trackpy as tp
import pims

# Load a TIF image stack (T frames × Y × X)
frames = pims.open("particles.tif")   # shape: (T, Y, X)

# Locate particles in all frames
f = tp.batch(frames, diameter=11, minmass=500)
print(f"Found {len(f)} particle detections across {f['frame'].nunique()} frames")

# Link into trajectories
t = tp.link(f, search_range=5, memory=3)

# Remove short-lived tracks (fewer than 10 frames)
t = tp.filter_stubs(t, threshold=10)
print(f"Retained {t['particle'].nunique()} trajectories")

# Compute ensemble MSD
imsd = tp.imsd(t, mpp=0.16, fps=10)   # mpp: microns per pixel, fps: frames per second
print(imsd.head())
```

## Core API

### Module 1: tp.locate() — Single-Frame Particle Detection

`tp.locate()` finds bright circular features in one image frame using a bandpass filter followed by local maximum detection. It returns a DataFrame with subpixel x/y positions, integrated mass, signal, and eccentricity for each detected particle.

```python
import trackpy as tp
import pims
import matplotlib.pyplot as plt

frames = pims.open("particles.tif")
frame0 = frames[0]   # single 2D array

# Locate particles: diameter must be odd integer, roughly matching spot size in pixels
f0 = tp.locate(frame0, diameter=11, minmass=300, maxsize=None, separation=None)
print(f"Detected {len(f0)} particles in frame 0")
print(f0[['x', 'y', 'mass', 'size', 'ecc']].head())
# x, y: subpixel centroid; mass: integrated brightness; size: Gaussian width; ecc: eccentricity (0=circular)
```

```python
# Diagnostic plot: annotate detected particles on the raw frame
fig, ax = plt.subplots(figsize=(8, 8))
tp.annotate(f0, frame0, ax=ax, imshow_style={"cmap": "gray"})
ax.set_title(f"Frame 0: {len(f0)} particles detected")
plt.tight_layout()
plt.savefig("locate_diagnostic.png", dpi=150)
print("Saved locate_diagnostic.png")
```

### Module 2: tp.batch() — Multi-Frame Detection

`tp.batch()` applies `tp.locate()` to every frame in an image sequence and concatenates results into a single DataFrame with a `frame` column. It accepts any pims-compatible image reader or a list of 2D arrays.

```python
import trackpy as tp
import pims

frames = pims.open("particles.tif")

# Locate particles across all frames (same parameters as tp.locate)
f = tp.batch(frames, diameter=11, minmass=300, processes=1)
# processes=1 uses serial processing; set processes="auto" for multicore (requires joblib)
print(f"Total detections: {len(f)}")
print(f"Frames with data: {f['frame'].nunique()} / {len(frames)}")
print(f"Mean particles per frame: {len(f)/f['frame'].nunique():.1f}")
print(f.groupby('frame').size().describe())
```

```python
# Mass histogram: use to choose minmass cutoff
import matplotlib.pyplot as plt

fig, ax = plt.subplots(figsize=(6, 4))
f['mass'].hist(bins=40, ax=ax)
ax.axvline(300, color='red', linestyle='--', label='minmass=300')
ax.set_xlabel("Integrated mass")
ax.set_ylabel("Count")
ax.set_title("Mass distribution of detections")
ax.legend()
plt.tight_layout()
plt.savefig("mass_histogram.png", dpi=150)
print("Saved mass_histogram.png — use to refine minmass cutoff")
```

### Module 3: tp.link() — Trajectory Linking

`tp.link()` connects particle detections across frames into trajectories by solving a bipartite assignment problem (Hungarian algorithm). It adds a `particle` column (integer trajectory ID) to the positions DataFrame. `search_range` (pixels) is the maximum displacement between frames; `memory` allows a particle to disappear for up to N frames before being dropped.

```python
import trackpy as tp
import pims

frames = pims.open("particles.tif")
f = tp.batch(frames, diameter=11, minmass=300)

# Link: search_range in pixels; memory handles brief disappearances (blinking, out-of-focus)
t = tp.link(f, search_range=5, memory=3)
print(f"Number of unique trajectories: {t['particle'].nunique()}")
print(f"Trajectory length distribution:")
print(t.groupby('particle').size().describe())
```

```python
# Visualize all trajectories overlaid on the first frame
import matplotlib.pyplot as plt

fig, ax = plt.subplots(figsize=(8, 8))
tp.plot_traj(t, superimpose=frames[0], ax=ax)
ax.set_title(f"{t['particle'].nunique()} trajectories")
plt.tight_layout()
plt.savefig("trajectories.png", dpi=150)
print("Saved trajectories.png")
```

### Module 4: tp.filter_stubs() — Short-Track Removal

`tp.filter_stubs()` removes trajectories shorter than a given number of frames. Short tracks arise from noise detections, particles entering/leaving the field of view, or linking errors. Removing them improves MSD reliability because short tracks contribute high-variance MSD estimates at long lag times.

```python
import trackpy as tp
import pims

frames = pims.open("particles.tif")
f = tp.batch(frames, diameter=11, minmass=300)
t = tp.link(f, search_range=5, memory=3)

before = t['particle'].nunique()
t_filt = tp.filter_stubs(t, threshold=10)   # keep only tracks with ≥10 frames
after = t_filt['particle'].nunique()
print(f"Tracks before filtering: {before}")
print(f"Tracks after filtering (≥10 frames): {after}")
print(f"Removed {before - after} short tracks ({100*(before-after)/before:.1f}%)")
```

### Module 5: MSD Analysis — tp.imsd() and tp.emsd()

`tp.imsd()` computes per-particle mean squared displacement as a function of lag time, returning a DataFrame (lag time as index, particle ID as columns). `tp.emsd()` computes the ensemble-averaged MSD across all particles. Both require the physical scale (`mpp`, microns per pixel) and frame rate (`fps`).

```python
import trackpy as tp
import pims
import matplotlib.pyplot as plt

frames = pims.open("particles.tif")
f = tp.batch(frames, diameter=11, minmass=300)
t = tp.link(f, search_range=5, memory=3)
t = tp.filter_stubs(t, threshold=10)

mpp = 0.16    # microns per pixel (from microscope calibration)
fps = 10.0    # frames per second

# Individual MSD curves (one column per particle)
imsd = tp.imsd(t, mpp=mpp, fps=fps, max_lagtime=100)
print(f"IMSD shape: {imsd.shape}")  # (lag times) × (particles)

# Ensemble MSD
emsd = tp.emsd(t, mpp=mpp, fps=fps, max_lagtime=100)
print(f"EMSD at lag 1 s: {emsd.iloc[0]:.4f} µm²")
```

```python
# Plot ensemble MSD and fit diffusion coefficient
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import linregress

mpp = 0.16
fps = 10.0

# Fit MSD = 4*D*t (2D Brownian) over first 10 lag times
lag_s = emsd.index.values[:10]   # lag times in seconds
msd_vals = emsd.values[:10]
slope, intercept, r, p, se = linregress(lag_s, msd_vals)
D = slope / 4   # diffusion coefficient in µm²/s
print(f"Diffusion coefficient D = {D:.4f} µm²/s  (R²={r**2:.3f})")

fig, ax = plt.subplots(figsize=(6, 5))
ax.plot(emsd.index, emsd.values, 'o-', label='Ensemble MSD')
ax.plot(lag_s, slope * lag_s + intercept, 'r--', label=f'Fit: D={D:.4f} µm²/s')
ax.set_xlabel("Lag time (s)")
ax.set_ylabel("MSD (µm²)")
ax.set_title("Ensemble Mean Squared Displacement")
ax.legend()
plt.tight_layout()
plt.savefig("emsd.png", dpi=150)
print("Saved emsd.png")
```

### Module 6: Motion Analysis — Characterize and Drift Correction

`tp.motion.characterize()` computes per-trajectory statistics (mean velocity, net displacement, straightness). `tp.subtract_drift()` removes bulk stage drift from trajectories before MSD analysis.

```python
import trackpy as tp
import pims

frames = pims.open("particles.tif")
f = tp.batch(frames, diameter=11, minmass=300)
t = tp.link(f, search_range=5, memory=3)
t = tp.filter_stubs(t, threshold=10)

# Estimate and subtract drift (bulk movement of the sample/stage)
drift = tp.compute_drift(t)
print("Drift (first 5 frames):")
print(drift.head())

t_corrected = tp.subtract_drift(t.copy(), drift)
print(f"Drift subtracted from {t_corrected['particle'].nunique()} trajectories")
```

```python
import trackpy as tp

# Characterize individual trajectories (requires tp.motion module)
from trackpy import motion

# Per-particle summary statistics
char = motion.characterize(t, mpp=0.16, fps=10.0)
print(char.columns.tolist())
# Columns: 'alpha' (anomalous exponent), 'D_app' (apparent diffusion), 'r^2' (fit quality)
print(char[['alpha', 'D_app']].describe())
# alpha ~ 1.0: Brownian; alpha < 1: confined/subdiffusion; alpha > 1: directed/superdiffusion
```

## Common Workflows

### Workflow 1: Full 2D Tracking Pipeline with MSD and Diffusion Coefficient

**Goal**: Load a fluorescence video, locate and link particles across all frames, filter short tracks, compute MSD, and extract diffusion coefficients.

```python
import trackpy as tp
import pims
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import linregress

# ── 1. Load image sequence ──────────────────────────────────────────────────
frames = pims.open("fluorescence_video.tif")   # (T, Y, X) grayscale TIF stack
print(f"Loaded {len(frames)} frames, frame shape: {frames.frame_shape}")

# ── 2. Tune detection on a single frame ─────────────────────────────────────
f0 = tp.locate(frames[0], diameter=11, minmass=400)
print(f"Frame 0: {len(f0)} particles detected")
# Adjust diameter (odd integer ≥ spot size) and minmass until count looks right

# ── 3. Batch detect across all frames ───────────────────────────────────────
f = tp.batch(frames, diameter=11, minmass=400, processes=1)
print(f"Total detections: {len(f)} across {f['frame'].nunique()} frames")

# ── 4. Link into trajectories ────────────────────────────────────────────────
t = tp.link(f, search_range=6, memory=3)
print(f"Unique trajectories before filtering: {t['particle'].nunique()}")

# ── 5. Remove short trajectories ─────────────────────────────────────────────
t = tp.filter_stubs(t, threshold=15)
print(f"Trajectories after filtering (≥15 frames): {t['particle'].nunique()}")

# ── 6. Subtract stage drift ───────────────────────────────────────────────────
drift = tp.compute_drift(t)
t = tp.subtract_drift(t.copy(), drift)

# ── 7. Compute MSD ────────────────────────────────────────────────────────────
mpp = 0.16   # µm/pixel — from microscope calibration
fps = 10.0   # frames per second

emsd = tp.emsd(t, mpp=mpp, fps=fps, max_lagtime=50)
imsd = tp.imsd(t, mpp=mpp, fps=fps, max_lagtime=50)

# ── 8. Fit diffusion coefficient from linear regime (first 10 points) ─────────
n_fit = 10
lag_s = emsd.index.values[:n_fit]
msd_v = emsd.values[:n_fit]
slope, intercept, r, _, _ = linregress(lag_s, msd_v)
D = slope / 4   # MSD = 4Dt for 2D Brownian
print(f"Diffusion coefficient D = {D:.4f} µm²/s  (R²={r**2:.3f})")

# ── 9. Plot ────────────────────────────────────────────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(12, 5))

# Individual + ensemble MSD
axes[0].plot(imsd.index, imsd.values, alpha=0.2, color='steelblue', linewidth=0.8)
axes[0].plot(emsd.index, emsd.values, 'k-', linewidth=2, label='Ensemble MSD')
axes[0].plot(lag_s, slope * lag_s + intercept, 'r--', label=f'D={D:.4f} µm²/s')
axes[0].set_xlabel("Lag time (s)")
axes[0].set_ylabel("MSD (µm²)")
axes[0].set_title("MSD: individual (blue) + ensemble (black)")
axes[0].legend()

# Trajectory overlay
tp.plot_traj(t, superimpose=frames[0], ax=axes[1])
axes[1].set_title(f"{t['particle'].nunique()} trajectories")

plt.tight_layout()
plt.savefig("tracking_results.png", dpi=150, bbox_inches="tight")
print("Saved tracking_results.png")

# ── 10. Export trajectories ───────────────────────────────────────────────────
t.to_csv("trajectories.csv", index=False)
emsd.to_csv("ensemble_msd.csv")
print("Exported trajectories.csv and ensemble_msd.csv")
```

### Workflow 2: 3D Particle Tracking from Confocal Z-Stacks

**Goal**: Track particles in 3D from a time-series of confocal z-stacks (T × Z × Y × X), link in 3D, and compute 3D MSD.

```python
import trackpy as tp
import pims
import numpy as np
import matplotlib.pyplot as plt

# ── 1. Load 4D image stack (T × Z × Y × X) ─────────────────────────────────
# pims opens multi-page TIF; reshape into (T, Z, Y, X) as needed
raw = pims.open("confocal_3d_timeseries.tif")
# Assume each "frame" in pims is one Z-slice; reshape to (T, Z, Y, X)
T, n_z = 50, 20   # adjust to match acquisition
frames_4d = np.array(raw).reshape(T, n_z, raw.frame_shape[0], raw.frame_shape[1])
print(f"4D stack shape: {frames_4d.shape}")  # (T, Z, Y, X)

# ── 2. Detect in 3D (tp.locate works on 3D arrays) ─────────────────────────
# For 3D, pass a single 3D volume; diameter can be (z_diam, y_diam, x_diam)
f0_3d = tp.locate(frames_4d[0], diameter=(7, 11, 11), minmass=2000)
print(f"3D detections in t=0: {len(f0_3d)}")
print(f0_3d[['x', 'y', 'z', 'mass']].head())

# ── 3. Batch detect across all time points ──────────────────────────────────
detections = []
for t_idx in range(T):
    frame_3d = frames_4d[t_idx]    # Z × Y × X
    detected = tp.locate(frame_3d, diameter=(7, 11, 11), minmass=2000)
    detected['frame'] = t_idx
    detections.append(detected)

import pandas as pd
f3d = pd.concat(detections, ignore_index=True)
print(f"Total 3D detections: {len(f3d)}")

# ── 4. Link in 3D ────────────────────────────────────────────────────────────
# search_range in pixels; use a 3-tuple (z, y, x) for anisotropic voxels
t3d = tp.link(f3d, search_range=(3, 6, 6), memory=2)
t3d = tp.filter_stubs(t3d, threshold=10)
print(f"3D trajectories: {t3d['particle'].nunique()}")

# ── 5. Compute 3D MSD ────────────────────────────────────────────────────────
mpp_xy = 0.16   # µm/pixel in x, y
mpp_z = 0.30    # µm/pixel in z (z-step size)
fps = 1.0       # z-stack volume rate

# Scale z coordinates to µm
t3d_um = t3d.copy()
t3d_um['x'] *= mpp_xy
t3d_um['y'] *= mpp_xy
t3d_um['z'] *= mpp_z

emsd_3d = tp.emsd(t3d_um, mpp=1.0, fps=fps, max_lagtime=20)  # mpp=1 since already in µm
print(f"3D ensemble MSD (lag=1 s): {emsd_3d.iloc[0]:.4f} µm²")

# ── 6. Fit 3D diffusion coefficient (MSD = 6Dt for 3D) ─────────────────────
from scipy.stats import linregress
lag_s = emsd_3d.index.values[:8]
slope, _, r, _, _ = linregress(lag_s, emsd_3d.values[:8])
D_3d = slope / 6
print(f"3D Diffusion coefficient D = {D_3d:.4f} µm²/s  (R²={r**2:.3f})")

t3d.to_csv("trajectories_3d.csv", index=False)
print("Saved trajectories_3d.csv")
```

## Key Parameters

| Parameter | Module | Default | Range / Options | Effect |
|-----------|--------|---------|-----------------|--------|
| `diameter` | `locate`, `batch` | required | odd integer ≥ 3 (or tuple for 3D) | Approximate particle diameter in pixels; must be odd. Too small: split detections. Too large: merged detections |
| `minmass` | `locate`, `batch` | `100` | `0` to `∞` | Minimum integrated brightness; primary filter against noise. Start at 0, plot mass histogram, set to separate noise peak |
| `search_range` | `link` | required | `1`–`50` pixels | Max displacement between frames. Set to ~1.5× max expected per-frame movement |
| `memory` | `link` | `0` | `0`–`10` frames | Frames a particle may be absent before track is broken; useful for blinking fluorophores |
| `threshold` | `filter_stubs` | `1` | integer ≥ 1 | Minimum track length in frames; short tracks have unreliable MSD |
| `max_lagtime` | `imsd`, `emsd` | `100` | integer | Maximum lag time in frames for MSD calculation; use ~10–20% of total frames for reliability |
| `mpp` | `imsd`, `emsd` | `1` | float > 0 | Microns per pixel; converts pixel units to physical units (µm) |
| `fps` | `imsd`, `emsd` | `1` | float > 0 | Frames per second; converts frame lag to seconds |
| `separation` | `locate`, `batch` | `diameter+1` | integer | Minimum center-to-center distance between features; prevents double-counting dense particles |
| `invert` | `locate`, `batch` | `False` | `True`, `False` | Set `True` for dark particles on bright background (transmitted light imaging) |

## Best Practices

1. **Always tune `diameter` and `minmass` on a single frame first**: Run `tp.locate()` on one representative frame and use `tp.annotate()` to visually check detections before committing to `tp.batch()`. Over-detection wastes time; under-detection misses particles.

   ```python
   f0 = tp.locate(frames[0], diameter=11, minmass=200)
   tp.annotate(f0, frames[0])   # visual check in Jupyter
   ```

2. **Set `search_range` conservatively**: Too large a search range causes spurious links between unrelated particles in dense samples. Estimate typical per-frame displacement from `tp.locate()` output scatter before linking.

3. **Subtract drift before computing MSD**: Stage drift inflates MSD, causing overestimation of D. Always call `tp.compute_drift()` + `tp.subtract_drift()` before `tp.emsd()`.

4. **Use only the linear regime for diffusion coefficient fitting**: MSD curves become noisy at long lag times (few track pairs contribute). Fit only the first 10–20% of available lag times. Use log-log slope to detect non-Brownian behavior before fitting.

5. **Do not mix `mpp` units between locate and MSD steps**: `tp.locate()` returns positions in pixels. `mpp` is applied only in `tp.imsd()`/`tp.emsd()`. Avoid rescaling positions manually before linking, as this breaks the pixel-unit search_range.

6. **For 3D tracking with anisotropic voxels**: Pass `diameter` and `search_range` as tuples matching `(z, y, x)` axis order. The z-step is usually 2-5× coarser than xy pixel size; set the z component of `diameter` and `search_range` accordingly.

## Common Recipes

### Recipe: Drift Correction and Corrected MSD Comparison

When to use: Compare raw vs drift-corrected MSD to assess stage drift contribution.

```python
import trackpy as tp
import pims
import matplotlib.pyplot as plt

frames = pims.open("particles.tif")
f = tp.batch(frames, diameter=11, minmass=400, processes=1)
t = tp.link(f, search_range=6, memory=3)
t = tp.filter_stubs(t, threshold=15)

mpp, fps = 0.16, 10.0

# MSD without drift correction
emsd_raw = tp.emsd(t, mpp=mpp, fps=fps, max_lagtime=50)

# Subtract drift
drift = tp.compute_drift(t)
t_corr = tp.subtract_drift(t.copy(), drift)
emsd_corr = tp.emsd(t_corr, mpp=mpp, fps=fps, max_lagtime=50)

fig, ax = plt.subplots(figsize=(6, 5))
ax.loglog(emsd_raw.index, emsd_raw.values, 'r--', label='Raw MSD')
ax.loglog(emsd_corr.index, emsd_corr.values, 'b-', label='Drift-corrected MSD')
ax.set_xlabel("Lag time (s)")
ax.set_ylabel("MSD (µm²)")
ax.set_title("Effect of drift correction on MSD")
ax.legend()
plt.tight_layout()
plt.savefig("drift_correction_comparison.png", dpi=150)
print("Saved drift_correction_comparison.png")
```

### Recipe: Classify Particles by Diffusion Regime

When to use: Separate particle population into confined, normal (Brownian), and directed motion based on log-log MSD slope (anomalous exponent alpha).

```python
import trackpy as tp
import pims
import numpy as np
import pandas as pd
from scipy.stats import linregress

frames = pims.open("particles.tif")
f = tp.batch(frames, diameter=11, minmass=400, processes=1)
t = tp.link(f, search_range=6, memory=3)
t = tp.filter_stubs(t, threshold=20)

drift = tp.compute_drift(t)
t = tp.subtract_drift(t.copy(), drift)

mpp, fps = 0.16, 10.0
imsd = tp.imsd(t, mpp=mpp, fps=fps, max_lagtime=30)

# Fit log-log slope (anomalous exponent alpha) for each particle
results = []
for pid in imsd.columns:
    curve = imsd[pid].dropna()
    if len(curve) < 5:
        continue
    log_lag = np.log(curve.index.values)
    log_msd = np.log(curve.values)
    slope, intercept, r, _, _ = linregress(log_lag[:10], log_msd[:10])
    D_app = np.exp(intercept) / 4   # apparent D from intercept
    results.append({'particle': pid, 'alpha': slope, 'D_app': D_app, 'r2': r**2})

df_char = pd.DataFrame(results)

# Classify by alpha
df_char['regime'] = pd.cut(
    df_char['alpha'],
    bins=[-np.inf, 0.7, 1.3, np.inf],
    labels=['confined', 'brownian', 'directed']
)
print(df_char['regime'].value_counts())
print(f"\nMean D by regime:\n{df_char.groupby('regime')['D_app'].mean()}")

df_char.to_csv("particle_classification.csv", index=False)
print("Saved particle_classification.csv")
```

### Recipe: Filter by Eccentricity to Remove Aggregates

When to use: Exclude non-circular detections (doublets, aggregates, debris) that pass the mass threshold but are elongated.

```python
import trackpy as tp
import pims

frames = pims.open("particles.tif")
f = tp.batch(frames, diameter=11, minmass=400, processes=1)

# Eccentricity: 0 = perfect circle, 1 = line
# Remove elongated features (likely aggregates or debris)
f_round = f[f['ecc'] < 0.3]
print(f"Before ecc filter: {len(f)} detections")
print(f"After ecc filter (ecc<0.3): {len(f_round)} detections")
print(f"Removed: {len(f)-len(f_round)} elongated features")

t = tp.link(f_round, search_range=6, memory=3)
t = tp.filter_stubs(t, threshold=10)
print(f"Trajectories after eccentricity filtering: {t['particle'].nunique()}")
```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| Too many spurious detections | `minmass` too low or `diameter` mismatched to spot size | Plot mass histogram; raise `minmass` to the valley between noise and signal peaks. Verify `diameter` matches actual spot width in pixels |
| Few or zero detections | `minmass` too high, or particles are dim / out of focus | Lower `minmass`; check image contrast; apply background subtraction before locate |
| Very short trajectories (all stubs filtered out) | `search_range` too small for particle velocity, or `memory=0` with blinking | Increase `search_range` to 1.5–2× max per-frame displacement; set `memory=2` or `3` for blinking dyes |
| MSD curves are noisy or non-monotonic at long lag times | Too few tracks or fitting too many lag points | Use only first 10–20% of lag times for fitting; ensure at least 50+ trajectories for ensemble MSD |
| Drift correction makes MSD worse | Too few immobile reference particles; drift estimated from mobile particles | Include fiducial beads or immobile particles; use `tp.compute_drift()` only on particles known to be immobile |
| `MemoryError` during `tp.batch()` | All frames loaded into RAM at once | Use pims lazy reader (default); set `processes=1`; process frames in chunks using a loop over `tp.locate()` |
| 3D `locate` returns 2D positions only | Passed a 2D frame instead of a 3D volume | Confirm input array has 3 dimensions `(Z, Y, X)`; check `frames_4d[t_idx].ndim == 3` |
| Linked trajectories fragment into many short segments | Particles moving faster than `search_range` between frames | Increase `search_range`; increase `memory`; consider sub-sampling frames if frame rate is very high |

## References

- [trackpy documentation](http://soft-matter.github.io/trackpy/) — official API reference, tutorials, and notebooks
- [trackpy GitHub repository](https://github.com/soft-matter/trackpy) — source code, issue tracker, example notebooks
- [Crocker, J.C. & Grier, D.G. (1996). Methods of Digital Video Microscopy for Colloidal Studies. *J. Colloid Interface Sci.* 179, 298–310](https://doi.org/10.1006/jcis.1996.0217) — original algorithm paper
- [pims documentation](http://soft-matter.github.io/pims/) — image sequence reader library that integrates with trackpy
- [trackpy walkthrough notebook](https://github.com/soft-matter/trackpy/blob/master/doc/tutorial/walkthrough.ipynb) — step-by-step tutorial for 2D tracking
