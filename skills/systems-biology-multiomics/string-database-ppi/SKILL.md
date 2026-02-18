---
name: string-database-ppi
description: Query STRING REST API for protein-protein interactions (59M proteins, 20B interactions, 5000+ species). Retrieve interaction networks, perform GO/KEGG enrichment analysis, discover interaction partners, test PPI enrichment significance, generate network visualizations, and analyze protein homology for systems biology and pathway analysis.
license: CC-BY-4.0
---

# STRING Database — Protein-Protein Interactions

## Overview

Query the STRING protein-protein interaction database (59M proteins, 20B+ interactions, 5000+ species) via REST API. Covers network retrieval, functional enrichment (GO, KEGG, Pfam), interaction partner discovery, PPI enrichment testing, network visualization, and homology analysis.

## When to Use

- Retrieving protein-protein interaction networks for one or multiple proteins
- Performing functional enrichment analysis (GO, KEGG, Pfam, InterPro) on protein lists
- Discovering interaction partners and expanding protein networks from seed proteins
- Testing whether a set of proteins forms a significantly enriched functional module
- Generating network visualizations with evidence-based coloring
- Analyzing homology and protein family relationships across species
- Identifying hub proteins and network connectivity patterns
- For chemical compound interactions use chembl-database-bioactivity instead; for pathway-centric queries use kegg-database

## Prerequisites

```bash
uv pip install requests pandas
```

**Rate limiting**: No strict rate limit, but wait ~1 second between API calls. For proteome-scale analyses, use bulk downloads from https://string-db.org/cgi/download instead of the API.

## Quick Start

```python
import requests
import time

STRING_API = "https://string-db.org/api"

def string_query(endpoint, params, fmt="tsv"):
    """Reusable helper for all STRING API calls."""
    url = f"{STRING_API}/{fmt}/{endpoint}"
    params.setdefault("caller_identity", "python_script")
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.text

# Map gene names to STRING IDs (always do this first)
result = string_query("get_string_ids", {
    "identifiers": "TP53\nBRCA1\nEGFR",
    "species": 9606
})
print(result)

# Get interaction network
time.sleep(1)
network = string_query("network", {
    "identifiers": "TP53%0dBRCA1%0dMDM2",
    "species": 9606,
    "required_score": 400
})
print(network[:500])
```

## Key Concepts

### Common Species NCBI Taxon IDs

| Organism | Common Name | Taxon ID |
|----------|-------------|----------|
| Homo sapiens | Human | 9606 |
| Mus musculus | Mouse | 10090 |
| Rattus norvegicus | Rat | 10116 |
| Drosophila melanogaster | Fruit fly | 7227 |
| Caenorhabditis elegans | C. elegans | 6239 |
| Saccharomyces cerevisiae | Yeast | 4932 |
| Arabidopsis thaliana | Thale cress | 3702 |
| Escherichia coli K-12 | E. coli | 511145 |
| Danio rerio | Zebrafish | 7955 |
| Gallus gallus | Chicken | 9031 |

Full species list: https://string-db.org/cgi/input?input_page_active_form=organisms

### STRING Identifier Format

STRING uses Ensembl protein IDs with taxon prefix: `{taxonId}.{ensemblProteinId}` (e.g., `9606.ENSP00000269305` for human TP53). Always map gene names to STRING IDs first via `get_string_ids` for faster subsequent queries.

### Interaction Confidence Scores

Combined scores (0-1000) integrating 7 evidence channels:

| Channel | Code | Source |
|---------|------|--------|
| Neighborhood | `nscore` | Conserved genomic neighborhood |
| Fusion | `fscore` | Gene fusion events |
| Phylogenetic profile | `pscore` | Co-occurrence across species |
| Coexpression | `ascore` | Correlated RNA expression |
| Experimental | `escore` | Biochemical/genetic experiments |
| Database | `dscore` | Curated pathway/complex databases |
| Text-mining | `tscore` | Literature co-occurrence and NLP |

**Recommended thresholds**:
- **150**: Low confidence (exploratory, hypothesis generation)
- **400**: Medium confidence (standard analysis, default)
- **700**: High confidence (conservative, fewer false positives)
- **900**: Highest confidence (very stringent, experimental evidence preferred)

### Network Types

- **Functional** (default): All evidence types — proteins functionally associated even without direct binding. Use for pathway analysis, enrichment, systems biology
- **Physical**: Direct binding evidence only — experimental data and curated physical interactions. Use for structural studies, complex analysis

### Output Formats

Replace `/tsv/` in the URL with the desired format:
- **TSV**: Tab-separated (default, best for data processing)
- **JSON**: Structured data (`/json/`)
- **PNG/SVG**: Network images (`/image/`)
- **PSI-MI/PSI-MITAB**: Proteomics standard formats

## Core API

### 1. Identifier Mapping

```python
# Map gene names to STRING IDs
result = string_query("get_string_ids", {
    "identifiers": "TP53\nBRCA1\nEGFR",
    "species": 9606,
    "limit": 1,        # matches per identifier
    "echo_query": 1    # include query term in output
})

# Parse the mapping
import pandas as pd
import io
df = pd.read_csv(io.StringIO(result), sep='\t')
id_map = dict(zip(df['queryItem'], df['stringId']))
print(id_map)
# {'TP53': '9606.ENSP00000269305', 'BRCA1': '9606.ENSP00000...', ...}
```

### 2. Network Retrieval

```python
# Get PPI network with confidence scores
network = string_query("network", {
    "identifiers": "TP53%0dBRCA1%0dMDM2%0dATM%0dCHEK2",
    "species": 9606,
    "required_score": 400,
    "network_type": "functional"  # or "physical"
})

# Parse network edges
time.sleep(1)
df = pd.read_csv(io.StringIO(network), sep='\t')
print(f"Found {len(df)} interactions")
print(df[['preferredName_A', 'preferredName_B', 'score']].head())

# Expand network with additional interactors
expanded = string_query("network", {
    "identifiers": "TP53",
    "species": 9606,
    "add_nodes": 10,  # add 10 most connected proteins
    "required_score": 700
})
```

### 3. Network Visualization

```python
# Get PNG network image
url = f"{STRING_API}/image/network"
params = {
    "identifiers": "TP53%0dMDM2%0dATM%0dCHEK2%0dBRCA1",
    "species": 9606,
    "required_score": 700,
    "network_flavor": "evidence",  # "evidence", "confidence", or "actions"
    "caller_identity": "python_script"
}
response = requests.get(url, params=params)
with open("network.png", "wb") as f:
    f.write(response.content)
```

### 4. Interaction Partners

```python
# Discover top interaction partners
partners = string_query("interaction_partners", {
    "identifiers": "TP53",
    "species": 9606,
    "limit": 20,
    "required_score": 700
})

df = pd.read_csv(io.StringIO(partners), sep='\t')
print(f"Top 20 TP53 interactors:")
print(df[['preferredName_B', 'score']].head(10))
```

### 5. Functional Enrichment

```python
# GO, KEGG, Pfam, InterPro, SMART, UniProt Keywords enrichment
# Statistical method: Fisher's exact test with Benjamini-Hochberg FDR correction
enrichment = string_query("enrichment", {
    "identifiers": "TP53%0dMDM2%0dATM%0dCHEK2%0dBRCA1%0dATR%0dTP73",
    "species": 9606
})

df = pd.read_csv(io.StringIO(enrichment), sep='\t')
significant = df[df['fdr'] < 0.05]
print(f"Significant terms: {len(significant)}")

# Group by annotation category
for cat, group in significant.groupby('category'):
    print(f"\n{cat}: {len(group)} terms")
    for _, row in group.head(3).iterrows():
        print(f"  {row['description']} (FDR={row['fdr']:.2e})")
```

### 6. PPI Enrichment Testing

```python
import json

# Test if proteins form a significant functional module
result = string_query("ppi_enrichment", {
    "identifiers": "TP53%0dMDM2%0dATM%0dCHEK2%0dBRCA1",
    "species": 9606,
    "required_score": 400
}, fmt="json")

data = json.loads(result)
print(f"Observed edges: {data['number_of_edges']}")
print(f"Expected edges: {data['expected_number_of_edges']}")
print(f"P-value: {data['p_value']}")
# p < 0.05 → proteins form a significantly enriched network
```

### 7. Homology Scores

```python
# Get homology/similarity between proteins
homology = string_query("homology", {
    "identifiers": "TP53%0dTP63%0dTP73",
    "species": 9606
})
print(homology)
```

## Common Workflows

### Workflow 1: Protein List Analysis (Standard)

```python
import requests, pandas as pd, io, json, time

STRING_API = "https://string-db.org/api"
def string_query(endpoint, params, fmt="tsv"):
    url = f"{STRING_API}/{fmt}/{endpoint}"
    params.setdefault("caller_identity", "python_script")
    response = requests.get(url, params=params)
    response.raise_for_status()
    time.sleep(1)
    return response.text

genes = "TP53%0dBRCA1%0dATM%0dCHEK2%0dMDM2%0dATR%0dBRCA2"

# Step 1: Map identifiers
mapping = string_query("get_string_ids", {"identifiers": genes.replace("%0d", "\n"), "species": 9606})

# Step 2: Get interaction network
network = string_query("network", {"identifiers": genes, "species": 9606, "required_score": 400})
net_df = pd.read_csv(io.StringIO(network), sep='\t')
print(f"Network: {len(net_df)} interactions")

# Step 3: Test PPI enrichment
ppi = json.loads(string_query("ppi_enrichment", {"identifiers": genes, "species": 9606}, fmt="json"))
print(f"PPI enrichment p-value: {ppi['p_value']}")

# Step 4: Functional enrichment
enrich = string_query("enrichment", {"identifiers": genes, "species": 9606})
enrich_df = pd.read_csv(io.StringIO(enrich), sep='\t')
sig = enrich_df[enrich_df['fdr'] < 0.05]
print(f"Significant GO/KEGG terms: {len(sig)}")

# Step 5: Save network image
img_resp = requests.get(f"{STRING_API}/image/network", params={
    "identifiers": genes, "species": 9606, "required_score": 400,
    "network_flavor": "evidence", "caller_identity": "python_script"
})
with open("protein_network.png", "wb") as f:
    f.write(img_resp.content)
```

### Workflow 2: Network Expansion from Seed Proteins

```python
# Start with seed proteins, discover connected functional modules
seed = "TP53"

# Step 1: Get high-confidence interaction partners
partners = string_query("interaction_partners", {
    "identifiers": seed, "species": 9606, "limit": 30, "required_score": 700
})
df = pd.read_csv(io.StringIO(partners), sep='\t')
all_proteins = list(set(df['preferredName_A'].tolist() + df['preferredName_B'].tolist()))
print(f"Expanded network: {len(all_proteins)} proteins")

# Step 2: Enrichment on expanded set
expanded_ids = "%0d".join(all_proteins[:50])
enrichment = string_query("enrichment", {"identifiers": expanded_ids, "species": 9606})
enrich_df = pd.read_csv(io.StringIO(enrichment), sep='\t')
modules = enrich_df[enrich_df['fdr'] < 0.001]
print(f"Highly significant terms: {len(modules)}")
```

### Workflow 3: Cross-Species Comparison

```python
# Compare protein interactions across species
for species, name, gene in [(9606, "Human", "TP53"), (10090, "Mouse", "Trp53")]:
    network = string_query("network", {
        "identifiers": gene, "species": species,
        "required_score": 700, "add_nodes": 5
    })
    df = pd.read_csv(io.StringIO(network), sep='\t')
    print(f"{name} ({gene}): {len(df)} interactions at score >= 700")
```

## Common Recipes

### Recipe: Parse Enrichment Results to DataFrame

```python
import pandas as pd, io

enrichment_tsv = string_query("enrichment", {
    "identifiers": "TP53%0dBRCA1%0dATM", "species": 9606
})
df = pd.read_csv(io.StringIO(enrichment_tsv), sep='\t')
# Columns: category, term, description, number_of_genes, p_value, fdr
kegg = df[df['category'] == 'KEGG'].sort_values('fdr')
print(kegg[['description', 'fdr']].head(5))
```

### Recipe: Batch Protein Queries with Rate Limiting

```python
import time

protein_lists = [["TP53", "MDM2"], ["EGFR", "ERBB2"], ["BRCA1", "BRCA2"]]
results = []
for proteins in protein_lists:
    ids = "%0d".join(proteins)
    network = string_query("network", {"identifiers": ids, "species": 9606})
    results.append(network)
    time.sleep(1)  # respect rate limits
```

### Recipe: Version Check for Reproducibility

```python
version = string_query("version", {})
print(f"STRING version: {version.strip()}")
# Include in methods section: "STRING v{version}, accessed {date}"
```

## Key Parameters

| Parameter | Endpoint | Default | Description |
|-----------|----------|---------|-------------|
| `identifiers` | All | — | Protein IDs, `%0d`-separated for URL or `\n`-separated for POST |
| `species` | All | — | NCBI taxon ID (9606=human, 10090=mouse) |
| `required_score` | network, partners, ppi_enrichment | 400 | Confidence threshold 0-1000 |
| `network_type` | network | `functional` | `functional` (all evidence) or `physical` (direct binding) |
| `add_nodes` | network, image | 0 | Additional connected proteins to include (0-10) |
| `limit` | get_string_ids, partners | 1/10 | Max results per query |
| `network_flavor` | image | `evidence` | `evidence`, `confidence`, or `actions` |

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| No proteins found | Wrong species or identifier typo | Verify species taxon ID; use `get_string_ids` to check identifier mapping |
| Empty network | Too strict confidence threshold | Lower `required_score`; verify proteins actually interact in STRING |
| Timeout on large queries | Too many proteins in single request | Split into batches of 50-100; use bulk downloads for proteome-scale |
| "Species required" error | Missing species for >10 protein networks | Always include `species` parameter |
| Unexpected results | Wrong network type or STRING version | Check `network_type` (functional vs physical); verify version with `/version` |
| 400 Bad Request | Malformed identifiers | Use `%0d` separator in URL or `\n` in POST body; URL-encode special characters |
| Enrichment returns no terms | Too few input proteins | Enrichment needs 5+ proteins for meaningful results |

## Best Practices

- **Always map identifiers first** — use `get_string_ids()` before other operations; STRING IDs (e.g., `9606.ENSP00000269305`) are faster than gene names
- **Rate-limit all requests** — add `time.sleep(1)` between API calls
- **Choose appropriate thresholds** — 400 for exploratory analysis, 700 for publications, 900 for high-confidence only
- **Specify species explicitly** — required for networks >10 proteins, recommended always
- **Use functional networks** for pathway analysis and enrichment; **physical networks** for structural biology and direct binding
- **Include version in methods** — check `string_version()` for reproducibility

## Related Skills

- `networkx-graph-analysis` — Graph analysis and visualization of STRING interaction networks
- `kegg-database` — Pathway-centric queries complementary to STRING enrichment
- `bioservices-multi-database` — Alternative access to STRING via the PSICQUIC interface

## References

- STRING website: https://string-db.org
- API documentation: https://string-db.org/help/api/
- Download page: https://string-db.org/cgi/download
- Publications: https://string-db.org/cgi/about

## Bundled Resources

**Main SKILL.md** + 1 reference file. Original total: 990 lines (SKILL.md 534 + string_reference.md 456). Scripts: 370 lines (string_api.py).

**references/api_advanced.md**: Advanced API features (values/ranks enrichment, bulk upload, R/Cytoscape integration), output format details, HTTP error codes, data license — content from original string_reference.md that exceeds Core API scope.

**Original file disposition**:
- `SKILL.md` (534 lines) → Core API modules 1-7, Workflows 1-3, Quick Start helper function, Key Concepts (species table, score thresholds, network types). Promotional section stripped (rule 4). "Common Use Cases" per-operation subsections consolidated into Core API module descriptions (rule 7b): each operation's "When to use" and "Use cases" → Core API intro text. "Detailed Reference" stub section → removed, content consolidated inline
- `references/string_reference.md` (456 lines) → Partially consolidated inline: API endpoints → Core API modules with code blocks; species table → Key Concepts; confidence scores → Key Concepts; identifier format → Key Concepts. Advanced features (values/ranks enrichment, bulk upload), integration examples (R STRINGdb, Cytoscape), output format details, HTTP error codes, data license → migrated to `references/api_advanced.md`
- `scripts/string_api.py` (370 lines) → Helper function pattern absorbed into Quick Start (`string_query` reusable function). Per-function disposition: `string_map_ids` → Core API Module 1; `string_network` → Module 2; `string_network_image` → Module 3; `string_interaction_partners` → Module 4; `string_enrichment` → Module 5; `string_ppi_enrichment` → Module 6; `string_homology` → Module 7; `string_version` → Recipe. All were thin wrappers around urllib; replaced with requests-based `string_query` helper

**Retention**: ~460 lines (SKILL.md) + ~180 lines (reference) = ~640 / 990 original = ~65%.
