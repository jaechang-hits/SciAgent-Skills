---
name: "quickgo-database"
description: "Query EBI QuickGO REST API for GO terms and protein annotations. Fetch term metadata by ID, search by keyword, walk ancestor/descendant hierarchies, download annotations filtered by taxon, evidence code, aspect. Use for GO resolution, ontology traversal, annotation retrieval before enrichment. Use gseapy-gene-enrichment for enrichment; uniprot-protein-database for proteins."
license: "Apache-2.0"
---

# QuickGO Database

## Overview

QuickGO is the EBI's Gene Ontology annotation browser and REST API. It provides programmatic access to the GO ontology (terms, synonyms, hierarchies) and to the manually curated and electronic GO annotations for proteins across all species. The API is free, requires no authentication, and returns JSON responses. All endpoints live under `https://www.ebi.ac.uk/QuickGO/services/`.

## When to Use

- Resolving a GO term ID (e.g., `GO:0006915`) to its name, definition, and aspect (biological_process, molecular_function, cellular_component)
- Retrieving all GO annotations for a UniProt protein, filtered by evidence code and taxon
- Searching GO terms by keyword (e.g., "apoptosis") to find relevant term IDs before enrichment analysis
- Walking the GO DAG upward (ancestors) or downward (descendants) from a specific term
- Getting annotation counts stratified by evidence code or GO aspect for a set of proteins
- Resolving multiple GO IDs in one batch request to avoid looping over individual term lookups
- For enrichment analysis (ORA/GSEA) on a gene list use `gseapy-gene-enrichment`; QuickGO provides the raw annotation data
- For comprehensive protein function annotations in Swiss-Prot format use `uniprot-protein-database`

## Prerequisites

- **Python packages**: `requests`, `pandas`, `matplotlib`
- **Data requirements**: GO term IDs (`GO:XXXXXXX`) or UniProt accessions; taxon IDs (e.g., `9606` for human)
- **Environment**: internet connection; no API key required
- **Rate limits**: no published hard limit; use `time.sleep(1.0)` between requests in batch loops for polite access

```bash
pip install requests pandas matplotlib
```

## Quick Start

```python
import requests
import time

QUICKGO_BASE = "https://www.ebi.ac.uk/QuickGO/services"

def quickgo_get(endpoint: str, params: dict = None) -> dict:
    """Send a GET request to a QuickGO endpoint and return parsed JSON."""
    url = f"{QUICKGO_BASE}/{endpoint}"
    headers = {"Accept": "application/json"}
    r = requests.get(url, params=params, headers=headers, timeout=30)
    r.raise_for_status()
    return r.json()

# Fetch metadata for the apoptotic process GO term
result = quickgo_get("ontology/go/terms/GO:0006915")
term = result["results"][0]
print(f"ID     : {term['id']}")
print(f"Name   : {term['name']}")
print(f"Aspect : {term['aspect']}")
print(f"Def    : {term['definition']['text'][:100]}...")
# ID     : GO:0006915
# Name   : apoptotic process
# Aspect : biological_process
# Def    : A programmed cell death process which begins when a cell receives ...
```

## Core API

### Query 1: GO Term Lookup

Fetch term metadata — name, definition, aspect, synonyms, and is-obsolete status — for one or more GO IDs.

```python
import requests

QUICKGO_BASE = "https://www.ebi.ac.uk/QuickGO/services"

def get_go_term(go_id: str) -> dict:
    """Retrieve metadata for a single GO term by ID."""
    headers = {"Accept": "application/json"}
    r = requests.get(
        f"{QUICKGO_BASE}/ontology/go/terms/{go_id}",
        headers=headers, timeout=30
    )
    r.raise_for_status()
    results = r.json().get("results", [])
    return results[0] if results else {}

term = get_go_term("GO:0005515")
print(f"Name    : {term['name']}")
print(f"Aspect  : {term['aspect']}")
print(f"Obsolete: {term.get('isObsolete', False)}")
print(f"Synonyms: {[s['name'] for s in term.get('synonyms', [])[:3]]}")
# Name    : protein binding
# Aspect  : molecular_function
# Obsolete: False
# Synonyms: ['protein-protein interaction', 'protein binding activity']
```

```python
# Batch lookup: resolve multiple GO IDs in one request
go_ids = ["GO:0006915", "GO:0005515", "GO:0016020"]
ids_param = ",".join(go_ids)
r = requests.get(
    f"{QUICKGO_BASE}/ontology/go/terms/{ids_param}",
    headers={"Accept": "application/json"}, timeout=30
)
r.raise_for_status()
for t in r.json().get("results", []):
    print(f"{t['id']}  {t['aspect']:<25}  {t['name']}")
# GO:0006915  biological_process        apoptotic process
# GO:0005515  molecular_function        protein binding
# GO:0016020  cellular_component        membrane
```

### Query 2: Annotation Search

Retrieve GO annotations for a protein or a set of proteins. Filter by evidence code and taxon.

```python
import requests

QUICKGO_BASE = "https://www.ebi.ac.uk/QuickGO/services"

def get_protein_annotations(uniprot_id: str, evidence_codes: list = None,
                             limit: int = 100) -> list:
    """Fetch GO annotations for a UniProt protein."""
    params = {
        "geneProductId": f"UniProtKB:{uniprot_id}",
        "limit": limit,
        "page": 1,
    }
    if evidence_codes:
        params["evidenceCode"] = ",".join(evidence_codes)
    headers = {"Accept": "application/json"}
    r = requests.get(
        f"{QUICKGO_BASE}/annotation/search",
        params=params, headers=headers, timeout=30
    )
    r.raise_for_status()
    return r.json().get("results", [])

# Fetch experimental annotations for TP53 (P04637)
annotations = get_protein_annotations(
    "P04637",
    evidence_codes=["EXP", "IDA", "IPI", "IMP", "IGI", "IEP"]
)
print(f"Experimental annotations for TP53: {len(annotations)}")
for ann in annotations[:4]:
    print(f"  {ann['goId']}  {ann['goName']:<40}  {ann['evidenceCode']}")
# Experimental annotations for TP53: 87
#   GO:0006977  DNA damage response, ...          IDA
#   GO:0043065  positive regulation of apoptosis  IMP
```

```python
# Annotations for a taxon (human, 9606) + specific GO term
params = {
    "goId": "GO:0006915",
    "taxonId": "9606",
    "evidenceCode": "EXP,IDA,IPI,IMP,IGI,IEP",
    "limit": 100,
    "page": 1,
}
r = requests.get(
    f"{QUICKGO_BASE}/annotation/search",
    params=params,
    headers={"Accept": "application/json"},
    timeout=30
)
r.raise_for_status()
data = r.json()
print(f"Total annotations: {data.get('numberOfHits', 'N/A')}")
print(f"Retrieved         : {len(data.get('results', []))}")
for ann in data["results"][:3]:
    print(f"  {ann['geneProductId']}  {ann['goId']}  {ann['evidenceCode']}")
```

### Query 3: Term Hierarchy

Get ancestors (terms more general than the query term) or descendants (more specific terms) by traversing the GO DAG.

```python
import requests

QUICKGO_BASE = "https://www.ebi.ac.uk/QuickGO/services"

def get_ancestors(go_id: str, relations: str = "is_a,part_of") -> list:
    """Return ancestor GO IDs for a term via the ontology hierarchy."""
    r = requests.get(
        f"{QUICKGO_BASE}/ontology/go/terms/{go_id}/ancestors",
        params={"relations": relations},
        headers={"Accept": "application/json"},
        timeout=30
    )
    r.raise_for_status()
    results = r.json().get("results", [])
    return results[0].get("ancestors", []) if results else []

def get_descendants(go_id: str, relations: str = "is_a,part_of") -> list:
    """Return descendant GO IDs for a term via the ontology hierarchy."""
    r = requests.get(
        f"{QUICKGO_BASE}/ontology/go/terms/{go_id}/descendants",
        params={"relations": relations},
        headers={"Accept": "application/json"},
        timeout=30
    )
    r.raise_for_status()
    results = r.json().get("results", [])
    return results[0].get("descendants", []) if results else []

ancestors = get_ancestors("GO:0006915")
descendants = get_descendants("GO:0006915")
print(f"Ancestors  of GO:0006915 (apoptotic process): {len(ancestors)}")
print(f"Descendants of GO:0006915                    : {len(descendants)}")
print(f"First 5 ancestors : {ancestors[:5]}")
# Ancestors  of GO:0006915 (apoptotic process): 6
# Descendants of GO:0006915                    : 53
# First 5 ancestors : ['GO:0008219', 'GO:0009987', ...]
```

### Query 4: Ontology Search

Text-search for GO terms by keyword. Useful for discovering relevant GO IDs before building annotation queries.

```python
import requests

QUICKGO_BASE = "https://www.ebi.ac.uk/QuickGO/services"

def search_go_terms(query: str, limit: int = 20) -> list:
    """Search GO terms by keyword; returns list of term dicts."""
    r = requests.get(
        f"{QUICKGO_BASE}/ontology/go/search",
        params={"query": query, "limit": limit, "page": 1},
        headers={"Accept": "application/json"},
        timeout=30
    )
    r.raise_for_status()
    return r.json().get("results", [])

hits = search_go_terms("autophagy")
print(f"GO terms matching 'autophagy': {len(hits)}")
for h in hits[:5]:
    print(f"  {h['id']}  {h['aspect']:<25}  {h['name']}")
# GO terms matching 'autophagy': 20
#   GO:0006914  biological_process        autophagy
#   GO:0016236  biological_process        macroautophagy
#   GO:0061709  biological_process        reticulophagy
```

### Query 5: Annotation Statistics

Get counts of annotations grouped by evidence code, GO aspect, or taxon for a gene product or GO term.

```python
import requests

QUICKGO_BASE = "https://www.ebi.ac.uk/QuickGO/services"

def get_annotation_stats(uniprot_id: str) -> dict:
    """Retrieve annotation counts by evidence type and GO aspect."""
    params = {
        "geneProductId": f"UniProtKB:{uniprot_id}",
        "limit": 200,
        "page": 1,
    }
    r = requests.get(
        f"{QUICKGO_BASE}/annotation/search",
        params=params,
        headers={"Accept": "application/json"},
        timeout=30
    )
    r.raise_for_status()
    results = r.json().get("results", [])
    by_evidence = {}
    by_aspect = {}
    for ann in results:
        ec = ann.get("evidenceCode", "unknown")
        asp = ann.get("goAspect", "unknown")
        by_evidence[ec] = by_evidence.get(ec, 0) + 1
        by_aspect[asp] = by_aspect.get(asp, 0) + 1
    return {"by_evidence": by_evidence, "by_aspect": by_aspect,
            "total": len(results)}

stats = get_annotation_stats("P04637")   # TP53
print(f"Total annotations (first page): {stats['total']}")
print("\nBy evidence code:")
for ec, n in sorted(stats["by_evidence"].items(), key=lambda x: -x[1]):
    print(f"  {ec:<5} : {n}")
print("\nBy GO aspect:")
for asp, n in stats["by_aspect"].items():
    print(f"  {asp}: {n}")
```

### Query 6: Batch GO Term Query

Resolve a list of GO IDs to their names and aspects in a single API call (up to ~200 IDs per request).

```python
import requests

QUICKGO_BASE = "https://www.ebi.ac.uk/QuickGO/services"

def batch_resolve_go_terms(go_ids: list) -> dict:
    """Resolve a list of GO IDs → {id: {name, aspect, definition}} in one call."""
    ids_param = ",".join(go_ids)
    r = requests.get(
        f"{QUICKGO_BASE}/ontology/go/terms/{ids_param}",
        headers={"Accept": "application/json"},
        timeout=60
    )
    r.raise_for_status()
    return {
        t["id"]: {
            "name": t["name"],
            "aspect": t["aspect"],
            "definition": t.get("definition", {}).get("text", ""),
            "obsolete": t.get("isObsolete", False),
        }
        for t in r.json().get("results", [])
    }

go_ids = ["GO:0006915", "GO:0005515", "GO:0016020", "GO:0006281", "GO:0051301"]
resolved = batch_resolve_go_terms(go_ids)
print(f"Resolved {len(resolved)}/{len(go_ids)} GO IDs")
for gid, info in resolved.items():
    print(f"  {gid}  [{info['aspect'][:2].upper()}]  {info['name']}")
# Resolved 5/5 GO IDs
#   GO:0006915  [BI]  apoptotic process
#   GO:0005515  [MO]  protein binding
#   GO:0016020  [CE]  membrane
```

## Key Concepts

### GO Ontology Structure

The Gene Ontology is a directed acyclic graph (DAG) organized into three independent root aspects:

| Aspect code | Aspect name | Root term |
|-------------|-------------|-----------|
| `biological_process` | Biological process (BP) | GO:0008150 |
| `molecular_function` | Molecular function (MF) | GO:0003674 |
| `cellular_component` | Cellular component (CC) | GO:0005575 |

Terms are connected by two primary relation types: `is_a` (subclass) and `part_of` (mereological). When filtering annotation enrichment results, always check the `aspect` field to avoid mixing BP, MF, and CC terms.

### Evidence Code Categories

The evidence code determines annotation reliability. Filter to experimental codes for high-confidence annotations; exclude `IEA` in clinical or mechanistic analyses.

| Category | Codes | Meaning |
|----------|-------|---------|
| Experimental | EXP, IDA, IPI, IMP, IGI, IEP | Direct biochemical or genetic experiments |
| Computational/similarity | ISS, ISO, ISA, IBA, RCA | Inferred by sequence or phylogenetic similarity |
| Author statement | TAS, IC | Curator or author assertion without experiment |
| Electronic | IEA | Automated; no human review — lowest confidence |
| High throughput | HTP, HDA, HMP, HGI, HEP | High-throughput experimental methods |

### Pagination

QuickGO annotation searches return paginated results. The `numberOfHits` field in the response gives the total count. Use the `page` parameter to iterate through all results when `numberOfHits > limit`.

```python
import requests, time

def get_all_annotations(go_id: str, taxon_id: str = "9606",
                         evidence_codes: str = "EXP,IDA,IPI,IMP",
                         page_size: int = 100) -> list:
    """Retrieve all annotation pages for a GO term + taxon combination."""
    QUICKGO_BASE = "https://www.ebi.ac.uk/QuickGO/services"
    all_results = []
    page = 1
    while True:
        params = {"goId": go_id, "taxonId": taxon_id,
                  "evidenceCode": evidence_codes, "limit": page_size,
                  "page": page}
        r = requests.get(f"{QUICKGO_BASE}/annotation/search",
                         params=params, headers={"Accept": "application/json"},
                         timeout=30)
        r.raise_for_status()
        data = r.json()
        results = data.get("results", [])
        all_results.extend(results)
        total = data.get("numberOfHits", 0)
        if len(all_results) >= total or not results:
            break
        page += 1
        time.sleep(1.0)   # polite delay
    return all_results
```

## Common Workflows

### Workflow 1: GO Annotation Profile for a Protein

**Goal**: Retrieve all GO annotations for a protein, split by aspect and evidence category, and visualize the evidence code distribution.

```python
import requests, time
import pandas as pd
import matplotlib.pyplot as plt

QUICKGO_BASE = "https://www.ebi.ac.uk/QuickGO/services"

def get_all_annotations_for_protein(uniprot_id: str, page_size: int = 200) -> list:
    all_results = []
    page = 1
    while True:
        params = {"geneProductId": f"UniProtKB:{uniprot_id}",
                  "limit": page_size, "page": page}
        r = requests.get(f"{QUICKGO_BASE}/annotation/search",
                         params=params, headers={"Accept": "application/json"},
                         timeout=30)
        r.raise_for_status()
        data = r.json()
        results = data.get("results", [])
        all_results.extend(results)
        if len(all_results) >= data.get("numberOfHits", 0) or not results:
            break
        page += 1
        time.sleep(1.0)
    return all_results

UNIPROT_ID = "P04637"   # TP53 human
annotations = get_all_annotations_for_protein(UNIPROT_ID)
print(f"Total annotations for {UNIPROT_ID}: {len(annotations)}")

df = pd.DataFrame([{
    "goId": a["goId"],
    "goName": a.get("goName", ""),
    "aspect": a.get("goAspect", ""),
    "evidenceCode": a.get("evidenceCode", ""),
    "reference": a.get("reference", ""),
    "assignedBy": a.get("assignedBy", ""),
} for a in annotations])

# Evidence code distribution bar chart
ec_counts = df["evidenceCode"].value_counts()
fig, ax = plt.subplots(figsize=(9, 4))
bars = ax.bar(ec_counts.index, ec_counts.values, color="#2171B5", edgecolor="white")
ax.bar_label(bars, fontsize=8, padding=2)
ax.set_xlabel("Evidence Code")
ax.set_ylabel("Annotation Count")
ax.set_title(f"GO Annotation Evidence Codes — {UNIPROT_ID} (TP53)")
plt.tight_layout()
plt.savefig(f"{UNIPROT_ID}_evidence_codes.png", dpi=150, bbox_inches="tight")
print(f"Saved {UNIPROT_ID}_evidence_codes.png")
print(df.groupby(["aspect", "evidenceCode"]).size().to_string())
```

### Workflow 2: Ontology-Aware Annotation Retrieval

**Goal**: For a GO term of interest, find all descendant terms and then retrieve annotations for all of them combined — capturing the full semantic scope.

```python
import requests, time, pandas as pd

QUICKGO_BASE = "https://www.ebi.ac.uk/QuickGO/services"

def quickgo_get(endpoint, params=None):
    r = requests.get(f"{QUICKGO_BASE}/{endpoint}",
                     params=params, headers={"Accept": "application/json"},
                     timeout=30)
    r.raise_for_status()
    return r.json()

# Step 1: Get all descendants of "cell death" (GO:0008219)
parent_go_id = "GO:0008219"
desc_data = quickgo_get(f"ontology/go/terms/{parent_go_id}/descendants",
                         params={"relations": "is_a,part_of"})
descendants = desc_data["results"][0]["descendants"] if desc_data["results"] else []
all_ids = [parent_go_id] + descendants
print(f"GO terms in '{parent_go_id}' subtree: {len(all_ids)}")

# Step 2: Batch-resolve term names (chunk to ≤ 100 per request)
resolved = {}
chunk_size = 100
for i in range(0, len(all_ids), chunk_size):
    chunk = all_ids[i:i + chunk_size]
    data = quickgo_get(f"ontology/go/terms/{','.join(chunk)}")
    for t in data.get("results", []):
        resolved[t["id"]] = t["name"]
    time.sleep(1.0)
print(f"Resolved {len(resolved)} term names")

# Step 3: Fetch experimental annotations for human for all descendant terms
rows = []
for go_id in all_ids[:10]:   # limit for demo; remove slice for full run
    params = {"goId": go_id, "taxonId": "9606",
              "evidenceCode": "EXP,IDA,IPI,IMP,IGI,IEP",
              "limit": 100, "page": 1}
    data = quickgo_get("annotation/search", params=params)
    for ann in data.get("results", []):
        rows.append({
            "query_go_id": go_id,
            "query_go_name": resolved.get(go_id, ""),
            "protein": ann["geneProductId"],
            "evidence": ann["evidenceCode"],
        })
    time.sleep(1.0)

df = pd.DataFrame(rows)
df.to_csv("cell_death_annotations.csv", index=False)
print(f"Saved {len(df)} annotation rows → cell_death_annotations.csv")
```

### Workflow 3: Cross-Protein GO Term Comparison

**Goal**: Compare GO term coverage across a list of proteins and export a presence/absence matrix.

```python
import requests, time, pandas as pd

QUICKGO_BASE = "https://www.ebi.ac.uk/QuickGO/services"

proteins = {
    "TP53": "P04637",
    "BRCA1": "P38398",
    "MDM2": "Q00987",
    "BCL2": "P10415",
}

records = {}
for gene, uniprot_id in proteins.items():
    params = {"geneProductId": f"UniProtKB:{uniprot_id}",
              "evidenceCode": "EXP,IDA,IPI,IMP,IGI,IEP",
              "limit": 200, "page": 1}
    r = requests.get(f"{QUICKGO_BASE}/annotation/search",
                     params=params, headers={"Accept": "application/json"},
                     timeout=30)
    r.raise_for_status()
    go_ids = {ann["goId"] for ann in r.json().get("results", [])}
    records[gene] = go_ids
    print(f"{gene}: {len(go_ids)} experimental GO annotations")
    time.sleep(1.0)

# Build presence/absence matrix
all_terms = sorted(set().union(*records.values()))
matrix = pd.DataFrame(
    {gene: [1 if t in s else 0 for t in all_terms] for gene, s in records.items()},
    index=all_terms
)
shared = matrix[matrix.sum(axis=1) == len(proteins)]
print(f"\nGO terms shared by all {len(proteins)} proteins: {len(shared)}")
print(shared.index.tolist()[:10])
matrix.to_csv("protein_go_matrix.csv")
print(f"Saved protein_go_matrix.csv ({matrix.shape[0]} GO terms)")
```

## Key Parameters

| Parameter | Endpoint | Default | Range / Options | Effect |
|-----------|----------|---------|-----------------|--------|
| `goId` | `annotation/search` | — | `GO:XXXXXXX` | Filter annotations to a specific GO term |
| `geneProductId` | `annotation/search` | — | `UniProtKB:ACCESSION` | Filter to a specific protein |
| `taxonId` | `annotation/search` | — | NCBI taxon integer (e.g., `9606`) | Filter annotations by species |
| `evidenceCode` | `annotation/search` | — | Comma-separated codes, e.g., `EXP,IDA` | Filter by annotation evidence type |
| `goAspect` | `annotation/search` | — | `biological_process`, `molecular_function`, `cellular_component` | Filter by ontology namespace |
| `relations` | `terms/{id}/ancestors`, `terms/{id}/descendants` | `is_a` | `is_a`, `part_of`, `occurs_in`, `regulates` | Relation types for hierarchy traversal |
| `limit` | `annotation/search`, `ontology/go/search` | `25` | `1`–`200` | Results per page |
| `page` | `annotation/search`, `ontology/go/search` | `1` | positive integer | Pagination control |
| `query` | `ontology/go/search` | — | free-text string | Keyword search across GO term names and definitions |

## Best Practices

1. **Use `batch_resolve_go_terms` instead of per-ID loops**: The terms endpoint accepts a comma-separated list of IDs and resolves all in one round trip. For lists of up to 200 IDs this is 100× faster than one request per term.

2. **Exclude IEA for mechanistic conclusions**: Electronic annotations (`IEA`) are assigned by automated pipelines without manual review. They can inflate annotation counts and introduce false positives. Set `evidenceCode=EXP,IDA,IPI,IMP,IGI,IEP,TAS` for curated-only results.

3. **Add `time.sleep(1.0)` in batch loops**: QuickGO is shared EBI infrastructure with no published hard limit. One request per second keeps your scripts well within fair-use bounds.

4. **Use descendants for ontology-aware queries**: Searching only the exact `goId` misses proteins annotated to more specific child terms. Retrieve descendants first, then query each or combine into an `evidenceCode`-filtered batch.

5. **Check `numberOfHits` before assuming completeness**: The default `limit=25` often returns a fraction of total annotations. Always inspect `numberOfHits` and paginate when `numberOfHits > limit`.

## Common Recipes

### Recipe: Resolve GO IDs from an Enrichment Result

When to use: Convert a list of GO IDs returned by gseapy or another enrichment tool to human-readable names.

```python
import requests

QUICKGO_BASE = "https://www.ebi.ac.uk/QuickGO/services"

def resolve_go_names(go_ids: list) -> dict:
    """Return {go_id: name} for a list of GO IDs (single batch call)."""
    ids_str = ",".join(go_ids)
    r = requests.get(
        f"{QUICKGO_BASE}/ontology/go/terms/{ids_str}",
        headers={"Accept": "application/json"}, timeout=60
    )
    r.raise_for_status()
    return {t["id"]: t["name"] for t in r.json().get("results", [])}

# Example: map enrichment result GO IDs
enriched_ids = ["GO:0006915", "GO:0043066", "GO:0097553", "GO:0008219", "GO:0006281"]
names = resolve_go_names(enriched_ids)
for gid, name in names.items():
    print(f"{gid}  {name}")
# GO:0006915  apoptotic process
# GO:0043066  negative regulation of apoptotic process
```

### Recipe: Get All Experimental Annotations for a Human Protein

When to use: Pull curated evidence for a protein before manually reviewing its GO function landscape.

```python
import requests, time

QUICKGO_BASE = "https://www.ebi.ac.uk/QuickGO/services"
EXP_CODES = "EXP,IDA,IPI,IMP,IGI,IEP"

def get_experimental_annotations(uniprot_id: str) -> list:
    results, page = [], 1
    while True:
        r = requests.get(
            f"{QUICKGO_BASE}/annotation/search",
            params={"geneProductId": f"UniProtKB:{uniprot_id}",
                    "evidenceCode": EXP_CODES,
                    "limit": 200, "page": page},
            headers={"Accept": "application/json"}, timeout=30
        )
        r.raise_for_status()
        data = r.json()
        batch = data.get("results", [])
        results.extend(batch)
        if not batch or len(results) >= data.get("numberOfHits", 0):
            break
        page += 1
        time.sleep(1.0)
    return results

anns = get_experimental_annotations("P04637")   # TP53
print(f"Experimental GO annotations for TP53: {len(anns)}")
for a in anns[:5]:
    print(f"  {a['goId']}  {a.get('goName', '')[:40]}  ({a['evidenceCode']})")
```

### Recipe: Check if a GO Term Is Experimental or Inferred

When to use: Quickly decide whether an annotation is trustworthy before including it in a pathway model.

```python
import requests

QUICKGO_BASE = "https://www.ebi.ac.uk/QuickGO/services"

EXPERIMENTAL = {"EXP", "IDA", "IPI", "IMP", "IGI", "IEP",
                "HTP", "HDA", "HMP", "HGI", "HEP"}

def annotation_is_experimental(uniprot_id: str, go_id: str) -> bool:
    """Return True if any experimental annotation exists for protein + GO term."""
    r = requests.get(
        f"{QUICKGO_BASE}/annotation/search",
        params={"geneProductId": f"UniProtKB:{uniprot_id}",
                "goId": go_id, "limit": 10, "page": 1},
        headers={"Accept": "application/json"}, timeout=30
    )
    r.raise_for_status()
    return any(a["evidenceCode"] in EXPERIMENTAL
               for a in r.json().get("results", []))

print(annotation_is_experimental("P04637", "GO:0006977"))   # True
print(annotation_is_experimental("P04637", "GO:0016020"))   # False (membrane — IEA only)
```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `HTTP 400` on term lookup | Malformed GO ID (spaces, wrong prefix) | Ensure format is `GO:XXXXXXX` (7 digits, colon, uppercase GO) |
| `results: []` for a known GO ID | Term is obsolete or merged into another | Check `isObsolete` field; look up the replacement in `consider` or `replacedBy` |
| Annotation search returns 0 hits for a protein | UniProt accession format wrong | Prefix with `UniProtKB:` (case-sensitive), e.g., `UniProtKB:P04637` |
| `numberOfHits` >> `len(results)` | Default `limit=25` is too small | Set `limit=200` and implement pagination with `page` parameter |
| Batch term resolve returns fewer than expected | Some IDs are obsolete or malformed | Check returned `id` set against input; missing IDs are invalid or obsolete |
| Rate limit / `503 Service Unavailable` | Too many rapid requests | Add `time.sleep(1.0)` between paged calls; backoff on `5xx` errors |
| Descendant list is very large (1000+) | Broad root term selected | Use a more specific child term, or process descendants in chunks of 100 |

## Related Skills

- `gseapy-gene-enrichment` — ORA and GSEA enrichment analysis against GO and other gene set databases; use QuickGO to resolve term IDs from gseapy output
- `uniprot-protein-database` — UniProt REST API for Swiss-Prot GO annotations integrated with protein sequence and feature data
- `ensembl-database` — Ensembl REST API for variant-level GO annotations and cross-species gene lookups
- `kegg-database` — KEGG pathways as an alternative functional annotation vocabulary

## References

- [QuickGO API documentation](https://www.ebi.ac.uk/QuickGO/api/index.html) — Full Swagger/OpenAPI endpoint reference
- [Binns et al., Bioinformatics 2009](https://doi.org/10.1093/bioinformatics/btp536) — QuickGO: a web-based tool for Gene Ontology searching
- [Gene Ontology Consortium](https://geneontology.org/) — GO evidence codes, ontology files, and annotation downloads
- [Ashburner et al., Nature Genetics 2000](https://doi.org/10.1038/75556) — Original Gene Ontology paper
