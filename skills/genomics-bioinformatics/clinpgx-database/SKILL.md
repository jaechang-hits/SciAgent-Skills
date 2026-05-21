---
name: "clinpgx-database"
description: "Query the ClinPGx (formerly PharmGKB) REST API plus the CPIC PostgREST companion API for pharmacogenomic clinical annotations, CPIC/DPWG dosing guidelines, gene-drug pairs, variant-drug associations, FDA/EMA drug labels, and PGx pathways. Two-host architecture: api.clinpgx.org for annotation records, api.cpicpgx.org for genotype→recommendation lookups. No auth. For germline pathogenicity use clinvar-database; for somatic cancer PGx use cosmic-database or opentargets-database; for drug bioactivity use chembl-database-bioactivity."
license: "CC-BY-SA-4.0"
---

# ClinPGx (PharmGKB) Pharmacogenomics Database

## Overview

PharmGKB rebranded as **ClinPGx** in 2024 and the API moved from `api.pharmgkb.org` to `api.clinpgx.org`. The old host now returns 404/405; every example here uses the new endpoints. Two complementary APIs are used together:

- **ClinPGx Data API** (`api.clinpgx.org/v1`) — record-style access to genes, drugs, variants, clinical annotations, guideline annotations, drug labels, and pathways. Responses wrap data as `{"data": [...], "status": "success"}`. Filters use dotted property paths (e.g. `relatedChemicals.name=clopidogrel`, `levelOfEvidence.term=1A`).
- **CPIC PostgREST API** (`api.cpicpgx.org/v1`) — relational lookup of genotype → drug recommendation rows. PostgREST filter syntax (`column=eq.value`, JSON `cs.{...}` for jsonb containment). Returns flat JSON arrays.

Use ClinPGx for *what is known* about a gene/drug/variant; use CPIC for *how to prescribe* given a phenotype. The pattern is `ClinPGx for annotations, CPIC for recommendations`.

## When to Use

- Retrieving CPIC genotype-specific dosing recommendations for a gene-drug pair (e.g., CYP2C19 + clopidogrel) — use CPIC
- Looking up all pharmacogenomic clinical annotations for a drug or evidence level — use ClinPGx `data/clinicalAnnotation`
- Finding all CPIC/DPWG guideline annotations for a pharmacogene — use ClinPGx `data/guidelineAnnotation`
- Resolving a gene symbol, drug name, or rsID to ClinPGx PA identifiers — use `data/{gene,drug,variant}`
- Free-text search across all ClinPGx record types (genes, drugs, variants, annotations) — use `POST /site/search`
- Retrieving FDA/EMA pharmacogenomic drug label annotations — use ClinPGx `data/label`
- Building precision-medicine prescribing workflows that combine annotation evidence with phenotype-specific recommendations
- For germline disease pathogenicity (not PGx) use `clinvar-database`
- For somatic cancer pharmacogenomics use `cosmic-database` or `opentargets-database`

## Prerequisites

- **Python packages**: `requests`, `pandas` — both already in standard environments
- **Data requirements**: HGNC gene symbols, drug names (lowercase generic), dbSNP rsIDs, or PA identifiers
- **Environment**: internet connection; no authentication required for either host
- **Rate limits**: the ClinPGx host occasionally returns HTTP 429; insert `time.sleep(0.3–0.5)` between sequential calls. CPIC is more permissive.

If you are inside a pixi/conda environment that already provides `requests` and `pandas`, skip the install — invoke scripts with `pixi run python ...`.

```bash
pip install requests pandas
```

## Quick Start

```python
import requests

CLINPGX = "https://api.clinpgx.org/v1"
CPIC    = "https://api.cpicpgx.org/v1"

# CPIC genotype → recommendation: clopidogrel + CYP2C19 Poor Metabolizer
drug = requests.get(f"{CPIC}/drug", params={"name": "eq.clopidogrel"}).json()[0]
recs = requests.get(f"{CPIC}/recommendation",
                    params={"drugid": f"eq.{drug['drugid']}",
                            "phenotypes": 'cs.{"CYP2C19":"Poor Metabolizer"}'}).json()
print(f"clopidogrel CYP2C19=PM: {len(recs)} recommendation(s)")
for rec in recs[:2]:
    print(f"  [{rec['classification']}] {rec['drugrecommendation'][:80]}…")

# ClinPGx side: how many CPIC guideline annotations cover CYP2C19?
glines = requests.get(f"{CLINPGX}/data/guidelineAnnotation",
                      params={"relatedGenes.symbol": "CYP2C19",
                              "source": "CPIC", "view": "base"}).json()["data"]
print(f"CYP2C19 CPIC guidelines: {len(glines)}")
```

## Core API

### Module 1: Free-text site search

`POST /site/search` with a JSON body `{"query": "<term>"}` is the canonical entry point when you don't know the PA ID. It searches across drugs, genes, variants, clinical annotations, guideline annotations, and labels in one shot.

```python
import requests

CLINPGX = "https://api.clinpgx.org/v1"

r = requests.post(f"{CLINPGX}/site/search",
                  json={"query": "rs4149056"}, timeout=15)
r.raise_for_status()
hits = r.json()["data"]["hits"]
print(f"Total hits: {r.json()['data']['total']}")
for h in hits[:5]:
    print(f"  id={h.get('id')}  name={h.get('name')[:80]}")
```

```python
# Broader concept search
r = requests.post(f"{CLINPGX}/site/search",
                  json={"query": "TPMT azathioprine"}, timeout=15)
hits = r.json()["data"]["hits"]
print(f"TPMT+azathioprine hits: {len(hits)}")
for h in hits[:5]:
    print(f"  {h.get('id'):>15}  {h.get('name','')[:80]}")
```

### Module 2: Gene, drug, and variant record lookup

The `/data/{type}` endpoints accept simple property filters. All return `{"data": [...], "status": "success"}` — use `view=base` for summary, `view=max` for full nested objects.

```python
import requests

CLINPGX = "https://api.clinpgx.org/v1"

# Gene by HGNC symbol
gene = requests.get(f"{CLINPGX}/data/gene",
                    params={"symbol": "CYP2D6", "view": "base"}).json()["data"][0]
print(f"{gene['symbol']}  id={gene['id']}  {gene['name']}")

# Drug by name (lowercase generic preferred)
drug = requests.get(f"{CLINPGX}/data/drug",
                    params={"name": "warfarin", "view": "base"}).json()["data"][0]
print(f"{drug['name']}  id={drug['id']}")

# Variant by rsID
var = requests.get(f"{CLINPGX}/data/variant",
                   params={"name": "rs4149056", "view": "base"}).json()["data"][0]
print(f"{var['name']}  id={var['id']}  significance={var.get('clinicalSignificance')}")
```

```python
# Direct record fetch when you already have a PA ID
r = requests.get(f"{CLINPGX}/data/drug/PA449088", params={"view": "max"}).json()
d = r["data"]
print(f"PA449088 → {d['name']}  (objCls={d['objCls']})")
```

### Module 3: Clinical annotations

`data/clinicalAnnotation` records associate a variant (`location`) with one or more drugs (`relatedChemicals`) and an evidence level (`levelOfEvidence.term`). The two supported filters are `relatedChemicals.name=` and `levelOfEvidence.term=`. There is **no working `gene=` filter on this endpoint** — see Module 4 for gene-driven access.

```python
import requests, pandas as pd

CLINPGX = "https://api.clinpgx.org/v1"

# All clinical annotations for clopidogrel
data = requests.get(f"{CLINPGX}/data/clinicalAnnotation",
                    params={"relatedChemicals.name": "clopidogrel",
                            "view": "base"}).json()["data"]
print(f"clopidogrel annotations: {len(data)}")

rows = []
for ann in data[:10]:
    loc = ann.get("location") or {}
    drugs = ", ".join(c.get("name", "") for c in ann.get("relatedChemicals", []))
    rows.append({
        "id": ann["id"],
        "variant": loc.get("displayName"),
        "gene": (loc.get("genes") or [{}])[0].get("symbol"),
        "drug": drugs,
        "level": (ann.get("levelOfEvidence") or {}).get("term"),
        "score": ann.get("score"),
    })
print(pd.DataFrame(rows).to_string(index=False))
```

```python
# All Level 1A clinical annotations (highest evidence)
data = requests.get(f"{CLINPGX}/data/clinicalAnnotation",
                    params={"levelOfEvidence.term": "1A",
                            "view": "base"}).json()["data"]
print(f"Level 1A annotations: {len(data)}")

drug_to_count = {}
for ann in data:
    for c in ann.get("relatedChemicals") or []:
        drug_to_count[c["name"]] = drug_to_count.get(c["name"], 0) + 1
top = sorted(drug_to_count.items(), key=lambda x: -x[1])[:10]
for d, n in top:
    print(f"  {n:3}  {d}")
```

### Module 4: Guideline annotations (gene-driven access)

`data/guidelineAnnotation` supports both `relatedGenes.symbol=` and `relatedChemicals.name=`, plus `source=` (`CPIC`, `DPWG`, `CPNDS`, `RNPGx`). This is the canonical way to get gene→guideline coverage.

```python
import requests

CLINPGX = "https://api.clinpgx.org/v1"

# All CPIC guidelines mentioning CYP2C19
data = requests.get(f"{CLINPGX}/data/guidelineAnnotation",
                    params={"relatedGenes.symbol": "CYP2C19",
                            "source": "CPIC",
                            "view": "base"}).json()["data"]
print(f"CYP2C19 CPIC guidelines: {len(data)}")
for g in data[:5]:
    print(f"  PA{g['id']}: {g['name'][:80]}")
```

```python
# Guidelines for a specific drug across all bodies (CPIC, DPWG, …)
data = requests.get(f"{CLINPGX}/data/guidelineAnnotation",
                    params={"relatedChemicals.name": "clopidogrel",
                            "view": "base"}).json()["data"]
by_source = {}
for g in data:
    for s in (g.get("crossReferences") or []):
        by_source.setdefault(s.get("resource", "?"), 0)
        by_source[s["resource"]] = by_source.get(s["resource"], 0) + 1
print(f"clopidogrel guidelines: {len(data)} ({list({g.get('source') for g in data})})")
```

### Module 5: Regulatory drug labels (FDA / EMA)

`data/label` records are PharmGKB-curated annotations of FDA/EMA pharmacogenomic labeling. Filter by `relatedChemicals.name=` and `source=` (`FDA`, `EMA`, `HCSC`, `PMDA`, `Swissmedic`).

```python
import requests, pandas as pd

CLINPGX = "https://api.clinpgx.org/v1"

data = requests.get(f"{CLINPGX}/data/label",
                    params={"relatedChemicals.name": "warfarin",
                            "source": "FDA",
                            "view": "base"}).json()["data"]
print(f"warfarin FDA labels: {len(data)}")

rows = [{
    "name": d["name"][:60],
    "biomarker_status": d.get("biomarkerStatus"),
    "testing_required": d.get("testingRequired"),
    "alternate_drug": d.get("alternateDrugAvailable"),
} for d in data]
print(pd.DataFrame(rows).to_string(index=False))
```

### Module 6: CPIC genotype → recommendation chain

CPIC's PostgREST API uses `column=eq.value` for equality and `column=cs.{...}` for JSONB containment. The standard lookup chain is `drug → drugid → recommendation`, optionally filtered by phenotype.

```python
import requests

CPIC = "https://api.cpicpgx.org/v1"

# Resolve drug name to drugid (RxNorm-prefixed)
drug = requests.get(f"{CPIC}/drug",
                    params={"name": "eq.clopidogrel"}).json()[0]
print(f"clopidogrel drugid: {drug['drugid']}")

# All phenotype-specific recommendations for clopidogrel
recs = requests.get(f"{CPIC}/recommendation",
                    params={"drugid": f"eq.{drug['drugid']}"}).json()
print(f"Total recommendations: {len(recs)}")
for rec in recs[:3]:
    print(f"  {rec['phenotypes']}  [{rec['classification']}]")
    print(f"    {rec['drugrecommendation'][:90]}…")
```

```python
# Phenotype filter via jsonb containment (cs.{...})
# The phenotypes column is a jsonb dict; cs. checks that the query is a subset.
recs = requests.get(f"{CPIC}/recommendation",
                    params={"drugid": f"eq.{drug['drugid']}",
                            "phenotypes": 'cs.{"CYP2C19":"Poor Metabolizer"}'}
                    ).json()
for rec in recs:
    print(f"  [{rec['classification']}] {rec['drugrecommendation'][:90]}…")

# Gene-driven: list every drug with a CPIC pair for CYP2C19
pairs = requests.get(f"{CPIC}/pair",
                     params={"genesymbol": "eq.CYP2C19"}).json()
print(f"\nCYP2C19 CPIC pairs: {len(pairs)}")
drug_ids = sorted({p["drugid"] for p in pairs})
print(f"Sample drug IDs: {drug_ids[:5]}")
```

## Key Concepts

### Two-host architecture

| Question                                        | Use                                 | Why                                                                              |
| ----------------------------------------------- | ----------------------------------- | -------------------------------------------------------------------------------- |
| What clinical annotations exist for this drug?  | ClinPGx `data/clinicalAnnotation`   | Annotation-level evidence with curated levelOfEvidence.term                      |
| What CPIC guidelines cover this gene?           | ClinPGx `data/guidelineAnnotation`  | Filter by `relatedGenes.symbol`; no working `gene=` filter on clinicalAnnotation |
| Given phenotype X, what should I prescribe?     | CPIC `recommendation` + `phenotypes`| Structured genotype→action rows; CPIC is the prescribing-rule oracle             |
| What FDA labels mention this drug + gene?       | ClinPGx `data/label?source=FDA`     | Curated regulatory PGx labeling                                                  |
| Free-text "anything about X"                    | ClinPGx `POST /site/search`         | Cross-record-type fan-out                                                        |

### PharmGKB / ClinPGx evidence levels

Levels 1A → 4 in decreasing evidence quality:
- **1A** — Annotation of a variant–drug pair in a clinical guideline or FDA label (strongest)
- **1B** — Significant association replicated in multiple studies
- **2A** — Variant in a known PGx gene, significant association
- **2B** — Moderate evidence, often single study
- **3** — Limited evidence (single study or unreplicated)
- **4** — Case reports / biological plausibility only

Filter via `levelOfEvidence.term` on `data/clinicalAnnotation`. The term is a *string*, not an enum (`"1A"` not `1A`).

### ClinPGx response envelope and view modes

Every ClinPGx `/data/...` response is `{"data": [...] | {...}, "status": "success" | "fail"}`. On failure the body is `{"status": "fail", "data": {"errors": [{"message": "..."}]}}` — always read both keys.

- `view=base` (default) — flat summary record; recommended for bulk filters
- `view=max` — full nested objects (relatedDiseases, allelePhenotypes, scoreDetails, …). Larger payload, slower; use only for single-record details.

## Common Workflows

### Workflow 1: Pharmacogene panel CPIC coverage

**Goal:** Given a patient's pharmacogene panel, count how many CPIC guideline annotations cover each gene.

```python
import requests, pandas as pd, time

CLINPGX = "https://api.clinpgx.org/v1"
pharmacogenes = ["CYP2D6", "CYP2C19", "CYP2C9", "DPYD", "TPMT", "SLCO1B1"]

rows = []
for g in pharmacogenes:
    data = requests.get(f"{CLINPGX}/data/guidelineAnnotation",
                        params={"relatedGenes.symbol": g,
                                "source": "CPIC", "view": "base"},
                        timeout=20).json()["data"]
    drugs = sorted({c["name"] for guideline in data
                                for c in (guideline.get("relatedChemicals") or [])})
    rows.append({"gene": g, "cpic_guidelines": len(data),
                 "n_drugs": len(drugs), "sample": ", ".join(drugs[:3])})
    time.sleep(0.3)

df = pd.DataFrame(rows).sort_values("cpic_guidelines", ascending=False)
print(df.to_string(index=False))
df.to_csv("pharmacogene_cpic_coverage.csv", index=False)
```

### Workflow 2: Drug panel — CPIC prescribing rule lookup

**Goal:** Given a prescribed drug list, identify which have CPIC genotype-specific recommendations and surface the rule rows.

```python
import requests, pandas as pd, time

CPIC = "https://api.cpicpgx.org/v1"
drugs = ["warfarin", "clopidogrel", "codeine", "simvastatin",
         "metoprolol", "omeprazole", "azathioprine", "tacrolimus"]

rows = []
for name in drugs:
    drug = requests.get(f"{CPIC}/drug", params={"name": f"eq.{name}"}, timeout=15).json()
    if not drug:
        rows.append({"drug": name, "in_cpic": False, "n_recs": 0, "phenotypes": ""}); continue
    did = drug[0]["drugid"]
    recs = requests.get(f"{CPIC}/recommendation",
                        params={"drugid": f"eq.{did}"}, timeout=15).json()
    phens = sorted({f"{k}={v}" for rec in recs
                                  for k, v in (rec.get("phenotypes") or {}).items()})
    rows.append({"drug": name, "in_cpic": True, "n_recs": len(recs),
                 "phenotypes": "; ".join(phens[:3])})
    time.sleep(0.3)

df = pd.DataFrame(rows).sort_values(["in_cpic", "n_recs"], ascending=[False, False])
print(df.to_string(index=False))
```

### Workflow 3: Variant → drug interactions (rsID-driven)

**Goal:** Starting from a single rsID (e.g., SLCO1B1 *5 = rs4149056), find every clinical annotation that involves it.

The Data API does **not** accept rsID as a filter property. Use `POST /site/search` to discover related annotation IDs, then fetch each by ID.

```python
import requests

CLINPGX = "https://api.clinpgx.org/v1"
rsid = "rs4149056"

hits = requests.post(f"{CLINPGX}/site/search",
                     json={"query": rsid}, timeout=15).json()["data"]["hits"]
print(f"{rsid}: {len(hits)} hits")

# Filter hits that look like clinical annotations
ann_hits = [h for h in hits if h.get("name", "").lower().startswith("clinical annotation")]
print(f"Clinical-annotation hits: {len(ann_hits)}")
for h in ann_hits[:5]:
    print(f"  id={h['id']}  {h['name'][:90]}")

# Dereference one annotation by ID for full detail
if ann_hits:
    ann = requests.get(f"{CLINPGX}/data/clinicalAnnotation/{ann_hits[0]['id']}",
                       params={"view": "max"}, timeout=15).json()["data"]
    drugs = ", ".join(c["name"] for c in (ann.get("relatedChemicals") or []))
    print(f"\nFirst annotation:")
    print(f"  drugs: {drugs}")
    print(f"  level: {(ann.get('levelOfEvidence') or {}).get('term')}")
```

## Key Parameters

| Parameter                   | Module / Endpoint                              | Default | Range / Options                                          | Effect                                                                  |
| --------------------------- | ---------------------------------------------- | ------- | -------------------------------------------------------- | ----------------------------------------------------------------------- |
| `view`                      | all `/data/...`                                | `base`  | `base`, `min`, `max`                                     | Field detail level; `max` includes all nested arrays (slow but complete) |
| `relatedChemicals.name`     | `clinicalAnnotation`, `variantAnnotation`, `guidelineAnnotation`, `label`, `pathway` | — | lowercase generic drug name                              | Filter records related to a drug                                        |
| `relatedGenes.symbol`       | `guidelineAnnotation`, `pathway`               | —       | HGNC gene symbol                                         | Filter records related to a gene (not available on `clinicalAnnotation`) |
| `levelOfEvidence.term`      | `clinicalAnnotation`                           | —       | `"1A"`, `"1B"`, `"2A"`, `"2B"`, `"3"`, `"4"`             | Minimum evidence level                                                  |
| `source`                    | `guidelineAnnotation`, `label`                 | —       | `CPIC`, `DPWG`, `FDA`, `EMA`, `HCSC`, `PMDA`, `Swissmedic` | Issuing body                                                            |
| `symbol`                    | `data/gene`                                    | —       | HGNC gene symbol                                         | Gene record lookup                                                      |
| `name`                      | `data/drug`, `data/variant`                    | —       | drug name or rsID                                        | Record lookup by canonical name                                         |
| CPIC `column=eq.value`      | all `api.cpicpgx.org/v1/...`                   | —       | PostgREST equality                                       | Filter by exact match                                                   |
| CPIC `phenotypes=cs.{json}` | `recommendation`                               | —       | JSON-encoded jsonb subset                                | Filter by phenotype containment (must URL-encode if special chars)      |

## Best Practices

1. **Resolve PA identifiers once.** Never hand-construct ClinPGx PA IDs. Call `data/{type}?{symbol|name}=...` (or `site/search`) once and cache the returned `id` for reuse — `gene/PA128` for CYP2D6, `drug/PA449088` for clopidogrel, `variant/PA166154579` for rs4149056.

2. **Pick the right host for the question.** Use ClinPGx for `what is annotated` and CPIC for `what to prescribe`. Trying to derive genotype-specific recommendations from ClinPGx alone misses the structured `recommendation.phenotypes` rows.

3. **Filter by evidence level upfront** when building clinical workflows. `levelOfEvidence.term=1A` returns 312 actionable annotations across all of ClinPGx; Level 3/4 records are exploratory and shouldn't drive prescribing.

4. **Don't filter `clinicalAnnotation` by gene — filter by `guidelineAnnotation`** with `relatedGenes.symbol`. The `clinicalAnnotation` endpoint has no working gene property and returns HTTP 400 for any attempt.

5. **Use `view=base` for bulk filters, `view=max` for single-record drill-downs.** A list query with `view=max` can time out or hit 429; the difference is roughly 5–10× payload size.

6. **Throttle the ClinPGx host.** Insert `time.sleep(0.3)` between sequential queries in loops; the API returns occasional HTTP 429s on tight loops. CPIC tolerates faster iteration.

7. **URL-encode `cs.{...}` jsonb filters** when phenotype values contain spaces or special characters. `requests.get(..., params={"phenotypes": 'cs.{"CYP2C19":"Poor Metabolizer"}'})` works because `requests` does the encoding; a manual URL string needs `urllib.parse.quote`.

## Common Recipes

### Recipe 1 — Free-text discovery via site/search

When to use: you have an arbitrary string (rsID, drug name, gene, allele) and want to find related ClinPGx records without knowing which endpoint to hit.

```python
import requests
r = requests.post("https://api.clinpgx.org/v1/site/search",
                  json={"query": "VKORC1 warfarin"}, timeout=15)
hits = r.json()["data"]["hits"]
for h in hits[:10]:
    print(f"  {h.get('id'):>15}  {h.get('name','')[:80]}")
```

### Recipe 2 — Top drugs by Level 1A annotation count

When to use: build a leaderboard of the most actionable PGx drugs.

```python
import requests, pandas as pd
data = requests.get("https://api.clinpgx.org/v1/data/clinicalAnnotation",
                    params={"levelOfEvidence.term": "1A", "view": "base"},
                    timeout=30).json()["data"]
counts = {}
for ann in data:
    for c in ann.get("relatedChemicals") or []:
        counts[c["name"]] = counts.get(c["name"], 0) + 1
df = pd.DataFrame(sorted(counts.items(), key=lambda x: -x[1]),
                  columns=["drug", "n_1A_annotations"]).head(15)
print(df.to_string(index=False))
```

### Recipe 3 — Patient genotype → drug recommendations

When to use: given a phenotype call from a PGx test, surface every CPIC recommendation row.

```python
import requests
CPIC = "https://api.cpicpgx.org/v1"

genotype = {"CYP2C19": "Poor Metabolizer"}
drug = "clopidogrel"

did = requests.get(f"{CPIC}/drug", params={"name": f"eq.{drug}"}).json()[0]["drugid"]
import json
recs = requests.get(f"{CPIC}/recommendation",
                    params={"drugid": f"eq.{did}",
                            "phenotypes": f"cs.{json.dumps(genotype)}"}).json()
for rec in recs:
    print(f"[{rec['classification']}] {rec['drugrecommendation']}")
    print(f"  implications: {rec['implications']}")
```

### Recipe 4 — Robust session with retry

When to use: long-running loops over many genes / drugs / variants.

```python
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

s = requests.Session()
s.headers.update({"Accept": "application/json"})
s.mount("https://", HTTPAdapter(max_retries=Retry(
    total=4, backoff_factor=1.0,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["GET", "POST"])))

r = s.get("https://api.clinpgx.org/v1/data/gene",
          params={"symbol": "CYP2D6", "view": "base"}, timeout=20)
r.raise_for_status()
print(r.json()["data"][0]["name"])
```

## Troubleshooting

| Problem                                                                                   | Cause                                                                                              | Solution                                                                                                                            |
| ----------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| HTTP 404/405 on `https://api.pharmgkb.org/v1/...`                                         | Old PharmGKB host is dead; the service rebranded to ClinPGx in 2024                                | Migrate to `https://api.clinpgx.org/v1/...`. Old `/clinicalAnnotation?gene=X` is now `data/clinicalAnnotation` with different filters. |
| `{"status":"fail","data":{"errors":[{"message":"No such property: 'gene'"}]}}`            | `data/clinicalAnnotation` does **not** accept `gene=` or `relatedGenes.symbol=`                    | Use `data/guidelineAnnotation?relatedGenes.symbol=X` for gene-driven access, or `?relatedChemicals.name=Y` for drug-driven.        |
| `{"status":"fail","data":{"errors":[{"message":"Missing criteria."}]}}`                   | A `data/{type}` list query has no filter and no ID                                                 | Add at least one filter (`name=`, `symbol=`, `relatedChemicals.name=`, …) or fetch by ID via `data/{type}/{paId}`.                  |
| HTTP 405 on `GET /site/search?query=...`                                                  | `site/search` only accepts POST with a JSON body                                                   | Use `requests.post(url, json={"query": "..."})`.                                                                                    |
| HTTP 429 mid-loop                                                                         | Hit ClinPGx rate limit                                                                             | Insert `time.sleep(0.3–0.5)` between calls; use the Retry session in Recipe 4.                                                      |
| HTTP 400 on `https://api.cpicpgx.org/v1/recommendation?phenotypes=cs.{...}`               | The `cs.` JSON wasn't URL-encoded                                                                  | Pass via `requests` `params={"phenotypes": 'cs.{"CYP2C19":"Poor Metabolizer"}'}` (auto-encoded) or `urllib.parse.quote` manually.    |
| Empty `data` list for an obviously-real drug                                              | Drug name mismatch (brand vs. generic; capitalization)                                             | Try lowercase generic name; fall back to `POST /site/search` to fan out and find the canonical PA ID.                              |
| `data/variant?name=rs...` returns 1 record but `data/clinicalAnnotation?location.name=rs...` returns 404 | rsID is stored under `location.displayName`/`location.rsid`, not exposed as a filterable property | Use `site/search` to discover annotation IDs by rsID, then dereference each with `data/clinicalAnnotation/{id}`. (Workflow 3.)      |

## Related Skills

- `clinvar-database` — germline pathogenicity / clinical significance for variants found in PharmGKB (complementary; ClinVar is disease-focused, ClinPGx is drug-response-focused)
- `opentargets-database` — drug-target associations and safety signals overlapping ClinPGx pharmacogene targets
- `chembl-database-bioactivity` — bioactivity and binding data for the drugs annotated in ClinPGx
- `cosmic-database` — somatic cancer mutations and tumor-specific PGx (orthogonal to germline PGx covered here)

## References

- [ClinPGx (formerly PharmGKB) website](https://www.clinpgx.org/) — Database front end; web links match the `data/{type}/{paId}` URL shape
- [ClinPGx REST API documentation](https://www.clinpgx.org/page/webResources) — Official endpoint reference, `data/...` and `site/search` schemas
- [CPIC API documentation](https://api.cpicpgx.org/) — Swagger UI for the PostgREST companion API
- [CPIC guidelines](https://cpicpgx.org/guidelines/) — Source of `recommendation` rows; canonical genotype-prescribing oracle
- [Relling & Klein (2011) Nature Reviews Drug Discovery — PharmGKB foundational paper](https://doi.org/10.1038/nrd3499)
- [Whirl-Carrillo et al. (2021) Clin Pharmacol Ther — PharmGKB data architecture update](https://doi.org/10.1002/cpt.2350)
