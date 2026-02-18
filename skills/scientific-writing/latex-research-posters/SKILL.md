---
name: latex-research-posters
description: "Create professional research posters in LaTeX using beamerposter, tikzposter, or baposter. Layout design, typography, color schemes, figure integration, accessibility, and quality control for conference presentations. Includes ready-to-use templates. For programmatic figure generation use matplotlib-scientific-plotting or plotly-interactive-visualization."
license: CC-BY-4.0
---

# LaTeX Research Posters

## Overview

Research posters are a critical medium for scientific communication at conferences, symposia, and academic events. This knowhow covers end-to-end poster creation in LaTeX: package selection, layout design, typography, color schemes, figure integration, accessibility, compilation, and quality control for print and digital display.

## Key Concepts

### 1. LaTeX Poster Packages

Three major packages, each with distinct strengths:

| Package | Architecture | Best For | Learning Curve |
|---------|-------------|----------|---------------|
| **beamerposter** | Beamer extension | Traditional academic posters, institutional branding | Low (if you know Beamer) |
| **tikzposter** | TikZ-based blocks | Modern colorful designs, custom graphics | Medium |
| **baposter** | Box-based grid | Multi-column layouts, consistent spacing | Low |

**beamerposter**: Uses Beamer's `\begin{block}` syntax. Themes and color schemes from Beamer carry over. Best when your institution already has a Beamer theme.

**tikzposter**: Declarative block placement with `\block{Title}{Content}`. Built-in color styles (Denmark, Germany, etc.) and layout themes (Rays, Wave). Most flexible for custom designs.

**baposter**: Defines named boxes in a grid. Automatic positioning and spacing. Best when you want structured, uniform column layouts without manual placement.

### 2. Poster Dimensions and Orientation

| Standard | Size | Region | Use |
|----------|------|--------|-----|
| **A0** | 841 × 1189 mm (33.1 × 46.8 in) | Europe | Most common academic standard |
| **A1** | 594 × 841 mm (23.4 × 33.1 in) | Europe | Smaller venues |
| **36 × 48 in** | 914 × 1219 mm | North America | Standard US conference size |
| **42 × 56 in** | 1067 × 1422 mm | North America | Large format |
| **48 × 72 in** | 1219 × 1829 mm | North America | Extra large |

**Orientation**: Portrait (vertical) is most common and traditional. Landscape (horizontal) works better for timelines, wide figures, or side-by-side comparisons.

### 3. Typography Rules

| Element | Size Range | Purpose |
|---------|-----------|---------|
| Title | 72–120 pt | Readable from 15+ feet |
| Section headers | 48–72 pt | Readable from 8–10 feet |
| Body text | 24–36 pt | Readable from 4–6 feet |
| Captions | 20–28 pt | Readable from 3 feet |

- Use **sans-serif** fonts (Helvetica, Calibri, Arial) for poster readability
- Limit to **2–3 font families** maximum
- Avoid italics (harder to read from distance)
- Use bold for emphasis, not underlining

### 4. Visual Content Guidelines

- **40–50% of poster area** should be visual content (figures, diagrams, tables)
- **300 DPI minimum** for raster images at final print size
- Use **vector graphics** (PDF, SVG) whenever possible for scalability
- Target **3–6 main figures** per poster
- Total text: **300–800 words** (less is more)

## Decision Framework

### Package Selection

```
Start: What is your design priority?
├── Institutional branding / existing Beamer theme?
│   └── YES → beamerposter
├── Modern, colorful, custom TikZ graphics?
│   └── YES → tikzposter
├── Structured multi-column grid with minimal setup?
│   └── YES → baposter
└── Not sure
    └── tikzposter (most flexible default)
```

### Layout Decision Table

| Poster Content | Columns | Layout Strategy |
|---------------|---------|-----------------|
| Few key results, large figures | 2 columns | Wide figure panels, brief text |
| Balanced text and figures | 3 columns | Standard academic layout |
| Data-heavy with many small figures | 4 columns | Compact grid, small text |
| Narrative flow / timeline | 2 columns landscape | Left-to-right story |

### Content vs Visual Balance

| Poster Type | Text % | Visual % | Word Count |
|-------------|--------|----------|------------|
| Experimental research | 40% | 60% | 400–600 |
| Computational/modeling | 50% | 50% | 500–700 |
| Review/survey | 55% | 45% | 600–800 |
| Method paper | 35% | 65% | 300–500 |

## Best Practices

1. **MANDATORY: Every poster must include at least 2 figures.** Posters are primarily visual media — text-heavy posters fail to communicate. Target 3–4 figures for comprehensive posters: methodology diagram, key results, conceptual framework.

2. **MANDATORY: Verify poster dimensions match conference requirements exactly.** Use `pdfinfo poster.pdf | grep "Page size"` after compilation. A0 should show ~2384 × 3370 points.

3. **Follow the Z-pattern reading flow.** Place the most important content (title, key result figure) in the top-left quadrant. Readers naturally scan: top-left → top-right → bottom-left → bottom-right.

4. **Use white space intentionally.** White space is not wasted space — it improves readability and visual hierarchy. Don't fill every gap with text.

5. **Keep text scannable.** Use bullet points instead of paragraphs. Each section should be understandable in under 30 seconds.

6. **Anti-pattern — cramming the full paper into poster format.** A poster is not a shrunken paper. Extract 1–3 key messages and design around those. Leave details for the handout or QR-linked paper.

7. **Test readability at reduced scale.** Print at 25% scale on letter/A4 paper. If the title isn't readable from 6 feet, the body text isn't readable from 2 feet, or figures are unclear, revise.

8. **Use color-blind friendly palettes.** Avoid red-green combinations (affects ~8% of males). Use Viridis, ColorBrewer, or IBM Color Blind Safe palettes. Add patterns or shapes alongside color coding.

9. **Embed all fonts in the final PDF.** Run `pdffonts poster.pdf` — every font should show "yes" in the "emb" column. Non-embedded fonts may render differently on the printer's system.

10. **Include QR codes for supplementary materials.** Link to: full paper (DOI), code repository (GitHub), data (Zenodo), video demo. Minimum size: 2 × 2 cm for reliable scanning.

## Common Pitfalls

1. **Font sizes too small (under 24pt body text).** Viewers stand 4–6 feet away; small text is unreadable. *How to avoid*: Set minimum body text to 24pt and verify with a reduced-scale print test.

2. **Too much text (over 1000 words).** Poster sessions are 2–5 minutes per viewer; they won't read paragraphs. *How to avoid*: Target 300–800 words. Replace explanatory text with annotated figures.

3. **Low-resolution images that pixelate when printed.** Screen-resolution images (72–150 DPI) look fine on monitor but terrible at poster size. *How to avoid*: Ensure all raster images are 300+ DPI at final print size. Use `pdfimages -list poster.pdf` to verify.

4. **RGB colors sent to CMYK printer cause color shift.** Bright screen colors appear dull or shifted when printed. *How to avoid*: Request the printer's color profile; convert color space if required. When in doubt, use muted, high-contrast palettes.

5. **Content extends beyond page boundaries or large white margins.** Default margin settings often waste 10–15% of poster area. *How to avoid*: Set explicit margins (10mm recommended) in documentclass options. Debug with a visible page boundary frame during development.

6. **Placeholder text left in final version.** "Lorem ipsum", "TODO", or template instructions left visible. *How to avoid*: Use the QC checklist (Step 8 of Workflow) systematically — check for all placeholder text before sending to print.

7. **Unembedded fonts cause rendering failures.** The printer's system substitutes different fonts, breaking layout and character rendering. *How to avoid*: Compile with `pdflatex` (auto-embeds), or use `-dEmbedAllFonts=true`. Verify with `pdffonts`.

8. **No clear visual hierarchy — everything looks the same importance.** Viewers can't identify the key message or navigate the poster. *How to avoid*: Use 3 distinct size levels (title, headers, body). Use color blocks to group related content. Add a "Take-Home Message" box.

## Workflow

### Stage 1: Planning

1. **Confirm requirements**: poster size, orientation, submission deadline, format requirements
2. **Draft content outline**: identify 1–3 core messages, select 3–6 key figures
3. **Choose package**: beamerposter (institutional), tikzposter (modern), or baposter (structured)
4. **Plan layout**: number of columns (2–4), content flow (Z-pattern), space allocation (title 10–15%, content 70–80%, footer 5–10%)

### Stage 2: Template Setup

1. **Start from a template** (see Companion Assets): customize color scheme, page size, orientation
2. **Configure typography**: set font sizes per hierarchy level (title → headers → body → captions)
3. **Set margins**: 10mm outer margins recommended; configure column spacing (15–20mm)
4. **Add institutional elements**: logos (high-resolution), color codes (official RGB/CMYK values)

### Stage 3: Content Integration

1. **Create header**: title (10–15 words, concise), authors, affiliations, logos
2. **Populate sections**: Introduction, Methods, Results, Conclusions — bullet points preferred
3. **Generate figures**: create publication-quality figures using matplotlib, plotly, or specialized tools:
   - Methodology flowcharts and experimental design diagrams
   - Results plots (bar charts, heatmaps, scatter plots, Kaplan-Meier curves)
   - Conceptual framework or model architecture diagrams
4. **Integrate figures**: use `\includegraphics` with consistent sizing and clear captions
5. **Add references**: 5–10 key citations in abbreviated style; consider QR code to full bibliography
6. **Add QR codes**: link to paper DOI, GitHub repo, supplementary data

### Stage 4: Refinement

1. **Review visual balance**: ensure 40–50% visual content, no overcrowded sections
2. **Check typography**: all fonts readable at intended viewing distances
3. **Verify color accessibility**: test with color-blindness simulator (e.g., Coblis)
4. **Check contrast ratios**: text-background ≥ 4.5:1 (WCAG AA), important elements ≥ 7:1 (WCAG AAA)
5. **Proofread**: all text, author names, affiliations, numbers, statistics

### Stage 5: Compilation and QC

1. **Compile**: `pdflatex poster.tex` (or `lualatex` for better font support)
2. **Verify page size**: `pdfinfo poster.pdf | grep "Page size"` — must match requirements exactly
3. **Verify font embedding**: `pdffonts poster.pdf` — all "yes" in "emb" column
4. **Verify image resolution**: `pdfimages -list poster.pdf` — all ≥300 DPI
5. **Reduced-scale print test**: print at 25% on letter/A4; check readability from 2, 4, 6 feet
6. **Peer review**: 30-second test (can they identify main message?), 5-minute review (do they understand conclusions?)
7. **Optimize for delivery**: compress for email (< 10MB) if needed; keep original for printing
8. **Final checklist**: no placeholders, all citations resolved (no [?] marks), file named `[LastName]_[Conference]_Poster.pdf`

## Protocol Guidelines

### Compilation Commands

```bash
# Basic compilation
pdflatex poster.tex

# With bibliography
pdflatex poster.tex && bibtex poster && pdflatex poster.tex && pdflatex poster.tex

# Better font support
lualatex poster.tex
# or
xelatex poster.tex
```

### Quality Control Commands

```bash
# Verify page dimensions
pdfinfo poster.pdf | grep "Page size"

# Check font embedding
pdffonts poster.pdf

# Check image resolution
pdfimages -list poster.pdf

# Check for compilation warnings
grep -i "warning\|error\|overfull\|underfull" poster.log

# Compress for email (keeps print quality)
gs -sDEVICE=pdfwrite -dCompatibilityLevel=1.4 \
   -dPDFSETTINGS=/printer -dNOPAUSE -dQUIET -dBATCH \
   -sOutputFile=poster_compressed.pdf poster.pdf
```

### Package Installation

```bash
# TeX Live (Linux/Mac)
tlmgr install beamerposter tikzposter baposter qrcode subcaption tcolorbox

# MiKTeX (Windows) — packages auto-install on first use
```

## Further Reading

- [beamerposter CTAN page](https://ctan.org/pkg/beamerposter) — official documentation and examples
- [tikzposter CTAN page](https://ctan.org/pkg/tikzposter) — themes, color styles, block customization
- [baposter project page](http://www.brian-amberg.de/uni/poster/) — box-based layout documentation
- Colin Purrington, "Designing conference posters" — evidence-based design guidelines (https://colinpurrington.com/tips/poster-design)
- [Web AIM Contrast Checker](https://webaim.org/resources/contrastchecker/) — WCAG compliance verification

## Related Skills

- **matplotlib-scientific-plotting** — generate publication-quality figures (bar charts, heatmaps, scatter plots) for poster content
- **plotly-interactive-visualization** — create interactive figures exportable as static PNG/PDF for posters
- **seaborn-statistical-visualization** — statistical plots with automatic aggregation for results figures

## Companion Assets

Templates are provided in the `assets/` subdirectory:

| File | Package | Description |
|------|---------|-------------|
| `beamerposter_template.tex` | beamerposter | Traditional 3-column portrait layout (A0) with institutional header |
| `tikzposter_template.tex` | tikzposter | Modern block-based design with Denmark color style |
| `baposter_template.tex` | baposter | Structured 3-column portrait grid with automatic spacing |

Each template is a **complete, compilable LaTeX document** with placeholder content. Customize: (1) replace placeholder text and figures, (2) adjust color scheme, (3) update page size if needed.
