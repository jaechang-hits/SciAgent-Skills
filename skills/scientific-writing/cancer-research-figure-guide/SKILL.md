---
name: cancer-research-figure-guide
description: "Figure and image preparation guide for Cancer Research (AACR). Covers resolution (300-1200 DPI), file formats (EPS, TIFF, AI), hierarchical panel labeling (Ai, Aii, Bi), figure/table limits, and legend requirements including replicate counts."
license: CC-BY-4.0
compatibility: Python 3.10+, Pillow, Matplotlib
metadata:
  authors: HITS
  version: "1.0"
---

# Cancer Research (AACR) Figure Preparation Guide

## Overview

This guide provides the complete specifications for preparing figures for submission to **Cancer Research** and other AACR (American Association for Cancer Research) journals. Cancer Research has a distinctive **hierarchical panel labeling system** (Ai, Aii, Bi, Bii) and strict limits on the total number of display items.

**Official reference**: https://aacrjournals.org/pages/article-style-and-format

---

## Resolution Requirements

| Image Type | Minimum Resolution |
|---|---|
| Line art | **1,200 DPI** |
| Halftone / color images | **300 DPI** |
| Combination artwork | **600-900 DPI** |

```python
from PIL import Image

def check_cancer_res_resolution(image_path, image_type='halftone'):
    """Check if image meets Cancer Research resolution requirements.

    Args:
        image_type: 'lineart' (1200), 'halftone' (300), or 'combination' (600)
    """
    min_dpi = {'lineart': 1200, 'halftone': 300, 'combination': 600}
    required = min_dpi.get(image_type, 300)

    img = Image.open(image_path)
    dpi = img.info.get('dpi', (72, 72))

    print(f"Type: {image_type} | Required: {required} DPI | Actual: {dpi[0]} DPI")
    passed = dpi[0] >= required
    print("PASS" if passed else f"FAIL: Need {required} DPI minimum")

    return passed
```

---

## File Format

| Format | Accepted |
|---|---|
| **EPS** | Yes |
| **TIFF** | Yes |
| **AI** (Adobe Illustrator) | Yes |
| **PSD** (Photoshop) | Yes |
| **PNG** | Yes |
| **PS** (PostScript) | Yes |

---

## Figure Size and Dimensions

### Display Item Limits

| Article Type | Maximum Display Items |
|---|---|
| Research Articles | **7** figures + tables combined |
| Letters | **2** display items total |

- Each figure must fit on a **single printed page**
- Figures should be presented in sequential order adjacent to legends

---

## Color Mode

- No strict CMYK/RGB mandate in published guidelines
- **RGB recommended** for online display
- Follow general best practices for color accessibility

---

## Font Requirements

| Element | Font | Size |
|---|---|---|
| Manuscript body text | Arial, Helvetica, or Times New Roman | 12 pt |
| Figure text | Same fonts | 8-12 pt range |

---

## Labeling Conventions

### Hierarchical Panel Label System (AACR-Specific)

Cancer Research uses a unique **three-level hierarchical labeling** system:

1. **Level 1**: Capital letters — **A, B, C, D**
2. **Level 2**: Roman numerals — **i, ii, iii, iv**
3. **Level 3**: Lowercase letters — **a, b, c, d**

**Preferred format**: `Ai, Aii, Bi, Bii` (NOT `Aa, Ab, Ba, Bb`)

### Labeling Rules
- **No boxes** around panel labels
- **No periods** after panel labels
- Multiple panels should each be labeled and described in the legend

### Legend Requirements
- Figure legends must include the **number of technical AND biological replicates**
- This is a mandatory requirement for Cancer Research

```python
def generate_cancer_res_labels(n_main_panels, sub_panels_per_main=None):
    """Generate Cancer Research hierarchical panel labels.

    Args:
        n_main_panels: Number of main panels (A, B, C, ...)
        sub_panels_per_main: List of sub-panel counts per main panel,
                             or None for no sub-panels

    Returns:
        List of label strings

    Example:
        generate_cancer_res_labels(3, [2, 3, 1])
        # Returns: ['Ai', 'Aii', 'Bi', 'Bii', 'Biii', 'C']
    """
    import string

    labels = []
    roman = ['i', 'ii', 'iii', 'iv', 'v', 'vi', 'vii', 'viii']

    for i in range(n_main_panels):
        main_label = string.ascii_uppercase[i]

        if sub_panels_per_main and sub_panels_per_main[i] > 1:
            for j in range(sub_panels_per_main[i]):
                labels.append(f"{main_label}{roman[j]}")
        else:
            labels.append(main_label)

    return labels
```

### Example Usage

```python
# 3 main panels: A has 2 sub-panels, B has 3, C has 1
labels = generate_cancer_res_labels(3, [2, 3, 1])
print(labels)
# Output: ['Ai', 'Aii', 'Bi', 'Bii', 'Biii', 'C']
```

---

## Image Integrity and Manipulation Policy

Cancer Research follows general **AACR editorial policies** for image integrity:

- All image adjustments should be applied uniformly to the entire image
- No selective enhancement of specific features
- Original unprocessed data should be available upon request
- Processing details should be described in Methods

---

## Python Quick Start: Full Validation

```python
from PIL import Image
import os

def validate_cancer_res_figure(image_path, image_type='halftone'):
    """Full validation of a figure against Cancer Research requirements."""
    img = Image.open(image_path)
    issues = []

    # 1. Resolution check
    min_dpi = {'lineart': 1200, 'halftone': 300, 'combination': 600}
    required = min_dpi.get(image_type, 300)
    dpi = img.info.get('dpi', (72, 72))
    if dpi[0] < required:
        issues.append(f"Resolution {dpi[0]} DPI below {required} DPI for {image_type}")

    # 2. Color mode check
    if img.mode not in ('RGB', 'RGBA'):
        issues.append(f"Color mode is {img.mode}; RGB recommended")

    # 3. Format check
    fmt = img.format
    accepted = ['TIFF', 'EPS', 'PNG', 'JPEG', 'PDF']
    if fmt and fmt.upper() not in accepted:
        issues.append(f"Format '{fmt}' not in standard list")

    # Report
    print(f"=== Cancer Research Figure Validation ===")
    print(f"Dimensions: {img.size[0]} x {img.size[1]} px")
    print(f"DPI: {dpi[0]} x {dpi[1]}")
    print(f"Color mode: {img.mode}")
    print(f"Format: {fmt}")

    if issues:
        print(f"\nISSUES FOUND ({len(issues)}):")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("\nAll checks PASSED")

    print("\nREMINDER: Cancer Research limits Research Articles to 7 figures+tables total")
    print("REMINDER: Legends must include number of technical AND biological replicates")

    return len(issues) == 0
```

---

## Pre-Submission Checklist

Before submitting figures to Cancer Research, verify:

- [ ] Line art at 1,200+ DPI
- [ ] Halftone/color images at 300+ DPI
- [ ] Combination images at 600-900 DPI
- [ ] File format is EPS, TIFF, AI, PSD, or PNG
- [ ] Research Article: maximum 7 figures + tables combined
- [ ] Letters: maximum 2 display items
- [ ] Each figure fits on a single printed page
- [ ] Panel labels use hierarchical format (Ai, Aii, Bi, Bii)
- [ ] No boxes around panel labels
- [ ] No periods after panel labels
- [ ] Font is Arial, Helvetica, or Times New Roman
- [ ] Legend includes number of **technical and biological replicates**
- [ ] Image adjustments applied uniformly
- [ ] Original data available upon request

---

## References

- AACR Article Style and Format: https://aacrjournals.org/pages/article-style-and-format
- AACR Editorial Policies: https://aacrjournals.org/pages/editorial-policies
