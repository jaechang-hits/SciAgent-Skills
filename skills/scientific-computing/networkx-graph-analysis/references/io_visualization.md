# NetworkX — I/O Formats & Advanced Visualization Reference

Supplementary reference for the NetworkX Graph Analysis skill. Core I/O (edge list, GraphML, JSON, pandas, NumPy/SciPy) is in Module 6 of the main SKILL.md. Basic matplotlib drawing is in Module 7.

---

## Part 1: I/O Formats

### Adjacency List

Simple text format: each line lists a node followed by its neighbors.

```python
import networkx as nx

G = nx.read_adjlist('graph.adjlist', nodetype=int)
G = nx.read_adjlist('graph.adjlist', create_using=nx.DiGraph())  # directed
nx.write_adjlist(G, 'graph.adjlist')
```

Example file: `0 1 2` means node 0 connects to nodes 1 and 2.

### GML / GEXF / Pajek / LEDA

All preserve attributes (GML, GEXF fully; Pajek, LEDA partially). GML is widely supported by Gephi, Cytoscape, igraph. GEXF adds dynamic/temporal support for Gephi.

```python
# GML — full attribute preservation
G = nx.read_gml('graph.gml');  nx.write_gml(G, 'graph.gml')

# GEXF — Gephi dynamic graphs
G = nx.read_gexf('graph.gexf');  nx.write_gexf(G, 'graph.gexf')

# Pajek (.net) — legacy Pajek software
G = nx.read_pajek('graph.net');  nx.write_pajek(G, 'graph.net')

# LEDA — LEDA graph library (C++)
G = nx.read_leda('graph.leda');  nx.write_leda(G, 'graph.leda')
```

### Cytoscape JSON

Export/import for Cytoscape desktop or Cytoscape.js web visualization.

```python
import json, networkx as nx

data = nx.cytoscape_data(G)
with open('cytoscape.json', 'w') as f:
    json.dump(data, f)

with open('cytoscape.json', 'r') as f:
    G = nx.cytoscape_graph(json.load(f))
```

### DOT Format (Graphviz)

For Graphviz rendering. Requires `pydot` or `pygraphviz`.

```python
import networkx as nx
from networkx.drawing.nx_pydot import to_pydot

nx.drawing.nx_pydot.write_dot(G, 'graph.dot')      # write
G = nx.drawing.nx_pydot.read_dot('graph.dot')       # read
to_pydot(G).write_png('graph.png')                  # render to image
```

### Matrix Market Format

Standard sparse matrix format for exchanging adjacency matrices with SciPy/MATLAB.

```python
from scipy.io import mmread, mmwrite
import networkx as nx

G = nx.from_scipy_sparse_array(mmread('graph.mtx'))        # read
mmwrite('graph.mtx', nx.to_scipy_sparse_array(G))          # write
```

### CSV Files (Custom)

For non-standard CSV edge data, use manual reading with the `csv` module.

```python
import csv
import networkx as nx

# Read edges from CSV
G = nx.Graph()
with open('edges.csv', 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        G.add_edge(row['source'], row['target'],
                   weight=float(row['weight']))

# Write edges to CSV
with open('edges.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['source', 'target', 'weight'])
    for u, v, data in G.edges(data=True):
        writer.writerow([u, v, data.get('weight', 1.0)])
```

### Database / SQL Integration

Load and save graphs via SQL databases using pandas as an intermediary.

```python
import sqlite3
import pandas as pd
import networkx as nx

# Read from SQL database
conn = sqlite3.connect('network.db')
df = pd.read_sql_query("SELECT source, target, weight FROM edges", conn)
G = nx.from_pandas_edgelist(df, 'source', 'target', edge_attr='weight')
conn.close()

# Write to SQL database
df = nx.to_pandas_edgelist(G)
conn = sqlite3.connect('network.db')
df.to_sql('edges', conn, if_exists='replace', index=False)
conn.close()
```

### Compressed I/O (gzip)

Use gzip with any text-based format for large graphs.

```python
import gzip, networkx as nx

with gzip.open('graph.adjlist.gz', 'wt') as f:
    nx.write_adjlist(G, f)
with gzip.open('graph.adjlist.gz', 'rt') as f:
    G = nx.read_adjlist(f)
# Works with edge lists too: nx.write_edgelist(G, gzip.open(..., 'wt'))
```

### Format Selection Guide

| Format | Attributes | Best For |
|--------|-----------|----------|
| Adjacency List | No | Simple unweighted graphs, quick inspection |
| Edge List | Weight only | Weighted graphs (Module 6) |
| GML | Full | Complete serialization with all metadata |
| GraphML | Full | Interop: Gephi, yEd, Cytoscape (Module 6) |
| GEXF | Full + dynamic | Gephi, temporal/dynamic networks |
| JSON (node-link) | Full | Web apps, d3.js (Module 6) |
| Cytoscape JSON | Full | Cytoscape desktop / Cytoscape.js |
| DOT | Partial | Graphviz rendering |
| Pajek / LEDA | Partial | Legacy software |
| CSV | Custom | Custom data pipelines |
| Matrix Market | Matrix only | Sparse matrix exchange (SciPy/MATLAB) |
| Pandas/NumPy/SciPy | Varies | In-memory processing (Module 6) |
| Pickle | Full | Python-only storage (use `pickle` directly) |
| SQL | Custom | Relational database integration |

**Decision heuristic**: Attributes preserved? GML/GraphML/GEXF. Web? JSON/Cytoscape JSON. Visualization? DOT. Sparse math? Matrix Market. Quick text exchange? Edge list or adjacency list.

---

## Part 2: Advanced Visualization

### Plotly Interactive Network

Creates interactive HTML plots with hover, zoom, and pan. Ideal for exploratory analysis.

```python
import networkx as nx
import plotly.graph_objects as go

G = nx.karate_club_graph()
pos = nx.spring_layout(G, seed=42)

# Edge traces
edge_x, edge_y = [], []
for u, v in G.edges():
    x0, y0 = pos[u]
    x1, y1 = pos[v]
    edge_x.extend([x0, x1, None])
    edge_y.extend([y0, y1, None])

edge_trace = go.Scatter(
    x=edge_x, y=edge_y,
    line=dict(width=0.5, color='#888'),
    hoverinfo='none', mode='lines')

# Node traces colored by degree
node_x = [pos[n][0] for n in G.nodes()]
node_y = [pos[n][1] for n in G.nodes()]
node_deg = [G.degree(n) for n in G.nodes()]

node_trace = go.Scatter(
    x=node_x, y=node_y, mode='markers',
    hoverinfo='text',
    marker=dict(showscale=True, colorscale='YlGnBu',
                size=10, color=node_deg,
                colorbar=dict(thickness=15, title='Degree'),
                line_width=2))
node_trace.text = [f"Node {n}, degree {G.degree(n)}" for n in G.nodes()]

fig = go.Figure(data=[edge_trace, node_trace],
                layout=go.Layout(showlegend=False, hovermode='closest',
                                 margin=dict(b=0, l=0, r=0, t=0)))
fig.write_html('interactive_network.html')
print("Saved interactive_network.html")
```

### PyVis Interactive HTML

Quick interactive visualization with physics simulation controls.

```python
from pyvis.network import Network
import networkx as nx

G = nx.karate_club_graph()

# Create PyVis network from NetworkX graph
net = Network(notebook=True, height='750px', width='100%')
net.from_nx(G)

# Add interactive physics controls
net.show_buttons(filter_=['physics'])
net.show('graph.html')
print("Saved graph.html")
```

### Graphviz Layouts

Specialized layout algorithms. Requires `graphviz` and `pydot`/`pygraphviz`.

```python
import networkx as nx, matplotlib.pyplot as plt
from networkx.drawing.nx_pydot import graphviz_layout

G = nx.karate_club_graph()
# Programs: neato (force), dot (hierarchical), fdp, sfdp (scalable), circo, twopi
pos = graphviz_layout(G, prog='neato')
nx.draw(G, pos=pos, with_labels=True, node_size=300, font_size=8)
plt.savefig('graphviz_layout.png', dpi=300, bbox_inches='tight'); plt.close()

# Hierarchical layout for trees/DAGs
T = nx.random_tree(n=20, seed=42)
pos_tree = graphviz_layout(T, prog='dot')
nx.draw(T, pos=pos_tree, with_labels=True, arrows=True)
plt.savefig('tree_layout.png', dpi=300, bbox_inches='tight'); plt.close()
```

### 3D Network Visualization

```python
import numpy as np, networkx as nx, matplotlib.pyplot as plt

G = nx.karate_club_graph()
pos = nx.spring_layout(G, dim=3, seed=42)
node_xyz = np.array([pos[v] for v in G.nodes()])

fig = plt.figure(figsize=(10, 8))
ax = fig.add_subplot(111, projection='3d')
for u, v in G.edges():
    coords = np.array([pos[u], pos[v]])
    ax.plot(*coords.T, color='gray', alpha=0.5)
ax.scatter(*node_xyz.T, s=100, c=[G.degree(n) for n in G.nodes()],
           cmap='viridis', edgecolors='black')
ax.set_axis_off()
plt.savefig('network_3d.png', dpi=300, bbox_inches='tight'); plt.close()
```

### Bipartite Layout

Two-column layout with color-coded node sets.

```python
import networkx as nx, matplotlib.pyplot as plt

B = nx.Graph()
B.add_nodes_from([1, 2, 3, 4], bipartite=0)
B.add_nodes_from(['a', 'b', 'c', 'd', 'e'], bipartite=1)
B.add_edges_from([(1,'a'),(1,'b'),(2,'b'),(2,'c'),(3,'d'),(4,'e')])

top = [n for n, d in B.nodes(data=True) if d['bipartite'] == 0]
bottom = [n for n, d in B.nodes(data=True) if d['bipartite'] == 1]
pos = {n: (0, i) for i, n in enumerate(top)}
pos.update({n: (1, i) for i, n in enumerate(bottom)})

colors = ['lightblue' if B.nodes[n]['bipartite'] == 0 else 'lightgreen'
          for n in B.nodes()]
nx.draw(B, pos=pos, with_labels=True, node_color=colors, node_size=600)
plt.savefig('bipartite.png', dpi=300, bbox_inches='tight'); plt.close()
```

### Community Coloring

Assign distinct colors per detected community.

```python
import networkx as nx, matplotlib.pyplot as plt
from networkx.algorithms import community

G = nx.karate_club_graph()
comms = community.greedy_modularity_communities(G)
palette = ['#e41a1c','#377eb8','#4daf4a','#984ea3','#ff7f00','#a65628']
cmap = {}
for i, c in enumerate(comms):
    for node in c:
        cmap[node] = palette[i % len(palette)]

pos = nx.spring_layout(G, seed=42)
nx.draw(G, pos=pos, node_color=[cmap[n] for n in G.nodes()],
        with_labels=True, node_size=400, edge_color='gray', alpha=0.8)
plt.title(f'{len(comms)} communities detected')
plt.savefig('community_coloring.png', dpi=300, bbox_inches='tight'); plt.close()
```

### Subgraph Highlighting

Emphasize a subgraph over the full graph background.

```python
import networkx as nx, matplotlib.pyplot as plt

G = nx.karate_club_graph()
pos = nx.spring_layout(G, seed=42)
H = G.subgraph([0, 1, 2, 3, 7, 13])  # subgraph to highlight

nx.draw_networkx_nodes(G, pos, node_color='lightgray', node_size=200)
nx.draw_networkx_edges(G, pos, alpha=0.15)
nx.draw_networkx_nodes(H, pos, node_color='red', node_size=500)
nx.draw_networkx_edges(H, pos, edge_color='red', width=2.5)
nx.draw_networkx_labels(G, pos, font_size=7)
plt.axis('off')
plt.savefig('subgraph_highlight.png', dpi=300, bbox_inches='tight'); plt.close()
```

### Multi-Panel Layout Comparison

```python
import networkx as nx, matplotlib.pyplot as plt

G = nx.karate_club_graph()
fig, axes = plt.subplots(1, 3, figsize=(18, 6))
for ax, (title, pos) in zip(axes, [
    ('Circular', nx.circular_layout(G)),
    ('Spring', nx.spring_layout(G, seed=42)),
    ('Spectral', nx.spectral_layout(G))]):
    nx.draw(G, pos=pos, ax=ax, with_labels=True,
            node_color='lightblue', node_size=300, font_size=8)
    ax.set_title(title, fontsize=14); ax.axis('off')
plt.tight_layout()
plt.savefig('layouts_comparison.png', dpi=300, bbox_inches='tight'); plt.close()
```

### Edge Labels

Display edge attributes (weights, types) on edges.

```python
import networkx as nx, matplotlib.pyplot as plt

G = nx.Graph()
G.add_edge('A', 'B', weight=0.9); G.add_edge('B', 'C', weight=0.4)
G.add_edge('A', 'C', weight=0.7)

pos = nx.spring_layout(G, seed=42)
nx.draw_networkx_nodes(G, pos, node_size=600, node_color='lightblue')
nx.draw_networkx_labels(G, pos, font_size=12)
nx.draw_networkx_edges(G, pos)
nx.draw_networkx_edge_labels(G, pos,
    edge_labels=nx.get_edge_attributes(G, 'weight'), font_size=10)
plt.axis('off')
plt.savefig('edge_labels.png', dpi=300, bbox_inches='tight'); plt.close()
```

### Directed Graph Arrows

Customize arrow styles for directed graphs.

```python
import networkx as nx, matplotlib.pyplot as plt

D = nx.DiGraph([('A','B'),('B','C'),('C','A'),('A','D'),('D','B')])
pos = nx.spring_layout(D, seed=42)
nx.draw(D, pos=pos, with_labels=True,
        node_size=700, node_color='lightyellow', edgecolors='black',
        arrows=True, arrowsize=25, arrowstyle='->',
        connectionstyle='arc3,rad=0.1', edge_color='steelblue', width=2)
plt.axis('off')
plt.savefig('directed_arrows.png', dpi=300, bbox_inches='tight'); plt.close()
```

---

Condensed from io.md (441 lines) + visualization.md (529 lines). Retained: adjacency list, GML, GEXF, Pajek, LEDA, Cytoscape JSON, DOT/Graphviz, Matrix Market, CSV, database/SQL, compressed gzip, format selection guide, Plotly interactive, PyVis HTML, Graphviz layouts, 3D networks, bipartite layout, community coloring, subgraph highlighting, multi-panel figures, edge labels, directed arrows. Omitted from io.md: edge list / GraphML / JSON / pandas / NumPy-SciPy I/O (relocated to SKILL.md Module 6), `write_gpickle`/`read_gpickle` (deprecated in NetworkX 3.0), `read_shp`/`write_shp` (removed in NetworkX 3.0; use geopandas), pickle convenience functions (use `pickle` directly), incremental loading pattern, error handling boilerplate. Omitted from visualization.md: basic matplotlib drawing, layout algorithms, node customization (colors/sizes/shapes/borders), edge customization (colors/widths/styles) -- all relocated to SKILL.md Module 7 and Key Concepts; visualization best practices prose. Combined coverage: ~390 retained / 970 original lines = ~40.2%.
