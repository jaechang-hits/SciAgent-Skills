---
name: pnas-figure-guide
description: "Figure and image preparation guide for PNAS. Covers resolution (300-1000 PPI by type), file formats (TIFF, EPS, PDF), strict RGB-only color mode, Arial/Helvetica fonts, italicized uppercase panel labels, and automated image screening."
license: CC-BY-4.0
compatibility: Python 3.10+, Pillow, Matplotlib
metadata:
  authors: HITS
  version: "1.0"
---

# PNAS Figure Preparation Guide

## Overview

This guide provides the complete specifications for preparing figures for submission to **PNAS** (Proceedings of the National Academy of Sciences). PNAS is notable for its **strict RGB-only policy** (CMYK submissions are returned), **italicized uppercase panel labels**, and **automated image screening software**.

**Official reference**: https://www.pnas.org/author-center/submitting-your-manuscript

---

## Resolution Requirements

| Image Type | Minimum Resolution | Notes |
|---|---|---|
| Halftones (color/grayscale photos) | **300 PPI** | At publication size |
| Combination artwork (MS Office) | **600-900 DPI** | Mixed text and images |
| Line art (bitmap text/thin lines) | **1,000 PPI** | At publication size |
| LaTeX figures | — | High-quality PDF or EPS |

```python
from PIL import Image

def check_pnas_resolution(image_path, image_type='halftone'):
    """Check if image meets PNAS resolution requirements.

    Args:
        image_type: 'halftone' (300), 'combination' (600), or 'lineart' (1000)
    """
    min_ppi = {'halftone': 300, 'combination': 600, 'lineart': 1000}
    required = min_ppi.get(image_type, 300)

    img = Image.open(image_path)
    dpi = img.info.get('dpi', (72, 72))

    print(f"Type: {image_type} | Required: {required} PPI | Actual: {dpi[0]} PPI")

    if dpi[0] >= required:
        print("PASS")
    else:
        print(f"FAIL: Need {required} PPI minimum")

    return dpi[0] >= required
```

---

## File Format

| Format | Accepted |
|---|---|
| **TIFF** | Yes (preferred for raster) |
| **EPS** | Yes (fonts must be embedded) |
| **PDF** | Yes (fonts must be embedded) |
| **PPT** | Yes |
| **3D images** | PRC or U3D with 2D representation (TIFF/EPS/PDF) |

### Submission Stages
- **Initial submission**: Format-neutral — single PDF containing full manuscript, figures, and SI. High-resolution files not required.
- **Production phase**: Separate high-resolution figure uploads required.

---

## Figure Size and Dimensions

**IMPORTANT**: Provide images at **final publication size**, not full-page size.

| Layout | Width |
|---|---|
| 1 column | **8.7 cm** (3.43 in) |
| 1.5 columns | **11.4 cm** (4.5 in / 27 picas) |
| 2 columns | **17.8 cm** (7.0 in / 42.125 picas) |
| Maximum height | **22.5 cm** (9 in / 54 picas) |

```python
import matplotlib.pyplot as plt

PNAS_WIDTHS = {
    'single':  8.7 / 2.54,   # 3.43 inches
    'middle':  11.4 / 2.54,  # 4.49 inches
    'double':  17.8 / 2.54,  # 7.01 inches
}
PNAS_MAX_HEIGHT = 22.5 / 2.54  # 8.86 inches

def create_pnas_figure(layout='single', aspect_ratio=0.75):
    """Create a Matplotlib figure sized for PNAS."""
    width = PNAS_WIDTHS[layout]
    height = min(width * aspect_ratio, PNAS_MAX_HEIGHT)

    fig, ax = plt.subplots(figsize=(width, height))
    fig.set_dpi(300)
    return fig, ax
```

---

## Color Mode

### CRITICAL: RGB Only

- **Submit in RGB color mode ONLY**
- **CMYK submissions will be returned for correction**
- Tag RGB images with originating ICC profile for accurate RGB-to-CMYK conversion
- PNAS manages print conversion using calibrated profiles

```python
from PIL import Image

def validate_pnas_color_mode(image_path):
    """PNAS strictly requires RGB. CMYK will be rejected."""
    img = Image.open(image_path)

    if img.mode == 'CMYK':
        print("REJECTED: PNAS does not accept CMYK images")
        print("Action: Convert to RGB before submission")
        return False
    elif img.mode in ('RGB', 'RGBA'):
        print("PASS: Image is in RGB mode")
        return True
    else:
        print(f"WARNING: Unexpected mode '{img.mode}'; convert to RGB")
        return False

def convert_to_rgb(image_path, output_path):
    """Convert any image to RGB for PNAS submission."""
    img = Image.open(image_path)
    if img.mode != 'RGB':
        img = img.convert('RGB')
        print(f"Converted from {img.mode} to RGB")
    img.save(output_path)
```

---

## Font Requirements

| Element | Specification |
|---|---|
| Approved fonts | **Arial, Helvetica, Times, Symbol, Mathematical Pi, European Pi** |
| Font size | **6-8 pt** at final publication size (minimum 2 mm when printed) |
| Consistency | Same font for all figures in manuscript |
| Text type | **Vector text** preferred (scales cleanly) |
| Embedding | **All fonts must be embedded** in EPS and PDF files |

### Panel Labels (PNAS-Specific Convention)
- **Italicized uppercase letters**: *A*, *B*, *C*, *D*, ...
- This is a distinctive PNAS convention — different from most other journals

```python
import matplotlib.pyplot as plt

def set_pnas_fonts():
    """Configure Matplotlib for PNAS figure fonts."""
    plt.rcParams.update({
        'font.family': 'sans-serif',
        'font.sans-serif': ['Arial', 'Helvetica'],
        'font.size': 7,
        'axes.labelsize': 7,
        'axes.titlesize': 7,
        'xtick.labelsize': 6,
        'ytick.labelsize': 6,
        'legend.fontsize': 6,
    })

def add_pnas_panel_labels(fig, axes):
    """Add PNAS-style italicized uppercase panel labels."""
    import string
    if not hasattr(axes, '__iter__'):
        axes = [axes]

    for i, ax in enumerate(axes):
        label = string.ascii_uppercase[i]
        ax.text(-0.1, 1.1, label,
                transform=ax.transAxes,
                fontsize=8,
                fontstyle='italic',
                fontweight='bold',
                va='top',
                ha='right',
                fontfamily='Arial')
```

---

## Labeling Conventions

- Panel labels: **Italicized uppercase** (*A*, *B*, *C*)
- All text, numbers, letters, symbols: **6-12 pt (2-6 mm)** after reduction
- Text sizing must be **consistent within each graphic**
- Labels should match body text font conventions

---

## Image Integrity and Manipulation Policy

### PROHIBITED
- Enhancing, obscuring, moving, removing, or introducing any specific feature within an image

### PERMITTED
- Brightness, contrast, color balance adjustments applied to the **whole image** without obscuring or eliminating original information (including backgrounds)

### REQUIRED
- When combining images from multiple sources: make **explicit** by arrangement and figure legend text
- Name processing software in Methods section
- Indicate all manipulations in figure legends
- Original data must be available on request (missing data may result in rejection)

### Automated Screening
**PNAS uses screening software** to detect:
- Cloning and pasting artifacts
- Suspicious contrast adjustments that obscure data
- Inconsistent background pixelation
- Other signs of inappropriate image manipulation

### Accessibility
- Beginning with Volume 123, PNAS includes **alt text** for all journal figures to improve digital accessibility

---

## Python Quick Start: Full Validation

```python
from PIL import Image
import os

def validate_pnas_figure(image_path, image_type='halftone', layout='single'):
    """Full validation of a figure against PNAS requirements."""
    img = Image.open(image_path)
    issues = []

    # 1. Resolution check
    min_ppi = {'halftone': 300, 'combination': 600, 'lineart': 1000}
    required = min_ppi.get(image_type, 300)
    dpi = img.info.get('dpi', (72, 72))
    if dpi[0] < required:
        issues.append(f"Resolution {dpi[0]} PPI below {required} PPI for {image_type}")

    # 2. STRICT RGB check
    if img.mode == 'CMYK':
        issues.append("REJECTED: CMYK not accepted. Must convert to RGB")
    elif img.mode not in ('RGB', 'RGBA'):
        issues.append(f"Color mode '{img.mode}' not standard; use RGB")

    # 3. Dimension check at publication size
    widths_cm = {'single': 8.7, 'middle': 11.4, 'double': 17.8}
    max_height_cm = 22.5
    if layout in widths_cm and dpi[0] > 0:
        actual_w_cm = (img.size[0] / dpi[0]) * 2.54
        actual_h_cm = (img.size[1] / dpi[1]) * 2.54
        target_w = widths_cm[layout]
        if actual_h_cm > max_height_cm:
            issues.append(f"Height {actual_h_cm:.1f} cm exceeds max {max_height_cm} cm")
        print(f"Print size: {actual_w_cm:.1f} x {actual_h_cm:.1f} cm (target width: {target_w} cm)")

    # 4. Format check
    fmt = img.format
    accepted = ['TIFF', 'EPS', 'PDF', 'PNG', 'JPEG']
    if fmt and fmt.upper() not in accepted:
        issues.append(f"Format '{fmt}' not in preferred list (TIFF, EPS, PDF)")

    # Report
    print(f"=== PNAS Figure Validation ===")
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

### Strict RGB-Only Policy

PNAS enforces one of the strictest color mode policies in scientific publishing. CMYK submissions are returned without review. Authors must submit all figures in RGB color mode and tag images with their originating ICC profile to ensure accurate RGB-to-CMYK conversion by the journal's production team.

### Three-Tier Resolution System

PNAS uses PPI (pixels per inch) rather than DPI and defines three tiers: 300 PPI for halftones (photographs), 600-900 DPI for combination artwork (mixed text and images from MS Office), and 1,000 PPI for line art (bitmap text and thin lines). Images must meet these thresholds at final publication size.

### Automated Image Screening

PNAS employs screening software that automatically detects signs of inappropriate image manipulation including cloning/pasting artifacts, suspicious contrast adjustments, and inconsistent background pixelation. This automated screening supplements editorial review and can flag issues that manual inspection might miss.

## Decision Framework

```
What color mode is your image?
├── CMYK → REJECTED (convert to RGB before submission)
├── RGB → Accepted
│   └── ICC profile tagged? → Recommended for accurate print conversion
└── Grayscale → Convert to RGB

What type of image?
├── Halftone (photo/micrograph) → 300 PPI minimum
├── Combination (MS Office mixed) → 600-900 DPI
├── Line art (bitmap text/lines) → 1,000 PPI
└── LaTeX figure → High-quality PDF or EPS

What submission stage?
├── Initial → Single PDF with all content (format-neutral)
└── Production → Separate high-resolution figure uploads
```

| Scenario | Format | Resolution | Color Mode |
|---|---|---|---|
| Micrograph | TIFF | 300 PPI | RGB (ICC tagged) |
| PowerPoint chart | PPT or TIFF | 600-900 DPI | RGB |
| Schematic diagram | EPS or PDF | Vector or 1,000 PPI | RGB |
| Gel/blot image | TIFF | 300 PPI | RGB |
| 3D molecular model | PRC/U3D + TIFF | 300 PPI (2D fallback) | RGB |

## Best Practices

1. **Convert CMYK to RGB before submission**: PNAS returns CMYK files without review. Always verify color mode before upload using image metadata tools
2. **Tag RGB images with ICC profiles**: Embedding the originating ICC profile ensures accurate color conversion during PNAS's print production pipeline
3. **Provide images at final publication size**: PNAS requires figures sized to column widths (8.7/11.4/17.8 cm). Do not submit oversized images expecting the journal to resize
4. **Use italicized uppercase panel labels**: PNAS uses a distinctive convention — *A*, *B*, *C* (italic, uppercase) — that differs from most other journals
5. **Embed all fonts in EPS and PDF files**: Missing fonts cause rendering failures. Use vector text rather than rasterized text for clean scaling
6. **Prepare alt text for accessibility**: Since Volume 123, PNAS includes alt text for all figures. Drafting alt text during figure preparation saves revision time
7. **Name processing software in Methods**: PNAS requires explicit mention of all image processing software used, not just a general description of adjustments

## Common Pitfalls

1. **Submitting figures in CMYK color mode**: PNAS strictly rejects CMYK. This is the most common preventable rejection reason for figures
   - *How to avoid*: Run the color mode validation script on every figure before submission; convert CMYK to RGB
2. **Using 300 PPI for line art**: Line art with bitmap text requires 1,000 PPI. At 300 PPI, thin lines and small text appear jagged
   - *How to avoid*: Classify each figure by type (halftone vs. line art vs. combination) and apply the correct resolution tier
3. **Submitting figures larger than publication size**: PNAS requires images at final size, not oversized. Oversized figures may be rescaled, degrading quality
   - *How to avoid*: Set canvas size to the target column width before exporting
4. **Using non-italic panel labels**: PNAS's italic uppercase convention (*A*, *B*, *C*) is unique. Non-italic labels signal unfamiliarity with the journal
   - *How to avoid*: Use `fontstyle='italic'` in matplotlib or the italic setting in Illustrator for panel labels
5. **Omitting multi-source composite indicators**: When combining images from different experiments, PNAS requires explicit visual and textual indication
   - *How to avoid*: Use clear borders or spacing between composite elements and describe the composition in the figure legend

## Pre-Submission Checklist

Before submitting figures to PNAS, verify:

- [ ] Halftones at 300+ PPI; line art at 1,000+ PPI
- [ ] File format is TIFF, EPS, or PDF
- [ ] **Color mode is RGB** (NOT CMYK — will be rejected)
- [ ] ICC profile tagged for accurate color conversion
- [ ] Figure width matches column layout (8.7 / 11.4 / 17.8 cm)
- [ ] Figure height does not exceed 22.5 cm
- [ ] Images provided at **final publication size**
- [ ] Font is Arial, Helvetica, or Times at 6-8 pt
- [ ] All fonts embedded in EPS/PDF
- [ ] Panel labels are **italicized uppercase** (*A*, *B*, *C*)
- [ ] Text sizing consistent within each figure
- [ ] All adjustments applied to entire image uniformly
- [ ] Multi-source composites explicitly indicated in legend
- [ ] Processing software named in Methods
- [ ] Original unprocessed data available for review
- [ ] Alt text prepared for accessibility

---

## References

- PNAS Submission Guidelines: https://www.pnas.org/author-center/submitting-your-manuscript
- PNAS Digital Art Guidelines: https://www.pnas.org/pb-assets/authors/digitalart.pdf
- PNAS Editorial Policies: https://www.pnas.org/author-center/editorial-and-journal-policies
