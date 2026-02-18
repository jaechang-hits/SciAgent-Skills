# NetworkX — Algorithms & Generators Reference

Detailed algorithm parameters and full generator catalog beyond what is covered inline
in the main SKILL.md Core API modules.

---

## Traversal Algorithms

### Depth-First Search (DFS)

```python
import networkx as nx
G = nx.karate_club_graph()

dfs_edges = list(nx.dfs_edges(G, source=0))
dfs_tree = nx.dfs_tree(G, source=0)
dfs_pred = nx.dfs_predecessors(G, source=0)
preorder = list(nx.dfs_preorder_nodes(G, source=0))
postorder = list(nx.dfs_postorder_nodes(G, source=0))
print(f"DFS tree: {dfs_tree.number_of_edges()} edges")
print(f"Preorder first 5: {preorder[:5]}")
```

### Breadth-First Search (BFS)

```python
bfs_edges = list(nx.bfs_edges(G, source=0))
bfs_tree = nx.bfs_tree(G, source=0)
bfs_pred = dict(nx.bfs_predecessors(G, source=0))
bfs_succ = dict(nx.bfs_successors(G, source=0))
print(f"BFS tree: {bfs_tree.number_of_edges()} edges")
```

---

## Cycles and Topological Sorting

```python
import networkx as nx

# Undirected: cycle basis
G = nx.karate_club_graph()
basis = nx.cycle_basis(G)
print(f"Cycle basis size: {len(basis)}")

# Directed: simple cycles
D = nx.DiGraph([(0,1),(1,2),(2,0),(2,3),(3,4),(4,2)])
cycles = list(nx.simple_cycles(D))
print(f"Simple cycles: {len(cycles)}")

# DAG check and topological sort
dag = nx.DiGraph([("a","b"),("a","c"),("b","d"),("c","d")])
print(f"Is DAG: {nx.is_directed_acyclic_graph(dag)}")
topo_order = list(nx.topological_sort(dag))
print(f"Topological order: {topo_order}")

# All topological sorts (iterator, potentially many)
all_topo = list(nx.all_topological_sorts(dag))
print(f"Total topological orderings: {len(all_topo)}")
```

---

## Cliques

```python
import networkx as nx
G = nx.karate_club_graph()

# All maximal cliques (Bron-Kerbosch algorithm)
cliques = list(nx.find_cliques(G))
largest_clique = max(cliques, key=len)
print(f"Maximal cliques: {len(cliques)}, largest size: {len(largest_clique)}")

# Approximate maximum clique (for large graphs, NP-hard exact)
approx_max = nx.approximation.max_clique(G)

# Clique number and per-node clique counts
clique_num = nx.graph_clique_number(G)
clique_counts = nx.node_clique_number(G)
print(f"Clique number: {clique_num}")
```

---

## Graph Coloring

```python
import networkx as nx
G = nx.karate_club_graph()

# Greedy coloring — strategies: 'largest_first', 'smallest_last', 'random_sequential'
for strategy in ["largest_first", "smallest_last", "random_sequential"]:
    coloring = nx.greedy_color(G, strategy=strategy)
    n_colors = max(coloring.values()) + 1
    print(f"Strategy '{strategy}': {n_colors} colors")
```

---

## Isomorphism

```python
import networkx as nx
from networkx.algorithms import isomorphism

# Graph isomorphism
G1 = nx.cycle_graph(6)
G2 = nx.cycle_graph(6)
print(f"Isomorphic: {nx.is_isomorphic(G1, G2)}")

# Get mapping via GraphMatcher
GM = isomorphism.GraphMatcher(G1, G2)
if GM.is_isomorphic():
    print(f"Mapping: {GM.mapping}")

# Subgraph isomorphism
G_large = nx.karate_club_graph()
GM_sub = isomorphism.GraphMatcher(G_large, nx.complete_graph(4))
print(f"Subgraph isomorphic: {GM_sub.subgraph_is_isomorphic()}")

# DiGraph isomorphism
DGM = isomorphism.DiGraphMatcher(
    nx.DiGraph([(0,1),(1,2)]), nx.DiGraph([(5,6),(6,7)])
)
print(f"DiGraph isomorphic: {DGM.is_isomorphic()}")
```

---

## Matching and Covering

```python
import networkx as nx
G = nx.karate_club_graph()

# Maximum weight matching
matching = nx.max_weight_matching(G)
print(f"Matching size: {len(matching)}, valid: {nx.is_matching(G, matching)}")
print(f"Perfect matching: {nx.is_perfect_matching(G, matching)}")

# Minimum weighted vertex cover (approximation)
min_vc = nx.approximation.min_weighted_vertex_cover(G)
print(f"Min vertex cover size: {len(min_vc)}")

# Minimum edge dominating set (approximation)
min_eds = nx.approximation.min_edge_dominating_set(G)
print(f"Min edge dominating set size: {len(min_eds)}")
```

---

## Tree Algorithms

### Minimum Spanning Tree Variants

```python
import networkx as nx

G = nx.erdos_renyi_graph(30, 0.2, seed=42)
for u, v in G.edges():
    G[u][v]["weight"] = round(abs(hash((u,v))) % 100 / 10, 1)

# Kruskal's (default) and Prim's algorithm
mst = nx.minimum_spanning_tree(G, weight="weight", algorithm="kruskal")
mst_prim = nx.minimum_spanning_tree(G, weight="weight", algorithm="prim")
mst_weight = sum(d["weight"] for _, _, d in mst.edges(data=True))
print(f"MST: {mst.number_of_edges()} edges, weight={mst_weight:.1f}")

# Maximum spanning tree
max_st = nx.maximum_spanning_tree(G, weight="weight")
max_weight = sum(d["weight"] for _, _, d in max_st.edges(data=True))
print(f"Max spanning tree weight: {max_weight:.1f}")
```

### Tree Properties

```python
T = nx.random_tree(n=20, seed=42)
print(f"Is tree: {nx.is_tree(T)}, Is forest: {nx.is_forest(T)}")

# Arborescence = rooted directed tree
D = nx.bfs_tree(T, source=0)
print(f"Is arborescence: {nx.is_arborescence(D)}")
```

---

## Generators: Classic Graphs

```python
import networkx as nx

# Complete graphs
K10 = nx.complete_graph(10)                        # All-to-all
K_bip = nx.complete_bipartite_graph(5, 7)          # Complete bipartite
K_multi = nx.complete_multipartite_graph(3, 4, 5)  # 3 partitions

# Cycle, path, ring variants
cycle = nx.cycle_graph(20)
path = nx.path_graph(15)
ladder = nx.circular_ladder_graph(10)

# Star and wheel
star = nx.star_graph(19)    # 1 center + 19 leaves
wheel = nx.wheel_graph(10)  # Cycle with central hub

# Special named graphs
petersen = nx.petersen_graph()
dodeca = nx.dodecahedral_graph()
heawood = nx.heawood_graph()
karate = nx.karate_club_graph()
print(f"Petersen: {petersen.number_of_nodes()} nodes, {petersen.number_of_edges()} edges")
```

### Social Network Datasets

```python
G_karate = nx.karate_club_graph()            # Zachary 1977
G_davis = nx.davis_southern_women_graph()     # Bipartite social network
G_flor = nx.florentine_families_graph()      # Marriage/business ties
G_miser = nx.les_miserables_graph()          # Character co-occurrence
```

---

## Generators: Lattice and Grid

```python
import networkx as nx

grid_2d = nx.grid_2d_graph(5, 7)             # 2D grid (35 nodes)
grid_3d = nx.grid_graph(dim=[5, 7, 3])       # 3D grid (105 nodes)
hex_lat = nx.hexagonal_lattice_graph(5, 7)   # Hexagonal lattice
tri_lat = nx.triangular_lattice_graph(5, 7)  # Triangular lattice
hypercube = nx.hypercube_graph(4)            # 4D hypercube (16 nodes, 32 edges)
print(f"2D grid: {grid_2d.number_of_nodes()}, hypercube: {hypercube.number_of_nodes()}")
```

---

## Generators: Tree Graphs

```python
import networkx as nx

tree = nx.random_tree(n=100, seed=42)
binary_tree = nx.balanced_tree(r=2, h=5)     # Binary tree, height 5
ternary = nx.full_rary_tree(r=3, n=100)      # Ternary with 100 nodes
prefix = nx.prefix_tree([[0,1,2],[0,1,3],[0,4]])  # Trie

# Barbell: two complete graphs joined by a path
barbell = nx.barbell_graph(m1=5, m2=3)       # Two K5 + 3-node path
lollipop = nx.lollipop_graph(m=7, n=5)       # K7 + 5-node tail
print(f"Barbell: {barbell.number_of_nodes()} nodes")
```

---

## Generators: Bipartite

```python
import networkx as nx

G_bip = nx.bipartite.random_graph(n=50, m=30, p=0.1, seed=42)
print(f"Random bipartite: {G_bip.number_of_nodes()} nodes, {G_bip.number_of_edges()} edges")

# Configuration model (specify degree sequences per partition)
G_bip_conf = nx.bipartite.configuration_model(aseq=[3,3,2], bseq=[2,2,2,2], seed=42)

# Gnmk: n and m node sets with exactly k edges
G_gnmk = nx.bipartite.gnmk_random_graph(n=10, m=8, k=20, seed=42)
```

---

## Generators: Degree Sequence

```python
import networkx as nx

seq = [3, 3, 3, 3, 2, 2, 2, 1, 1, 1]
print(f"Is graphical: {nx.is_graphical(seq)}")

# Havel-Hakimi (deterministic)
G_hh = nx.havel_hakimi_graph(seq)

# Configuration model (may produce self-loops/multi-edges — clean up)
G_conf = nx.configuration_model(seq, seed=42)
G_conf = nx.Graph(G_conf)
G_conf.remove_edges_from(nx.selfloop_edges(G_conf))

# Directed configuration model
in_seq, out_seq = [2,2,2,1,1], [2,2,1,2,1]
print(f"Is digraphical: {nx.is_digraphical(in_seq, out_seq)}")
G_dconf = nx.directed_configuration_model(in_seq, out_seq, seed=42)

# Biological network models
G_plc = nx.powerlaw_cluster_graph(n=100, m=3, p=0.1, seed=42)
G_dd = nx.duplication_divergence_graph(n=100, p=0.5, seed=42)
```

---

## Generators: Directed Graphs

```python
import networkx as nx

# Directed Erdos-Renyi
G_dir = nx.gnp_random_graph(n=100, p=0.1, directed=True, seed=42)

# Scale-free directed graph
G_sf = nx.scale_free_graph(n=100, seed=42)

# Random tournament (every pair has exactly one directed arc)
G_tourn = nx.random_tournament(n=10, seed=42)
print(f"Tournament edges: {G_tourn.number_of_edges()}")  # n*(n-1)/2 = 45

# Build a DAG by filtering edges u < v
G_raw = nx.gnp_random_graph(n=20, p=0.2, directed=True, seed=42)
dag = nx.DiGraph([(u, v) for (u, v) in G_raw.edges() if u < v])
print(f"Is DAG: {nx.is_directed_acyclic_graph(dag)}")
```

---

## Graph Operations

```python
import networkx as nx

G1 = nx.cycle_graph(5)
G2 = nx.complete_graph(4)

# Union and compose
G_union = nx.disjoint_union(G1, G2)          # Disjoint node sets
G_compose = nx.compose(G1, nx.path_graph(5)) # Overlay, shared nodes merge

# Complement (edges <-> non-edges)
G_comp = nx.complement(nx.path_graph(5))
print(f"Complement of P5: {G_comp.number_of_edges()} edges")  # 6

# Graph products
cart = nx.cartesian_product(nx.path_graph(3), nx.path_graph(3))
tensor = nx.tensor_product(nx.path_graph(3), nx.path_graph(3))
strong = nx.strong_product(nx.path_graph(3), nx.path_graph(3))
print(f"Cartesian: {cart.number_of_nodes()} nodes, {cart.number_of_edges()} edges")
print(f"Tensor: {tensor.number_of_nodes()} nodes, {tensor.number_of_edges()} edges")
print(f"Strong: {strong.number_of_nodes()} nodes, {strong.number_of_edges()} edges")
```

---

## Efficiency Notes

- **Traversal**: DFS/BFS are O(V+E). Use generator forms (`nx.dfs_edges`) for memory efficiency.
- **Cliques**: `find_cliques` is exponential worst-case; use `approximation.max_clique` for large graphs.
- **Isomorphism**: VF2 algorithm, worst-case exponential but fast for most real-world graphs.
- **Spanning trees**: Kruskal O(E log E), Prim O(E log V). Select via `algorithm=` parameter.
- **Generators**: Always use `seed=` for reproducibility. Use `fast_gnp_random_graph` for large sparse ER graphs.
- **Graph products**: Result has |V1| x |V2| nodes; beware memory with large inputs.

---

Condensed from algorithms.md (383 lines) + generators.md (378 lines). Retained: traversal (DFS/BFS), cycles, topological sorting, cliques, graph coloring, isomorphism, matching/covering, tree algorithms (MST variants, tree properties), classic generators, social network datasets, lattice/grid, tree generators, bipartite, degree sequence, directed generators, graph operations. Omitted: A* heuristic customization, Bellman-Ford negative weights -- consult official docs. Relocated to SKILL.md inline: shortest paths (Module 4), centrality measures (Module 3), connectivity (Module 4), community detection (Module 5), flow/capacity (Module 4), clustering/transitivity (Module 3), core random generators ER/BA/WS/SBM (Module 8), random geometric/regular graphs (Module 8), graph type conversion (Key Concepts + Module 1). Combined coverage: ~290 retained / 761 original lines = ~38%.
