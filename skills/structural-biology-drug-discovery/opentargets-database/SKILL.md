---
name: "opentargets-database"
description: "Query Open Targets Platform GraphQL API for target-disease associations, evidence scores, drug-target links, and safety data. Search targets by gene symbol, diseases by EFO ID, retrieve evidence scores from 20+ data sources, drug mechanisms, and tractability assessments. For ChEMBL bioactivity use chembl-database-bioactivity; for clinical trials use clinicaltrials-database-search."
license: "Apache-2.0"
---

# Open Targets Platform Database

## Overview

Open Targets Platform integrates evidence from genetics, genomics, literature, and drug databases to systematically score target-disease associations for 60,000+ targets and 20,000+ diseases/phenotypes. The public GraphQL API (no authentication required) provides access to association scores, evidence from 20+ data sources (GWAS, ClinVar, ChEMBL, drugs, pathways, mouse models, expression), and detailed drug-target-disease triangles.

## When to Use

- Ranking therapeutic targets for a disease by overall association score and evidence breakdown
- Finding all diseases associated with a gene of interest and their confidence scores
- Retrieving approved and investigational drugs for a target, with mechanism of action and clinical phase
- Assessing target druggability and tractability (small molecule, antibody, PROTAC likelihood)
- Pulling genetic association evidence (GWAS hits, variant-to-gene mappings) for a target-disease pair
- Exploring safety/adverse event data for a drug target from FAERS and literature
- For bioactivity IC50/Ki data use `chembl-database-bioactivity`; for clinical trial details use `clinicaltrials-database-search`

## Prerequisites

- **Python packages**: `requests`
- **Data requirements**: gene symbols (HGNC), Ensembl gene IDs, disease EFO IDs, or drug names
- **Environment**: internet connection; no authentication needed
- **Rate limits**: no hard limit stated; use reasonable delays for large queries (>100 targets)

```bash
pip install requests
```

## Quick Start

```python
import requests

OT_URL = "https://api.platform.opentargets.org/api/v4/graphql"

def ot_query(gql, variables=None):
    r = requests.post(OT_URL, json={"query": gql, "variables": variables or {}})
    r.raise_for_status()
    return r.json()["data"]

# Top disease associations for BRCA1
query = """
query TargetDiseases($ensgId: String!) {
  target(ensemblId: $ensgId) {
    id
    approvedSymbol
    associatedDiseases(page: {index: 0, size: 5}) {
      rows {
        disease { id name }
        score
      }
    }
  }
}
"""
data = ot_query(query, {"ensgId": "ENSG00000012048"})
target = data["target"]
print(f"Target: {target['approvedSymbol']}")
for row in target["associatedDiseases"]["rows"]:
    print(f"  {row['disease']['name']}: {row['score']:.3f}")
```

## Core API

### Query 1: Target Lookup by Gene Symbol

Search for a target and retrieve basic metadata (Ensembl ID, biotype, description).

```python
import requests

OT_URL = "https://api.platform.opentargets.org/api/v4/graphql"

def ot_query(gql, variables=None):
    r = requests.post(OT_URL, json={"query": gql, "variables": variables or {}})
    r.raise_for_status()
    return r.json()["data"]

# Search by gene symbol
query = """
query SearchTarget($sym: String!) {
  search(queryString: $sym, entityNames: ["target"]) {
    hits {
      id
      name
      entity
      object {
        ... on Target {
          approvedSymbol
          approvedName
          biotype
          functionDescriptions
        }
      }
    }
  }
}
"""
data = ot_query(query, {"sym": "BRCA1"})
for hit in data["search"]["hits"][:3]:
    obj = hit.get("object", {})
    print(f"ID: {hit['id']} | {obj.get('approvedSymbol')} | {obj.get('biotype')}")
    descs = obj.get("functionDescriptions", [])
    if descs:
        print(f"  Function: {descs[0][:120]}")
```

```python
# Direct lookup by Ensembl ID
query2 = """
query Target($ensgId: String!) {
  target(ensemblId: $ensgId) {
    id approvedSymbol approvedName biotype
    tractability { label modality value }
  }
}
"""
data2 = ot_query(query2, {"ensgId": "ENSG00000141510"})  # TP53
t = data2["target"]
print(f"\n{t['approvedSymbol']} ({t['id']}): {t['biotype']}")
print("Tractability:")
for tr in t.get("tractability", [])[:5]:
    print(f"  {tr['modality']} | {tr['label']}: {tr['value']}")
```

### Query 2: Target-Disease Associations

Retrieve association scores for a target across all associated diseases.

```python
import requests, pandas as pd

OT_URL = "https://api.platform.opentargets.org/api/v4/graphql"

def ot_query(gql, variables=None):
    r = requests.post(OT_URL, json={"query": gql, "variables": variables or {}})
    r.raise_for_status()
    return r.json()["data"]

query = """
query Associations($ensgId: String!, $size: Int!) {
  target(ensemblId: $ensgId) {
    approvedSymbol
    associatedDiseases(page: {index: 0, size: $size}, orderByScore: "score") {
      count
      rows {
        disease { id name therapeuticAreas { name } }
        score
        datatypeScores { componentId score }
      }
    }
  }
}
"""
data = ot_query(query, {"ensgId": "ENSG00000012048", "size": 20})
target = data["target"]
assoc = target["associatedDiseases"]
print(f"{target['approvedSymbol']}: {assoc['count']} associated diseases")

rows = []
for r in assoc["rows"]:
    scores = {d["componentId"]: d["score"] for d in r.get("datatypeScores", [])}
    rows.append({
        "disease": r["disease"]["name"],
        "disease_id": r["disease"]["id"],
        "overall_score": round(r["score"], 4),
        "genetics": round(scores.get("genetic_association", 0), 3),
        "drugs": round(scores.get("known_drug", 0), 3),
        "literature": round(scores.get("literature", 0), 3),
    })

df = pd.DataFrame(rows)
print(df.head(10).to_string(index=False))
```

### Query 3: Disease-Target Associations

Given a disease, retrieve all associated targets ranked by score.

```python
import requests, pandas as pd

OT_URL = "https://api.platform.opentargets.org/api/v4/graphql"

def ot_query(gql, variables=None):
    r = requests.post(OT_URL, json={"query": gql, "variables": variables or {}})
    r.raise_for_status()
    return r.json()["data"]

query = """
query DiseaseTargets($efoId: String!, $size: Int!) {
  disease(efoId: $efoId) {
    id name
    associatedTargets(page: {index: 0, size: $size}, orderByScore: "score") {
      count
      rows {
        target { id approvedSymbol biotype }
        score
        datatypeScores { componentId score }
      }
    }
  }
}
"""
# EFO_0000305 = breast carcinoma
data = ot_query(query, {"efoId": "EFO_0000305", "size": 10})
disease = data["disease"]
print(f"Disease: {disease['name']}")
print(f"Total associated targets: {disease['associatedTargets']['count']}")

for row in disease["associatedTargets"]["rows"][:5]:
    t = row["target"]
    print(f"  {t['approvedSymbol']:12s} score={row['score']:.3f} biotype={t['biotype']}")
```

### Query 4: Known Drugs for a Target

Retrieve approved and investigational drugs, their mechanism, and clinical phase.

```python
import requests, pandas as pd

OT_URL = "https://api.platform.opentargets.org/api/v4/graphql"

def ot_query(gql, variables=None):
    r = requests.post(OT_URL, json={"query": gql, "variables": variables or {}})
    r.raise_for_status()
    return r.json()["data"]

query = """
query KnownDrugs($ensgId: String!) {
  target(ensemblId: $ensgId) {
    approvedSymbol
    knownDrugs {
      count
      rows {
        drug { id name drugType maximumClinicalTrialPhase isApproved }
        mechanismOfAction
        disease { name }
        phase
        status
      }
    }
  }
}
"""
data = ot_query(query, {"ensgId": "ENSG00000146648"})  # EGFR
target = data["target"]
drugs_data = target["knownDrugs"]
print(f"{target['approvedSymbol']}: {drugs_data['count']} drug-indication pairs")

rows = []
for r in drugs_data["rows"]:
    drug = r["drug"]
    rows.append({
        "drug": drug["name"],
        "type": drug["drugType"],
        "phase": r["phase"],
        "approved": drug["isApproved"],
        "indication": r["disease"]["name"] if r.get("disease") else "n/a",
        "mechanism": r["mechanismOfAction"],
    })

df = pd.DataFrame(rows).drop_duplicates(subset=["drug", "indication"])
print(df.head(10).to_string(index=False))
```

### Query 5: Evidence for a Specific Target-Disease Pair

Retrieve detailed evidence records (GWAS, ClinVar, literature) for a target-disease pair.

```python
import requests

OT_URL = "https://api.platform.opentargets.org/api/v4/graphql"

def ot_query(gql, variables=None):
    r = requests.post(OT_URL, json={"query": gql, "variables": variables or {}})
    r.raise_for_status()
    return r.json()["data"]

query = """
query Evidence($ensgId: String!, $efoId: String!) {
  disease(efoId: $efoId) {
    evidences(
      ensemblIds: [$ensgId]
      enableIndirect: true
      size: 10
      datasourceIds: ["gwas_catalog", "clinvar", "chembl"]
    ) {
      count
      rows {
        datasourceId
        score
        variantId
        studyId
        publicationYear
        clinicalSignificances
      }
    }
  }
}
"""
data = ot_query(query, {"ensgId": "ENSG00000012048", "efoId": "EFO_0000305"})
evidences = data["disease"]["evidences"]
print(f"Evidence records: {evidences['count']}")
for ev in evidences["rows"][:5]:
    print(f"  Source: {ev['datasourceId']:20s} | Score: {ev['score']:.3f}")
```

### Query 6: Safety and Adverse Events

Retrieve known adverse events and safety data for a target.

```python
import requests

OT_URL = "https://api.platform.opentargets.org/api/v4/graphql"

def ot_query(gql, variables=None):
    r = requests.post(OT_URL, json={"query": gql, "variables": variables or {}})
    r.raise_for_status()
    return r.json()["data"]

query = """
query Safety($ensgId: String!) {
  target(ensemblId: $ensgId) {
    approvedSymbol
    safetyLiabilities {
      event
      effects { direction dosing }
      biosamples { tissueLabel cellLabel }
      datasources { name pmid }
    }
  }
}
"""
data = ot_query(query, {"ensgId": "ENSG00000146648"})  # EGFR
target = data["target"]
print(f"Safety liabilities for {target['approvedSymbol']}:")
for s in target.get("safetyLiabilities", [])[:5]:
    print(f"  Event: {s['event']}")
    for ds in s.get("datasources", []):
        print(f"    Source: {ds['name']}, PMID: {ds.get('pmid', 'n/a')}")
```

## Key Concepts

### Association Scores

Open Targets uses harmonic sum aggregation to combine evidence from multiple data sources into a 0–1 association score. Subscores include: genetic_association, somatic_mutation, known_drug, affected_pathway, literature, RNA_expression, animal_model, and others. Higher scores indicate more and stronger evidence.

### EFO IDs for Diseases

Open Targets uses Experimental Factor Ontology (EFO) identifiers for diseases (e.g., `EFO_0000305` for breast carcinoma). Search by disease name using the `search` query to find EFO IDs before querying associations.

## Common Workflows

### Workflow 1: Target Prioritization for a Disease

**Goal**: Given a disease, rank all associated targets by overall score and export with evidence breakdown.

```python
import requests, pandas as pd, time

OT_URL = "https://api.platform.opentargets.org/api/v4/graphql"

def ot_query(gql, variables=None):
    r = requests.post(OT_URL, json={"query": gql, "variables": variables or {}})
    r.raise_for_status()
    return r.json()["data"]

def disease_search(name):
    q = 'query S($q:String!){search(queryString:$q,entityNames:["disease"]){hits{id name}}}'
    data = ot_query(q, {"q": name})
    return [(h["id"], h["name"]) for h in data["search"]["hits"][:3]]

def get_top_targets(efo_id, n=50):
    q = """
    query($efoId:String!,$size:Int!){
      disease(efoId:$efoId){
        name
        associatedTargets(page:{index:0,size:$size},orderByScore:"score"){
          count
          rows{
            target{id approvedSymbol biotype}
            score
            datatypeScores{componentId score}
          }
        }
      }
    }"""
    data = ot_query(q, {"efoId": efo_id, "size": n})
    disease = data["disease"]
    rows = []
    for row in disease["associatedTargets"]["rows"]:
        t = row["target"]
        scores = {d["componentId"]: round(d["score"], 3) for d in row.get("datatypeScores", [])}
        rows.append({
            "target": t["approvedSymbol"],
            "ensembl_id": t["id"],
            "biotype": t["biotype"],
            "overall_score": round(row["score"], 4),
            **scores
        })
    return disease["name"], pd.DataFrame(rows)

# Step 1: Find EFO ID for disease
candidates = disease_search("non-small cell lung carcinoma")
print("Disease candidates:", candidates)

# Step 2: Get top targets
disease_name, df = get_top_targets("EFO_0003060", n=50)
df.to_csv("target_prioritization.csv", index=False)
print(f"\nTop targets for {disease_name}:")
print(df[["target", "overall_score", "genetic_association", "known_drug"]].head(10).to_string(index=False))
```

### Workflow 2: Drug-Target-Disease Triangle

**Goal**: For a target, retrieve all drugs and their associated indications and phases.

```python
import requests, pandas as pd

OT_URL = "https://api.platform.opentargets.org/api/v4/graphql"

def ot_query(gql, variables=None):
    r = requests.post(OT_URL, json={"query": gql, "variables": variables or {}})
    r.raise_for_status()
    return r.json()["data"]

query = """
query($ensgId:String!){
  target(ensemblId:$ensgId){
    approvedSymbol
    knownDrugs{
      count
      rows{
        drug{id name drugType maximumClinicalTrialPhase isApproved}
        disease{id name}
        mechanismOfAction phase status
      }
    }
  }
}"""

targets = {
    "EGFR": "ENSG00000146648",
    "ERBB2": "ENSG00000141736",
}

all_rows = []
for sym, ensg in targets.items():
    data = ot_query(query, {"ensgId": ensg})
    for row in data["target"]["knownDrugs"]["rows"]:
        drug = row["drug"]
        all_rows.append({
            "target": sym,
            "drug": drug["name"],
            "drug_type": drug["drugType"],
            "phase": row["phase"],
            "approved": drug["isApproved"],
            "indication": row["disease"]["name"] if row.get("disease") else "n/a",
            "mechanism": row["mechanismOfAction"],
        })

df = pd.DataFrame(all_rows)
df.to_csv("drug_target_matrix.csv", index=False)
print(df.head(10).to_string(index=False))
```

## Key Parameters

| Parameter | Module | Default | Range / Options | Effect |
|-----------|--------|---------|-----------------|--------|
| `page.size` | Associations | `10` | `1`–`10000` | Records per page |
| `page.index` | Associations | `0` | `0`–N | Page index for pagination |
| `orderByScore` | Associations | `"score"` | `"score"`, component IDs | Sort associations by score |
| `datasourceIds` | Evidence | all sources | list of datasource IDs | Filter evidence by source |
| `enableIndirect` | Evidence | `false` | `true`/`false` | Include child disease evidence |
| `entityNames` | Search | all | `["target"]`, `["disease"]` | Filter search entity type |

## Best Practices

1. **Use EFO IDs for diseases**: Disease names vary; always use the `search` query to get the canonical EFO ID before running association queries to avoid name-matching issues.

2. **Paginate for full result sets**: Default page size is 10; use `page.size: 10000` for complete results, but be aware this can return large payloads.

3. **Filter by `datatypeScores`**: For genetic target validation, filter on `genetic_association` subscore > 0.1; for drug repurposing, prioritize `known_drug` subscore.

4. **Use `enableIndirect: true`** in evidence queries to include evidence for disease subtypes (child terms in EFO hierarchy).

5. **Cache GraphQL responses**: Open Targets data updates quarterly; cache responses during analysis to avoid redundant API calls.

## Common Recipes

### Recipe: Disease Name to EFO ID

When to use: Resolve a disease name to the EFO ID needed for association queries.

```python
import requests

OT_URL = "https://api.platform.opentargets.org/api/v4/graphql"

query = """
query($q: String!) {
  search(queryString: $q, entityNames: ["disease"]) {
    hits { id name score }
  }
}"""
r = requests.post(OT_URL, json={"query": query, "variables": {"q": "breast cancer"}})
for hit in r.json()["data"]["search"]["hits"][:5]:
    print(f"{hit['id']}: {hit['name']} (score={hit['score']:.3f})")
```

### Recipe: Target Tractability Assessment

When to use: Assess whether a target is tractable for small molecules, antibodies, or PROTACs.

```python
import requests

OT_URL = "https://api.platform.opentargets.org/api/v4/graphql"

query = """
query($ensgId: String!) {
  target(ensemblId: $ensgId) {
    approvedSymbol
    tractability { label modality value }
  }
}"""
r = requests.post(OT_URL, json={"query": query, "variables": {"ensgId": "ENSG00000141510"}})
t = r.json()["data"]["target"]
print(f"Tractability for {t['approvedSymbol']}:")
for tr in t.get("tractability", []):
    if tr["value"]:
        print(f"  [{tr['modality']}] {tr['label']}")
```

### Recipe: Approved Drugs for a Disease

When to use: Find all approved drugs for a disease with phase 4 evidence.

```python
import requests, pandas as pd

OT_URL = "https://api.platform.opentargets.org/api/v4/graphql"

query = """
query($efoId: String!) {
  disease(efoId: $efoId) {
    name
    knownDrugs { count rows {
      drug { name isApproved maximumClinicalTrialPhase }
      target { approvedSymbol }
      mechanismOfAction
    }}
  }
}"""
r = requests.post(OT_URL, json={"query": query, "variables": {"efoId": "EFO_0000305"}})
data = r.json()["data"]["disease"]
approved = [row for row in data["knownDrugs"]["rows"] if row["drug"]["isApproved"]]
print(f"Approved drugs for {data['name']}: {len(approved)}")
for row in approved[:5]:
    print(f"  {row['drug']['name']} → {row['target']['approvedSymbol']}: {row['mechanismOfAction']}")
```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `HTTP 400` with GraphQL error | Malformed query or invalid field name | Check query against GraphQL schema at https://api.platform.opentargets.org/api/v4/graphql |
| Empty `rows` in associations | EFO ID not recognized | Use `search` query to find correct EFO ID |
| Target not found | Gene symbol vs Ensembl ID mismatch | Use `search` query first to resolve Ensembl ID |
| Slow query for large result set | `page.size` too large | Cap at 500 rows; paginate with multiple requests |
| Missing tractability data | Target not assessed | Not all targets have tractability; check `tractability` field is non-null |
| `knownDrugs` empty | No drug-target evidence in ChEMBL | Use `chembl-database-bioactivity` for preclinical compound activity |

## Related Skills

- `chembl-database-bioactivity` — Bioactivity IC50/Ki data for compounds against targets
- `clinicaltrials-database-search` — Detailed clinical trial information for drugs found via Open Targets
- `ensembl-database` — Ensembl IDs and variant annotations needed as input to Open Targets queries
- `string-database-ppi` — Protein-protein interaction networks to contextualize target biology

## References

- [Open Targets Platform](https://platform.opentargets.org/) — Interactive target-disease browser
- [Open Targets GraphQL API documentation](https://platform-docs.opentargets.org/data-access/graphql-api) — Query reference and schema
- [GraphQL playground](https://api.platform.opentargets.org/api/v4/graphql) — Interactive query builder
- [Open Targets data sources](https://platform-docs.opentargets.org/evidence) — Evidence types and scoring methodology
