---
name: lancet-figure-guide
description: "Figure and image preparation guide for The Lancet. Covers resolution (300+ DPI at 120% size), file formats (PowerPoint, Word, SVG preferred), column widths (75/154 mm), Times New Roman font, and Lancet in-house redraw policy."
license: CC-BY-4.0
compatibility: Python 3.10+, Pillow, Matplotlib
metadata:
  authors: HITS
  version: "1.0"
---

# The Lancet Figure Preparation Guide

## Overview

This guide provides the complete specifications for preparing figures for submission to **The Lancet** and Lancet family journals. A key distinguishing feature of The Lancet is that **most figures are redrawn by in-house illustrators** into Lancet house style. Therefore, editable source formats (PowerPoint, Word, SVG) are strongly preferred over rasterized images.

**Official reference**: https://www.thelancet.com/submission-guidelines

---

## Resolution Requirements

| Requirement | Specification |
|---|---|
| All photographic images | **300 DPI minimum** |
| Submission size | **120%** of intended publication size |

**TIP**: Supply images 20% larger than publication size to ensure quality is maintained after any resizing by the production team.

```python
from PIL import Image

def check_lancet_resolution(image_path):
    """Check if image meets Lancet resolution requirements."""
    img = Image.open(image_path)
    dpi = img.info.get('dpi', (72, 72))

    print(f"DPI: {dpi[0]} x {dpi[1]}")
    print(f"Minimum required: 300 DPI")
    print(f"TIP: Submit at 120% of publication size")

    if dpi[0] >= 300:
        print("PASS: Resolution meets Lancet requirements")
    else:
        print("FAIL: Need at least 300 DPI")

    return dpi[0] >= 300
```

---

## File Format

### Preferred Formats (Editable)

| Format | Notes |
|---|---|
| **PowerPoint (.pptx)** | Most preferred — easy for in-house redraw |
| **Word (.docx)** | Accepted for simple figures |
| **SVG** | Scalable vector graphics |

### Also Accepted

| Format | Notes |
|---|---|
| TIFF | For photographic images |
| JPEG | Acceptable quality |
| EPS | Vector format |
| PDF | General purpose |

### Why Editable Formats?
The Lancet's in-house illustration team **redraws most submitted figures** into the Lancet house style. Providing editable source files (especially PowerPoint) makes this process smoother and more accurate.

---

## Figure Size and Dimensions

| Layout | Width |
|---|---|
| 1 column | **75 mm** (2.95 in) |
| 2 columns | **154 mm** (6.06 in) |
| Minimum width | **107 mm** (4.21 in) |

- All panels must fit on a **single page**

```python
import matplotlib.pyplot as plt

LANCET_WIDTHS = {
    'single':  75 / 25.4,    # 2.95 inches
    'minimum': 107 / 25.4,   # 4.21 inches
    'double':  154 / 25.4,   # 6.06 inches
}

def create_lancet_figure(layout='single', aspect_ratio=0.75):
    """Create a Matplotlib figure sized for The Lancet."""
    width = LANCET_WIDTHS[layout]
    height = width * aspect_ratio

    fig, ax = plt.subplots(figsize=(width, height))
    fig.set_dpi(300)
    return fig, ax
```

---

## Color Mode

| Purpose | Color Mode |
|---|---|
| Online publication | **RGB** |
| Print publication | **CMYK** |

- Color and black-and-white photographs both accepted

---

## Font Requirements

| Element | Font | Size | Style |
|---|---|---|---|
| Main figure heading | Times New Roman | **10 pt** | **Bold** |
| Figure legend | Times New Roman | 10 pt | Regular, single-spaced |

### Key Difference from Other Journals
- The Lancet uses **Times New Roman** (serif font), unlike most other biomedical journals that prefer sans-serif fonts

```python
import matplotlib.pyplot as plt

def set_lancet_fonts():
    """Configure Matplotlib for Lancet figure fonts."""
    plt.rcParams.update({
        'font.family': 'serif',
        'font.serif': ['Times New Roman', 'Times'],
        'font.size': 10,
        'axes.labelsize': 10,
        'axes.titlesize': 10,
        'axes.titleweight': 'bold',
        'xtick.labelsize': 8,
        'ytick.labelsize': 8,
        'legend.fontsize': 8,
    })
```

---

## Labeling Conventions

### Rules
- **No box outlines** around graphs
- **No titles** inside graphs or artwork — include in caption instead
- Number figures in order of citation in text

### Best Practices
- Keep figures as simple and clear as possible
- The Lancet illustrators will redraw most figures, so focus on conveying data accurately rather than visual polish

---

## Image Integrity and Manipulation Policy

- Follow standard biomedical publishing ethics
- All image adjustments should be applied uniformly
- Describe any image processing in Methods
- Maintain original data for potential review

---

## Python Quick Start: Full Validation

```python
from PIL import Image
import os

def validate_lancet_figure(image_path, layout='single'):
    """Full validation of a figure against Lancet requirements."""
    img = Image.open(image_path)
    issues = []

    # 1. Resolution check (300 DPI at 120% size)
    dpi = img.info.get('dpi', (72, 72))
    if dpi[0] < 300:
        issues.append(f"Resolution {dpi[0]} DPI below 300 DPI minimum")

    # 2. Dimension check
    widths_mm = {'single': 75, 'minimum': 107, 'double': 154}
    if layout in widths_mm and dpi[0] > 0:
        actual_w_mm = (img.size[0] / dpi[0]) * 25.4
        target = widths_mm[layout]
        # Should be 120% of publication size
        target_120 = target * 1.2
        print(f"Width: {actual_w_mm:.1f} mm (target at 120%: {target_120:.1f} mm)")

    # 3. Format recommendation
    fmt = img.format
    if fmt and fmt.upper() in ('TIFF', 'JPEG', 'PNG'):
        print(f"NOTE: Format is {fmt}. Lancet prefers PowerPoint/Word/SVG for redrawing")

    # Report
    print(f"=== Lancet Figure Validation ===")
    print(f"Dimensions: {img.size[0]} x {img.size[1]} px")
    print(f"DPI: {dpi[0]} x {dpi[1]}")
    print(f"Color mode: {img.mode}")

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

### In-House Figure Redraw Policy

The Lancet's most distinctive feature is that most submitted figures are redrawn by in-house illustrators into Lancet house style. This means editable source formats (PowerPoint, Word, SVG) are strongly preferred over polished raster images. Authors should focus on data accuracy rather than visual refinement.

### The 120% Size Rule

The Lancet requires photographic images to be submitted at 120% of intended publication size at 300+ DPI. This buffer ensures quality is maintained after any resizing during production. A figure intended for single-column (75 mm) should be supplied at 90 mm width.

### Serif Font Convention

Unlike most biomedical journals that use sans-serif fonts, The Lancet uses Times New Roman as its standard figure font. Headings are 10 pt bold; legend text is 10 pt regular single-spaced. This aligns with Lancet's traditional typographic style.

## Decision Framework

```
What type of figure are you preparing?
├── Data visualization (graph, chart)
│   ├── PowerPoint available → Submit .pptx (preferred for redraw)
│   └── Only image available → SVG or EPS (vector, editable)
├── Photograph or clinical image
│   ├── High quality needed → TIFF at 300+ DPI, 120% size
│   └── Standard quality → JPEG at 300+ DPI, 120% size
└── Schematic or diagram
    ├── Editable source → PowerPoint or Word
    └── Vector only → SVG or EPS
```

| Scenario | Format | Resolution | Notes |
|---|---|---|---|
| Bar chart from clinical trial | PowerPoint (.pptx) | N/A (vector) | Lancet redraws in house style |
| Kaplan-Meier curve | PowerPoint or SVG | N/A (vector) | Provide raw data if possible |
| Histology micrograph | TIFF | 300+ DPI at 120% size | Cannot be redrawn |
| Flowchart (CONSORT) | PowerPoint or Word | N/A (editable) | Lancet will redraw |
| Forest plot (meta-analysis) | PowerPoint or SVG | N/A (vector) | Data accuracy is priority |

## Best Practices

1. **Submit editable formats whenever possible**: PowerPoint is most preferred because Lancet illustrators redraw figures. Provide the editable source, not a rasterized export
2. **Supply images at 120% of publication size**: Calculate target size (75 mm or 154 mm column width), then multiply by 1.2 for the submission dimensions
3. **Use Times New Roman consistently**: The Lancet's serif font convention differs from most journals. Set Times New Roman as default before creating figures
4. **Remove box outlines from graphs**: Lancet style does not use borders around graph panels. Remove any automatic axis boxes
5. **Place titles in captions only**: Do not embed titles inside figures or graphs. All descriptive text goes in the figure caption
6. **Focus on data accuracy over aesthetics**: Since figures will be redrawn, ensure data values are correct and clearly labeled rather than investing in visual polish
7. **Number figures in citation order**: Figures must be numbered sequentially in the order they are first cited in the text

## Common Pitfalls

1. **Submitting only rasterized images for data figures**: Lancet illustrators cannot redraw from JPEG/PNG rasters of graphs
   - *How to avoid*: Always provide the editable source file (PowerPoint, Word, or SVG) alongside any raster export
2. **Forgetting the 120% size requirement**: Submitting at 100% publication size means the image will be undersized after production resizing
   - *How to avoid*: Multiply the target column width by 1.2 before setting your canvas size
3. **Using sans-serif fonts**: Most journals use Arial/Helvetica, but Lancet uses Times New Roman. Sans-serif fonts signal unfamiliarity with Lancet style
   - *How to avoid*: Set Times New Roman as the default font before creating any Lancet figures
4. **Including box outlines around graphs**: Lancet style prohibits boxes around graph panels, a common default in plotting software
   - *How to avoid*: Disable axis box/frame in your plotting settings (e.g., `ax.spines` in matplotlib)
5. **Over-polishing figure aesthetics**: Since Lancet redraws most figures, spending excessive time on visual refinement is wasted effort
   - *How to avoid*: Ensure data accuracy and clear labeling; leave visual styling to Lancet's illustration team

## Pre-Submission Checklist

Before submitting figures to The Lancet, verify:

- [ ] Photographic images at 300+ DPI
- [ ] Images supplied at **120% of publication size**
- [ ] Preferred format: PowerPoint, Word, or SVG (for in-house redraw)
- [ ] TIFF/JPEG/EPS acceptable for photographs
- [ ] 1-column figures: 75 mm wide
- [ ] 2-column figures: 154 mm wide
- [ ] All panels fit on a single page
- [ ] Font is Times New Roman (10 pt bold for headings)
- [ ] No box outlines around graphs
- [ ] No titles inside graphs (use captions)
- [ ] Figures numbered in order of text citation
- [ ] Data clearly and accurately represented (Lancet will redraw)
- [ ] Original data retained for review

---

## References

- Lancet Submission Guidelines: https://www.thelancet.com/submission-guidelines
- Lancet Artwork Guidelines: https://www.thelancet.com/pb/assets/raw/Lancet/test/artwork-guidelines-aug2015.pdf
- Lancet Information for Authors: https://www.thelancet.com/information-for-authors
