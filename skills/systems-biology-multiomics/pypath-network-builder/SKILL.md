---
name: "pypath-network-builder"
description: "Build customized biological knowledge graphs with pypath — the saezlab Python framework that powers OmniPath. Provides ~150 input modules for individual signaling, regulatory, complex, PTM, annotation, and intercellular databases (SIGNOR, SignaLink, KEGG, Reactome, DoRothEA, CollecTRI, CORUM, ComplexPortal, hu.MAP, Compleat, HMDB, RaMP, dbPTM, Phospho.ELM, ...), plus high-level Network/Annotation/Complex/Enz_sub/Intercell aggregator classes that merge the raw inputs and de-duplicate evidence. Includes ID translation utilities, a persistent on-disk cache, and pickle-backed snapshots. Use `omnipath-knowledge-graph` instead when you only need to query the existing OmniPath service via its REST API."
license: "GPL-3.0"
---

# pypath — OmniPath Network Builder

## Overview

`pypath` is the Python framework that builds OmniPath. It loads, normalizes, and integrates ~150 primary biological resources into unified Network, Annotation, Complex, Enzyme-Substrate, and Intercellular databases. Where the lightweight `omnipath` client only queries the pre-built web service, `pypath` operates on the raw input modules — letting you add custom resources, swap ID systems, change merging rules, restrict to specific organisms, or rebuild a private OmniPath snapshot. It also provides reusable utilities: a curl-based caching layer, ID-mapping tables across UniProt/Ensembl/Entrez/HGNC/MGI/MIRBase/RefSeq, and a settings/context system for download timeouts and debug logging.

## When to Use

- Rebuilding OmniPath from primary resources to lock in a reproducible snapshot for a publication
- Loading individual input modules (`pypath.inputs.signor`, `pypath.inputs.kegg`, ...) without going through the integrated database
- Integrating a custom or in-house resource into a Network alongside OmniPath inputs
- Translating identifiers between UniProt, Ensembl, Entrez, HGNC, MGI, RefSeq, miRBase, and chemical IDs (KEGG, ChEBI, HMDB, InChI, SMILES) at scale
- Inspecting per-resource evidence on individual interactions, complexes, or PTMs
- Querying the integrated databases offline from cached pickles after an initial build
- Use `omnipath-knowledge-graph` instead when you only need to query the public OmniPath REST API and do not need to rebuild or extend it
- Use `string-database-ppi` instead when you only need STRING PPI; use `reactome-database` for Reactome pathway hierarchies

## Prerequisites

- **Python packages**: `pypath-omnipath`, `pandas`, `numpy`, `requests`, `lxml`, `pycurl`, `python-igraph`
- **System**: ≥ 8 GB RAM (more for full builds), ≥ 50 GB free disk for cache + pickles on a complete build
- **Network access**: outbound HTTPS to many primary resource websites (saezlab mirrors many of them but some are upstream)
- **Cache**: `~/.pypath/cache/` (raw downloads), `~/.pypath/pickles/` (built database snapshots) by default

```bash
pip install pypath-omnipath pandas python-igraph
```

> **Performance note**: First-time builds of large databases can take 30–90 minutes because pypath downloads from dozens of upstream resources. Subsequent loads use cached pickles and complete in seconds.

## Quick Start

```python
from pypath.core import network
from pypath.resources import network as netres

# Build a literature-curated activity-flow network (the curated subset of OmniPath)
n = network.Network()
n.load(netres.pathway)                # core literature-curated signaling
n.load(netres.enzyme_substrate)       # add kinase/phosphatase-substrate relationships
print(f"Nodes: {n.vcount}   Edges: {n.ecount}")

# Inspect a single interaction
ia = next(iter(n.interactions.values()))
print(ia)
```

## Core API

### Module 1: `pypath.core.network` — The Network Class

The `Network` class is the central aggregator. Resources are added via `load()` and can be queried, exported, or pickled.

```python
from pypath.core import network
from pypath.resources import network as netres

n = network.Network()
n.load(netres.pathway)
n.load(netres.transcription_dorothea, only_directions=True)

# Iterate over interactions and inspect evidence per resource
for ia in list(n.interactions.values())[:3]:
    print(ia.a.label, "->", ia.b.label,
          "  resources:", [str(e) for e in ia.evidences][:3])

# Filter to a subgraph by gene symbols
seed = {"EGFR", "KRAS", "BRAF", "MAP2K1", "MAPK1"}
sub = [ia for ia in n.interactions.values()
       if ia.a.label in seed and ia.b.label in seed]
print(f"Seed-induced subgraph: {len(sub)} edges")
```

```python
# Export to a tidy pandas DataFrame and save as Parquet
df = n.records()
print(df.shape, df.columns.tolist()[:8])

df.to_parquet("network.parquet")
print("Saved network.parquet")

# Pickle the whole Network for fast reload
n.save_to_pickle("network.pkl")
n2 = network.Network.from_pickle("network.pkl")
print(f"Reloaded: {n2.vcount} nodes / {n2.ecount} edges")
```

### Module 2: Resource Presets — `pypath.resources.network`

`pypath.resources.network` ships pre-defined collections of resources covering common analytical layers, so you do not need to assemble them manually.

```python
from pypath.resources import network as netres

# Available presets (each is a dict of {resource_name: ResourceDefinition})
print("Pathway resources:", sorted(netres.pathway)[:8])
print("Transcription presets:", sorted(netres.transcription))
print("PTM resources:", sorted(netres.enzyme_substrate)[:8])

# Single-resource pulls — only SIGNOR, only SignaLink, only KEGG, ...
from pypath.core import network
n = network.Network()
n.load(netres.pathway["SIGNOR"])
print(f"SIGNOR-only network: {n.vcount} nodes / {n.ecount} edges")
```

### Module 3: Input Modules — `pypath.inputs.*`

Each primary resource has its own input module exposing per-resource loaders that return raw or lightly-normalized records (lists of named tuples or DataFrames).

```python
from pypath.inputs import signor, kegg, dorothea

# SIGNOR signaling interactions, complexes, and enzyme-substrate
signor_int = signor.signor_interactions()
print(f"SIGNOR raw interactions: {len(signor_int)}")
print(signor_int[0])

complexes = signor.signor_complexes()
print(f"SIGNOR complexes: {len(complexes)}")

enz = signor.signor_enzyme_substrate()
print(f"SIGNOR enzyme-substrate: {len(enz)}")
```

```python
from pypath.inputs import collectri, hmdb

# CollecTRI TF-target collection
ctri = collectri.collectri_interactions()
print(f"CollecTRI TF-target rows: {len(ctri)}")
print(ctri[0])

# HMDB metabolite metadata
metabolites = hmdb.metabolites_table("accession", "name", "smiles", head=5)
print(metabolites)
```

### Module 4: Annotations / Complexes / Enz_sub / Intercell Aggregators

Each integrated database has its own `core` module that pre-merges all input resources and deduplicates evidence.

```python
from pypath.core import annot, complex as cplx, enz_sub, intercell

# Build (or load from pickle) the annotation database
an = annot.AnnotationTable()
print(f"Annotation records: {len(an)}")

# Protein complex aggregator
co = cplx.ComplexAggregator()
print(f"Complexes: {len(co.complexes)}")

# Enzyme-substrate aggregator (kinase, phosphatase, methyltransferase, ...)
es = enz_sub.EnzymeSubstrateAggregator()
print(f"Enzyme-substrate relationships: {len(es)}")

# Intercell categories merged across resources
ic = intercell.IntercellAnnotation()
print(f"Intercell records: {len(ic)}")
```

### Module 5: ID Mapping — `pypath.utils.mapping`

Translate identifiers across databases and resolve organism/gene-symbol/UniProt mappings used internally by every input module.

```python
from pypath.utils import mapping

# Single-record translation (returns a set of equivalents)
print(mapping.map_name("EGFR", "genesymbol", "uniprot"))         # → {'P00533'}
print(mapping.map_name("P00533", "uniprot", "ensembl_gene_id"))  # → ENSG00000146648
print(mapping.map_name("C01152", "kegg", "inchi"))               # KEGG → InChI

# Bulk translation
genes = ["EGFR", "KRAS", "BRAF", "TP53"]
uniprot_map = {g: mapping.map_name(g, "genesymbol", "uniprot") for g in genes}
print(uniprot_map)

# Inspect available ID types
mapper = mapping.get_mapper()
print("Identifier types known:", len(mapper.id_types()))
```

### Module 6: Cache and Settings — `pypath.share.curl` / `pypath.share.settings`

Manage the on-disk download cache, force fresh downloads, and tune timeouts or debug verbosity.

```python
from pypath.share import curl, settings

# Default cache dirs (expand to absolute paths)
print("Cache dir:    ", settings.get("cachedir"))
print("Pickles dir:  ", settings.get("pickle_dir"))
print("Secrets dir:  ", settings.get("secrets_dir"))

# Bypass cache for a single call (useful when a resource updates)
from pypath.inputs import depod
with curl.cache_off():
    fresh = depod.depod_enzyme_substrate()

# Delete a cached file before the next call (after a corrupted download)
with curl.cache_delete_on():
    fixed = depod.depod_enzyme_substrate()

# Bump the timeout for a slow resource
with settings.context(curl_timeout=360):
    big = depod.depod_enzyme_substrate()

# Verbose curl logging for troubleshooting
with curl.debug_on():
    debug = depod.depod_enzyme_substrate()
```

### Module 7: High-Level OmniPath Database Manager — `pypath.omnipath`

The `omnipath` namespace exposes the same datasets as the public web service, but rebuilt locally with full provenance.

```python
from pypath import omnipath

# Lazy-built database manager: first call builds, subsequent calls use the pickle
cu = omnipath.db.get_db("curated")     # literature-curated signaling
op = omnipath.db.get_db("omnipath")    # full integrated network
tft = omnipath.db.get_db("tf_target")  # transcriptional regulation
print(cu)   # <Network ... nodes / ... edges>
print(op)
print(tft)

# List built-in database names
print("Available DBs:", list(omnipath.db.datasets()))

# Force a rebuild for a specific dataset
omnipath.db.remove_db("curated")
cu = omnipath.db.get_db("curated")
```

## Common Workflows

### Workflow 1: Rebuild a Snapshot of OmniPath Locally

```python
from pypath.core import network
from pypath.resources import network as netres
from pathlib import Path

snap = Path("omnipath_snapshot/")
snap.mkdir(exist_ok=True)

n = network.Network()
n.load(netres.pathway)
n.load(netres.pathway_extra)
n.load(netres.kinase_extra)
n.load(netres.ligand_receptor)
n.load(netres.transcription_dorothea, only_directions=True)
n.load(netres.enzyme_substrate)

print(f"Built snapshot: {n.vcount} nodes / {n.ecount} edges")
n.save_to_pickle(snap / "network.pkl")
n.records().to_parquet(snap / "edges.parquet")
print("Snapshot pickled and exported.")
```

### Workflow 2: Add a Custom In-house Resource to OmniPath

```python
from pypath.core import network
from pypath.resources import network as netres
from pypath.inputs import common
import csv

def my_curated_edges():
    """Yield edges from an internal curation TSV."""
    rows = []
    with open("inhouse_signaling.tsv") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for r in reader:
            rows.append((
                r["source_uniprot"], r["target_uniprot"],
                r["effect"],          # 'stimulation' / 'inhibition'
                r["pmids"],           # 'pmid1;pmid2'
            ))
    return rows

# Build the standard OmniPath core, then layer the custom edges on top
n = network.Network()
n.load(netres.pathway)

custom_added = 0
for src, tgt, effect, pmids in my_curated_edges():
    n.add_interaction(
        a=src, b=tgt,
        attrs={
            "directed":    True,
            "effect":      effect,
            "references":  pmids.split(";"),
            "resource":    "InHouseCuration",
        },
    )
    custom_added += 1

print(f"Custom edges added: {custom_added}")
print(f"Network total: {n.vcount} nodes / {n.ecount} edges")
n.save_to_pickle("network_plus_custom.pkl")
```

### Workflow 3: Build a Tissue-Specific Ligand-Receptor Network

```python
from pypath.core import intercell
from pypath import omnipath

# Build (or load) the integrated databases
ic = omnipath.db.get_db("intercell")
op = omnipath.db.get_db("omnipath")

# Filter to ligand and receptor entities
ligands   = ic.select(scope="generic", category="ligand").entities()
receptors = ic.select(scope="generic", category="receptor").entities()
print(f"Ligands: {len(ligands)}   Receptors: {len(receptors)}")

# Project onto OmniPath edges and keep ligand → receptor pairs
lr_edges = []
for ia in op.interactions.values():
    if ia.a.identifier in ligands and ia.b.identifier in receptors:
        lr_edges.append((ia.a.label, ia.b.label, len(ia.evidences)))

print(f"Ligand → Receptor edges: {len(lr_edges)}")
print(sorted(lr_edges, key=lambda x: -x[2])[:5])
```

### Workflow 4: ID Translation for a Multi-omics Gene Table

```python
from pypath.utils import mapping
import pandas as pd

table = pd.read_csv("multiomics_genes.csv")  # columns: gene_symbol, ensembl_id, ...
def to_uniprot(s):
    hits = mapping.map_name(s, "genesymbol", "uniprot")
    return next(iter(hits)) if hits else None

table["uniprot"] = table["gene_symbol"].apply(to_uniprot)
unmapped = table[table["uniprot"].isna()]
print(f"Mapped: {len(table) - len(unmapped)}/{len(table)}  unmapped: {len(unmapped)}")
table.to_csv("multiomics_genes_with_uniprot.csv", index=False)
```

## Key Parameters

| Parameter | Module / Function | Default | Range / Options | Effect |
|-----------|------------------|---------|-----------------|--------|
| `only_directions` | `Network.load` | `False` | `True` / `False` | When loading a regulatory resource, keep direction but discard sign and effect details |
| `cache_off` (context) | `pypath.share.curl` | off | context manager | Bypass on-disk cache and force fresh HTTP download |
| `cache_delete_on` (context) | `pypath.share.curl` | off | context manager | Delete cached entries before download (recover from corrupted files) |
| `curl_timeout` | `settings.context` | `120` (s) | `30`–`3600` | HTTP timeout when fetching upstream resources |
| `cachedir` | `pypath.share.settings` | `~/.pypath/cache` | any path | Override the on-disk cache root |
| `pickle_dir` | `pypath.share.settings` | `~/.pypath/pickles` | any path | Override the integrated-database pickle directory |
| `head` | `inputs.<resource>.<table>` | `None` | int | Return only the first N rows (useful for quick sanity checks) |
| `target_id_type` | `mapping.map_name` | — | `uniprot`, `genesymbol`, `ensembl_gene_id`, `entrez`, `hgnc`, `mgi`, `refseqp`, `kegg`, `chebi`, `hmdb`, `inchi` | Destination identifier type |
| `ncbi_tax_id` | many input loaders | `9606` (human) | NCBI tax IDs (e.g., `10090` mouse) | Limits resource pulls to the requested organism |
| `dataset` | `omnipath.db.get_db` | — | `curated`, `omnipath`, `tf_target`, `mirna_mrna`, `complex`, `annotations`, `intercell`, `enz_sub` | Selects which integrated database to materialize |

## Common Recipes

### Recipe: Inspect Per-Resource Evidence on a Specific Edge

When to use: you want to know which databases support a particular interaction and with what literature.

```python
from pypath import omnipath

op = omnipath.db.get_db("omnipath")

# Find every edge between EGFR and GRB2
hits = [ia for ia in op.interactions.values()
        if {ia.a.label, ia.b.label} == {"EGFR", "GRB2"}]
print(f"Edges EGFR-GRB2: {len(hits)}")

for ia in hits:
    print(f"{ia.a.label} -> {ia.b.label}")
    for ev in ia.evidences:
        print(f"  resource={ev.resource}  references={list(ev.references)[:3]}")
```

### Recipe: List Every Built-in Resource

When to use: discover which databases pypath can load before designing a custom build.

```python
from pypath.resources import network as netres

for preset in ("pathway", "pathway_extra", "kinase_extra",
               "ligand_receptor", "transcription_dorothea",
               "transcription_collectri", "mirna_target",
               "enzyme_substrate"):
    resources = sorted(getattr(netres, preset))
    print(f"\n{preset} ({len(resources)} resources):")
    for r in resources:
        print(f"  - {r}")
```

### Recipe: Reuse a Pickled Database Across Sessions

When to use: avoid the 30–90 minute first-time build on every analysis run.

```python
from pathlib import Path
from pypath.core import network
from pypath.resources import network as netres

pkl = Path("omnipath.pkl")

if pkl.exists():
    n = network.Network.from_pickle(pkl)
    print(f"Loaded from pickle: {n.vcount} nodes / {n.ecount} edges")
else:
    n = network.Network()
    n.load(netres.pathway)
    n.load(netres.enzyme_substrate)
    n.save_to_pickle(pkl)
    print(f"Built and pickled: {n.vcount} nodes / {n.ecount} edges")
```

### Recipe: Convert a Network to igraph for Topological Analysis

When to use: compute centralities, communities, or shortest paths on the integrated network.

```python
from pypath import omnipath

op = omnipath.db.get_db("omnipath")
g = op.igraph_network()  # builds an igraph.Graph with vertex/edge attrs

print(f"igraph: {g.vcount()} nodes / {g.ecount()} edges")
betw = g.betweenness()
top = sorted(zip(g.vs["label"], betw), key=lambda x: -x[1])[:10]
print("Top betweenness:", top)
```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `ModuleNotFoundError: pypath` | Wrong package name | Install with `pip install pypath-omnipath` (the importable name is `pypath`) |
| First load takes > 1 hour | Full build downloading 100+ resources | Use `omnipath.db.get_db("curated")` for a smaller subset; pickle the result for reuse |
| `pycurl` install fails | Missing libcurl headers / OpenSSL on macOS | `brew install curl openssl` then `PYCURL_SSL_LIBRARY=openssl pip install --no-cache-dir pycurl` |
| `Resource X failed to download` warnings | Upstream resource temporarily down | Re-run with `curl.cache_delete_on()` later; pypath will skip dead resources by default |
| Cache disk usage exceeds tens of GB | Many large resources cached locally | Move cache: `settings.set("cachedir", "/data/pypath_cache")` and re-run |
| Stale pickle after pypath upgrade | Pickle was written by an older version | Delete `~/.pypath/pickles/` and rebuild; pickles are not always forward-compatible |
| `KeyError` from `mapping.map_name` | Identifier type name typo | List supported types with `mapping.get_mapper().id_types()` |
| Network has zero edges after `load()` | Wrong organism or empty resource subset | Pass `ncbi_tax_id=9606` (or your species), confirm the resource supports that organism |
| Memory error during build | Several integrated DBs exceed 8 GB residency | Run on a machine with ≥ 32 GB RAM, or build databases one at a time and pickle each |

## Related Skills

- [`omnipath-knowledge-graph`](../omnipath-knowledge-graph/SKILL.md) — lightweight REST client for the public OmniPath service when no custom build is needed
- [`string-database-ppi`](../string-database-ppi/SKILL.md) — STRING-only protein-protein interactions
- [`reactome-database`](../reactome-database/SKILL.md) — Reactome pathway hierarchy and enrichment
- [`kegg-pathway-analysis`](../kegg-pathway-analysis/SKILL.md) — KEGG-only pathway analysis

## References

- [pypath GitHub: saezlab/pypath](https://github.com/saezlab/pypath) — source code, issue tracker, and changelog
- [pypath documentation](https://pypath.omnipathdb.org/) — API reference, manual, and resource catalog
- [OmniPath web service: omnipathdb.org](https://omnipathdb.org/) — REST endpoints and dataset catalog
- [Türei et al. (2021) Mol Syst Biol 17(3):e9923](https://doi.org/10.15252/msb.20209923) — primary OmniPath / pypath publication
- [Türei et al. (2016) Nat Methods 13:966–967](https://doi.org/10.1038/nmeth.4077) — original OmniPath signaling resource
- [Resource catalog (saezlab)](https://saezlab.github.io/pypath/) — visual index of all input modules and their citations
