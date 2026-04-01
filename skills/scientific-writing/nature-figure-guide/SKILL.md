---
name: nature-figure-guide
description: "Figure and image preparation guide for Nature journal. Covers resolution (300+ DPI), file formats (AI, EPS, TIFF), RGB color mode, Helvetica/Arial fonts, lowercase panel labels, and image integrity requirements."
license: CC-BY-4.0
compatibility: Python 3.10+, Pillow, Matplotlib
metadata:
  authors: HITS
  version: "1.0"
---

# Nature Figure Preparation Guide

## Overview

This guide provides the complete specifications for preparing figures for submission to **Nature** and Nature Research journals. Following these guidelines ensures smooth processing and high-quality reproduction of your figures in both print and online formats.

**Official reference**: https://www.nature.com/nature/for-authors/formatting-guide

---

## Resolution Requirements

| Image Type | Minimum Resolution | Notes |
|---|---|---|
| All figures | 300 DPI | At maximum print size |
| Optimal quality | 450 DPI+ | Recommended for best online display |
| Online submission | 300 PPI max | To keep file sizes manageable |

**CRITICAL**: Do NOT artificially increase resolution (upsampling) in image editing software. This does not improve quality and may introduce artifacts.

### Verify Resolution with Python

```python
from PIL import Image

def check_nature_resolution(image_path):
    """Check if image meets Nature's resolution requirements."""
    img = Image.open(image_path)
    width_px, height_px = img.size
    dpi = img.info.get('dpi', (72, 72))

    print(f"Image: {image_path}")
    print(f"Dimensions: {width_px} x {height_px} px")
    print(f"DPI: {dpi[0]} x {dpi[1]}")

    if dpi[0] < 300 or dpi[1] < 300:
        print("WARNING: Resolution below 300 DPI minimum")
        print(f"  Need at least 300 DPI for Nature submission")
    elif dpi[0] >= 450:
        print("PASS: Meets optimal resolution (450+ DPI)")
    else:
        print("PASS: Meets minimum resolution (300+ DPI)")

    # Check file size
    import os
    size_mb = os.path.getsize(image_path) / (1024 * 1024)
    print(f"File size: {size_mb:.1f} MB")
    if size_mb > 10:
        print("WARNING: File exceeds 10 MB limit")

    return dpi[0] >= 300 and dpi[1] >= 300
```

---

## File Format

### Preferred Formats by Figure Type

| Figure Type | Preferred Format | Alternative |
|---|---|---|
| Line drawings, graphs, schematics | Adobe Illustrator (AI), EPS, PDF | Vector formats preserve editability |
| Photographs, micrographs | Photoshop (PSD), TIFF | High-quality raster |
| General purpose | JPEG (300-600 DPI) | Acceptable for most figures |
| Extended Data figures | JPEG (preferred), TIFF, EPS | |

### Also Accepted
- CorelDraw (up to version 8)
- Microsoft Word, Excel, PowerPoint

### File Size
- **Maximum**: 10 MB per figure file
- Most files should be well under this limit

### Important Rules
- Multi-panel figures must be assembled into a **single image file**
- Individual panels must NOT be uploaded separately
- Each complete figure must be a separate file upload

---

## Figure Size and Dimensions

Nature does not specify fixed column widths for initial submission, but figures should be:

- Composed as a **single image** for multi-panel figures
- Sized appropriately for the intended display
- **Not** uploaded as individual panels

### Python: Set Figure Dimensions

```python
import matplotlib.pyplot as plt

def create_nature_figure(n_panels=1, fig_type='single_column'):
    """Create a Matplotlib figure sized for Nature."""
    if fig_type == 'single_column':
        fig_width = 3.5  # inches (approx 89 mm)
    elif fig_type == 'double_column':
        fig_width = 7.0  # inches (approx 178 mm)
    else:
        fig_width = 5.0  # 1.5 column

    fig_height = fig_width * 0.75  # default aspect ratio

    fig, axes = plt.subplots(1, n_panels, figsize=(fig_width, fig_height))
    fig.set_dpi(450)

    return fig, axes
```

---

## Color Mode

- **RGB recommended** (wider color gamut; faithful reproduction of fluorescent colors online)
- CMYK also accepted (converted for print automatically)
- **Accessibility**: Use colorblind-friendly palettes

### Recommended Colorblind-Safe Palette

```python
# Nature-friendly colorblind-safe colors
NATURE_COLORS = {
    'blue':   '#0072B2',
    'orange': '#E69F00',
    'green':  '#009E73',
    'red':    '#D55E00',
    'purple': '#CC79A7',
    'cyan':   '#56B4E9',
    'yellow': '#F0E442',
    'black':  '#000000',
}
```

---

## Font Requirements

| Element | Font | Size | Style |
|---|---|---|---|
| Body text in figures | Helvetica or Arial | 5-7 pt | Regular |
| Panel labels | Helvetica or Arial | 8 pt | **Bold, lowercase** (a, b, c) |
| Amino acid sequences | Courier | — | Monospace |
| Greek characters | Symbol | — | — |

### Critical Rules
- Use **sans-serif** fonts only (Helvetica or Arial)
- **Do NOT outline text** — text must remain editable
- Embed fonts as TrueType 2 or 42 (NOT TrueType 3)
- Panel labels: **lowercase bold letters** (a, b, c — not A, B, C)

### Python: Apply Nature Font Settings

```python
import matplotlib.pyplot as plt

def set_nature_fonts():
    """Configure Matplotlib for Nature figure fonts."""
    plt.rcParams.update({
        'font.family': 'sans-serif',
        'font.sans-serif': ['Helvetica', 'Arial'],
        'font.size': 7,
        'axes.labelsize': 7,
        'axes.titlesize': 7,
        'xtick.labelsize': 6,
        'ytick.labelsize': 6,
        'legend.fontsize': 6,
        'figure.titlesize': 8,
    })
```

---

## Labeling Conventions

### Figure Numbering
- Sequential: Figure 1, Figure 2, Figure 3, etc.
- All figures must be cited in the text in order

### Panel Labels
- **Lowercase bold letters**: a, b, c, d, ...
- Font size: **8 pt bold**
- Position: top-left corner of each panel

### Axes and Legends
- Include **units in parentheses** on all axes
- Scale bars must be on **separate layers** (not flattened into the image)
- Figure legends placed on a separate manuscript page after References

### Example Panel Labeling

```python
import matplotlib.pyplot as plt
import string

def add_nature_panel_labels(fig, axes):
    """Add Nature-style lowercase bold panel labels."""
    if not hasattr(axes, '__iter__'):
        axes = [axes]

    for i, ax in enumerate(axes):
        label = string.ascii_lowercase[i]
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

### Prohibited
- Flattening scale bars into the image layer
- Outlining text (must remain editable)
- Adding gridlines, patterns, or drop shadows
- Using colored text in graphs
- Publishing copyrighted images without permission

### Permitted (with transparency)
- Linear brightness/contrast adjustments applied **uniformly to the entire image**
- Color balance corrections applied to the **whole image**

### Best Practices
- Keep scale bars on separate layers for editability
- Avoid busy backgrounds behind text
- Remove superfluous decorative elements
- Obtain permissions for all copyrighted figures

---

## Python Quick Start: Full Validation

```python
from PIL import Image
import os

def validate_nature_figure(image_path):
    """Full validation of a figure against Nature requirements."""
    img = Image.open(image_path)
    issues = []

    # 1. Resolution check
    dpi = img.info.get('dpi', (72, 72))
    if dpi[0] < 300 or dpi[1] < 300:
        issues.append(f"Resolution too low: {dpi[0]}x{dpi[1]} DPI (need 300+)")

    # 2. Color mode check
    if img.mode == 'CMYK':
        issues.append("Color mode is CMYK; RGB is recommended for Nature")
    elif img.mode not in ('RGB', 'RGBA'):
        issues.append(f"Unexpected color mode: {img.mode}; use RGB")

    # 3. File size check
    size_mb = os.path.getsize(image_path) / (1024 * 1024)
    if size_mb > 10:
        issues.append(f"File size {size_mb:.1f} MB exceeds 10 MB limit")

    # 4. Format check
    fmt = img.format
    accepted = ['TIFF', 'JPEG', 'PNG', 'EPS', 'PDF']
    if fmt and fmt.upper() not in accepted:
        issues.append(f"Format '{fmt}' may not be accepted; prefer TIFF or JPEG")

    # Report
    print(f"=== Nature Figure Validation: {os.path.basename(image_path)} ===")
    print(f"Dimensions: {img.size[0]} x {img.size[1]} px")
    print(f"DPI: {dpi[0]} x {dpi[1]}")
    print(f"Color mode: {img.mode}")
    print(f"Format: {fmt}")
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

### Resolution and DPI

DPI (dots per inch) measures print resolution. Nature requires 300+ DPI at maximum print size. Upsampling (artificially increasing resolution in software) does not improve image quality and introduces interpolation artifacts. Always capture or export images at native high resolution.

### Vector vs Raster Formats

Vector formats (AI, EPS, PDF) store images as mathematical paths and scale without quality loss — ideal for graphs, schematics, and line art. Raster formats (TIFF, JPEG, PSD) store pixel grids and degrade when enlarged — appropriate for photographs and micrographs. Nature prefers vector for line drawings and raster for photographic content.

### Image Integrity

Nature enforces strict image integrity policies aligned with the Committee on Publication Ethics (COPE) guidelines. All adjustments must be applied uniformly to the entire image. Selective enhancement of specific regions (e.g., adjusting brightness on one gel lane) is considered data manipulation and grounds for rejection or retraction.

## Decision Framework

```
What type of figure are you preparing?
├── Graph, schematic, or diagram → Vector format (AI, EPS, PDF)
│   ├── Created in Illustrator → Export as AI or EPS
│   └── Created in Python/R → Export as PDF or EPS
├── Photograph or micrograph → Raster format (TIFF, PSD, JPEG)
│   ├── Need highest quality → TIFF at 450+ DPI
│   └── File size constrained → JPEG at 300+ DPI
└── Multi-panel composite → Single assembled file
    ├── Mixed vector + raster → Assemble in Illustrator, export as AI/PDF
    └── All raster panels → Assemble in Photoshop, export as TIFF
```

| Scenario | Recommended Format | Resolution | Notes |
|---|---|---|---|
| Bar chart or line graph | AI, EPS, PDF | Vector (resolution-independent) | Keep text editable |
| Fluorescence micrograph | TIFF | 450+ DPI | RGB mode, colorblind-safe palette |
| Western blot image | TIFF | 300+ DPI | No selective adjustments |
| Flow chart or pathway | AI, EPS | Vector | Use Helvetica/Arial fonts |
| Extended Data figure | JPEG | 300+ DPI | Same standards as main figures |

## Best Practices

1. **Export at native resolution**: Always capture or generate images at the target resolution (300+ DPI). Never upsample low-resolution images in Photoshop or similar tools
2. **Use colorblind-friendly palettes**: Nature strongly recommends accessible color schemes. Avoid red-green combinations; use blue-orange or include pattern/shape differentiation
3. **Keep text editable in vector files**: Do not outline or rasterize text in AI/EPS files. Nature's production team may need to edit fonts during typesetting
4. **Assemble multi-panel figures before upload**: Combine all panels (a, b, c, etc.) into a single image file. Individual panel uploads will be rejected
5. **Maintain separate layers for scale bars**: Scale bars must remain on a separate layer from the image data so they can be repositioned during production
6. **Apply adjustments uniformly**: Any brightness, contrast, or color correction must be applied to the entire image, not selectively to specific regions
7. **Retain original unprocessed data**: Editors or reviewers may request raw image files at any stage of review or post-publication

## Common Pitfalls

1. **Upsampling low-resolution images**: Artificially increasing DPI in image software does not add real detail and introduces blurring artifacts
   - *How to avoid*: Re-export from the original source (microscope, plotting software) at 300+ DPI natively
2. **Submitting individual panels instead of assembled figures**: Nature requires multi-panel figures as a single composite file
   - *How to avoid*: Assemble all panels in Illustrator or Photoshop before uploading; use lowercase bold labels (a, b, c)
3. **Using uppercase panel labels**: Nature uses lowercase bold (a, b, c), unlike many other journals that use uppercase
   - *How to avoid*: Double-check the journal's labeling convention; Nature specifically requires lowercase
4. **Outlining text in vector files**: Converting text to outlines makes it uneditable, which Nature prohibits
   - *How to avoid*: Embed fonts as TrueType 2 or 42 instead of converting to outlines
5. **Submitting in CMYK color mode**: While accepted, CMYK narrows the color gamut and may misrepresent fluorescence data online
   - *How to avoid*: Submit in RGB; Nature handles CMYK conversion for print internally
6. **Exceeding the 10 MB file size limit**: Large TIFF files often exceed this threshold
   - *How to avoid*: Use LZW compression for TIFF files or convert to high-quality JPEG (300+ DPI)

---

## Pre-Submission Checklist

Before submitting figures to Nature, verify:

- [ ] Resolution is at least 300 DPI (450+ DPI preferred)
- [ ] File format is AI, EPS, TIFF, PSD, or high-quality JPEG
- [ ] Each file is under 10 MB
- [ ] Multi-panel figures assembled as a single image file
- [ ] Color mode is RGB (not CMYK)
- [ ] Colorblind-accessible palette used
- [ ] Fonts are Helvetica or Arial, 5-7 pt body, 8 pt bold panel labels
- [ ] Panel labels are lowercase bold (a, b, c)
- [ ] Text is NOT outlined (remains editable)
- [ ] Fonts embedded as TrueType 2 or 42
- [ ] Scale bars on separate layers (not flattened)
- [ ] No gridlines, patterns, or drop shadows
- [ ] Axes include units in parentheses
- [ ] All image adjustments applied uniformly to entire image
- [ ] Original unprocessed data retained for editor/reviewer requests
- [ ] Copyright permissions obtained for any third-party images

---

## References

- Nature Formatting Guide: https://www.nature.com/nature/for-authors/formatting-guide
- Nature Final Submission: https://www.nature.com/nature/for-authors/final-submission
- Nature Research Figure Guide: https://research-figure-guide.nature.com/figures/preparing-figures-our-specifications/
