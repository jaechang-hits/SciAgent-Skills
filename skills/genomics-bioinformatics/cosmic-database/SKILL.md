---
name: "cosmic-database"
description: "Query COSMIC for cancer somatic mutations, gene census, mutational signatures, drug resistance variants. REST API v3.1 supports gene/sample/variant queries; free registration. For germline use clinvar-database; for drug-target data use opentargets-database or chembl-database-bioactivity."
license: "CC-BY-NC-SA-4.0"
---

# COSMIC Somatic Cancer Mutations Database

## Overview

COSMIC (Catalogue Of Somatic Mutations In Cancer) is the world's largest expert-curated database of somatic mutations in cancer, covering 6.7M+ coding mutations, 40,000+ cancer samples, 19,000+ genes across all cancer types. It includes the Cancer Gene Census (critical cancer genes), mutational signatures (SBS, DBS, ID), drug resistance variants, copy number data, gene expression, and methylation. The REST API v3.1 enables programmatic queries; most features are freely accessible after registration.

## When to Use

- Checking whether a specific somatic variant in a cancer gene is annotated in COSMIC (frequency, cancer type distribution)
- Retrieving all somatic mutations in a gene of interest across COSMIC cancer samples
- Accessing COSMIC Cancer Gene Census classifications (Tier 1/2, role: oncogene/TSG/fusion)
- Looking up mutational signature attributions for samples or cancer types
- Identifying drug resistance variants (pharmacogenomic data) from COSMIC drug resistance database
- Building cancer driver gene lists for bioinformatic pipelines
- For germline/inherited variants use `clinvar-database`; for drug-target associations use `opentargets-database`

## Prerequisites

- **Python packages**: `requests`, `pandas`
- **Data requirements**: gene symbols (HGNC), COSMIC mutation IDs (COSM), sample IDs, or genomic coordinates
- **Environment**: internet connection; free account registration at https://cancer.sanger.ac.uk/cosmic/register
- **Rate limits**: authenticated requests only; 10 requests/second max; API key required

```bash
pip install requests pandas
# Register at https://cancer.sanger.ac.uk/cosmic/register to obtain API credentials
```

## Quick Start

```python
import requests
import base64

# COSMIC API requires base64-encoded email:password authentication
EMAIL = "your_registered@email.com"
PASSWORD = "your_password"
token = base64.b64encode(f"{EMAIL}:{PASSWORD}".encode()).decode()

BASE = "https://cancer.sanger.ac.uk/cosmic/api"
HEADERS = {"Authorization": f"Basic {token}"}

# Get mutations for KRAS gene
r = requests.get(f"{BASE}/mutations",
                 headers=HEADERS,
                 params={"gene_name": "KRAS", "limit": 5})
r.raise_for_status()
data = r.json()
print(f"Total KRAS mutations: {data['meta']['total']}")
for m in data["data"][:3]:
    print(f"  {m['mutation_id']:15s} AA: {m.get('mutation_aa')} | Cancer: {m.get('primary_site')}")
```

## Core API

### Query 1: Gene Mutations Search

Retrieve all COSMIC somatic mutations for a gene, with cancer type and amino acid change.

```python
import requests, base64, pandas as pd

EMAIL = "your@email.com"
PASSWORD = "your_password"
token = base64.b64encode(f"{EMAIL}:{PASSWORD}".encode()).decode()

BASE = "https://cancer.sanger.ac.uk/cosmic/api"
HEADERS = {"Authorization": f"Basic {token}"}

def get_gene_mutations(gene, limit=100, cancer_site=None):
    params = {"gene_name": gene, "limit": limit}
    if cancer_site:
        params["primary_site"] = cancer_site
    r = requests.get(f"{BASE}/mutations", headers=HEADERS, params=params)
    r.raise_for_status()
    return r.json()

data = get_gene_mutations("TP53", limit=20)
print(f"Total TP53 mutations in COSMIC: {data['meta']['total']}")

rows = []
for m in data["data"][:10]:
    rows.append({
        "mutation_id": m.get("mutation_id"),
        "mutation_aa": m.get("mutation_aa"),
        "mutation_cds": m.get("mutation_cds"),
        "primary_site": m.get("primary_site"),
        "histology": m.get("primary_histology"),
        "count": m.get("count"),
    })
df = pd.DataFrame(rows)
print(df.head())
```

```python
# Filter by cancer site
data_lung = get_gene_mutations("TP53", cancer_site="lung", limit=20)
print(f"\nTP53 mutations in lung cancer: {data_lung['meta']['total']}")
```

### Query 2: Cancer Gene Census

Retrieve the COSMIC Cancer Gene Census — classified cancer driver genes.

```python
import requests, base64, pandas as pd

EMAIL = "your@email.com"
PASSWORD = "your_password"
token = base64.b64encode(f"{EMAIL}:{PASSWORD}".encode()).decode()

BASE = "https://cancer.sanger.ac.uk/cosmic/api"
HEADERS = {"Authorization": f"Basic {token}"}

r = requests.get(f"{BASE}/genes", headers=HEADERS, params={"limit": 100})
r.raise_for_status()
data = r.json()
print(f"Total genes in COSMIC: {data['meta']['total']}")

# Get Cancer Gene Census genes
r_cgc = requests.get(f"{BASE}/genes",
                     headers=HEADERS,
                     params={"cgc_tier": "1", "limit": 50})
cgc_data = r_cgc.json()
print(f"\nCGC Tier 1 genes: {cgc_data['meta']['total']}")

rows = []
for g in cgc_data["data"][:15]:
    rows.append({
        "gene": g.get("gene_name"),
        "tier": g.get("cgc_tier"),
        "role": g.get("role_in_cancer"),
        "mutation_types": g.get("mutation_types"),
        "tumour_types": str(g.get("tumour_types_somatic", []))[:80],
    })
df = pd.DataFrame(rows)
print(df.to_string(index=False))
```

### Query 3: Specific Mutation Lookup

Retrieve details for a known COSMIC mutation ID (COSM…).

```python
import requests, base64

EMAIL = "your@email.com"
PASSWORD = "your_password"
token = base64.b64encode(f"{EMAIL}:{PASSWORD}".encode()).decode()

BASE = "https://cancer.sanger.ac.uk/cosmic/api"
HEADERS = {"Authorization": f"Basic {token}"}

# KRAS G12D mutation
mutation_id = "COSM521"
r = requests.get(f"{BASE}/mutations/{mutation_id}", headers=HEADERS)
r.raise_for_status()
m = r.json()

print(f"Mutation ID : {m.get('mutation_id')}")
print(f"Gene        : {m.get('gene_name')}")
print(f"AA change   : {m.get('mutation_aa')}")
print(f"CDS change  : {m.get('mutation_cds')}")
print(f"Substitution: {m.get('mutation_description')}")
print(f"Count       : {m.get('count')} samples")
print(f"Cancer types: {str(m.get('cancer_types', []))[:100]}")
```

### Query 4: Sample-Level Mutation Data

Retrieve all somatic mutations for a specific cancer sample.

```python
import requests, base64, pandas as pd

EMAIL = "your@email.com"
PASSWORD = "your_password"
token = base64.b64encode(f"{EMAIL}:{PASSWORD}".encode()).decode()

BASE = "https://cancer.sanger.ac.uk/cosmic/api"
HEADERS = {"Authorization": f"Basic {token}"}

# Search for a specific sample
r = requests.get(f"{BASE}/samples",
                 headers=HEADERS,
                 params={"primary_site": "breast", "limit": 5})
r.raise_for_status()
samples = r.json()["data"]
print(f"Example breast cancer samples:")
for s in samples[:3]:
    print(f"  {s.get('sample_id')}: {s.get('sample_name')} | {s.get('primary_histology')}")

# Get mutations for a specific sample
if samples:
    sample_id = samples[0]["sample_id"]
    r2 = requests.get(f"{BASE}/samples/{sample_id}/mutations", headers=HEADERS)
    if r2.ok:
        muts = r2.json()["data"]
        print(f"\nMutations in sample {sample_id}: {len(muts)}")
        for m in muts[:5]:
            print(f"  {m.get('gene_name'):10s} {m.get('mutation_aa')}")
```

### Query 5: Mutational Signatures

Retrieve COSMIC mutational signature data for cancer types.

```python
import requests, base64, pandas as pd

EMAIL = "your@email.com"
PASSWORD = "your_password"
token = base64.b64encode(f"{EMAIL}:{PASSWORD}".encode()).decode()

BASE = "https://cancer.sanger.ac.uk/cosmic/api"
HEADERS = {"Authorization": f"Basic {token}"}

# List available mutational signatures
r = requests.get(f"{BASE}/signatures", headers=HEADERS)
r.raise_for_status()
sigs = r.json()["data"]
print(f"COSMIC mutational signatures: {len(sigs)}")
for s in sigs[:5]:
    print(f"  {s.get('signature_name')}: {s.get('aetiology', '')[:80]}")
```

```python
# Get signature attributions by cancer type
r2 = requests.get(f"{BASE}/signatures/attributions",
                  headers=HEADERS,
                  params={"cancer_type": "Breast", "limit": 10})
if r2.ok:
    attributions = r2.json()["data"]
    for a in attributions[:5]:
        print(f"  {a.get('signature_name')}: {a.get('attribution_proportion'):.2%} in breast cancer")
```

### Query 6: Drug Resistance Variants

Query the COSMIC drug resistance database for variants conferring drug resistance.

```python
import requests, base64, pandas as pd

EMAIL = "your@email.com"
PASSWORD = "your_password"
token = base64.b64encode(f"{EMAIL}:{PASSWORD}".encode()).decode()

BASE = "https://cancer.sanger.ac.uk/cosmic/api"
HEADERS = {"Authorization": f"Basic {token}"}

# Get drug resistance variants
r = requests.get(f"{BASE}/resistance_mutations",
                 headers=HEADERS,
                 params={"gene": "EGFR", "limit": 20})
if r.ok:
    data = r.json()
    print(f"EGFR drug resistance variants: {data['meta'].get('total', 'n/a')}")
    for v in data.get("data", [])[:5]:
        print(f"  {v.get('mutation_aa'):20s} Drug: {v.get('drug')} | Resistance: {v.get('resistance_type')}")
else:
    print(f"Drug resistance API: {r.status_code} - endpoint may require specific access level")
```

## Key Concepts

### Cancer Gene Census Tiers

COSMIC's Cancer Gene Census classifies genes into:
- **Tier 1**: Well-established cancer drivers with documented mutations and molecular mechanisms in cancer
- **Tier 2**: Genes with strong evidence for roles in cancer but less functional characterization

### Mutation ID Stability

COSMIC mutation IDs (COSM…) are stable identifiers for specific amino acid changes in a gene. The same COSM ID appears across all samples with that mutation, allowing cross-study comparison.

## Common Workflows

### Workflow 1: Gene Hotspot Mutation Analysis

**Goal**: Identify the most frequently occurring somatic mutations in a cancer gene.

```python
import requests, base64, pandas as pd
from collections import Counter

EMAIL = "your@email.com"
PASSWORD = "your_password"
token = base64.b64encode(f"{EMAIL}:{PASSWORD}".encode()).decode()

BASE = "https://cancer.sanger.ac.uk/cosmic/api"
HEADERS = {"Authorization": f"Basic {token}"}

def get_all_gene_mutations(gene, max_records=1000):
    """Paginate through all COSMIC mutations for a gene."""
    all_muts = []
    skip = 0
    limit = 200
    while len(all_muts) < max_records:
        r = requests.get(f"{BASE}/mutations",
                         headers=HEADERS,
                         params={"gene_name": gene, "limit": limit, "skip": skip})
        r.raise_for_status()
        batch = r.json()["data"]
        if not batch:
            break
        all_muts.extend(batch)
        total = r.json()["meta"]["total"]
        skip += limit
        if skip >= total:
            break
    return all_muts

# Get hotspots for KRAS
mutations = get_all_gene_mutations("KRAS", max_records=500)
print(f"Retrieved {len(mutations)} KRAS somatic mutations")

# Rank by amino acid change frequency
aa_counter = Counter(m["mutation_aa"] for m in mutations if m.get("mutation_aa"))
hotspots = pd.DataFrame(aa_counter.most_common(15), columns=["mutation_aa", "sample_count"])
print("\nKRAS hotspot mutations:")
print(hotspots.head(10).to_string(index=False))
hotspots.to_csv("KRAS_hotspots.csv", index=False)
```

### Workflow 2: Cancer Gene Census Export

**Goal**: Export the full Cancer Gene Census as a structured table for downstream pipeline use.

```python
import requests, base64, pandas as pd, time

EMAIL = "your@email.com"
PASSWORD = "your_password"
token = base64.b64encode(f"{EMAIL}:{PASSWORD}".encode()).decode()

BASE = "https://cancer.sanger.ac.uk/cosmic/api"
HEADERS = {"Authorization": f"Basic {token}"}

all_genes = []
for tier in [1, 2]:
    skip = 0
    while True:
        r = requests.get(f"{BASE}/genes",
                         headers=HEADERS,
                         params={"cgc_tier": str(tier), "limit": 100, "skip": skip})
        r.raise_for_status()
        batch = r.json()["data"]
        if not batch:
            break
        all_genes.extend(batch)
        if len(batch) < 100:
            break
        skip += 100
        time.sleep(0.1)

rows = [{
    "gene": g.get("gene_name"),
    "tier": g.get("cgc_tier"),
    "role_in_cancer": g.get("role_in_cancer"),
    "mutation_types": g.get("mutation_types"),
    "somatic_tumours": str(g.get("tumour_types_somatic", [])),
    "germline_tumours": str(g.get("tumour_types_germline", [])),
    "chr": g.get("chromosomal_location"),
} for g in all_genes]

df = pd.DataFrame(rows)
df.to_csv("COSMIC_cancer_gene_census.csv", index=False)
print(f"Exported {len(df)} Cancer Gene Census genes → COSMIC_cancer_gene_census.csv")
print(df.groupby("tier")["gene"].count())
```

## Key Parameters

| Parameter | Module | Default | Range / Options | Effect |
|-----------|--------|---------|-----------------|--------|
| `gene_name` | Mutations | — | HGNC symbol | Filter mutations by gene |
| `primary_site` | Mutations/Samples | — | tissue type string | Filter by primary tumor site |
| `limit` | All | `10` | `1`–`200` | Records per page |
| `skip` | All | `0` | integer | Pagination offset |
| `cgc_tier` | Genes | — | `"1"`, `"2"` | Cancer Gene Census tier |
| `mutation_id` | Mutations | — | COSM ID string | Lookup specific mutation |

## Best Practices

1. **Authenticate via Base64**: COSMIC uses HTTP Basic Auth with base64-encoded `email:password`. Store credentials in environment variables, not in code.

2. **Paginate large gene queries**: Popular cancer genes (TP53, KRAS) have 100,000+ mutation records; use `skip`/`limit` pagination and cache results locally.

3. **Use COSM IDs for cross-study comparison**: Amino acid change strings may have formatting variations (p.G12D vs G12D); use COSMIC mutation IDs (COSM…) for unambiguous references.

4. **Check data license for commercial use**: COSMIC data is free for academic use but requires a commercial license for industry applications. Verify at https://cancer.sanger.ac.uk/cosmic/license.

5. **Complement with clinical data**: COSMIC captures somatic mutations from cancer sequencing; complement with `clinvar-database` for germline pathogenicity and `opentargets-database` for therapeutic significance.

## Common Recipes

### Recipe: Top Mutated Genes in a Cancer Type

When to use: Identify frequently mutated genes in a specific cancer type.

```python
import requests, base64, pandas as pd
from collections import Counter

EMAIL = "your@email.com"
PASSWORD = "your_password"
token = base64.b64encode(f"{EMAIL}:{PASSWORD}".encode()).decode()

HEADERS = {"Authorization": f"Basic {token}"}
r = requests.get("https://cancer.sanger.ac.uk/cosmic/api/mutations",
                 headers=HEADERS,
                 params={"primary_site": "lung", "limit": 200})
data = r.json()["data"]
gene_counts = Counter(m.get("gene_name") for m in data if m.get("gene_name"))
df = pd.DataFrame(gene_counts.most_common(10), columns=["gene", "mutations"])
print(df.to_string(index=False))
```

### Recipe: Check if a Variant Is in COSMIC

When to use: Look up whether a specific amino acid change is recorded in COSMIC.

```python
import requests, base64

EMAIL = "your@email.com"
PASSWORD = "your_password"
token = base64.b64encode(f"{EMAIL}:{PASSWORD}".encode()).decode()

HEADERS = {"Authorization": f"Basic {token}"}
gene = "KRAS"
aa_change = "p.G12D"

r = requests.get("https://cancer.sanger.ac.uk/cosmic/api/mutations",
                 headers=HEADERS,
                 params={"gene_name": gene, "limit": 200})
all_muts = r.json()["data"]
matches = [m for m in all_muts if aa_change in (m.get("mutation_aa") or "")]
print(f"{gene} {aa_change}: {'FOUND' if matches else 'NOT FOUND'} in COSMIC ({len(matches)} records)")
if matches:
    print(f"  Sample count: {sum(m.get('count', 0) for m in matches)}")
```

### Recipe: Download CGC Tier 1 Gene List

When to use: Get a simple list of Tier 1 cancer driver genes for filtering.

```python
import requests, base64

EMAIL = "your@email.com"
PASSWORD = "your_password"
token = base64.b64encode(f"{EMAIL}:{PASSWORD}".encode()).decode()

HEADERS = {"Authorization": f"Basic {token}"}
r = requests.get("https://cancer.sanger.ac.uk/cosmic/api/genes",
                 headers=HEADERS,
                 params={"cgc_tier": "1", "limit": 200})
genes = [g["gene_name"] for g in r.json()["data"]]
print(f"CGC Tier 1 genes ({len(genes)}): {', '.join(genes[:10])}...")
with open("cosmic_tier1_genes.txt", "w") as f:
    f.write("\n".join(genes))
```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `HTTP 401 Unauthorized` | Missing or incorrect API credentials | Check base64 encoding: `base64.b64encode(f"{email}:{password}".encode())` |
| `HTTP 403 Forbidden` | Access requires different tier | Some endpoints need commercial license; check COSMIC license page |
| Empty `data` array | No records match filter | Broaden query; check spelling of gene symbol or site name |
| Very slow for large genes | TP53/KRAS have 100K+ records | Paginate with small `limit=200`; cache results to local CSV |
| Rate limit errors | >10 req/s | Add `time.sleep(0.15)` between requests |
| Different AA notation format | Various mutation string formats | Normalize with RDKit or use COSM IDs for exact matching |

## Related Skills

- `clinvar-database` — Germline pathogenicity classifications complementing COSMIC's somatic focus
- `opentargets-database` — Drug-target associations for COSMIC cancer driver genes
- `ensembl-database` — Variant consequence predictions (VEP) for COSMIC variants
- `gwas-database` — Population-level SNP associations for cancer risk (vs. COSMIC's somatic mutations)

## References

- [COSMIC website](https://cancer.sanger.ac.uk/cosmic/) — Official COSMIC database and downloads
- [COSMIC REST API v3 documentation](https://cancer.sanger.ac.uk/cosmic/api) — API endpoint reference
- [Cancer Gene Census](https://cancer.sanger.ac.uk/census/) — Curated cancer driver gene catalog
- [COSMIC mutational signatures (Alexandrov et al. 2020)](https://doi.org/10.1038/s41586-020-1943-3) — Reference paper for COSMIC v3 signatures
