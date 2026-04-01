---
name: elife-figure-guide
description: "Figure and image preparation guide for eLife. Covers file formats (TIFF, EPS, PDF), striking image requirements (1800x900 px), figure supplement naming conventions, and routine image screening policy where selective enhancement is treated as misconduct."
license: CC-BY-4.0
compatibility: Python 3.10+, Pillow, Matplotlib
metadata:
  authors: HITS
  version: "1.0"
---

# eLife Figure Preparation Guide

## Overview

This guide provides the complete specifications for preparing figures for submission to **eLife**. eLife is known for its open-access model, **figure supplement system**, **striking image requirements**, and a **strict image screening policy** where selective enhancement of scientific images is treated as research misconduct.

**Official reference**: https://elife-rp.msubmit.net/html/elife-rp_author_instructions.html

---

## Resolution Requirements

| Image Type | Minimum Resolution |
|---|---|
| Striking images | **1800 x 900 pixels** minimum |
| Regular figures | No strict DPI mandate (standard 300 DPI recommended) |

```python
from PIL import Image

def check_elife_resolution(image_path, is_striking=False):
    """Check if image meets eLife resolution requirements.

    Args:
        is_striking: True for striking/graphical abstract images
    """
    img = Image.open(image_path)
    w, h = img.size
    dpi = img.info.get('dpi', (72, 72))

    print(f"Dimensions: {w} x {h} px")
    print(f"DPI: {dpi[0]} x {dpi[1]}")

    if is_striking:
        if w >= 1800 and h >= 900:
            print("PASS: Meets striking image minimum (1800x900 px)")
            return True
        else:
            print(f"FAIL: Striking image needs 1800x900 px, got {w}x{h}")
            return False
    else:
        if dpi[0] >= 300:
            print("PASS: Resolution meets standard (300+ DPI)")
        else:
            print(f"NOTE: DPI is {dpi[0]}; 300+ DPI recommended")
        return True
```

---

## File Format

### Regular Figures

| Format | Accepted |
|---|---|
| **TIFF** | Yes |
| **EPS** | Yes |
| **PDF** | Yes |
| **JPEG / JPG** | Yes |
| **GIF** | Yes |
| **PS** (PostScript) | Yes |
| **RTF** | Yes |
| **Microsoft Excel** | Yes (for data-based figures) |
| **CorelDraw** | Yes |

### Striking Images

| Format | Recommended |
|---|---|
| **PNG** | Yes (preferred) |
| **TIFF** | Yes |
| **JPEG** | Yes |

---

## Figure Size and Dimensions

### Striking Images (Graphical Abstract)
- Minimum: **1800 x 900 pixels**
- Format: **Landscape orientation**
- Composed of **1-2 panels maximum**
- **No labels or text** should be included

### Regular Figures
- Each figure uploaded as an **individual file**
- No specific column width requirements published

---

## Color Mode

- No explicit RGB/CMYK mandate in published guidelines
- Follow standard practice: RGB for digital submission

---

## Font Requirements

### Striking Images
- **No labels or text** should be included in striking images

### Regular Figures
- No strict font specifications published
- Follow standard scientific figure conventions (sans-serif, 6-8 pt)

```python
import matplotlib.pyplot as plt

def set_elife_fonts():
    """Configure Matplotlib with standard settings for eLife."""
    plt.rcParams.update({
        'font.family': 'sans-serif',
        'font.sans-serif': ['Helvetica', 'Arial'],
        'font.size': 7,
        'axes.labelsize': 7,
        'axes.titlesize': 8,
        'xtick.labelsize': 6,
        'ytick.labelsize': 6,
        'legend.fontsize': 6,
    })
```

---

## Labeling Conventions

### Figure Supplements (eLife-Specific System)

eLife uses a unique **figure supplement** system instead of traditional supplementary figures:

- Format: `Figure 1--Figure Supplement 1`, `Figure 1--Figure Supplement 2`, etc.
- Each supplement should have a **short title** and an optional legend
- Supplements are linked to their parent figure in the publication

### Striking Images
- Must NOT contain any labels or text
- Limited to 1-2 panels

```python
def generate_elife_supplement_names(main_figure_num, n_supplements):
    """Generate eLife figure supplement naming.

    Args:
        main_figure_num: The main figure number (1, 2, 3, ...)
        n_supplements: Number of supplements for this figure

    Returns:
        List of supplement name strings
    """
    names = []
    for i in range(1, n_supplements + 1):
        names.append(f"Figure {main_figure_num}--Figure Supplement {i}")
    return names

# Example
supplements = generate_elife_supplement_names(3, 4)
for s in supplements:
    print(s)
# Output:
# Figure 3--Figure Supplement 1
# Figure 3--Figure Supplement 2
# Figure 3--Figure Supplement 3
# Figure 3--Figure Supplement 4
```

---

## Image Integrity and Manipulation Policy

### CRITICAL: eLife Screens Images Routinely

eLife **routinely screens submitted images** for inappropriate digital processing. This is not a random check — it is a systematic process.

### PROHIBITED
- Enhancing, obscuring, moving, removing, or introducing any specific feature within an image
- **Selective enhancement constitutes research misconduct**
  - Example: Adjusting the intensity of a single band in a blot = **misconduct**

### PERMITTED
- Brightness, contrast, and color balance adjustments applied **equally across the entire image**
- Adjustments must NOT obscure or eliminate information present in the original

### Consequences
- Inappropriate image manipulation may result in:
  - Manuscript rejection
  - Investigation by the author's institution
  - Public correction or retraction of published articles

---

## Python Quick Start: Full Validation

```python
from PIL import Image
import os

def validate_elife_figure(image_path, is_striking=False):
    """Full validation of a figure against eLife requirements."""
    img = Image.open(image_path)
    issues = []
    w, h = img.size

    # 1. Striking image checks
    if is_striking:
        if w < 1800 or h < 900:
            issues.append(f"Striking image: {w}x{h} px below 1800x900 minimum")
        if w < h:
            issues.append("Striking image should be landscape orientation")

    # 2. Resolution check (standard recommendation)
    dpi = img.info.get('dpi', (72, 72))
    if not is_striking and dpi[0] < 300:
        issues.append(f"Resolution {dpi[0]} DPI; 300+ DPI recommended")

    # 3. Format check
    fmt = img.format
    accepted = ['TIFF', 'JPEG', 'PNG', 'EPS', 'PDF', 'GIF']
    if fmt and fmt.upper() not in accepted:
        issues.append(f"Format '{fmt}' may not be standard")

    if is_striking:
        striking_formats = ['PNG', 'TIFF', 'JPEG']
        if fmt and fmt.upper() not in striking_formats:
            issues.append(f"Striking image: prefer PNG, TIFF, or JPEG (got {fmt})")

    # Report
    print(f"=== eLife Figure Validation {'(Striking)' if is_striking else ''} ===")
    print(f"Dimensions: {w} x {h} px")
    print(f"DPI: {dpi[0]} x {dpi[1]}")
    print(f"Color mode: {img.mode}")
    print(f"Format: {fmt}")

    if issues:
        print(f"\nISSUES FOUND ({len(issues)}):")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("\nAll checks PASSED")

    print("\nWARNING: eLife routinely screens images for manipulation")
    print("Selective enhancement (e.g., single band intensity) = MISCONDUCT")

    return len(issues) == 0
```

---

## Key Concepts

### Figure Supplement System

eLife replaces traditional supplementary figures with a linked figure supplement system. Supplements are named "Figure X--Figure Supplement Y" and are directly associated with their parent figure in the publication. Each supplement requires a short title and optional legend. This system improves discoverability compared to buried supplementary files.

### Striking Image Requirements

eLife requires a striking image (graphical abstract) with specific constraints: minimum 1800 x 900 pixels, landscape orientation, 1-2 panels maximum, and no labels or text. This image appears prominently in article listings and social media. It must be a standalone visual that conveys the paper's main finding.

### Routine Image Screening Policy

eLife routinely screens all submitted images for inappropriate digital processing. This is systematic, not random. Selective enhancement of any part of a scientific image (e.g., adjusting intensity of a single band in a blot) is treated as research misconduct and may result in rejection, institutional investigation, or retraction.

## Decision Framework

```
What type of figure are you preparing?
├── Striking image (graphical abstract)
│   ├── Dimensions: 1800 x 900 px minimum, landscape
│   ├── Format: PNG (preferred), TIFF, or JPEG
│   └── Content: No text, no labels, 1-2 panels max
├── Main figure
│   ├── Standard format: TIFF, EPS, PDF, JPEG
│   └── Upload as individual file
└── Figure supplement
    ├── Naming: "Figure X--Figure Supplement Y"
    ├── Include short title
    └── Same format requirements as main figures
```

| Scenario | Format | Resolution | Notes |
|---|---|---|---|
| Striking image | PNG | 1800 x 900 px minimum | No text or labels |
| Western blot | TIFF | 300+ DPI | Will be screened for manipulation |
| Graph or chart | EPS or PDF | Vector | Individual file upload |
| Micrograph | TIFF | 300+ DPI | Uniform adjustments only |
| Supplementary panel | Same as main | Same as main | Name as "Figure X--Figure Supplement Y" |
| Data from Excel | Excel (.xlsx) | N/A | Accepted for data-based figures |

## Best Practices

1. **Prepare striking images without any text**: eLife strictly prohibits labels or text in striking images. The image must communicate visually without words
2. **Use the figure supplement system correctly**: Name supplements using the exact format "Figure X--Figure Supplement Y" with double hyphens. Include a short descriptive title for each
3. **Apply all adjustments uniformly to entire images**: eLife's screening software detects selective enhancement. Any brightness/contrast change must cover the whole image
4. **Maintain original unprocessed data**: Given eLife's screening policy, having originals available demonstrates integrity and speeds up any inquiries
5. **Submit each figure as an individual file**: Do not combine multiple figures into a single file. Each figure gets its own upload
6. **Use landscape orientation for striking images**: Portrait-oriented striking images do not meet eLife's requirements. Ensure width exceeds height with minimum 1800 x 900 pixels
7. **Describe all processing in Methods**: Document every image processing step (software used, adjustments applied) to preempt screening concerns

## Common Pitfalls

1. **Adding text or labels to striking images**: Any text in the striking image violates eLife requirements
   - *How to avoid*: Create a purely visual composition; remove all annotations, labels, and text overlays
2. **Selectively enhancing parts of scientific images**: Adjusting one region (e.g., a single gel lane) while leaving others unchanged is treated as misconduct
   - *How to avoid*: Apply all brightness, contrast, and color adjustments to the entire image uniformly
3. **Using incorrect figure supplement naming**: Missing the double-hyphen format or incorrect numbering breaks the linking system
   - *How to avoid*: Use the exact format "Figure X--Figure Supplement Y" with double hyphens (--) and sequential numbering
4. **Submitting striking images below minimum size**: Images under 1800 x 900 pixels are rejected
   - *How to avoid*: Check pixel dimensions before upload; create striking images at or above the minimum
5. **Submitting portrait-oriented striking images**: eLife requires landscape orientation for striking images
   - *How to avoid*: Ensure width (1800+ px) exceeds height (900+ px) in the final composition

## Pre-Submission Checklist

Before submitting figures to eLife, verify:

- [ ] Striking image: minimum 1800 x 900 px, landscape, no text/labels
- [ ] Striking image format: PNG, TIFF, or JPEG
- [ ] Regular figures: 300+ DPI recommended
- [ ] File format: TIFF, EPS, PDF, JPEG, or other accepted format
- [ ] Each figure uploaded as individual file
- [ ] Figure supplements named: "Figure X--Figure Supplement Y"
- [ ] Each supplement has a short title
- [ ] **No selective enhancement** of any image region
- [ ] All brightness/contrast adjustments applied to entire image
- [ ] Adjustments do not obscure or eliminate original information
- [ ] Original unprocessed data retained
- [ ] Aware that eLife routinely screens images for manipulation

---

## References

- eLife Author Guide: https://elife-rp.msubmit.net/html/elife-rp_author_instructions.html
- eLife Image Screening Policy: https://elifesciences.org/inside-elife/77dd2808/taking-a-closer-look-screening-of-images
- eLife Submission Guidelines: https://reviewer.elifesciences.org/author-guide/full
