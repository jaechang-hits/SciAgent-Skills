---
name: "networkx-graph-analysis"
description: "Graph and network analysis toolkit: create, manipulate, and analyze complex networks. Four graph types (directed, undirected, multi-edge), centrality measures, shortest paths, community detection, graph generators, I/O (GraphML, GML, edge list, pandas, NumPy), visualization with matplotlib. For large-scale graphs (100K+ nodes) use igraph or graph-tool; for graph neural networks use PyG."
license: BSD-3-Clause
---

# NetworkX Graph Analysis

## Overview

NetworkX is a Python library for creating, manipulating, and analyzing complex networks and graphs. It provides data structures for undirected, directed, and multi-edge graphs along with a comprehensive collection of graph algorithms, generators, and I/O utilities. Use NetworkX when working with relationship data in social networks, biological interaction networks, transportation systems, citation graphs, or any domain involving pairwise entity relationships.

## When to Use

- Analyzing protein-protein interaction networks, gene regulatory networks, or metabolic pathways
- Computing centrality measures (degree, betweenness, PageRank) to identify important nodes
- Finding shortest paths or optimal routes in transportation or communication networks
- Detecting communities or clusters in social networks or co-expression data
- Generating synthetic networks (scale-free, small-world, random) for simulation or null models
- Reading and writing graph data in standard formats (GraphML, GML, edge lists, JSON)
- Visualizing network topology with node/edge attribute mapping
- Checking graph properties: connectivity, planarity, isomorphism, DAG structure
- For large-scale graphs (100K+ nodes) where speed is critical, use `igraph` or `graph-tool` instead
- For billion-edge graphs or GPU-accelerated analytics, use `graph-tool` with OpenMP or `cuGraph`
- For graph neural networks and deep learning on graphs, use `torch-geometric-graph-neural-networks`

## Prerequisites

- **Python packages**: `networkx`, `matplotlib`, `scipy`, `pandas`, `numpy`
- **Optional**: `pydot` or `pygraphviz` (Graphviz layouts)

```bash
pip install networkx matplotlib scipy pandas numpy
```

## Quick Start

```python
import networkx as nx

# Create a graph and add edges with weights
G = nx.karate_club_graph()
print(f"Nodes: {G.number_of_nodes()}, Edges: {G.number_of_edges()}")
# Nodes: 34, Edges: 78

# Compute centrality and find most central node
bc = nx.betweenness_centrality(G)
top_node = max(bc, key=bc.get)
print(f"Most central node: {top_node}, betweenness: {bc[top_node]:.3f}")

# Detect communities
from networkx.algorithms import community
comms = community.greedy_modularity_communities(G)
print(f"Communities found: {len(comms)}")
```

## Core API

### Module 1: Graph Creation and Types

```python
import networkx as nx

# Undirected graph (most common)
G = nx.Graph()
G.add_node("protein_A", type="kinase", weight=1.5)
G.add_nodes_from(["protein_B", "protein_C"])
G.add_edge("protein_A", "protein_B", weight=0.9, interaction="phosphorylation")
G.add_edges_from([("protein_B", "protein_C"), ("protein_A", "protein_C")])
print(f"Nodes: {G.number_of_nodes()}, Edges: {G.number_of_edges()}")
# Nodes: 3, Edges: 3

# Directed graph (gene regulation, citations)
D = nx.DiGraph()
D.add_edges_from([("TF1", "geneA"), ("TF1", "geneB"), ("TF2", "geneA")])
print(f"TF1 out-degree: {D.out_degree('TF1')}")  # 2

# MultiGraph (multiple relationship types between same nodes)
M = nx.MultiGraph()
M.add_edge("A", "B", key="binding", affinity=0.8)
M.add_edge("A", "B", key="regulation", effect="inhibition")
print(f"Edges between A-B: {M.number_of_edges('A', 'B')}")  # 2
```

### Module 2: Node and Edge Operations

```python
import networkx as nx
G = nx.karate_club_graph()

# Query structure
print(f"Degree of node 0: {G.degree(0)}")
print(f"Neighbors of node 0: {list(G.neighbors(0))[:5]}")
print(f"Has edge 0-1: {G.has_edge(0, 1)}")

# Set and get attributes
G.nodes[0]["role"] = "instructor"
nx.set_node_attributes(G, {0: "high", 33: "high"}, "importance")
G[0][1]["weight"] = 0.95

# Iterate with data
for u, v, data in G.edges(data=True):
    if "weight" in data:
        print(f"  Edge {u}-{v}: weight={data['weight']}")
        break

# Subgraphs (returns read-only view; use .copy() for mutable)
H = G.subgraph([0, 1, 2, 3, 4, 5]).copy()
print(f"Subgraph: {H.number_of_nodes()} nodes, {H.number_of_edges()} edges")
```

### Module 3: Graph Analysis (Centrality)

```python
import networkx as nx
G = nx.karate_club_graph()

degree_c = nx.degree_centrality(G)
between_c = nx.betweenness_centrality(G, weight="weight")
# For large graphs, approximate: nx.betweenness_centrality(G, k=100)
close_c = nx.closeness_centrality(G)
eigen_c = nx.eigenvector_centrality(G, max_iter=1000)
pr = nx.pagerank(G, alpha=0.85)

# Compare top nodes across measures
for name, metric in [("Degree", degree_c), ("Betweenness", between_c),
                     ("Closeness", close_c), ("PageRank", pr)]:
    top = max(metric, key=metric.get)
    print(f"{name:12s}: top node={top}, score={metric[top]:.4f}")
```

### Module 4: Path and Connectivity

```python
import networkx as nx
G = nx.karate_club_graph()

# Shortest path
path = nx.shortest_path(G, source=0, target=33)
length = nx.shortest_path_length(G, source=0, target=33)
print(f"Shortest path 0->33: {path} (length {length})")
print(f"Average shortest path length: {nx.average_shortest_path_length(G):.3f}")

# Connected components
print(f"Connected: {nx.is_connected(G)}")
components = list(nx.connected_components(G))
print(f"Components: {len(components)}, largest: {len(max(components, key=len))}")

# For directed graphs: strong/weak connectivity
D = nx.DiGraph([(0,1),(1,2),(2,0),(3,4)])
print(f"Strongly connected: {list(nx.strongly_connected_components(D))}")

# Connectivity measures
print(f"Node connectivity: {nx.node_connectivity(G)}")
print(f"Edge connectivity: {nx.edge_connectivity(G)}")
```

### Module 5: Community Detection

Partition networks into densely connected groups.

```python
import networkx as nx
from networkx.algorithms import community
import itertools

G = nx.karate_club_graph()

# Greedy modularity maximization
comms_greedy = community.greedy_modularity_communities(G)
mod_score = community.modularity(G, comms_greedy)
print(f"Greedy: {len(comms_greedy)} communities, modularity={mod_score:.4f}")

# Label propagation (fast, non-deterministic)
comms_lpa = community.label_propagation_communities(G)
print(f"Label propagation: {len(list(comms_lpa))} communities")

# Girvan-Newman (hierarchical, edge betweenness removal)
gn = community.girvan_newman(G)
# Get first level of partition
first_level = next(gn)
print(f"Girvan-Newman first split: {len(first_level)} groups")
print(f"  Sizes: {[len(c) for c in first_level]}")
```

### Module 6: I/O and Serialization

```python
import networkx as nx
import pandas as pd
import json

G = nx.karate_club_graph()

# Edge list (simple text format)
nx.write_edgelist(G, "karate.edgelist")
G_loaded = nx.read_edgelist("karate.edgelist", nodetype=int)

# GraphML (preserves all attributes, XML-based)
nx.write_graphml(G, "karate.graphml")
G_xml = nx.read_graphml("karate.graphml")

# JSON (node-link format, web-friendly for d3.js)
data = nx.node_link_data(G)
with open("karate.json", "w") as f:
    json.dump(data, f)

# Pandas integration
df = pd.DataFrame({"source": [1,2,3], "target": [2,3,4], "weight": [0.5,1.0,0.75]})
G_pd = nx.from_pandas_edgelist(df, "source", "target", edge_attr="weight")
df_out = nx.to_pandas_edgelist(G_pd)
print(f"Pandas round-trip: {len(df_out)} edges")

# NumPy/SciPy matrices
A = nx.to_numpy_array(G)
print(f"Adjacency matrix shape: {A.shape}")
A_sparse = nx.to_scipy_sparse_array(G, format="csr")  # Memory-efficient
```

### Module 7: Visualization

```python
import networkx as nx
import matplotlib.pyplot as plt

G = nx.karate_club_graph()
pos = nx.spring_layout(G, seed=42)

# Color by degree, size by betweenness centrality
bc = nx.betweenness_centrality(G)
fig, ax = plt.subplots(figsize=(10, 8))
nx.draw(G, pos=pos, ax=ax,
        node_color=[G.degree(n) for n in G.nodes()], cmap=plt.cm.viridis,
        node_size=[3000 * bc[n] + 100 for n in G.nodes()],
        edge_color="gray", alpha=0.8, with_labels=True, font_size=8)
plt.tight_layout()
plt.savefig("network.png", dpi=300, bbox_inches="tight")
plt.savefig("network.pdf", bbox_inches="tight")  # Vector format
print("Saved network.png and network.pdf")
```

### Module 8: Generators

```python
import networkx as nx

# Erdos-Renyi random graph: n nodes, edge probability p
G_er = nx.erdos_renyi_graph(n=200, p=0.05, seed=42)
print(f"ER: {G_er.number_of_nodes()} nodes, {G_er.number_of_edges()} edges")

# Barabasi-Albert scale-free (power-law degree distribution)
G_ba = nx.barabasi_albert_graph(n=200, m=3, seed=42)

# Watts-Strogatz small-world
G_ws = nx.watts_strogatz_graph(n=200, k=6, p=0.1, seed=42)
print(f"WS clustering: {nx.average_clustering(G_ws):.3f}")

# Stochastic block model (community structure)
sizes, probs = [50, 50, 50], [[0.25,0.05,0.02],[0.05,0.35,0.07],[0.02,0.07,0.40]]
G_sbm = nx.stochastic_block_model(sizes, probs, seed=42)

# Built-in datasets and classic graphs
G_karate = nx.karate_club_graph()       # Zachary's karate club
G_grid = nx.grid_2d_graph(5, 7)         # 2D lattice
G_tree = nx.random_tree(n=50, seed=42)  # Random tree
G_geo = nx.random_geometric_graph(n=100, radius=0.2, seed=42)
# See references/algorithms_generators.md for full generator catalog
```

## Key Concepts

### Graph Types

| Class | Directed | Multi-edge | Self-loops | Use Case |
|-------|----------|------------|------------|----------|
| `Graph` | No | No | Yes | Undirected networks: social, PPI |
| `DiGraph` | Yes | No | Yes | Gene regulation, citations, web |
| `MultiGraph` | No | Yes | Yes | Multiple relationship types |
| `MultiDiGraph` | Yes | Yes | Yes | Transportation with routes |

### Attribute Patterns

Attributes are stored as dictionaries at graph, node, and edge levels:

```python
import networkx as nx
G = nx.Graph(name="example")              # Graph-level attribute
G.add_node(1, label="hub", weight=1.5)    # Node attributes
G.add_edge(1, 2, weight=0.8, type="ppi")  # Edge attributes

# Bulk set/get
nx.set_node_attributes(G, {1: "red", 2: "blue"}, "color")
colors = nx.get_node_attributes(G, "color")  # {1: 'red', 2: 'blue'}
```

### Layout Algorithms

| Layout | Function | Best For |
|--------|----------|----------|
| Spring (force-directed) | `spring_layout(G, seed=42)` | General networks |
| Circular | `circular_layout(G)` | Regular graphs, cycles |
| Kamada-Kawai | `kamada_kawai_layout(G)` | Small-medium networks |
| Spectral | `spectral_layout(G)` | Highlighting clusters |
| Shell (concentric) | `shell_layout(G, nlist=[[...],[...]])` | Layered/hierarchical |
| Planar | `planar_layout(G)` | Planar graphs only |

## Common Workflows

### Workflow 1: Social Network Analysis

**Goal**: Identify influential actors, detect communities, and visualize.

```python
import networkx as nx
import matplotlib.pyplot as plt
from networkx.algorithms import community

# Step 1: Load network and basic stats
G = nx.karate_club_graph()
print(f"Network: {G.number_of_nodes()} actors, {G.number_of_edges()} ties")
print(f"Density: {nx.density(G):.4f}, Clustering: {nx.average_clustering(G):.4f}")

# Step 2: Identify influential nodes
bc = nx.betweenness_centrality(G)
top_bc = sorted(bc.items(), key=lambda x: x[1], reverse=True)[:5]
print("Top 5 by betweenness:", [(n, f"{s:.3f}") for n, s in top_bc])

# Step 3: Detect communities
comms = community.greedy_modularity_communities(G)
print(f"Communities: {len(comms)}, modularity: {community.modularity(G, comms):.4f}")

# Step 4: Visualize with community coloring
pos = nx.spring_layout(G, seed=42)
fig, ax = plt.subplots(figsize=(10, 8))
for i, comm in enumerate(comms):
    nx.draw_networkx_nodes(G, pos, nodelist=list(comm), ax=ax,
                           node_color=[plt.cm.Set2(i)]*len(comm), node_size=400)
nx.draw_networkx_edges(G, pos, ax=ax, alpha=0.3)
nx.draw_networkx_labels(G, pos, ax=ax, font_size=8)
plt.axis("off")
plt.tight_layout()
plt.savefig("social_network_analysis.png", dpi=300, bbox_inches="tight")
print("Saved social_network_analysis.png")
```

### Workflow 2: Biological Interaction Network

**Goal**: Build a PPI network from tabular data, analyze topology, and identify hub proteins.

```python
import networkx as nx
import pandas as pd

# Step 1: Load interaction data from DataFrame
interactions = pd.DataFrame({
    "protein_a": ["TP53","TP53","BRCA1","BRCA1","MDM2","ATM","ATM","CHEK2","RB1","CDK2"],
    "protein_b": ["MDM2","BRCA1","ATM","CHEK2","RB1","CHEK2","BRCA2","CDC25A","CDK2","CCNA2"],
    "score": [0.99, 0.95, 0.92, 0.88, 0.91, 0.97, 0.85, 0.90, 0.87, 0.93]
})
G = nx.from_pandas_edgelist(interactions, "protein_a", "protein_b",
                             edge_attr="score")
print(f"PPI network: {G.number_of_nodes()} proteins, {G.number_of_edges()} interactions")

# Step 2: Network statistics
print(f"Connected: {nx.is_connected(G)}")
print(f"Diameter: {nx.diameter(G)}")
print(f"Avg path length: {nx.average_shortest_path_length(G):.2f}")
print(f"Transitivity: {nx.transitivity(G):.4f}")

# Step 3: Hub identification (multiple centrality measures)
degree_c = nx.degree_centrality(G)
between_c = nx.betweenness_centrality(G)
close_c = nx.closeness_centrality(G)

results = pd.DataFrame({
    "protein": list(G.nodes()),
    "degree_centrality": [degree_c[n] for n in G.nodes()],
    "betweenness": [between_c[n] for n in G.nodes()],
    "closeness": [close_c[n] for n in G.nodes()],
}).sort_values("betweenness", ascending=False)
print("\nHub proteins:")
print(results.head(5).to_string(index=False))

# Step 4: Export for downstream analysis
nx.write_graphml(G, "ppi_network.graphml")
results.to_csv("protein_centrality.csv", index=False)
print("Exported ppi_network.graphml and protein_centrality.csv")
```

## Key Parameters

| Parameter | Module | Default | Range / Options | Effect |
|-----------|--------|---------|-----------------|--------|
| `weight` | Paths/Centrality | `None` | Edge attribute name | Use weighted edges for path/centrality calculations |
| `alpha` | `pagerank` | `0.85` | `0.0`-`1.0` | Damping factor; lower = more uniform distribution |
| `k` | `betweenness_centrality` | `None` | `int` | Sample k nodes for approximation on large graphs |
| `max_iter` | `eigenvector_centrality` | `100` | `int` | Max iterations for convergence |
| `seed` | Generators/Layouts | `None` | `int` | Random seed for reproducibility |
| `n` / `p` / `m` | ER/BA generators | varies | `int`/`float` | Node count, edge probability, edges per new node |
| `k` / `p` | Watts-Strogatz | varies | `int`/`float` | Nearest neighbors, rewiring probability |
| `nodetype` | `read_edgelist` | `str` | `int`, `float`, `str` | Type conversion for node identifiers |
| `edge_attr` | `from_pandas_edgelist` | `None` | Column name(s) | Edge attribute columns to include from DataFrame |
| `format` | `to_scipy_sparse_array` | `"csc"` | `"csr"`, `"csc"`, `"coo"` | Sparse matrix format |

## Best Practices

1. **Always set random seeds** for reproducible generators and layouts: `seed=42` in both `erdos_renyi_graph()` and `spring_layout()`.

2. **Use approximate algorithms for large graphs**: `nx.betweenness_centrality(G, k=500)` samples k nodes instead of all pairs.

3. **Prefer `from_pandas_edgelist`** over manual `add_edge` loops for bulk data loading -- handles attributes cleanly and is faster.

4. **Copy subgraphs before modification**: `G.subgraph(nodes)` returns a read-only view; call `.copy()` for a mutable independent graph.

5. **Use GraphML or GML for persistent storage** to preserve all node/edge attributes. Edge lists lose metadata unless explicitly handled.

6. **Convert graph types explicitly**: `D.to_undirected()` (DiGraph -> Graph), `nx.Graph(M)` (MultiGraph -> Graph, collapses multi-edges).

7. **Use sparse matrices for large adjacency exports**: `to_scipy_sparse_array()` is far more memory-efficient than `to_numpy_array()`.

8. **Anti-pattern -- Don't use `nx.info()`**: Deprecated; use `G.number_of_nodes()`, `G.number_of_edges()`, `nx.density(G)` directly.

9. **Anti-pattern -- Don't assume node ordering**: Algorithms may return results in different orders. Always index by node key, not position.

## Common Recipes

### Recipe: Minimum Spanning Tree

Extract the minimum spanning tree and compare to the original graph.

```python
import networkx as nx

# Create weighted graph
G = nx.erdos_renyi_graph(50, 0.15, seed=42)
for u, v in G.edges():
    G[u][v]["weight"] = round(nx.utils.py_random_state(42).random(), 2)

mst = nx.minimum_spanning_tree(G, weight="weight")
print(f"Original: {G.number_of_edges()} edges")
print(f"MST: {mst.number_of_edges()} edges")
total_weight = sum(d["weight"] for _, _, d in mst.edges(data=True))
print(f"MST total weight: {total_weight:.2f}")
```

### Recipe: Graph Coloring and Cliques

Find cliques and compute graph coloring.

```python
import networkx as nx

G = nx.karate_club_graph()

# Find all maximal cliques
cliques = list(nx.find_cliques(G))
print(f"Maximal cliques: {len(cliques)}")
largest_clique = max(cliques, key=len)
print(f"Largest clique size: {len(largest_clique)}, nodes: {largest_clique}")

# Greedy graph coloring
coloring = nx.greedy_color(G, strategy="largest_first")
n_colors = max(coloring.values()) + 1
print(f"Chromatic number (greedy upper bound): {n_colors}")
```

### Recipe: DAG and Topological Sort

Build a directed acyclic graph and find execution order.

```python
import networkx as nx

# Task dependency DAG
D = nx.DiGraph()
D.add_edges_from([
    ("download_data", "preprocess"),
    ("download_data", "validate"),
    ("preprocess", "analyze"),
    ("validate", "analyze"),
    ("analyze", "visualize"),
    ("analyze", "report"),
    ("visualize", "report"),
])

print(f"Is DAG: {nx.is_directed_acyclic_graph(D)}")
order = list(nx.topological_sort(D))
print(f"Execution order: {order}")

# Find all paths from start to end
paths = list(nx.all_simple_paths(D, "download_data", "report"))
print(f"Paths to report: {len(paths)}")
for p in paths:
    print(f"  {' -> '.join(p)}")
```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `NetworkXError: Graph is not connected` | Algorithm requires connected graph | Extract largest component: `G.subgraph(max(nx.connected_components(G), key=len)).copy()` |
| `PowerIterationFailedConvergence` | Eigenvector/PageRank did not converge | Increase `max_iter` (e.g., 1000) or check for disconnected components |
| Very slow centrality computation | O(n*m) complexity on large graphs | Use `k` parameter for sampling: `betweenness_centrality(G, k=500)` |
| `nx.NetworkXNotImplemented` | Algorithm not available for graph type | Convert graph type: `G.to_undirected()` or `G.to_directed()` |
| Memory error on large graphs | Dense adjacency matrix | Use `to_scipy_sparse_array()` instead of `to_numpy_array()` |
| Node IDs read as strings from file | `read_edgelist` defaults to `str` | Pass `nodetype=int`: `nx.read_edgelist(f, nodetype=int)` |
| Community detection returns frozen sets | Normal return type for communities | Convert: `[list(c) for c in communities]` |
| Self-loops in generated graphs | Configuration model allows self-loops | Remove: `G.remove_edges_from(nx.selfloop_edges(G))` |
| Visualization too cluttered | Too many nodes/edges | Filter to subgraph, adjust `alpha`, increase figure size, or use interactive tools (Plotly, PyVis) |

## Bundled Resources

Migrated from original entry (STUB: 436-line main file + 2,014 lines across 5 reference files, main/total = 17.8%).

### references/algorithms_generators.md

Covers: Detailed algorithm parameters for traversal (DFS/BFS), cycles, cliques, graph coloring, isomorphism, matching/covering, tree algorithms (MST variants). Full generator catalog: classic graphs, lattice/grid, tree, bipartite, degree sequence, graph operations (union, compose, complement, products).
Relocated inline: Core algorithms (centrality, paths, connectivity, community, flow) -> Core API Modules 3-5. Core generators (ER, BA, WS, SBM) -> Module 8.
Omitted: A* heuristic customization, Bellman-Ford negative weights -- consult official docs.

**Original file disposition**:
- `algorithms.md` (383 lines): Top algorithms relocated to Core API Modules 3-5 + Recipes. Remaining (traversal, cliques, coloring, isomorphism, matching, cycles, trees) -> this reference.
- `generators.md` (378 lines): Core generators relocated to Module 8. Full catalog (classic, lattice, tree, bipartite, degree sequence, operators) -> this reference.

### references/io_visualization.md

Covers: All I/O formats (adjacency list, GEXF, Pajek, LEDA, Cytoscape JSON, DOT/Graphviz, Matrix Market, CSV, database/SQL, compressed gzip). Format selection guide. Advanced visualization: Plotly interactive, PyVis HTML, Graphviz layouts, 3D networks, bipartite layout, community coloring, subgraph highlighting, multi-panel figures, edge labels, directed arrows.
Relocated inline: Core I/O (edge list, GraphML, JSON, pandas, NumPy/SciPy) -> Module 6. Basic matplotlib -> Module 7.
Omitted: `write_gpickle`/`read_gpickle` (deprecated), `read_shp`/`write_shp` (removed in NetworkX 3.0; use geopandas).

**Original file disposition**:
- `io.md` (441 lines): Core formats relocated to Module 6. Remaining formats + format selection guide -> this reference.
- `visualization.md` (529 lines): Basic matplotlib relocated to Module 7. Advanced techniques (Plotly, PyVis, 3D, bipartite, community coloring) -> this reference.

### Fully consolidated original file

- `graph-basics.md` (283 lines): Fully consolidated into main SKILL.md. Graph types -> Key Concepts. Node/edge operations, attributes, subgraphs -> Core API Modules 1-2. Diagnostics -> Common Workflows. Memory/float-point considerations -> Best Practices + Troubleshooting. Omitted: `nx.info()` (deprecated).

## Related Skills

- **torch-geometric-graph-neural-networks** -- graph neural networks (GCN, GAT, GraphSAGE) for node/graph classification and link prediction on graph-structured data
- **matplotlib-scientific-plotting** -- advanced figure customization beyond NetworkX's built-in `nx.draw`
- **plotly-interactive-visualization** -- interactive network plots with hover, zoom, and pan
- **pandas** (planned) -- DataFrame operations for preparing edge/node data before graph construction
- **scipy** (planned) -- sparse matrix operations and numerical algorithms used by NetworkX internally

## References

- [NetworkX documentation](https://networkx.org/documentation/latest/) -- official docs and API reference
- [NetworkX tutorial](https://networkx.org/documentation/latest/tutorial.html) -- official getting started guide
- [NetworkX GitHub](https://github.com/networkx/networkx) -- source code and issue tracker
- [NetworkX gallery](https://networkx.org/documentation/latest/auto_examples/index.html) -- example gallery with visualizations
- Hagberg, A., Schult, D., & Swart, P. (2008). Exploring network structure, dynamics, and function using NetworkX. SciPy 2008.
