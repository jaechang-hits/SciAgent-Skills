---
name: "napari-image-viewer"
description: "Interactive viewer for microscopy. Displays 2D/3D/4D arrays as Image, Labels, Points, Shapes, Tracks layers; supports annotation, plugin analysis, headless screenshots. Core visualization for Python bioimage workflows. Use ImageJ/FIJI for macro processing; napari for Python-native interactive visualization and DL segmentation review."
license: "BSD-3-Clause"
---

# napari — Multi-dimensional Image Viewer

## Overview

napari is a fast, interactive multi-dimensional viewer for scientific data built on PyQt5 and VisPy. It displays NumPy arrays and zarr arrays as layered visualizations — Image layers for raw data, Labels layers for segmentation masks, Points layers for cell centroids, and Shapes layers for ROI annotations. napari integrates with scikit-image, Cellpose, and StarDist via plugins, making it the standard visualization and annotation tool in Python bioimage analysis pipelines. For headless environments (HPC, CI), napari supports offscreen rendering and `viewer.screenshot()` for automated figure generation.

## When to Use

- Visually inspecting and quality-checking microscopy images and segmentation masks before quantitative analysis
- Annotating training data for deep learning segmentation models (Cellpose, StarDist)
- Overlaying multiple image channels (DAPI, GFP, mCherry) with independent contrast and colormap control
- Reviewing 3D z-stacks and 4D time-lapse experiments with slider-based navigation
- Exporting annotated screenshots or label masks from GUI for publication figures
- Running plugin-based analysis (Cellpose napari plugin, StarDist plugin, n2v denoising) interactively
- Use **ImageJ/FIJI** for macro/batch scripting with minimal Python dependency
- Use **ITK-SNAP** as an alternative for medical imaging (DICOM, NIfTI) segmentation

## Prerequisites

- **Python packages**: `napari`, `numpy`, `scikit-image`
- **Qt backend**: requires display server; for headless use `QT_QPA_PLATFORM=offscreen`
- **Optional plugins**: `napari-cellpose`, `napari-stardist`, `napari-animation`

```bash
# Install with all backends
pip install "napari[all]"

# Or minimal install
pip install napari pyqt5

# Verify
python -c "import napari; print(napari.__version__)"
# 0.5.5

# Install useful plugins
pip install napari-cellpose napari-animation
```

## Quick Start

```python
import napari
import numpy as np
from skimage import data

# Open viewer with a sample image
viewer = napari.Viewer()
viewer.add_image(data.cells3d()[:, 1, :, :], name="DAPI", colormap="blue")
napari.run()   # blocks until viewer closed (use in scripts)
```

## Core API

### Module 1: Image Layer — Display Raw Images

Add and configure multi-channel image layers.

```python
import napari
import numpy as np
from skimage import io

viewer = napari.Viewer()

# Add single grayscale image
img = io.imread("cells.tif")  # shape: (H, W)
viewer.add_image(img, name="phase contrast", colormap="gray",
                 contrast_limits=[0, img.max()])

# Add multichannel image (3 channels)
img_mc = io.imread("multichannel.tif")  # shape: (H, W, 3)
viewer.add_image(img_mc[..., 0], name="DAPI", colormap="blue", blending="additive")
viewer.add_image(img_mc[..., 1], name="GFP", colormap="green", blending="additive")
viewer.add_image(img_mc[..., 2], name="mCherry", colormap="red", blending="additive")

print(f"Layers: {[l.name for l in viewer.layers]}")
```

### Module 2: Labels Layer — Visualize Segmentation Masks

Display and edit integer label masks from Cellpose, StarDist, or scikit-image.

```python
import napari
import numpy as np
from skimage import io

viewer = napari.Viewer()

img = io.imread("cells.tif")
masks = np.load("masks.npy")  # integer label array: 0=background, 1..N=cells

# Add raw image
viewer.add_image(img, name="raw", colormap="gray")

# Add label mask (each cell gets a unique random color)
label_layer = viewer.add_labels(masks, name="cell_masks", opacity=0.5)

# Access labels for editing
print(f"Unique cells: {len(np.unique(masks)) - 1}")
print(f"Label layer data shape: {label_layer.data.shape}")
```

### Module 3: Points Layer — Mark Cell Centroids

Add and style point markers for centroids, landmarks, or detected features.

```python
import napari
import numpy as np
import pandas as pd
from skimage.measure import regionprops_table

viewer = napari.Viewer()

# Compute centroids from label mask
masks = np.load("masks.npy")
props = regionprops_table(masks, properties=["centroid", "label"])
centroids = np.column_stack([props["centroid-0"], props["centroid-1"]])

# Add centroids as Points layer
viewer.add_points(
    centroids,
    name=f"centroids ({len(centroids)} cells)",
    size=8,
    face_color="yellow",
    edge_color="black",
    edge_width=0.5,
)
print(f"Cells marked: {len(centroids)}")
```

### Module 4: Shapes Layer — Draw ROIs and Annotations

Add bounding boxes, polygons, and line annotations.

```python
import napari
import numpy as np

viewer = napari.Viewer()

# Add rectangles as ROIs (format: [[y1, x1], [y2, x2]])
rois = [
    np.array([[50, 100], [200, 300]]),   # ROI 1
    np.array([[300, 150], [450, 350]]),  # ROI 2
]

shapes_layer = viewer.add_shapes(
    rois,
    shape_type="rectangle",
    name="ROIs",
    edge_color="cyan",
    face_color="transparent",
    edge_width=2,
)

# Retrieve shapes data for analysis
for i, shape in enumerate(shapes_layer.data):
    y_min, x_min = shape.min(axis=0)
    y_max, x_max = shape.max(axis=0)
    print(f"ROI {i+1}: y={y_min:.0f}-{y_max:.0f}, x={x_min:.0f}-{x_max:.0f}")
```

### Module 5: 3D and Time-lapse Visualization

Display z-stacks and time series with sliders.

```python
import napari
import numpy as np
from skimage import data

viewer = napari.Viewer()

# 3D z-stack: shape (Z, H, W)
zstack = data.cells3d()[:, 1, :, :]   # nuclei channel
viewer.add_image(zstack, name="z-stack nuclei",
                 colormap="cyan", blending="additive")

# 4D time-lapse: shape (T, H, W) or (T, Z, H, W)
timelapse = np.random.randint(0, 65535, (10, 256, 256), dtype=np.uint16)
viewer.add_image(timelapse, name="timelapse", colormap="gray")

# napari shows axis sliders automatically for ndim > 2
print(f"z-stack shape: {zstack.shape} → slider for Z axis")
print(f"timelapse shape: {timelapse.shape} → sliders for T axis")
```

### Module 6: Headless Screenshot Export

Export screenshots without a display (for HPC and CI environments).

```python
import os
os.environ["QT_QPA_PLATFORM"] = "offscreen"  # must be set BEFORE importing napari

import napari
import numpy as np
from skimage import io, data
import matplotlib
matplotlib.use("Agg")  # also set matplotlib backend

viewer = napari.Viewer(show=False)

img = data.cells3d()[30, 1, :, :]  # single z-slice
masks = (img > img.mean()).astype(int)  # simple threshold mask

viewer.add_image(img, name="DAPI", colormap="blue", blending="additive")
viewer.add_labels(masks.astype(np.int32), name="masks", opacity=0.5)

# Export screenshot
screenshot = viewer.screenshot(path="napari_export.png", canvas_only=True)
print(f"Screenshot saved: napari_export.png ({screenshot.shape})")
viewer.close()
```

## Key Parameters

| Parameter | Module | Default | Effect |
|-----------|--------|---------|--------|
| `colormap` | `add_image` | `"gray"` | Colormap name (matplotlib cmaps + napari built-ins: "green", "blue", "cyan") |
| `contrast_limits` | `add_image` | auto | `[min, max]` intensity clipping for display |
| `blending` | `add_image` | `"translucent"` | `"additive"` for multichannel overlay; `"opaque"` for solid |
| `opacity` | `add_labels` | `0.7` | 0–1 transparency of label layer over image |
| `face_color` | `add_points` | `"white"` | Point fill color (name, hex, or RGBA) |
| `size` | `add_points` | `10` | Point radius in data coordinates (pixels) |
| `edge_width` | `add_shapes` | `1` | Shape outline width in pixels |
| `show` | `Viewer()` | `True` | `False` for headless/offscreen mode |
| `ndisplay` | `Viewer()` | `2` | `3` for 3D OpenGL rendering mode |
| `canvas_only` | `screenshot()` | `False` | `True` to exclude the napari toolbar from export |

## Common Workflows

### Workflow 1: Review Cellpose Segmentation Quality

```python
import os
os.environ["QT_QPA_PLATFORM"] = "offscreen"

import napari
import numpy as np
from cellpose import models
from skimage import io
from skimage.measure import regionprops_table

# Segment with Cellpose
img = io.imread("cells.tif")
model = models.Cellpose(model_type="cyto3", gpu=False)
masks, _, _, diams = model.eval(img, diameter=0, channels=[0, 0])

# Visualize in napari (headless for export)
viewer = napari.Viewer(show=False)
viewer.add_image(img, name="raw", colormap="gray")
viewer.add_labels(masks, name=f"masks ({masks.max()} cells)", opacity=0.6)

# Add centroids
props = regionprops_table(masks, properties=["centroid"])
centroids = np.column_stack([props["centroid-0"], props["centroid-1"]])
viewer.add_points(centroids, name="centroids", size=6, face_color="yellow")

viewer.screenshot(path="segmentation_review.png", canvas_only=True)
viewer.close()
print(f"QC export: segmentation_review.png — {masks.max()} cells detected")
```

### Workflow 2: Multi-channel FISH Image Analysis

```python
import napari
import numpy as np
from skimage import io

# Load 4-channel FISH image: DAPI + 3 RNA probes
img = io.imread("fish_4channel.tif")  # shape: (H, W, 4)

viewer = napari.Viewer()
channels = [
    ("DAPI", "blue", img[..., 0]),
    ("probe_A_cy3", "yellow", img[..., 1]),
    ("probe_B_cy5", "red", img[..., 2]),
    ("probe_C_gfp", "green", img[..., 3]),
]

for name, colormap, channel in channels:
    viewer.add_image(channel, name=name, colormap=colormap,
                     blending="additive",
                     contrast_limits=[channel.min(), np.percentile(channel, 99.5)])

napari.run()
```

## Common Recipes

### Recipe 1: Export All Layers as Annotated Figure

```python
import os
os.environ["QT_QPA_PLATFORM"] = "offscreen"

import napari
import numpy as np
from skimage import io
import matplotlib.pyplot as plt

viewer = napari.Viewer(show=False)

img = io.imread("cells.tif")
masks = np.load("masks.npy")

viewer.add_image(img, name="raw", colormap="gray")
viewer.add_labels(masks, name="segmentation", opacity=0.5)

# Set camera zoom and position
viewer.camera.zoom = 1.5
viewer.camera.center = (img.shape[0] // 2, img.shape[1] // 2)

screenshot = viewer.screenshot(path="figure_panel.png", canvas_only=True)
viewer.close()

# Add scalebar with matplotlib
fig, ax = plt.subplots(figsize=(6, 6))
ax.imshow(screenshot)
ax.axis("off")
plt.tight_layout()
plt.savefig("figure_final.pdf", dpi=300, bbox_inches="tight")
print("Exported: figure_final.pdf")
```

### Recipe 2: Batch Export Z-stack Projections

```python
import os
os.environ["QT_QPA_PLATFORM"] = "offscreen"

import napari
import numpy as np
from skimage import io
from pathlib import Path

output_dir = Path("projections")
output_dir.mkdir(exist_ok=True)

for img_path in sorted(Path("zstacks").glob("*.tif")):
    zstack = io.imread(img_path)  # shape: (Z, H, W)
    max_proj = zstack.max(axis=0)
    
    viewer = napari.Viewer(show=False)
    viewer.add_image(max_proj, name="max_projection", colormap="gray")
    viewer.screenshot(path=str(output_dir / f"{img_path.stem}_maxproj.png"), canvas_only=True)
    viewer.close()
    print(f"Exported: {img_path.stem}_maxproj.png")

print("All z-stack projections exported.")
```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `qt.qpa.plugin: Could not load the Qt platform plugin "xcb"` | Missing display or Qt platform plugin | Set `QT_QPA_PLATFORM=offscreen` before importing napari; install `libxcb-util-dev` |
| napari window does not open | Running in SSH without X forwarding | Use `viewer = napari.Viewer(show=False)` and export via `screenshot()` |
| Slow rendering of large images | Image too large for GPU VRAM | Use `viewer.add_image(img, multiscale=True)` for pyramidal rendering |
| Labels layer shows wrong colors | Mask dtype overflow | Ensure masks are `int32` not `uint8` (overflow at 255 cells) |
| `napari.run()` blocks Jupyter notebook | Qt event loop conflict | Use `%gui qt` magic in Jupyter; or use `viewer.show()` without `napari.run()` |
| Screenshot is black/empty | Viewer not fully rendered before screenshot | Add `viewer.update()` or slight delay before `screenshot()` |
| Plugin not appearing in menu | Plugin not installed or wrong napari version | `pip install napari-<plugin>`; check napari version compatibility on napari-hub |
| 3D rendering slow | Complex geometry or large volume | Switch `viewer.dims.ndisplay = 2`; reduce z-stack depth |

## References

- [napari documentation](https://napari.org/stable/) — official API reference and tutorials
- [napari GitHub: napari/napari](https://github.com/napari/napari) — source code and plugin development guide
- Sofroniew N et al. (2022) "napari: a multi-dimensional image viewer for Python" — *Zenodo*. [DOI:10.5281/zenodo.3555620](https://doi.org/10.5281/zenodo.3555620)
- [napari-hub](https://www.napari-hub.org/) — plugin registry with 300+ community analysis plugins
