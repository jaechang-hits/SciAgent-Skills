---
name: nejm-figure-guide
description: "Figure and image preparation guide for the New England Journal of Medicine (NEJM). Covers resolution (300-1200 DPI), editable vector formats (AI, EPS, SVG), in-house medical illustration policy, and strict image integrity requirements."
license: CC-BY-4.0
compatibility: Python 3.10+, Pillow, Matplotlib
metadata:
  authors: HITS
  version: "1.0"
---

# NEJM Figure Preparation Guide

## Overview

This guide provides the complete specifications for preparing figures for submission to the **New England Journal of Medicine (NEJM)**. A unique feature of NEJM is that **medical illustrations are created by NEJM's in-house illustrators** working directly with authors — authors should NOT submit finished medical illustrations due to copyright considerations.

**Official reference**: https://www.nejm.org/author-center/new-manuscripts

---

## Resolution Requirements

| Image Type | Minimum Resolution | Notes |
|---|---|---|
| Black-and-white line art | **1,200 DPI** | Highest requirement |
| Photographic / halftone images | **300 DPI** | Standard for photographs |
| Peer review stage | Lower resolution acceptable | High-res required for final publication |

```python
from PIL import Image

def check_nejm_resolution(image_path, image_type='photo', stage='final'):
    """Check if image meets NEJM resolution requirements.

    Args:
        image_type: 'lineart' (1200 DPI) or 'photo' (300 DPI)
        stage: 'review' (lower OK) or 'final' (strict requirements)
    """
    min_dpi = {'lineart': 1200, 'photo': 300}
    required = min_dpi.get(image_type, 300)

    if stage == 'review':
        print("NOTE: Lower resolution acceptable for peer review")
        required = 150  # relaxed for review

    img = Image.open(image_path)
    dpi = img.info.get('dpi', (72, 72))

    print(f"Stage: {stage} | Type: {image_type}")
    print(f"Required: {required} DPI | Actual: {dpi[0]} DPI")
    passed = dpi[0] >= required
    print("PASS" if passed else "FAIL")

    return passed
```

---

## File Format

| Figure Type | Preferred Format | Notes |
|---|---|---|
| Data visualizations (graphs, plots, diagrams) | **AI, EPS, SVG** | Editable vector files preferred |
| Photographic images | **TIFF** | High-resolution raster |
| Medical illustrations | **Do NOT submit** | NEJM illustrators create these |

### Submission Options
- Figures can be inserted in text files (preferred) or uploaded separately

### Medical Illustration Policy
**IMPORTANT**: NEJM's in-house medical illustrators will work directly with authors to create medical illustrations. Authors should NOT submit finished illustrations due to copyright considerations. The journal retains copyright on illustrations created by their team.

---

## Figure Size and Dimensions

NEJM does not publish detailed size specifications in their public guidelines. General best practices:

- Size figures appropriately for the intended column layout
- Ensure all text is legible at final print size
- Follow standard medical journal conventions

---

## Color Mode

- No explicit RGB/CMYK mandate in published guidelines
- Follow standard practice: submit in RGB for online; journal handles print conversion

---

## Font Requirements

| Element | Specification |
|---|---|
| Preferred style | **Sans-serif** |
| Historical font | Univers (NEJM house font) |
| Alternatives | Helvetica, Arial |

- Ensure all text is legible at final reduction size

```python
import matplotlib.pyplot as plt

def set_nejm_fonts():
    """Configure Matplotlib for NEJM figure fonts."""
    plt.rcParams.update({
        'font.family': 'sans-serif',
        'font.sans-serif': ['Univers', 'Helvetica', 'Arial'],
        'font.size': 8,
        'axes.labelsize': 8,
        'axes.titlesize': 8,
        'xtick.labelsize': 7,
        'ytick.labelsize': 7,
        'legend.fontsize': 7,
    })
```

---

## Labeling Conventions

### Images in Clinical Medicine
- Title: maximum **8 words**
- Legend: maximum **150 words**

### Patient Privacy
- **All patient-identifying information must be removed** from images
- This includes faces, names, medical record numbers, and any other identifiable information

```python
def check_clinical_image_text(title, legend):
    """Validate text limits for NEJM Images in Clinical Medicine."""
    title_words = len(title.split())
    legend_words = len(legend.split())

    issues = []
    if title_words > 8:
        issues.append(f"Title has {title_words} words (max 8)")
    if legend_words > 150:
        issues.append(f"Legend has {legend_words} words (max 150)")

    if issues:
        for issue in issues:
            print(f"ISSUE: {issue}")
    else:
        print(f"PASS: Title ({title_words} words), Legend ({legend_words} words)")

    return len(issues) == 0
```

---

## Image Integrity and Manipulation Policy

### PROHIBITED
- Enhancing, obscuring, moving, removing, or introducing any specific feature within an image

### REQUIRED
- Brightness, color, and contrast adjustments must be applied **uniformly to the entire image**
- Adjustments must not misrepresent any features of the original image

### Best Practices
- Maintain original unprocessed image files
- Document all processing steps
- Be prepared to provide raw data upon request

---

## Python Quick Start: Full Validation

```python
from PIL import Image
import os

def validate_nejm_figure(image_path, image_type='photo', stage='final'):
    """Full validation of a figure against NEJM requirements."""
    img = Image.open(image_path)
    issues = []

    # 1. Resolution check
    min_dpi = {'lineart': 1200, 'photo': 300}
    required = min_dpi.get(image_type, 300)
    if stage == 'review':
        required = 150
    dpi = img.info.get('dpi', (72, 72))
    if dpi[0] < required:
        issues.append(f"Resolution {dpi[0]} DPI below {required} DPI for {image_type} ({stage})")

    # 2. Color mode
    if img.mode not in ('RGB', 'RGBA', 'L'):
        issues.append(f"Color mode {img.mode} may not be ideal; use RGB or Grayscale")

    # 3. Format check
    fmt = img.format
    vector_preferred = image_type != 'photo'
    if vector_preferred and fmt and fmt.upper() in ('JPEG', 'PNG'):
        issues.append(f"Data visualizations: prefer vector format (AI, EPS, SVG) over {fmt}")

    # Report
    print(f"=== NEJM Figure Validation ({stage}) ===")
    print(f"Dimensions: {img.size[0]} x {img.size[1]} px")
    print(f"DPI: {dpi[0]} x {dpi[1]}")
    print(f"Color mode: {img.mode}")

    if issues:
        print(f"\nISSUES FOUND ({len(issues)}):")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("\nAll checks PASSED")

    print("\nREMINDER: Do NOT submit finished medical illustrations (NEJM creates these)")
    print("REMINDER: Remove ALL patient-identifying information from images")

    return len(issues) == 0
```

---

## Pre-Submission Checklist

Before submitting figures to NEJM, verify:

- [ ] Line art at 1,200+ DPI
- [ ] Photographs at 300+ DPI (lower OK for peer review only)
- [ ] Data visualizations in editable vector format (AI, EPS, SVG)
- [ ] Photographs in TIFF format
- [ ] Medical illustrations: NOT submitted (NEJM creates these in-house)
- [ ] Sans-serif font used (Univers, Helvetica, or Arial)
- [ ] All text legible at final print size
- [ ] Images in Clinical Medicine: title ≤ 8 words, legend ≤ 150 words
- [ ] **All patient-identifying information removed**
- [ ] Adjustments applied uniformly to entire image
- [ ] No selective enhancement of image features
- [ ] Original unprocessed data retained

---

## References

- NEJM Author Center: https://www.nejm.org/author-center/new-manuscripts
- NEJM Technical Guidelines for Figures: https://www.nejm.org/pb-assets/pdfs/Technical-Guidelines-for-Figures.pdf
