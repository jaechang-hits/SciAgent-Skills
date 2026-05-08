---
name: "omnipath-knowledge-graph"
description: "Query the OmniPath integrated biological knowledge graph from Python. The `omnipath` client wraps the saezlab OmniPath web service which integrates 150+ resources covering signaling interactions, transcriptional regulation (DoRothEA, CollecTRI), miRNA-target, post-translational modifications (enzyme-substrate), protein complexes, intercellular communication (ligand-receptor), and entity annotations. All requests return tidy pandas DataFrames. Use `pypath-network-builder` instead when you need to rebuild OmniPath from primary resources or add custom databases; use `string-database-ppi` for STRING-only protein interactions; use `reactome-database` for Reactome pathways."
license: "MIT"
---

# OmniPath Knowledge Graph Client

## Overview

`omnipath` is a Python client for the OmniPath web service — an integrated knowledge graph maintained by the Saez Lab that combines 150+ literature-curated resources into a unified API. A single import gives access to signed, directed, evidence-tracked interactions (signaling, transcriptional, post-translational, miRNA, lncRNA), enzyme-substrate relationships, protein complex compositions, intercellular communication categories (ligand, receptor, ECM, transporter), and ~5 million functional annotations spanning subcellular localization, function, disease, and pathway membership. Every request returns a pandas DataFrame and respects per-resource license restrictions (academic vs. commercial).

## When to Use

- Pulling a literature-curated signaling network around a target protein or pathway and writing it to NetworkX or a graph database
- Retrieving ligand-receptor pairs to seed cell-cell communication analyses (CellChat, CellPhoneDB, LIANA inputs)
- Querying enzyme-substrate (kinase-substrate / phosphatase-substrate) pairs for PTM analysis
- Mapping a list of genes to subcellular localization, function, pathway, or disease annotations from OmniPath's `Annotations` database
- Filtering networks by license (`academic` vs. `commercial`) before redistribution
- Looking up TF-target or miRNA-target relationships for regulatory network construction
- Use `pypath-network-builder` instead when you need to rebuild OmniPath from raw input modules or add custom resources
- Use `string-database-ppi` instead for STRING-specific PPI queries with confidence scores; use `reactome-database` for Reactome pathway hierarchy

## Prerequisites

- **Python packages**: `omnipath`, `pandas`, `networkx`, `requests`
- **Network access**: HTTPS access to `https://omnipathdb.org/`
- **Cache**: omnipath caches responses by default to `~/.cache/omnipathdb/`; clear with `op.clear_cache()`
- **Rate limits**: no hard rate limit but be polite (≤ a few requests/sec); large queries return tens of MB so prefer filtered requests over `AllInteractions().get()` without filters

```bash
pip install omnipath pandas networkx
```

## Quick Start

```python
import omnipath as op

# Pull the curated signaling network for human (largest filtered subset)
net = op.interactions.OmniPath.get(
    organism="human",
    genesymbols=True,
    fields=["sources", "references", "curation_effort"],
)
print(f"Edges: {len(net):,}   Unique proteins: {net['source_genesymbol'].nunique() + net['target_genesymbol'].nunique():,}")
print(net[["source_genesymbol", "target_genesymbol", "is_directed", "is_stimulation", "curation_effort"]].head())
```

## Core API

### Module 1: Interactions — Signaling, TF-target, miRNA, PTM

The `omnipath.interactions` module exposes one class per interaction dataset. All classes share `.get()`, `.params()`, and `.resources()` helpers.

```python
import omnipath as op

# Curated signed/directed signaling (the canonical "OmniPath" subset)
signaling = op.interactions.OmniPath.get(
    organism="human",
    genesymbols=True,
    directed=True,
    signed=True,
)
print(f"Signaling edges: {len(signaling)}")
print(signaling.columns.tolist())

# All datasets in one query (signaling + TF + miRNA + lncRNA + ...)
all_int = op.interactions.AllInteractions.get(
    organism="human",
    genesymbols=True,
    datasets=["omnipath", "pathwayextra", "kinaseextra", "ligrecextra"],
)
print(f"All-interactions union: {len(all_int):,}")
```

```python
# Transcriptional regulation: DoRothEA + CollecTRI via Transcriptional class
tf = op.interactions.Transcriptional.get(
    organism="human",
    genesymbols=True,
    dorothea_levels=["A", "B", "C"],   # confidence A is highest
)
print(f"TF -> target edges: {len(tf):,}")
print(tf[["source_genesymbol", "target_genesymbol", "dorothea_level"]].head())

# miRNA-target interactions
mi = op.interactions.miRNA.get(organism="human", genesymbols=True)
print(f"miRNA -> mRNA edges: {len(mi):,}")
```

### Module 2: Enzyme-Substrate (PTMs)

Kinase-substrate, phosphatase-substrate, and other enzyme-PTM relationships at residue resolution.

```python
import omnipath as op

ptm = op.requests.Enzsub.get(
    organism="human",
    genesymbols=True,
)
print(f"PTM relationships: {len(ptm):,}")
print(ptm[["enzyme_genesymbol", "substrate_genesymbol",
           "residue_type", "residue_offset", "modification"]].head())

# Filter to kinase phosphorylation events on a target substrate
egfr_ptm = ptm[(ptm["substrate_genesymbol"] == "EGFR") &
               (ptm["modification"] == "phosphorylation")]
print(f"EGFR phosphosites: {len(egfr_ptm)}")
print(egfr_ptm[["enzyme_genesymbol", "residue_type", "residue_offset"]].to_string(index=False))
```

### Module 3: Protein Complexes

Curated protein complex compositions (pre-merged across CORUM, Compleat, ComplexPortal, hu.MAP, Signor, PDB, etc.).

```python
import omnipath as op

complexes = op.requests.Complexes.get()
print(f"Complexes: {len(complexes):,}")
print(complexes.columns.tolist())
# ['name', 'stoichiometry', 'components_genesymbols', 'sources', 'references', ...]

# Find every complex containing a given subunit
target = "TP53"
target_complexes = complexes[complexes["components_genesymbols"].fillna("").str.contains(target)]
print(f"Complexes containing {target}: {len(target_complexes)}")
print(target_complexes[["name", "components_genesymbols", "sources"]].head().to_string(index=False))
```

### Module 4: Annotations — Function, Localization, Pathway, Disease

The Annotations database integrates ~50 resources into a long-format table of `record_id, uniprot, source, label, value`.

```python
import omnipath as op

# Pull annotations from a single resource (filtered queries are much faster)
sig_paths = op.requests.Annotations.get(
    resources=["SignaLink_pathway"],
    genesymbols=True,
)
print(f"SignaLink pathway annotations: {len(sig_paths):,}")
print(sig_paths.head())

# Pivot into a wide gene x label matrix
wide = (
    sig_paths.assign(present=1)
    .pivot_table(index="genesymbol", columns="label", values="present",
                 aggfunc="max", fill_value=0)
)
print(f"Wide annotation matrix shape: {wide.shape}")
```

```python
# Annotations for a specific gene set (UniProt accessions or gene symbols)
genes = ["EGFR", "ERBB2", "KRAS", "BRAF", "MAP2K1"]
annot = op.requests.Annotations.get(
    proteins=genes,
    resources=["HPA_subcellular", "Compartments", "DisGeNet"],
    genesymbols=True,
)
print(f"Records returned: {len(annot)}")
print(annot[["genesymbol", "source", "label", "value"]].head(10).to_string(index=False))
```

### Module 5: Intercell — Ligand-Receptor and Cell-Cell Communication

The Intercell database categorizes proteins into intercellular roles (`ligand`, `receptor`, `adhesion`, `ecm`, `transporter`, ...). Combine with interactions to build a ligand-receptor network.

```python
import omnipath as op

# Per-protein intercell category labels
icell = op.requests.Intercell.get(
    aspect="functional",
    scope="generic",
    categories=["ligand", "receptor"],
)
print(f"Intercell records: {len(icell):,}")
print(icell.head()[["uniprot", "genesymbol", "category", "parent", "source"]])

# Pre-built ligand-receptor network (intercell categories joined to OmniPath edges)
lr = op.interactions.import_intercell_network(
    transmitter_params={"categories": ["ligand"]},
    receiver_params={"categories": ["receptor"]},
)
print(f"Ligand -> receptor edges: {len(lr):,}")
print(lr[["source_genesymbol", "target_genesymbol",
          "category_intercell_source", "category_intercell_target"]].head())
```

### Module 6: Resource Catalog and Global Options

Discover datasets, organisms, and licenses; control caching and HTTP timeouts.

```python
import omnipath as op

# Enumerate available interaction datasets
print("Datasets:", [d.value for d in op.constants.InteractionDataset])
# ['omnipath', 'pathwayextra', 'kinaseextra', 'ligrecextra', 'dorothea',
#  'tf_target', 'collectri', 'mirnatarget', 'tf_mirna', 'lncrna_mrna', 'small_molecule']

# Supported organisms
print("Organisms:", [o.value for o in op.constants.Organism])

# License filter (academic == include all; commercial == only commercial-friendly resources)
commercial_only = op.interactions.OmniPath.get(license="commercial", organism="human")
academic = op.interactions.OmniPath.get(license="academic", organism="human")
print(f"academic: {len(academic):>5}  commercial: {len(commercial_only):>5}")
```

```python
# Configure global options
op.options.timeout = 60                    # seconds
op.options.num_retries = 3
op.options.cache  # current cache backend (FileCache by default)

# Resources contributing to a particular dataset
print("Resources behind OmniPath core:", op.interactions.OmniPath.resources()[:10])

# Wipe the local response cache (useful after server-side updates)
op.clear_cache()
```

## Key Concepts

### Field Reference

| Column | Meaning |
|--------|---------|
| `source` / `target` | UniProt IDs of the interacting proteins |
| `source_genesymbol` / `target_genesymbol` | Gene symbol shortcuts (require `genesymbols=True`) |
| `is_directed` | Whether direction is known (1) or undirected (0) |
| `is_stimulation` / `is_inhibition` | Sign of the directed edge |
| `consensus_direction` / `consensus_stimulation` / `consensus_inhibition` | Majority vote across resources |
| `dorothea_level` | A–E, where A is highest curation confidence |
| `references` | `pmid:12345;pmid:67890` semicolon-joined evidence list |
| `sources` | Resources reporting the edge (semicolon-joined) |
| `curation_effort` | Number of literature references supporting the edge |
| `n_references` / `n_resources` | Counts of supporting evidence |

### Dataset Cheat Sheet

| Dataset | Class | Coverage |
|---------|-------|----------|
| `omnipath` | `OmniPath` | Signed, directed signaling (the curated core) |
| `pathwayextra` | `PathwayExtra` | Additional activity-flow signaling (less stringent) |
| `kinaseextra` | `KinaseExtra` | Extra kinase-substrate edges from PTM resources |
| `ligrecextra` | `LigRecExtra` | Additional ligand-receptor edges |
| `dorothea` | `Dorothea` | Literature-curated TF-target with A–E confidence |
| `tf_target` | `TFtarget` | Pooled TF-target (DoRothEA + CollecTRI + others) |
| `mirnatarget` | `miRNA` | miRNA-mRNA targeting |
| `lncrna_mrna` | `lncRNAmRNA` | lncRNA-mRNA regulation |

## Common Workflows

### Workflow 1: Build a Signaling Subnetwork around a Gene Set

```python
import omnipath as op
import networkx as nx
import pandas as pd

genes = {"EGFR", "ERBB2", "KRAS", "BRAF", "MAP2K1", "MAPK1", "MYC"}

# Pull all curated signaling, then filter to edges with both endpoints in the seed set
edges = op.interactions.OmniPath.get(
    organism="human",
    genesymbols=True,
    directed=True,
)
sub = edges[edges["source_genesymbol"].isin(genes) &
            edges["target_genesymbol"].isin(genes)]
print(f"Subnetwork edges: {len(sub)}")

# Build a directed multigraph; tag edges with sign and curation effort
G = nx.DiGraph()
for _, r in sub.iterrows():
    G.add_edge(
        r["source_genesymbol"], r["target_genesymbol"],
        sign=("+" if r["is_stimulation"] else
              "-" if r["is_inhibition"] else "?"),
        n_refs=r.get("n_references", 0),
        sources=r["sources"],
    )
print(f"Graph: {G.number_of_nodes()} nodes / {G.number_of_edges()} edges")
print("Top hubs by out-degree:",
      sorted(G.out_degree, key=lambda x: -x[1])[:5])
```

### Workflow 2: Ligand-Receptor Pairs for Cell-Cell Communication

```python
import omnipath as op

# Materialize the integrated ligand -> receptor edges with downstream signaling enabled
lr = op.interactions.import_intercell_network(
    transmitter_params={"categories": ["ligand"], "scope": "generic"},
    receiver_params={"categories": ["receptor"], "scope": "generic"},
)

# Keep edges with at least one literature reference
lr_high = lr[lr["n_references"].fillna(0) >= 1].copy()
print(f"High-confidence LR pairs: {len(lr_high):,}")

# Build a tidy LR table for downstream tools (CellPhoneDB / LIANA / CellChat input)
lr_table = (
    lr_high[["source_genesymbol", "target_genesymbol",
             "is_stimulation", "is_inhibition", "n_references", "sources"]]
    .rename(columns={"source_genesymbol": "ligand",
                     "target_genesymbol": "receptor"})
    .drop_duplicates(["ligand", "receptor"])
)
lr_table.to_csv("omnipath_lr_pairs.tsv", sep="\t", index=False)
print("Saved omnipath_lr_pairs.tsv")
```

### Workflow 3: Kinase-Substrate Phosphosite Map for a Pathway

```python
import omnipath as op
import pandas as pd

# Genes in the MAPK cascade
mapk = {"EGFR", "GRB2", "SOS1", "HRAS", "KRAS", "RAF1", "BRAF",
        "MAP2K1", "MAP2K2", "MAPK1", "MAPK3"}

ptm = op.requests.Enzsub.get(organism="human", genesymbols=True)
mapk_ptm = ptm[ptm["substrate_genesymbol"].isin(mapk)
               & (ptm["modification"] == "phosphorylation")]
print(f"Phosphosites on MAPK proteins: {len(mapk_ptm)}")

# Per-substrate phosphosite count and the kinases targeting it
summary = (
    mapk_ptm.groupby("substrate_genesymbol")
            .agg(n_sites=("residue_offset", "nunique"),
                 kinases=("enzyme_genesymbol", lambda s: ",".join(sorted(set(s)))))
            .sort_values("n_sites", ascending=False)
)
print(summary.to_string())
```

### Workflow 4: Annotate a Differentially-Expressed Gene List

```python
import omnipath as op
import pandas as pd

degs = pd.read_csv("deseq2_results.csv")
sig = degs.query("padj < 0.05 and abs(log2FoldChange) > 1")["gene"].tolist()

annot = op.requests.Annotations.get(
    proteins=sig,
    resources=["SignaLink_pathway", "HPA_subcellular", "DisGeNet", "MSigDB"],
    genesymbols=True,
)
print(f"Annotations retrieved: {len(annot):,}")

# Most enriched pathway labels among up-regulated DEGs
pathway_hits = (
    annot[annot["source"] == "SignaLink_pathway"]
    .groupby("label").size()
    .sort_values(ascending=False)
    .head(10)
)
print("Top SignaLink pathways:")
print(pathway_hits.to_string())
```

## Key Parameters

| Parameter | Module | Default | Range / Options | Effect |
|-----------|--------|---------|-----------------|--------|
| `organism` | all | `"human"` | `"human"`, `"mouse"`, `"rat"` | Species-specific results (mapped via orthology where supported) |
| `genesymbols` | interactions, enzsub, intercell | `False` | `True` / `False` | Adds `*_genesymbol` columns alongside UniProt IDs |
| `license` | all | `"academic"` | `"academic"`, `"commercial"`, `"for_profit"` | Drops resources whose license forbids the chosen redistribution mode |
| `datasets` | `AllInteractions` | all | subset of `InteractionDataset` enum | Restricts the union to the chosen interaction layers |
| `dorothea_levels` | `Dorothea`, `Transcriptional` | `["A","B","C","D"]` | any subset of `A`–`E` | Confidence cutoff for TF-target interactions (A is highest) |
| `directed` | interactions | `False` | `True` / `False` | Keep only directed edges |
| `signed` | interactions | `False` | `True` / `False` | Keep only edges with known stimulation/inhibition |
| `fields` | interactions | minimal | list of column names | Request additional output columns (e.g., `references`, `curation_effort`) |
| `resources` | annotations, intercell | all | list of resource names | Restricts to the named source databases |
| `proteins` | annotations | none | list of UniProt or gene symbols | Limits the query to a gene set (much faster than full pulls) |
| `categories` | intercell | none | list of category labels | E.g., `["ligand"]`, `["receptor"]`, `["ecm"]` |
| `scope` | intercell | `"generic"` | `"generic"`, `"specific"` | Granularity of the intercell category hierarchy |

## Common Recipes

### Recipe: Save a Network as GraphML for Cytoscape

When to use: hand off an OmniPath subnetwork to Cytoscape, Gephi, or yEd for visualization.

```python
import omnipath as op
import networkx as nx

edges = op.interactions.OmniPath.get(organism="human", genesymbols=True, directed=True)
G = nx.from_pandas_edgelist(
    edges, source="source_genesymbol", target="target_genesymbol",
    edge_attr=["is_stimulation", "is_inhibition", "n_references", "sources"],
    create_using=nx.DiGraph,
)
nx.write_graphml(G, "omnipath_signaling.graphml")
print(f"Wrote omnipath_signaling.graphml ({G.number_of_nodes()} nodes, {G.number_of_edges()} edges)")
```

### Recipe: Materialize a Reusable Local Snapshot

When to use: make repeated downstream analyses fast and reproducible by pinning to a specific OmniPath snapshot.

```python
import omnipath as op
import pandas as pd
from pathlib import Path

snap = Path("omnipath_snapshot/")
snap.mkdir(exist_ok=True)

op.interactions.OmniPath.get(organism="human", genesymbols=True).to_parquet(snap / "signaling.parquet")
op.requests.Enzsub.get(organism="human", genesymbols=True).to_parquet(snap / "enzsub.parquet")
op.requests.Complexes.get().to_parquet(snap / "complexes.parquet")
op.requests.Intercell.get(scope="generic").to_parquet(snap / "intercell.parquet")
print("Snapshot files:", [p.name for p in snap.glob("*.parquet")])
```

### Recipe: Filter to Highly-Curated Edges Only

When to use: reduce noise from low-evidence edges before downstream perturbation modeling.

```python
import omnipath as op

edges = op.interactions.OmniPath.get(
    organism="human",
    genesymbols=True,
    fields=["curation_effort", "references", "sources"],
)
# Keep edges with ≥3 supporting publications and ≥2 independent resources
strong = edges[(edges["curation_effort"] >= 3) &
               (edges["sources"].str.count(";") >= 1)]
print(f"Strong edges: {len(strong):,} of {len(edges):,}")
```

### Recipe: Cache Inspection and Manual Cleanup

When to use: free disk or force a refresh after a server-side database update.

```python
import omnipath as op
from pathlib import Path

cache_dir = Path(op.options.cache.path)
print(f"Cache: {cache_dir}")
total = sum(p.stat().st_size for p in cache_dir.rglob("*") if p.is_file())
print(f"Cache size: {total / 1e6:.1f} MB across {sum(1 for _ in cache_dir.rglob('*'))} entries")

# Wipe and re-pull (next request will hit the server)
op.clear_cache()
print("Cache cleared.")
```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `requests.exceptions.ReadTimeout` on first call | Default timeout too short for very large downloads | Increase `op.options.timeout = 120` and retry |
| Empty DataFrame from `Annotations.get()` | Forgot `proteins=...` or `resources=...`; full DB query is too large | Always filter by `proteins` or `resources`; the unfiltered pull is ~5 M rows |
| `KeyError: 'genesymbol'` | Forgot `genesymbols=True` | Re-run with `genesymbols=True`; default returns UniProt IDs only |
| Different result counts between sessions | OmniPath releases roll forward; cached responses are stale | Run `op.clear_cache()` and re-issue the query |
| `commercial` license drops most edges | Many sources are academic-only (KEGG, SignaLink, ...) | Confirm license requirement; otherwise stay on `academic` |
| Network too dense to plot | Default OmniPath core is ~80 k edges | Filter by `curation_effort`, `n_references`, or restrict to a gene set |
| `import_intercell_network` returns ~M edges | Generic-scope ligand x receptor cross-product is large | Restrict transmitter and receiver `categories` and `scope` |
| Mouse organism returns very few rows | Resource-by-resource species coverage varies | Combine `organism="mouse"` with `dorothea_levels=["A","B","C"]` and check `pypath-network-builder` for orthology pre-builds |

## Related Skills

- [`pypath-network-builder`](../pypath-network-builder/SKILL.md) — build OmniPath itself, integrate custom resources, fine-grained control beyond what the web service exposes
- [`string-database-ppi`](../string-database-ppi/SKILL.md) — alternative for STRING-only PPI with confidence scores and species coverage
- [`reactome-database`](../reactome-database/SKILL.md) — alternative for Reactome pathway hierarchy and enrichment
- [`cellchat-cell-communication`](../cellchat-cell-communication/SKILL.md) — downstream consumer of OmniPath ligand-receptor pairs

## References

- [omnipath GitHub: saezlab/omnipath](https://github.com/saezlab/omnipath) — Python client source code and issue tracker
- [omnipath documentation](https://omnipath.readthedocs.io/) — full API reference and examples
- [OmniPath web service: omnipathdb.org](https://omnipathdb.org/) — REST endpoints, dataset catalog, and license matrix
- [Türei et al. (2021) Mol Syst Biol 17(3):e9923](https://doi.org/10.15252/msb.20209923) — primary OmniPath publication
- [Türei et al. (2016) Nat Methods 13:966–967](https://doi.org/10.1038/nmeth.4077) — original OmniPath signaling resource
- [DoRothEA TF regulons (Garcia-Alonso et al. 2019)](https://doi.org/10.1101/gr.240663.118) — TF-target confidence levels exposed via `Dorothea`
