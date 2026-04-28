---
name: cancer-research-figure-guide
description: "Cancer Research (AACR) figures: resolution (300-1200 DPI), formats (EPS/TIFF/AI), hierarchical panel labels (Ai, Aii, Bi), figure/table limits, legend requirements with replicate counts."
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

## Key Concepts

### Hierarchical Panel Labeling

Cancer Research uses a unique three-level labeling system: Level 1 uses capital letters (A, B, C), Level 2 uses Roman numerals (i, ii, iii), and Level 3 uses lowercase letters (a, b, c). The preferred format is Ai, Aii, Bi, Bii — not Aa, Ab, Ba, Bb. No boxes or periods surround panel labels.

### Display Item Limits

Cancer Research strictly limits the total number of display items (figures + tables combined). Research Articles are limited to 7 display items; Letters are limited to 2. Planning figure composition to maximize information density within these limits is essential.

### Replicate Reporting in Legends

A distinctive Cancer Research requirement is that figure legends must include the number of both technical and biological replicates for each experiment shown. This transparency standard supports reproducibility and is checked during editorial review.

## Decision Framework

```
What type of image are you preparing?
├── Line art (diagram, schematic) → 1,200 DPI
├── Halftone (photo, micrograph) → 300 DPI
├── Combination (mixed text + image) → 600-900 DPI
└── Multi-panel figure
    ├── Simple panels (A, B, C) → Standard uppercase labels
    └── Sub-panels needed → Hierarchical: Ai, Aii, Bi, Bii
```

| Scenario | Format | Resolution | Labeling |
|---|---|---|---|
| Western blot with quantification | TIFF + EPS | 300 DPI (blot) + 1,200 DPI (graph) | Ai (blot), Aii (quantification) |
| Tumor growth curves | EPS or AI | Vector or 1,200 DPI | A, B, C (simple panels) |
| Immunohistochemistry panel | TIFF | 300 DPI | Ai, Aii, Bi, Bii (conditions x magnifications) |
| Flow cytometry dot plots | TIFF or PDF | 300 DPI | Hierarchical by condition |
| Kaplan-Meier survival curves | EPS or PDF | Vector | Simple A, B labeling |

## Best Practices

1. **Plan display items early**: With a 7-item limit for Research Articles, plan which results become figures vs. tables vs. supplementary material before drafting
2. **Use hierarchical labels for complex panels**: When a main panel has sub-components (e.g., image + quantification), use the Ai/Aii system rather than separate figure letters
3. **Include replicate counts in every legend**: State both technical and biological replicate numbers for each panel. This is a mandatory requirement, not optional
4. **Avoid boxes and periods on labels**: Cancer Research specifically prohibits decorative elements around panel labels. Use clean, unboxed capital letters
5. **Size figures to fit a single page**: Each figure must fit on one printed page. If content exceeds this, consider splitting into two figures or moving data to supplements
6. **Present figures in sequential order**: Figures should appear adjacent to their legends in the order they are cited in the text

## Common Pitfalls

1. **Exceeding the display item limit**: Submitting more than 7 figures + tables for a Research Article triggers immediate revision request
   - *How to avoid*: Count all display items before submission; consolidate related panels using hierarchical labeling
2. **Using incorrect hierarchical label format**: Writing Aa/Ab instead of Ai/Aii is a common mistake
   - *How to avoid*: Use Roman numerals (i, ii, iii) for Level 2, not lowercase letters
3. **Omitting replicate information from legends**: Missing replicate counts delay review and may require revision
   - *How to avoid*: Add a template line to every legend: "Data represent N=X biological replicates with Y technical replicates each"
4. **Adding boxes or periods to panel labels**: Decorative elements around labels violate Cancer Research formatting rules
   - *How to avoid*: Use plain capital letters without any surrounding decoration
5. **Using 300 DPI for line art**: Line art requires 1,200 DPI — the highest tier. Graphs at 300 DPI will appear jagged in print
   - *How to avoid*: Export vector graphics as EPS/AI, or rasterize at 1,200 DPI minimum

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
- Cancer Research Author Guidelines: https://aacrjournals.org/cancerresearch/pages/prep
