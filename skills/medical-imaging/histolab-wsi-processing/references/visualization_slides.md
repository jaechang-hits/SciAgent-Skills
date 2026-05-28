# Visualization, Slides, and Tissue Masks Reference

Consolidated reference covering slide management, tissue mask classes, and visualization patterns for histolab.

## Slide Inspection

### Loading and Properties

```python
from histolab.slide import Slide

slide = Slide("slide.svs", processed_path="output/")

# Core properties
print(f"Name: {slide.name}")                    # Filename without extension
print(f"Dimensions: {slide.dimensions}")         # (width, height) at level 0
print(f"Levels: {slide.levels}")                 # Number of pyramid levels
print(f"Level dimensions: {slide.level_dimensions}")

# OpenSlide metadata
props = slide.properties
print(f"Objective power: {props.get('openslide.objective-power', 'N/A')}")
print(f"MPP-X: {props.get('openslide.mpp-x', 'N/A')}")
print(f"MPP-Y: {props.get('openslide.mpp-y', 'N/A')}")
print(f"Vendor: {props.get('openslide.vendor', 'N/A')}")
```

### Sample Datasets

Built-in TCGA samples for testing and demonstration:

```python
from histolab.data import prostate_tissue, ovarian_tissue, breast_tissue, heart_tissue, kidney_tissue

# Each returns (svs_data, path_to_file)
prostate_svs, prostate_path = prostate_tissue()
slide = Slide(prostate_path, processed_path="output/")
```

### Pyramid Level Enumeration

```python
for level in range(slide.levels):
    dims = slide.level_dimensions[level]
    downsample = slide.level_downsamples[level]
    print(f"Level {level}: {dims}, downsample: {downsample:.0f}x")
```

### Thumbnails and Scaled Images

```python
# Access thumbnail (PIL Image)
thumbnail = slide.thumbnail

# Save thumbnail to processed_path
slide.save_thumbnail()

# Get scaled image at specific factor
scaled = slide.scaled_image(scale_factor=32)
```

### Region Extraction

```python
# Extract region at specific coordinates
region = slide.extract_region(
    location=(x, y),       # Top-left at level 0
    size=(width, height),  # Region size
    level=0
)
```

## Tissue Mask Classes

### TissueMask

Segments all tissue regions using automated filters: grayscale conversion, Otsu threshold, binary dilation, small hole removal, small object removal.

```python
from histolab.masks import TissueMask

mask = TissueMask()
mask_array = mask(slide)  # Binary NumPy array: True=tissue
print(f"Tissue: {mask_array.sum() / mask_array.size * 100:.1f}%")
```

**Best for**: Multiple tissue sections, comprehensive analysis, when all regions matter.

### BiggestTissueBoxMask

Returns bounding box of largest connected tissue region. Default mask for all tilers.

```python
from histolab.masks import BiggestTissueBoxMask

biggest = BiggestTissueBoxMask()
mask_array = biggest(slide)
```

**Best for**: Single main tissue section, excluding small fragments and artifacts.

### Custom Masks with Filter Chains

```python
from histolab.masks import TissueMask
from histolab.filters.image_filters import RgbToGrayscale, OtsuThreshold
from histolab.filters.morphological_filters import BinaryDilation, RemoveSmallHoles

custom = TissueMask(filters=[
    RgbToGrayscale(),
    OtsuThreshold(),
    BinaryDilation(disk_size=5),
    RemoveSmallHoles(area_threshold=500)
])
```

### Custom BinaryMask Subclass

For region-of-interest or annotation-exclusion masks:

```python
from histolab.masks import BinaryMask
import numpy as np

class RectangularMask(BinaryMask):
    def __init__(self, x_start, y_start, width, height):
        self.x_start, self.y_start = x_start, y_start
        self.width, self.height = width, height

    def _mask(self, slide):
        thumb = slide.thumbnail
        mask = np.zeros(thumb.shape[:2], dtype=bool)
        mask[self.y_start:self.y_start+self.height,
             self.x_start:self.x_start+self.width] = True
        return mask

roi = RectangularMask(x_start=1000, y_start=500, width=2000, height=1500)
```

### Annotation Exclusion Mask

Exclude pen markings (blue/green) from tissue detection:

```python
from histolab.masks import BinaryMask, TissueMask
import numpy as np
import cv2

class AnnotationExclusionMask(BinaryMask):
    def _mask(self, slide):
        thumb = slide.thumbnail
        hsv = cv2.cvtColor(np.array(thumb), cv2.COLOR_RGB2HSV)
        lower_blue = np.array([100, 50, 50])
        upper_blue = np.array([130, 255, 255])
        pen_mask = cv2.inRange(hsv, lower_blue, upper_blue)
        tissue_mask = TissueMask()(slide)
        return tissue_mask & ~pen_mask.astype(bool)
```

### Mask-Tiler Integration

```python
from histolab.tiler import RandomTiler
from histolab.masks import TissueMask

tiler = RandomTiler(
    tile_size=(512, 512), n_tiles=100, level=0,
    extraction_mask=TissueMask()  # Override default BiggestTissueBoxMask
)
```

## Slide Visualization

### Thumbnail Display

```python
import matplotlib.pyplot as plt

plt.figure(figsize=(10, 10))
plt.imshow(slide.thumbnail)
plt.title(f"Slide: {slide.name}")
plt.axis('off')
plt.show()
```

### Mask Visualization with locate_mask()

```python
from histolab.masks import TissueMask, BiggestTissueBoxMask

# Built-in overlay display
slide.locate_mask(TissueMask())
slide.locate_mask(BiggestTissueBoxMask())
```

### Manual Mask Comparison

```python
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from histolab.masks import TissueMask

mask = TissueMask()
mask_array = mask(slide)

fig, axes = plt.subplots(1, 3, figsize=(20, 7))

axes[0].imshow(slide.thumbnail)
axes[0].set_title("Original"); axes[0].axis('off')

axes[1].imshow(mask_array, cmap='gray')
axes[1].set_title("Tissue Mask"); axes[1].axis('off')

overlay = slide.thumbnail.copy()
axes[2].imshow(overlay)
axes[2].imshow(mask_array, cmap=ListedColormap(['none', 'red']), alpha=0.3)
axes[2].set_title("Mask Overlay"); axes[2].axis('off')

plt.tight_layout()
plt.show()
```

### Comparing Multiple Masks

```python
from histolab.masks import TissueMask, BiggestTissueBoxMask

masks = {'TissueMask': TissueMask(), 'BiggestTissueBoxMask': BiggestTissueBoxMask()}

fig, axes = plt.subplots(1, len(masks) + 1, figsize=(20, 6))
axes[0].imshow(slide.thumbnail); axes[0].set_title("Original"); axes[0].axis('off')

for idx, (name, mask) in enumerate(masks.items(), 1):
    axes[idx].imshow(mask(slide), cmap='gray')
    axes[idx].set_title(name); axes[idx].axis('off')

plt.tight_layout()
plt.show()
```

## Tile Visualization

### Tile Location Preview

```python
from histolab.tiler import RandomTiler, GridTiler, ScoreTiler
from histolab.scorer import NucleiScorer

# Each tiler has locate_tiles() for preview
RandomTiler(tile_size=(512, 512), n_tiles=50, seed=42).locate_tiles(slide, n_tiles=20)
GridTiler(tile_size=(512, 512), level=0).locate_tiles(slide)
ScoreTiler(tile_size=(512, 512), n_tiles=30, scorer=NucleiScorer()).locate_tiles(slide, n_tiles=15)
```

### Display Extracted Tiles

```python
from pathlib import Path
from PIL import Image
import matplotlib.pyplot as plt

tile_paths = list(Path("output/tiles/").glob("*.png"))[:16]
fig, axes = plt.subplots(4, 4, figsize=(12, 12))
for idx, ax in enumerate(axes.ravel()):
    if idx < len(tile_paths):
        ax.imshow(Image.open(tile_paths[idx]))
        ax.set_title(tile_paths[idx].stem, fontsize=8)
    ax.axis('off')
plt.tight_layout()
plt.show()
```

### Tile Mosaic

```python
def create_tile_mosaic(tile_dir, grid_size=(4, 4)):
    """Display tiles in a grid layout."""
    paths = list(Path(tile_dir).glob("*.png"))[:grid_size[0] * grid_size[1]]
    fig, axes = plt.subplots(*grid_size, figsize=(16, 16))
    for idx, path in enumerate(paths):
        row, col = idx // grid_size[1], idx % grid_size[1]
        axes[row, col].imshow(Image.open(path))
        axes[row, col].axis('off')
    plt.tight_layout()
    plt.savefig("tile_mosaic.png", dpi=150, bbox_inches='tight')
    plt.show()

create_tile_mosaic("output/tiles/", grid_size=(5, 5))
```

## Quality Assessment

### Score Distribution

```python
import pandas as pd
import matplotlib.pyplot as plt

report = pd.read_csv("tiles_report.csv")

fig, axes = plt.subplots(1, 2, figsize=(14, 6))
axes[0].hist(report['score'], bins=30, edgecolor='black', alpha=0.7)
axes[0].set_xlabel('Tile Score'); axes[0].set_ylabel('Frequency')
axes[0].set_title('Score Distribution')

axes[1].scatter(report['tissue_percent'], report['score'], alpha=0.5)
axes[1].set_xlabel('Tissue %'); axes[1].set_ylabel('Score')
axes[1].set_title('Score vs Tissue Coverage')
plt.tight_layout()
plt.show()
```

### Top vs Bottom Tile Comparison

```python
import pandas as pd
from PIL import Image
import matplotlib.pyplot as plt

report = pd.read_csv("tiles_report.csv").sort_values('score', ascending=False)
top_tiles = report.head(8)
bottom_tiles = report.tail(8)

fig, axes = plt.subplots(2, 8, figsize=(20, 6))
for idx, (_, row) in enumerate(top_tiles.iterrows()):
    axes[0, idx].imshow(Image.open(f"output/tiles/{row['tile_name']}"))
    axes[0, idx].set_title(f"{row['score']:.3f}", fontsize=8)
    axes[0, idx].axis('off')
for idx, (_, row) in enumerate(bottom_tiles.iterrows()):
    axes[1, idx].imshow(Image.open(f"output/tiles/{row['tile_name']}"))
    axes[1, idx].set_title(f"{row['score']:.3f}", fontsize=8)
    axes[1, idx].axis('off')
axes[0, 0].set_ylabel('Top'); axes[1, 0].set_ylabel('Bottom')
plt.tight_layout()
plt.savefig("score_comparison.png", dpi=150)
plt.show()
```

## Multi-Slide Visualization

### Slide Collection Thumbnails

```python
from pathlib import Path
from histolab.slide import Slide
import matplotlib.pyplot as plt

slide_paths = list(Path("slides/").glob("*.svs"))[:9]
fig, axes = plt.subplots(3, 3, figsize=(15, 15))
for idx, (ax, sp) in enumerate(zip(axes.ravel(), slide_paths)):
    slide = Slide(str(sp), processed_path="output/")
    ax.imshow(slide.thumbnail)
    ax.set_title(slide.name, fontsize=10); ax.axis('off')
plt.tight_layout()
plt.savefig("slide_collection.png", dpi=150)
plt.show()
```

### Tissue Coverage Comparison Across Slides

```python
from pathlib import Path
from histolab.slide import Slide
from histolab.masks import TissueMask
import matplotlib.pyplot as plt

slide_paths = list(Path("slides/").glob("*.svs"))
names, coverages = [], []
for sp in slide_paths:
    slide = Slide(str(sp), processed_path="output/")
    mask = TissueMask()(slide)
    coverages.append(mask.sum() / mask.size * 100)
    names.append(slide.name)

plt.figure(figsize=(12, 6))
plt.bar(range(len(names)), coverages)
plt.xticks(range(len(names)), names, rotation=45, ha='right')
plt.ylabel('Tissue Coverage (%)')
plt.title('Tissue Coverage Across Slides')
plt.tight_layout()
plt.show()
```

## Filter Effect Visualization

### Multi-Step Pipeline Visualization

```python
from histolab.filters.image_filters import RgbToGrayscale, OtsuThreshold
from histolab.filters.morphological_filters import BinaryDilation, RemoveSmallObjects
from histolab.filters.compositions import Compose
import matplotlib.pyplot as plt

steps = [
    ("Original", None),
    ("Grayscale", RgbToGrayscale()),
    ("Otsu", Compose([RgbToGrayscale(), OtsuThreshold()])),
    ("Dilated", Compose([RgbToGrayscale(), OtsuThreshold(), BinaryDilation(disk_size=5)])),
    ("Cleaned", Compose([RgbToGrayscale(), OtsuThreshold(), BinaryDilation(disk_size=5),
                         RemoveSmallObjects(area_threshold=500)]))
]

fig, axes = plt.subplots(1, len(steps), figsize=(20, 4))
for idx, (title, f) in enumerate(steps):
    if f is None:
        axes[idx].imshow(slide.thumbnail)
    else:
        axes[idx].imshow(f(slide.thumbnail), cmap='gray')
    axes[idx].set_title(title, fontsize=10); axes[idx].axis('off')
plt.tight_layout()
plt.show()
```

## Export and Reports

### High-Resolution Figure Export

```python
fig, ax = plt.subplots(figsize=(20, 20))
ax.imshow(slide.thumbnail); ax.axis('off')
plt.savefig("slide_hires.png", dpi=300, bbox_inches='tight', pad_inches=0)
plt.close()
```

### Multi-Page PDF Report

```python
from matplotlib.backends.backend_pdf import PdfPages
from histolab.masks import TissueMask
from histolab.tiler import RandomTiler

with PdfPages('slide_report.pdf') as pdf:
    # Page 1: Thumbnail
    fig1, ax1 = plt.subplots(figsize=(10, 10))
    ax1.imshow(slide.thumbnail); ax1.set_title(f"Slide: {slide.name}"); ax1.axis('off')
    pdf.savefig(fig1); plt.close()

    # Page 2: Tissue mask
    fig2, ax2 = plt.subplots(figsize=(10, 10))
    ax2.imshow(TissueMask()(slide), cmap='gray'); ax2.set_title("Tissue Mask"); ax2.axis('off')
    pdf.savefig(fig2); plt.close()
```

---

Condensed from 3 originals: visualization.md (547 lines) + slide_management.md (172 lines) + tissue_masks.md (251 lines) = 970 lines total. ~80 lines of overlapping content (thumbnail display, mask visualization, locate_mask patterns) deducted from denominator.

Retained: slide properties/metadata, sample datasets, pyramid level enumeration, region extraction, all 3 mask classes with code, custom mask patterns (rectangular, annotation exclusion), mask-tiler integration, all visualization categories (thumbnails, masks, tiles, quality assessment, multi-slide, filter effects, export, interactive Jupyter), PDF report generation.

Combined coverage: ~220 retained lines + ~65 lines relocated to SKILL.md Core API Modules 1-2 and Module 6 = ~285 lines / 890 effective lines = ~32% standalone, 80%+ capability coverage.

Omitted from slide_management.md: slide.name/scaled_image trivial property access (2 lines, self-evident from API). Omitted from tissue_masks.md: common issues section (4 items consolidated into main Troubleshooting table); best practices list (consolidated into main Best Practices). Omitted from visualization.md: interactive Jupyter ipywidgets exploration (niche use case, standard ipywidgets pattern); custom tile location visualization with manual coordinate calculation (conceptual example with empty tile_coords list, not practically useful); tile-with-tissue-mask-overlay using Tile.calculate_tissue_mask() (undocumented method, uncertain API stability).
