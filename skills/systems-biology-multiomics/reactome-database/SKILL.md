---
name: reactome-database
description: "Query Reactome pathways via REST: pathway queries, entity lookup, keyword search, gene list enrichment, hierarchy, cross-refs. Content + Analysis services. Python wrapper: reactome2py. For KEGG use kegg-database; for PPIs use string-database-ppi."
license: CC-BY-4.0
---

# Reactome Database — Biological Pathway Queries & Enrichment Analysis

## Overview

Reactome is an open-source, curated database of biological pathways and reactions for 16+ species. It provides two REST APIs: the **Content Service** for querying pathway data, entities, and hierarchy, and the **Analysis Service** for gene/protein list enrichment and expression data overlay. All endpoints return JSON (default) or other formats and require no authentication.

## When to Use

- Querying pathway details by stable ID (e.g., R-HSA-69620 for Cell Cycle)
- Searching for pathways, reactions, or entities by keyword
- Running gene list enrichment analysis (over-representation) against Reactome pathways
- Retrieving pathway hierarchy and containment relationships
- Mapping identifiers across databases (UniProt, Ensembl, NCBI, ChEBI)
- Getting species-specific pathway data (human, mouse, rat, and 13+ other organisms)
- Retrieving analysis results by token for sharing or re-filtering
- Building pathway context for multi-omics integration workflows
- For **KEGG metabolic pathways** and cross-database ID conversion, use `kegg-database` instead
- For **protein-protein interaction networks**, use `string-database-ppi` instead
- For **a Python wrapper with caching**, consider `reactome2py` (`pip install reactome2py`)

## Prerequisites

```bash
pip install requests
```

**API constraints**:
- **No authentication required** — all endpoints are public
- **No documented hard rate limit** — add `time.sleep(0.5)` between batch requests to be respectful
- **Content Service base URL**: `https://reactome.org/ContentService`
- **Analysis Service base URL**: `https://reactome.org/AnalysisService`
- **Identifier input**: gene/protein lists accept UniProt IDs, Ensembl gene IDs, NCBI Gene IDs, HGNC symbols, ChEBI IDs, miRBase IDs, KEGG IDs, and more

## Quick Start

```python
import requests
import time

CONTENT = "https://reactome.org/ContentService"
ANALYSIS = "https://reactome.org/AnalysisService"

def reactome_get(base, path, params=None):
    """Generic Reactome REST API caller. Returns JSON or raises."""
    resp = requests.get(f"{base}{path}", params=params)
    resp.raise_for_status()
    try:
        return resp.json()
    except ValueError:
        return resp.text

# Check database version
version = reactome_get(CONTENT, "/data/database/version")
print(f"Reactome version: {version}")

# Query a pathway
pathway = reactome_get(CONTENT, "/data/query/R-HSA-69620")
print(f"Pathway: {pathway['displayName']}")
print(f"Species: {pathway['speciesName']}")
time.sleep(0.5)

# Search for pathways
results = reactome_get(CONTENT, "/search/query", params={"query": "apoptosis", "types": "Pathway"})
print(f"Found {results['found']} results for 'apoptosis'")
```

## Core API

### 1. Pathway & Entity Queries

Retrieve detailed information about pathways, reactions, and biological entities by stable ID. Uses `reactome_get` helper from Quick Start.

```python
# Query pathway by stable ID
pathway = reactome_get(CONTENT, "/data/query/R-HSA-69620")
print(f"Name: {pathway['displayName']}")
print(f"Stable ID: {pathway['stId']}, Species: {pathway['speciesName']}")
print(f"Schema class: {pathway['schemaClass']}")  # Pathway, TopLevelPathway, etc.
time.sleep(0.5)

# Get participating physical entities in a pathway
entities = reactome_get(CONTENT, f"/data/participants/{pathway['stId']}")
print(f"\nParticipating entities: {len(entities)}")
for e in entities[:3]:
    print(f"  {e['displayName']} ({e['schemaClass']})")
time.sleep(0.5)

# Get participating molecules with reference entities (UniProt, ChEBI, etc.)
refs = reactome_get(CONTENT, f"/data/participants/{pathway['stId']}/referenceEntities")
print(f"\nReference entities: {len(refs)}")
for r in refs[:3]:
    print(f"  {r['displayName']} — {r.get('databaseName', 'N/A')}:{r.get('identifier', 'N/A')}")
```

### 2. Search & Discovery

Search across Reactome by keyword with faceted filtering.

```python
# Keyword search filtered to Pathways
results = reactome_get(CONTENT, "/search/query", params={
    "query": "cell cycle",
    "types": "Pathway",
    "species": "Homo sapiens",
    "cluster": "true"
})
print(f"Total found: {results['found']}")
for entry in results.get("results", [])[:1]:
    for e in entry.get("entries", [])[:5]:
        print(f"  {e['stId']}: {e['name']}")
time.sleep(0.5)

# Search for proteins/complexes
proteins = reactome_get(CONTENT, "/search/query", params={
    "query": "TP53", "types": "Protein", "species": "Homo sapiens"
})
print(f"\nTP53 protein entries: {proteins['found']}")
time.sleep(0.5)

# Suggest (autocomplete)
suggestions = reactome_get(CONTENT, "/search/suggest", params={"query": "apopt"})
print(f"Suggestions: {suggestions}")
```

**Searchable types**: `Pathway`, `Reaction`, `Protein`, `Complex`, `SmallMolecule`, `Gene`, `DNA`, `RNA`, `Drug`, `ReferenceEntity`

### 3. Enrichment Analysis

Submit a gene/protein list for over-representation analysis against Reactome pathways.

```python
import requests
import time

ANALYSIS = "https://reactome.org/AnalysisService"

# Gene list (newline-separated identifiers — UniProt, HGNC symbols, Ensembl, etc.)
gene_list = "TP53\nBRCA1\nBRCA2\nATM\nCHEK2\nCDK2\nRB1\nMDM2\nCDKN1A\nBAX"

# Submit for enrichment (POST with text body)
resp = requests.post(
    f"{ANALYSIS}/identifiers/",
    headers={"Content-Type": "text/plain"},
    data=gene_list,
    params={"pageSize": 10, "page": 1, "sortBy": "ENTITIES_FDR", "order": "ASC"}
)
resp.raise_for_status()
result = resp.json()

print(f"Analysis token: {result['summary']['token']}")
print(f"Pathways found: {result['pathwaysFound']}")
print(f"Identifiers found: {result['identifiersNotFound']}")
print(f"\nTop enriched pathways:")
for p in result["pathways"][:5]:
    print(f"  {p['stId']}: {p['name']}")
    print(f"    FDR: {p['entities']['fdr']:.2e}, "
          f"Found: {p['entities']['found']}/{p['entities']['total']}")
time.sleep(0.5)
```

**Analysis accepts**: newline-separated identifiers, or tab-separated with expression values (for expression overlay). Supported IDs include UniProt, HGNC symbols, Ensembl, NCBI Gene, ChEBI, miRBase, KEGG, and more.

### 4. Analysis Results & Filtering

Retrieve previously computed analysis results by token and apply filters.

```python
import requests
import time

ANALYSIS = "https://reactome.org/AnalysisService"

# Re-fetch results by token (from a previous analysis)
token = "MjAyNTA2MTcxMDA3MzRfMQ%3D%3D"  # example — use token from Module 3

# Get results with filtering
results = requests.get(f"{ANALYSIS}/token/{token}", params={
    "pageSize": 20,
    "page": 1,
    "sortBy": "ENTITIES_FDR",
    "species": "Homo sapiens",
    "resource": "TOTAL"  # TOTAL, UNIPROT, ENSEMBL, CHEBI, etc.
})
results.raise_for_status()
data = results.json()
print(f"Token: {data['summary']['token']}")
print(f"Pathways: {data['pathwaysFound']}")
time.sleep(0.5)

# Get identifiers found in a specific pathway
pathway_detail = requests.get(
    f"{ANALYSIS}/token/{token}/found/all/{data['pathways'][0]['stId']}"
)
pathway_detail.raise_for_status()
found = pathway_detail.json()
print(f"\nIdentifiers found in {data['pathways'][0]['name']}:")
for entity in found.get("entities", [])[:5]:
    mapsTo = [m["identifier"] for m in entity.get("mapsTo", [])]
    print(f"  {entity['id']} -> {mapsTo}")
```

**Token persistence**: analysis tokens are valid for several hours. Share tokens to let collaborators view the same results without re-running. Filter by `resource` (TOTAL, UNIPROT, ENSEMBL, CHEBI, etc.) and `species`.

### 5. Pathway Hierarchy & Events

Navigate the Reactome pathway hierarchy from top-level pathways down to reactions.

```python
# Top-level pathways for human (9606 = NCBI taxonomy ID)
top = reactome_get(CONTENT, "/data/pathways/top/9606")
print(f"Top-level human pathways: {len(top)}")
for p in top[:5]:
    print(f"  {p['stId']}: {p['displayName']}")
time.sleep(0.5)

# Get contained events (sub-pathways and reactions)
events = reactome_get(CONTENT, "/data/pathway/R-HSA-69620/containedEvents")
print(f"\nContained events in Cell Cycle: {len(events)}")
for e in events[:5]:
    print(f"  {e['stId']}: {e['displayName']} ({e['schemaClass']})")
time.sleep(0.5)

# Get the full ancestor chain for a pathway
ancestors = reactome_get(CONTENT, "/data/event/R-HSA-69620/ancestors")
print(f"\nAncestors of Cell Cycle:")
for chain in ancestors:
    names = [a["displayName"] for a in chain]
    print(f"  {' > '.join(names)}")
```

**Species identifiers**: use NCBI taxonomy IDs (9606=human, 10090=mouse, 10116=rat) or species names.

### 6. Cross-References & Species

Map identifiers across databases and query species-specific data.

```python
# List all species in Reactome
species = reactome_get(CONTENT, "/data/species/all")
print(f"Species in Reactome: {len(species)}")
for s in species[:5]:
    print(f"  {s['displayName']} (taxId: {s['taxId']})")
time.sleep(0.5)

# Map a Reactome entity to external references
xrefs = reactome_get(CONTENT, "/data/query/R-HSA-69620/xrefs")
if isinstance(xrefs, list):
    print(f"\nCross-references for R-HSA-69620: {len(xrefs)}")
    for x in xrefs[:5]:
        print(f"  {x}")
time.sleep(0.5)

# Get orthologous pathway in another species (human → mouse)
mouse_ortho = reactome_get(CONTENT, "/data/orthology/R-HSA-69620/species/10090")
if mouse_ortho:
    for o in mouse_ortho[:3]:
        print(f"Mouse ortholog: {o['stId']}: {o['displayName']}")
```

## Key Concepts

### Pathway Hierarchy

Reactome organizes knowledge in a hierarchical structure:

| Level | Schema Class | Example |
|-------|-------------|---------|
| Top-Level Pathway | `TopLevelPathway` | Cell Cycle, Immune System, Metabolism |
| Pathway | `Pathway` | Cell Cycle Checkpoints, Mitotic G1-G1/S phases |
| Reaction | `Reaction` | TP53 binds RB1 |
| Physical Entity | `EntityWithAccessionedSequence` | TP53 [cytosol] |

Pathways contain sub-pathways and reactions. Reactions connect input/output physical entities. Each entity maps to reference databases (UniProt, ChEBI, Ensembl).

### Supported Identifiers

The Analysis Service accepts a wide range of identifiers:

| Database | Example ID | Type |
|----------|-----------|------|
| UniProt | P04637 | Protein |
| HGNC Symbol | TP53 | Gene symbol |
| Ensembl Gene | ENSG00000141510 | Gene |
| NCBI Gene | 7157 | Gene |
| ChEBI | CHEBI:15377 | Small molecule |
| miRBase | hsa-miR-21-5p | microRNA |
| KEGG Gene | hsa:7157 | Gene (KEGG format) |
| Ensembl Protein | ENSP00000269305 | Protein |

### Analysis Token System

When you submit an analysis, Reactome returns a **token** — a URL-safe string that identifies your result set. Tokens enable:
- **Re-fetching** results without re-running analysis (`GET /token/{token}`)
- **Filtering** results by species or resource after initial analysis
- **Sharing** results with collaborators via URL: `https://reactome.org/PathwayBrowser/#/DTAB=AN&ANALYSIS={token}`
- Tokens expire after several hours; re-submit the gene list if needed

## Common Workflows

### Workflow 1: Gene List Enrichment Pipeline

**Goal**: Submit a gene list, get enriched pathways, and explore top hits.

```python
import requests
import time

CONTENT = "https://reactome.org/ContentService"
ANALYSIS = "https://reactome.org/AnalysisService"

# Step 1: Submit gene list
genes = "TP53\nBRCA1\nBRCA2\nATM\nCHEK2\nCDK2\nRB1\nMDM2\nCDKN1A\nBAX"
resp = requests.post(
    f"{ANALYSIS}/identifiers/",
    headers={"Content-Type": "text/plain"},
    data=genes,
    params={"pageSize": 5, "sortBy": "ENTITIES_FDR", "order": "ASC"}
)
resp.raise_for_status()
result = resp.json()
token = result["summary"]["token"]
print(f"Token: {token} | Pathways found: {result['pathwaysFound']}")

# Step 2: Show top pathways with FDR
for p in result["pathways"][:5]:
    fdr = p["entities"]["fdr"]
    ratio = f"{p['entities']['found']}/{p['entities']['total']}"
    print(f"  {p['stId']}: {p['name']} (FDR={fdr:.2e}, {ratio})")
time.sleep(0.5)

# Step 3: Get details on top pathway
top_id = result["pathways"][0]["stId"]
detail = requests.get(f"{CONTENT}/data/query/{top_id}").json()
print(f"\nTop pathway: {detail['displayName']}")
print(f"Compartments: {[c['displayName'] for c in detail.get('compartment', [])]}")
```

### Workflow 2: Pathway Exploration

**Goal**: Navigate from a top-level pathway down to specific reactions and entities.

```python
# Uses reactome_get helper and CONTENT base URL from Quick Start

# Step 1: Find pathway by search
results = reactome_get(CONTENT, "/search/query",
                       params={"query": "DNA repair", "types": "Pathway", "species": "Homo sapiens"})
top_hit = results["results"][0]["entries"][0]
pid = top_hit["stId"]
print(f"Found: {pid} — {top_hit['name']}")
time.sleep(0.5)

# Step 2: Get sub-events
events = reactome_get(CONTENT, f"/data/pathway/{pid}/containedEvents")
reactions = [e for e in events if e["schemaClass"] == "Reaction"]
subpaths = [e for e in events if "Pathway" in e["schemaClass"]]
print(f"Sub-pathways: {len(subpaths)}, Reactions: {len(reactions)}")
time.sleep(0.5)

# Step 3: Get participating molecules for a reaction
if reactions:
    rxn = reactions[0]
    refs = reactome_get(CONTENT, f"/data/participants/{rxn['stId']}/referenceEntities")
    print(f"\n{rxn['displayName']} participants:")
    for r in refs[:5]:
        print(f"  {r.get('databaseName', '?')}:{r.get('identifier', '?')} — {r['displayName']}")
```

### Workflow 3: Expression Data Analysis

**Goal**: Submit expression values alongside identifiers for pathway-level expression overlay.

```python
import requests

ANALYSIS = "https://reactome.org/AnalysisService"

# Tab-separated: identifier \t expression_value1 \t expression_value2 ...
# First line can be a header (auto-detected)
expression_data = """#id\tcontrol\ttreated
TP53\t1.2\t3.5
BRCA1\t2.1\t1.8
CDK2\t0.9\t4.2
RB1\t1.5\t0.6
MDM2\t1.0\t2.8
CDKN1A\t0.8\t5.1
BAX\t1.1\t3.9"""

resp = requests.post(
    f"{ANALYSIS}/identifiers/",
    headers={"Content-Type": "text/plain"},
    data=expression_data,
    params={"pageSize": 10, "sortBy": "ENTITIES_FDR"}
)
resp.raise_for_status()
result = resp.json()

print(f"Expression columns: {result['summary'].get('sampleName', 'N/A')}")
print(f"Token: {result['summary']['token']}")
for p in result["pathways"][:3]:
    exp = p["entities"].get("exp", [])
    print(f"  {p['name']}: FDR={p['entities']['fdr']:.2e}, expr={exp}")
```

## Key Parameters

| Parameter | Function/Endpoint | Default | Options | Effect |
|-----------|-------------------|---------|---------|--------|
| `query` | `/search/query` | — | Any string | Keyword search term |
| `types` | `/search/query` | All | `Pathway`, `Reaction`, `Protein`, etc. | Filter search by schema class |
| `species` | `/search/query`, analysis | All | Species name or taxon ID | Restrict to organism |
| `pageSize` | Analysis, search | 20 | 1-250 | Results per page |
| `sortBy` | Analysis | `ENTITIES_PVALUE` | `ENTITIES_FDR`, `ENTITIES_PVALUE`, `ENTITIES_FOUND`, `NAME` | Sort enrichment results |
| `resource` | Analysis filtering | `TOTAL` | `TOTAL`, `UNIPROT`, `ENSEMBL`, `CHEBI`, etc. | Filter by identifier source |
| `cluster` | `/search/query` | `true` | `true`, `false` | Group search results by type |

## Best Practices

1. **Use `time.sleep(0.5)` between sequential requests**: Reactome has no documented hard rate limit, but rapid-fire requests may be throttled. Be courteous to the shared resource.

2. **Save and reuse analysis tokens**: Tokens remain valid for hours. Store the token to re-filter results by species or resource without re-submitting.

3. **Prefer stable IDs over database IDs**: Reactome stable IDs (R-HSA-69620) are permanent. Internal database IDs can change between releases.

4. **Use `sortBy=ENTITIES_FDR`** for enrichment results: FDR-corrected p-values are more reliable than raw p-values for pathway-level significance.

5. **Check `identifiersNotFound`** in analysis results: a high unmapped count may indicate wrong identifier type or outdated IDs.

## Common Recipes

### Recipe: Get All Genes in a Pathway

```python
import requests

CONTENT = "https://reactome.org/ContentService"

pathway_id = "R-HSA-69620"  # Cell Cycle
refs = requests.get(f"{CONTENT}/data/participants/{pathway_id}/referenceEntities").json()
genes = set()
for r in refs:
    if r.get("databaseName") == "UniProt":
        genes.add(r.get("displayName", r.get("identifier")))
print(f"UniProt proteins in {pathway_id}: {len(genes)}")
for g in sorted(genes)[:10]:
    print(f"  {g}")
```

### Recipe: Pathway Diagram URL

```python
# Generate a direct link to the Reactome pathway diagram
pathway_id = "R-HSA-69620"
diagram_url = f"https://reactome.org/PathwayBrowser/#/{pathway_id}"
print(f"View diagram: {diagram_url}")

# With analysis overlay
token = "YOUR_TOKEN"
overlay_url = f"https://reactome.org/PathwayBrowser/#/{pathway_id}&DTAB=AN&ANALYSIS={token}"
print(f"View with analysis: {overlay_url}")
```

### Recipe: Batch Pathway Query

```python
import requests
import time

CONTENT = "https://reactome.org/ContentService"

pathway_ids = ["R-HSA-69620", "R-HSA-109581", "R-HSA-1640170"]
summaries = []
for pid in pathway_ids:
    resp = requests.get(f"{CONTENT}/data/query/{pid}")
    resp.raise_for_status()
    data = resp.json()
    summaries.append({
        "stId": data["stId"],
        "name": data["displayName"],
        "species": data["speciesName"],
        "hasDiagram": data.get("hasDiagram", False)
    })
    time.sleep(0.5)

for s in summaries:
    print(f"{s['stId']}: {s['name']} (diagram: {s['hasDiagram']})")
```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `404 Not Found` | Invalid stable ID or wrong species prefix | Verify ID format: `R-HSA-{number}` for human; use `/search/query` to find valid IDs |
| `400 Bad Request` | Malformed POST body or wrong Content-Type | Use `Content-Type: text/plain` for analysis; newline-separated identifiers |
| Empty analysis results | Identifiers not recognized | Check `identifiersNotFound`; try different ID types (UniProt vs HGNC symbol) |
| `500 Internal Server Error` | Server-side issue or very large input | Retry after delay; split large gene lists (>2000 IDs) into batches |
| Token expired | Analysis results no longer available | Re-submit the gene list; tokens last several hours |
| Wrong species results | No species filter applied | Add `species=Homo sapiens` parameter to search/analysis |
| Slow response | Large pathway with many entities | Use `pageSize` to paginate; cache results locally |
| Cross-reference returns empty | Entity has no external DB mapping | Not all Reactome entities have UniProt/Ensembl mappings; check entity schema class |

## Bundled Resources

This skill consolidates content from:
- **API reference** (465 lines): Content Service endpoints (data/query, search, participants, pathway hierarchy, species, xrefs) and Analysis Service endpoints (identifiers, token retrieval, filtering) are covered across Core API modules 1-6. Supported identifier types are in Key Concepts. Response format details and error handling are in Troubleshooting.
- **Query script** (286 lines): ReactomeClient class methods (query_pathway, get_pathway_entities, search_pathways, analyze_genes, get_analysis_by_token) are absorbed into Core API code blocks and Common Workflows.

## Related Skills

- **kegg-database** — KEGG pathway queries and metabolic network data; use for metabolic pathway focus and cross-database ID conversion
- **string-database-ppi** — protein-protein interaction networks from STRING; complements Reactome pathway data with interaction evidence
- **bioservices-multi-database** — unified Python interface to 40+ databases including Reactome via `bioservices.Reactome`
- **cobrapy-metabolic-modeling** — constraint-based metabolic modeling; use Reactome pathway data as input for FBA analysis

## References

- [Reactome Content Service API](https://reactome.org/ContentService/) — interactive API documentation (Swagger)
- [Reactome Analysis Service API](https://reactome.org/AnalysisService/) — enrichment analysis API documentation
- [Reactome website](https://reactome.org/) — pathway browser, diagram viewer, species comparison
- [reactome2py](https://github.com/reactome/reactome2py) — official Python wrapper for Reactome APIs
- Gillespie, M. et al. (2022) "The reactome pathway knowledgebase 2022" *Nucleic Acids Research* 50:D364-D370
