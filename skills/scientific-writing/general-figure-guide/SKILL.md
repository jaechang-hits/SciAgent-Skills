---
name: general-figure-guide
description: "General scientific figure quality checklist for generated plots. Covers visual inspection for overlapping labels, clipped text, missing axes/legends, empty plot areas, overcrowded data, and resolution/format best practices across journals."
license: CC-BY-4.0
---

# General Scientific Figure Quality Guide

## Overview

This guide provides a universal quality checklist for evaluating scientific figures, whether generated programmatically (matplotlib, seaborn, R/ggplot2) or assembled manually. It focuses on visual readability issues that are common across all journals and easily missed during automated plot generation.

## Key Concepts

### Visual Readability

A figure must communicate its data without requiring the reader to guess. The most common readability failures are overlapping labels, clipped text that runs outside the figure boundary, missing or unlabeled axes, absent legends, empty plot areas from incorrect data filtering, and overcrowded data points that merge into an unreadable mass.

### Resolution and Output Format

Scientific figures generally require 300+ DPI for raster output (TIFF, PNG, JPEG) and vector formats (PDF, EPS, SVG) for line art and graphs. Vector formats are preferred for plots because they scale without quality loss. Raster formats are appropriate for photographs and micrographs.

### Color Accessibility

Approximately 8% of males have some form of color vision deficiency. Figures that rely solely on red-green color differences exclude these readers. Use colorblind-friendly palettes (blue-orange, or viridis/cividis colormaps), add pattern or shape differentiation, and test figures with a colorblindness simulator before submission.

### Uniform Image Adjustments

All major journals require that brightness, contrast, and color adjustments be applied uniformly to the entire image. Selective enhancement of specific regions (e.g., adjusting one gel lane) is considered data manipulation and grounds for rejection across all journals. Always document processing steps in the Methods section and retain original unprocessed files.

## Decision Framework

```
Is the figure a generated plot or a photograph?
├── Generated plot (matplotlib, ggplot2, seaborn)
│   ├── Export as vector (PDF, SVG, EPS) → preferred
│   └── Export as raster → 300+ DPI minimum, PNG or TIFF
├── Photograph or micrograph
│   └── Export as raster → 300+ DPI, TIFF preferred
└── Multi-panel composite
    ├── Assemble panels first, then export as single file
    └── Use consistent font sizes and label styles across panels
```

| Issue | How to Detect | Fix |
|---|---|---|
| Overlapping labels | Text visually collides on axes or legend | Rotate labels, reduce font size, or increase figure dimensions |
| Clipped text | Labels or titles cut off at figure edge | Increase margins with `tight_layout()` or `constrained_layout` |
| Missing axes or legends | No axis labels, units, or legend present | Add `xlabel`, `ylabel`, `legend()` calls |
| Empty plot area | Blank canvas with axes but no visible data | Check data filtering, column names, and plot function arguments |
| Overcrowded data | Points merge into solid mass | Reduce marker size, add transparency (alpha), or use density plots |

## Best Practices

1. **Run a visual check after every plot generation**: Inspect the rendered image for overlapping labels, clipped text, missing axes/legends, empty areas, and overcrowded data before proceeding
2. **Use `tight_layout()` or `constrained_layout=True`**: These prevent text clipping at figure boundaries, the most common layout failure in matplotlib
3. **Set DPI at figure creation time**: Configure `fig.set_dpi(300)` or `plt.savefig(..., dpi=300)` to ensure publication-quality output from the start
4. **Export plots as vector formats**: Use PDF, SVG, or EPS for graphs and diagrams. Reserve raster formats (PNG, TIFF) for photographs and micrographs
5. **Apply consistent font sizes across panels**: All text in a multi-panel figure should use the same font family and comparable sizes (typically 6-8 pt for labels, 8 pt for panel identifiers)
6. **Add transparency for dense scatter plots**: Use `alpha=0.3`-`0.5` when plotting thousands of points to reveal density structure instead of a solid mass
7. **Include units on all axes**: Every axis should show the measured parameter and units in parentheses (e.g., "Time (hours)", "Concentration (nM)")

## Common Pitfalls

1. **Not inspecting generated plots before saving**: Automated pipelines often produce figures with layout issues that go unnoticed until review
   - *How to avoid*: Always render and visually inspect each figure; if reviewing programmatically, check for text bounding-box overlaps
2. **Clipped axis labels or titles**: Default matplotlib margins often cut off long labels or suptitles
   - *How to avoid*: Call `fig.tight_layout()` or create figures with `constrained_layout=True`
3. **Missing legends on multi-series plots**: Plots with multiple lines or groups are unreadable without a legend
   - *How to avoid*: Always call `ax.legend()` when plotting more than one series; verify legend entries match the data
4. **Overcrowded scatter plots at large N**: Scatter plots with >10,000 points become solid blobs at default settings
   - *How to avoid*: Use `alpha` transparency, hexbin plots, or kernel density estimation for large datasets
5. **Saving at screen resolution (72 DPI)**: Default screen DPI produces figures that are unprintable in journals
   - *How to avoid*: Always specify `dpi=300` (minimum) in `savefig()` or set it on the figure object at creation

## Protocol Guidelines

1. **Set up figure dimensions and DPI**: Before plotting, configure target width (journal column width), aspect ratio, and DPI (300+ minimum) on the figure object
2. **Generate the figure** using your plotting library with the pre-configured settings
3. **Visually inspect** the rendered output for these specific issues:
   - Overlapping labels or annotations
   - Clipped text at figure boundaries
   - Missing axis labels, units, or legends
   - Empty plot areas (data not rendered)
   - Overcrowded or indistinguishable data points
4. **If any issue is found**, regenerate with targeted fixes (adjust layout, font size, margins, alpha, or figure dimensions)
5. **Export in the correct format**: vector (PDF/EPS/SVG) for plots, raster (TIFF/PNG at 300+ DPI) for photographs
6. **Verify the saved file**: reopen the exported file to confirm it matches the on-screen rendering

## Further Reading

- [Matplotlib Figure Layout Guide](https://matplotlib.org/stable/users/explain/axes/tight_layout_guide.html) -- tight_layout and constrained_layout usage
- [Ten Simple Rules for Better Figures (PLOS)](https://doi.org/10.1371/journal.pcbi.1003833) -- general principles for scientific figure design
- [Points of View: Nature Methods Column](https://www.nature.com/collections/qghhqm/pointsofview) -- visual design principles for scientific data

## Related Skills

- `nature-figure-guide` -- Nature-specific figure requirements
- `cell-figure-guide` -- Cell Press figure requirements
- `science-figure-guide` -- Science (AAAS) figure requirements
- `pnas-figure-guide` -- PNAS figure requirements
