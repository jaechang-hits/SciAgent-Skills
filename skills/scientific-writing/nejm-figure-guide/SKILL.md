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

## Key Concepts

### In-House Medical Illustration

NEJM's most distinctive policy is that medical illustrations are created by their in-house illustrators working directly with authors. Authors should NOT submit finished medical illustrations. The journal retains copyright on illustrations created by their team. This applies only to medical illustrations — data visualizations and photographs are author-submitted.

### Two-Stage Resolution Requirements

NEJM accepts lower-resolution figures during peer review to reduce submission friction. However, final publication requires full resolution: 1,200 DPI for line art and 300 DPI for photographs. Authors should prepare high-resolution originals from the start to avoid rework.

### Patient Privacy in Clinical Images

NEJM enforces strict patient privacy requirements. All patient-identifying information must be removed from images, including faces, names, medical record numbers, and any other identifiable features. This is non-negotiable and applies to all clinical images regardless of consent status.

## Decision Framework

```
What type of figure are you preparing?
├── Medical illustration (anatomy, mechanism)
│   └── Do NOT submit → NEJM illustrators create these
├── Data visualization (graph, chart, diagram)
│   ├── Vector source available → AI, EPS, or SVG (preferred)
│   └── Raster only → TIFF at 1,200 DPI (line art) or 300 DPI (photo)
├── Clinical photograph
│   ├── Patient identifiable? → Remove ALL identifying information
│   └── Ready for submission → TIFF at 300+ DPI
└── What stage?
    ├── Peer review → Lower resolution acceptable
    └── Final publication → Full resolution required
```

| Scenario | Format | Resolution | Special Considerations |
|---|---|---|---|
| Kaplan-Meier curve | AI, EPS, SVG | Vector | Editable format preferred |
| Clinical photograph | TIFF | 300+ DPI | Remove patient identifiers |
| Histology image | TIFF | 300+ DPI | Include scale bar |
| Flowchart or diagram | AI, EPS, SVG | Vector | Use Univers or Helvetica |
| Medical illustration | Do NOT submit | N/A | NEJM creates in-house |
| Images in Clinical Medicine | TIFF/JPEG | 300+ DPI | Title max 8 words, legend max 150 words |

## Best Practices

1. **Submit data visualizations as editable vector files**: NEJM prefers AI, EPS, or SVG for graphs and diagrams. Vector formats allow their production team to make typographic adjustments
2. **Do not submit finished medical illustrations**: NEJM's in-house illustrators will create these. Submit reference sketches or descriptions instead
3. **Remove all patient-identifying information**: Strip faces, names, record numbers, and any identifiable features from clinical images before submission
4. **Prepare high-resolution originals early**: Although peer review accepts lower resolution, having 300+ DPI originals ready prevents delays during final production
5. **Use Univers or Helvetica fonts**: NEJM's house font is Univers; Helvetica and Arial are acceptable alternatives. Ensure all text is legible at final reduction size
6. **Respect word limits for Images in Clinical Medicine**: Titles must be 8 words or fewer; legends must be 150 words or fewer
7. **Maintain original unprocessed files**: NEJM may request raw data at any point during review or after publication

## Common Pitfalls

1. **Submitting finished medical illustrations**: NEJM retains copyright on illustrations they create. Submitting finished artwork creates copyright conflicts
   - *How to avoid*: Provide reference sketches, descriptions, or rough drafts; NEJM illustrators will create the final version
2. **Leaving patient-identifying information in images**: Any identifiable features in clinical images can result in rejection and ethical concerns
   - *How to avoid*: Review all clinical images for faces, names, ID numbers, and other identifiers; blur or crop as needed
3. **Using raster formats for data visualizations**: JPEG or PNG graphs lose editability and may appear pixelated at print size
   - *How to avoid*: Export charts and diagrams as AI, EPS, or SVG from your plotting software
4. **Submitting low-resolution line art**: Line art requires 1,200 DPI — significantly higher than the 300 DPI for photographs
   - *How to avoid*: Export line art at 1,200 DPI or use vector formats that are resolution-independent
5. **Exceeding word limits for clinical image submissions**: Images in Clinical Medicine has strict limits (8-word title, 150-word legend)
   - *How to avoid*: Count words before submission; move detailed descriptions to supplementary text if needed

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
- NEJM Editorial Policies: https://www.nejm.org/about-nejm/editorial-policies
