---
name: "pathml"
description: "PathML is an open-source toolkit for computational pathology. Use it to process whole-slide images (WSIs): load slides, extract tiles, apply stain normalization and nuclear segmentation preprocessing, extract features, and train machine learning models. Supports H&E and multiplex imaging. Ideal for building end-to-end digital pathology pipelines from raw WSI files to quantitative outputs."
license: "GPL-2.0"
---

# pathml

## Overview

PathML is a Python toolkit designed for computational pathology workflows on whole-slide images (WSIs). It provides a unified pipeline from raw slide files (SVS, NDPI, MRXS, TIFF) through tile extraction, preprocessing (stain normalization, nuclear segmentation, tissue detection), feature extraction, and machine learning. PathML integrates with popular Python ML and image processing libraries while abstracting the complexity of WSI handling through its `SlideData` and `Pipeline` abstractions.

## When to Use

- **Processing whole-slide H&E images**: Tiling a large WSI, normalizing staining variability across slides from different scanners or batches.
- **Nuclear segmentation on pathology slides**: Detecting and segmenting nuclei in H&E or DAPI-stained WSIs using built-in segmentation pipelines.
- **Building ML training datasets from WSIs**: Extracting tiles with associated labels for training tissue classifiers, tumor detectors, or survival prediction models.
- **Multiplex immunofluorescence (mIF) image analysis**: Processing multi-channel IF slides with channel-specific preprocessing and feature extraction.
- **Stain normalization across cohorts**: Applying Macenko or Vahadane stain normalization to harmonize H&E slides from multiple institutions.
- **Feature extraction for downstream ML**: Extracting handcrafted or deep learning features from tiles for patient-level prediction tasks.
- For standard 2D microscopy images (non-WSI), use `scikit-image` or `cellpose` directly without PathML overhead.

## Prerequisites

- **Python packages**: `pathml`, `torch`, `torchvision`, `numpy`, `scikit-image`, `openslide-python`
- **System**: OpenSlide C library (required for WSI reading)
- **Data requirements**: WSI files in SVS, NDPI, MRXS, or TIFF format; GPU recommended for segmentation
- **Environment**: Python 3.8+, CUDA-compatible GPU for deep learning preprocessing

```bash
# Install system dependency first
conda install -c conda-forge openslide

# Install PathML
pip install pathml

# For GPU support
pip install torch torchvision --extra-index-url https://download.pytorch.org/whl/cu118
```

## Quick Start

```python
from pathml.core import SlideData
from pathml.preprocessing import Pipeline
from pathml.preprocessing.transforms import BoxBlur, TissueDetectionHE

# Load → build pipeline → tile → preprocess
slide = SlideData("tumor.svs", name="demo")
pipeline = Pipeline([BoxBlur(kernel_size=3), TissueDetectionHE(mask_name="tissue")])
slide.run(pipeline, tile_size=256, tile_stride=256)

# Inspect tiles
from pathml.core import Tile
tiles = [t for t in slide.tiles if t.masks["tissue"].any()]
print(f"Tissue tiles: {len(tiles)} of {len(slide.tiles)}")
```

## Workflow

### Step 1: Load a Whole-Slide Image

```python
from pathml.core import SlideData

# Load an H&E whole-slide image
slide = SlideData("path/to/slide.svs", name="tumor_slide_001")
print(f"Slide name: {slide.name}")
print(f"Slide shape: {slide.slide.shape}")
print(f"Slide properties: {slide.slide.properties}")
```

### Step 2: Define a Preprocessing Pipeline

```python
from pathml.preprocessing import Pipeline
from pathml.preprocessing.transforms import (
    BoxBlur,
    TissueDetectionHE,
    HEStainNormalization,
)

# Build a preprocessing pipeline for H&E slides
pipeline = Pipeline([
    BoxBlur(kernel_size=5),                       # smooth image
    TissueDetectionHE(mask_name="tissue"),         # detect tissue regions
    HEStainNormalization(target="normalize"),       # normalize H&E staining
])
print(f"Pipeline steps: {len(pipeline.transforms)}")
```

### Step 3: Create a TileDataset

```python
from pathml.core import TileDataset

# Tile the slide into 256x256 patches at 20x magnification
slide.generate_tiles(
    shape=(256, 256),
    stride=(256, 256),
    pad=False,
    level=0,           # pyramid level 0 = highest resolution
    coords_format="fractional",
)
print(f"Total tiles generated: {len(slide.tiles)}")
```

### Step 4: Run the Preprocessing Pipeline

```python
# Apply preprocessing pipeline to all tiles
slide.run(pipeline, distributed=False, tile_pad=False)
print("Pipeline complete — tiles preprocessed")

# Inspect a single tile
tile = slide.tiles[0]
print(f"Tile shape: {tile.image.shape}")      # (256, 256, 3)
print(f"Tile masks: {list(tile.masks.keys())}")
```

### Step 5: Nuclear Segmentation

```python
from pathml.preprocessing.transforms import NuclearSegmentation

# Run Hematoxylin-channel nuclear segmentation
seg_pipeline = Pipeline([
    TissueDetectionHE(mask_name="tissue"),
    NuclearSegmentation(mask_name="nuclei"),
])

slide.run(seg_pipeline, distributed=False)

# Count nuclei per tile
for tile in list(slide.tiles)[:5]:
    n_nuclei = tile.masks["nuclei"].max()
    print(f"Tile {tile.coords}: {n_nuclei} nuclei detected")
```

### Step 6: Feature Extraction

```python
import numpy as np
from pathml.core import SlideDataset

features = []
for tile in slide.tiles:
    if "tissue" in tile.masks and tile.masks["tissue"].any():
        img = tile.image
        feat = {
            "mean_r":    img[:, :, 0].mean(),
            "mean_g":    img[:, :, 1].mean(),
            "mean_b":    img[:, :, 2].mean(),
            "std_r":     img[:, :, 0].std(),
            "n_nuclei":  int(tile.masks["nuclei"].max()) if "nuclei" in tile.masks else 0,
            "tile_x":    tile.coords[0],
            "tile_y":    tile.coords[1],
        }
        features.append(feat)

import pandas as pd
df = pd.DataFrame(features)
df.to_csv("slide_features.csv", index=False)
print(f"Extracted features from {len(df)} tissue tiles -> slide_features.csv")
```

### Step 7: Save and Export Processed Slide

```python
import h5py

# Save slide data (tiles + masks) to HDF5
slide.write("processed_slide.h5")
print("Slide saved to processed_slide.h5")

# Reload for downstream use
from pathml.core import SlideData
slide_loaded = SlideData.read("processed_slide.h5")
print(f"Reloaded: {len(slide_loaded.tiles)} tiles")
```

## Key Parameters

| Parameter | Default | Range / Options | Effect |
|-----------|---------|-----------------|--------|
| `shape` | `(256, 256)` | `(64,64)` – `(1024,1024)` | Tile dimensions in pixels |
| `stride` | equals `shape` | any tuple ≤ `shape` | Step between tile centers; `stride < shape` gives overlapping tiles |
| `level` | `0` | `0` – max pyramid level | Pyramid resolution level (0 = full resolution) |
| `kernel_size` | `5` | odd integers `3`–`21` | Smoothing kernel size in `BoxBlur` |
| `mask_name` | required | any string | Name of output mask stored in `tile.masks` |
| `distributed` | `False` | `True`, `False` | Enable Dask distributed processing for large slides |
| `pad` | `False` | `True`, `False` | Pad edge tiles to full `shape` size |

## Common Recipes

### Recipe: Tissue-Only Tile Filtering

When to use: Exclude background tiles to reduce memory and computation in downstream steps.

```python
# Filter tiles to only tissue regions after running tissue detection pipeline
tissue_tiles = [t for t in slide.tiles if "tissue" in t.masks and t.masks["tissue"].mean() > 0.5]
print(f"Tissue tiles: {len(tissue_tiles)} / {len(slide.tiles)} total")
```

### Recipe: Export Tiles as PNG Files

When to use: Create a labeled tile dataset for training a custom classifier in PyTorch.

```python
from PIL import Image
import numpy as np
from pathlib import Path

output_dir = Path("tiles_png")
output_dir.mkdir(exist_ok=True)

for i, tile in enumerate(slide.tiles):
    if "tissue" in tile.masks and tile.masks["tissue"].mean() > 0.5:
        img = Image.fromarray(tile.image.astype(np.uint8))
        img.save(output_dir / f"tile_{i:05d}_x{tile.coords[0]}_y{tile.coords[1]}.png")

print(f"Saved {i+1} tiles to {output_dir}/")
```

### Recipe: Batch Process Multiple Slides

When to use: Running the same preprocessing pipeline on a directory of WSI files.

```python
from pathlib import Path
from pathml.core import SlideData
from pathml.preprocessing import Pipeline
from pathml.preprocessing.transforms import TissueDetectionHE, HEStainNormalization

pipeline = Pipeline([
    TissueDetectionHE(mask_name="tissue"),
    HEStainNormalization(target="normalize"),
])

wsi_dir = Path("slides/")
for wsi_path in sorted(wsi_dir.glob("*.svs")):
    slide = SlideData(str(wsi_path), name=wsi_path.stem)
    slide.generate_tiles(shape=(256, 256), stride=(256, 256), level=0)
    slide.run(pipeline, distributed=False)
    slide.write(f"processed/{wsi_path.stem}.h5")
    print(f"Processed {wsi_path.name}: {len(slide.tiles)} tiles")
```

## Expected Outputs

- `slide.tiles` — iterable of `Tile` objects, each with `.image` (numpy array) and `.masks` (dict of numpy arrays)
- `slide_features.csv` — tabular per-tile features (color statistics, nucleus counts, coordinates)
- `processed_slide.h5` — HDF5 file with tiles, masks, and metadata for downstream use
- PNG tile files (optional) — ready for PyTorch `ImageFolder` dataset loading

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `openslide.lowlevel.OpenSlideUnsupportedFormatError` | OpenSlide C library not installed or WSI format unsupported | `conda install -c conda-forge openslide`; check format compatibility |
| `CUDA out of memory` during segmentation | Tile size too large for GPU | Reduce tile `shape` to `(128, 128)` or run with `distributed=False` on CPU |
| `slide.tiles` is empty after generate_tiles | Level index out of range or all tiles filtered | Use `level=0`; check slide pyramid with `slide.slide.level_count` |
| Stain normalization produces black tiles | Source slide too low contrast or failed tissue detection | Apply `TissueDetectionHE` before normalization; inspect tissue mask coverage |
| `KeyError: 'nuclei'` in tile.masks | Segmentation pipeline not yet run | Run the `NuclearSegmentation` pipeline with `slide.run()` before accessing masks |
| Very slow tile generation | High-resolution level 0 on large SVS | Use a lower pyramid level (`level=1` or `level=2`) for faster prototyping |
| `AttributeError: SlideData has no attribute 'write'` | Old PathML version | `pip install --upgrade pathml` to get HDF5 save/load support |

## References

- [PathML Documentation](https://pathml.readthedocs.io/) — official docs with tutorials
- [PathML GitHub (Dana-Farber/PathML)](https://github.com/Dana-Farber-AIOS/pathml) — source code and examples
- [Rosenthal et al. (2022), Cell Systems — PathML paper](https://doi.org/10.1016/j.cels.2022.01.004) — original publication
- [OpenSlide Documentation](https://openslide.org/) — WSI reading library underlying PathML
