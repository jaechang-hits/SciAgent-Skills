---
name: omics-plotting
description: >
  omics-plotting: publication-style figure authoring for omics / bioinformatics
  results with matplotlib / seaborn. Read this before writing any plotting or
  figure code in any omics analysis — RNA-seq, proteomics, single-cell, variant,
  or database results — not only when a plot is explicitly requested: whenever an
  analysis will produce a figure, load this first and follow its recipes. Covers
  volcano, MA, expression / correlation heatmap, GSEA bar / dot plot,
  box / violin / bar / ridgeline, PCA / UMAP / t-SNE scatter, Kaplan–Meier,
  Manhattan / QQ / forest. Supplies a shared journal-ready style and copy-paste
  recipes so every figure looks like one consistent system. To combine several
  plots into ONE multi-panel composite figure, use the sibling `multipanel` skill.
license: Proprietary (HITS Inc.)
---

# omics-plotting

## Overview

When the user wants a figure, **generate it with matplotlib / seaborn**,
applying the shared style block below. The user can hand-tune
colors, fonts, or spines per plot, but unless they ask for something specific,
paste the style block and reuse the palette so a whole analysis reads as one
figure system at a glance.

This skill is self-contained: everything you need (style, palette, recipes) is
in this document.

## When to use

- The user asks for a plot / figure / chart / visualization from a results table
  or an in-memory DataFrame (DEG table, enrichment result, expression matrix,
  long-form measurements, survival table…).
- You are preparing figures for a report, a paper submission or presentation and
  want a consistent publication style.

> Combining several plots into one multi-panel composite, or assembling
> user-supplied PNG/PDF panels, is handled by the sibling `multipanel`
> skill — use this skill to draw each individual panel.

## Do NOT use for

- Interactive dashboards or web charts (this is static matplotlib output).
- 3D molecular structure rendering (that is the structure viewer, not a plot).

## Key Concepts

### One consistent figure system

The core idea is that every figure from a single analysis should look like it
came from the same publication. That is enforced by two shared objects: the
`PUB_STYLE` rcParams block (fonts, spines, DPI, editable vector text) and a fixed
`PALETTE` / directional color set (`UP`, `DOWN`, `NS`). Paste both at the top of
every plot script and map the *same* group or direction to the *same* color
across panels, so a reader can carry meaning from one figure to the next.

### Diverging vs sequential colormaps

Color encoding is not free choice. Use the **diverging** colormap
(`DIVERGING_CMAP = "RdBu_r"`, always `center=0`, `vmin=-vmax`) for signed
quantities where zero is meaningful — z-scores, log2 fold changes, correlations.
Use the **sequential** colormap (`SEQUENTIAL_CMAP = "viridis"`) for unsigned
magnitudes — densities, `-log10 p`, counts. Mixing these (a sequential map on
signed data) hides the sign and misleads the reader.

### Data shape drives figure type

Each recipe expects a specific table shape: a per-gene DEG table (volcano, MA), a
genes × samples matrix (heatmap), a samples × features matrix (PCA/UMAP), or
long-form tidy rows (box/violin/bar, ridgeline, Kaplan–Meier). Identifying the
shape first — then reading the header to confirm the real column names — is what
selects the recipe. The column names in each recipe are defaults to override, not
fixed requirements.

## Decision Framework

Pick the figure type from what the data represents and what question it answers:

```
What does the table hold?
├─ Per-gene stats (log2FC, padj)
│   ├─ emphasize significance ......... Volcano
│   └─ emphasize expression level ..... MA plot
├─ genes × samples matrix
│   ├─ show patterns/clusters ......... Clustered expression heatmap (z-score)
│   └─ show sample-sample QC .......... Correlation heatmap
├─ Enrichment / gene-set result
│   ├─ signed effect (NES) ............ GSEA bar
│   └─ ratio + size + significance .... GSEA dot plot
├─ Long-form measurements (x, y)
│   ├─ compare distributions .......... Box / Violin
│   ├─ compare means .................. Bar (with error bars)
│   └─ many groups, shape matters ..... Ridgeline
├─ samples × features (high-dim) ...... PCA / UMAP / t-SNE
└─ time-to-event + group ............. Kaplan–Meier
```

| Data you have | Question | Figure | Colormap / palette |
|---|---|---|---|
| DEG table | Which genes change, how significantly? | Volcano | `UP`/`DOWN`/`NS` |
| DEG table | Effect vs abundance | MA plot | `UP`/`DOWN`/`NS` |
| Expression matrix | Cluster structure | Clustered heatmap | diverging, center 0 |
| Expression matrix | Sample QC | Correlation heatmap | diverging, [-1, 1] |
| Enrichment result | Top pathways, direction | GSEA bar | `UP`/`DOWN` |
| Enrichment result | Ratio + significance + size | GSEA dot plot | sequential |
| Long-form | Group distributions | Box / Violin | categorical `PALETTE` |
| High-dim matrix | Global sample layout | PCA / UMAP / t-SNE | categorical `PALETTE` |
| Survival table | Group survival over time | Kaplan–Meier | categorical `PALETTE` |

## Workflow

1. **Identify the data source** — a workspace-relative CSV/TSV path or a
   DataFrame already in memory — and the **figure type** (pick from the table
   below). If the required columns are unclear, inspect the table's header first.
2. **Write one python script**: paste the style block, load the data,
   draw the plot with the matching recipe, and save to a **workspace-relative**
   path under `figures/`.
3. **Report the saved path** back to the user (and reference it in any report /
   deck by that relative path, e.g. `![Volcano](figures/volcano.png)`).

## Shared style — paste at the top of every plot script

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
plt.rcParams.update(PUB_STYLE)   # or: with plt.rc_context(PUB_STYLE): ...

# Palette — reuse the SAME colors across every panel of an analysis
UP, DOWN, NS = "#d73721", "#204897", "#d9d9d9"   # up / down / not-significant
PALETTE = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4",
           "#008300", "#4a3aa7", "#e34948", "#12a4c0", "#a66a2e"]  # categorical (CVD-safe order)
GROUP_COLORS = {"Group1": "#204897", "Group2": "#e34948", "Group3": "#E7B800"}
DIVERGING_CMAP = "RdBu_r"    # z-score / log2FC heatmaps — set center=0, vmin=-vmax
SEQUENTIAL_CMAP = "viridis"  # magnitude / -log10 p / density
```

## Multi-panel / composite figures

For combining several plots into **one** multi-panel journal figure (panels A,
B, C…), or assembling already-rendered PNG/PDF panels the user supplies, use the
sibling **`multipanel`** skill — it owns the composition discipline
(one `subplot_mosaic` canvas, per-panel legends, correctly placed panel letters,
text-legibility rules, image assembly). Draw each panel with the single-panel
recipes below, then compose per that skill. The recipes here each build their
*own* figure, so do not call them directly for a composite — copy the recipe
**body** onto a mosaic axis as `multipanel` describes.

## Plot catalogue

Pick the recipe by figure type. Columns listed are the **defaults** — override
the column-name variables to match the actual table.

| Figure | Input shape | Key columns (defaults) |
|---|---|---|
| Volcano | DEG table | `log2FoldChange`, `padj`; optional label column |
| MA plot | DEG table | `baseMean`, `log2FoldChange`, `padj` |
| Expression heatmap | genes × samples matrix | numeric matrix, optional `index_col` |
| Correlation heatmap | samples × features (numeric) | all numeric columns |
| GSEA bar plot | enrichment result | `Term`, `NES`, `FDR q-val` |
| GSEA dot plot | enrichment result | `Term`, `GeneRatio`, `Count`, `Adjusted P-value` |
| Box / Violin / Bar | long-form | `x` (category), `y` (numeric), optional `hue` |
| Ridgeline | long-form | numeric `x`, categorical `group` |
| PCA / UMAP / t-SNE | samples × features | numeric features + optional `group` |
| Kaplan–Meier | survival table | `time`, `event`, `group` |
| Manhattan | GWAS summary stats | `CHR`, `BP`, `P` |
| QQ plot | p-value vector | `P` |
| Forest | effect + CI table | `label`, `estimate`, `ci_low`, `ci_high` |

## Recipes

Each is a full python script body. Adjust column names, thresholds, and the
save path. All save under `figures/`.

**Volcano** (`-log10 p` vs `log2` fold change):

```python
import numpy as np, pandas as pd
df = pd.read_csv("deg_results.csv").dropna(subset=["log2FoldChange", "padj"])
fc, p = df["log2FoldChange"].to_numpy(float), df["padj"].to_numpy(float)
nlp = -np.log10(np.clip(p, 1e-300, None))
fc_t, p_t = 0.58, 0.05
up, down = (fc >= fc_t) & (p < p_t), (fc <= -fc_t) & (p < p_t)
ns = ~(up | down)
fig, ax = plt.subplots(figsize=(7, 6))
ax.scatter(fc[ns], nlp[ns], c=NS, s=12, alpha=0.5, edgecolors="none", rasterized=True, label=f"NS ({ns.sum()})")
ax.scatter(fc[down], nlp[down], c=DOWN, s=18, alpha=0.85, edgecolors="none", label=f"Down ({down.sum()})")
ax.scatter(fc[up], nlp[up], c=UP, s=18, alpha=0.85, edgecolors="none", label=f"Up ({up.sum()})")
for v in (fc_t, -fc_t): ax.axvline(v, ls="--", lw=0.8, color="0.5")
ax.axhline(-np.log10(p_t), ls="--", lw=0.8, color="0.5")
lab = (df["gene"] if "gene" in df else pd.Series(df.index)).astype(str).to_numpy()
sig = np.where(up | down)[0]
top = sig[np.argsort(nlp[sig])[::-1][:10]]      # standalone: top ~10; composite panel: cut to <=5
try:                                            # repel labels so they never overlap
    from adjustText import adjust_text
    texts = [ax.text(fc[i], nlp[i], lab[i], fontsize=7) for i in top]
    adjust_text(texts, ax=ax, expand=(1.3, 1.6),
                arrowprops=dict(arrowstyle="-", color="0.6", lw=0.5))
except ImportError:                             # no adjustText -> label fewer, with an offset
    for i in top[:5]:
        ax.annotate(lab[i], (fc[i], nlp[i]), xytext=(6, 6), textcoords="offset points",
                    fontsize=7, ha="left", va="bottom")
ax.set_xlabel(r"$\log_{2}$ fold change"); ax.set_ylabel(r"$-\log_{10}$ padj")
ax.set_title("Volcano plot"); ax.legend(loc="upper right", markerscale=1.4)
fig.tight_layout(); fig.savefig("figures/volcano.png")
```

**MA plot** (`log2` fold change vs mean expression; columns `baseMean`, `log2FoldChange`, optional `padj`):

```python
import numpy as np, pandas as pd
df = pd.read_csv("deg_results.csv").dropna(subset=["baseMean", "log2FoldChange"])
x = np.log10(df["baseMean"].to_numpy(float) + 1)
fc = df["log2FoldChange"].to_numpy(float)
sig = (df["padj"].to_numpy(float) < 0.05) if "padj" in df else np.zeros(len(df), bool)
fig, ax = plt.subplots(figsize=(7, 5))
ax.scatter(x[~sig], fc[~sig], c=NS, s=10, alpha=0.5, edgecolors="none", rasterized=True, label="NS")
ax.scatter(x[sig], fc[sig], c=UP, s=14, alpha=0.85, edgecolors="none", label=f"padj<0.05 ({int(sig.sum())})")
ax.axhline(0, color="0.4", lw=0.8)
ax.set_xlabel(r"$\log_{10}$(mean norm. count + 1)"); ax.set_ylabel(r"$\log_{2}$ fold change")
ax.set_title("MA plot"); ax.legend(loc="upper right")
fig.tight_layout(); fig.savefig("figures/ma.png")
```

**Clustered expression heatmap** (z-scored, seaborn `clustermap`):

```python
import seaborn as sns, pandas as pd
mat = pd.read_csv("expression.csv", index_col=0).select_dtypes("number")
g = sns.clustermap(mat, z_score=0, cmap=DIVERGING_CMAP, center=0,
                   figsize=(8, 8), xticklabels=True, yticklabels=mat.shape[0] <= 60,
                   cbar_kws={"label": "z-score"})
g.ax_col_dendrogram.set_title("Expression heatmap", pad=12)
g.figure.savefig("figures/heatmap.png")
```

**Correlation heatmap** (sample QC):

```python
import numpy as np, seaborn as sns, pandas as pd
corr = pd.read_csv("expr.csv", index_col=0).select_dtypes("number").corr(method="pearson")
mask = np.triu(np.ones_like(corr, dtype=bool), k=1)
fig, ax = plt.subplots(figsize=(7, 6))
sns.heatmap(corr, mask=mask, cmap=DIVERGING_CMAP, vmin=-1, vmax=1, center=0,
            annot=True, # if the n>20 samples then set annot=False
            fmt=".2f", annot_kws={"size": 7}, square=True,
            linewidths=0.5, 
            cbar_kws={"label": "Pearson r", "shrink": 0.7}, 
            ax=ax)
ax.set_title("Sample correlation"); fig.tight_layout(); fig.savefig("figures/corr.png")

```

**GSEA bar** (top gene sets, colored by direction):

```python
import pandas as pd
df = pd.read_csv("gsea.csv").dropna(subset=["Term", "NES"]).copy()
df = df.assign(_a=df["NES"].abs()).nlargest(15, "_a").sort_values("NES")
colors = [UP if v >= 0 else DOWN for v in df["NES"]]
fig, ax = plt.subplots(figsize=(7, 6))
ax.barh(df["Term"].astype(str), df["NES"], color=colors)
ax.axvline(0, color="0.4", lw=0.8); ax.set_xlabel("NES"); ax.set_title("GSEA")
fig.tight_layout(); fig.savefig("figures/gsea_bar.png")
```

**GSEA dot plot** (clusterProfiler-style; `GeneRatio` may be `"k/n"`):

```python
import numpy as np, pandas as pd
from matplotlib.cm import ScalarMappable
from matplotlib.colors import Normalize
df = pd.read_csv("enrichment.csv").dropna(subset=["Term", "GeneRatio", "Adjusted P-value"]).copy()
df["_ratio"] = df["GeneRatio"].map(lambda v: float(v.split("/")[0]) / float(v.split("/")[1]) if isinstance(v, str) and "/" in v else float(v))
df["_nlp"] = -np.log10(np.clip(df["Adjusted P-value"].astype(float), 1e-300, None))
df = df.nlargest(15, "_nlp").sort_values("_ratio")
cnt = df["Count"].to_numpy(float); sizes = 40 + 220 * (cnt - cnt.min()) / (np.ptp(cnt) + 1e-9)
norm = Normalize(df["_nlp"].min(), df["_nlp"].max())
fig, ax = plt.subplots(figsize=(7, 6))
ax.scatter(df["_ratio"], df["Term"].astype(str), s=sizes, c=df["_nlp"], cmap=SEQUENTIAL_CMAP, norm=norm, edgecolors="0.3", linewidths=0.5, zorder=3)
ax.grid(axis="y", ls=":", color="0.8", zorder=0); ax.set_xlabel("Gene ratio"); ax.set_title("Enrichment")
cb = fig.colorbar(ScalarMappable(norm=norm, cmap=SEQUENTIAL_CMAP), ax=ax, shrink=0.6, pad=0.02)
cb.set_label(r"$-\log_{10}$ adj. $p$"); fig.tight_layout(); fig.savefig("figures/dotplot.png")
```

**Box plot** (long-form, jittered points, optional 2-group test):

```python
import seaborn as sns, pandas as pd
from scipy import stats
df = pd.read_csv("measurements.csv"); x, y = "group", "value"
fig, ax = plt.subplots(figsize=(6, 5))
sns.boxplot(data=df, x=x, y=y, hue=x, palette=PALETTE[:df[x].nunique()], legend=False, fliersize=0, width=0.6, ax=ax)
sns.stripplot(data=df, x=x, y=y, color="0.25", size=3, alpha=0.6, ax=ax)
lv = list(df[x].dropna().unique())
if len(lv) == 2:  # optional significance star
    a, b = (df.loc[df[x] == l, y].dropna() for l in lv)
    p = stats.mannwhitneyu(a, b, alternative="two-sided").pvalue
    star = "****" if p < 1e-4 else "***" if p < 1e-3 else "**" if p < 1e-2 else "*" if p < 0.05 else "ns"
    ymax = df[y].max(); h = (ymax - df[y].min()) * 0.08
    ax.plot([0, 0, 1, 1], [ymax + h, ymax + 2*h, ymax + 2*h, ymax + h], lw=1.0, c="0.2")
    ax.text(0.5, ymax + 2*h, star, ha="center", va="bottom")
ax.set_title(f"{y} by {x}"); fig.tight_layout(); fig.savefig("figures/box.png")
```

For **violin** swap `sns.boxplot` → `sns.violinplot(..., inner="box", cut=0)`;
for **bar of the mean** use `sns.barplot(..., errorbar="se", capsize=0.15)`.

**Grouped embedding scatter (PCA / UMAP / t-SNE / factor scatter):** (samples × features + `group` column):

```python
import numpy as np, pandas as pd

def scatter_emb(ax, emb, grp, xi=0, yi=1, ev=None, name="PC", centered=True):
    """emb: (n_samples, n_comp). ev: variance explained % or None. UMAP/t-SNE -> centered=False."""
    emb, grp = np.asarray(emb), pd.Series(grp).astype(str)
    for g in [g for g in GROUP_COLORS if g in set(grp)]:     
        m = (grp == g).to_numpy()
        ax.scatter(emb[m, xi], emb[m, yi], c=GROUP_COLORS[g], s=45, alpha=.9,
                   edgecolors="white", linewidths=.4, label=g)
    if centered:                   # PC/factor are 0-centered and equally spaced
        ax.axhline(0, lw=.5, ls="--", c="0.75"); ax.axvline(0, lw=.5, ls="--", c="0.75")
        ax.set_aspect("equal", adjustable="datalim")
    lab = lambda i: f"{name}{i+1}" + (f" ({ev[i]:.1f}%)" if ev is not None else "")
    ax.set_xlabel(lab(xi)); ax.set_ylabel(lab(yi))
    ax.spines[["top", "right"]].set_visible(False); ax.legend(frameon=False, fontsize=7)
```
FOR **PCA**: samples × features + 'group' column 

``` python
from sklearn.decomposition import PCA

df = pd.read_csv("samples_features.csv", index_col=0)    
grp = df.pop("group") if "group" in df else pd.Series("all", index=df.index)
X = df.select_dtypes("number")
p = PCA(n_components=min(5, *X.shape)).fit(X) 
emb, ev = p.transform(X), p.explained_variance_ratio_ * 100
fig, ax = plt.subplots(figsize=(70/25.4, 70/25.4), constrained_layout=True)
scatter_emb(ax, emb, grp, 0, 1, ev, "PC")
fig.savefig("figures/pca.png", dpi=400)
```

FOR **UMAP/t-SNE**: no ev

```python
import umap           # t-SNE: from sklearn.manifold import TSNE

emb = umap.UMAP(n_neighbors=15, min_dist=0.1).fit_transform(X)   # TSNE(perplexity=30).fit_transform(X)
fig, ax = plt.subplots(figsize=(70/25.4, 70/25.4), constrained_layout=True)
scatter_emb(ax, emb, grp, name="UMAP", centered=False)    # 원점·축 스케일에 의미 없음
fig.savefig("figures/umap.png", dpi=400)
```

FOR **factor scatter**:

```python
Z  = pd.DataFrame(model.get_factors()["group1"], index=meta.index)
r2 = model.get_variance_explained()["r2_per_factor"]["group1"]    # view × factor
ev = r2.sum(axis=0).to_numpy()                           
keep = [i for i, v in enumerate(ev) if v >= 5.0]        
fig, ax = plt.subplots(figsize=(70/25.4, 70/25.4), constrained_layout=True)
scatter_emb(ax, Z, meta["condition"], keep[0], keep[1], ev, "Factor")
fig.savefig("figures/factor_scatter.png", dpi=400)
```

**Kaplan–Meier** (survival by group):

```python
import pandas as pd
from lifelines import KaplanMeierFitter
df = pd.read_csv("survival.csv"); kmf = KaplanMeierFitter()
fig, ax = plt.subplots(figsize=(6, 5))
for i, g in enumerate(sorted(df["group"].unique())):
    m = df["group"] == g
    kmf.fit(df.loc[m, "time"], df.loc[m, "event"], label=str(g))
    kmf.plot_survival_function(ax=ax, color=PALETTE[i % len(PALETTE)], ci_show=True)
ax.set_xlabel("Time"); ax.set_ylabel("Survival probability"); ax.set_ylim(0, 1.02)
ax.set_title("Kaplan–Meier"); fig.tight_layout(); fig.savefig("figures/km.png")
```

**Manhattan** (GWAS summary stats; columns `CHR`, `BP`, `P`):

```python
import numpy as np, pandas as pd
df = pd.read_csv("gwas.csv").dropna(subset=["CHR", "BP", "P"]).copy()
df["CHR"] = df["CHR"].astype(str)
chrom_order = sorted(df["CHR"].unique(), key=lambda c: (len(c), c))
df["_nlp"] = -np.log10(np.clip(df["P"].astype(float), 1e-300, None))
offset, xticks, ticklabels, xpos = 0.0, [], [], np.zeros(len(df))  # lay chromosomes end-to-end
for c in chrom_order:
    m = (df["CHR"] == c).to_numpy()
    bp = df.loc[m, "BP"].astype(float)
    xpos[m] = bp + offset
    xticks.append(offset + bp.median()); ticklabels.append(c)
    offset = xpos[m].max() + 1
fig, ax = plt.subplots(figsize=(180/25.4, 70/25.4), constrained_layout=True)
for i, c in enumerate(chrom_order):
    m = (df["CHR"] == c).to_numpy()
    ax.scatter(xpos[m], df["_nlp"].to_numpy()[m], s=6, c=["#2a78d6", "#9fb3c8"][i % 2], edgecolors="none")
ax.axhline(-np.log10(5e-8), color=UP, lw=0.8, ls="--")   # genome-wide significance
ax.set_xticks(xticks); ax.set_xticklabels(ticklabels, fontsize=6)
ax.set_xlabel("Chromosome"); ax.set_ylabel(r"$-\log_{10} p$"); ax.set_title("Manhattan")
fig.savefig("figures/manhattan.png", dpi=400)
```

**QQ plot** (p-value calibration; reports genomic inflation λ):

```python
import numpy as np, pandas as pd
from scipy import stats
p = pd.read_csv("gwas.csv")["P"].dropna().astype(float).to_numpy()
p = np.clip(np.sort(p), 1e-300, 1.0)
obs = -np.log10(p)
exp = -np.log10((np.arange(1, len(p) + 1) - 0.5) / len(p))
lam = np.median(stats.chi2.isf(p, 1)) / stats.chi2.isf(0.5, 1)   # genomic inflation
fig, ax = plt.subplots(figsize=(70/25.4, 70/25.4), constrained_layout=True)
ax.scatter(exp, obs, s=6, c="#2a78d6", edgecolors="none")
lim = float(max(exp.max(), obs.max()))
ax.plot([0, lim], [0, lim], color="0.4", lw=0.8, ls="--")
ax.set_xlabel(r"Expected $-\log_{10} p$"); ax.set_ylabel(r"Observed $-\log_{10} p$")
ax.set_title(f"QQ (λ = {lam:.3f})"); fig.savefig("figures/qq.png", dpi=400)
```

**Forest** (effect size ± 95% CI per study/variant; columns `label`, `estimate`, `ci_low`, `ci_high`):

```python
import pandas as pd
df = pd.read_csv("effects.csv").iloc[::-1].reset_index(drop=True)  # first row at top
y = list(range(len(df)))
fig, ax = plt.subplots(figsize=(90/25.4, max(60, 14 * len(df)) / 25.4), constrained_layout=True)
ax.errorbar(df["estimate"], y,
            xerr=[df["estimate"] - df["ci_low"], df["ci_high"] - df["estimate"]],
            fmt="s", color="#204897", ecolor="0.4", capsize=2, markersize=4, lw=0.8)
ax.axvline(1.0, color=UP, lw=0.8, ls="--")   # null: OR/HR=1 (use 0.0 for log-scale beta)
ax.set_yticks(y); ax.set_yticklabels(df["label"])
ax.set_xlabel("Effect size (95% CI)"); ax.set_title("Forest")
fig.savefig("figures/forest.png", dpi=400)
```

## Best Practices

- **Only plot data that exists.** Never invent columns, groups, or values; if a
  needed column is missing, inspect the header and ask or adapt — do not fabricate.
- **Workspace-relative paths only.** Save under `figures/` (create it if needed);
  never write to absolute paths like `/tmp` or `/home/...`.
- **Reuse the palette across a figure set** so related panels share colors for
  the same group / direction. Use the diverging colormap (centered at 0) for
  z-scores and log2FC; the sequential colormap for magnitudes and `-log10 p`.
  However, if the user explicitly requests a different color, use it.
- **Label axes and give a real title.** Include units, group `n`, and thresholds
  where relevant (e.g. volcano cutoff lines).
- For vector / print output, also save a `.pdf` (`fig.savefig("figures/x.pdf")`);
  text stays editable because `pdf.fonttype=42` / `svg.fonttype="none"`.

## Common Pitfalls

- **Wrong colormap family for the data.** A sequential map on signed values
  (log2FC, z-score) hides the sign. **How to avoid:** use the diverging colormap
  with `center=0, vmin=-vmax` for signed data, and reserve the sequential colormap
  for unsigned magnitudes only.
- **Columns don't match the recipe (`KeyError`).** The recipe's default column
  names rarely match the real table. **How to avoid:** read the header first and
  override the `*_col` / `x` / `y` variables to the real names; never invent a
  missing column — pick a figure the data supports instead.
- **Overcrowded / overlapping labels.** Annotating every volcano point, or
  cramming long pathway names on an x-axis, produces unreadable overlap. **How to
  avoid:** label only the top ~10 by `|log2FC| × -log10 p` (≤5 inside a composite
  panel) and repel with `adjustText`; move long category names to a horizontal
  y-axis, or rotate 90° and wrap to ≤26 chars; skip labels rather than dumping
  colliding text.
- **Dot / bubble markers all one size or too small.** A size encoding that maps to
  invisible dots carries no information. **How to avoid:** floor the size mapping
  (`s` in ~[25, 220]) so the smallest stays visible, and confirm the size column
  actually varies.
- **Legend or clustermap title collides.** A legend sits on top of the data, or a
  `clustermap` title is cropped. **How to avoid:** move the legend to a free corner
  or outside the axes (or shrink its font); put a clustermap title on
  `g.ax_col_dendrogram`, not a figure `suptitle`.
- **Empty / all-NS plot.** Nothing passes the threshold because the columns or
  scale are wrong. **How to avoid:** confirm the p-value and fold-change columns
  are numeric and that thresholds match the data scale (adjusted vs raw p).

For multi-panel composition issues (panel letters misplaced, legends floating in
margins, panels colliding), see the `multipanel` skill.

## Further Reading

- Matplotlib documentation — https://matplotlib.org/stable/
- Seaborn documentation — https://seaborn.pydata.org/
- Wong, "Points of view: Color blindness", Nature Methods (2011) — https://www.nature.com/articles/nmeth.1618
- ColorBrewer diverging/sequential palettes — https://colorbrewer2.org/
