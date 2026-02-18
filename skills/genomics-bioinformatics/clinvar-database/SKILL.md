---
name: "clinvar-database"
description: "Query NCBI ClinVar via E-utilities REST API for clinical significance, pathogenicity classifications, and disease associations of genetic variants. Search by gene, rsID, condition, or review status. Returns structured variant records: ClinSig, submitter data, conditions, HGVS expressions. For GWAS associations use gwas-database; for variant consequence prediction use Ensembl VEP."
license: "CC0-1.0"
---

# ClinVar Clinical Variants Database

## Overview

ClinVar is NCBI's public archive of interpretations of variants submitted by clinical laboratories, researchers, and expert panels. It contains 2M+ variants with clinical significance classifications (Pathogenic, Likely Pathogenic, VUS, Likely Benign, Benign) for over 6,000 conditions. Access is free and requires no authentication via NCBI E-utilities.

## When to Use

- Checking whether a specific variant (rsID, HGVS, or genomic position) has a clinical significance classification
- Retrieving all pathogenic/likely-pathogenic variants in a gene of interest
- Identifying conflicting interpretations between submitting laboratories
- Pulling condition/phenotype associations for a variant (MIM, MeSH, HPO terms)
- Building variant filtering pipelines that prioritize clinically actionable variants
- For somatic cancer variants, also check `cosmic-database`; for GWAS associations use `gwas-database`

## Prerequisites

- **Python packages**: `requests`, `xml.etree.ElementTree` (stdlib)
- **Data requirements**: gene symbols, rsIDs, HGVS strings, or ClinVar Variation IDs
- **Environment**: internet connection; NCBI Entrez email required (set `email` parameter)
- **Rate limits**: 3 requests/second unauthenticated; 10/second with API key (free at https://www.ncbi.nlm.nih.gov/account/)

```bash
pip install requests
# No additional packages required; xml.etree is part of Python stdlib
```

## Quick Start

```python
import requests

EMAIL = "your@email.com"  # required by NCBI policy

def clinvar_search(query, retmax=10):
    """Search ClinVar and return a list of ClinVar Variation IDs."""
    r = requests.get(
        "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi",
        params={"db": "clinvar", "term": query, "retmax": retmax,
                "retmode": "json", "email": EMAIL}
    )
    r.raise_for_status()
    return r.json()["esearchresult"]["idlist"]

# Find pathogenic BRCA1 variants
ids = clinvar_search("BRCA1[gene] AND pathogenic[clinsig]", retmax=5)
print(f"Found variation IDs: {ids}")
```

## Core API

### Query 1: Search Variants by Gene and Clinical Significance

Use ESearch to find ClinVar Variation IDs matching a structured query.

```python
import requests

EMAIL = "your@email.com"
BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

def esearch(query, retmax=200):
    r = requests.get(f"{BASE}/esearch.fcgi",
                     params={"db": "clinvar", "term": query,
                             "retmax": retmax, "retmode": "json", "email": EMAIL})
    r.raise_for_status()
    result = r.json()["esearchresult"]
    return result["idlist"], int(result["count"])

# Gene-specific pathogenic variants
ids, total = esearch("BRCA2[gene] AND (pathogenic[clinsig] OR likely pathogenic[clinsig])")
print(f"Pathogenic/LP BRCA2 variants: {total} total, retrieved {len(ids)}")
print(f"First 5 IDs: {ids[:5]}")
```

```python
# By rsID
ids, _ = esearch("rs80357906[rs]")
print(f"Variant IDs for rs80357906: {ids}")

# By condition name
ids, total = esearch("breast cancer[dis] AND pathogenic[clinsig]")
print(f"Pathogenic variants for breast cancer: {total}")
```

### Query 2: Fetch Variant Summary Records

Retrieve structured summary data (JSON) for a list of Variation IDs.

```python
import requests, json

EMAIL = "your@email.com"
BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

def esummary(ids):
    """Fetch ESummary records for a list of ClinVar variation IDs."""
    r = requests.post(f"{BASE}/esummary.fcgi",
                      data={"db": "clinvar", "id": ",".join(ids),
                            "retmode": "json", "email": EMAIL})
    r.raise_for_status()
    return r.json()["result"]

ids, _ = esearch_func = lambda q: requests.get(
    f"{BASE}/esearch.fcgi",
    params={"db": "clinvar", "term": q, "retmax": 5, "retmode": "json", "email": EMAIL}
).json()["esearchresult"]["idlist"]

# Manual example with known IDs
sample_ids = ["12375", "17684", "54270"]
result = esummary(sample_ids)

for vid in result.get("uids", []):
    rec = result[vid]
    print(f"\nVariation {vid}: {rec.get('title')}")
    print(f"  ClinSig  : {rec.get('clinical_significance', {}).get('description')}")
    print(f"  Review   : {rec.get('clinical_significance', {}).get('review_status')}")
    print(f"  Gene     : {rec.get('genes', [{}])[0].get('symbol')}")
```

### Query 3: Fetch Full XML Records

Retrieve the complete variant record in XML for detailed submitter and condition data.

```python
import requests
import xml.etree.ElementTree as ET

EMAIL = "your@email.com"
BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

def efetch_xml(ids):
    r = requests.post(f"{BASE}/efetch.fcgi",
                      data={"db": "clinvar", "id": ",".join(ids),
                            "rettype": "clinvarset", "retmode": "xml", "email": EMAIL})
    r.raise_for_status()
    return ET.fromstring(r.text)

root = efetch_xml(["12375"])

# Parse clinical assertions
for ca in root.iter("ClinVarAssertion"):
    clin_sig = ca.find(".//ClinicalSignificance/Description")
    submitter = ca.find(".//ClinVarSubmissionID")
    if clin_sig is not None and submitter is not None:
        print(f"Submitter: {submitter.get('submitterDate', 'n/a')} | ClinSig: {clin_sig.text}")
```

### Query 4: ClinVar FTP Bulk Data

For large-scale queries, download and parse the full variant summary file.

```python
import urllib.request
import gzip, csv, io

# Full summary (tab-separated, ~300 MB compressed)
URL = "https://ftp.ncbi.nlm.nih.gov/pub/clinvar/tab_delimited/variant_summary.txt.gz"

# Stream and parse without full download
with urllib.request.urlopen(URL) as resp:
    with gzip.open(resp, "rt", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        pathogenic_brca1 = []
        for row in reader:
            if row["GeneSymbol"] == "BRCA1" and "Pathogenic" in row["ClinicalSignificance"]:
                pathogenic_brca1.append({
                    "name": row["Name"],
                    "clinsig": row["ClinicalSignificance"],
                    "condition": row["PhenotypeList"],
                    "rsid": row["RS# (dbSNP)"],
                })
        print(f"Pathogenic BRCA1 variants: {len(pathogenic_brca1)}")
        for v in pathogenic_brca1[:3]:
            print(f"  {v['name']} | {v['clinsig']} | rs{v['rsid']}")
```

### Query 5: Review Status and Conflicting Interpretations

Filter variants by review status (evidence quality) and find conflicts.

```python
import requests

EMAIL = "your@email.com"
BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

# Stars correspond to review levels:
# 0 = no assertion criteria, 1 = criteria provided (single),
# 2 = criteria provided (multiple), 3 = expert panel, 4 = practice guideline

def search_by_review_stars(gene, min_stars=2):
    """Search for variants with at least min_stars review status."""
    star_terms = {1: "criteria provided, single submitter",
                  2: "criteria provided, multiple submitters, no conflicts",
                  3: "reviewed by expert panel",
                  4: "practice guideline"}
    terms = [f'"{star_terms[s]}"[review status]' for s in range(min_stars, 5) if s in star_terms]
    query = f"{gene}[gene] AND (" + " OR ".join(terms) + ")"
    r = requests.get(f"{BASE}/esearch.fcgi",
                     params={"db": "clinvar", "term": query, "retmax": 100,
                             "retmode": "json", "email": EMAIL})
    return r.json()["esearchresult"]

result = search_by_review_stars("BRCA1", min_stars=3)
print(f"Expert-reviewed BRCA1 variants: {result['count']}")
```

### Query 6: Variant-to-Condition Mapping

Extract condition (phenotype) data from ClinVar records.

```python
import requests, json

EMAIL = "your@email.com"
BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

def get_conditions(variation_ids):
    """Return condition data for a list of ClinVar variation IDs."""
    r = requests.post(f"{BASE}/esummary.fcgi",
                      data={"db": "clinvar", "id": ",".join(variation_ids),
                            "retmode": "json", "email": EMAIL})
    r.raise_for_status()
    result = r.json()["result"]
    conditions = {}
    for vid in result.get("uids", []):
        rec = result[vid]
        trait_set = rec.get("trait_set", [])
        conditions[vid] = [t.get("trait_name") for t in trait_set]
    return conditions

sample_ids = ["12375", "17684", "54270"]
cond_map = get_conditions(sample_ids)
for vid, conds in cond_map.items():
    print(f"Variation {vid}: {', '.join(conds)}")
```

## Key Concepts

### ClinVar Variation ID vs. rsID

ClinVar assigns its own stable Variation ID (integer) to each interpreted variant record. This differs from dbSNP rsIDs. A single rsID can correspond to multiple ClinVar Variation IDs if different alleles or interpretations are submitted separately.

### Review Stars and Evidence Quality

ClinVar's "review status" encodes the level of evidence:
- **0 stars**: No assertion criteria provided
- **1 star**: Criteria provided, single submitter
- **2 stars**: Multiple submitters, no conflict
- **3 stars**: Reviewed by expert panel (e.g., ENIGMA, ClinGen)
- **4 stars**: Practice guideline

## Common Workflows

### Workflow 1: Gene Pathogenicity Report

**Goal**: Retrieve all high-confidence pathogenic variants in a gene and export to CSV.

```python
import requests, json, time, pandas as pd

EMAIL = "your@email.com"
BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

def search_gene_pathogenic(gene, clinsig="pathogenic"):
    query = f"{gene}[gene] AND {clinsig}[clinsig]"
    r = requests.get(f"{BASE}/esearch.fcgi",
                     params={"db": "clinvar", "term": query, "retmax": 500,
                             "retmode": "json", "email": EMAIL})
    return r.json()["esearchresult"]["idlist"]

def fetch_summaries(ids):
    records = []
    for i in range(0, len(ids), 100):
        batch = ids[i:i+100]
        r = requests.post(f"{BASE}/esummary.fcgi",
                          data={"db": "clinvar", "id": ",".join(batch),
                                "retmode": "json", "email": EMAIL})
        result = r.json()["result"]
        for vid in result.get("uids", []):
            rec = result[vid]
            clinsig = rec.get("clinical_significance", {})
            records.append({
                "variation_id": vid,
                "name": rec.get("title"),
                "clinsig": clinsig.get("description"),
                "review_status": clinsig.get("review_status"),
                "gene": ",".join(g.get("symbol", "") for g in rec.get("genes", [])),
                "conditions": "; ".join(t.get("trait_name", "") for t in rec.get("trait_set", [])),
            })
        time.sleep(0.15)
    return records

gene = "BRCA1"
ids = search_gene_pathogenic(gene)
print(f"Found {len(ids)} pathogenic variants in {gene}")

records = fetch_summaries(ids)
df = pd.DataFrame(records)
df.to_csv(f"{gene}_pathogenic_variants.csv", index=False)
print(f"Saved {len(df)} records → {gene}_pathogenic_variants.csv")
print(df[["name", "clinsig", "review_status"]].head())
```

### Workflow 2: Variant Classification Check

**Goal**: Check ClinVar status for a list of user-provided rsIDs or HGVS notations.

```python
import requests, time, pandas as pd

EMAIL = "your@email.com"
BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

variants = ["rs80357906", "rs80357220", "rs28897672"]
results = []

for rsid in variants:
    r = requests.get(f"{BASE}/esearch.fcgi",
                     params={"db": "clinvar", "term": f"{rsid}[rs]",
                             "retmax": 5, "retmode": "json", "email": EMAIL})
    ids = r.json()["esearchresult"]["idlist"]
    if not ids:
        results.append({"rsid": rsid, "variation_id": None, "clinsig": "Not in ClinVar"})
        continue

    r2 = requests.post(f"{BASE}/esummary.fcgi",
                       data={"db": "clinvar", "id": ",".join(ids[:1]),
                             "retmode": "json", "email": EMAIL})
    rec = r2.json()["result"][ids[0]]
    clinsig = rec.get("clinical_significance", {})
    results.append({
        "rsid": rsid,
        "variation_id": ids[0],
        "clinsig": clinsig.get("description", "Unknown"),
        "review_status": clinsig.get("review_status"),
    })
    time.sleep(0.15)

df = pd.DataFrame(results)
print(df.to_string(index=False))
```

## Key Parameters

| Parameter | Module | Default | Range / Options | Effect |
|-----------|--------|---------|-----------------|--------|
| `retmax` | ESearch | `20` | `1`–`10000` | Max records returned per query |
| `retmode` | ESearch/ESummary | `"xml"` | `"json"`, `"xml"` | Response format |
| `rettype` | EFetch | `"clinvarset"` | `"clinvarset"`, `"vcv"` | Record type for XML fetch |
| `clinsig` query field | ESearch | — | `"pathogenic"`, `"likely pathogenic"`, `"VUS"` | Filter by clinical significance |
| `review status` query field | ESearch | — | 0–4 star terms | Filter by evidence quality |
| `email` | All | required | valid email | NCBI policy; prevents blocking |

## Best Practices

1. **Always set `email`**: NCBI requires an email in all E-utility calls for rate-limit attribution and policy compliance.

2. **Use FTP bulk download for large queries**: For more than ~1000 variants, download `variant_summary.txt.gz` from the ClinVar FTP rather than looping over EFetch — it's faster and avoids rate limits.

3. **Filter by review status**: Automated pipelines should filter to ≥2-star variants to reduce noise from single-submitter assertions without peer review.

4. **Use API key for production**: Register at https://www.ncbi.nlm.nih.gov/account/ to get a free API key (`api_key` parameter) and triple your rate limit (3 → 10 req/s).

5. **Handle VUS separately**: "Conflicting interpretations of pathogenicity" is its own ClinSig category — don't combine it with "VUS" in filters; they have different implications for clinical decision-making.

## Common Recipes

### Recipe: Check if rsID Is in ClinVar

When to use: Quick lookup for a single known variant.

```python
import requests

EMAIL = "your@email.com"
rsid = "rs80357906"

r = requests.get(
    "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi",
    params={"db": "clinvar", "term": f"{rsid}[rs]",
            "retmax": 1, "retmode": "json", "email": EMAIL}
)
count = int(r.json()["esearchresult"]["count"])
print(f"{rsid}: {'found' if count else 'NOT'} in ClinVar ({count} records)")
```

### Recipe: Download Variant Summary TSV

When to use: Bulk analysis — load entire ClinVar into a pandas DataFrame.

```python
import pandas as pd

url = "https://ftp.ncbi.nlm.nih.gov/pub/clinvar/tab_delimited/variant_summary.txt.gz"
# Only human GRCh38 pathogenic variants
df = pd.read_csv(url, sep="\t", compression="gzip",
                 usecols=["#AlleleID", "Name", "GeneSymbol", "ClinicalSignificance",
                          "ReviewStatus", "PhenotypeList", "Assembly", "RS# (dbSNP)"])
df = df[(df["Assembly"] == "GRCh38") & (df["ClinicalSignificance"].str.contains("Pathogenic", na=False))]
print(f"Pathogenic variants (GRCh38): {len(df)}")
df.to_csv("clinvar_pathogenic_grch38.csv", index=False)
```

### Recipe: Search by OMIM Disease ID

When to use: Find all ClinVar variants associated with a specific OMIM condition.

```python
import requests

EMAIL = "your@email.com"
omim_id = "604370"  # BRCA1-associated breast-ovarian cancer

r = requests.get(
    "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi",
    params={"db": "clinvar", "term": f"{omim_id}[MIM]",
            "retmax": 20, "retmode": "json", "email": EMAIL}
)
result = r.json()["esearchresult"]
print(f"Variants for OMIM {omim_id}: {result['count']} total")
print(f"First IDs: {result['idlist'][:5]}")
```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `HTTP 429` or no response | Rate limit exceeded | Add `time.sleep(0.35)` between requests; use API key |
| Empty `idlist` for rsID query | rsID not indexed in ClinVar | Try HGVS notation or gene+position query instead |
| Missing `clinsig` in summary | Variant has no interpretation | Check `review_status`; "no interpretation for the single variant" means no ClinSig yet |
| XML parse error in EFetch | Incomplete response (timeout) | Set `requests.get(..., timeout=30)` and retry once |
| Conflicting results for same rsID | Multiple submissions with different interpretations | Group by `review_status` and prefer higher-star entries |
| FTP download fails | Large file / slow connection | Use `pandas.read_csv` with `chunksize=100000` or pre-filter with `grep` |

## Related Skills

- `gwas-database` — GWAS Catalog for population-level SNP-trait associations (complement to ClinVar's clinical assertions)
- `ensembl-database` — Ensembl VEP for predicting variant consequences without requiring prior clinical curation
- `cosmic-database` — Somatic cancer variant database (complementary to ClinVar's germline focus)
- `pubmed-database` — Retrieve supporting publications cited in ClinVar submissions

## References

- [ClinVar official site](https://www.ncbi.nlm.nih.gov/clinvar/) — Browse and download ClinVar data
- [NCBI E-utilities documentation](https://www.ncbi.nlm.nih.gov/books/NBK25499/) — Full E-utilities API reference
- [ClinVar FTP downloads](https://ftp.ncbi.nlm.nih.gov/pub/clinvar/) — Bulk data files (variant_summary.txt.gz, etc.)
- [ClinVar data model](https://www.ncbi.nlm.nih.gov/clinvar/docs/help/) — Understanding review status stars and ClinSig categories
