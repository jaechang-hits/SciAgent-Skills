---
name: "fda-database"
description: "Query openFDA REST API for drug adverse event reports (FAERS), drug labeling, product information, recalls, and enforcement actions. Search by drug name, active ingredient, adverse event term (MedDRA), or NDC code. No API key needed for 1000 req/day; free key for 120,000 req/day. For clinical trial data use clinicaltrials-database-search; for drug structures use drugbank-database-access or chembl-database-bioactivity."
license: "CC0-1.0"
---

# openFDA Drug and Adverse Event Database

## Overview

openFDA provides public access to FDA regulatory data through a simple REST API. Key datasets include the FDA Adverse Event Reporting System (FAERS) with 20M+ adverse event reports, drug product labeling (NDC, SPL), drug approvals (Drugs@FDA), medical device reports, and recall enforcement actions. The API supports full-text search and structured queries using Elasticsearch-style syntax.

## When to Use

- Retrieving adverse event reports for a drug to assess safety signals and side effect profiles
- Querying FAERS for disproportionality analysis (comparing drug vs. drug adverse event profiles)
- Looking up official drug labeling (indications, contraindications, warnings, dosing) by drug name or NDC
- Searching for drug recalls and enforcement actions by drug name or company
- Identifying all marketed products containing a given active ingredient
- Building pharmacovigilance pipelines that monitor drug safety signals from public regulatory data
- For clinical trial efficacy data use `clinicaltrials-database-search`; for drug structures/targets use `drugbank-database-access`

## Prerequisites

- **Python packages**: `requests`, `pandas`
- **Data requirements**: drug names, active ingredients, MedDRA terms, NDC codes
- **Environment**: internet connection; no authentication required for basic use
- **Rate limits**: 1000 req/day without API key; 120,000 req/day with free API key from https://open.fda.gov/apis/authentication/

```bash
pip install requests pandas
```

## Quick Start

```python
import requests

BASE = "https://api.fda.gov/drug"
# Optional: add api_key parameter for higher rate limits

# Find adverse events for aspirin
r = requests.get(
    f"{BASE}/event.json",
    params={
        "search": 'patient.drug.medicinalproduct:"aspirin"',
        "count": "patient.reaction.reactionmeddrapt.exact",
        "limit": 10
    }
)
r.raise_for_status()
data = r.json()
print("Top adverse reactions for aspirin:")
for item in data["results"][:5]:
    print(f"  {item['term']:40s} count={item['count']}")
```

## Core API

### Query 1: Adverse Event Report Search (FAERS)

Search the FDA Adverse Event Reporting System for drug-event associations.

```python
import requests, pandas as pd

BASE = "https://api.fda.gov/drug"

def faers_search(drug_name, limit=100):
    """Search FAERS for adverse event reports mentioning a drug."""
    r = requests.get(f"{BASE}/event.json",
                     params={"search": f'patient.drug.medicinalproduct:"{drug_name}"',
                             "limit": limit})
    r.raise_for_status()
    return r.json()

data = faers_search("warfarin", limit=5)
total = data["meta"]["results"]["total"]
print(f"Total FAERS reports for warfarin: {total:,}")

# Show first report summary
report = data["results"][0]
print(f"\nReport {report['safetyreportid']}:")
print(f"  Date     : {report.get('receivedate', 'n/a')}")
print(f"  Serious  : {report.get('serious', 'n/a')}")
drugs = [d.get("medicinalproduct", "n/a") for d in report.get("patient", {}).get("drug", [])]
print(f"  Drugs    : {drugs[:5]}")
reactions = [r.get("reactionmeddrapt", "n/a") for r in report.get("patient", {}).get("reaction", [])]
print(f"  Reactions: {reactions[:5]}")
```

### Query 2: Count Top Adverse Events for a Drug

Use the `count` parameter to aggregate adverse event terms.

```python
import requests, pandas as pd

BASE = "https://api.fda.gov/drug"

def top_adverse_events(drug_name, limit=20):
    """Get the most frequently reported adverse events for a drug."""
    r = requests.get(f"{BASE}/event.json",
                     params={
                         "search": f'patient.drug.medicinalproduct:"{drug_name}"',
                         "count": "patient.reaction.reactionmeddrapt.exact",
                         "limit": limit
                     })
    r.raise_for_status()
    results = r.json()["results"]
    return pd.DataFrame(results).rename(columns={"term": "reaction", "count": "reports"})

df_atorvastatin = top_adverse_events("atorvastatin", limit=15)
print("Top adverse events for atorvastatin:")
print(df_atorvastatin.head(10).to_string(index=False))
df_atorvastatin.to_csv("atorvastatin_adverse_events.csv", index=False)
```

```python
# Compare two drugs: adverse event profile overlap
df_drug1 = top_adverse_events("simvastatin", limit=20)
df_drug2 = top_adverse_events("atorvastatin", limit=20)

common = set(df_drug1["reaction"]) & set(df_drug2["reaction"])
print(f"\nCommon adverse events (simvastatin ∩ atorvastatin): {len(common)}")
print("Shared reactions:", list(common)[:10])
```

### Query 3: Drug Labeling Search

Retrieve official drug labels (indications, warnings, dosing, contraindications).

```python
import requests

BASE = "https://api.fda.gov/drug"

def get_label(drug_name):
    """Retrieve FDA drug label by brand or generic name."""
    r = requests.get(f"{BASE}/label.json",
                     params={"search": f'openfda.brand_name:"{drug_name}"',
                             "limit": 1})
    if r.status_code == 404:
        r = requests.get(f"{BASE}/label.json",
                         params={"search": f'openfda.generic_name:"{drug_name}"',
                                 "limit": 1})
    r.raise_for_status()
    results = r.json()["results"]
    return results[0] if results else None

label = get_label("Lipitor")
if label:
    print(f"Brand name  : {label.get('openfda', {}).get('brand_name', ['n/a'])[0]}")
    print(f"Generic name: {label.get('openfda', {}).get('generic_name', ['n/a'])[0]}")
    print(f"Manufacturer: {label.get('openfda', {}).get('manufacturer_name', ['n/a'])[0]}")
    indications = label.get("indications_and_usage", ["n/a"])[0]
    print(f"\nIndications (first 300 chars):\n{indications[:300]}...")
```

### Query 4: Drug Product Lookup by NDC

Retrieve marketed product information by National Drug Code.

```python
import requests, pandas as pd

BASE = "https://api.fda.gov/drug"

def ndc_search(ndc_or_name, limit=10):
    """Search NDC directory for drug product information."""
    # Search by product name or NDC
    r = requests.get(f"{BASE}/ndc.json",
                     params={"search": f'generic_name:"{ndc_or_name}"',
                             "limit": limit})
    r.raise_for_status()
    return r.json()

data = ndc_search("metformin", limit=10)
total = data["meta"]["results"]["total"]
print(f"Metformin products: {total}")

rows = []
for prod in data["results"]:
    rows.append({
        "product_ndc": prod.get("product_ndc"),
        "brand_name": prod.get("brand_name"),
        "generic_name": prod.get("generic_name"),
        "dosage_form": prod.get("dosage_form"),
        "route": ", ".join(prod.get("route", [])),
        "labeler": prod.get("labeler_name"),
    })
df = pd.DataFrame(rows)
print(df.to_string(index=False))
```

### Query 5: Drug Recall Search

Search FDA enforcement actions and drug recalls by drug name or company.

```python
import requests, pandas as pd

BASE = "https://api.fda.gov/drug"

def drug_recalls(drug_name, limit=20):
    """Find FDA drug recalls for a given drug name."""
    r = requests.get(f"{BASE}/enforcement.json",
                     params={
                         "search": f'product_description:"{drug_name}"',
                         "limit": limit
                     })
    if r.status_code == 404:
        return pd.DataFrame()
    r.raise_for_status()
    results = r.json()["results"]
    return pd.DataFrame([{
        "recalling_firm": rec.get("recalling_firm"),
        "product": rec.get("product_description", "")[:80],
        "reason": rec.get("reason_for_recall", "")[:100],
        "classification": rec.get("classification"),
        "recall_date": rec.get("recall_initiation_date"),
        "status": rec.get("status"),
    } for rec in results])

recalls = drug_recalls("metformin", limit=5)
print(f"Metformin recalls: {len(recalls)}")
if not recalls.empty:
    print(recalls[["recalling_firm", "classification", "recall_date", "status"]].to_string(index=False))
```

### Query 6: Active Ingredient Search Across Products

Find all drug products containing a specific active ingredient.

```python
import requests, pandas as pd

BASE = "https://api.fda.gov/drug"

def products_by_ingredient(ingredient, limit=50):
    """Find all FDA-listed products with a given active ingredient."""
    r = requests.get(f"{BASE}/ndc.json",
                     params={
                         "search": f'active_ingredients.name:"{ingredient}"',
                         "limit": limit
                     })
    r.raise_for_status()
    data = r.json()
    print(f"Total products with {ingredient}: {data['meta']['results']['total']}")

    rows = []
    for prod in data["results"]:
        for ai in prod.get("active_ingredients", []):
            if ingredient.lower() in ai.get("name", "").lower():
                rows.append({
                    "brand": prod.get("brand_name"),
                    "generic": prod.get("generic_name"),
                    "strength": ai.get("strength"),
                    "dosage_form": prod.get("dosage_form"),
                    "route": ", ".join(prod.get("route", [])),
                })
    return pd.DataFrame(rows)

df = products_by_ingredient("metformin hydrochloride")
print(df.drop_duplicates(subset=["generic", "strength", "dosage_form"]).head(10).to_string(index=False))
```

## Key Concepts

### openFDA API Endpoints

| Endpoint | Dataset | Key Use |
|----------|---------|---------|
| `/drug/event.json` | FAERS (adverse events) | Pharmacovigilance, safety signals |
| `/drug/label.json` | Structured Product Labeling | Indications, warnings, dosing |
| `/drug/ndc.json` | NDC Directory | Marketed products, strengths |
| `/drug/enforcement.json` | Recalls & Enforcement | Drug recalls, market withdrawals |
| `/device/event.json` | MAUDE (device events) | Medical device adverse events |

### Query Syntax

openFDA uses Elasticsearch-style queries. Use `field:"exact phrase"` for exact matching, `field:term` for fuzzy matching, and `+field1:"A" +field2:"B"` for AND logic. Use `count` parameter to aggregate (equivalent to GROUP BY). Use `limit` (1–1000) for pagination with `skip` for offset.

## Common Workflows

### Workflow 1: Drug Safety Signal Analysis

**Goal**: Compare adverse event frequency for multiple drugs in the same therapeutic class to identify differentiated safety profiles.

```python
import requests, pandas as pd, time

BASE = "https://api.fda.gov/drug"

drugs = ["atorvastatin", "simvastatin", "rosuvastatin"]

def count_reactions(drug, limit=20):
    r = requests.get(f"{BASE}/event.json",
                     params={"search": f'patient.drug.medicinalproduct:"{drug}"',
                             "count": "patient.reaction.reactionmeddrapt.exact",
                             "limit": limit})
    if r.status_code != 200:
        return pd.Series(dtype=float, name=drug)
    df = pd.DataFrame(r.json()["results"])
    df.columns = ["reaction", drug]
    return df.set_index("reaction")[drug]

series_list = []
for drug in drugs:
    s = count_reactions(drug, limit=20)
    series_list.append(s)
    time.sleep(0.5)

comparison = pd.concat(series_list, axis=1).fillna(0)
comparison = comparison.sort_values(drugs[0], ascending=False)
print("Adverse event count comparison (statins):")
print(comparison.head(10).to_string())
comparison.to_csv("statin_safety_comparison.csv")
```

### Workflow 2: Drug Label Information Extractor

**Goal**: Extract indications, contraindications, and warnings for multiple drugs and save to CSV.

```python
import requests, pandas as pd, time, re

BASE = "https://api.fda.gov/drug"

def get_label_sections(drug_name):
    r = requests.get(f"{BASE}/label.json",
                     params={"search": f'openfda.generic_name:"{drug_name}"', "limit": 1})
    if r.status_code != 200 or not r.json()["results"]:
        return None
    label = r.json()["results"][0]

    def clean(field):
        text = " ".join(label.get(field, [""]))
        return re.sub(r"\s+", " ", text).strip()[:500]

    return {
        "drug": drug_name,
        "indications": clean("indications_and_usage"),
        "contraindications": clean("contraindications"),
        "warnings": clean("warnings_and_cautions") or clean("warnings"),
    }

drugs = ["metformin", "atorvastatin", "lisinopril", "omeprazole"]
rows = []
for drug in drugs:
    info = get_label_sections(drug)
    if info:
        rows.append(info)
    time.sleep(0.4)

df = pd.DataFrame(rows)
df.to_csv("drug_labels.csv", index=False)
print(df[["drug", "indications"]].to_string(index=False))
```

## Key Parameters

| Parameter | Module | Default | Range / Options | Effect |
|-----------|--------|---------|-----------------|--------|
| `search` | All endpoints | — | Elasticsearch syntax | Filter query |
| `count` | All endpoints | — | field name + `.exact` | Aggregate/count by field value |
| `limit` | All endpoints | `1` | `1`–`1000` | Results per request |
| `skip` | All endpoints | `0` | integer | Offset for pagination |
| `api_key` | All endpoints | — | API key string | Increase rate limit to 120K/day |
| `.exact` suffix | count field | — | appended to field name | Exact string matching vs tokenized |

## Best Practices

1. **Get a free API key**: Registration at https://open.fda.gov/apis/authentication/ is instant and raises your limit from 1,000 to 120,000 requests/day — essential for production use.

2. **Use `.exact` for drug name searches**: `patient.drug.medicinalproduct.exact` (not `.medicinalproduct`) gives exact phrase matching, preventing partial matches that inflate counts.

3. **Normalize drug names**: FAERS reporters use many spellings (e.g., "Lipitor", "atorvastatin calcium", "ATORVASTATIN"). Search multiple name variants or use generic ingredient field for consistent coverage.

4. **Interpret FAERS counts carefully**: Report counts do not equal incidence rates. FAERS is voluntary and subject to reporting bias; higher counts may reflect market size or media attention, not higher risk.

5. **Paginate large result sets**: Maximum `limit` is 1000; use `skip` to paginate through large result sets (`total` in `meta.results`).

## Common Recipes

### Recipe: Total FAERS Reports Count for a Drug

When to use: Quick check of total adverse event report volume for a drug.

```python
import requests

drug = "ibuprofen"
r = requests.get("https://api.fda.gov/drug/event.json",
                 params={"search": f'patient.drug.medicinalproduct.exact:"{drug}"',
                         "limit": 1})
total = r.json()["meta"]["results"]["total"]
print(f"Total FAERS reports for {drug}: {total:,}")
```

### Recipe: Find Serious Adverse Events Only

When to use: Filter FAERS for reports classified as serious (death, hospitalization, disability).

```python
import requests, pandas as pd

r = requests.get("https://api.fda.gov/drug/event.json",
                 params={
                     "search": 'patient.drug.medicinalproduct:"warfarin" AND serious:1',
                     "count": "patient.reaction.reactionmeddrapt.exact",
                     "limit": 10
                 })
df = pd.DataFrame(r.json()["results"])
df.columns = ["reaction", "serious_reports"]
print(df.to_string(index=False))
```

### Recipe: Check Drug Market Approval Status

When to use: Verify whether a drug has FDA NDA/ANDA approval and find the approval year.

```python
import requests

r = requests.get("https://api.fda.gov/drug/label.json",
                 params={"search": 'openfda.generic_name:"metformin"', "limit": 1})
label = r.json()["results"][0]
openfda = label.get("openfda", {})
print(f"Application numbers: {openfda.get('application_number', ['n/a'])}")
print(f"Product type: {openfda.get('product_type', ['n/a'])}")
print(f"NDA sponsor: {openfda.get('manufacturer_name', ['n/a'])}")
```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `HTTP 404` with `{"error": {"code": "NOT_FOUND"}}` | No results match query | Check drug name spelling; try alternative name formats |
| `HTTP 429 Too Many Requests` | Rate limit exceeded | Register for API key; add `time.sleep(1)` between requests |
| Count results don't match expectations | Drug name tokenization | Use `.exact` suffix: `medicinalproduct.exact` not `medicinalproduct` |
| Label search returns wrong drug | Ambiguous name | Add `+openfda.product_type:"HUMAN PRESCRIPTION DRUG"` to filter |
| Missing fields in FAERS report | Incomplete voluntary report | Check if field exists with `.get("field", "n/a")` |
| `skip + limit > 26000` error | Pagination limit | openFDA caps pagination at 26,000 records; use `count` endpoint for aggregates beyond this |

## Related Skills

- `clinicaltrials-database-search` — Clinical trial data for drugs identified via openFDA
- `drugbank-database-access` — Drug structures, targets, and interactions to contextualize FDA data
- `chembl-database-bioactivity` — Preclinical bioactivity data for drugs in the FAERS database
- `string-database-ppi` — Protein interactions for drug targets found via adverse event analysis

## References

- [openFDA API documentation](https://open.fda.gov/apis/) — Full API reference, endpoints, and query syntax
- [openFDA API key registration](https://open.fda.gov/apis/authentication/) — Free registration for increased rate limits
- [FAERS overview](https://www.fda.gov/drugs/surveillance/questions-and-answers-fdas-adverse-event-reporting-system-faers) — Understanding FAERS data and limitations
- [openFDA GitHub](https://github.com/FDA/openfda) — Source code and data download references
