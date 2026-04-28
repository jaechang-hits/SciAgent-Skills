---
name: "etetoolkit"
description: "ETE Toolkit (ETE3): Python phylogenetic tree analysis and visualization. Parse Newick/NHX/PhyloXML, traverse/annotate nodes, render figures with TreeStyle/NodeStyle, integrate NCBI taxonomy, run PhyloTree comparative genomics. Use for species trees, gene family evolution, annotated tree figures."
license: "GPL-3.0"
---

# ETE Toolkit: Phylogenetic Tree Analysis and Visualization

## Overview

ETE Toolkit (ETE3) is a Python framework for phylogenetic tree exploration, manipulation, and publication-quality visualization. It supports reading and writing Newick, NHX, PhyloXML, and NeXML formats, rich node annotation, programmatic tree traversal, NCBI taxonomy integration, and a flexible rendering engine for customizable tree figures. ETE3 is widely used in comparative genomics, phylogenomics, and evolutionary biology workflows.

## When to Use

- Parse phylogenetic trees from Newick, NHX, PhyloXML, or NeXML files and programmatically traverse or modify topology
- Annotate tree nodes with metadata (bootstrap values, gene names, taxonomic ranks, expression data) for visualization or downstream analysis
- Render publication-quality tree figures with custom node shapes, colors, branch widths, and face decorations using TreeStyle and NodeStyle
- Map NCBI taxonomy IDs to lineage information, validate species names, or build taxonomy-aware trees
- Compute evolutionary statistics: branch lengths, tree distances (Robinson-Foulds), LCA queries, monophyly tests
- Build PhyloTree objects for comparative genomics — gene duplication/speciation event annotation, orthologs/paralogs inference
- Prune, reroot, or ultrametricize trees programmatically before passing to downstream tools (BEAST, IQ-TREE, etc.)
- For sequence alignment prior to tree building, use `biopython-molecular-biology` instead

## Prerequisites

- **Python packages**: `ete3`, `numpy`, `PyQt5` (for interactive rendering), `lxml` (for PhyloXML)
- **Data requirements**: Newick string or tree file; NCBI taxonomy database (downloaded on first use for NCBI module)
- **Environment**: Python 3.6+; PyQt5 required for `TreeStyle` rendering and interactive GUI; headless rendering requires `xvfb`

> **Check before installing**: The tool may already be available in the current environment (e.g., inside a `pixi` / `conda` env). Run `command -v python` first and skip the install commands below if it returns a path. When running inside a pixi project, invoke the tool via `pixi run python` rather than bare `python`.

```bash
pip install ete3 numpy lxml PyQt5
# For headless rendering on Linux servers:
# apt-get install xvfb python3-pyqt5
```

## Quick Start

```python
from ete3 import Tree

# Load a Newick tree and inspect basic properties
t = Tree("((A:0.1,B:0.2)AB:0.3,(C:0.4,D:0.1)CD:0.2)root;")
print(f"Number of leaves: {len(t.get_leaves())}")
print(f"Leaf names: {t.get_leaf_names()}")
print(f"Tree depth: {t.get_farthest_leaf()[1]:.3f}")
# Number of leaves: 4
# Leaf names: ['A', 'B', 'C', 'D']
# Tree depth: 0.700
t.show()  # Opens interactive viewer (requires PyQt5)
```

## Core API

### Module 1: Tree I/O (Tree parsing and serialization)

Load trees from strings or files; write in various formats.

```python
from ete3 import Tree, PhyloTree

# Parse Newick string (format 1 = standard Newick with support values)
t = Tree("((A:0.1,B:0.2)90:0.3,(C:0.4,D:0.1)85:0.2)root;", format=1)
print(f"Root children: {[n.name for n in t.children]}")

# Load from file
t_file = Tree("my_tree.nwk")

# Write Newick with internal names and supports
nwk_str = t.write(format=1)
print(f"Newick: {nwk_str}")

# Write to file
t.write(outfile="output_tree.nwk", format=0)
print("Saved output_tree.nwk")
```

```python
from ete3 import PhyloTree

# Load PhyloXML tree (retains sequence annotations)
# pt = PhyloTree("my_phylo.xml", parser="phyloxml")

# Load NHX format (extended Newick with key=value annotations)
nhx = Tree("((A[&&NHX:S=human:D=Y],B[&&NHX:S=mouse:D=N]))")
for leaf in nhx.get_leaves():
    print(f"{leaf.name}: species={leaf.S}, duplication={leaf.D}")
# A: species=human, duplication=Y
# B: species=mouse, duplication=N
```

### Module 2: Tree Traversal and Search

Navigate nodes using pre-order, post-order, or breadth-first traversal; search by name or attribute.

```python
from ete3 import Tree

t = Tree("((Homo_sapiens:0.1,Pan_troglodytes:0.05)Hominidae:0.2,(Mus_musculus:0.3,Rattus_norvegicus:0.25)Muridae:0.4)Euarchontoglires;")

# Iterate all nodes (preorder by default)
for node in t.traverse("preorder"):
    depth = node.get_distance(t)
    print(f"{'leaf' if node.is_leaf() else 'internal'}: {node.name or 'unnamed'} depth={depth:.3f}")

# Search by name
human = t.search_nodes(name="Homo_sapiens")[0]
print(f"Human branch length: {human.dist:.3f}")
print(f"Ancestors: {[a.name for a in human.get_ancestors()]}")
```

```python
from ete3 import Tree

t = Tree("((Homo_sapiens:0.1,Pan_troglodytes:0.05)Hominidae:0.2,(Mus_musculus:0.3,Rattus_norvegicus:0.25)Muridae:0.4)Euarchontoglires;")

# Lowest common ancestor (LCA) query
human = t & "Homo_sapiens"   # shorthand for search_nodes(name=...)[0]
mouse = t & "Mus_musculus"
lca = t.get_common_ancestor(human, mouse)
print(f"LCA of human and mouse: {lca.name}")
# LCA of human and mouse: Euarchontoglires

# Check monophyly
is_mono, mono_type, broken = t.check_monophyly(
    values=["Homo_sapiens", "Pan_troglodytes"], target_attr="name"
)
print(f"Hominids monophyletic: {is_mono}, type: {mono_type}")
# Hominids monophyletic: True, type: monophyletic
```

### Module 3: Node Annotation

Add custom attributes to nodes for metadata-driven visualization and analysis.

```python
from ete3 import Tree

t = Tree("((Homo_sapiens,Pan_troglodytes)Hominidae,(Mus_musculus,Rattus_norvegicus)Muridae)Euarchontoglires;")

# Annotate leaves with arbitrary metadata
metadata = {
    "Homo_sapiens":      {"genome_size_gb": 3.2, "ploidy": 2, "color": "blue"},
    "Pan_troglodytes":   {"genome_size_gb": 3.1, "ploidy": 2, "color": "green"},
    "Mus_musculus":      {"genome_size_gb": 2.7, "ploidy": 2, "color": "orange"},
    "Rattus_norvegicus": {"genome_size_gb": 2.9, "ploidy": 2, "color": "red"},
}
for leaf in t.get_leaves():
    for attr, val in metadata[leaf.name].items():
        setattr(leaf, attr, val)

# Access annotations
for leaf in t.get_leaves():
    print(f"{leaf.name}: {leaf.genome_size_gb} Gb, {leaf.color}")
```

```python
from ete3 import Tree
import pandas as pd

t = Tree("((A,B)AB,(C,D)CD)root;")

# Load annotations from a DataFrame and apply to tree
df = pd.DataFrame({
    "name":  ["A", "B", "C", "D"],
    "value": [1.2, 3.4, 0.8, 2.1],
    "group": ["x", "x", "y", "y"],
})
name_to_row = df.set_index("name").to_dict(orient="index")

for leaf in t.get_leaves():
    if leaf.name in name_to_row:
        leaf.add_features(**name_to_row[leaf.name])
        print(f"{leaf.name}: value={leaf.value}, group={leaf.group}")
```

### Module 4: Tree Manipulation

Prune, reroot, ultrametricize, and compute distances.

```python
from ete3 import Tree

t = Tree("((A:0.1,B:0.2)AB:0.3,(C:0.4,D:0.1,(E:0.2,F:0.3)EF:0.1)CD:0.2)root;")
print(f"Original leaves: {t.get_leaf_names()}")

# Prune to a subset of taxa
t.prune(["A", "C", "E"], preserve_branch_length=True)
print(f"Pruned leaves: {t.get_leaf_names()}")

# Reroot on midpoint
t2 = Tree("((A:0.5,B:0.1):0.2,(C:0.3,D:0.4):0.1);")
midpoint_node, midpoint_dist = t2.get_midpoint_outgroup()
t2.set_outgroup(midpoint_node)
print(f"Rerooted at midpoint; root children: {[n.name for n in t2.children]}")

# Robinson-Foulds distance between two topologies
t_ref = Tree("((A,B),(C,D));")
t_alt = Tree("((A,C),(B,D));")
rf, rf_max, common_attrs, discard_t1, discard_t2, parts1, parts2 = t_ref.robinson_foulds(t_alt)
print(f"RF distance: {rf}, normalized: {rf/rf_max:.3f}")
```

### Module 5: Tree Visualization (TreeStyle / NodeStyle)

Render publication-quality tree figures with custom styles.

```python
from ete3 import Tree, TreeStyle, NodeStyle, faces, AttrFace, CircleFace

t = Tree("((Homo_sapiens,Pan_troglodytes)Hominidae,(Mus_musculus,Rattus_norvegicus)Muridae)Euarchontoglires;")

# Define node styles
for node in t.traverse():
    nstyle = NodeStyle()
    if node.is_leaf():
        nstyle["shape"] = "circle"
        nstyle["size"] = 8
        nstyle["fgcolor"] = "darkblue"
    else:
        nstyle["shape"] = "sphere"
        nstyle["size"] = 6
        nstyle["fgcolor"] = "gray"
    node.set_style(nstyle)

# Add text face to leaves
for leaf in t.get_leaves():
    name_face = AttrFace("name", fsize=12, fgcolor="black")
    leaf.add_face(name_face, column=0, position="branch-right")

# Configure TreeStyle
ts = TreeStyle()
ts.mode = "r"          # rectangular (use "c" for circular)
ts.show_leaf_name = False
ts.branch_vertical_margin = 15
ts.title.add_face(faces.TextFace("Phylogenetic Tree", fsize=16), column=0)

# Render to file (no display needed)
t.render("tree_figure.png", tree_style=ts, w=800, units="px")
print("Saved tree_figure.png")
```

```python
from ete3 import Tree, TreeStyle, NodeStyle, faces, RectFace

t = Tree("((A,B)AB,(C,D)CD)root;")

# Circular cladogram with colored rectangles
metadata = {"A": "red", "B": "red", "C": "blue", "D": "blue"}
for leaf in t.get_leaves():
    leaf.color = metadata[leaf.name]
    leaf.add_face(RectFace(width=20, height=20, fgcolor=leaf.color, bgcolor=leaf.color),
                  column=0, position="aligned")

ts = TreeStyle()
ts.mode = "c"          # circular layout
ts.arc_start = -180
ts.arc_span = 359
ts.show_leaf_name = True

t.render("circular_tree.png", tree_style=ts, w=600, units="px")
print("Saved circular_tree.png")
```

### Module 6: NCBI Taxonomy Integration

Map species to NCBI taxonomy, retrieve lineages, and build taxonomy trees.

```python
from ete3 import NCBITaxa

# Initialize (downloads ~50 MB taxonomy DB on first call)
ncbi = NCBITaxa()
# ncbi.update_taxonomy_database()  # Refresh to latest NCBI taxonomy

# Name → taxid
taxid_map = ncbi.get_name_translator(["Homo sapiens", "Mus musculus", "Danio rerio"])
print(f"Taxid map: {taxid_map}")
# Taxid map: {'Homo sapiens': [9606], 'Mus musculus': [10090], 'Danio rerio': [7955]}

# Taxid → lineage
lineage = ncbi.get_lineage(9606)
names = ncbi.get_taxid_translator(lineage)
ranks = ncbi.get_rank(lineage)
for taxid in lineage[-6:]:
    print(f"  {ranks[taxid]:15s}: {names[taxid]}")
```

```python
from ete3 import NCBITaxa, Tree, TreeStyle

ncbi = NCBITaxa()

# Build a taxonomy tree for a set of taxids
taxids = [9606, 10090, 7955, 6239, 7227]   # human, mouse, zebrafish, C. elegans, fruit fly
tree = ncbi.get_topology(taxids, intermediate_nodes=True)

# Annotate with common names
translator = ncbi.get_taxid_translator([int(n.name) for n in tree.get_leaves()])
for leaf in tree.get_leaves():
    leaf.sci_name = translator.get(int(leaf.name), leaf.name)
    print(f"Taxid {leaf.name}: {leaf.sci_name}")

# Render taxonomy tree
ts = TreeStyle()
ts.show_leaf_name = True
tree.render("taxonomy_tree.png", tree_style=ts, w=600, units="px")
print("Saved taxonomy_tree.png")
```

### Module 7: PhyloTree for Comparative Genomics

Annotate gene trees with duplication/speciation events and query ortholog relationships.

```python
from ete3 import PhyloTree

# Build a gene tree with species mapping
# Format: leaf names must follow "gene_SPECIES" or use sp_naming_function
nwk = "((Hsap_BRCA1:0.1,Ptro_BRCA1:0.05)0.99:0.2,(Mmus_Brca1:0.3,Rnor_Brca1:0.25)0.95:0.1);"
t = PhyloTree(nwk, sp_naming_function=lambda name: name.split("_")[0])

# Annotate events (duplication vs speciation)
t.get_descendant_evol_events()

# Report events per node
for node in t.traverse():
    if not node.is_leaf() and hasattr(node, "evoltype"):
        print(f"Node evoltype: {node.evoltype} "
              f"(D=duplication, S=speciation)")

# Get orthologs for a given leaf
leaf = t & "Hsap_BRCA1"
orthologs = leaf.get_sisters()
print(f"Orthologs of Hsap_BRCA1: {[n.name for n in t.get_leaves() if n != leaf]}")
```

## Key Concepts

### Newick Format Variants

ETE3's `format` parameter controls which Newick flavor to parse:

| Format | Internal node labels | Branch lengths | Typical use |
|--------|---------------------|----------------|-------------|
| 0 | Flexible | Yes | IQ-TREE, RAxML output |
| 1 | Named + support | Yes | Standard annotated trees |
| 5 | Internal names only | No | Topology-only trees |
| 9 | Leaf names only | Yes | Simple labeled trees |
| 100 | No names | No | Pure topology |

```python
from ete3 import Tree
# RAxML output (bootstrap values as internal labels)
t = Tree("((A:0.1,B:0.2)90:0.3,(C:0.4,D:0.1)85:0.2);", format=1)
for node in t.traverse():
    if not node.is_leaf():
        print(f"Support: {node.support}, dist: {node.dist}")
```

## Common Workflows

### Workflow 1: Annotated Tree Figure from Alignment Output

**Goal**: Load an IQ-TREE result, annotate leaves with metadata, and render a publication figure.

```python
from ete3 import Tree, TreeStyle, NodeStyle, AttrFace, faces
import pandas as pd

# Load IQ-TREE Newick output (format=1 handles support values)
t = Tree("iqtree_output.treefile", format=1)

# Midpoint rooting
outgroup, _ = t.get_midpoint_outgroup()
t.set_outgroup(outgroup)

# Load metadata table
meta = pd.read_csv("sample_metadata.csv")   # columns: name, clade, color
meta_dict = meta.set_index("name").to_dict(orient="index")

# Annotate leaves
for leaf in t.get_leaves():
    info = meta_dict.get(leaf.name, {})
    leaf.clade = info.get("clade", "unknown")
    leaf.face_color = info.get("color", "gray")

# Apply per-node styles
for node in t.traverse():
    ns = NodeStyle()
    if node.is_leaf():
        ns["size"] = 8
        ns["fgcolor"] = node.face_color if hasattr(node, "face_color") else "black"
    else:
        ns["size"] = 0   # hide internal nodes
    node.set_style(ns)

# Add name labels
for leaf in t.get_leaves():
    leaf.add_face(AttrFace("name", fsize=10), column=0, position="branch-right")
    leaf.add_face(AttrFace("clade", fsize=9, fgcolor="gray"), column=1, position="branch-right")

ts = TreeStyle()
ts.show_leaf_name = False
ts.branch_vertical_margin = 12
ts.scale = 200   # pixels per branch length unit

t.render("annotated_tree.pdf", tree_style=ts)
print("Saved annotated_tree.pdf")
```

### Workflow 2: Taxonomy-Aware Species Tree Construction

**Goal**: Build a topology-correct species tree from a list of NCBI taxids and export as Newick.

```python
from ete3 import NCBITaxa, TreeStyle

ncbi = NCBITaxa()

# Input: list of NCBI taxids
taxids = [9606, 10090, 7955, 6239, 7227, 3702]  # human, mouse, zebrafish, worm, fly, Arabidopsis

# Build topology tree
species_tree = ncbi.get_topology(taxids, intermediate_nodes=False)

# Translate taxid leaf names to scientific names
translator = ncbi.get_taxid_translator([int(n.name) for n in species_tree.get_leaves()])
for leaf in species_tree.get_leaves():
    leaf.name = translator.get(int(leaf.name), leaf.name)

# Export Newick
nwk = species_tree.write(format=9)
print(f"Species tree Newick:\n{nwk}")
with open("species_tree.nwk", "w") as f:
    f.write(nwk)

# Render figure
ts = TreeStyle()
ts.show_leaf_name = True
ts.mode = "r"
species_tree.render("species_tree.png", tree_style=ts, w=800, units="px")
print("Saved species_tree.nwk and species_tree.png")
```

### Workflow 3: Batch Robinson-Foulds Comparison

**Goal**: Compare a set of bootstrap replicate trees against a reference topology.

```python
from ete3 import Tree
import pandas as pd

# Reference tree
ref_tree = Tree("reference.nwk", format=1)
ref_leaves = set(ref_tree.get_leaf_names())

results = []
for i, line in enumerate(open("bootstrap_trees.nwk")):
    bt = Tree(line.strip(), format=1)
    # Prune to common taxa
    common = ref_leaves & set(bt.get_leaf_names())
    ref_pruned = ref_tree.copy()
    bt_pruned = bt.copy()
    ref_pruned.prune(list(common))
    bt_pruned.prune(list(common))

    rf, rf_max, *_ = ref_pruned.robinson_foulds(bt_pruned, unrooted_trees=True)
    norm_rf = rf / rf_max if rf_max > 0 else 0
    results.append({"replicate": i + 1, "rf": rf, "rf_max": rf_max, "norm_rf": norm_rf})

df = pd.DataFrame(results)
print(df.describe())
df.to_csv("rf_distances.csv", index=False)
print(f"Mean normalized RF: {df['norm_rf'].mean():.4f}")
```

## Key Parameters

| Parameter | Module | Default | Range / Options | Effect |
|-----------|--------|---------|-----------------|--------|
| `format` | Tree I/O | `0` | `0`–`9`, `100` | Newick flavor; controls parsing of support values vs internal names |
| `quoted_node_names` | Tree I/O | `False` | `True`, `False` | Allow spaces and special chars in node names |
| `preserve_branch_length` | Pruning | `False` | `True`, `False` | Maintain patristic distances when pruning subtrees |
| `unrooted_trees` | Robinson-Foulds | `False` | `True`, `False` | Compare unrooted topologies (required for most gene trees) |
| `ts.mode` | TreeStyle | `"r"` | `"r"`, `"c"` | Rectangular or circular layout |
| `ts.scale` | TreeStyle | `None` | positive int | Pixels per branch length unit; controls horizontal spread |
| `ts.branch_vertical_margin` | TreeStyle | `5` | int (px) | Vertical spacing between leaf branches |
| `intermediate_nodes` | NCBITaxa | `False` | `True`, `False` | Include ancestral NCBI taxids in topology tree |

## Common Recipes

### Recipe: Extract All Subtrees Matching a Clade Name

When to use: Identify all subtrees rooted at nodes whose name matches a pattern.

```python
from ete3 import Tree

t = Tree("((Homo_sapiens,Pan_troglodytes)Hominidae,(Mus_musculus,Rattus_norvegicus)Muridae)Euarchontoglires;")

target_clade = "Hominidae"
nodes = t.search_nodes(name=target_clade)
for node in nodes:
    print(f"Clade {node.name}: {node.get_leaf_names()}")
    subtree_nwk = node.write(format=1)
    print(f"  Newick: {subtree_nwk}")
```

### Recipe: Ultrametricize a Non-Ultrametric Tree

When to use: Prepare a tree for time-calibrated analyses requiring ultrametric input.

```python
from ete3 import Tree

t = Tree("((A:0.3,B:0.1):0.4,(C:0.7,D:0.2):0.1);")
print(f"Before: max leaf distance = {max(t.get_distance(l) for l in t.get_leaves()):.4f}")

# Convert to ultrametric using ETE's method
t.convert_to_ultrametric()
dists = [t.get_distance(l) for l in t.get_leaves()]
print(f"After: all leaf distances = {set(round(d, 6) for d in dists)}")
```

### Recipe: Color Leaves by Group and Export SVG

When to use: Quickly produce a colored tree for presentations without manual styling.

```python
from ete3 import Tree, TreeStyle, NodeStyle

t = Tree("((A,B,C)GroupX,(D,E)GroupY,(F,G,H)GroupZ);")
group_colors = {"GroupX": "steelblue", "GroupY": "tomato", "GroupZ": "seagreen"}

for node in t.traverse():
    ns = NodeStyle()
    if node.is_leaf():
        parent_name = node.up.name if node.up else ""
        ns["fgcolor"] = group_colors.get(parent_name, "black")
        ns["size"] = 10
    node.set_style(ns)

ts = TreeStyle()
ts.show_leaf_name = True
ts.branch_vertical_margin = 14
t.render("colored_tree.svg", tree_style=ts, w=600, units="px")
print("Saved colored_tree.svg")
```

## Expected Outputs

- **Tree objects**: `Tree` / `PhyloTree` instances — navigable node hierarchies with `.children`, `.up`, `.name`, `.dist`, `.support`
- **Newick strings**: produced by `t.write(format=N)` — standard text for downstream tools
- **Image files**: `.png`, `.pdf`, `.svg` via `t.render()` — resolution controlled by `w` parameter and `dpi`
- **Taxonomy trees**: `NCBITaxa.get_topology()` returns a `Tree` with taxid node names
- **RF distances**: integer raw RF + integer max RF from `robinson_foulds()`; normalize as `rf / rf_max`

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `NewickError: Unexepected char` | Newick format mismatch (support vs name field) | Try `format=0`, `1`, or `5`; check if internal nodes have support values or names |
| `RuntimeError: cannot connect to display` | PyQt5 requires a display for rendering | Use `t.render("out.png", ...)` instead of `t.show()`; on headless servers, run under `xvfb-run` |
| `AttributeError: 'Tree' object has no attribute` | Node feature not annotated | Check `dir(node)` or use `hasattr(node, "attr")` before access |
| NCBI taxonomy DB not found | First-time use; DB not downloaded | Call `NCBITaxa().update_taxonomy_database()` once |
| Tree figure all leaves collapsed | Branch lengths all zero with `scale` set too low | Set `ts.scale = None` to auto-scale, or increase `ts.scale` value |
| `ValueError` on `robinson_foulds` | Trees have no common leaves | Prune both trees to shared taxon set before comparison |
| Slow rendering for large trees (500+ leaves) | Per-node Python rendering loop | Use `ts.show_leaf_name = False` and minimal faces; consider exporting Newick and rendering with FigTree |

## References

- [ETE3 documentation](http://etetoolkit.org/docs/latest/tutorial/) — official tutorial covering all modules
- [ETE3 API reference](http://etetoolkit.org/docs/latest/reference/) — complete class and method reference
- [ETE3 GitHub repository](https://github.com/etetoolkit/ete) — source, issue tracker, and example notebooks
- [Huerta-Cepas J, Serra F, Bork P (2016) ETE 3: Reconstruction, Analysis, and Visualization of Phylogenomic Data. *Mol Biol Evol* 33:1635-1638](https://doi.org/10.1093/molbev/msw046) — primary citation for ETE3
