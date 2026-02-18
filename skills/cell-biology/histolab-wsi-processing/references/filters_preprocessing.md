# Filters and Preprocessing Reference

Comprehensive reference for histolab's filter system. Filters are composable building blocks for tissue detection, quality control, artifact removal, and image preprocessing.

## Image Filters

### RgbToGrayscale

Convert RGB images to single-channel grayscale. Required before thresholding operations.

```python
from histolab.filters.image_filters import RgbToGrayscale

gray_filter = RgbToGrayscale()
gray_image = gray_filter(rgb_image)
```

### RgbToHsv

Convert RGB to Hue-Saturation-Value color space. Useful for color-based segmentation (e.g., detecting pen marks by hue range).

```python
from histolab.filters.image_filters import RgbToHsv

hsv_filter = RgbToHsv()
hsv_image = hsv_filter(rgb_image)
# Channel 0: Hue (0-1), Channel 1: Saturation, Channel 2: Value
```

### RgbToHed

Convert RGB to Hematoxylin-Eosin-DAB color space for stain deconvolution. Separates H&E stain components for quantitative analysis.

```python
from histolab.filters.image_filters import RgbToHed

hed_filter = RgbToHed()
hed_image = hed_filter(rgb_image)
# Channel 0: Hematoxylin (nuclei), Channel 1: Eosin (cytoplasm), Channel 2: DAB
```

**Use cases**: Separating nuclear (hematoxylin) vs cytoplasmic (eosin) staining, quantifying stain intensity, nuclei enhancement pipelines.

### OtsuThreshold

Automatic thresholding using Otsu's method. Determines optimal threshold to separate foreground from background by minimizing intra-class variance.

```python
from histolab.filters.image_filters import OtsuThreshold

otsu_filter = OtsuThreshold()
binary_image = otsu_filter(grayscale_image)
```

**Use cases**: Tissue detection, nuclei segmentation, binary mask creation.

### AdaptiveThreshold

Local thresholding for images with non-uniform illumination or variable staining intensity.

```python
from histolab.filters.image_filters import AdaptiveThreshold

adaptive_filter = AdaptiveThreshold(
    block_size=11,  # Size of local neighborhood (must be odd)
    offset=2        # Constant subtracted from mean
)
binary_image = adaptive_filter(grayscale_image)
```

### Invert, StretchContrast, HistogramEqualization

Intensity manipulation filters for preprocessing and normalization.

```python
from histolab.filters.image_filters import Invert, StretchContrast, HistogramEqualization

Invert()(image)                      # Invert intensity values
StretchContrast()(image)             # Stretch intensity range for low-contrast features
HistogramEqualization()(grayscale)   # Equalize histogram to standardize contrast
```

### Lambda

Create custom inline filters without subclassing.

```python
from histolab.filters.image_filters import Lambda
import numpy as np

brightness = Lambda(lambda img: np.clip(img * 1.2, 0, 255).astype(np.uint8))
red_channel = Lambda(lambda img: img[:, :, 0])
```

## Morphological Filters

All morphological filters operate on binary images. Apply after thresholding.

### BinaryDilation

Expand white (True) regions. Connects nearby tissue fragments and fills small gaps.

```python
from histolab.filters.morphological_filters import BinaryDilation

dilation = BinaryDilation(disk_size=5)  # Structuring element size (default: 5)
dilated = dilation(binary_image)
```

### BinaryErosion

Shrink white regions. Removes small protrusions and separates connected objects.

```python
from histolab.filters.morphological_filters import BinaryErosion

erosion = BinaryErosion(disk_size=5)
eroded = erosion(binary_image)
```

### BinaryOpening

Erosion followed by dilation. Removes small objects while preserving larger shapes.

```python
from histolab.filters.morphological_filters import BinaryOpening

opening = BinaryOpening(disk_size=3)
opened = opening(binary_image)
```

### BinaryClosing

Dilation followed by erosion. Fills small holes while preserving overall shape.

```python
from histolab.filters.morphological_filters import BinaryClosing

closing = BinaryClosing(disk_size=5)
closed = closing(binary_image)
```

### RemoveSmallObjects

Remove connected components smaller than a pixel area threshold.

```python
from histolab.filters.morphological_filters import RemoveSmallObjects

remove_small = RemoveSmallObjects(area_threshold=500)  # Minimum area in pixels
cleaned = remove_small(binary_image)
```

### RemoveSmallHoles

Fill holes in tissue regions smaller than a threshold area.

```python
from histolab.filters.morphological_filters import RemoveSmallHoles

fill_holes = RemoveSmallHoles(area_threshold=1000)  # Maximum hole size to fill
filled = fill_holes(binary_image)
```

## Filter Composition

### Compose

Chain multiple filters into a reusable pipeline. Output of each filter feeds into the next.

```python
from histolab.filters.compositions import Compose
from histolab.filters.image_filters import RgbToGrayscale, OtsuThreshold
from histolab.filters.morphological_filters import (
    BinaryDilation, RemoveSmallHoles, RemoveSmallObjects
)

# Standard tissue detection pipeline
tissue_detection = Compose([
    RgbToGrayscale(),
    OtsuThreshold(),
    BinaryDilation(disk_size=5),
    RemoveSmallHoles(area_threshold=1000),
    RemoveSmallObjects(area_threshold=500)
])

result = tissue_detection(rgb_image)
```

## Common Preprocessing Pipelines

### Pen Mark Removal

Remove blue/green pen markings common on pathology slides.

```python
from histolab.filters.image_filters import RgbToHsv, Lambda
from histolab.filters.compositions import Compose
import numpy as np

def remove_pen_marks(hsv_image):
    """Remove blue/green pen markings from slide."""
    h, s, v = hsv_image[:, :, 0], hsv_image[:, :, 1], hsv_image[:, :, 2]
    pen_mask = ((h > 0.45) & (h < 0.7) & (s > 0.3))
    hsv_image[pen_mask] = [0, 0, 1]  # Set pen regions to white
    return hsv_image

pen_removal = Compose([RgbToHsv(), Lambda(remove_pen_marks)])
```

### Nuclei Enhancement

Isolate and enhance nuclear staining from H&E images.

```python
from histolab.filters.image_filters import RgbToHed, HistogramEqualization, Lambda
from histolab.filters.compositions import Compose

nuclei_enhancement = Compose([
    RgbToHed(),
    Lambda(lambda hed: hed[:, :, 0]),  # Extract hematoxylin channel
    HistogramEqualization()
])
```

### Contrast Normalization

Normalize contrast across slides with variable staining quality.

```python
from histolab.filters.image_filters import RgbToGrayscale, StretchContrast, HistogramEqualization
from histolab.filters.compositions import Compose

contrast_norm = Compose([
    RgbToGrayscale(),
    StretchContrast(),
    HistogramEqualization()
])
```

### Basic Stain Normalization

Simple H&E stain normalization using channel-wise z-score standardization.

```python
from histolab.filters.image_filters import RgbToHed, Lambda
from histolab.filters.compositions import Compose
import numpy as np

def normalize_hed(hed_image, target_means=[0.65, 0.70], target_stds=[0.15, 0.13]):
    """Z-score normalize H&E channels to target distribution."""
    h = hed_image[:, :, 0]
    e = hed_image[:, :, 1]
    hed_image[:, :, 0] = (h - h.mean()) / (h.std() + 1e-8) * target_stds[0] + target_means[0]
    hed_image[:, :, 1] = (e - e.mean()) / (e.std() + 1e-8) * target_stds[1] + target_means[1]
    return hed_image

stain_norm = Compose([RgbToHed(), Lambda(normalize_hed)])
```

## Applying Filters to Tiles

Filters can be applied to individual `Tile` objects for post-extraction preprocessing.

```python
from histolab.tile import Tile
from histolab.filters.compositions import Compose
from histolab.filters.image_filters import RgbToGrayscale, StretchContrast

filter_chain = Compose([RgbToGrayscale(), StretchContrast()])
processed_tile = tile.apply_filters(filter_chain)
```

## Custom Mask Integration

Use custom filter pipelines with `TissueMask` for specialized tissue detection.

```python
from histolab.masks import TissueMask
from histolab.filters.compositions import Compose
from histolab.filters.image_filters import RgbToGrayscale, OtsuThreshold
from histolab.filters.morphological_filters import BinaryDilation, RemoveSmallObjects

aggressive_filters = Compose([
    RgbToGrayscale(),
    OtsuThreshold(),
    BinaryDilation(disk_size=10),
    RemoveSmallObjects(area_threshold=5000)
])

custom_mask = TissueMask(filters=aggressive_filters)
```

## Quality Control Filters

### Blur Detection

Score tile sharpness using Laplacian variance. Low values indicate blurry tiles.

```python
from histolab.filters.image_filters import RgbToGrayscale, Lambda
import cv2
import numpy as np

def laplacian_blur_score(gray_image):
    """Laplacian variance blur metric. Higher = sharper."""
    return cv2.Laplacian(np.array(gray_image), cv2.CV_64F).var()

blur_detector = Lambda(
    lambda img: laplacian_blur_score(RgbToGrayscale()(img))
)
```

### Tissue Coverage Calculation

Calculate percentage of tissue in an image region.

```python
from histolab.filters.image_filters import RgbToGrayscale, OtsuThreshold, Lambda
from histolab.filters.compositions import Compose

def tissue_coverage(image):
    """Return tissue percentage (0-100)."""
    mask = Compose([RgbToGrayscale(), OtsuThreshold()])(image)
    return mask.sum() / mask.size * 100

coverage = Lambda(tissue_coverage)
```

---

Condensed from original: 514 lines. Retained: all 10 image filter types, all 6 morphological filter types, Compose chaining, 4 preprocessing pipelines (tissue detection, pen removal, nuclei enhancement, stain normalization), tile filter application, custom mask integration, QC filters (blur detection, tissue coverage). Omitted: duplicate tissue detection pipeline (shown identically in main SKILL.md Core API Module 4); per-filter "Use cases" lists shortened to inline descriptions for filters with obvious purpose (Invert, StretchContrast, HistogramEqualization); troubleshooting section (4 items consolidated into main Troubleshooting table).
