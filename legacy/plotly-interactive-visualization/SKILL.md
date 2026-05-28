---
name: plotly-interactive-visualization
description: "Interactive visualization with Plotly. 40+ chart types (scatter, line, heatmap, 3D, geographic) with hover, zoom, pan. Two APIs: Plotly Express (DataFrame) and Graph Objects (fine control). For static publication figures use matplotlib; for statistical grammar use seaborn."
license: MIT
---

# Plotly — Interactive Scientific Visualization

## Overview

Plotly is a Python graphing library for interactive, web-embeddable visualizations with 40+ chart types. It provides two APIs: Plotly Express (high-level, pandas-native) for quick plots and Graph Objects (low-level) for full customization. Output to interactive HTML, static PNG/PDF/SVG, or Dash web apps.

## When to Use

- Creating interactive charts with hover tooltips, zoom, and pan
- Building multi-panel exploratory dashboards for data analysis
- Visualizing 3D data (surfaces, scatter3d, mesh, volume)
- Making geographic/map visualizations (choropleth, scatter_geo)
- Presenting data in web-embeddable HTML format
- Statistical distribution comparison (violin, box, histogram with marginals)
- Time series with range sliders and animation frames
- For **static publication-quality figures** (journal submissions), use `matplotlib` instead
- For **statistical grammar-of-graphics** style, use `seaborn` instead

## Prerequisites

- **Python packages**: `plotly`, `pandas`, `numpy`
- **For static export**: `kaleido` (PNG/PDF/SVG rendering)
- **For web apps**: `dash` (optional)

```bash
pip install plotly kaleido
```

## Quick Start

```python
import plotly.express as px
import pandas as pd
import numpy as np

# Sample data
np.random.seed(42)
df = pd.DataFrame({
    "x": np.random.randn(200),
    "y": np.random.randn(200),
    "group": np.random.choice(["A", "B", "C"], 200),
    "size": np.random.uniform(5, 20, 200),
})

fig = px.scatter(df, x="x", y="y", color="group", size="size",
                 title="Interactive Scatter Plot", hover_data=["group"])
fig.write_html("scatter.html")
fig.write_image("scatter.png", width=800, height=500, scale=2)
print("Saved scatter.html and scatter.png")
```

## Core API

### 1. Plotly Express (High-Level API)

Quick, one-line charts from pandas DataFrames. Returns `go.Figure` objects that can be further customized.

```python
import plotly.express as px
import pandas as pd
import numpy as np

np.random.seed(42)
df = pd.DataFrame({
    "temperature": np.linspace(20, 80, 50),
    "yield": 50 + 0.8 * np.linspace(20, 80, 50) + np.random.randn(50) * 5,
    "catalyst": np.random.choice(["Pd", "Pt", "Rh"], 50),
})

# Scatter with trendline
fig = px.scatter(df, x="temperature", y="yield", color="catalyst",
                 trendline="ols", title="Temperature vs Yield")
fig.write_image("scatter_trend.png", width=700, height=450)
print("Saved scatter_trend.png")

# Bar chart
summary = df.groupby("catalyst")["yield"].mean().reset_index()
fig = px.bar(summary, x="catalyst", y="yield", color="catalyst",
             title="Mean Yield by Catalyst")
fig.write_image("bar_catalyst.png", width=600, height=400)
print("Saved bar_catalyst.png")
```

```python
# Heatmap from correlation matrix
import plotly.express as px
import pandas as pd
import numpy as np

np.random.seed(42)
data = pd.DataFrame(np.random.randn(100, 5), columns=["Gene_A", "Gene_B", "Gene_C", "Gene_D", "Gene_E"])
corr = data.corr()

fig = px.imshow(corr, text_auto=".2f", color_continuous_scale="RdBu_r",
                zmin=-1, zmax=1, title="Gene Expression Correlation")
fig.write_image("heatmap.png", width=600, height=500)
print("Saved heatmap.png")
```

### 2. Graph Objects (Low-Level API)

Full control over individual traces, layouts, and annotations.

```python
import plotly.graph_objects as go
import numpy as np

# 3D surface plot
x = np.linspace(-5, 5, 50)
y = np.linspace(-5, 5, 50)
X, Y = np.meshgrid(x, y)
Z = np.sin(np.sqrt(X**2 + Y**2))

fig = go.Figure(data=[go.Surface(z=Z, x=X[0], y=y, colorscale="Viridis")])
fig.update_layout(title="3D Surface Plot",
                  scene=dict(xaxis_title="X", yaxis_title="Y", zaxis_title="Z"))
fig.write_image("surface_3d.png", width=700, height=500)
print("Saved surface_3d.png")
```

```python
# Multi-trace figure with custom styling
import plotly.graph_objects as go
import numpy as np

np.random.seed(42)
x = np.linspace(0, 10, 100)
fig = go.Figure()
fig.add_trace(go.Scatter(x=x, y=np.sin(x), mode="lines", name="sin(x)",
                         line=dict(color="blue", width=2)))
fig.add_trace(go.Scatter(x=x, y=np.cos(x), mode="lines", name="cos(x)",
                         line=dict(color="red", width=2, dash="dash")))
fig.add_hline(y=0, line_dash="dot", line_color="gray", opacity=0.5)
fig.add_annotation(x=np.pi/2, y=1, text="sin peak", showarrow=True, arrowhead=2)

fig.update_layout(template="plotly_white", title="Trigonometric Functions",
                  xaxis_title="x", yaxis_title="f(x)")
fig.write_image("multi_trace.png", width=700, height=400)
print("Saved multi_trace.png")
```

### 3. Subplots and Multi-Panel Layouts

Create figure grids with shared or independent axes.

```python
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import numpy as np

np.random.seed(42)
data = np.random.randn(500)

fig = make_subplots(
    rows=2, cols=2,
    subplot_titles=("Histogram", "Box Plot", "Scatter", "Violin"),
    specs=[[{"type": "histogram"}, {"type": "box"}],
           [{"type": "scatter"}, {"type": "violin"}]],
)

fig.add_trace(go.Histogram(x=data, nbinsx=30, name="Hist"), row=1, col=1)
fig.add_trace(go.Box(y=data, name="Box"), row=1, col=2)
fig.add_trace(go.Scatter(x=data[:100], y=data[100:200], mode="markers", name="Scatter"), row=2, col=1)
fig.add_trace(go.Violin(y=data, name="Violin", box_visible=True), row=2, col=2)

fig.update_layout(height=700, width=800, title_text="Multi-Panel Dashboard", showlegend=False)
fig.write_image("subplots.png", width=800, height=700)
print("Saved subplots.png")
```

### 4. Statistical Charts

Distribution comparison, error bars, and statistical annotations.

```python
import plotly.express as px
import pandas as pd
import numpy as np

np.random.seed(42)
df = pd.DataFrame({
    "value": np.concatenate([np.random.normal(0, 1, 100), np.random.normal(2, 1.5, 100)]),
    "group": ["Control"] * 100 + ["Treatment"] * 100,
})

# Histogram with marginal box plot
fig = px.histogram(df, x="value", color="group", marginal="box",
                   nbins=30, barmode="overlay", opacity=0.7,
                   title="Distribution Comparison")
fig.write_image("stat_hist.png", width=700, height=450)
print("Saved stat_hist.png")

# Violin plot with individual points
fig = px.violin(df, x="group", y="value", box=True, points="all",
                title="Treatment Effect (Violin + Points)")
fig.write_image("violin.png", width=500, height=450)
print("Saved violin.png")
```

```python
# Error bars
import plotly.graph_objects as go
import numpy as np

conditions = ["Control", "Low Dose", "Med Dose", "High Dose"]
means = [5.2, 7.1, 9.8, 11.3]
sems = [0.4, 0.6, 0.5, 0.8]

fig = go.Figure(data=[go.Bar(
    x=conditions, y=means,
    error_y=dict(type="data", array=sems, visible=True),
    marker_color=["#636EFA", "#EF553B", "#00CC96", "#AB63FA"],
)])
fig.update_layout(title="Dose Response (mean ± SEM)", yaxis_title="Response",
                  template="plotly_white")
fig.write_image("error_bars.png", width=600, height=400)
print("Saved error_bars.png")
```

### 5. Export and Rendering

Save to interactive HTML, static images, or embed in notebooks.

```python
import plotly.express as px
import pandas as pd

df = px.data.iris()
fig = px.scatter(df, x="sepal_width", y="sepal_length", color="species")

# Interactive HTML (full standalone)
fig.write_html("interactive.html")
# HTML with CDN (smaller file, needs internet)
fig.write_html("interactive_cdn.html", include_plotlyjs="cdn")

# Static images (requires kaleido)
fig.write_image("plot.png", width=800, height=500, scale=2)  # 2x resolution
fig.write_image("plot.pdf")  # Vector PDF
fig.write_image("plot.svg")  # Vector SVG

# Get image as bytes (for embedding)
img_bytes = fig.to_image(format="png", width=600, height=400)
print(f"PNG bytes: {len(img_bytes)}")
```

### 6. Interactivity Features

Customize hover, animations, buttons, and range sliders.

```python
import plotly.express as px
import pandas as pd
import numpy as np

# Custom hover template
np.random.seed(42)
df = pd.DataFrame({
    "date": pd.date_range("2024-01-01", periods=100),
    "price": 100 + np.cumsum(np.random.randn(100) * 2),
    "volume": np.random.randint(1000, 5000, 100),
})

fig = px.line(df, x="date", y="price", title="Stock Price",
              hover_data={"volume": True, "price": ":.2f"})
fig.update_traces(hovertemplate="<b>%{x|%Y-%m-%d}</b><br>Price: $%{y:.2f}<br>Volume: %{customdata[0]:,}<extra></extra>")
fig.update_xaxes(rangeslider_visible=True)
fig.write_html("timeseries.html")
print("Saved timeseries.html with range slider")
```

## Common Workflows

### Workflow 1: Exploratory Data Analysis Dashboard

**Goal**: Create a multi-panel interactive dashboard for dataset exploration.

```python
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np

# Sample dataset
np.random.seed(42)
n = 300
df = pd.DataFrame({
    "gene_expression": np.random.lognormal(2, 1, n),
    "protein_level": np.random.lognormal(1.5, 0.8, n),
    "cell_type": np.random.choice(["Neuron", "Astrocyte", "Microglia"], n),
    "treatment": np.random.choice(["Control", "Drug_A", "Drug_B"], n),
    "viability": np.random.uniform(0.3, 1.0, n),
})

fig = make_subplots(rows=2, cols=2,
                    subplot_titles=("Expression vs Protein", "Expression by Cell Type",
                                    "Viability by Treatment", "Expression Distribution"))

# Panel 1: Scatter
for ct in df["cell_type"].unique():
    sub = df[df["cell_type"] == ct]
    fig.add_trace(go.Scatter(x=sub["gene_expression"], y=sub["protein_level"],
                             mode="markers", name=ct, opacity=0.6), row=1, col=1)

# Panel 2: Box
for ct in df["cell_type"].unique():
    fig.add_trace(go.Box(y=df[df["cell_type"]==ct]["gene_expression"],
                         name=ct, showlegend=False), row=1, col=2)

# Panel 3: Violin
for tx in df["treatment"].unique():
    fig.add_trace(go.Violin(y=df[df["treatment"]==tx]["viability"],
                            name=tx, showlegend=False, box_visible=True), row=2, col=1)

# Panel 4: Histogram
fig.add_trace(go.Histogram(x=df["gene_expression"], nbinsx=30,
                           name="Expression", showlegend=False), row=2, col=2)

fig.update_layout(height=800, width=1000, title="Exploratory Data Analysis")
fig.write_html("eda_dashboard.html")
fig.write_image("eda_dashboard.png", width=1000, height=800)
print("Saved eda_dashboard.html and eda_dashboard.png")
```

### Workflow 2: Publication Figure with Annotations

**Goal**: Create a polished, annotated figure suitable for supplementary materials or presentations.

```python
import plotly.graph_objects as go
import numpy as np

np.random.seed(42)
x = np.linspace(0, 24, 100)
control = 50 + 10 * np.sin(x * np.pi / 12) + np.random.randn(100) * 3
treatment = 70 + 15 * np.sin(x * np.pi / 12 + 0.5) + np.random.randn(100) * 4

fig = go.Figure()
fig.add_trace(go.Scatter(x=x, y=control, mode="lines", name="Control",
                         line=dict(color="#636EFA", width=2)))
fig.add_trace(go.Scatter(x=x, y=treatment, mode="lines", name="Treatment",
                         line=dict(color="#EF553B", width=2)))

# Add shaded region for treatment window
fig.add_vrect(x0=6, x1=18, fillcolor="yellow", opacity=0.1, line_width=0,
              annotation_text="Treatment Window", annotation_position="top left")

# Add annotation at peak difference
fig.add_annotation(x=12, y=85, text="Peak difference<br>p < 0.001",
                   showarrow=True, arrowhead=2, font=dict(size=11))

fig.update_layout(
    template="plotly_white",
    title="Circadian Response to Treatment",
    xaxis_title="Time (hours)", yaxis_title="Response (AU)",
    font=dict(family="Arial", size=12),
    legend=dict(x=0.02, y=0.98),
    width=700, height=450,
)
fig.write_image("publication_figure.png", width=700, height=450, scale=3)
print("Saved publication_figure.png (3x resolution)")
```

## Key Parameters

| Parameter | Module | Default | Range / Options | Effect |
|-----------|--------|---------|-----------------|--------|
| `template` | `update_layout` | `"plotly"` | `"plotly_white"`, `"plotly_dark"`, `"ggplot2"`, `"seaborn"`, `"simple_white"` | Global figure styling theme |
| `color_continuous_scale` | `px` / `go` | varies | `"Viridis"`, `"Plasma"`, `"RdBu"`, `"RdBu_r"`, `"Blues"` | Color scale for continuous data |
| `barmode` | `px.histogram` | `"relative"` | `"group"`, `"overlay"`, `"relative"`, `"stack"` | How multiple histograms are arranged |
| `trendline` | `px.scatter` | `None` | `None`, `"ols"`, `"lowess"`, `"expanding"` | Regression line overlay |
| `marginal` | `px.scatter/histogram` | `None` | `None`, `"rug"`, `"box"`, `"violin"`, `"histogram"` | Marginal distribution display |
| `scale` | `write_image` | `1` | `1`–`5` | Image resolution multiplier (2=retina, 3=print) |
| `include_plotlyjs` | `write_html` | `True` | `True`, `"cdn"`, `"directory"`, `False` | How Plotly.js is bundled in HTML |
| `opacity` | most trace types | `1.0` | `0.0`–`1.0` | Trace transparency for overlapping data |

## Best Practices

1. **Start with Plotly Express, customize with Graph Objects**: `px` functions return `go.Figure` objects, so you can always add Graph Objects methods after. Don't start with `go` unless `px` genuinely cannot express what you need.
   ```python
   fig = px.scatter(df, x="x", y="y", color="group")
   fig.update_layout(template="plotly_white")  # go method on px figure
   fig.add_hline(y=threshold)
   ```

2. **Use `plotly_white` template for publication figures**: The default `plotly` template has a gray background that looks unprofessional in papers. `plotly_white` or `simple_white` gives a clean look.

3. **Always set explicit width/height for static export**: Without dimensions, `write_image` uses the default viewport size which may not match your target (journal column width, slide dimensions).

4. **Use `scale=2` or higher for print-quality images**: Default `scale=1` produces 72 DPI equivalent. For publications, use `scale=3` (216 DPI effective).

5. **Prefer HTML export for interactive data sharing**: HTML files are self-contained and can be opened in any browser without Python. Use `include_plotlyjs="cdn"` to reduce file size.

## Common Recipes

### Recipe: Correlation Matrix Heatmap

```python
import plotly.express as px
import pandas as pd
import numpy as np

np.random.seed(42)
df = pd.DataFrame(np.random.randn(100, 6), columns=[f"Var_{i}" for i in range(6)])
corr = df.corr()

# Mask upper triangle
mask = np.triu(np.ones_like(corr, dtype=bool), k=1)
corr_masked = corr.where(~mask)

fig = px.imshow(corr_masked, text_auto=".2f", color_continuous_scale="RdBu_r",
                zmin=-1, zmax=1, title="Correlation Matrix")
fig.write_image("correlation.png", width=600, height=500, scale=2)
print("Saved correlation.png")
```

### Recipe: Animated Scatter Plot

```python
import plotly.express as px
import pandas as pd
import numpy as np

np.random.seed(42)
frames = []
for year in range(2010, 2025):
    n = 50
    frames.append(pd.DataFrame({
        "x": np.random.randn(n) * (year - 2009),
        "y": np.random.randn(n) * (year - 2009),
        "size": np.random.uniform(5, 20, n),
        "year": year,
    }))
df = pd.concat(frames)

fig = px.scatter(df, x="x", y="y", size="size", animation_frame="year",
                 range_x=[-30, 30], range_y=[-30, 30], title="Animated Scatter")
fig.write_html("animated.html")
print("Saved animated.html")
```

### Recipe: Geographic Choropleth Map

```python
import plotly.express as px

# Built-in gapminder dataset
df = px.data.gapminder().query("year == 2007")
fig = px.choropleth(df, locations="iso_alpha", color="gdpPercap",
                    hover_name="country", color_continuous_scale="Plasma",
                    title="GDP per Capita (2007)")
fig.write_image("choropleth.png", width=900, height=500, scale=2)
print("Saved choropleth.png")
```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `write_image` fails with `ValueError` | `kaleido` not installed | `pip install kaleido` |
| Blank/white image from `write_image` | Plotly version mismatch with kaleido | Update both: `pip install --upgrade plotly kaleido` |
| HTML file very large (>10 MB) | Full Plotly.js bundled | Use `fig.write_html(path, include_plotlyjs="cdn")` |
| Hover data not showing | Column not in DataFrame or wrong name | Check `hover_data` parameter matches DataFrame columns exactly |
| Subplot traces appear in wrong panel | Incorrect `row`/`col` in `add_trace` | Verify `row=` and `col=` match your `make_subplots` grid (1-indexed) |
| Colors don't match between px and go | Different default color sequences | Set explicitly: `fig.update_layout(colorway=px.colors.qualitative.Plotly)` |
| Animation slow/choppy | Too many points per frame | Reduce data points or use `px.scatter` with `render_mode="webgl"` for large datasets |

## Related Skills

- **matplotlib** — static, publication-quality figures for journal submissions (more control over typography and layout)
- **seaborn** — statistical visualization with grammar-of-graphics approach (built on matplotlib)
- **scientific-visualization** — general principles of scientific figure design and color theory

## References

- [Plotly Python documentation](https://plotly.com/python/) — official guides and API reference
- [Plotly Express API](https://plotly.com/python-api-reference/plotly.express.html) — high-level API reference
- [Dash documentation](https://dash.plotly.com/) — interactive web application framework
- [Plotly community forum](https://community.plotly.com/) — community support and examples
