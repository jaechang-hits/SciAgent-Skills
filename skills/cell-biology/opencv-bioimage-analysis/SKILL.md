---
name: "opencv-bioimage-analysis"
description: "Computer vision library for bio-image preprocessing, feature detection, and real-time microscopy analysis. Performs color space conversion, morphological operations, contour/blob detection, template matching, and optical flow on fluorescence and brightfield images. 10-100× faster than pure Python implementations using optimized C++ kernels. Use scikit-image for scientific morphometry and regionprops; use OpenCV for real-time processing, video, and classical feature extraction pipelines."
license: "Apache-2.0"
---

# OpenCV — Bio-image Computer Vision

## Overview

OpenCV (cv2) provides optimized C++-backed image processing routines for preprocessing, segmentation, feature extraction, and video analysis of biological images. In life sciences, OpenCV is used for fluorescence image enhancement (background subtraction, CLAHE), morphological segmentation (watershed, contour detection), brightfield cell detection, and real-time microscopy stream processing. Unlike scikit-image (which emphasizes scientific measurement), OpenCV prioritizes computational speed and video support — making it ideal for preprocessing pipelines and real-time imaging applications.

## When to Use

- Preprocessing fluorescence or brightfield images: background subtraction, CLAHE, Gaussian/median blur
- Detecting cell contours, blobs, or edges without deep learning (classical methods)
- Processing video streams from live-cell imaging microscopes in real-time
- Template matching for finding repeated structures (organelles, crystals, patterns)
- Applying morphological operations (erosion, dilation, opening, closing) for mask refinement
- Computing optical flow between video frames for cell tracking
- Use **scikit-image** instead for scientific morphometry, regionprops, and scientific image I/O (TIFF metadata)
- Use **Cellpose** or **StarDist** instead for deep-learning cell segmentation on fluorescence images

## Prerequisites

- **Python packages**: `opencv-python`, `numpy`, `matplotlib`
- **Optional**: `opencv-contrib-python` for extra modules (SIFT, SURF, optical flow)

```bash
# Install OpenCV
pip install opencv-python

# Install with extra contributed modules (SIFT, SURF, etc.)
pip install opencv-contrib-python

# Verify
python -c "import cv2; print(cv2.__version__)"
# 4.10.0
```

## Quick Start

```python
import cv2
import numpy as np

# Read and display image info
img = cv2.imread("cells.tif", cv2.IMREAD_GRAYSCALE)
print(f"Shape: {img.shape}, dtype: {img.dtype}")
print(f"Min: {img.min()}, Max: {img.max()}")

# Apply Gaussian blur and threshold
blurred = cv2.GaussianBlur(img, (5, 5), 0)
_, binary = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
print(f"Cells detected (rough): {np.sum(binary > 0)} foreground pixels")
```

## Core API

### Module 1: Image I/O and Color Space Conversion

Read, write, and convert images between color spaces.

```python
import cv2
import numpy as np

# Read image (GRAYSCALE, COLOR, or UNCHANGED for 16-bit)
img_gray  = cv2.imread("cells.tif", cv2.IMREAD_GRAYSCALE)   # uint8
img_color = cv2.imread("rgb.tif", cv2.IMREAD_COLOR)         # BGR order!
img_16bit = cv2.imread("16bit.tif", cv2.IMREAD_UNCHANGED)   # uint16

print(f"Grayscale shape: {img_gray.shape}, dtype: {img_gray.dtype}")
print(f"Color shape:     {img_color.shape}")

# Color space conversions
img_rgb  = cv2.cvtColor(img_color, cv2.COLOR_BGR2RGB)   # BGR → RGB
img_hsv  = cv2.cvtColor(img_color, cv2.COLOR_BGR2HSV)   # BGR → HSV
img_gray2 = cv2.cvtColor(img_color, cv2.COLOR_BGR2GRAY) # BGR → gray

# Write image
cv2.imwrite("output.png", img_gray)
cv2.imwrite("output_16bit.tif", img_16bit)
print("Images written.")
```

### Module 2: Filtering and Enhancement

Apply filters and contrast enhancement for image preprocessing.

```python
import cv2
import numpy as np

img = cv2.imread("cells.tif", cv2.IMREAD_GRAYSCALE)

# Gaussian blur (noise reduction)
blurred = cv2.GaussianBlur(img, (7, 7), sigmaX=1.5)

# Median blur (salt-and-pepper noise)
median = cv2.medianBlur(img, 5)

# CLAHE: Contrast Limited Adaptive Histogram Equalization (for microscopy)
clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
clahe_img = clahe.apply(img)

# Top-hat filter for bright spots on dark background
kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))
tophat = cv2.morphologyEx(img, cv2.MORPH_TOPHAT, kernel)

print(f"CLAHE range: [{clahe_img.min()}, {clahe_img.max()}]")
cv2.imwrite("clahe_enhanced.tif", clahe_img)
```

### Module 3: Thresholding and Binary Segmentation

Convert grayscale images to binary masks using various thresholding methods.

```python
import cv2
import numpy as np

img = cv2.imread("nuclei.tif", cv2.IMREAD_GRAYSCALE)

# Otsu's thresholding (automatic threshold selection)
thresh_val, otsu_mask = cv2.threshold(img, 0, 255,
                                      cv2.THRESH_BINARY + cv2.THRESH_OTSU)
print(f"Otsu threshold: {thresh_val:.0f}")

# Adaptive thresholding (handles uneven illumination)
adaptive = cv2.adaptiveThreshold(
    img, 255,
    cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
    cv2.THRESH_BINARY,
    blockSize=11,     # neighborhood size (odd)
    C=2,              # constant subtracted from mean
)

# For 16-bit images: normalize first
img_16 = cv2.imread("16bit_nuclei.tif", cv2.IMREAD_UNCHANGED)
img_8 = cv2.normalize(img_16, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)
_, mask_16 = cv2.threshold(img_8, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

print(f"Otsu mask foreground: {mask_16.sum() / 255} pixels")
```

### Module 4: Contour Detection and Measurement

Find and measure cell contours from binary masks.

```python
import cv2
import numpy as np
import pandas as pd

img = cv2.imread("cells.tif", cv2.IMREAD_GRAYSCALE)
blurred = cv2.GaussianBlur(img, (5, 5), 0)
_, binary = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

# Remove small objects with morphological opening
kernel = np.ones((3, 3), np.uint8)
cleaned = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel, iterations=2)

# Find contours
contours, hierarchy = cv2.findContours(cleaned, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
print(f"Objects detected: {len(contours)}")

# Measure each contour
records = []
for i, cnt in enumerate(contours):
    area = cv2.contourArea(cnt)
    if area < 50: continue  # skip tiny objects
    perimeter = cv2.arcLength(cnt, True)
    x, y, w, h = cv2.boundingRect(cnt)
    (cx, cy), radius = cv2.minEnclosingCircle(cnt)
    records.append({"cell_id": i, "area": area, "perimeter": perimeter,
                     "x": x, "y": y, "w": w, "h": h, "radius": radius})

df = pd.DataFrame(records)
print(f"Cells > 50 px²: {len(df)}")
print(df[["area", "perimeter", "radius"]].describe())
```

### Module 5: Morphological Operations for Mask Refinement

Refine segmentation masks with morphological operations.

```python
import cv2
import numpy as np

# Load binary mask (from thresholding or Cellpose)
mask = cv2.imread("rough_mask.png", cv2.IMREAD_GRAYSCALE)
_, mask = cv2.threshold(mask, 127, 255, cv2.THRESH_BINARY)

# Structural elements
ellipse = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
rect    = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))

# Opening: remove small bright noise
opened = cv2.morphologyEx(mask, cv2.MORPH_OPEN, ellipse, iterations=1)

# Closing: fill small holes inside cells
closed = cv2.morphologyEx(opened, cv2.MORPH_CLOSE, ellipse, iterations=2)

# Dilation: expand cell boundaries slightly
dilated = cv2.dilate(closed, ellipse, iterations=1)

# Distance transform for watershed seed generation
dist = cv2.distanceTransform(closed, cv2.DIST_L2, 5)
_, seeds = cv2.threshold(dist, 0.5 * dist.max(), 255, 0)
seeds = seeds.astype(np.uint8)
print(f"Potential cell centers: {cv2.connectedComponents(seeds)[0] - 1}")
```

### Module 6: Video Processing for Live-Cell Imaging

Process video streams from time-lapse microscopy.

```python
import cv2
import numpy as np

# Process a time-lapse video file
cap = cv2.VideoCapture("timelapse.avi")
fps = cap.get(cv2.CAP_PROP_FPS)
n_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
print(f"Video: {n_frames} frames at {fps} FPS")

# Background subtraction (remove static background)
bg_subtractor = cv2.createBackgroundSubtractorMOG2(
    history=50, varThreshold=25, detectShadows=False
)

frame_counts = []
frame_idx = 0
while cap.isOpened():
    ret, frame = cap.read()
    if not ret: break
    
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    fg_mask = bg_subtractor.apply(gray)
    
    # Count moving objects in this frame
    contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    moving = [c for c in contours if cv2.contourArea(c) > 100]
    frame_counts.append(len(moving))
    frame_idx += 1

cap.release()
print(f"Processed {frame_idx} frames. Mean moving objects: {np.mean(frame_counts):.1f}")
```

## Key Parameters

| Parameter | Module | Default | Effect |
|-----------|--------|---------|--------|
| `sigmaX` | `GaussianBlur` | auto from ksize | Gaussian standard deviation; larger = more smoothing |
| `clipLimit` | `createCLAHE` | `40.0` | Maximum contrast amplification; 2.0–4.0 for microscopy |
| `tileGridSize` | `createCLAHE` | `(8,8)` | Tile size for local histogram equalization |
| `blockSize` | `adaptiveThreshold` | required | Neighborhood size for adaptive threshold (must be odd, ≥ 3) |
| `C` | `adaptiveThreshold` | required | Constant subtracted from mean; positive to subtract |
| `iterations` | `morphologyEx` | `1` | Number of erosion/dilation cycles; higher = stronger effect |
| `history` | `BackgroundSubtractorMOG2` | `500` | Frames to model background; lower = faster adaptation |
| `varThreshold` | `BackgroundSubtractorMOG2` | `16` | Pixel variance threshold; higher = less sensitive |
| `minArea` | contour filter | — | Minimum `cv2.contourArea(cnt)` to keep; filter noise |
| `cv2.IMREAD_UNCHANGED` | `imread` | — | Preserve bit-depth (16-bit, 32-bit); required for scientific images |

## Common Workflows

### Workflow 1: Fluorescence Nucleus Detection Pipeline

```python
import cv2
import numpy as np
import pandas as pd

def detect_nuclei(image_path: str, min_area: int = 200) -> pd.DataFrame:
    """Detect DAPI-stained nuclei from a fluorescence image."""
    img = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
    
    # Normalize 16-bit to 8-bit
    if img.dtype == np.uint16:
        img = cv2.normalize(img, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)
    
    # Preprocess: CLAHE → Gaussian blur
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(img)
    blurred = cv2.GaussianBlur(enhanced, (5, 5), 1.5)
    
    # Segment: Otsu threshold → morphological opening
    _, binary = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    cleaned = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel, iterations=1)
    
    # Find and measure contours
    contours, _ = cv2.findContours(cleaned, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    records = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < min_area: continue
        M = cv2.moments(cnt)
        if M["m00"] == 0: continue
        cx = int(M["m10"] / M["m00"])
        cy = int(M["m01"] / M["m00"])
        records.append({"area": area, "cx": cx, "cy": cy,
                         "perimeter": cv2.arcLength(cnt, True)})
    
    return pd.DataFrame(records)

df = detect_nuclei("dapi.tif", min_area=300)
print(f"Nuclei detected: {len(df)}")
print(df.describe())
```

### Workflow 2: Batch Process Image Directory

```python
import cv2
import numpy as np
import pandas as pd
from pathlib import Path

def process_image(path: str) -> dict:
    img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        return {}
    blurred = cv2.GaussianBlur(img, (5, 5), 0)
    _, binary = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cells = [c for c in contours if cv2.contourArea(c) > 200]
    return {"file": Path(path).name, "cell_count": len(cells),
            "mean_area": np.mean([cv2.contourArea(c) for c in cells]) if cells else 0}

results = [process_image(str(p)) for p in sorted(Path("images").glob("*.tif"))]
df = pd.DataFrame([r for r in results if r])
print(df)
df.to_csv("batch_results.csv", index=False)
print("Saved: batch_results.csv")
```

## Common Recipes

### Recipe 1: Annotate Detected Cells on Image

```python
import cv2
import numpy as np

img = cv2.imread("cells.tif", cv2.IMREAD_GRAYSCALE)
img_color = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)

blurred = cv2.GaussianBlur(img, (5, 5), 0)
_, binary = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

for i, cnt in enumerate(contours):
    if cv2.contourArea(cnt) < 200: continue
    # Draw contour outline
    cv2.drawContours(img_color, [cnt], -1, (0, 255, 0), 2)
    # Label with cell number
    M = cv2.moments(cnt)
    if M["m00"] > 0:
        cx, cy = int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"])
        cv2.putText(img_color, str(i), (cx - 5, cy), cv2.FONT_HERSHEY_SIMPLEX,
                    0.4, (255, 255, 0), 1)

cv2.imwrite("annotated_cells.png", img_color)
print(f"Annotated {len(contours)} cells. Saved: annotated_cells.png")
```

### Recipe 2: Background Subtraction with Rolling Ball

```python
import cv2
import numpy as np

def rolling_ball_background(img: np.ndarray, radius: int = 50) -> np.ndarray:
    """Estimate and subtract background using a blur approximation."""
    kernel_size = 2 * radius + 1
    background = cv2.GaussianBlur(img, (kernel_size, kernel_size), radius / 3)
    corrected = cv2.subtract(img, background)
    return corrected

img = cv2.imread("uneven_fluorescence.tif", cv2.IMREAD_GRAYSCALE)
corrected = rolling_ball_background(img, radius=50)
cv2.imwrite("background_corrected.tif", corrected)
print(f"Background corrected. Range: [{corrected.min()}, {corrected.max()}]")
```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `imread` returns `None` | File not found or unsupported format | Use absolute path; verify with `Path(path).exists()`; for TIFF use `cv2.IMREAD_UNCHANGED` |
| 16-bit image shows as black | `IMREAD_GRAYSCALE` clips to uint8 | Use `cv2.IMREAD_UNCHANGED` and normalize: `cv2.normalize(img, None, 0, 255, cv2.NORM_MINMAX)` |
| BGR vs RGB color mismatch | OpenCV uses BGR, matplotlib uses RGB | Convert: `rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)` before `plt.imshow()` |
| Contours split one cell into many | Binary mask has holes or noise | Apply `cv2.MORPH_CLOSE` before contour detection; increase Gaussian blur sigma |
| `GaussianBlur` requires odd kernel | Even kernel size provided | Always use odd kernel sizes: 3, 5, 7, 9; `ksize=(5,5)` not `(4,4)` |
| CLAHE makes image worse | clipLimit too high | Reduce `clipLimit` to 1.5–2.0; increase `tileGridSize` to `(16,16)` |
| Background subtraction removes cells | History too short for MOG2 | Increase `history` parameter; use static frame subtraction for microscopy |
| Performance slow on large images | Python loop over pixels | Use vectorized NumPy operations or CUDA-accelerated `cv2.cuda` module |

## References

- [OpenCV Python documentation](https://docs.opencv.org/4.x/d6/d00/tutorial_py_root.html) — full Python API reference and tutorials
- [OpenCV GitHub: opencv/opencv](https://github.com/opencv/opencv) — source code and Python bindings
- Bradski G (2000) "The OpenCV Library" — *Dr. Dobb's Journal of Software Tools* 25(11):120-125
- [PyImageSearch tutorials](https://pyimagesearch.com/) — applied OpenCV for computer vision in biological imaging
