---
name: "monarch-database"
description: "Query disease-gene-phenotype associations, entity details, and cross-species orthology from the Monarch Initiative knowledge graph REST API. Retrieve MONDO disease-to-gene and disease-to-phenotype mappings, HP phenotype profiles, and cross-species phenotype comparisons. Use for rare disease gene prioritization, phenotype-based candidate gene ranking, and building disease-phenotype networks. For GWAS associations use gwas-database; for clinical pathogenicity use clinvar-database."
license: "BSD-3-Clause"
---

# monarch-database

## Overview

The Monarch Initiative integrates disease-phenotype-gene relationships from 30+ biomedical databases (OMIM, Orphanet, ClinVar, MGI, ZFIN, Reactome) into a unified knowledge graph. The REST API at `https://api.monarchinitiative.org/v3/api` provides access to associations between genes, diseases, and phenotypes using MONDO disease IDs, Human Phenotype Ontology (HPO) terms, and standard gene identifiers. No authentication is required; the service is free for academic use.

## When to Use

- Mapping a disease (MONDO ID) to all associated causal genes and their evidence sources
- Retrieving phenotype profiles (HP terms) for a disease to build phenotypic similarity models
- Ranking candidate genes by phenotypic similarity to a patient's HPO symptom list
- Querying cross-species gene-phenotype associations (mouse, zebrafish, fly) for model organism comparisons
- Exploring rare disease gene-phenotype networks for diagnostic candidate generation
- Resolving entity metadata (gene symbol, disease name, phenotype label) from a MONDO/HP/HGNC ID
- Use `opentargets-database` instead when you need drug-target evidence scores or tractability data alongside disease associations
- Use `clinvar-database` when you need clinical pathogenicity classifications with submitter review status

## Prerequisites

- **Python packages**: `requests`, `pandas`, `matplotlib`
- **Data requirements**: MONDO IDs (e.g., `MONDO:0007374`), HP term IDs (e.g., `HP:0001250`), or gene symbols/HGNC IDs
- **Environment**: internet connection; no API key required
- **Rate limits**: no published rate limit; use `time.sleep(0.3)` between batch requests; avoid bursts over 10 requests/second

```bash
pip install requests pandas matplotlib
```

## Quick Start

```python
import requests

MONARCH_API = "https://api.monarchinitiative.org/v3/api"

def monarch_get(endpoint: str, params: dict = None) -> dict:
    """GET request to Monarch API; raises on HTTP errors."""
    r = requests.get(f"{MONARCH_API}{endpoint}", params=params, timeout=30)
    r.raise_for_status()
    return r.json()

# Get all genes associated with Marfan syndrome (MONDO:0007374)
result = monarch_get("/association/all", params={
    "subject": "MONDO:0007374",
    "category": "biolink:GeneToDiseaseAssociation",
    "limit": 10
})
print(f"Total gene associations: {result['total']}")
for item in result["items"][:5]:
    obj = item.get("object", {})
    print(f"  Gene: {obj.get('label', 'N/A')}  ({obj.get('id', 'N/A')})")
# Total gene associations: 3
# Gene: FBN1  (HGNC:3603)
```

## Core API

### Query 1: Disease-Gene Associations

Retrieve all genes associated with a disease by MONDO ID. Returns causal gene records with evidence metadata.

```python
import requests
import pandas as pd
import time

MONARCH_API = "https://api.monarchinitiative.org/v3/api"

def monarch_get(endpoint, params=None):
    r = requests.get(f"{MONARCH_API}{endpoint}", params=params, timeout=30)
    r.raise_for_status()
    return r.json()

def get_disease_genes(mondo_id: str, limit: int = 200) -> pd.DataFrame:
    """Return DataFrame of genes associated with a disease."""
    result = monarch_get("/association/all", params={
        "subject": mondo_id,
        "category": "biolink:CausalGeneToDiseaseAssociation",
        "limit": limit
    })
    rows = []
    for item in result.get("items", []):
        obj = item.get("object", {})
        rows.append({
            "gene_id": obj.get("id"),
            "gene_symbol": obj.get("label"),
            "taxon": obj.get("taxon", {}).get("label") if obj.get("taxon") else None,
            "relation": item.get("predicate"),
            "evidence_count": len(item.get("evidence", [])),
        })
    return pd.DataFrame(rows)

# Cystic fibrosis (MONDO:0009861)
df = get_disease_genes("MONDO:0009861")
print(f"Genes for cystic fibrosis: {len(df)}")
print(df[["gene_symbol", "gene_id", "relation"]].to_string(index=False))
# Genes for cystic fibrosis: 1
# gene_symbol  gene_id    relation
#        CFTR  HGNC:1884  biolink:causes
```

### Query 2: Disease-Phenotype Associations

Retrieve HPO phenotype terms linked to a disease. Useful for building phenotype profiles and similarity scoring.

```python
def get_disease_phenotypes(mondo_id: str, limit: int = 200) -> pd.DataFrame:
    """Return DataFrame of phenotypes (HP terms) for a disease."""
    result = monarch_get("/association/all", params={
        "subject": mondo_id,
        "category": "biolink:DiseaseToPhenotypicFeatureAssociation",
        "limit": limit
    })
    rows = []
    for item in result.get("items", []):
        obj = item.get("object", {})
        rows.append({
            "hp_id": obj.get("id"),
            "phenotype": obj.get("label"),
            "frequency": item.get("frequency", {}).get("label") if item.get("frequency") else None,
            "onset": item.get("onset", {}).get("label") if item.get("onset") else None,
        })
    return pd.DataFrame(rows)

# Marfan syndrome (MONDO:0007374)
df = get_disease_phenotypes("MONDO:0007374", limit=50)
print(f"Phenotypes for Marfan syndrome: {len(df)}")
print(df[["phenotype", "hp_id", "frequency"]].head(8).to_string(index=False))
# Phenotypes for Marfan syndrome: 26
# phenotype                      hp_id        frequency
# Aortic root aneurysm        HP:0002616    HP:0040281  ...
```

### Query 3: Entity Lookup

Retrieve metadata for any Monarch entity (gene, disease, phenotype) by its identifier.

```python
def get_entity(entity_id: str) -> dict:
    """Retrieve metadata for a gene, disease, or phenotype by its ID."""
    result = monarch_get(f"/entity/{entity_id}")
    return result

# Look up HP:0001250 (Seizure)
hp = get_entity("HP:0001250")
print(f"Name: {hp.get('name')}")
print(f"ID: {hp.get('id')}")
print(f"Description: {hp.get('description', '')[:120]}")
print(f"Synonyms: {[s.get('val') for s in hp.get('synonyms', [])[:3]]}")
# Name: Seizure
# ID: HP:0001250
# Description: A seizure is an intermittent abnormality of nervous system physiology ...

# Look up a MONDO disease
disease = get_entity("MONDO:0007374")
print(f"\nDisease: {disease.get('name')}")
print(f"ID: {disease.get('id')}")
```

### Query 4: Text Search for Entities

Search for entities by free-text label, useful for resolving disease names or phenotype terms to IDs.

```python
def search_entities(query: str, category: str = None, limit: int = 10) -> list:
    """Search Monarch entities by label/synonym."""
    params = {"q": query, "limit": limit}
    if category:
        params["category"] = category
    result = monarch_get("/search", params=params)
    return result.get("items", [])

# Search for "Ehlers-Danlos" diseases
hits = search_entities("Ehlers-Danlos", category="biolink:Disease", limit=8)
for hit in hits:
    print(f"  {hit.get('id'):<25}  {hit.get('name', 'N/A')}")
# MONDO:0020066              Ehlers-Danlos syndrome
# MONDO:0007522              classical Ehlers-Danlos syndrome
# MONDO:0007528              hypermobile Ehlers-Danlos syndrome
# MONDO:0007523              kyphoscoliotic Ehlers-Danlos syndrome
```

### Query 5: Gene-to-Disease Associations

Retrieve diseases associated with a gene. Useful for understanding a gene's disease spectrum.

```python
def get_gene_diseases(gene_id: str, limit: int = 100) -> pd.DataFrame:
    """Return DataFrame of diseases associated with a gene."""
    result = monarch_get("/association/all", params={
        "subject": gene_id,
        "category": "biolink:GeneToDiseaseAssociation",
        "limit": limit
    })
    rows = []
    for item in result.get("items", []):
        obj = item.get("object", {})
        rows.append({
            "disease_id": obj.get("id"),
            "disease_name": obj.get("label"),
            "predicate": item.get("predicate"),
        })
    return pd.DataFrame(rows)

# Diseases caused by FBN1 (HGNC:3603)
df = get_gene_diseases("HGNC:3603")
print(f"Diseases linked to FBN1: {len(df)}")
print(df[["disease_name", "disease_id"]].head(5).to_string(index=False))
# Diseases linked to FBN1: 8
# disease_name                     disease_id
# Marfan syndrome                  MONDO:0007374
# Stiff skin syndrome              MONDO:0007926
```

### Query 6: Gene-Phenotype Associations (Cross-Species)

Query phenotypes linked to a gene across species including mouse, zebrafish, and human.

```python
def get_gene_phenotypes(gene_id: str, limit: int = 100) -> pd.DataFrame:
    """Return gene-phenotype associations, optionally across species."""
    result = monarch_get("/association/all", params={
        "subject": gene_id,
        "category": "biolink:GeneToPhenotypicFeatureAssociation",
        "limit": limit
    })
    rows = []
    for item in result.get("items", []):
        subj = item.get("subject", {})
        obj = item.get("object", {})
        rows.append({
            "gene_id": subj.get("id"),
            "gene_symbol": subj.get("label"),
            "taxon": subj.get("taxon", {}).get("label") if subj.get("taxon") else None,
            "phenotype_id": obj.get("id"),
            "phenotype": obj.get("label"),
        })
    return pd.DataFrame(rows)

# Phenotypes for human FBN1
df = get_gene_phenotypes("HGNC:3603")
print(f"FBN1 phenotype associations: {len(df)}")
print(df[["taxon", "phenotype"]].value_counts("taxon"))
# Homo sapiens    18
# Mus musculus     6
```

### Query 7: Histopheno — Phenotype Distribution for a Disease

Retrieve summarized phenotype counts by anatomical system for a disease, useful for phenotype spectrum overviews.

```python
def get_histopheno(mondo_id: str) -> dict:
    """Retrieve summarized phenotype distribution for a disease."""
    result = monarch_get(f"/histopheno/{mondo_id}")
    return result

hist = get_histopheno("MONDO:0007374")   # Marfan syndrome
items = hist.get("items", [])
print(f"Phenotype categories for Marfan syndrome ({len(items)} systems):")
for item in sorted(items, key=lambda x: x.get("count", 0), reverse=True)[:8]:
    print(f"  {item.get('label', 'N/A'):<40}  n={item.get('count', 0)}")
# Connective tissue                         n=12
# Cardiovascular system                     n=8
# Eye                                       n=6
```

### Query 8: Phenotype-to-Gene Associations

Given a set of HP phenotype terms, retrieve associated genes — the basis of phenotype-matching tools.

```python
def get_phenotype_genes(hp_id: str, limit: int = 50) -> pd.DataFrame:
    """Return genes associated with a phenotype term."""
    result = monarch_get("/association/all", params={
        "object": hp_id,
        "category": "biolink:GeneToPhenotypicFeatureAssociation",
        "limit": limit
    })
    rows = []
    for item in result.get("items", []):
        subj = item.get("subject", {})
        rows.append({
            "gene_id": subj.get("id"),
            "gene_symbol": subj.get("label"),
            "taxon": subj.get("taxon", {}).get("label") if subj.get("taxon") else None,
        })
    return pd.DataFrame(rows)

# HP:0001631 — Atrial septal defect
df = get_phenotype_genes("HP:0001631")
print(f"Genes associated with Atrial septal defect: {len(df)}")
print(df[df["taxon"] == "Homo sapiens"]["gene_symbol"].head(8).tolist())
# ['TBX5', 'GATA4', 'NKX2-5', 'MYH6', 'ACTC1', ...]
```

## Key Concepts

### Monarch Identifier System

Monarch uses ontology-based compact URIs (CURIEs) as identifiers:

| Prefix | Namespace | Example |
|--------|-----------|---------|
| `MONDO` | Mondo Disease Ontology | `MONDO:0007374` (Marfan syndrome) |
| `HP` | Human Phenotype Ontology | `HP:0001250` (Seizure) |
| `HGNC` | HGNC human genes | `HGNC:3603` (FBN1) |
| `NCBIGene` | NCBI Gene IDs | `NCBIGene:2200` (FBN1) |
| `MGI` | Mouse Genome Informatics | `MGI:95489` (Fbn1 mouse) |
| `ZFIN` | Zebrafish Information Network | `ZFIN:ZDB-GENE-...` |

Use the `/search` endpoint to convert free-text names to IDs before querying associations.

### Association Categories

Monarch uses biolink model categories for associations:

| Category | Meaning |
|----------|---------|
| `biolink:CausalGeneToDiseaseAssociation` | Gene causes the disease |
| `biolink:DiseaseToPhenotypicFeatureAssociation` | Disease → phenotype (HPO terms) |
| `biolink:GeneToPhenotypicFeatureAssociation` | Gene → phenotype (any species) |
| `biolink:GeneToDiseaseAssociation` | Any gene-disease link (broader) |

Use `CausalGeneToDiseaseAssociation` for pathogenic gene lists; use `GeneToDiseaseAssociation` for broader evidence including susceptibility loci.

## Common Workflows

### Workflow 1: Rare Disease Gene Prioritization

**Goal**: Given a set of HPO terms from a patient, retrieve all diseases with overlapping phenotypes and their causal genes.

```python
import requests
import pandas as pd
import time

MONARCH_API = "https://api.monarchinitiative.org/v3/api"

def monarch_get(endpoint, params=None):
    r = requests.get(f"{MONARCH_API}{endpoint}", params=params, timeout=30)
    r.raise_for_status()
    return r.json()

# Patient HPO profile
patient_hp_terms = ["HP:0001250", "HP:0000252", "HP:0001263"]   # Seizure, Microcephaly, DD

gene_scores = {}
for hp_id in patient_hp_terms:
    result = monarch_get("/association/all", params={
        "object": hp_id,
        "category": "biolink:DiseaseToPhenotypicFeatureAssociation",
        "limit": 50
    })
    diseases = [item.get("subject", {}).get("id") for item in result.get("items", [])]
    # For each disease, get causal genes
    for disease_id in diseases[:5]:    # limit per phenotype for demo
        gene_result = monarch_get("/association/all", params={
            "subject": disease_id,
            "category": "biolink:CausalGeneToDiseaseAssociation",
            "limit": 20
        })
        for item in gene_result.get("items", []):
            gene_sym = item.get("object", {}).get("label", "")
            if gene_sym:
                gene_scores[gene_sym] = gene_scores.get(gene_sym, 0) + 1
        time.sleep(0.3)

# Rank genes by co-occurrence with patient phenotypes
df = pd.DataFrame(
    [(gene, score) for gene, score in gene_scores.items()],
    columns=["gene_symbol", "phenotype_overlap_score"]
).sort_values("phenotype_overlap_score", ascending=False)
print(f"Candidate genes ranked by phenotype overlap (n={len(df)})")
print(df.head(10).to_string(index=False))
df.to_csv("candidate_genes_phenotype_ranked.csv", index=False)
```

### Workflow 2: Disease Phenotype Profile and Visualization

**Goal**: Retrieve all HPO terms for a disease, summarize by anatomical category, and plot a bar chart.

```python
import requests
import pandas as pd
import matplotlib.pyplot as plt
import time

MONARCH_API = "https://api.monarchinitiative.org/v3/api"

def monarch_get(endpoint, params=None):
    r = requests.get(f"{MONARCH_API}{endpoint}", params=params, timeout=30)
    r.raise_for_status()
    return r.json()

mondo_id = "MONDO:0009861"   # Cystic fibrosis
disease_info = monarch_get(f"/entity/{mondo_id}")
disease_name = disease_info.get("name", mondo_id)

# Step 1: Get phenotype associations
result = monarch_get("/association/all", params={
    "subject": mondo_id,
    "category": "biolink:DiseaseToPhenotypicFeatureAssociation",
    "limit": 200
})
items = result.get("items", [])
print(f"Phenotypes for {disease_name}: {len(items)}")

# Step 2: Gather HP term labels
rows = []
for item in items:
    obj = item.get("object", {})
    rows.append({
        "hp_id": obj.get("id"),
        "phenotype": obj.get("label"),
        "frequency": item.get("frequency", {}).get("label") if item.get("frequency") else "Unknown"
    })
df = pd.DataFrame(rows)

# Step 3: Histopheno summary for bar chart
hist = monarch_get(f"/histopheno/{mondo_id}")
hist_items = sorted(hist.get("items", []), key=lambda x: x.get("count", 0), reverse=True)[:12]
systems = [x.get("label", "Other")[:25] for x in hist_items]
counts = [x.get("count", 0) for x in hist_items]

fig, ax = plt.subplots(figsize=(10, 5))
bars = ax.barh(systems[::-1], counts[::-1], color="#2196F3")
ax.bar_label(bars, fmt="%d", padding=3)
ax.set_xlabel("Phenotype Count")
ax.set_title(f"Phenotype Distribution by System\n{disease_name} ({mondo_id})")
plt.tight_layout()
plt.savefig("monarch_phenotype_distribution.png", dpi=150, bbox_inches="tight")
print(f"Saved monarch_phenotype_distribution.png ({len(df)} total phenotypes)")

# Step 4: Export HPO terms
df.to_csv(f"{mondo_id.replace(':', '_')}_phenotypes.csv", index=False)
print(df[["hp_id", "phenotype", "frequency"]].head(8).to_string(index=False))
```

### Workflow 3: Cross-Species Gene-Disease Network

**Goal**: Build a table of disease-gene associations including mouse model genes for a list of rare diseases.

```python
import requests
import pandas as pd
import time

MONARCH_API = "https://api.monarchinitiative.org/v3/api"

def monarch_get(endpoint, params=None):
    r = requests.get(f"{MONARCH_API}{endpoint}", params=params, timeout=30)
    r.raise_for_status()
    return r.json()

diseases = {
    "MONDO:0007374": "Marfan syndrome",
    "MONDO:0009861": "Cystic fibrosis",
    "MONDO:0007522": "Classical EDS",
}

all_rows = []
for mondo_id, disease_name in diseases.items():
    # Human causal genes
    result = monarch_get("/association/all", params={
        "subject": mondo_id,
        "category": "biolink:CausalGeneToDiseaseAssociation",
        "limit": 50
    })
    for item in result.get("items", []):
        obj = item.get("object", {})
        all_rows.append({
            "disease_id": mondo_id,
            "disease_name": disease_name,
            "gene_id": obj.get("id"),
            "gene_symbol": obj.get("label"),
            "species": "Homo sapiens",
        })
    time.sleep(0.3)

df = pd.DataFrame(all_rows)
df.to_csv("rare_disease_gene_network.csv", index=False)
print(f"Associations collected: {len(df)}")
print(df.groupby("disease_name")["gene_symbol"].apply(list).to_string())
```

## Key Parameters

| Parameter | Function/Endpoint | Default | Range / Options | Effect |
|-----------|-------------------|---------|-----------------|--------|
| `category` | `/association/all` | (none) | `biolink:CausalGeneToDiseaseAssociation`, `biolink:DiseaseToPhenotypicFeatureAssociation`, `biolink:GeneToPhenotypicFeatureAssociation`, `biolink:GeneToDiseaseAssociation` | Filters association type |
| `subject` | `/association/all` | (none) | CURIE string (e.g., `MONDO:0007374`) | Source entity (disease or gene) |
| `object` | `/association/all` | (none) | CURIE string (e.g., `HP:0001250`) | Target entity (phenotype or disease) |
| `limit` | `/association/all`, `/search` | `20` | `1`–`500` | Max items returned per page |
| `offset` | `/association/all` | `0` | integer | Pagination offset |
| `q` | `/search` | (none) | free-text string | Label/synonym text search |
| `entity_id` | `/entity/{id}` | (none) | CURIE string | Entity ID for metadata lookup |
| `mondo_id` | `/histopheno/{id}` | (none) | MONDO CURIE | Disease ID for phenotype histogram |

## Best Practices

1. **Resolve names to IDs first using `/search`**: All association queries require CURIE IDs (e.g., `MONDO:0007374`), not free-text. Use `search_entities()` to resolve "Marfan syndrome" → `MONDO:0007374` before querying associations.

2. **Use `CausalGeneToDiseaseAssociation` for gene lists, not `GeneToDiseaseAssociation`**: The broader category includes susceptibility associations and ambiguous links. Causal associations have stronger evidence support.

3. **Paginate large result sets with `offset`**: The default `limit` is 20 and max is 500. Check `result["total"]` and paginate with `offset` increments to retrieve all records for diseases with many phenotypes:
   ```python
   total = monarch_get("/association/all", params={"subject": mondo_id, "category": "...", "limit": 1})["total"]
   all_items = []
   for offset in range(0, total, 200):
       batch = monarch_get("/association/all", params={"subject": mondo_id, "category": "...", "limit": 200, "offset": offset})
       all_items.extend(batch.get("items", []))
       time.sleep(0.3)
   ```

4. **Use `time.sleep(0.3)` between requests in batch loops**: The API is publicly accessible without rate limit documentation; polite access avoids throttling for multi-disease workflows.

5. **Cross-reference gene IDs with HGNC for human genes**: Monarch may return `HGNC:XXXX` or `NCBIGene:XXXX` IDs. Use the HGNC prefix for downstream tools that require HGNC; use the `/entity/{id}` endpoint to retrieve the alternative ID.

## Common Recipes

### Recipe: Resolve Disease Name to MONDO ID

When to use: Convert a disease name string to the canonical MONDO identifier before querying.

```python
import requests

MONARCH_API = "https://api.monarchinitiative.org/v3/api"

def resolve_disease(name: str, top_n: int = 5) -> list:
    """Search for disease name and return top MONDO ID candidates."""
    r = requests.get(f"{MONARCH_API}/search",
                     params={"q": name, "category": "biolink:Disease", "limit": top_n},
                     timeout=15)
    r.raise_for_status()
    return [(h.get("id"), h.get("name")) for h in r.json().get("items", [])]

candidates = resolve_disease("Huntington disease")
for mondo_id, label in candidates:
    print(f"  {mondo_id:<25}  {label}")
# MONDO:0007739              Huntington disease
# MONDO:0024321              Huntington disease-like 1
```

### Recipe: Batch Disease-Gene Lookup

When to use: Retrieve causal genes for a list of MONDO IDs in one call each, with results combined into a single DataFrame.

```python
import requests
import pandas as pd
import time

MONARCH_API = "https://api.monarchinitiative.org/v3/api"

def get_causal_genes(mondo_id):
    r = requests.get(f"{MONARCH_API}/association/all",
                     params={"subject": mondo_id,
                             "category": "biolink:CausalGeneToDiseaseAssociation",
                             "limit": 100},
                     timeout=30)
    r.raise_for_status()
    data = r.json()
    return [(item.get("object", {}).get("id"), item.get("object", {}).get("label"))
            for item in data.get("items", [])]

disease_ids = ["MONDO:0007374", "MONDO:0009861", "MONDO:0007739"]
rows = []
for mondo_id in disease_ids:
    for gene_id, gene_sym in get_causal_genes(mondo_id):
        rows.append({"disease_id": mondo_id, "gene_id": gene_id, "gene_symbol": gene_sym})
    time.sleep(0.3)

df = pd.DataFrame(rows)
print(df.to_string(index=False))
df.to_csv("batch_disease_genes.csv", index=False)
print(f"\nTotal disease-gene pairs: {len(df)}")
```

### Recipe: HPO Profile Similarity Seed

When to use: Retrieve disease HPO profiles to use as input seeds for phenotype similarity tools (e.g., Phenomizer, LIRICAL).

```python
import requests, json

MONARCH_API = "https://api.monarchinitiative.org/v3/api"

def get_hp_profile(mondo_id, limit=500):
    """Return list of HP term IDs for a disease."""
    r = requests.get(f"{MONARCH_API}/association/all",
                     params={"subject": mondo_id,
                             "category": "biolink:DiseaseToPhenotypicFeatureAssociation",
                             "limit": limit},
                     timeout=30)
    r.raise_for_status()
    items = r.json().get("items", [])
    return [item.get("object", {}).get("id") for item in items if item.get("object", {}).get("id")]

hp_terms = get_hp_profile("MONDO:0007374")   # Marfan syndrome
print(f"HP terms for Marfan syndrome: {len(hp_terms)}")
print(hp_terms[:8])
# ['HP:0002616', 'HP:0001166', 'HP:0000768', 'HP:0001083', ...]

# Save for downstream phenotype similarity tool input
with open("MONDO_0007374_hp_profile.json", "w") as f:
    json.dump({"disease": "MONDO:0007374", "hpo_terms": hp_terms}, f, indent=2)
print("Saved MONDO_0007374_hp_profile.json")
```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| Empty `items` list | Wrong category string or entity has no associations of that type | Check the category name exactly; try `biolink:GeneToDiseaseAssociation` as a broader fallback |
| `404 Not Found` for `/entity/{id}` | Malformed CURIE or deprecated ID | Verify ID format (e.g., `MONDO:0007374` not `MONDO_0007374`); use `/search` to find current IDs |
| `total` is 0 but entity exists | Subject/object direction reversed | Check whether you need `subject` or `object` parameter; gene→disease uses `subject=gene_id`; disease→phenotype uses `subject=disease_id` |
| `requests.exceptions.Timeout` | API overloaded or network issue | Increase `timeout=60`; retry with exponential backoff |
| Gene ID returned as `NCBIGene` instead of `HGNC` | Monarch may use either namespace | Use `/entity/{id}` to retrieve `xrefs` field for alternative IDs including HGNC, Ensembl |
| Results differ between API calls for same entity | Monarch knowledge graph is updated regularly | Pin your data collection date; note API version in methods section |
| Rate-limited or slow responses | Too many rapid requests | Add `time.sleep(0.5)` between batch requests; use `limit=200` to reduce total requests |

## Related Skills

- `clinvar-database` — clinical pathogenicity classifications for specific variants (complements Monarch's gene-disease associations)
- `gwas-database` — GWAS Catalog associations for common variants and traits
- `opentargets-database` — drug-target evidence with tractability and safety scores
- `ensembl-database` — gene/transcript annotation and cross-species orthology via Ensembl REST API
- `gseapy-gene-enrichment` — gene set enrichment analysis using the Monarch-derived gene lists

## References

- [Monarch Initiative API v3](https://api.monarchinitiative.org/v3/api) — Interactive Swagger/OpenAPI documentation
- [Monarch Initiative](https://monarchinitiative.org/) — Main portal with disease-gene-phenotype knowledge graph browser
- [Mungall et al., Genome Biology 2017](https://doi.org/10.1186/s13059-017-1223-7) — Monarch Integration methodology paper
- [Mondo Disease Ontology](https://mondo.monarchinitiative.org/) — MONDO ID reference and ontology browser
- [Human Phenotype Ontology](https://hpo.jax.org/) — HPO term browser and clinical applications
