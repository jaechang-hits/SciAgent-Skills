---
name: "plotly-interactive-plots"
description: "Interactive scientific visualization with Plotly. Two APIs: plotly.express (px) for one-liner DataFrame plots, plotly.graph_objects (go) for trace-level control. 40+ chart types with hover, zoom, pan, animation. Exports HTML or static PNG/SVG/PDF via kaleido. Use for volcano plots with gene hover, dose-response dashboards, expression heatmaps, 3D molecular views. Use seaborn for stats; matplotlib for publication figures."
license: "MIT"
---

# Plotly Interactive Plots

## Overview

Plotly is a Python library for producing interactive, web-ready figures backed by HTML and JavaScript. It exposes two complementary APIs: `plotly.express` (px) provides a high-level, DataFrame-oriented interface for generating common chart types in one line, while `plotly.graph_objects` (go) offers fine-grained control over every trace, axis, and layout property. Figures are fully interactive by default — supporting hover tooltips, zoom, pan, and click events — and can be embedded in web pages, Jupyter notebooks, or built into web applications using the Dash framework.

## When to Use

- You need hover tooltips that display gene names, p-values, or sample metadata without cluttering the static figure.
- You are building a multi-panel interactive dashboard for dose-response curves, patient cohorts, or multi-condition comparisons.
- You want to share figures as self-contained HTML files that non-programmers can explore in a browser.
- You need 3D scatter or surface plots for structural biology, conformational landscapes, or PCA of high-dimensional data.
- You are creating heatmaps of gene expression or correlation matrices where users need to zoom into specific gene clusters.
- You require animation frames to show time-series or treatment-response trajectories.
- Use `seaborn` instead when you need automatic statistical aggregation (confidence intervals, regression fits) with minimal code.
- Use `matplotlib` when you need fine-grained control over every axis element for print-ready publication figures at exact journal specifications.

## Prerequisites

- **Python packages**: `plotly`, `kaleido` (static image export), `pandas`, `numpy`
- **Data requirements**: pandas DataFrames or NumPy arrays; long-form (tidy) data works best with `px`
- **Environment**: Jupyter Lab/Notebook (inline rendering), or save as HTML for browser display

```bash
pip install plotly kaleido pandas numpy
```

For Jupyter Lab inline rendering (if not automatic):

```bash
pip install "jupyterlab>=3" ipywidgets
```

## Quick Start

```python
import plotly.express as px
import pandas as pd

# Gene expression scatter with hover info
df = pd.DataFrame({
    "log2FC": [-3.1, 0.2, 1.8, 2.5, -0.5, 4.1],
    "neg_log10_padj": [8.2, 0.4, 2.1, 6.8, 0.1, 9.3],
    "gene": ["BRCA1", "MYC", "TP53", "EGFR", "CDKN1A", "KRAS"],
    "significance": ["sig", "ns", "ns", "sig", "ns", "sig"],
})

fig = px.scatter(
    df, x="log2FC", y="neg_log10_padj",
    color="significance", hover_name="gene",
    title="Volcano Plot — Treatment vs Control",
)
fig.show()
```

## Core API

### Module 1: px Scatter and Line — Relational Plots

`px.scatter()` and `px.line()` map DataFrame columns to visual encodings (color, symbol, size) and automatically populate hover tooltips from `hover_data`.

```python
import plotly.express as px
import pandas as pd
import numpy as np

# Dose-response scatter: color by drug, symbol by cell line
np.random.seed(42)
df = pd.DataFrame({
    "dose_uM": np.tile([0.01, 0.1, 1, 10, 100], 4),
    "viability": np.clip(np.random.normal(
        [100, 90, 70, 40, 10] * 4, 5), 0, 110),
    "drug": ["DrugA"] * 5 + ["DrugA"] * 5 + ["DrugB"] * 5 + ["DrugB"] * 5,
    "cell_line": ["HCT116"] * 10 + ["MCF7"] * 10,
    "replicate": np.tile([1, 2, 3, 4, 5], 4),
})

fig = px.scatter(
    df, x="dose_uM", y="viability",
    color="drug", symbol="cell_line",
    log_x=True,
    hover_data={"replicate": True, "dose_uM": ":.2f"},
    labels={"viability": "Cell Viability (%)", "dose_uM": "Dose (µM)"},
    title="Dose-Response by Drug and Cell Line",
)
fig.show()
print(f"Figure has {len(fig.data)} traces")
```

```python
# Time-course gene expression line plot
time_df = pd.DataFrame({
    "hour": list(range(0, 25, 4)) * 3,
    "expression": [1.0, 1.8, 3.2, 4.5, 3.8, 2.1, 1.2,
                   1.0, 2.5, 5.1, 6.8, 5.5, 3.2, 1.8,
                   1.0, 1.1, 1.0, 1.2, 1.1, 1.0, 0.9],
    "gene": ["MYC"] * 7 + ["EGFR"] * 7 + ["GAPDH"] * 7,
})

fig = px.line(
    time_df, x="hour", y="expression",
    color="gene", markers=True,
    labels={"expression": "Relative Expression (log2)", "hour": "Time (h)"},
    title="Time-Course Gene Expression",
)
fig.update_traces(line=dict(width=2.5), marker=dict(size=8))
fig.show()
```

### Module 2: px Statistical Plots — Distributions and Categories

`px.box()`, `px.violin()`, `px.histogram()`, and `px.strip()` produce publication-ready distribution summaries with built-in grouping.

```python
import plotly.express as px
import pandas as pd
import numpy as np

# Violin + strip overlay: expression by cell type
np.random.seed(7)
n = 60
cell_data = pd.DataFrame({
    "expression": np.concatenate([
        np.random.normal(4.2, 0.8, n),
        np.random.normal(6.5, 1.2, n),
        np.random.normal(2.8, 0.6, n),
    ]),
    "cell_type": ["T cell"] * n + ["B cell"] * n + ["NK cell"] * n,
    "patient_id": np.tile([f"P{i:02d}" for i in range(1, 11)], 18),
})

fig = px.violin(
    cell_data, x="cell_type", y="expression",
    color="cell_type", box=True, points="all",
    hover_data=["patient_id"],
    labels={"expression": "CD3E Expression (log2 CPM)"},
    title="CD3E Expression Across Cell Types",
)
fig.update_traces(jitter=0.3, pointpos=-1.5)
fig.show()
print(f"Cells per type: {cell_data.groupby('cell_type').size().to_dict()}")
```

```python
# Histogram with rug: distribution of fold changes
fc_df = pd.DataFrame({
    "log2FC": np.concatenate([
        np.random.normal(0.1, 0.8, 500),   # not DE genes
        np.random.normal(2.5, 0.4, 50),    # upregulated
        np.random.normal(-2.3, 0.4, 40),   # downregulated
    ]),
    "category": ["background"] * 500 + ["up"] * 50 + ["down"] * 40,
})

fig = px.histogram(
    fc_df, x="log2FC", color="category",
    nbins=60, barmode="overlay", opacity=0.7,
    marginal="rug",
    labels={"log2FC": "log2 Fold Change", "count": "Gene Count"},
    title="Distribution of Fold Changes (DESeq2 Results)",
    color_discrete_map={"background": "gray", "up": "crimson", "down": "steelblue"},
)
fig.show()
```

### Module 3: px Heatmap and Matrix — Gene Expression and Correlations

`px.imshow()` renders 2D arrays or DataFrames as color-encoded matrices, ideal for expression heatmaps and correlation matrices.

```python
import plotly.express as px
import pandas as pd
import numpy as np

# Gene expression heatmap (genes × samples)
np.random.seed(12)
genes = [f"Gene_{g}" for g in ["BRCA1", "TP53", "EGFR", "MYC", "KRAS",
                                 "CDKN1A", "RB1", "PTEN", "VHL", "APC"]]
samples = [f"S{i:02d}" for i in range(1, 9)]

expr_matrix = pd.DataFrame(
    np.random.normal(0, 1.5, (10, 8)) +
    np.array([2, -1, 3, -2, 1, -3, 0, 2, -1, 3]).reshape(-1, 1),
    index=genes, columns=samples,
)

fig = px.imshow(
    expr_matrix,
    color_continuous_scale="RdBu_r",
    color_continuous_midpoint=0,
    aspect="auto",
    labels={"color": "log2 Expression (z-score)"},
    title="Gene Expression Heatmap",
)
fig.update_xaxes(side="top")
fig.update_layout(width=600, height=500)
fig.show()
print(f"Heatmap shape: {expr_matrix.shape} (genes × samples)")
```

```python
# Correlation matrix heatmap
from itertools import combinations

markers = ["IL6", "TNF", "CXCL10", "IFNg", "IL10", "IL1B", "CCL2", "IL17A"]
np.random.seed(3)
raw = np.random.multivariate_normal(
    mean=np.zeros(8),
    cov=np.eye(8) * 0.3 + 0.7,
    size=80,
)
corr_df = pd.DataFrame(raw, columns=markers).corr()

fig = px.imshow(
    corr_df,
    color_continuous_scale="RdBu_r",
    color_continuous_midpoint=0,
    zmin=-1, zmax=1,
    text_auto=".2f",
    title="Cytokine Correlation Matrix (n=80 patients)",
)
fig.update_traces(textfont_size=10)
fig.show()
```

### Module 4: go Graph Objects — Full Trace Control

`plotly.graph_objects` provides fine-grained access to every trace property: marker symbols, error bars, fill areas, and multi-trace layouts. Essential when `px` lacks the flexibility you need.

```python
import plotly.graph_objects as go
import numpy as np

# Volcano plot built from scratch with go.Scatter
np.random.seed(99)
n_genes = 5000
log2fc = np.random.normal(0, 1.2, n_genes)
pval = np.random.uniform(0, 1, n_genes) ** 2  # skew toward low p-values
neg_log10_p = -np.log10(pval + 1e-300)
gene_names = [f"Gene_{i:04d}" for i in range(n_genes)]

# Classify genes
sig_mask = (np.abs(log2fc) > 1.5) & (neg_log10_p > 3)
up_mask = sig_mask & (log2fc > 0)
down_mask = sig_mask & (log2fc < 0)
ns_mask = ~sig_mask

fig = go.Figure()

# Non-significant background
fig.add_trace(go.Scatter(
    x=log2fc[ns_mask], y=neg_log10_p[ns_mask],
    mode="markers",
    name="Not significant",
    marker=dict(color="lightgray", size=4, opacity=0.5),
    text=[gene_names[i] for i in np.where(ns_mask)[0]],
    hovertemplate="<b>%{text}</b><br>log2FC: %{x:.2f}<br>-log10(p): %{y:.2f}<extra></extra>",
))

# Upregulated
fig.add_trace(go.Scatter(
    x=log2fc[up_mask], y=neg_log10_p[up_mask],
    mode="markers",
    name=f"Up ({up_mask.sum()} genes)",
    marker=dict(color="crimson", size=7, opacity=0.8),
    text=[gene_names[i] for i in np.where(up_mask)[0]],
    hovertemplate="<b>%{text}</b><br>log2FC: %{x:.2f}<br>-log10(p): %{y:.2f}<extra></extra>",
))

# Downregulated
fig.add_trace(go.Scatter(
    x=log2fc[down_mask], y=neg_log10_p[down_mask],
    mode="markers",
    name=f"Down ({down_mask.sum()} genes)",
    marker=dict(color="steelblue", size=7, opacity=0.8),
    text=[gene_names[i] for i in np.where(down_mask)[0]],
    hovertemplate="<b>%{text}</b><br>log2FC: %{x:.2f}<br>-log10(p): %{y:.2f}<extra></extra>",
))

# Threshold lines
fig.add_hline(y=3, line_dash="dash", line_color="black", line_width=1)
fig.add_vline(x=1.5, line_dash="dash", line_color="black", line_width=1)
fig.add_vline(x=-1.5, line_dash="dash", line_color="black", line_width=1)

fig.update_layout(
    title="Volcano Plot (Treatment vs Control, n=5000 genes)",
    xaxis_title="log2 Fold Change",
    yaxis_title="-log10(adjusted p-value)",
    legend=dict(x=0.01, y=0.99),
    width=750, height=550,
)
fig.show()
print(f"Up: {up_mask.sum()}, Down: {down_mask.sum()}, NS: {ns_mask.sum()}")
```

```python
# Bar chart with error bars: mean ± SEM per treatment group
groups = ["Vehicle", "DrugA 1µM", "DrugA 10µM", "DrugB 1µM", "DrugB 10µM"]
means = [100.0, 82.3, 54.7, 91.2, 68.5]
sems = [3.2, 4.1, 3.8, 3.5, 4.7]

fig = go.Figure(go.Bar(
    x=groups, y=means,
    error_y=dict(type="data", array=sems, visible=True),
    marker_color=["gray", "lightsalmon", "crimson", "lightblue", "steelblue"],
    hovertemplate="%{x}<br>Mean: %{y:.1f}%<br>SEM: ±%{error_y.array:.1f}%<extra></extra>",
))

fig.update_layout(
    title="Cell Viability by Treatment (Mean ± SEM, n=6)",
    yaxis_title="Viability (%)", yaxis_range=[0, 120],
    xaxis_title="Treatment Group",
    showlegend=False,
)
fig.show()
```

### Module 5: 3D and Specialized Charts

Plotly supports 3D scatter, surface plots, parallel coordinates, and treemaps — chart types unavailable in seaborn or standard matplotlib.

```python
import plotly.express as px
import numpy as np
import pandas as pd

# 3D PCA scatter: cell clusters in embedding space
np.random.seed(42)
n_per_cluster = 80
cluster_centers = {"T cell": [3, 2, 1], "B cell": [-3, 1, 2], "Monocyte": [0, -3, -1]}

records = []
for ctype, center in cluster_centers.items():
    coords = np.random.normal(center, 0.8, (n_per_cluster, 3))
    for row in coords:
        records.append({
            "PC1": row[0], "PC2": row[1], "PC3": row[2],
            "cell_type": ctype,
            "score": np.random.uniform(0.5, 1.0),
        })

pca_df = pd.DataFrame(records)

fig = px.scatter_3d(
    pca_df, x="PC1", y="PC2", z="PC3",
    color="cell_type", size="score", opacity=0.7,
    hover_data={"score": ":.3f"},
    title="3D PCA — Single-Cell Transcriptomics",
)
fig.update_traces(marker=dict(sizeref=0.04))
fig.show()
print(f"Total cells: {len(pca_df)}, clusters: {pca_df['cell_type'].nunique()}")
```

```python
import plotly.graph_objects as go
import numpy as np
import pandas as pd

# Parallel coordinates: multi-parameter drug screen
np.random.seed(5)
n_compounds = 200
drug_df = pd.DataFrame({
    "MW": np.random.normal(380, 60, n_compounds),
    "logP": np.random.uniform(-1, 6, n_compounds),
    "HBA": np.random.randint(2, 10, n_compounds),
    "HBD": np.random.randint(0, 6, n_compounds),
    "IC50_nM": np.random.lognormal(4, 1.5, n_compounds),
    "selectivity": np.random.uniform(1, 100, n_compounds),
})

fig = px.parallel_coordinates(
    drug_df,
    color="IC50_nM",
    color_continuous_scale="RdYlGn_r",
    dimensions=["MW", "logP", "HBA", "HBD", "IC50_nM", "selectivity"],
    labels={
        "MW": "MW (Da)", "logP": "logP",
        "HBA": "H-Bond Acceptors", "HBD": "H-Bond Donors",
        "IC50_nM": "IC50 (nM)", "selectivity": "Selectivity Index",
    },
    title="Drug Candidate Properties — Parallel Coordinates",
)
fig.show()
```

### Module 6: Subplots and Export

`make_subplots()` creates multi-panel layouts with shared axes, mixed chart types, and independent traces per panel. `fig.write_html()` exports interactive figures; `fig.write_image()` exports static files via kaleido.

```python
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import numpy as np

# Two-panel: raw data + summary statistics
np.random.seed(77)
doses = [0.01, 0.1, 1, 10, 100]
drugs = {"DrugA": {"EC50": 1.0, "hill": 1.5}, "DrugB": {"EC50": 8.0, "hill": 0.9}}

def hill_curve(dose, ec50, hill, top=100, bottom=0):
    return bottom + (top - bottom) / (1 + (ec50 / dose) ** hill)

fig = make_subplots(
    rows=1, cols=2,
    subplot_titles=["Dose-Response Curves", "IC50 Comparison"],
    shared_yaxes=False,
)

colors = {"DrugA": "crimson", "DrugB": "steelblue"}
ic50_values = []

for drug, params in drugs.items():
    # Smooth fit curve
    x_fit = np.logspace(-2, 2, 200)
    y_fit = hill_curve(x_fit, params["EC50"], params["hill"])
    fig.add_trace(go.Scatter(
        x=x_fit, y=y_fit, mode="lines",
        name=f"{drug} fit", line=dict(color=colors[drug], width=2.5),
    ), row=1, col=1)

    # Noisy data points
    y_data = [hill_curve(d, params["EC50"], params["hill"]) +
              np.random.normal(0, 4) for d in doses]
    fig.add_trace(go.Scatter(
        x=doses, y=y_data, mode="markers",
        name=f"{drug} data", marker=dict(color=colors[drug], size=9),
        showlegend=False,
    ), row=1, col=1)
    ic50_values.append(params["EC50"])

# Bar chart of IC50 values
fig.add_trace(go.Bar(
    x=list(drugs.keys()), y=ic50_values,
    marker_color=list(colors.values()),
    showlegend=False,
    hovertemplate="%{x}<br>IC50: %{y:.2f} µM<extra></extra>",
), row=1, col=2)

fig.update_xaxes(type="log", title_text="Dose (µM)", row=1, col=1)
fig.update_yaxes(title_text="Viability (%)", row=1, col=1)
fig.update_xaxes(title_text="Drug", row=1, col=2)
fig.update_yaxes(title_text="IC50 (µM)", row=1, col=2)
fig.update_layout(title="Dose-Response Dashboard", height=450, width=850)
fig.show()
print(f"Subplots: {len(fig.data)} traces across 2 panels")
```

```python
# Export to HTML (interactive) and PNG (static)
# Requires: pip install kaleido

fig.write_html("dose_response_dashboard.html")
print("Saved: dose_response_dashboard.html (interactive, shareable)")

fig.write_image("dose_response_dashboard.png", width=1200, height=600, scale=2)
print("Saved: dose_response_dashboard.png (300 DPI equivalent with scale=2)")

fig.write_image("dose_response_dashboard.svg")
print("Saved: dose_response_dashboard.svg (vector, editable in Inkscape/Illustrator)")
```

## Common Workflows

### Workflow 1: Interactive Volcano Plot with Gene Annotations

**Goal**: Build a fully annotated volcano plot from DESeq2 results, with gene-name hover tooltips, threshold lines, and highlighted hit labels for sharing as HTML.

```python
import plotly.graph_objects as go
import pandas as pd
import numpy as np

# Simulate DESeq2 output (replace with pd.read_csv("deseq2_results.csv"))
np.random.seed(42)
n = 3000
df = pd.DataFrame({
    "gene": [f"GENE_{i:04d}" for i in range(n)],
    "log2FC": np.random.normal(0, 1.0, n),
    "padj": np.clip(np.random.exponential(0.1, n), 1e-20, 1.0),
    "baseMean": np.random.lognormal(5, 1.5, n),
})
# Inject some hits
df.loc[:20, "log2FC"] = np.random.uniform(2.5, 5, 21)
df.loc[:20, "padj"] = np.random.uniform(1e-15, 1e-5, 21)
df.loc[21:35, "log2FC"] = np.random.uniform(-4, -2, 15)
df.loc[21:35, "padj"] = np.random.uniform(1e-12, 1e-4, 15)

df["neg_log10_padj"] = -np.log10(df["padj"].clip(1e-300))

# Classify
FC_THRESH, P_THRESH = 1.5, 2.0   # |log2FC| > 1.5, -log10(padj) > 2
df["category"] = "NS"
df.loc[(df["log2FC"] > FC_THRESH) & (df["neg_log10_padj"] > P_THRESH), "category"] = "Up"
df.loc[(df["log2FC"] < -FC_THRESH) & (df["neg_log10_padj"] > P_THRESH), "category"] = "Down"

color_map = {"NS": "lightgray", "Up": "crimson", "Down": "steelblue"}
size_map = {"NS": 4, "Up": 7, "Down": 7}
opacity_map = {"NS": 0.4, "Up": 0.85, "Down": 0.85}

fig = go.Figure()

for cat in ["NS", "Up", "Down"]:
    sub = df[df["category"] == cat]
    fig.add_trace(go.Scatter(
        x=sub["log2FC"], y=sub["neg_log10_padj"],
        mode="markers",
        name=f"{cat} (n={len(sub)})",
        marker=dict(
            color=color_map[cat],
            size=size_map[cat],
            opacity=opacity_map[cat],
        ),
        customdata=sub[["gene", "padj", "baseMean"]].values,
        hovertemplate=(
            "<b>%{customdata[0]}</b><br>"
            "log2FC: %{x:.3f}<br>"
            "padj: %{customdata[1]:.2e}<br>"
            "baseMean: %{customdata[2]:.1f}<extra></extra>"
        ),
    ))

# Threshold lines
fig.add_hline(y=P_THRESH, line_dash="dot", line_color="black", line_width=1.2,
              annotation_text=f"padj=0.01", annotation_position="right")
fig.add_vline(x=FC_THRESH, line_dash="dot", line_color="black", line_width=1.2)
fig.add_vline(x=-FC_THRESH, line_dash="dot", line_color="black", line_width=1.2)

# Label top 5 upregulated hits by significance
top_up = df[df["category"] == "Up"].nlargest(5, "neg_log10_padj")
for _, row in top_up.iterrows():
    fig.add_annotation(
        x=row["log2FC"], y=row["neg_log10_padj"],
        text=row["gene"], showarrow=True,
        arrowhead=2, arrowsize=1, arrowcolor="crimson",
        font=dict(size=9, color="crimson"),
        xshift=8, yshift=5,
    )

fig.update_layout(
    title="Volcano Plot — Treatment vs Control (DESeq2)",
    xaxis_title="log2 Fold Change",
    yaxis_title="-log10(adjusted p-value)",
    legend=dict(x=0.01, y=0.99, bordercolor="lightgray", borderwidth=1),
    width=800, height=560,
    plot_bgcolor="white",
)
fig.update_xaxes(showgrid=True, gridcolor="lightgray", zeroline=True, zerolinecolor="darkgray")
fig.update_yaxes(showgrid=True, gridcolor="lightgray")

fig.write_html("volcano_interactive.html")
print(f"Up: {(df.category=='Up').sum()}, Down: {(df.category=='Down').sum()}")
print("Saved: volcano_interactive.html")
```

### Workflow 2: Multi-Panel Dose-Response Dashboard with make_subplots

**Goal**: Display dose-response curves for multiple drugs across cell lines in a grid layout with a shared color scale and consistent formatting.

```python
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import numpy as np
import pandas as pd

# Simulated IC50 data for 3 drugs × 3 cell lines
np.random.seed(10)
drugs = ["DrugA", "DrugB", "DrugC"]
cell_lines = ["HCT116", "MCF7", "A549"]
doses = np.logspace(-2, 2, 7)  # 0.01 to 100 µM

def hill(x, ec50, hill_n, top=100, bottom=0):
    return bottom + (top - bottom) / (1 + (ec50 / x) ** hill_n)

ec50_table = {
    ("DrugA", "HCT116"): 0.5, ("DrugA", "MCF7"): 2.0, ("DrugA", "A549"): 8.0,
    ("DrugB", "HCT116"): 5.0, ("DrugB", "MCF7"): 0.8, ("DrugB", "A549"): 15.0,
    ("DrugC", "HCT116"): 12.0, ("DrugC", "MCF7"): 6.0, ("DrugC", "A549"): 1.2,
}

palette = px_colors = ["#EF553B", "#636EFA", "#00CC96", "#AB63FA", "#FFA15A",
                        "#19D3F3", "#FF6692", "#B6E880", "#FF97FF"]

fig = make_subplots(
    rows=len(drugs), cols=len(cell_lines),
    subplot_titles=[f"{d} / {c}" for d in drugs for c in cell_lines],
    shared_xaxes=True, shared_yaxes=True,
    vertical_spacing=0.08, horizontal_spacing=0.04,
)

for r, drug in enumerate(drugs, start=1):
    for c, cell_line in enumerate(cell_lines, start=1):
        ec50 = ec50_table[(drug, cell_line)]
        x_fit = np.logspace(-2, 2, 200)
        y_fit = hill(x_fit, ec50, hill_n=1.5)

        # Noisy replicate data
        y_data = np.array([hill(d, ec50, 1.5) + np.random.normal(0, 5) for d in doses])

        color = palette[(r - 1) * len(cell_lines) + (c - 1)]
        show_legend = (c == 1 and r == 1)

        fig.add_trace(go.Scatter(
            x=x_fit, y=y_fit, mode="lines",
            line=dict(color=color, width=2),
            name=f"{drug}/{cell_line}",
            showlegend=False,
            hovertemplate=f"{drug} in {cell_line}<br>Dose: %{{x:.2f}} µM<br>Viability: %{{y:.1f}}%<extra></extra>",
        ), row=r, col=c)

        fig.add_trace(go.Scatter(
            x=doses, y=np.clip(y_data, 0, 110), mode="markers",
            marker=dict(color=color, size=7, opacity=0.8),
            showlegend=False,
            hovertemplate=f"Measured<br>Dose: %{{x:.2f}} µM<br>Viability: %{{y:.1f}}%<extra></extra>",
        ), row=r, col=c)

        # IC50 annotation
        fig.add_annotation(
            x=np.log10(ec50), y=50,
            text=f"IC50={ec50:.1f}µM",
            font=dict(size=8), showarrow=False,
            xref=f"x{(r-1)*len(cell_lines)+c if (r-1)*len(cell_lines)+c > 1 else ''}",
            yref=f"y{(r-1)*len(cell_lines)+c if (r-1)*len(cell_lines)+c > 1 else ''}",
        )

# Apply log scale to all x-axes
for i in range(1, len(drugs) * len(cell_lines) + 1):
    axis_key = f"xaxis{i if i > 1 else ''}"
    fig.layout[axis_key].update(type="log", title_text="Dose (µM)" if i > 6 else "")

for i in range(1, len(drugs) * len(cell_lines) + 1):
    axis_key = f"yaxis{i if i > 1 else ''}"
    fig.layout[axis_key].update(range=[-5, 115],
                                 title_text="Viability (%)" if i in [1, 4, 7] else "")

fig.update_layout(
    title="Dose-Response Dashboard — 3 Drugs × 3 Cell Lines",
    height=700, width=900,
)
fig.write_html("dose_response_dashboard.html")
print("Saved: dose_response_dashboard.html")
print(f"Grid: {len(drugs)} drugs × {len(cell_lines)} cell lines = {len(drugs)*len(cell_lines)} panels")
```

## Key Parameters

| Parameter | Module / Function | Default | Range / Options | Effect |
|-----------|------------------|---------|-----------------|--------|
| `color` | `px.*` | `None` | Column name | Maps a DataFrame column to trace color; auto-assigns palette |
| `hover_data` | `px.*` | `{}` | Dict or list of column names | Extra columns shown in hover tooltip |
| `log_x` / `log_y` | `px.*` | `False` | `True`, `False` | Apply log10 scale to x or y axis |
| `facet_col` / `facet_row` | `px.*` | `None` | Column name | Split into subplot grid by a categorical variable |
| `color_continuous_scale` | `px.imshow`, `px.scatter` | `"plasma"` | `"RdBu_r"`, `"Viridis"`, `"Hot"`, etc. | Colormap for continuous color mapping |
| `color_continuous_midpoint` | `px.imshow` | `None` | Any numeric | Centers the diverging colormap at this value (use `0` for z-scores) |
| `barmode` | `px.histogram`, `px.bar` | `"relative"` | `"relative"`, `"overlay"`, `"group"` | How multiple bar traces are displayed |
| `opacity` | `go.Scatter`, `px.*` | `1.0` | `0.0`–`1.0` | Point/bar transparency |
| `size` / `sizeref` | `go.Scatter` | `6` / auto | Positive numeric | Marker size; `sizeref` normalizes sizes across traces |
| `line_dash` | `fig.add_hline`, `go.Scatter` | `"solid"` | `"solid"`, `"dash"`, `"dot"`, `"dashdot"` | Line style for reference lines and traces |
| `shared_xaxes` / `shared_yaxes` | `make_subplots` | `False` | `True`, `False`, `"rows"`, `"cols"` | Link axes across subplot panels |
| `scale` | `fig.write_image` | `1` | `1`–`4` | Resolution multiplier for PNG export (use `2` for ~150 DPI) |

## Best Practices

1. **Prefer `px` for DataFrame data, fall back to `go` for multi-trace composition.** Use `px.scatter()` and its siblings for 80% of plots. Switch to `go` when you need traces with different types in the same figure (e.g., scatter + filled area) or need fine-grained per-trace control.

   ```python
   # Correct: px for simple grouped plots
   fig = px.box(df, x="treatment", y="expression", color="genotype")

   # Correct: go when px cannot express the structure
   fig = go.Figure()
   fig.add_trace(go.Scatter(x=x, y=y_upper, fill="tonexty", ...))
   fig.add_trace(go.Scatter(x=x, y=y_lower, ...))
   ```

2. **Always include `hovertemplate` for scientific figures.** The default tooltip shows raw coordinates without units or gene names. A custom template with `customdata` provides full biological context.

   ```python
   fig.add_trace(go.Scatter(
       customdata=df[["gene", "padj"]].values,
       hovertemplate="<b>%{customdata[0]}</b><br>padj: %{customdata[1]:.2e}<extra></extra>",
   ))
   ```

3. **Export HTML for sharing, PNG/SVG for journals.** `fig.write_html()` produces a self-contained file with no external dependencies. Use `scale=2` or higher with `write_image()` to achieve sufficient resolution for print.

4. **Don't use `fig.show()` in batch scripts.** In non-interactive contexts (CI, HPC, cron jobs), `fig.show()` may open a browser window or fail. Use `write_html()` or `write_image()` exclusively.

5. **Use `color_continuous_midpoint=0` for diverging palettes on z-score data.** Without it, the midpoint color defaults to the data midpoint, not zero, misrepresenting symmetric fold changes or correlations.

   ```python
   fig = px.imshow(corr_matrix, color_continuous_scale="RdBu_r",
                   color_continuous_midpoint=0, zmin=-1, zmax=1)
   ```

6. **Set `plot_bgcolor="white"` for publication figures.** Plotly defaults to a light-gray grid background. White background with subtle gridlines is cleaner for most scientific contexts.

   ```python
   fig.update_layout(plot_bgcolor="white")
   fig.update_xaxes(showgrid=True, gridcolor="lightgray")
   fig.update_yaxes(showgrid=True, gridcolor="lightgray")
   ```

## Common Recipes

### Recipe: Dropdown Menu to Toggle Between Conditions

When to use: Overlay multiple conditions in one figure with a dropdown button to show/hide individual traces cleanly.

```python
import plotly.graph_objects as go
import numpy as np

conditions = ["Untreated", "DrugA", "DrugB"]
colors = ["gray", "crimson", "steelblue"]
np.random.seed(1)
x = np.linspace(0, 24, 49)

fig = go.Figure()
for i, (cond, color) in enumerate(zip(conditions, colors)):
    y = np.sin(x / 4 + i * 0.5) * (1 - i * 0.2) + np.random.normal(0, 0.05, len(x))
    fig.add_trace(go.Scatter(
        x=x, y=y, mode="lines+markers",
        name=cond, line=dict(color=color, width=2),
        visible=(i == 0),  # only first trace visible initially
    ))

# One button per condition (shows only that trace)
buttons = []
for i, cond in enumerate(conditions):
    visibility = [j == i for j in range(len(conditions))]
    buttons.append(dict(label=cond, method="update",
                        args=[{"visible": visibility}, {"title": f"Gene Expression — {cond}"}]))

# "Show All" button
buttons.append(dict(label="Show All", method="update",
                    args=[{"visible": [True] * len(conditions)}, {"title": "Gene Expression — All Conditions"}]))

fig.update_layout(
    updatemenus=[dict(type="dropdown", x=0.01, y=1.15, showactive=True, buttons=buttons)],
    title="Gene Expression — Untreated",
    xaxis_title="Time (h)", yaxis_title="Relative Expression",
)
fig.show()
```

### Recipe: Annotating Specific Hits with Arrows

When to use: Label outliers, drug hits, or significant genes directly on the figure without cluttering non-annotated points.

```python
import plotly.graph_objects as go
import numpy as np
import pandas as pd

np.random.seed(33)
df = pd.DataFrame({
    "x": np.random.normal(0, 1.5, 300),
    "y": np.random.normal(0, 1.5, 300),
    "gene": [f"G{i:03d}" for i in range(300)],
})
# Inject top hits
hits = pd.DataFrame({
    "x": [3.2, -2.8, 2.5, -3.5],
    "y": [4.1, 3.8, -3.2, -2.9],
    "gene": ["BRCA1", "TP53", "EGFR", "KRAS"],
})

fig = go.Figure()
fig.add_trace(go.Scatter(
    x=df["x"], y=df["y"], mode="markers",
    marker=dict(color="lightgray", size=5, opacity=0.6),
    text=df["gene"],
    hovertemplate="<b>%{text}</b><br>x: %{x:.2f}, y: %{y:.2f}<extra></extra>",
    name="Background",
))
fig.add_trace(go.Scatter(
    x=hits["x"], y=hits["y"], mode="markers",
    marker=dict(color="crimson", size=10, symbol="diamond"),
    text=hits["gene"],
    hovertemplate="<b>%{text}</b> [HIT]<br>x: %{x:.2f}, y: %{y:.2f}<extra></extra>",
    name="Hits",
))

for _, row in hits.iterrows():
    fig.add_annotation(
        x=row["x"], y=row["y"],
        text=f"<b>{row['gene']}</b>",
        showarrow=True, arrowhead=2, arrowwidth=1.5,
        arrowcolor="crimson", font=dict(size=11, color="crimson"),
        ax=25, ay=-30,  # arrow offset in pixels
        bgcolor="rgba(255,255,255,0.7)", bordercolor="crimson", borderwidth=1,
    )

fig.update_layout(
    title="Hit Identification with Arrow Annotations",
    xaxis_title="Score A", yaxis_title="Score B",
    plot_bgcolor="white",
)
fig.show()
```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `ValueError: kaleido is required for static image export` | `kaleido` not installed | `pip install kaleido`; verify with `import kaleido` |
| Blank figure in Jupyter Notebook | Renderer not configured | Run `import plotly.io as pio; pio.renderers.default = "notebook"` or upgrade JupyterLab to ≥3 |
| `fig.show()` opens blank browser tab | No data in figure or offline renderer issue | Check `len(fig.data) > 0`; use `pio.renderers.default = "browser"` |
| Hover tooltips show wrong values | `customdata` index mismatch in `hovertemplate` | Verify `customdata` column order matches `%{customdata[N]}` indices in template |
| Colors not assigned consistently across traces | `px` re-orders palette when category counts differ | Use `color_discrete_map={"Cat1": "#color1", ...}` to pin colors explicitly |
| `write_image` produces blurry PNG | Default `scale=1` is too low for print | Use `fig.write_image("fig.png", scale=2)` for 150 DPI or `scale=4` for 300 DPI |
| Subplots x-axes not all log-scaled after `shared_xaxes=True` | Shared axis only synchronizes range, not type | Iterate over all `xaxis` keys in `fig.layout` and set `type="log"` explicitly |
| Large datasets slow to render in browser | Too many individual points in a single scatter trace | Downsample background noise points; keep labeled hits as a separate, smaller trace |
| `fig.update_layout` does not apply to subplot axes | Multi-panel figures use indexed axes (`xaxis2`, `xaxis3`) | Use `fig.update_xaxes()` (applies to all) or target `fig.layout["xaxis2"]` explicitly |

## Related Skills

- **seaborn-statistical-plots** — use for statistical aggregation (confidence intervals, regression), publication-quality static figures with minimal code, and when matplotlib-level output is required
- **matplotlib-scientific-plotting** — use for full control over every figure element, custom layouts, embedded text rendering, and journal-specification figure preparation
- **pydeseq2-differential-expression** — volcano plot outputs from DESeq2 results are a primary input for the interactive volcano workflow above
- **scanpy-scrna-seq** — Scanpy's UMAP embeddings can be visualized interactively in 3D with `px.scatter_3d`

## References

- [Plotly Python Documentation](https://plotly.com/python/) — official API reference, examples gallery, and getting-started guides
- [Plotly Express API Reference](https://plotly.com/python-api-reference/plotly.express.html) — complete `px` function signatures and parameters
- [Plotly Graph Objects Reference](https://plotly.com/python/graph-objects/) — full `go` trace and layout attribute reference
- [Plotly GitHub Repository](https://github.com/plotly/plotly.py) — source code, issue tracker, changelog
- [Kaleido Static Image Export](https://github.com/plotly/Kaleido) — dependency for `write_image()` PNG/SVG/PDF export
