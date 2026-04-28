---
name: science-figure-guide
description: "Science (AAAS) figure preparation: resolution (150-300+ DPI), formats (PDF/EPS/TIFF), RGB color, Myriad/Helvetica fonts, strict image manipulation policies including gamma adjustment disclosure."
license: CC-BY-4.0
compatibility: Python 3.10+, Pillow, Matplotlib
metadata:
  authors: HITS
  version: "1.0"
---

# Science (AAAS) Figure Preparation Guide

## Overview

This guide provides the complete specifications for preparing figures for submission to **Science** journal (published by AAAS). Science has different requirements for initial vs. revised manuscript submissions and requires explicit disclosure of nonlinear image adjustments.

**Official reference**: https://www.science.org/content/page/instructions-preparing-initial-manuscript

---

## Resolution Requirements

### Initial Submission

| Image Type | Resolution |
|---|---|
| All figures | **150-300 DPI** |

### Revised Manuscript (Higher Standards)

| Image Type | Minimum Resolution | Notes |
|---|---|---|
| Line art | **300 DPI+** | At final print size |
| Grayscale and color artwork | **300 DPI+** | Higher resolution preferred |

**CRITICAL**: Upsampling (artificially increasing resolution) is **prohibited**. The resolution must be native to the image.

```python
from PIL import Image

def check_science_resolution(image_path, stage='initial'):
    """Check image resolution for Science submission.

    Args:
        image_path: Path to image file
        stage: 'initial' (150-300 DPI) or 'revised' (300+ DPI)
    """
    img = Image.open(image_path)
    dpi = img.info.get('dpi', (72, 72))

    min_dpi = 150 if stage == 'initial' else 300

    print(f"Stage: {stage} submission")
    print(f"DPI: {dpi[0]} x {dpi[1]}")
    print(f"Minimum required: {min_dpi} DPI")

    if dpi[0] >= min_dpi:
        print("PASS: Resolution meets Science requirements")
    else:
        print(f"FAIL: Need at least {min_dpi} DPI")

    return dpi[0] >= min_dpi
```

---

## File Format

### Revised Manuscript Formats (in order of preference)

| Figure Type | Preferred Formats |
|---|---|
| Vector illustrations/diagrams | **PDF, EPS, Adobe Illustrator (AI)** |
| Raster illustrations/diagrams | **TIFF** (300+ DPI) |
| Photography/microscopy | TIFF, JPEG, PNG, PSD, EPS, PDF |

### Initial Submission
- Figures can be embedded directly in `.docx` or PDF manuscript files

---

## Figure Size and Dimensions

| Layout | Width |
|---|---|
| 1 column | **3.4 inches** (86 mm / 20.38 picas) |
| 1.5 columns | **5.0 inches** |
| 2 columns | **7.0-7.3 inches** |
| Maximum | **6.5 x 8 inches** (16.5 x 20 cm) |

Figures should be sized to fit 8.5" x 11" or A4 paper.

```python
import matplotlib.pyplot as plt

SCIENCE_WIDTHS = {
    'single':  3.4,   # inches
    'middle':  5.0,
    'double':  7.3,
}

def create_science_figure(layout='single', aspect_ratio=0.75):
    """Create a Matplotlib figure sized for Science journal."""
    width = SCIENCE_WIDTHS[layout]
    height = min(width * aspect_ratio, 8.0)  # max height 8 inches

    fig, ax = plt.subplots(figsize=(width, height))
    fig.set_dpi(300)
    return fig, ax
```

---

## Color Mode

- **RGB** is the standard practice
- Journal handles CMYK conversion for print
- No explicit color mode mandate, but RGB is recommended

---

## Font Requirements

| Element | Font | Size | Style |
|---|---|---|---|
| Preferred font | **Myriad** | — | Sans-serif |
| Alternative fonts | Helvetica, Arial | — | Sans-serif |
| Panel labels | — | **8 pt** | **Bold** |
| Other figure text | — | 5-7 pt | Max 7 pt, min 5 pt |

### Critical Rules
- **All fonts must be embedded**
- Use sans-serif fonts whenever possible
- Simple solid or open symbols reduce well at small sizes

```python
import matplotlib.pyplot as plt

def set_science_fonts():
    """Configure Matplotlib for Science journal figure fonts."""
    plt.rcParams.update({
        'font.family': 'sans-serif',
        'font.sans-serif': ['Myriad Pro', 'Helvetica', 'Arial'],
        'font.size': 7,
        'axes.labelsize': 7,
        'axes.titlesize': 7,
        'xtick.labelsize': 6,
        'ytick.labelsize': 6,
        'legend.fontsize': 5,
    })
```

---

## Labeling Conventions

### Figure Numbering
- Cite figures in numerical order in the text

### Titles and Captions
- Figure titles go at the **beginning of the caption**, NOT inside the figure
- No single caption should exceed approximately **200 words**

### Axes
- Label ordinate and abscissa with: **parameter/variable**, **units**, and **scale**
- Use sans-serif fonts for all labels

```python
def format_science_axis(ax, xlabel, ylabel, x_unit='', y_unit=''):
    """Format axes following Science journal conventions."""
    if x_unit:
        ax.set_xlabel(f"{xlabel} ({x_unit})", fontsize=7)
    else:
        ax.set_xlabel(xlabel, fontsize=7)

    if y_unit:
        ax.set_ylabel(f"{ylabel} ({y_unit})", fontsize=7)
    else:
        ax.set_ylabel(ylabel, fontsize=7)

    ax.tick_params(labelsize=6)
```

---

## Image Integrity and Manipulation Policy

### PERMITTED
- **Linear adjustments**: Brightness, contrast, color — applied **uniformly to the entire image**

### REQUIRES DISCLOSURE
- **Nonlinear adjustments** (e.g., gamma corrections) must be **specified in the figure caption**

### PROHIBITED
- **Selective enhancement**: Altering one part of an image while leaving other parts unchanged
- Adjustments that cause changes in data interpretation
- Manipulations applied to local areas only

### Best Practices
- Perform all manipulations only on **copies** of unprocessed image data
- Adjustments must be moderate and not misrepresent the data
- All changes must be applied to the **whole image**

---

## Python Quick Start: Full Validation

```python
from PIL import Image
import os

def validate_science_figure(image_path, stage='initial'):
    """Full validation of a figure against Science requirements."""
    img = Image.open(image_path)
    issues = []

    # 1. Resolution check
    dpi = img.info.get('dpi', (72, 72))
    min_dpi = 150 if stage == 'initial' else 300
    if dpi[0] < min_dpi:
        issues.append(f"Resolution {dpi[0]} DPI below minimum {min_dpi} DPI for {stage} submission")

    # 2. Color mode check
    if img.mode not in ('RGB', 'RGBA'):
        issues.append(f"Color mode is {img.mode}; RGB recommended")

    # 3. Dimension check
    if dpi[0] > 0:
        width_in = img.size[0] / dpi[0]
        height_in = img.size[1] / dpi[1]
        if width_in > 7.3:
            issues.append(f"Width {width_in:.1f}\" exceeds maximum 7.3\"")
        if height_in > 8.0:
            issues.append(f"Height {height_in:.1f}\" exceeds maximum 8.0\"")

    # Report
    print(f"=== Science Figure Validation ({stage}) ===")
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

### Two-Stage Submission Process

Science uses different figure requirements for initial vs. revised manuscripts. Initial submissions accept 150-300 DPI figures embedded in the manuscript. Revised manuscripts require separate high-resolution files (300+ DPI) in publication-ready formats. This two-stage approach reduces upfront preparation burden while ensuring final quality.

### Nonlinear Adjustment Disclosure

Science uniquely requires explicit disclosure of nonlinear image adjustments (e.g., gamma corrections) in the figure caption. Linear adjustments (brightness, contrast) applied uniformly need no special disclosure. This distinction is critical — failure to disclose gamma changes can be flagged as data manipulation.

### Figure Sizing Constraints

Science enforces strict maximum dimensions: 6.5 x 8 inches (16.5 x 20 cm). Single-column figures are 3.4 inches wide; double-column figures are 7.0-7.3 inches. All figures must fit on standard letter (8.5 x 11 inch) or A4 paper.

## Decision Framework

```
What submission stage are you at?
├── Initial submission
│   ├── Embed figures in manuscript (.docx or PDF)
│   └── 150-300 DPI acceptable
└── Revised manuscript
    ├── Upload separate high-resolution files
    ├── Vector figures (graphs, diagrams)
    │   └── PDF, EPS, or AI format
    └── Raster figures (photos, micrographs)
        └── TIFF at 300+ DPI
```

| Scenario | Format | Resolution | Notes |
|---|---|---|---|
| Initial submission graph | Embedded in .docx | 150-300 DPI | Low bar for initial review |
| Revised manuscript graph | PDF or EPS | Vector | Separate upload required |
| Photograph (revised) | TIFF | 300+ DPI | Native resolution only |
| Micrograph with gamma adjustment | TIFF | 300+ DPI | Disclose gamma in caption |
| Diagram or schematic | AI or EPS | Vector | Embed all fonts |

## Best Practices

1. **Prepare high-resolution files from the start**: Even though initial submissions accept 150 DPI, creating figures at 300+ DPI from the beginning avoids rework during revision
2. **Disclose all nonlinear adjustments in captions**: Gamma corrections and other nonlinear transforms must be explicitly noted in the figure caption, not just in Methods
3. **Use Myriad Pro as primary font**: Science's preferred font is Myriad; Helvetica and Arial are acceptable alternatives. Consistent font usage across all figures is expected
4. **Keep captions under 200 words**: Science enforces a ~200-word limit on individual figure captions. Move detailed methodology to the Methods section
5. **Place titles in captions, not figures**: Figure titles belong at the beginning of the caption text, not rendered inside the figure itself
6. **Label axes with parameter, units, and scale**: Science requires all axes to include the measured parameter, units in parentheses, and scale information
7. **Use simple solid or open symbols**: Science recommends symbols that reproduce well at small sizes. Avoid complex or filled symbols that become indistinguishable when reduced

## Common Pitfalls

1. **Submitting low-resolution figures for revised manuscripts**: The 150 DPI floor only applies to initial submissions. Revised manuscripts require 300+ DPI
   - *How to avoid*: Re-export all figures at 300+ DPI before submitting the revision
2. **Failing to disclose gamma adjustments**: Nonlinear corrections not mentioned in the caption can trigger an image integrity investigation
   - *How to avoid*: Add a sentence to the caption for any figure with gamma or nonlinear adjustments (e.g., "Gamma correction of 0.8 applied uniformly")
3. **Exceeding figure dimension limits**: Figures wider than 7.3 inches or taller than 8 inches will be rejected
   - *How to avoid*: Check dimensions before export; use the validation script to verify
4. **Upsampling images to meet resolution requirements**: Artificially increasing DPI adds no real detail and may introduce artifacts
   - *How to avoid*: Re-export from the original source at native high resolution
5. **Using serif fonts in figures**: Science requires sans-serif fonts (Myriad, Helvetica, Arial). Serif fonts like Times New Roman are not acceptable
   - *How to avoid*: Set sans-serif as the default in your plotting software before generating figures

## Pre-Submission Checklist

Before submitting figures to Science, verify:

- [ ] Initial submission: 150-300 DPI minimum
- [ ] Revised submission: 300+ DPI minimum (no upsampling)
- [ ] Vector figures in PDF, EPS, or AI format
- [ ] Raster figures in TIFF at 300+ DPI
- [ ] Font is Myriad, Helvetica, or Arial (sans-serif)
- [ ] Panel labels at 8 pt bold; text between 5-7 pt
- [ ] All fonts embedded
- [ ] Figure titles in caption, not inside figure
- [ ] Captions under 200 words
- [ ] Axes labeled with parameter, units, and scale
- [ ] All adjustments applied uniformly to entire image
- [ ] Gamma/nonlinear adjustments noted in caption
- [ ] No selective enhancement of image regions
- [ ] Original unprocessed data preserved

---

## References

- Science Initial Manuscript Instructions: https://www.science.org/content/page/instructions-preparing-initial-manuscript
- Science Revised Article Instructions: https://www.science.org/content/page/instructions-authors-revised-research-articles
- Science Editorial Policies: https://www.science.org/content/page/science-journals-editorial-policies
