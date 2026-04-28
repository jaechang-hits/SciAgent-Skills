---
name: "scikit-image-processing"
description: "Python image processing for microscopy and bioimage analysis. Read/write images, filter (Gaussian, median, LoG), segment (thresholding, watershed, active contours), measure region properties, detect features. SciPy/NumPy ecosystem. Use OpenCV for real-time video; CellPose for DL cell segmentation; napari for visualization."
license: "BSD-3-Clause"
---

# scikit-image — Scientific Image Processing

## Overview

scikit-image is a Python library for image processing in the SciPy ecosystem. It provides algorithms for reading/writing images, filtering (noise reduction, edge detection), geometric transforms, segmentation (thresholding, watershed, active contours), object measurement (area, intensity, shape descriptors), and feature detection. Images are represented as NumPy arrays, enabling seamless integration with NumPy, SciPy, matplotlib, and pandas. Widely used for fluorescence microscopy, histology, and general bioimage analysis.

## When to Use

- Preprocessing fluorescence microscopy images: background subtraction, denoising, illumination correction
- Segmenting cells, nuclei, or organelles using thresholding or watershed
- Measuring object properties: area, perimeter, intensity statistics, shape descriptors
- Applying morphological operations: erosion, dilation, opening, closing, fill holes
- Detecting keypoints or local features in biological images
- Converting between image formats and color spaces
- Use `OpenCV` instead for real-time video processing or GPU-accelerated operations
- For deep-learning cell segmentation, use `CellPose` instead (better accuracy for touching cells)
- Use `napari` instead for interactive multi-dimensional image visualization and annotation
- For whole-slide image tiling, use `PathML` or `histolab` instead

## Prerequisites

- **Python packages**: `scikit-image`, `numpy`, `scipy`, `matplotlib`
- **Input requirements**: Images as files (TIFF, PNG, JPEG) or NumPy arrays; fluorescence images as 2D/3D grayscale arrays
- **Environment**: Python 3.9+

```bash
pip install scikit-image numpy scipy matplotlib

# For reading proprietary microscopy formats
pip install tifffile aicsimageio

# Verify
python -c "import skimage; print(skimage.__version__)"
```

## Quick Start

```python
from skimage import io, filters, measure
import numpy as np

# Load → denoise → threshold → measure
img = io.imread("cells.tif")
img_smooth = filters.gaussian(img, sigma=1.5)
threshold = filters.threshold_otsu(img_smooth)
binary = img_smooth > threshold

regions = measure.regionprops(measure.label(binary))
print(f"Found {len(regions)} objects")
print(f"Mean area: {np.mean([r.area for r in regions]):.1f} px²")
```

## Core API

### Module 1: Image I/O and Data Types

```python
from skimage import io, img_as_float, img_as_uint
import numpy as np

# Read single image
img = io.imread("nuclei.tif")
print(f"Shape: {img.shape}, dtype: {img.dtype}")  # (512, 512), uint16

# Read image collection from directory
from skimage import io as ski_io
images = ski_io.ImageCollection("data/*.tif")
print(f"Loaded {len(images)} images")

# Type conversions (critical for correct arithmetic)
img_f = img_as_float(img)      # uint16 → float64, range [0, 1]
img_u8 = (img_f * 255).astype(np.uint8)  # → 8-bit

# Save image
io.imsave("output.tif", img_u8)
```

```python
# Multi-channel fluorescence (TIFF with CZYX or ZCYX dims)
import tifffile

stack = tifffile.imread("multichannel.tif")  # shape: (C, Z, Y, X)
dapi = stack[0]   # DAPI channel
gfp = stack[1]    # GFP channel
print(f"DAPI: {dapi.shape}, GFP: {gfp.shape}")

# Maximum intensity projection along Z
mip = dapi.max(axis=0)
io.imsave("dapi_mip.tif", mip)
```

### Module 2: Filters and Preprocessing

```python
from skimage import filters, restoration
import numpy as np

# Gaussian blur (denoising, smoothing)
from skimage.filters import gaussian
smoothed = gaussian(img, sigma=2.0)

# Median filter (salt-and-pepper noise removal)
from skimage.filters import median
from skimage.morphology import disk
denoised = median(img, footprint=disk(3))

# Top-hat transform (background subtraction for uneven illumination)
from skimage.morphology import white_tophat, disk
background_removed = white_tophat(img, footprint=disk(50))
print(f"Background removed: range [{background_removed.min()}, {background_removed.max()}]")
```

```python
# Edge detection
from skimage.filters import sobel, laplace, prewitt

edges_sobel = sobel(img_as_float(img))
edges_laplace = laplace(img_as_float(img))

# Difference of Gaussians (blob-like structure detection)
from skimage.filters import difference_of_gaussians
blob_enhanced = difference_of_gaussians(img_as_float(img), low_sigma=1, high_sigma=3)

# Contrast enhancement (CLAHE: local histogram equalization)
from skimage.exposure import equalize_adapthist
enhanced = equalize_adapthist(img_as_float(img), clip_limit=0.03)
```

### Module 3: Thresholding and Segmentation

```python
from skimage import filters, morphology, segmentation
from skimage.color import label2rgb
import numpy as np

# Automatic thresholding methods
from skimage.filters import (threshold_otsu, threshold_li,
                              threshold_triangle, threshold_yen)

img_f = img_as_float(img)
print(f"Otsu: {threshold_otsu(img_f):.3f}")
print(f"Li: {threshold_li(img_f):.3f}")

# Apply threshold and clean binary mask
binary = img_f > threshold_otsu(img_f)
binary_clean = morphology.remove_small_objects(binary, min_size=50)
binary_filled = morphology.remove_small_holes(binary_clean, area_threshold=100)
```

```python
# Watershed segmentation (separate touching objects)
from skimage.segmentation import watershed
from skimage.feature import peak_local_max
from scipy import ndimage as ndi

# Distance transform → local maxima → watershed
distance = ndi.distance_transform_edt(binary_filled)
coords = peak_local_max(distance, min_distance=20, labels=binary_filled)
mask = np.zeros(distance.shape, dtype=bool)
mask[tuple(coords.T)] = True
markers = ndi.label(mask)[0]
labels = watershed(-distance, markers, mask=binary_filled)

print(f"Segmented objects: {labels.max()}")
overlay = label2rgb(labels, image=img_f, bg_label=0)
```

### Module 4: Morphological Operations

```python
from skimage.morphology import (erosion, dilation, opening, closing,
                                 disk, ball, binary_erosion, binary_dilation)

# Erosion and dilation
eroded = erosion(binary, footprint=disk(3))
dilated = dilation(binary, footprint=disk(5))

# Opening: erosion then dilation (removes small objects, smooths edges)
opened = opening(binary, footprint=disk(3))

# Closing: dilation then erosion (fills small holes)
closed = closing(binary, footprint=disk(5))

# Skeletonization
from skimage.morphology import skeletonize
skeleton = skeletonize(binary)
print(f"Skeleton pixels: {skeleton.sum()}")
```

### Module 5: Measurement and Region Properties

```python
from skimage import measure
import pandas as pd

# Label connected components
labeled = measure.label(binary_filled)

# Extract region properties
props = measure.regionprops(labeled, intensity_image=img_as_float(img))

# Convert to DataFrame
data = []
for r in props:
    data.append({
        "label": r.label,
        "area": r.area,
        "perimeter": r.perimeter,
        "eccentricity": r.eccentricity,
        "mean_intensity": r.mean_intensity,
        "max_intensity": r.max_intensity,
        "centroid_y": r.centroid[0],
        "centroid_x": r.centroid[1],
        "bbox": r.bbox,
    })

df = pd.DataFrame(data)
print(f"Objects: {len(df)}")
print(df[["area", "mean_intensity", "eccentricity"]].describe().round(2))
```

```python
# Filter by property thresholds
cells = df[(df["area"] > 100) & (df["area"] < 5000) & (df["eccentricity"] < 0.9)]
print(f"Valid cells: {len(cells)}")

# Measure co-localization: fraction of channel-1 signal in channel-2 positive mask
from skimage.measure import regionprops_table
import numpy as np

# For multi-channel images
table = regionprops_table(
    labeled, intensity_image=np.stack([dapi, gfp], axis=-1),
    properties=["label", "area", "mean_intensity"]
)
```

### Module 6: Feature Detection and Transforms

```python
from skimage.feature import blob_log, blob_dog, corner_harris, corner_peaks
from skimage import transform

# Laplacian of Gaussian blob detection (nuclei, puncta)
blobs = blob_log(img_as_float(img), min_sigma=5, max_sigma=20,
                  num_sigma=5, threshold=0.05)
print(f"Blobs detected: {len(blobs)}")
# blobs columns: [y, x, sigma] where radius = sqrt(2) * sigma

# Difference of Gaussians (faster alternative)
blobs_dog = blob_dog(img_as_float(img), min_sigma=5, max_sigma=20, threshold=0.02)
```

```python
# Geometric transforms
from skimage import transform

# Rescale
img_small = transform.rescale(img_as_float(img), 0.5)

# Rotate
img_rotated = transform.rotate(img_as_float(img), angle=15, resize=True)

# Affine registration (align two images)
from skimage.registration import phase_cross_correlation
shift, error, _ = phase_cross_correlation(ref_img, moving_img)
print(f"Alignment shift: {shift} px, error: {error:.4f}")
```

## Key Concepts

### Image Arrays and Conventions

scikit-image represents images as NumPy arrays. Shape conventions:

| Image Type | Shape | dtype |
|-----------|-------|-------|
| Grayscale 2D | `(H, W)` | uint8, uint16, float64 |
| RGB color | `(H, W, 3)` | uint8 |
| Multichannel | `(H, W, C)` | any |
| Z-stack | `(Z, H, W)` | any |

**dtype matters**: Most algorithms expect `float64` in [0, 1]. Use `img_as_float(img)` before processing; convert back with `img_as_uint(img)` for saving.

## Common Workflows

### Workflow 1: Fluorescence Cell Segmentation and Measurement

**Goal**: Segment DAPI-stained nuclei and measure GFP fluorescence per nucleus.

```python
from skimage import io, filters, morphology, measure, img_as_float
from skimage.segmentation import watershed
from skimage.feature import peak_local_max
from scipy import ndimage as ndi
import pandas as pd
import numpy as np
import tifffile

# Load 2-channel image (DAPI=ch0, GFP=ch1)
img = tifffile.imread("cells.tif")
dapi = img_as_float(img[0])
gfp = img_as_float(img[1])

# Segment nuclei from DAPI channel
dapi_smooth = filters.gaussian(dapi, sigma=2)
threshold = filters.threshold_otsu(dapi_smooth)
binary = dapi_smooth > threshold
binary = morphology.remove_small_objects(binary, min_size=200)
binary = morphology.remove_small_holes(binary, area_threshold=500)

# Watershed to separate touching nuclei
distance = ndi.distance_transform_edt(binary)
coords = peak_local_max(distance, min_distance=30, labels=binary)
mask = np.zeros_like(distance, dtype=bool)
mask[tuple(coords.T)] = True
markers = ndi.label(mask)[0]
labels = watershed(-distance, markers, mask=binary)

# Measure GFP per nucleus
props = measure.regionprops(labels, intensity_image=gfp)
df = pd.DataFrame([{
    "nucleus_id": p.label,
    "area_px2": p.area,
    "gfp_mean": p.mean_intensity,
    "gfp_max": p.max_intensity,
} for p in props])

df.to_csv("nucleus_measurements.csv", index=False)
print(f"Nuclei: {len(df)}, mean GFP: {df['gfp_mean'].mean():.3f}")
```

### Workflow 2: Batch Image Processing

**Goal**: Apply the same preprocessing and measurement pipeline to a folder of images.

```python
from pathlib import Path
from skimage import io, filters, measure, img_as_float, morphology
import pandas as pd

results = []
for img_path in sorted(Path("data/").glob("*.tif")):
    img = img_as_float(io.imread(img_path))
    if img.ndim == 3:
        img = img.mean(axis=-1)  # convert RGB to grayscale

    # Preprocess
    smooth = filters.gaussian(img, sigma=1.5)
    thresh = filters.threshold_otsu(smooth)
    binary = morphology.remove_small_objects(smooth > thresh, min_size=50)

    # Measure
    labeled = measure.label(binary)
    props = measure.regionprops(labeled, intensity_image=img)
    for p in props:
        results.append({
            "image": img_path.stem,
            "object_id": p.label,
            "area": p.area,
            "mean_intensity": p.mean_intensity,
        })

df = pd.DataFrame(results)
df.to_csv("batch_results.csv", index=False)
print(f"Processed {df['image'].nunique()} images, {len(df)} objects total")
```

## Key Parameters

| Function | Parameter | Default | Range/Options | Effect |
|----------|-----------|---------|---------------|--------|
| `gaussian` | `sigma` | 1.0 | 0.5–10+ | Smoothing kernel size; larger = more blur |
| `median` | `footprint` | `disk(1)` | `disk(1–10)` | Median filter neighborhood |
| `threshold_otsu` | — | — | — | Returns automatic threshold (no tuning) |
| `remove_small_objects` | `min_size` | 64 | any integer | Remove objects smaller than N pixels |
| `watershed` | — | — | — | Uses marker positions from `peak_local_max` |
| `peak_local_max` | `min_distance` | 1 | 5–50 | Min separation between detected peaks (px) |
| `blob_log` | `min_sigma` / `max_sigma` | 1/50 | dependent | Expected blob radius range |
| `regionprops` | `intensity_image` | None | array | Image for intensity measurements |

## Best Practices

1. **Always check dtype before processing**: Operations like subtraction on `uint8` silently clip to 0. Convert to float: `img = img_as_float(img)` as the first step.

2. **Visualize intermediate results**: For every segmentation pipeline, plot the binary mask overlaid on the original before measuring. Silent segmentation errors are the most common failure mode.

3. **Tune thresholds on representative samples**: Otsu works well for bimodal histograms. For difficult images, compare Otsu/Li/Triangle with `try_all_threshold(img)` from skimage.

4. **Use watershed for touching objects**: Simple thresholding cannot separate touching nuclei. Always apply watershed with distance transform markers for densely packed cells.

5. **Measure in physical units**: Convert pixel measurements to microns using the pixel size from microscope metadata: `area_um2 = area_px * pixel_size_um**2`.

6. **Validate with known samples**: Before batch processing, verify the pipeline on 3–5 images with manually counted objects. Spot-check object counts against expectations.

## Common Recipes

### Recipe: Measure Spot Intensity in Fluorescence Images

```python
from skimage import io, filters, measure, img_as_float
from skimage.feature import blob_log
import numpy as np

img = img_as_float(io.imread("spots.tif"))
blobs = blob_log(img, min_sigma=2, max_sigma=8, num_sigma=5, threshold=0.05)

intensities = []
for y, x, sigma in blobs:
    r = int(np.ceil(np.sqrt(2) * sigma))
    region = img[max(0,int(y-r)):int(y+r), max(0,int(x-r)):int(x+r)]
    intensities.append({"y": y, "x": x, "radius": r, "mean_intensity": region.mean()})

import pandas as pd
df = pd.DataFrame(intensities)
print(f"Spots: {len(df)}, mean intensity: {df['mean_intensity'].mean():.4f}")
```

### Recipe: Binary Mask from Multiple Channels

```python
from skimage import filters, morphology, img_as_float
import numpy as np

# Segment objects positive in BOTH channels
ch1 = img_as_float(dapi)
ch2 = img_as_float(gfp)

mask1 = ch1 > filters.threshold_otsu(ch1)
mask2 = ch2 > filters.threshold_otsu(ch2)
combined_mask = mask1 & mask2  # objects in both channels

combined_mask = morphology.binary_closing(combined_mask)
print(f"Co-positive pixels: {combined_mask.sum()}")
```

### Recipe: Save Labeled Overlay as Publication Figure

```python
from skimage.color import label2rgb
from skimage import io, img_as_ubyte
import matplotlib.pyplot as plt

overlay = label2rgb(labels, image=img_as_float(dapi), bg_label=0, alpha=0.5)

fig, axes = plt.subplots(1, 2, figsize=(12, 6))
axes[0].imshow(dapi, cmap="gray")
axes[0].set_title(f"DAPI (raw)")
axes[1].imshow(overlay)
axes[1].set_title(f"Segmented ({labels.max()} nuclei)")
for ax in axes:
    ax.axis("off")
plt.tight_layout()
plt.savefig("segmentation_overlay.png", dpi=300, bbox_inches="tight")
print("Saved segmentation_overlay.png")
```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `OverflowError` in arithmetic | Integer overflow from uint8/uint16 ops | Convert to float first: `img = img_as_float(img)` |
| Otsu threshold finds one class | Bimodal distribution absent | Try `threshold_li()` or `try_all_threshold(img)` for comparison |
| Watershed over-segments | Markers too close together | Increase `min_distance` in `peak_local_max`; smooth distance map |
| All objects merged in binary | Threshold too low | Check `plt.hist(img.ravel())` for histogram; manually adjust |
| `regionprops` missing intensity stats | `intensity_image` not provided | Pass: `regionprops(labels, intensity_image=img)` |
| 3D images processed as 2D | Z-stack not detected | Check shape: `img.shape`; process per slice or use 3D functions |
| Tiny noise objects in binary | Threshold too aggressive | Apply `morphology.remove_small_objects(binary, min_size=50)` |

## Related Skills

- **pathml** — whole-slide image processing using scikit-image under the hood
- **matplotlib-scientific-plotting** — visualizing segmentation results and measurement distributions
- **histolab-wsi-processing** — scikit-image-compatible preprocessing for H&E WSI tiles

## References

- [scikit-image documentation](https://scikit-image.org/docs/stable/) — API reference and tutorials
- [GitHub: scikit-image/scikit-image](https://github.com/scikit-image/scikit-image) — source code and examples
- van der Walt et al. (2014) "scikit-image: image processing in Python" — [PeerJ 2:e453](https://doi.org/10.7717/peerj.453)
- [scikit-image examples gallery](https://scikit-image.org/docs/stable/auto_examples/) — annotated code examples by category
