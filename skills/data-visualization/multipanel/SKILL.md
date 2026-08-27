---
name: multipanel
description: >
  Assemble multiple plots into ONE publication-ready multi-panel journal figure
  (e.g. Figure 1 with panels A, B, C). Use whenever the user asks to combine,
  compose, or lay out several plots as a single composite figure — newly plotted
  from data or from already-rendered panels the user supplies (PNG/PDF). Ask the
  user to pick one of two approaches: (1) redraw every
  panel into one unified figure using independent, tightly
  packed `subfigures` (each sized to its own labels, so axes need NOT align),
  consistent style, correctly placed panel letters, and per-panel legends/colorbars;
  (2) composite already-rendered PNG/PDF panels onto a mosaic canvas and add panel
  letters (image compositing, not plotting). Both export vector PDF + high-DPI PNG.
  For a SINGLE plot from a data table, use the sibling `omics-plotting` skill instead.
license: Proprietary (HITS Inc.)
---

# multipanel

## Overview

A multi-panel figure is **one** figure, built one of two ways depending on what
you have:

- **Option 1 — redraw every panel** (you have the data or plotting code): draw
  each data panel with a python script into its **own `subfigure`** so it packs
  to its own labels — no empty bands, and axes need NOT align across the grid.
  Follow the discipline below so legends stay inside their panels, panel letters
  sit at each panel's own top-left, and text never overlaps.
- **Option 2 — composite finished images** (you only have rendered PNG/PDF panels):
  paste them onto a `plt.subplot_mosaic` canvas — fine here, since images carry no
  tick labels to misalign — add panel letters, and export.

A mix is allowed: if one or two panels are image-only (no data/code), `imshow`
them onto their own subfigure axes and redraw the rest into the same figure. Both
modes export a vector PDF and a high-DPI PNG.

**Always export the individual panels AND the composite.** Every run outputs both:
one standalone figure per panel (`figure1A.png`, `figure1B.png`, …) and the combined
figure (`combined_figure1.pdf` + `.png`) — not just the composite. Because a
matplotlib `subfigure` cannot be saved on its own, factor every data panel's plotting
body into a `draw_<letter>(ax)` function (option 1); the same function then draws onto
the composite's subfigure axis AND onto a fresh standalone figure, so the panels stay
identical across both outputs with no duplicated drawing code. See "Exporting
individual panels" below.

This skill covers **composition**. For how to draw each individual plot type
(volcano, GSEA bar, heatmap, box/violin, PCA, Kaplan–Meier, …), use the sibling
`omics-plotting` skill — copy each recipe's **body** onto a subfigure's axis rather than
calling it as a standalone figure. Everything you need here (shared style,
composite recipe, panel-label helper) is in this document.

## When to use

- The user asks for a **multi-panel / composite / journal figure** (panels A, B,
  C…) combining two or more plots into one page of image.
- The user hands you or points out **already-rendered panels (PNG/PDF)** and wants them combined
  into one figure (image assembly — see "Assembling user-provided panels").
- You are assembling a figure for a report, a paper submission, or a presentation
  and want all panels to read as one consistent system.

## Do NOT use for

- A **single** plot from a data table — use the sibling `omics-plotting` skill.
- Interactive dashboards or web charts (this is static matplotlib output).
- 3D molecular structure rendering (that is the structure viewer, not a plot).

## Key Concepts

### Redraw vs composite — two composition modes

There are two fundamentally different ways to build a composite, and the user
chooses. **Redraw (option 1)** rebuilds every panel from data or
code in one script, giving uniform style, fonts, colors, and panel letters — best
when you hold the underlying data/DataFrame or the plotting code. **Composite
(option 2)** pastes already-rendered PNG/PDF panels onto a canvas and only adds
panel letters — image assembly, not plotting — best when you have only the
finished images. A mix is allowed: image-only panels are `imshow`-pasted while
data panels are redrawn, all into one figure.

### Independent subfigures vs shared mosaic

The central layout decision. Giving **each panel its own `subfigure`** lets it run
its own `constrained_layout` and pack tightly to its OWN labels — panels sit flush
with no empty bands, and axes deliberately do NOT align across the grid. A single
shared `subplot_mosaic` gridspec instead equalizes every column's margin to its
widest y-label, leaving wide empty bands beside short-label panels. Independent
subfigures are the default here because composites usually mix heterogeneous plot
types; a shared mosaic is correct only when panels genuinely share a scale and are
meant to be read against each other.

### Panel letters in the subfigure frame

Panel letters (bold `A, B, C…`) must sit at each panel's OWN outer top-left, left
of that panel's y-axis labels — never merged into the title and never snapped to a
shared column x-position. Placing each letter at `(0, 1)` in its subfigure's
coordinate frame (`transform=sf.transSubfigure`) guarantees it hugs its panel
regardless of neighbors' label widths.

## Decision Framework

Start from what you have, then how panels relate:

```
What sources do you have?
├─ Data / code for every panel .................. Option 1: redraw all
├─ Only finished PNG/PDF images ................. Option 2: composite images
└─ Mix (some data, some image-only) ............. Option 1 + imshow the image-only panels
        │
        ▼
How do the panels relate?
├─ Heterogeneous plot types (default) ........... Independent subfigures (tight pack, axes need NOT align)
└─ Same scale, read against each other .......... Shared subplot_mosaic (aligned axes)
        │
        ▼
Layout: sketch the grid [[...]], nest subfigures for spanning panels, fill every cell
```

| Situation | Approach | Layout primitive | Panel letters |
|---|---|---|---|
| Have data/code for all panels | Redraw (option 1) | `fig.subfigures(...)` per panel | subfigure frame `(0,1)` |
| Only rendered images | Composite (option 2) | `plt.subplot_mosaic` + `imshow` | mosaic axes top-left |
| Some data, some image-only | Redraw + paste | subfigures + `imshow` leaf | subfigure frame `(0,1)` |
| Panels share a common scale | Shared mosaic | `subplot_mosaic` aligned | axes top-left |
| Spanning panel (e.g. bottom row) | Nested subfigures | `top[0].subfigures(1, 2)` | leaf subfigure frame |

## Workflow

1. **Ask which approach first — ask the user, then wait.** Both approaches
   below are usually viable and the choice is the user's, so **before drawing or writing any
   script, ask the user to choose between these two concrete options**:
   - **Option 1 — Redraw every panel into one unified figure** (from data/code): consistent
     style, fonts, colors, and panel letters across all panels. Best when you have the
     underlying data (CSV/TSV/DataFrame) or the plotting code.
   - **Option 2 — Composite already-rendered images**: paste the finished PNG/PDF panels
     onto a canvas and add panel letters — image assembly, not plotting. Best when you only
     have the finished images (no data/code) or the user wants to keep the originals as-is.

   Skip the question only when one option is impossible (e.g. only images and no data/code →
   option 2 is forced; or a data table with no rendered images → option 1) and say why. If a
   mix (some panels have data, one or two are images-only), tell the user
   that the image-only panels will be pasted regardless (discipline in the intro).
2. **Decide the layout** (the grid `[[...]]` sketch is just to plan the tiling; you build
   it with nested `subfigures`, not `subplot_mosaic` — see discipline #1). Fill every cell.
  — e.g. two on top, one spanning the bottom → `[["A", "B"], ["C", "C"]]` →
    `top = fig.subfigures(2, 1); tc = top[0].subfigures(1, 2)` (A,B in `tc`; C in `top[1]`).
  — e.g. three on top, two on the bottom → `[["A", "B", "C"], ["D", "E", "E"]]`.
  - e.g. one big panel on the left, two stacked on the right → `[["A", "B"], ["A", "C"]]` →
    `lr = fig.subfigures(1, 2); A = lr[0]; rr = lr[1].subfigures(2, 1)`.
3. **Gather each panel's source** — a workspace-relative CSV/TSV (or DataFrame)
   for data panels, or a user-supplied PNG/PDF for image panels.
4. **Write one python script**: paste the style block, **factor each data panel's
   plotting body into a `draw_<letter>(ax)` function** (so it can render onto both a
   subfigure axis and a standalone figure), build the subfigures (nest for spanning
   panels), call each `draw_<letter>` onto its axis (data) or `imshow` the image,
   collect the subfigures into a `panels` dict, and add panel letters with the helper.
   Then **always save both outputs** to **workspace-relative** paths under `figures/`:
   - the **composite** as `figures/combined_figure1.pdf` + `figures/combined_figure1.png`, and
   - **each individual panel** as `figures/figure1A.png`, `figures/figure1B.png`, … (plus
     matching `.pdf`) by rendering every `draw_<letter>` onto a fresh standalone figure.
   See "Exporting individual panels" for the exact loop.
5. **Report the saved paths** back to the user — the combined figure and every
   individual panel file.

## Shared style — paste at the top of the script

```python
import matplotlib.pyplot as plt

# Publication style (colorblind-friendly, editable vector text, no top/right spines)
PUB_STYLE = {
    "figure.dpi": 110, "savefig.dpi": 300, "savefig.bbox": "tight",
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "Liberation Sans", "Nimbus Sans", "Helvetica", "DejaVu Sans"],
    "font.size": 11, "axes.titlesize": 13, "axes.titleweight": "bold",
    "figure.titlesize": 13, "figure.titleweight": "bold",
    "axes.labelsize": 12, "axes.linewidth": 1.0,
    "axes.spines.top": False, "axes.spines.right": False,
    "xtick.labelsize": 10, "ytick.labelsize": 10,
    "xtick.direction": "out", "ytick.direction": "out",
    "legend.frameon": False, "legend.fontsize": 9,
    "svg.fonttype": "none", "pdf.fonttype": 42, "ps.fonttype": 42,
}
plt.rcParams.update(PUB_STYLE)

# Palette — reuse the SAME colors across every panel
UP, DOWN, NS = "#d73721", "#204897", "#d9d9d9"   # up / down / not-significant
PALETTE = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4",
           "#008300", "#4a3aa7", "#e34948", "#12a4c0", "#a66a2e"]  # categorical (CVD-safe)
DIVERGING_CMAP = "RdBu_r"    # z-score / log2FC — set center=0, vmin=-vmax
SEQUENTIAL_CMAP = "viridis"  # magnitude / -log10 p / density
```

For a dense composite, lower the font: `plt.rcParams.update({"font.size": 7,
"axes.titlesize": 8, "axes.labelsize": 7, "legend.fontsize": 6})`.

## Multi-panel discipline

This is what keeps a composite clean — every rule prevents a specific failure.

1. **One figure, independent subfigures, constrained layout.** Give **each panel its
   own subfigure** so it packs to its OWN labels: `fig = plt.figure(layout="constrained",
   figsize=(width_mm/25.4, height_mm/25.4))`, then `sfs = fig.subfigures(nrows, ncols,
   width_ratios=..., height_ratios=...)` and `ax = sfs[r, c].subplots()` per panel. Each
   subfigure runs its own `constrained_layout`, so a panel with long y-tick labels no
   longer shoves its column-neighbors' plots sideways — **axes deliberately do NOT align
   across the grid; panels sit flush with no empty bands** (a single shared
   `subplot_mosaic` gridspec, by contrast, equalizes each column's margin to its widest
   y-label and leaves a wide gap beside the short-label panels). Reserve a hair of margin
   so panel letters never clip: `fig.get_layout_engine().set(rect=(0.012, 0, 0.988,
   0.985))`. Never add `tight_layout()` or manual `subplots_adjust`. Size in mm (single
   column = 88 mm, double = 180 mm).
   - **Spanning panels**: nest subfigures — e.g. two panels on top, one spanning the
     bottom → `top = fig.subfigures(2, 1); tc = top[0].subfigures(1, 2)` (A, B in `tc[0]`,
     `tc[1]`; C in `top[1]`). One `.subplots()` per leaf subfigure.
   - **Match each panel to its plot's shape** via the subfigures' `width_ratios`/
     `height_ratios` (pin with `ax.set_box_aspect(...)` if it still deforms): scatter
     panels (volcano/PCA) near-square; for **bar / box / histogram**, protect the value
     axis in **both orientations** — horizontal (`barh`, horizontal box) kept wide,
     vertical (bar, box, hist) kept tall. Never let a neighbor squeeze that axis flat.
   - **When panels genuinely share a scale** (same y-range, meant to be read against each
     other), a shared `subplot_mosaic` with aligned axes is the right choice instead — but
     this skill usually combines heterogeneous plot types, so independent subfigures are
     the default.
2. **Fill every cell.** No empty grid slots. If a panel would be blank, span a
   neighbor across it: `[["A", "B"], ["C", "C"]]`.
3. **Legends & colorbars belong to their own panel** — a legend in that panel's
   free corner (`ax.legend(loc="lower right", frameon=False)`) or a colorbar on
   that one axis (`fig.colorbar(im, ax=ax, fraction=0.025, pad=0.02)`). Never float
   a figure-level legend in empty space or stack two in a margin; for a dot plot,
   keep only the colorbar and drop the size legend (count range → panel title).
   - **Too wide?** Thin a colorbar with `aspect=40` + `shrink=0.6` (and small
     `fraction`); tighten a legend with `handlelength=1.0`, `handletextpad=0.2`,
     `borderpad=0.2`, or fold long legends into `ncol`.
4. **Panel letters at each panel's OWN outer top-left.** Bold capitals `A, B, C…`
   (lowercase fine; never numeric), placed **to the LEFT of that panel's y-axis tick and
   axis labels** — not merged into the title. Place each letter in its **own subfigure's
   coordinate frame** — `sf.text(0.0, 1.0, letter, transform=sf.transSubfigure, ...)` (the
   helper below). The subfigure's top-left corner is always left of that panel's y-labels
   and hugs that panel, so the letter never overlaps a wide label and never floats over an
   empty band. Do **not** snap letters to a shared column-x — with independent packing that
   would drag a short-label panel's letter far from its plot (the empty-gap failure the
   user sees). The reserved margin from discipline #1 keeps edge letters in-canvas.
5. **Text must stay readable — the #1 way composites go wrong.**
   - **Point labels (volcano/scatter):** cap to **≤5** strongest hits in a small
     panel, italic ~6 pt, and repel with `adjustText`; if it is not installed,
     skip labels rather than dumping overlapping text.
   - **Long category names (pathways/gene sets):** put them on the **y-axis**
     (horizontal, one per row), never crammed/rotated on a narrow x-axis. If they
     must go on x, rotate (45° to save vertical space, or 90° when very long,
     `ha="right"` so the tick end aligns under its bar), wrap to ≤26 chars, and
     give enough width per column — crammed x-labels otherwise collide into
     unreadable text.
     **Shorten over-long names** (common with MSigDB/GO/Reactome): strip the DB
     prefix (`HALLMARK_`, `GO_`, `REACTOME_`, `KEGG_`), swap `_`→space and title-case,
     and replace verbose terms with **standard abbreviations** (e.g.
     `HALLMARK_INTERFERON_GAMMA_RESPONSE` → `IFN-γ response`); truncate with an
     ellipsis only if still too long. Keep the full name in the underlying
     data/tooltip, not on the axis tick.
   - **Size-encoded markers (dot plot):** floor the size range (`s` in ~[25,150])
     so small dots stay visible.
   - **In-cell heatmap numbers:** annotate only when the values are needed (small
     font ~4–5 pt, no decimals); otherwise omit them and let the colorbar carry the
     values.
6. **Reuse one palette and axis convention across panels** so the composite reads
   as a single system.
7. **Export vector PDF + PNG** and report the relative path.

## Panel-label helper

Place each letter at the top-left **corner of its own subfigure**. Because every panel
lives in its own tightly-packed subfigure, that corner is always left of the panel's
y-labels and hugs the panel — so letters never float over an empty band (the shared-column
failure) and never overlap a wide y-label, no matter how the panels' label widths differ:

```python
def add_panel_labels(panels, size=11):
    """Bold letter at each panel's OWN outer top-left, in its subfigure frame.

    panels : dict {letter: subfigure} — the subfigure that holds each panel's axes,
    collected as you build them (for a spanning panel, its leaf subfigure). Placing
    the letter at (0, 1) in the subfigure's coordinates puts it at that cell's top-left
    corner: always LEFT of the panel's y-labels and hugging the panel, with no
    dependence on any neighbor's label width. Reserve a hair of figure margin first
    (`fig.get_layout_engine().set(rect=(0.012, 0, 0.988, 0.985))`, discipline #1) so the
    letters of edge panels are not clipped at the canvas edge.
    """
    for letter, sf in panels.items():
        sf.text(0.0, 1.0, letter, transform=sf.transSubfigure,
                fontsize=size, fontweight="bold", va="top", ha="left")
```

Usage: collect the subfigures as you create them, e.g. `panels = {"A": sfs[0, 0],
"B": sfs[0, 1], "C": top[1]}`, then call `add_panel_labels(panels)`.

## Exporting individual panels

Every run produces **both** the individual panels (`figure1A.png`, `figure1B.png`, …)
**and** the composite (`combined_figure1.pdf` + `.png`) — this is the default output,
not an extra. A matplotlib `subfigure` cannot be saved on its own, so put each panel's
plotting body in a `draw_<letter>(ax)` function and call it twice: once onto the
composite's subfigure axis, and once onto a fresh standalone figure. One source of
truth per panel — the panels stay identical across both outputs.

```python
import os

os.makedirs("plots", exist_ok=True)

# 1) Factor each DATA panel's body into a function of a single Axes.
#    (Copy the omics-plotting recipe body here, drawing onto `ax` instead of a new figure.)
def draw_A(ax):
    ax.scatter(df["log2FC"], -np.log10(df["padj"]), s=8, c=NS)  # volcano, etc.
    ax.set_xlabel("log2 fold change"); ax.set_ylabel("-log10 FDR")

def draw_B(ax):
    ...   # PCA / box / heatmap body onto ax

def draw_C(ax):
    ...

DATA_PANELS = {"A": draw_A, "B": draw_B, "C": draw_C}
# Per-panel standalone figure size (mm) — match each plot's shape (discipline #1).
PANEL_SIZE_MM = {"A": (88, 75), "B": (88, 75), "C": (180, 70)}
# Image-only panels stay separate: keep the PNG/PDF the user supplied as their
# standalone file, and only imshow them onto the composite axis (see intro).

# 2) Composite — draw each function onto its subfigure axis, add letters, save.
panels = {"A": sfs[0, 0], "B": sfs[0, 1], "C": top[1]}
for letter, sf in panels.items():
    DATA_PANELS[letter](sf.subplots())
add_panel_labels(panels)
fig.savefig("figures/combined_figure1.pdf")
fig.savefig("figures/combined_figure1.png", dpi=300)

# 3) Individual panels — same functions onto fresh standalone figures (no letter).
for letter, draw in DATA_PANELS.items():
    w_mm, h_mm = PANEL_SIZE_MM[letter]
    fp = plt.figure(layout="constrained", figsize=(w_mm / 25.4, h_mm / 25.4))
    draw(fp.subplots())
    fp.savefig(f"figures/figure1{letter}.pdf")
    fp.savefig(f"figures/figure1{letter}.png", dpi=300)
    plt.close(fp)
```

Output files (Figure 1 with panels A, B, C):
`figures/combined_figure1.pdf`, `figures/combined_figure1.png`,
`figures/figure1A.{pdf,png}`, `figures/figure1B.{pdf,png}`, `figures/figure1C.{pdf,png}`.

Notes:
- **No panel letter on standalones** — the `A/B/C` label belongs to the composite
  frame only; a lone `figure1A.png` needs no letter baked in.
- **Size each standalone to its plot's shape** (discipline #1) via `PANEL_SIZE_MM`:
  scatter/PCA near-square, `barh`/horizontal-box wide, vertical bar/box/hist tall —
  don't reuse one size for all.
- **Legends/colorbars still belong to their own axis** (discipline #3) — since the
  body lives in `draw_<letter>`, attach them inside that function so they appear in
  both the composite and the standalone.
- **Image-only panels** are already standalone files (the user's PNG/PDF); don't
  re-export them — just reference the originals.

## Best Practices

- **One figure, one style.** Never stitch separate PNGs or call standalone plot
  functions for a composite; copy their bodies onto each subfigure's axis.
- **Workspace-relative paths only.** Save under `figures/` (create it if needed);
  never absolute paths like `/tmp` or `/home/...`.
- **Only plot data that exists.** Never invent columns, groups, or values.
- **Label every axis, keep every legend inside its panel, fill every cell.**
- **Always export both** a vector `.pdf` and a `.png` (dpi≥300) under `figures/`.

## Common Pitfalls

- **Building the whole figure as one shared `subplot_mosaic` gridspec.** It
  equalizes each column's margin to its widest y-label, so a long-label panel
  shoves neighbors sideways, leaves empty bands, and strands letters snapped to the
  shared column edge. **How to avoid:** give each panel its own `subfigure` so it
  packs to its own labels (discipline #1); reserve a shared mosaic only for panels
  that genuinely share a scale.
- **Panel letters merged into titles, snapped to a shared column-x, or clipped at
  the edge.** They then sit right of the y-labels, float far from their plot, or
  vanish off-canvas. **How to avoid:** place each letter at `(0, 1)` in its own
  subfigure frame (`transform=sf.transSubfigure`) with the `add_panel_labels`
  helper, and reserve a hair of margin (`rect=(0.012, 0, 0.988, 0.985)`,
  discipline #1) so edge letters stay in-canvas.
- **Floating or bulky legends and colorbars.** Per-plot figure-level legends
  collide in the margins, or a colorbar eats half the panel. **How to avoid:**
  attach each legend/colorbar to its own panel's axis, drop a composite dot plot's
  size legend, and thin a wide colorbar (`aspect=40`, `shrink=0.6`, small
  `fraction`) (discipline #3).
- **Value axis flattened — scatter dots merge or bars/boxes squash.** A neighbor
  steals the space the plot's value direction needs. **How to avoid:** widen or
  heighten that cell via `width_ratios` / `height_ratios` (or pin with
  `ax.set_box_aspect`) instead of shrinking the plot; only then bump marker size.
- **Cramming long category names onto a narrow x-axis.** Pathway/gene-set names
  collide into unreadable text. **How to avoid:** put long names on the horizontal
  y-axis, strip DB prefixes (`HALLMARK_`, `GO_`) and abbreviate, or rotate 90° and
  wrap to ≤26 chars with enough panel width.
- **Fixing cramped panels with manual spacing.** Adding `tight_layout()` or
  `subplots_adjust` fights `constrained_layout` and makes it worse. **How to
  avoid:** instead increase `figsize` (in mm), adjust the ratios, or lower the
  font, and let constrained layout re-space.
- **Inconsistent or unreadable text.** Over-labeled points overlap, heatmap cell
  numbers are too dense, and font sizes drift between panels. **How to avoid:** cap
  point labels to ≤5 (repel with `adjustText`, else skip); annotate heatmap cells
  only at ~4–5 pt with no decimals or drop them for the colorbar; keep the same
  font sizes across all panels, including any the user supplies (discipline #5).

## Further Reading

- Matplotlib subfigures / `Figure.subfigures` — https://matplotlib.org/stable/gallery/subplots_axes_and_figures/subfigures.html
- Matplotlib constrained layout guide — https://matplotlib.org/stable/users/explain/axes/constrained_layout_guide.html
- Matplotlib `subplot_mosaic` tutorial — https://matplotlib.org/stable/users/explain/axes/mosaic.html
- adjustText (label de-overlap) — https://github.com/Phlya/adjustText
