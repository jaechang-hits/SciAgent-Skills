---
name: cell-figure-guide
description: "Figure and image preparation guide for Cell (Cell Press) journal. Covers resolution (300-1000 DPI by type), file formats (TIFF, PDF), RGB color mode, Avenir/Arial fonts, uppercase panel labels, and strict image manipulation policies."
license: CC-BY-4.0
compatibility: Python 3.10+, Pillow, Matplotlib
metadata:
  authors: HITS
  version: "1.0"
---

# Cell Figure Preparation Guide

## Overview

This guide provides the complete specifications for preparing figures for submission to **Cell** and other Cell Press journals (e.g., Cell Stem Cell, Cell Reports, Molecular Cell). Cell Press has strict figure requirements and a rigorous image integrity policy.

**Official reference**: https://www.cell.com/information-for-authors/figure-guidelines

---

## Resolution Requirements

| Image Type | Minimum Resolution | Notes |
|---|---|---|
| Color / Grayscale photographs | **300 DPI** | At desired print size |
| Black-and-white images | **500 DPI** | At desired print size |
| Line art (graphs, diagrams) | **1,000 DPI** | At desired print size |

**IMPORTANT**: All resolution measurements are at the **desired print size**, not at full-page size.

### Verify Resolution

```python
from PIL import Image

def check_cell_resolution(image_path, image_type='color'):
    """Check if image meets Cell journal resolution requirements.

    Args:
        image_path: Path to the image file
        image_type: 'color' (300 DPI), 'bw' (500 DPI), or 'lineart' (1000 DPI)
    """
    min_dpi = {'color': 300, 'bw': 500, 'lineart': 1000}
    required = min_dpi.get(image_type, 300)

    img = Image.open(image_path)
    dpi = img.info.get('dpi', (72, 72))

    print(f"Image type: {image_type}")
    print(f"Required DPI: {required}")
    print(f"Actual DPI: {dpi[0]} x {dpi[1]}")

    if dpi[0] >= required:
        print("PASS: Resolution meets Cell requirements")
    else:
        print(f"FAIL: Need at least {required} DPI, got {dpi[0]}")

    return dpi[0] >= required
```

---

## File Format

### Preferred Formats

| Format | Best For | Notes |
|---|---|---|
| **TIFF** | Bitmap, grayscale, color images | Use LZW compression to reduce size |
| **PDF** | Any figure type | Universally accepted |
| **EPS** | Vector images (graphs, diagrams) | Preserves scalability |

### Also Accepted
- JPEG, CDX files

### File Size
- Individual files: **20 MB maximum**

### Submission Notes
- Initial submission: Figures can be embedded in manuscript or uploaded separately
- Final production: Separate high-resolution files required

---

## Figure Size and Dimensions

### 2-Column Format Journals (Cell, Molecular Cell, etc.)

| Layout | Width |
|---|---|
| 1 column | **85 mm** (3.35 in) |
| 1.5 columns | **114 mm** (4.49 in) |
| Full width | **174 mm** (6.85 in) |

### 3-Column Format Journals

| Layout | Width |
|---|---|
| 1 column | **55 mm** (2.17 in) |
| 2 columns | **114 mm** (4.49 in) |
| Full width | **174 mm** (6.85 in) |

### Other Cell Press Journals (Chem, Joule, Matter, etc.)

| Layout | Width |
|---|---|
| 1 column | **112 mm** (4.41 in) |
| Full width | **172 mm** (6.77 in) |

**All figures** must fit on a single 8.5" x 11" page.

### Python: Set Cell Figure Dimensions

```python
import matplotlib.pyplot as plt

# Cell Press figure widths in inches
CELL_WIDTHS = {
    '2col_single':   85 / 25.4,   # 3.35 in
    '2col_1.5':      114 / 25.4,  # 4.49 in
    '2col_full':     174 / 25.4,  # 6.85 in
    '3col_single':   55 / 25.4,   # 2.17 in
    '3col_double':   114 / 25.4,  # 4.49 in
    '3col_full':     174 / 25.4,  # 6.85 in
}

def create_cell_figure(layout='2col_single', aspect_ratio=0.75):
    """Create a Matplotlib figure sized for Cell Press journals."""
    width = CELL_WIDTHS[layout]
    height = width * aspect_ratio

    fig, ax = plt.subplots(figsize=(width, height))
    fig.set_dpi(300)

    return fig, ax
```

---

## Color Mode

- **Submit in RGB** color space
- Journal converts to CMYK for print production
- RGB preserves brighter colors for online viewing

```python
from PIL import Image

def convert_to_rgb_for_cell(image_path, output_path):
    """Convert image to RGB for Cell Press submission."""
    img = Image.open(image_path)
    if img.mode == 'CMYK':
        img = img.convert('RGB')
        print("Converted from CMYK to RGB")
    elif img.mode != 'RGB':
        img = img.convert('RGB')
        print(f"Converted from {img.mode} to RGB")
    img.save(output_path)
    return output_path
```

---

## Font Requirements

| Element | Font | Size |
|---|---|---|
| Primary font | **Avenir** (preferred), Arial, Helvetica | — |
| Figure text | — | ~**7 pt** at print size |
| Panel labels | — | Bold, **capital letters** |

### Critical Rules
- **All fonts must be embedded** in Adobe Illustrator files
- Use Avenir as the first choice; Arial or Helvetica as alternatives
- Consistent font usage across all figure panels

```python
import matplotlib.pyplot as plt

def set_cell_fonts():
    """Configure Matplotlib for Cell Press figure fonts."""
    plt.rcParams.update({
        'font.family': 'sans-serif',
        'font.sans-serif': ['Avenir', 'Arial', 'Helvetica'],
        'font.size': 7,
        'axes.labelsize': 7,
        'axes.titlesize': 7,
        'xtick.labelsize': 6,
        'ytick.labelsize': 6,
        'legend.fontsize': 6,
    })
```

---

## Labeling Conventions

### Panel Labels
- **Capital letters**: A, B, C, D, ...
- Bold weight
- Position: top-left corner of each panel

### Titles
- **Do NOT place titles inside figures** — include them in the figure caption instead
- Remove any labels not essential for understanding the figure; explain in caption

```python
import matplotlib.pyplot as plt
import string

def add_cell_panel_labels(fig, axes):
    """Add Cell-style uppercase bold panel labels."""
    if not hasattr(axes, '__iter__'):
        axes = [axes]

    for i, ax in enumerate(axes):
        label = string.ascii_uppercase[i]
        ax.text(-0.1, 1.1, label,
                transform=ax.transAxes,
                fontsize=8,
                fontweight='bold',
                va='top',
                ha='right',
                fontfamily='Arial')
```

---

## Image Integrity and Manipulation Policy

### STRICTLY PROHIBITED
- **Photoshop clone/heal tool usage** on scientific images
- Selective enhancement or alteration of any part of an image
- Splicing images from different experiments without clear indication
- Touching up gel/blot images to hide or alter data

### PERMITTED (with full disclosure)
- Brightness, contrast, and color adjustments applied **uniformly to the entire image**
- Minimal image processing for microscopy (must be described in Methods)

### REQUIRED
- Single color channel alterations must be explained in **both legend and Methods**
- Gel images: removed lanes must be **clearly marked** and alterations noted in legend
- **Original unprocessed data** must be available upon editor/reviewer request
- All processing steps must be transparently described

---

## Python Quick Start: Full Validation

```python
from PIL import Image
import os

def validate_cell_figure(image_path, image_type='color', layout='2col_single'):
    """Full validation of a figure against Cell Press requirements."""
    img = Image.open(image_path)
    issues = []

    # 1. Resolution check
    min_dpi = {'color': 300, 'bw': 500, 'lineart': 1000}
    required_dpi = min_dpi.get(image_type, 300)
    dpi = img.info.get('dpi', (72, 72))
    if dpi[0] < required_dpi:
        issues.append(f"Resolution {dpi[0]} DPI below minimum {required_dpi} DPI for {image_type}")

    # 2. Color mode check
    if img.mode != 'RGB':
        issues.append(f"Color mode is {img.mode}; Cell requires RGB submission")

    # 3. File size check
    size_mb = os.path.getsize(image_path) / (1024 * 1024)
    if size_mb > 20:
        issues.append(f"File size {size_mb:.1f} MB exceeds 20 MB limit")

    # 4. Dimension check (width in mm)
    widths_mm = {
        '2col_single': 85, '2col_1.5': 114, '2col_full': 174,
        '3col_single': 55, '3col_double': 114, '3col_full': 174,
    }
    if layout in widths_mm and dpi[0] > 0:
        max_width_mm = widths_mm[layout]
        actual_width_mm = (img.size[0] / dpi[0]) * 25.4
        print(f"Width at current DPI: {actual_width_mm:.1f} mm (target: {max_width_mm} mm)")

    # Report
    print(f"=== Cell Figure Validation: {os.path.basename(image_path)} ===")
    print(f"Dimensions: {img.size[0]} x {img.size[1]} px")
    print(f"DPI: {dpi[0]} x {dpi[1]}")
    print(f"Color mode: {img.mode}")
    print(f"File size: {size_mb:.1f} MB")

    if issues:
        print(f"\nISSUES FOUND ({len(issues)}):")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("\nAll checks PASSED")

    return len(issues) == 0
```

---

## Key Concepts

### Resolution Tiers by Image Type

Cell Press uses a three-tier resolution system: 300 DPI for color/grayscale photographs, 500 DPI for black-and-white images, and 1,000 DPI for line art. All measurements are at the desired print size, not at arbitrary large dimensions. This tiered approach ensures each image type reproduces at appropriate quality.

### Cell Press Column System

Cell Press journals use different column layouts depending on the journal. Two-column journals (Cell, Molecular Cell) use 85/114/174 mm widths. Three-column journals use 55/114/174 mm. Other journals (Chem, Joule) use 112/172 mm. Sizing figures to the correct column width prevents unwanted rescaling.

### Image Manipulation Policy

Cell Press enforces one of the strictest image integrity policies in biomedical publishing. The use of Photoshop clone/heal tools on scientific images is explicitly prohibited. Any single-channel color alterations must be disclosed in both the figure legend and Methods section.

## Decision Framework

```
What type of image are you preparing?
├── Color or grayscale photograph → 300 DPI minimum
│   ├── Micrograph → TIFF (LZW compression)
│   └── Clinical image → TIFF or PDF
├── Black-and-white image → 500 DPI minimum
│   └── High-contrast micrograph → TIFF
├── Line art (graph, diagram) → 1,000 DPI minimum
│   ├── Vector source → Export as PDF or EPS
│   └── Raster source → Export TIFF at 1,000 DPI
└── Which journal layout?
    ├── Cell, Molecular Cell → 2-column (85/114/174 mm)
    ├── Cell Reports → 3-column (55/114/174 mm)
    └── Chem, Joule, Matter → Single/full (112/172 mm)
```

| Scenario | Format | Resolution | Width |
|---|---|---|---|
| Fluorescence micrograph | TIFF (LZW) | 300 DPI | Journal-specific column |
| Western blot | TIFF | 500 DPI | Single column (85 mm) |
| Bar chart or scatter plot | PDF or EPS | 1,000 DPI (if rasterized) | Varies by data density |
| Gel electrophoresis | TIFF | 500 DPI | Full width if multi-lane |
| Pathway diagram | PDF or EPS | Vector | Full width (174 mm) |

## Best Practices

1. **Use LZW compression for TIFF files**: Cell accepts TIFF with LZW compression, which significantly reduces file size without quality loss. This helps stay under the 20 MB limit
2. **Remove titles from figures**: Cell Press requires that figure titles appear only in captions, not inside the figure itself. Remove any embedded titles before submission
3. **Use Avenir as primary font**: While Arial and Helvetica are accepted, Avenir is Cell Press's preferred font. Using it signals familiarity with journal conventions
4. **Embed all fonts in AI files**: Adobe Illustrator files must have fonts fully embedded. Missing fonts cause rendering errors during production
5. **Disclose all gel image modifications**: Removed lanes must be clearly marked in the figure and described in the legend. Undisclosed modifications are grounds for rejection
6. **Match resolution to image type**: Do not use 300 DPI for line art (needs 1,000) or 1,000 DPI for photographs (wastes file size). Match the resolution tier to the content type
7. **Keep original unprocessed data**: Cell Press may request raw data during review or post-publication. Archive all originals alongside processed versions

## Common Pitfalls

1. **Applying 300 DPI to all image types**: Line art requires 1,000 DPI; black-and-white images require 500 DPI. Using 300 DPI for these types produces jagged edges
   - *How to avoid*: Check the three-tier resolution table and match your image type before export
2. **Using clone/heal tools on scientific images**: Cell Press explicitly prohibits Photoshop clone and heal tool usage on scientific data
   - *How to avoid*: Use only uniform brightness/contrast adjustments on the entire image; document all processing in Methods
3. **Placing titles inside figures**: Cell Press requires all titles in the caption, not embedded in the figure
   - *How to avoid*: Review each figure panel and remove any text that belongs in the caption
4. **Exceeding 20 MB file size**: Uncompressed TIFF files frequently exceed the limit
   - *How to avoid*: Apply LZW compression when saving TIFF files; check file size before upload
5. **Incorrect column width for journal**: Using 2-column widths for a 3-column journal (or vice versa) causes figures to be rescaled
   - *How to avoid*: Verify which Cell Press journal you are targeting and use the correct column width table
6. **Not disclosing single-channel color adjustments**: Altering individual color channels without disclosure violates Cell Press policy
   - *How to avoid*: Document any single-channel modifications in both the figure legend and Methods section

## Pre-Submission Checklist

Before submitting figures to Cell, verify:

- [ ] Color/grayscale images at 300+ DPI
- [ ] Black-and-white images at 500+ DPI
- [ ] Line art at 1,000+ DPI
- [ ] File format is TIFF (LZW), PDF, or EPS
- [ ] Each file under 20 MB
- [ ] Color mode is RGB
- [ ] Font is Avenir, Arial, or Helvetica at ~7 pt
- [ ] Panel labels are uppercase bold (A, B, C)
- [ ] No titles inside figures (use captions)
- [ ] All fonts embedded in AI files
- [ ] No clone/heal tool usage on scientific images
- [ ] All brightness/contrast adjustments applied to entire image
- [ ] Gel lane removals clearly marked in legend
- [ ] Processing details described in Methods
- [ ] Original unprocessed data retained

---

## References

- Cell Press Figure Guidelines: https://www.cell.com/information-for-authors/figure-guidelines
- Cell Press Digital Image Guidelines: https://www.cell.com/matter/figureguidelines
- Cell Press Image Integrity Policy: https://www.cell.com/cell/image-integrity
