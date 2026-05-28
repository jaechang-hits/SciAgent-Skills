---
name: "histolab-wsi-processing"
description: "WSI processing for digital pathology. Tissue detection, tile extraction (random, grid, score-based), filter pipelines for H&E/IHC. For dataset prep, tile-based DL, slide QC. Use pathml for multiplexed imaging."
license: Apache-2.0
---

# Histolab WSI Processing

## Overview

Histolab is a Python library for processing whole slide images (WSI) in digital pathology. It automates tissue detection, extracts informative tiles from gigapixel images using multiple strategies, and provides composable filter pipelines for preprocessing. The library handles SVS, TIFF, NDPI, and other WSI formats via OpenSlide.

## When to Use

- Extracting tiles from whole slide images for deep learning model training
- Detecting tissue regions and filtering background/artifacts in histopathology slides
- Building preprocessing pipelines for H&E or IHC stained tissue sections
- Creating quality-driven tile datasets ranked by nuclei density or cellularity
- Performing batch tile extraction across slide collections with consistent parameters
- Assessing slide quality and tissue coverage before computational pathology workflows
- For raw slide access without tile extraction, use `openslide-python` directly
- For complex multiplexed imaging or spatial proteomics pipelines, use `pathml` instead

## Prerequisites

- **Python packages**: `histolab` (includes OpenSlide Python bindings)
- **System dependency**: OpenSlide C library must be installed separately
- **Supported formats**: SVS, TIFF, NDPI, VMS, SCN, MRXS (via OpenSlide)

```bash
# macOS
brew install openslide
pip install histolab

# Ubuntu/Debian
sudo apt-get install openslide-tools
pip install histolab
```

## Quick Start

```python
from histolab.slide import Slide
from histolab.tiler import RandomTiler

# Load slide
slide = Slide("slide.svs", processed_path="output/")
print(f"Dimensions: {slide.dimensions}, Levels: {slide.levels}")

# Configure tiler
tiler = RandomTiler(
    tile_size=(512, 512), n_tiles=100, level=0, seed=42,
    check_tissue=True, tissue_percent=80.0
)

# Preview and extract
tiler.locate_tiles(slide, n_tiles=20)
tiler.extract(slide)
```

## Core API

### Module 1: Slide Management

The `Slide` class is the primary interface for loading and inspecting WSI files.

```python
from histolab.slide import Slide
from histolab.data import prostate_tissue

# Load from built-in sample data (prostate, ovarian, breast, heart, kidney)
prostate_svs, prostate_path = prostate_tissue()
slide = Slide(prostate_path, processed_path="output/")

# Inspect properties
print(f"Dimensions: {slide.dimensions}")       # (width, height) at level 0
print(f"Levels: {slide.levels}")               # Number of pyramid levels
print(f"Level dims: {slide.level_dimensions}") # Dimensions per level
print(f"Magnification: {slide.properties.get('openslide.objective-power', 'N/A')}")
print(f"MPP-X: {slide.properties.get('openslide.mpp-x', 'N/A')}")

# Thumbnail and scaled image
slide.save_thumbnail()  # Saves to processed_path
scaled = slide.scaled_image(scale_factor=32)

# Extract region at specific coordinates
region = slide.extract_region(location=(1000, 2000), size=(512, 512), level=0)
```

### Module 2: Tissue Detection

Mask classes identify tissue regions and filter background for tile extraction.

```python
from histolab.masks import TissueMask, BiggestTissueBoxMask, BinaryMask
import numpy as np

# TissueMask: segments ALL tissue regions (multiple sections)
tissue_mask = TissueMask()
mask_array = tissue_mask(slide)  # Binary NumPy array: True=tissue, False=background
print(f"Tissue coverage: {mask_array.sum() / mask_array.size * 100:.1f}%")

# BiggestTissueBoxMask: bounding box of largest tissue region (default)
biggest_mask = BiggestTissueBoxMask()

# Visualize mask on slide thumbnail
slide.locate_mask(tissue_mask)

# Custom mask via BinaryMask subclass
class RectangularROI(BinaryMask):
    def __init__(self, x, y, w, h):
        self.x, self.y, self.w, self.h = x, y, w, h

    def _mask(self, slide):
        thumb = slide.thumbnail
        mask = np.zeros(thumb.shape[:2], dtype=bool)
        mask[self.y:self.y+self.h, self.x:self.x+self.w] = True
        return mask
```

### Module 3: Tile Extraction

Three strategies for extracting tiles: random sampling, grid coverage, and score-based selection.

```python
from histolab.tiler import RandomTiler, GridTiler, ScoreTiler
from histolab.scorer import NucleiScorer
from histolab.masks import TissueMask

# RandomTiler: fixed number of randomly positioned tiles
random_tiler = RandomTiler(
    tile_size=(512, 512), n_tiles=100, level=0,
    seed=42, check_tissue=True, tissue_percent=80.0
)
random_tiler.locate_tiles(slide, n_tiles=20)  # Preview first
random_tiler.extract(slide)

# GridTiler: systematic grid coverage
grid_tiler = GridTiler(
    tile_size=(512, 512), level=0,
    pixel_overlap=0, check_tissue=True, tissue_percent=70.0
)
grid_tiler.extract(slide, extraction_mask=TissueMask())

# ScoreTiler: top-ranked tiles by scoring function
score_tiler = ScoreTiler(
    tile_size=(512, 512), n_tiles=50, level=0,
    scorer=NucleiScorer(), check_tissue=True
)
score_tiler.extract(slide, report_path="tiles_report.csv")
# Report CSV: tile_name, x_coord, y_coord, level, score, tissue_percent
```

### Module 4: Filters and Preprocessing

Composable image and morphological filters for tissue detection and preprocessing.

```python
from histolab.filters.image_filters import (
    RgbToGrayscale, RgbToHsv, RgbToHed,
    OtsuThreshold, AdaptiveThreshold,
    StretchContrast, HistogramEqualization, Invert
)
from histolab.filters.morphological_filters import (
    BinaryDilation, BinaryErosion, BinaryOpening, BinaryClosing,
    RemoveSmallObjects, RemoveSmallHoles
)
from histolab.filters.compositions import Compose

# Standard tissue detection pipeline
tissue_pipeline = Compose([
    RgbToGrayscale(),
    OtsuThreshold(),
    BinaryDilation(disk_size=5),
    RemoveSmallHoles(area_threshold=1000),
    RemoveSmallObjects(area_threshold=500)
])

# Use custom pipeline with TissueMask
from histolab.masks import TissueMask
custom_mask = TissueMask(filters=tissue_pipeline)

# Stain deconvolution (H&E)
hed_filter = RgbToHed()  # Hematoxylin-Eosin-DAB separation
```

```python
# Apply filters to individual tiles
from histolab.tile import Tile

filter_chain = Compose([RgbToGrayscale(), StretchContrast()])
filtered_tile = tile.apply_filters(filter_chain)

# Lambda for custom inline filters
from histolab.filters.image_filters import Lambda
import numpy as np

brightness = Lambda(lambda img: np.clip(img * 1.2, 0, 255).astype(np.uint8))
red_channel = Lambda(lambda img: img[:, :, 0])
```

### Module 5: Scoring

Scorers rank tiles by tissue content quality for use with ScoreTiler.

```python
from histolab.scorer import NucleiScorer, CellularityScorer, Scorer
import numpy as np

# Built-in scorers
nuclei = NucleiScorer()       # Scores by nuclei density (grayscale threshold + count)
cellularity = CellularityScorer()  # Scores by overall cellular content

# Custom scorer
class ColorVarianceScorer(Scorer):
    def __call__(self, tile):
        """Score tiles by color variance (higher = more informative)."""
        tile_array = np.array(tile.image)
        return np.var(tile_array, axis=(0, 1)).sum()

score_tiler = ScoreTiler(
    tile_size=(512, 512), n_tiles=30,
    scorer=ColorVarianceScorer()
)
```

### Module 6: Visualization

Built-in methods and matplotlib patterns for inspecting slides, masks, and tiles.

```python
import matplotlib.pyplot as plt
from histolab.masks import TissueMask

# Built-in: mask overlay on slide thumbnail
slide.locate_mask(TissueMask())

# Built-in: tile location preview
tiler.locate_tiles(slide, n_tiles=20)

# Manual side-by-side: slide vs mask
mask = TissueMask()
mask_array = mask(slide)
fig, axes = plt.subplots(1, 2, figsize=(15, 7))
axes[0].imshow(slide.thumbnail); axes[0].set_title("Slide"); axes[0].axis('off')
axes[1].imshow(mask_array, cmap='gray'); axes[1].set_title("Mask"); axes[1].axis('off')
plt.tight_layout()
plt.show()

# Display extracted tiles in grid
from pathlib import Path
from PIL import Image
tile_paths = list(Path("output/tiles/").glob("*.png"))[:16]
fig, axes = plt.subplots(4, 4, figsize=(12, 12))
for idx, tp in enumerate(axes.ravel()):
    if idx < len(tile_paths):
        tp.imshow(Image.open(tile_paths[idx]))
        tp.set_title(tile_paths[idx].stem, fontsize=8)
    tp.axis('off')
plt.tight_layout()
plt.show()
```

## Key Concepts

### WSI Pyramid Levels

Whole slide images use a pyramidal structure with multiple resolution levels. Level 0 is the highest resolution (native scan). Higher levels provide progressively lower resolutions for faster access.

```python
for level in range(slide.levels):
    dims = slide.level_dimensions[level]
    downsample = slide.level_downsamples[level]
    print(f"Level {level}: {dims}, downsample: {downsample:.0f}x")
# Level 0: (98304, 221184), downsample: 1x
# Level 1: (24576, 55296), downsample: 4x
```

### Filter Composition Pattern

Filters are designed to be chained via `Compose`. The output of one filter becomes the input of the next. Image filters operate on RGB/grayscale arrays; morphological filters operate on binary arrays. Order matters: always convert to the expected input type before applying downstream filters.

### Mask-Tiler Integration

All tilers accept an `extraction_mask` parameter. The default is `BiggestTissueBoxMask()`. Override with `TissueMask()` for multi-section slides or a custom `BinaryMask` subclass for ROI-specific extraction.

## Common Workflows

### Workflow 1: Exploratory Slide Analysis

**Goal**: Quickly inspect a slide, detect tissue, and sample diverse regions for review.

```python
from histolab.slide import Slide
from histolab.tiler import RandomTiler
from histolab.masks import TissueMask
import matplotlib.pyplot as plt
import logging

logging.basicConfig(level=logging.INFO)

slide = Slide("slide.svs", processed_path="output/exploratory/")
print(f"Dimensions: {slide.dimensions}, Levels: {slide.levels}")
slide.save_thumbnail()

# Visualize tissue detection
tissue_mask = TissueMask()
slide.locate_mask(tissue_mask)
mask_arr = tissue_mask(slide)
print(f"Tissue coverage: {mask_arr.sum() / mask_arr.size * 100:.1f}%")

# Sample tiles
tiler = RandomTiler(
    tile_size=(512, 512), n_tiles=50, level=0,
    seed=42, check_tissue=True, tissue_percent=80.0
)
tiler.locate_tiles(slide, n_tiles=20)
tiler.extract(slide)
```

### Workflow 2: Deep Learning Dataset Preparation

**Goal**: Build a quality-controlled tile dataset from multiple slides for model training.

```python
from pathlib import Path
from histolab.slide import Slide
from histolab.tiler import ScoreTiler
from histolab.scorer import NucleiScorer
import pandas as pd
import logging

logging.basicConfig(level=logging.INFO)

slide_dir = Path("slides/")
output_base = Path("output/dataset/")
all_reports = []

tiler = ScoreTiler(
    tile_size=(512, 512), n_tiles=100, level=0,
    scorer=NucleiScorer(), check_tissue=True, tissue_percent=80.0
)

for slide_path in sorted(slide_dir.glob("*.svs")):
    out_dir = output_base / slide_path.stem
    out_dir.mkdir(parents=True, exist_ok=True)
    slide = Slide(str(slide_path), processed_path=str(out_dir))
    slide.save_thumbnail()
    report_path = str(out_dir / "report.csv")
    tiler.extract(slide, report_path=report_path)
    df = pd.read_csv(report_path)
    df["slide"] = slide_path.stem
    all_reports.append(df)
    print(f"{slide_path.stem}: {len(df)} tiles, mean score {df['score'].mean():.3f}")

combined = pd.concat(all_reports, ignore_index=True)
combined.to_csv(output_base / "dataset_manifest.csv", index=False)
print(f"Total: {len(combined)} tiles from {len(all_reports)} slides")
```

### Workflow 3: Custom Tissue Detection with Artifact Removal

**Goal**: Handle slides with pen annotations or unusual staining using custom filter pipelines.

```python
from histolab.slide import Slide
from histolab.masks import TissueMask
from histolab.tiler import GridTiler
from histolab.filters.compositions import Compose
from histolab.filters.image_filters import RgbToGrayscale, OtsuThreshold
from histolab.filters.morphological_filters import (
    BinaryDilation, RemoveSmallObjects, RemoveSmallHoles
)

# Aggressive artifact removal pipeline
aggressive_filters = Compose([
    RgbToGrayscale(),
    OtsuThreshold(),
    BinaryDilation(disk_size=10),
    RemoveSmallHoles(area_threshold=5000),
    RemoveSmallObjects(area_threshold=3000)
])

custom_mask = TissueMask(filters=aggressive_filters)
slide = Slide("artifact_slide.svs", processed_path="output/clean/")

# Compare default vs custom mask
slide.locate_mask(TissueMask())     # Default
slide.locate_mask(custom_mask)      # Custom (tighter)

# Extract with custom mask
grid_tiler = GridTiler(
    tile_size=(512, 512), level=1,
    check_tissue=True, tissue_percent=70.0
)
grid_tiler.extract(slide, extraction_mask=custom_mask)
```

## Key Parameters

| Parameter | Module | Default | Range / Options | Effect |
|-----------|--------|---------|-----------------|--------|
| `tile_size` | All Tilers | `(512, 512)` | Any `(w, h)` tuple | Tile dimensions in pixels |
| `level` | All Tilers | `0` | `0` to `slide.levels-1` | Pyramid level (0=highest resolution) |
| `check_tissue` | All Tilers | `True` | `True`/`False` | Filter tiles by tissue content |
| `tissue_percent` | All Tilers | `80.0` | `0.0`-`100.0` | Minimum tissue coverage threshold |
| `n_tiles` | Random/ScoreTiler | varies | Any positive int | Number of tiles to extract |
| `seed` | RandomTiler | `None` | Any int | Random seed for reproducibility |
| `pixel_overlap` | GridTiler | `0` | `0`+ | Overlap between adjacent tiles in pixels |
| `scorer` | ScoreTiler | required | `NucleiScorer()`, `CellularityScorer()`, custom | Scoring function for tile ranking |
| `extraction_mask` | All Tilers | `BiggestTissueBoxMask()` | Any `BinaryMask` | Mask defining valid extraction region |
| `disk_size` | Morphological filters | `5` | `1`-`20` | Structuring element size |
| `area_threshold` | RemoveSmall* | `500`/`1000` | `0`+ | Minimum area for objects/holes in pixels |

## Best Practices

1. **Always preview before extracting**: Call `locate_tiles()` and `locate_mask()` to validate settings before committing to full extraction. This saves hours on large slide collections.

2. **Match level to analysis resolution**: Level 0 provides maximum detail but is slow; level 1-2 is typically sufficient for initial analysis. Use level 0 only for tasks requiring cellular detail.

3. **Choose the right tiler strategy**:
   - `RandomTiler` for exploratory analysis and diverse sampling
   - `GridTiler` for complete coverage and spatial analysis
   - `ScoreTiler` for quality-driven dataset curation

4. **Use seeds for reproducibility**: Always set `seed` in `RandomTiler` to ensure consistent tile selection across runs.

5. **Customize masks for specific stains**: H&E and IHC stains have different color profiles. Adjust filter parameters or build custom `Compose` pipelines for non-standard stains.

6. **Anti-pattern -- Don't use TissueMask when BiggestTissueBoxMask suffices**: `TissueMask` is more computationally expensive. Use it only when the slide has multiple tissue sections.

7. **Enable logging for batch processing**: `logging.basicConfig(level=logging.INFO)` provides progress tracking during extraction.

8. **Generate CSV reports with ScoreTiler**: Use `report_path` in `extract()` to create metadata manifests for downstream ML pipelines.

9. **Anti-pattern -- Don't extract at level 0 for initial exploration**: Use level 1 or 2 for fast iteration, then switch to level 0 for final dataset generation.

## Common Recipes

### Recipe: Nuclei Enhancement Pipeline

When to use: Isolate and enhance nuclei signal from H&E stained sections for analysis.

```python
from histolab.filters.image_filters import RgbToHed, HistogramEqualization, Lambda
from histolab.filters.compositions import Compose

nuclei_pipeline = Compose([
    RgbToHed(),
    Lambda(lambda hed: hed[:, :, 0]),  # Extract hematoxylin channel
    HistogramEqualization()
])

# Apply to slide thumbnail for visualization
enhanced = nuclei_pipeline(slide.thumbnail)
```

### Recipe: Score Distribution Analysis

When to use: Assess tile quality distribution and identify optimal score thresholds.

```python
import pandas as pd
import matplotlib.pyplot as plt

report = pd.read_csv("tiles_report.csv")
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

axes[0].hist(report['score'], bins=30, edgecolor='black', alpha=0.7)
axes[0].set_xlabel('Tile Score'); axes[0].set_ylabel('Frequency')
axes[0].set_title('Score Distribution')

axes[1].scatter(report['tissue_percent'], report['score'], alpha=0.5)
axes[1].set_xlabel('Tissue %'); axes[1].set_ylabel('Score')
axes[1].set_title('Score vs Tissue Coverage')

plt.tight_layout()
plt.savefig("quality_analysis.png", dpi=150, bbox_inches='tight')
plt.show()
```

### Recipe: Multi-Level Hierarchical Extraction

When to use: Extract tiles at multiple magnification levels from the same locations for multi-scale analysis.

```python
from histolab.tiler import RandomTiler

for level in [0, 1, 2]:
    tiler = RandomTiler(
        tile_size=(512, 512), n_tiles=50,
        level=level, seed=42,  # Same seed = same locations
        prefix=f"level{level}_"
    )
    tiler.extract(slide)
    print(f"Extracted level {level} tiles")
```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `OpenSlideError: Unsupported format` | OpenSlide C library not installed or slide format unsupported | Install OpenSlide system library; verify format with `openslide-show-properties` |
| No tiles extracted | `tissue_percent` too high or mask misses tissue | Lower `tissue_percent` (try 60-70%); preview mask with `locate_mask()` |
| Many background tiles | `check_tissue=False` or poor mask | Enable `check_tissue=True`; increase `tissue_percent`; use `TissueMask()` |
| Extraction very slow | Level 0 on large slide or `TissueMask` on many sections | Extract at level 1-2; use `BiggestTissueBoxMask`; reduce `n_tiles` |
| Tiles have pen artifacts | Default mask includes pen marks | Build custom filter with HSV-based pen detection; increase `RemoveSmallObjects` threshold |
| `MemoryError` during extraction | Level 0 tile access on very large WSI | Extract at lower level; process fewer tiles per batch |
| Inconsistent results across runs | Missing `seed` in `RandomTiler` | Always set `seed` parameter |
| Tiles too small/large for model | `tile_size` mismatch with model input | Adjust `tile_size` to match model requirements (commonly 224, 256, 512) |

## Bundled Resources

### references/filters_preprocessing.md

Comprehensive filter reference covering all image filters (RgbToGrayscale, RgbToHsv, RgbToHed, OtsuThreshold, AdaptiveThreshold, Invert, StretchContrast, HistogramEqualization, Lambda) and morphological filters (BinaryDilation, BinaryErosion, BinaryOpening, BinaryClosing, RemoveSmallObjects, RemoveSmallHoles) with individual code examples, use-case descriptions, and common preprocessing pipelines (tissue detection, pen removal, nuclei enhancement, stain normalization).

- **Covers**: All filter types with individual code blocks, `Compose` chaining, quality control filters, custom mask integration
- **Relocated inline**: Standard tissue detection pipeline and Lambda filter basics moved to Core API Module 4
- **Omitted**: Filter effect visualization step-by-step (covered in references/visualization_slides.md); best practices list partially consolidated into main Best Practices section

### references/tile_extraction.md

Detailed tile extraction reference covering all three tiler strategies (RandomTiler, GridTiler, ScoreTiler) with full parameter documentation, all built-in scorers (NucleiScorer, CellularityScorer), custom scorer creation, extraction workflows with logging and CSV reporting, and advanced patterns (multi-level, hierarchical, post-extraction blur filtering).

- **Covers**: Per-tiler parameters and use cases, scorer API, tile preview, extraction with reports, advanced patterns, performance optimization
- **Relocated inline**: Basic tiler usage and scorer creation moved to Core API Modules 3 and 5; common parameters table moved to Key Parameters
- **Omitted**: ASCII grid pattern diagrams (trivial visual aid)

### references/visualization_slides.md

Consolidated visualization, slide management, and tissue mask reference. Covers slide inspection workflows, mask comparison visualization, tile grid display, quality assessment (score distributions, top/bottom tile comparison), multi-slide collection thumbnails, tissue coverage bar charts, filter effect visualization pipeline, PDF report generation, and interactive Jupyter widgets.

- **Source**: Consolidates visualization.md (547 lines) + slide_management.md (172 lines) + tissue_masks.md (251 lines)
- **Covers**: All visualization patterns from original, slide inspection workflow, sample datasets, pyramid level enumeration, mask classes and customization, annotation exclusion pattern
- **Relocated inline**: Core slide properties and mask basics moved to Core API Modules 1-2; thumbnail display and basic locate_mask/locate_tiles moved to Module 6
- **Omitted**: Slide name/path trivial properties (2 lines); custom tile location visualization with manual coordinate calculation (conceptual only, not practical)

### Original reference file disposition (5 files):

1. **slide_management.md** (172 lines) -- (b) Consolidated: core content into Core API Module 1 (Slide class, properties, sample data, thumbnails, regions, pyramid levels); advanced slide inspection and multi-slide workflow into references/visualization_slides.md
2. **tissue_masks.md** (251 lines) -- (b) Consolidated: core mask classes and usage into Core API Module 2; custom masks (RectangularMask, AnnotationExclusionMask) and mask comparison into references/visualization_slides.md
3. **tile_extraction.md** (421 lines) -- (a) Migrated to references/tile_extraction.md with condensation
4. **filters_preprocessing.md** (514 lines) -- (a) Migrated to references/filters_preprocessing.md with condensation
5. **visualization.md** (547 lines) -- (a) Migrated to references/visualization_slides.md (consolidated with slide_management.md and tissue_masks.md content)

## Related Skills

- **pathml-spatial-omics (planned)** -- advanced multiplexed imaging and spatial proteomics
- **matplotlib-scientific-plotting** -- publication-quality figure generation from histolab outputs

## References

- [Histolab documentation](https://histolab.readthedocs.io/) -- official API reference and tutorials
- [Histolab GitHub repository](https://github.com/histolab/histolab) -- source code and examples
- [OpenSlide](https://openslide.org/) -- underlying C library for WSI format support
- [TCGA sample data](https://portal.gdc.cancer.gov/) -- source of built-in sample datasets
