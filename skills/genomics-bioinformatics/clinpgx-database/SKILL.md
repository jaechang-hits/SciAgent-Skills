---
name: "clinpgx-database"
description: "Query PharmGKB (Clinical Pharmacogenomics) database via REST API for drug-gene interactions, clinical annotations, dosing guidelines (CPIC, DPWG), variant-drug associations, and pharmacogenomic pathways. Search by gene, drug, rsID, or pathway. No authentication required. For somatic cancer pharmacogenomics use cosmic-database or opentargets-database; for drug structures use chembl-database-bioactivity."
license: "CC-BY-SA-4.0"
---

# PharmGKB Clinical Pharmacogenomics Database

## Overview

PharmGKB is the leading pharmacogenomics knowledge resource, curating how genetic variation affects drug response. It integrates CPIC (Clinical Pharmacogenomics Implementation Consortium) and DPWG (Dutch Pharmacogenomics Working Group) dosing guidelines, clinical annotations of variant-drug associations, gene-drug pathways, and literature evidence. The REST API provides free programmatic access without authentication to 24,000+ variant-drug annotations, 800+ clinical annotations, and 300+ CPIC guidelines.

## When to Use

- Retrieving CPIC/DPWG clinical dosing guidelines for a specific gene-drug pair (e.g., CYP2C19-clopidogrel)
- Looking up all pharmacogenomic variants associated with a drug's response or toxicity
- Finding all drugs whose dosing is affected by variants in a pharmacogene (e.g., CYP2D6, DPYD)
- Retrieving PharmGKB clinical annotation levels (1A, 1B, 2A, 2B, 3, 4) for a variant-drug association
- Building precision medicine dosing workflows that incorporate genotype-guided prescribing
- Fetching pharmacogenomic pathways (e.g., warfarin pharmacokinetics/pharmacodynamics) with gene roles
- For cancer somatic pharmacogenomics use `cosmic-database` or `opentargets-database`

## Prerequisites

- **Python packages**: `requests`, `pandas`
- **Data requirements**: gene symbols (HGNC), drug names, dbSNP rsIDs, or PharmGKB IDs
- **Environment**: internet connection; no authentication required
- **Rate limits**: no stated limit; use reasonable delays (~0.2s) for bulk queries

```bash
pip install requests pandas
```

## Quick Start

```python
import requests

BASE = "https://api.pharmgkb.org/v1"

# Search for clinical annotations for CYP2D6
r = requests.get(f"{BASE}/clinicalAnnotation",
                 params={"gene": "CYP2D6", "view": "base"})
r.raise_for_status()
data = r.json()
print(f"CYP2D6 clinical annotations: {data['count']}")
for ann in data["data"][:3]:
    print(f"  Level {ann.get('evidenceLevel')}: {ann.get('drug', {}).get('name')} | {ann.get('phenotype')}")
```

## Core API

### Query 1: Clinical Annotations by Gene or Drug

Retrieve variant-drug clinical annotations with evidence levels.

```python
import requests, pandas as pd

BASE = "https://api.pharmgkb.org/v1"

def get_clinical_annotations(gene=None, drug=None, level=None):
    params = {"view": "base"}
    if gene:
        params["gene"] = gene
    if drug:
        params["drug"] = drug
    if level:
        params["level"] = level
    r = requests.get(f"{BASE}/clinicalAnnotation", params=params)
    r.raise_for_status()
    return r.json()

# All 1A annotations (highest evidence) for warfarin
data = get_clinical_annotations(drug="warfarin", level="1A")
print(f"Warfarin 1A annotations: {data['count']}")

rows = []
for ann in data["data"][:10]:
    rows.append({
        "gene": ann.get("gene", {}).get("symbol"),
        "variant": ann.get("variant", {}).get("name"),
        "drug": ann.get("drug", {}).get("name"),
        "level": ann.get("evidenceLevel"),
        "phenotype": ann.get("phenotype"),
        "significance": ann.get("clinicalSignificance"),
    })
df = pd.DataFrame(rows)
print(df.to_string(index=False))
```

```python
# By rsID
def get_annotations_by_variant(rsid):
    r = requests.get(f"{BASE}/clinicalAnnotation",
                     params={"variant": rsid, "view": "base"})
    r.raise_for_status()
    return r.json()

data_rs = get_annotations_by_variant("rs4149056")  # SLCO1B1 variant for statin myopathy
print(f"\nrs4149056 annotations: {data_rs['count']}")
for ann in data_rs["data"][:5]:
    print(f"  Drug: {ann.get('drug', {}).get('name'):20s} Level: {ann.get('evidenceLevel')}")
```

### Query 2: CPIC/DPWG Dosing Guidelines

Retrieve clinical dosing guideline recommendations for gene-drug pairs.

```python
import requests, pandas as pd

BASE = "https://api.pharmgkb.org/v1"

def get_guidelines(gene=None, drug=None):
    params = {"view": "base"}
    if gene:
        params["gene"] = gene
    if drug:
        params["drug"] = drug
    r = requests.get(f"{BASE}/guideline", params=params)
    r.raise_for_status()
    return r.json()

# Guidelines for CYP2C19 gene (clopidogrel, SSRIs, PPIs)
data = get_guidelines(gene="CYP2C19")
print(f"CYP2C19 dosing guidelines: {data['count']}")

for gl in data["data"][:5]:
    source = gl.get("source", "")
    name = gl.get("name", "")
    url = gl.get("url", "")
    print(f"\n  [{source}] {name}")
    print(f"  URL: {url}")
```

```python
# Guidelines for a specific drug
data_drug = get_guidelines(drug="clopidogrel")
print(f"\nClopidogrel guidelines: {data_drug['count']}")
for gl in data_drug["data"]:
    print(f"  {gl.get('source')}: {gl.get('name')}")
```

### Query 3: Gene Information and Related Drugs

Retrieve pharmacogene information and all associated drugs.

```python
import requests, pandas as pd

BASE = "https://api.pharmgkb.org/v1"

def get_gene_info(gene_symbol):
    r = requests.get(f"{BASE}/gene", params={"symbol": gene_symbol, "view": "max"})
    r.raise_for_status()
    return r.json()

data = get_gene_info("CYP2D6")
gene = data["data"][0] if data["data"] else {}

print(f"Gene: {gene.get('symbol')}")
print(f"PharmGKB ID: {gene.get('id')}")
print(f"Name: {gene.get('name')}")
print(f"CPIC gene: {gene.get('cpicGene', False)}")
print(f"VIP gene: {gene.get('vip', False)}")
print(f"Description: {str(gene.get('summaries', [{}])[0].get('html', ''))[:200]}")
```

```python
# Drug relationships for a gene
def get_gene_drug_relationships(gene_symbol):
    r = requests.get(f"{BASE}/drugLabel",
                     params={"gene": gene_symbol, "view": "base"})
    r.raise_for_status()
    return r.json()

data_labels = get_gene_drug_relationships("CYP2D6")
print(f"\nCYP2D6 drug label annotations: {data_labels['count']}")
for dl in data_labels["data"][:5]:
    print(f"  {dl.get('drug', {}).get('name'):25s} Source: {dl.get('source')}")
```

### Query 4: PharmGKB Pathways

Retrieve pharmacogenomic pathways with gene roles.

```python
import requests, pandas as pd

BASE = "https://api.pharmgkb.org/v1"

def get_pathways(drug=None, gene=None):
    params = {"view": "base"}
    if drug:
        params["drug"] = drug
    if gene:
        params["gene"] = gene
    r = requests.get(f"{BASE}/pathway", params=params)
    r.raise_for_status()
    return r.json()

# Warfarin pharmacogenomic pathway
data = get_pathways(drug="warfarin")
print(f"Warfarin pathways: {data['count']}")
for pw in data["data"][:3]:
    print(f"\n  Pathway: {pw.get('name')}")
    print(f"  Type: {pw.get('type')}")
    print(f"  PharmGKB ID: {pw.get('id')}")
```

### Query 5: Drug Label Annotations (FDA/EMA)

Retrieve FDA and EMA drug label pharmacogenomic annotations.

```python
import requests, pandas as pd

BASE = "https://api.pharmgkb.org/v1"

def get_drug_labels(drug=None, gene=None, source=None):
    params = {"view": "base"}
    if drug:
        params["drug"] = drug
    if gene:
        params["gene"] = gene
    if source:
        params["source"] = source  # "FDA", "EMA", "HCSC", etc.
    r = requests.get(f"{BASE}/drugLabel", params=params)
    r.raise_for_status()
    return r.json()

# FDA labels mentioning TPMT
data = get_drug_labels(gene="TPMT", source="FDA")
print(f"FDA drug labels with TPMT: {data['count']}")

rows = []
for dl in data["data"][:10]:
    rows.append({
        "drug": dl.get("drug", {}).get("name"),
        "source": dl.get("source"),
        "pgx_level": dl.get("pgxLevel"),
        "testing_required": dl.get("testingRequired"),
    })
df = pd.DataFrame(rows)
print(df.to_string(index=False))
```

### Query 6: Variant Drug Associations

Retrieve all associations for a specific genetic variant.

```python
import requests, pandas as pd

BASE = "https://api.pharmgkb.org/v1"

def search_variant(rsid):
    """Look up a variant by rsID and get all associations."""
    # First find the variant record
    r = requests.get(f"{BASE}/variant", params={"name": rsid, "view": "base"})
    r.raise_for_status()
    return r.json()

# VKORC1 variant (warfarin dose)
data = search_variant("rs9923231")
print(f"rs9923231 records: {data['count']}")

if data["data"]:
    v = data["data"][0]
    print(f"  Variant: {v.get('name')}")
    print(f"  PharmGKB ID: {v.get('id')}")

# Get clinical annotations for this variant
r2 = requests.get(f"{BASE}/clinicalAnnotation",
                  params={"variant": "rs9923231", "view": "base"})
anns = r2.json()
print(f"  Clinical annotations: {anns['count']}")
for ann in anns["data"][:5]:
    print(f"    Drug: {ann.get('drug', {}).get('name'):15s} Level: {ann.get('evidenceLevel')} | {ann.get('phenotype')}")
```

## Key Concepts

### PharmGKB Evidence Levels

Clinical annotation levels range from 1A (highest evidence: multiple clinical guideline associations) to 4 (case reports, biological plausibility only):
- **1A/1B**: CPIC/DPWG guideline-level evidence
- **2A/2B**: Replicated or single study with moderate evidence
- **3**: Limited evidence (single study or case reports)
- **4**: Case reports only

### CPIC vs. DPWG Guidelines

CPIC (US-based) and DPWG (Netherlands-based) are the two primary bodies issuing genotype-based prescribing guidelines. Both are integrated in PharmGKB. CPIC focuses on actionable guidelines when PGx testing is already done; DPWG guidelines inform clinical decisions in the Netherlands.

## Common Workflows

### Workflow 1: Pharmacogene Drug Interaction Summary

**Goal**: For a patient's pharmacogene panel, retrieve all actionable drug-gene interactions with evidence levels.

```python
import requests, pandas as pd, time

BASE = "https://api.pharmgkb.org/v1"

# Patient's relevant pharmacogenes
pharmacogenes = ["CYP2D6", "CYP2C19", "CYP2C9", "DPYD", "TPMT", "SLCO1B1"]

rows = []
for gene in pharmacogenes:
    r = requests.get(f"{BASE}/clinicalAnnotation",
                     params={"gene": gene, "level": "1A", "view": "base"})
    if r.ok:
        data = r.json()
        for ann in data["data"]:
            rows.append({
                "gene": gene,
                "drug": ann.get("drug", {}).get("name"),
                "phenotype": ann.get("phenotype"),
                "level": ann.get("evidenceLevel"),
                "significance": ann.get("clinicalSignificance"),
            })
    time.sleep(0.2)

df = pd.DataFrame(rows)
df = df.sort_values(["gene", "drug"])
df.to_csv("pharmacogene_drug_interactions.csv", index=False)
print(f"1A-level drug-gene interactions: {len(df)}")
print(df[["gene", "drug", "phenotype", "level"]].head(10).to_string(index=False))
```

### Workflow 2: Guideline Compliance Check for Drug Panel

**Goal**: Given a list of prescribed drugs, identify which have CPIC guidelines and flag for PGx review.

```python
import requests, pandas as pd, time

BASE = "https://api.pharmgkb.org/v1"

# Patient's drug list
drugs = ["warfarin", "clopidogrel", "codeine", "simvastatin",
         "metoprolol", "omeprazole", "azathioprine"]

rows = []
for drug in drugs:
    r = requests.get(f"{BASE}/guideline",
                     params={"drug": drug, "view": "base"})
    if r.ok:
        guidelines = r.json()["data"]
        cpic_count = sum(1 for g in guidelines if "CPIC" in g.get("source", ""))
        dpwg_count = sum(1 for g in guidelines if "DPWG" in g.get("source", ""))
        rows.append({
            "drug": drug,
            "has_guideline": len(guidelines) > 0,
            "cpic": cpic_count,
            "dpwg": dpwg_count,
            "total_guidelines": len(guidelines),
        })
    time.sleep(0.2)

df = pd.DataFrame(rows)
df = df.sort_values("total_guidelines", ascending=False)
print("Drug PGx Guideline Coverage:")
print(df.to_string(index=False))
df.to_csv("drug_pgx_coverage.csv", index=False)
```

## Key Parameters

| Parameter | Module | Default | Range / Options | Effect |
|-----------|--------|---------|-----------------|--------|
| `gene` | All endpoints | — | HGNC symbol | Filter by gene |
| `drug` | All endpoints | — | drug name string | Filter by drug |
| `level` | Clinical Annotation | — | `"1A"`, `"1B"`, `"2A"`, `"2B"`, `"3"`, `"4"` | Minimum evidence level |
| `variant` | Clinical Annotation | — | rsID string | Filter by variant |
| `source` | Drug Label | — | `"FDA"`, `"EMA"`, `"HCSC"` | Regulatory body source |
| `view` | All endpoints | `"base"` | `"base"`, `"max"` | Field detail level (max includes all nested data) |

## Best Practices

1. **Start with Level 1A/1B annotations**: Use `level=1A` filter to retrieve only the highest-evidence actionable annotations for clinical workflows; Level 3-4 annotations have limited actionability.

2. **Use `view=max` for full details**: Default `view=base` returns summary fields; `view=max` returns nested gene objects, full phenotype text, and linked resources (larger payload but more complete).

3. **Check CPIC guidelines separately**: Not all drugs with clinical annotations have CPIC guidelines; always check `get_guidelines()` in addition to `get_clinical_annotations()` for prescribing decisions.

4. **Cross-reference with FDA label annotations**: FDA pharmacogenomic labeling (`get_drug_labels(source="FDA")`) reflects regulatory requirements; higher binding than CPIC recommendations in many clinical contexts.

5. **Handle API rate limits gracefully**: Add `time.sleep(0.2)` between requests for batch queries; use `try/except` to handle occasional API errors gracefully.

## Common Recipes

### Recipe: All Drugs with CPIC Level 1A Evidence

When to use: Build a list of all drugs with highest-evidence pharmacogenomic guidelines.

```python
import requests, pandas as pd

r = requests.get("https://api.pharmgkb.org/v1/clinicalAnnotation",
                 params={"level": "1A", "view": "base"})
data = r.json()
print(f"Total Level 1A annotations: {data['count']}")
rows = [{"gene": a.get("gene", {}).get("symbol"),
         "drug": a.get("drug", {}).get("name"),
         "phenotype": a.get("phenotype")}
        for a in data["data"]]
df = pd.DataFrame(rows).drop_duplicates()
print(df.sort_values("gene").head(10).to_string(index=False))
```

### Recipe: CPIC Guideline URL for a Drug

When to use: Get the direct PDF link to a CPIC guideline for a prescribing decision.

```python
import requests

drug = "tacrolimus"
r = requests.get("https://api.pharmgkb.org/v1/guideline",
                 params={"drug": drug, "source": "CPIC", "view": "base"})
for gl in r.json()["data"]:
    print(f"{gl.get('name')}")
    print(f"  URL: {gl.get('url')}")
```

### Recipe: Variant Clinical Significance Summary

When to use: Quick lookup of clinical annotations for a specific rsID.

```python
import requests

rsid = "rs4149056"  # SLCO1B1*5 - statin myopathy
r = requests.get("https://api.pharmgkb.org/v1/clinicalAnnotation",
                 params={"variant": rsid, "view": "base"})
data = r.json()
print(f"{rsid}: {data['count']} clinical annotations")
for ann in data["data"][:5]:
    print(f"  [{ann['evidenceLevel']}] {ann.get('drug', {}).get('name')}: {ann.get('phenotype')}")
```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| Empty `data` array | Drug/gene not in PharmGKB | Check name spelling; try partial name matching |
| `count` > 0 but `data` is empty | Pagination needed | Add `pageNum` and `pageSize` parameters for results >100 |
| Missing `drug` field in annotation | Annotation has no specific drug | Filter on `ann.get("drug")` before accessing `drug["name"]` |
| Slow response for `view=max` | Large nested response payload | Use `view=base` for bulk queries; `view=max` only for individual records |
| HTTP 404 for specific IDs | PharmGKB ID format wrong | Use search endpoints first; avoid hand-constructing IDs |
| Drug name not found | Name variation | Try generic vs. brand name; check PharmGKB web interface for canonical name |

## Related Skills

- `clinvar-database` — Germline pathogenicity for variants found in PharmGKB (complementary)
- `opentargets-database` — Drug-target associations and safety data for pharmacogenomic targets
- `chembl-database-bioactivity` — Bioactivity and binding data for drugs annotated in PharmGKB
- `fda-database` — openFDA adverse event reports linked to pharmacogenomic risk factors

## References

- [PharmGKB website](https://www.pharmgkb.org/) — Official database and knowledge portal
- [PharmGKB REST API documentation](https://api.pharmgkb.org/v1/documentation) — Full API endpoint reference
- [CPIC guidelines](https://cpicpgx.org/) — Clinical Pharmacogenomics Implementation Consortium
- [Relling & Klein (2011) Nature Reviews Drug Discovery](https://doi.org/10.1038/nrd3499) — PharmGKB foundational paper
