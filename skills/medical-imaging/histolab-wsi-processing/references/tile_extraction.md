# Tile Extraction Reference

Detailed reference for histolab's tile extraction strategies, scoring functions, extraction workflows, and advanced patterns.

## Common Parameters

All tiler classes share these parameters:

```python
tile_size: tuple = (512, 512)       # Tile dimensions (width, height) in pixels
level: int = 0                      # Pyramid level (0=highest resolution)
check_tissue: bool = True           # Filter tiles by tissue content
tissue_percent: float = 80.0        # Minimum tissue coverage (0-100)
prefix: str = ""                    # Prefix for saved tile filenames
suffix: str = ".png"                # File extension for saved tiles
extraction_mask: BinaryMask = BiggestTissueBoxMask()  # Region constraint
```

## RandomTiler

Extract a fixed number of randomly positioned tiles from tissue regions.

```python
from histolab.tiler import RandomTiler

random_tiler = RandomTiler(
    tile_size=(512, 512),
    n_tiles=100,            # Number of tiles to extract
    level=0,
    seed=42,                # Random seed for reproducibility
    check_tissue=True,
    tissue_percent=80.0,
    max_iter=1000           # Maximum attempts to find valid tiles
)

random_tiler.extract(slide, extraction_mask=TissueMask())
```

**When to use**:
- Exploratory analysis and quick sampling
- Creating diverse training datasets
- Balanced sampling from multiple slides
- Fast initial assessment of slide content

**Advantages**: Computationally efficient, good morphological diversity, reproducible with seed.

**Limitations**: May miss rare patterns, no coverage guarantee, random distribution may not capture structured features.

## GridTiler

Systematically extract tiles across tissue in a regular grid pattern.

```python
from histolab.tiler import GridTiler

grid_tiler = GridTiler(
    tile_size=(512, 512),
    level=0,
    check_tissue=True,
    tissue_percent=80.0,
    pixel_overlap=0         # Overlap between adjacent tiles
)

grid_tiler.extract(slide)
```

**`pixel_overlap` settings**:
- `0`: Non-overlapping tiles (default)
- `64-256`: Sliding window with partial overlap
- Use overlap for segmentation tasks requiring boundary coverage

**When to use**:
- Complete tissue coverage for whole-slide analysis
- Spatial analysis requiring positional information
- Image reconstruction from tiles
- Semantic segmentation tasks

**Advantages**: Complete coverage, preserves spatial relationships, predictable positions.

**Limitations**: Computationally intensive on large slides, may generate many low-tissue tiles (mitigated by `check_tissue`), larger output datasets.

## ScoreTiler

Extract top-ranked tiles based on a scoring function.

```python
from histolab.tiler import ScoreTiler
from histolab.scorer import NucleiScorer

score_tiler = ScoreTiler(
    tile_size=(512, 512),
    n_tiles=50,             # Number of top-scoring tiles to keep
    level=0,
    scorer=NucleiScorer(),
    check_tissue=True
)

score_tiler.extract(slide, report_path="tiles_report.csv")
```

**When to use**:
- Extracting the most informative regions
- Prioritizing tiles with specific features (nuclei, cellularity)
- Quality-based dataset curation
- Focusing on diagnostically relevant areas

**Advantages**: Focuses on most informative content, reduces dataset size while maintaining quality, customizable scoring.

**Limitations**: Slower than RandomTiler (scores all candidates), requires appropriate scorer, may miss low-scoring but relevant regions.

## Scorers

### NucleiScorer

Scores tiles based on nuclei detection and density. Converts tile to grayscale, applies thresholding, counts nuclei-like structures, and assigns density score.

```python
from histolab.scorer import NucleiScorer

nuclei_scorer = NucleiScorer()
# Best for: cell-rich regions, tumor detection, mitosis analysis
```

### CellularityScorer

Scores tiles based on overall cellular content (tissue vs stroma ratio).

```python
from histolab.scorer import CellularityScorer

cellularity_scorer = CellularityScorer()
# Best for: tumor cellularity, dense vs sparse tissue separation
```

### Custom Scorers

Subclass `Scorer` to implement domain-specific scoring.

```python
from histolab.scorer import Scorer
import numpy as np

class ColorVarianceScorer(Scorer):
    def __call__(self, tile):
        """Score by color variance — higher values indicate more varied tissue."""
        tile_array = np.array(tile.image)
        return np.var(tile_array, axis=(0, 1)).sum()

class StainIntensityScorer(Scorer):
    def __call__(self, tile):
        """Score by hematoxylin intensity (nuclear staining)."""
        from histolab.filters.image_filters import RgbToHed
        hed = RgbToHed()(np.array(tile.image))
        return np.mean(hed[:, :, 0])  # Mean hematoxylin channel

# Use with ScoreTiler
score_tiler = ScoreTiler(
    tile_size=(512, 512), n_tiles=30,
    scorer=StainIntensityScorer()
)
```

## Tile Preview

### locate_tiles()

Preview tile locations before extraction to validate configuration.

```python
# RandomTiler: show n_tiles sample locations
random_tiler.locate_tiles(slide, n_tiles=20)

# GridTiler: show all grid positions
grid_tiler.locate_tiles(slide)

# ScoreTiler: show top-n tile locations
score_tiler.locate_tiles(slide, n_tiles=15)
```

Displays colored rectangles on the slide thumbnail indicating where tiles will be extracted.

## Extraction Workflows

### Basic Extraction

```python
from histolab.slide import Slide
from histolab.tiler import RandomTiler

slide = Slide("slide.svs", processed_path="output/tiles/")
tiler = RandomTiler(tile_size=(512, 512), n_tiles=100, level=0, seed=42)
tiler.extract(slide)
# Tiles saved to: output/tiles/*.png
```

### Extraction with Logging

```python
import logging

logging.basicConfig(level=logging.INFO)
tiler.extract(slide)
# INFO: Tile 1/100 saved...
# INFO: Tile 2/100 saved...
```

### Extraction with CSV Report

ScoreTiler generates a CSV report with tile metadata.

```python
score_tiler = ScoreTiler(
    tile_size=(512, 512), n_tiles=50,
    scorer=NucleiScorer()
)
score_tiler.extract(slide, report_path="tiles_report.csv")
```

Report columns:
```
tile_name,x_coord,y_coord,level,score,tissue_percent
tile_001.png,10240,5120,0,0.89,95.2
tile_002.png,15360,7680,0,0.85,91.7
```

## Advanced Patterns

### Multi-Level Extraction

Extract tiles at different magnification levels for multi-scale analysis.

```python
for level in [0, 1, 2]:
    tiler = RandomTiler(
        tile_size=(512, 512), n_tiles=50,
        level=level, prefix=f"level{level}_"
    )
    tiler.extract(slide)
```

### Hierarchical Extraction (Same Locations, Different Scales)

Use the same seed to extract tiles at the same positions across levels.

```python
for level in [0, 1]:
    tiler = RandomTiler(
        tile_size=(512, 512), n_tiles=30,
        level=level, seed=42,  # Same seed = same locations
        prefix=f"level{level}_"
    )
    tiler.extract(slide)
```

### Post-Extraction Blur Filtering

Remove blurry tiles after extraction using Laplacian variance.

```python
from PIL import Image
import numpy as np
import cv2
from pathlib import Path

def filter_blurry_tiles(tile_dir, threshold=100):
    """Remove tiles below blur quality threshold."""
    for tile_path in Path(tile_dir).glob("*.png"):
        img = Image.open(tile_path)
        gray = np.array(img.convert('L'))
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        if laplacian_var < threshold:
            tile_path.unlink()
            print(f"Removed blurry: {tile_path.name} (score={laplacian_var:.1f})")

tiler.extract(slide)
filter_blurry_tiles("output/tiles/", threshold=100)
```

## Performance Optimization

1. **Extract at appropriate level**: Level 1-2 is 4-16x faster than level 0
2. **Adjust tissue_percent**: Higher thresholds reduce invalid tile attempts
3. **Use BiggestTissueBoxMask**: Faster than TissueMask for single sections
4. **Limit n_tiles**: For RandomTiler and ScoreTiler initial exploration
5. **Use pixel_overlap=0**: Minimize tile count in GridTiler
6. **Enable logging**: Monitor progress to estimate completion time

## Tiler Selection Guide

| Criterion | RandomTiler | GridTiler | ScoreTiler |
|-----------|-------------|-----------|------------|
| Speed | Fast | Slow (large slides) | Medium |
| Coverage | Sampled | Complete | Top-N |
| Reproducibility | With seed | Deterministic | Deterministic |
| Output size | Fixed (n_tiles) | Variable | Fixed (n_tiles) |
| Best for | Exploration, training | Spatial analysis | Quality curation |
| Preserves spatial info | No | Yes | Partial |

---

Condensed from original: 421 lines. Retained: all three tiler strategies with full parameters, all scorer types (NucleiScorer, CellularityScorer, custom), locate_tiles preview, extraction workflows (basic, logging, CSV report), advanced patterns (multi-level, hierarchical, blur filtering), performance optimization, tiler selection guide. Omitted: ASCII grid overlap diagrams (trivial visual aid); per-tiler advantages/limitations prose shortened to bullet summaries.
