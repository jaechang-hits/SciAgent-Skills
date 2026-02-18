---
name: "ensembl-database"
description: "Query Ensembl REST API for gene/transcript/variant annotations across 300+ species. Retrieve gene info by symbol/ID, sequence, cross-references (HGNC, RefSeq, UniProt), variants, regulatory features, comparative genomics. For bulk local access use pyensembl; for pathway lookups use kegg-database or reactome-database."
license: "Apache-2.0"
---

# Ensembl Genome Database

## Overview

Ensembl is a comprehensive genome annotation database covering 300+ vertebrate and non-vertebrate species. The Ensembl REST API provides programmatic access to gene models, transcript/protein sequences, variant annotations, cross-references, regulatory features, and comparative genomics without requiring any login or API key.

## When to Use

- Retrieving official gene and transcript annotations (stable IDs, biotype, genomic coordinates) for human or model organism genes
- Converting between gene identifier namespaces (HGNC symbol ↔ Ensembl ID ↔ RefSeq ↔ UniProt)
- Fetching genomic or cDNA/CDS/protein sequences for a gene or transcript
- Looking up variant consequences and functional impact (VEP) for a list of SNPs
- Querying regulatory features (promoters, enhancers, CTCF sites) in a genomic region
- Performing comparative genomics queries (orthologs, paralogs, gene trees) across species
- For local offline access to large genomic annotations, use `pyensembl` instead
- For pathway and metabolic annotations, use `kegg-database` or `reactome-database` instead

## Prerequisites

- **Python packages**: `requests`
- **Data requirements**: gene symbols, Ensembl stable IDs (ENSG…/ENST…/ENSP…), or genomic coordinates
- **Environment**: internet connection required; no API key needed
- **Rate limits**: max ~15 requests/second; use `expand=1` and batch endpoints to minimize calls

```bash
pip install requests
```

## Quick Start

```python
import requests

BASE = "https://rest.ensembl.org"
HEADERS = {"Content-Type": "application/json"}

def ensembl_get(endpoint, params=None):
    r = requests.get(f"{BASE}{endpoint}", headers=HEADERS, params=params)
    r.raise_for_status()
    return r.json()

# Look up human BRCA1
gene = ensembl_get("/lookup/symbol/homo_sapiens/BRCA1", params={"expand": 1})
print(f"ID: {gene['id']}, Chr: {gene['seq_region_name']}:{gene['start']}-{gene['end']}")
print(f"Transcripts: {len(gene.get('Transcript', []))}")
```

## Core API

### Query 1: Gene Lookup by Symbol or Stable ID

Retrieve gene metadata from a gene symbol or Ensembl stable ID.

```python
import requests

BASE = "https://rest.ensembl.org"
HEADERS = {"Content-Type": "application/json"}

# By gene symbol
r = requests.get(
    f"{BASE}/lookup/symbol/homo_sapiens/TP53",
    headers=HEADERS,
    params={"expand": 1}
)
gene = r.json()
print(f"Ensembl ID : {gene['id']}")
print(f"Location   : {gene['seq_region_name']}:{gene['start']}-{gene['end']} ({gene['strand']})")
print(f"Biotype    : {gene['biotype']}")
print(f"Transcripts: {len(gene.get('Transcript', []))}")
```

```python
# By stable ID (works for genes, transcripts, proteins)
r = requests.get(
    f"{BASE}/lookup/id/ENSG00000141510",
    headers=HEADERS,
    params={"expand": 0}
)
obj = r.json()
print(f"Symbol: {obj.get('display_name')}, Species: {obj.get('species')}")
```

### Query 2: Batch Lookup

Retrieve information for multiple IDs in one call (POST endpoint).

```python
import requests, json

BASE = "https://rest.ensembl.org"
HEADERS = {"Content-Type": "application/json"}

# Batch lookup by symbols
symbols = ["BRCA1", "BRCA2", "TP53", "EGFR", "MYC"]
r = requests.post(
    f"{BASE}/lookup/symbol/homo_sapiens",
    headers=HEADERS,
    data=json.dumps({"symbols": symbols})
)
results = r.json()
for sym, data in results.items():
    if data:
        print(f"{sym}: {data['id']} ({data['seq_region_name']}:{data['start']}-{data['end']})")
```

### Query 3: Sequence Retrieval

Fetch genomic, cDNA, CDS, or protein sequences.

```python
import requests

BASE = "https://rest.ensembl.org"
HEADERS = {"Content-Type": "text/plain"}

# Protein sequence for canonical transcript
r = requests.get(
    f"{BASE}/sequence/id/ENST00000269305",
    headers=HEADERS,
    params={"type": "protein"}
)
seq = r.text
print(f"Protein sequence ({len(seq)} aa): {seq[:60]}...")
```

```python
# Genomic region sequence
HEADERS_JSON = {"Content-Type": "application/json"}
r = requests.get(
    f"{BASE}/sequence/region/human/17:43044295..43125364",
    headers=HEADERS_JSON,
    params={"coord_system_version": "GRCh38"}
)
result = r.json()
print(f"Retrieved {len(result['seq'])} bp of genomic sequence")
```

### Query 4: Cross-References (ID Mapping)

Map Ensembl IDs to external database identifiers.

```python
import requests

BASE = "https://rest.ensembl.org"
HEADERS = {"Content-Type": "application/json"}

# All xrefs for a gene
r = requests.get(
    f"{BASE}/xrefs/id/ENSG00000141510",
    headers=HEADERS
)
xrefs = r.json()

# Group by database
from collections import defaultdict
by_db = defaultdict(list)
for x in xrefs:
    by_db[x["dbname"]].append(x["primary_id"])

for db in ["HGNC", "RefSeq_gene_name", "Uniprot_gn", "MIM_gene"]:
    if db in by_db:
        print(f"{db}: {by_db[db]}")
```

### Query 5: Variant Consequence Annotation (VEP)

Predict functional consequences of variants via REST VEP endpoint.

```python
import requests, json

BASE = "https://rest.ensembl.org"
HEADERS = {"Content-Type": "application/json"}

# Annotate a list of hgvs notations
variants = ["17:g.43094692C>T", "13:g.32929387C>T"]
r = requests.post(
    f"{BASE}/vep/human/hgvs",
    headers=HEADERS,
    data=json.dumps({"hgvs_notations": variants})
)
for v in r.json():
    print(f"\nVariant: {v.get('input')}")
    for tc in v.get("transcript_consequences", [])[:2]:
        print(f"  Gene: {tc.get('gene_symbol')}, Impact: {tc.get('impact')}, Consequence: {tc.get('consequence_terms')}")
```

```python
# Annotate by rsID
r = requests.get(
    f"{BASE}/vep/human/id/rs699",
    headers=HEADERS
)
v = r.json()[0]
print(f"rsID rs699 in gene: {v['transcript_consequences'][0]['gene_symbol']}")
print(f"Consequence: {v['transcript_consequences'][0]['consequence_terms']}")
```

### Query 6: Regulatory Features

Query regulatory build features in a genomic region.

```python
import requests

BASE = "https://rest.ensembl.org"
HEADERS = {"Content-Type": "application/json"}

# Regulatory features in BRCA1 region
r = requests.get(
    f"{BASE}/overlap/region/human/17:43044000-43126000",
    headers=HEADERS,
    params={"feature": "regulatory"}
)
features = r.json()
print(f"Found {len(features)} regulatory features")
for f in features[:5]:
    print(f"  {f.get('feature_type')}: {f.get('start')}-{f.get('end')} ({f.get('description', 'n/a')})")
```

### Query 7: Comparative Genomics (Orthologs / Gene Trees)

Find orthologs and paralogs across species.

```python
import requests

BASE = "https://rest.ensembl.org"
HEADERS = {"Content-Type": "application/json"}

# Get mouse ortholog for human TP53
r = requests.get(
    f"{BASE}/homology/symbol/human/TP53",
    headers=HEADERS,
    params={"target_species": "mus_musculus", "type": "orthologues"}
)
data = r.json()
for homo in data["data"][0]["homologies"][:3]:
    tgt = homo["target"]
    print(f"Mouse ortholog: {tgt['id']} ({tgt.get('perc_id', 'n/a')}% identity)")
```

## Key Concepts

### Stable IDs and Versioning

Ensembl uses stable IDs with optional version suffixes (e.g., `ENSG00000141510.17`). Genes (`ENSG`), transcripts (`ENST`), proteins (`ENSP`), and exons (`ENSE`) each have their own prefix. IDs are preserved across releases when possible; retired IDs can still be resolved via the archive API.

### Assembly Versions

Human genome: GRCh38 (current) and GRCh37 (legacy, via `grch37.rest.ensembl.org`). Always specify which assembly your coordinates belong to when making region-based queries.

## Common Workflows

### Workflow 1: Gene-to-Protein Information Pipeline

**Goal**: Retrieve all key annotations for a gene list — coordinates, transcripts, xrefs, and canonical protein sequence.

```python
import requests, json, time

BASE = "https://rest.ensembl.org"
HEADERS = {"Content-Type": "application/json"}

def batch_lookup(symbols, species="homo_sapiens"):
    r = requests.post(
        f"{BASE}/lookup/symbol/{species}",
        headers=HEADERS,
        data=json.dumps({"symbols": symbols, "expand": 1})
    )
    return r.json()

def canonical_transcript(gene_data):
    """Return the ID of the canonical (longest CDS) transcript."""
    transcripts = gene_data.get("Transcript", [])
    coding = [t for t in transcripts if t.get("biotype") == "protein_coding"]
    if not coding:
        return None
    return max(coding, key=lambda t: t.get("Translation", {}).get("length", 0))

genes = ["BRCA1", "BRCA2", "TP53"]
lookup = batch_lookup(genes)

for sym in genes:
    g = lookup.get(sym)
    if not g:
        print(f"{sym}: not found")
        continue
    canon = canonical_transcript(g)
    print(f"\n{sym} ({g['id']})")
    print(f"  Location: {g['seq_region_name']}:{g['start']}-{g['end']}")
    if canon:
        prot_len = canon.get("Translation", {}).get("length", "n/a")
        print(f"  Canonical transcript: {canon['id']} ({prot_len} aa)")
    time.sleep(0.1)  # be polite
```

### Workflow 2: Variant Annotation Pipeline

**Goal**: Annotate a VCF-style variant list with gene, consequence, and impact.

```python
import requests, json, pandas as pd

BASE = "https://rest.ensembl.org"
HEADERS = {"Content-Type": "application/json"}

# Input: list of hgvs notations
hgvs_list = [
    "17:g.43094692C>T",
    "17:g.43063873A>G",
    "13:g.32929387C>T",
]

# Annotate in batches of 200
def vep_batch(hgvs_batch):
    r = requests.post(
        f"{BASE}/vep/human/hgvs",
        headers=HEADERS,
        data=json.dumps({"hgvs_notations": hgvs_batch})
    )
    r.raise_for_status()
    return r.json()

records = []
for ann in vep_batch(hgvs_list):
    for tc in ann.get("transcript_consequences", []):
        if tc.get("canonical") == 1:
            records.append({
                "variant": ann["input"],
                "gene": tc.get("gene_symbol"),
                "consequence": ",".join(tc.get("consequence_terms", [])),
                "impact": tc.get("impact"),
                "biotype": tc.get("biotype"),
            })

df = pd.DataFrame(records)
print(df.to_string(index=False))
df.to_csv("vep_results.csv", index=False)
print(f"\nSaved {len(df)} variant annotations → vep_results.csv")
```

## Key Parameters

| Parameter | Module | Default | Range / Options | Effect |
|-----------|--------|---------|-----------------|--------|
| `expand` | Lookup | `0` | `0` or `1` | Include nested transcripts/translations |
| `type` | Sequence | `"genomic"` | `"genomic"`, `"cDNA"`, `"CDS"`, `"protein"` | Sequence type to return |
| `target_species` | Homology | `None` | Species name or taxon ID | Filter homologs to target species |
| `feature` | Overlap | required | `"gene"`, `"transcript"`, `"regulatory"`, `"variation"` | Feature type to retrieve |
| `coord_system_version` | Region | `"GRCh38"` | `"GRCh38"`, `"GRCh37"` | Genome assembly |
| `content_type` | All | via header | `"application/json"`, `"text/plain"` | Response format |

## Best Practices

1. **Use batch endpoints**: POST `/lookup/symbol/{species}` and POST `/vep/human/hgvs` accept up to 1000 IDs; single-ID GET requests in a loop will hit rate limits quickly.

2. **Pin assembly version**: For region-based queries always specify `coord_system_version=GRCh38` (or use `grch37.rest.ensembl.org` for legacy coordinates) to avoid silent mismatch errors.

3. **Cache responses**: Gene metadata rarely changes between Ensembl releases; cache results to disk (`joblib.Memory`) to avoid redundant API calls during development.
   ```python
   from joblib import Memory
   mem = Memory("cache/", verbose=0)
   cached_lookup = mem.cache(batch_lookup)
   ```

4. **Use `expand=0` for metadata**: When you only need gene coordinates and biotype (not transcript details), keep `expand=0` for smaller payloads and faster responses.

5. **Check canonical flag in VEP**: VEP returns consequences for all overlapping transcripts; filter on `tc.get("canonical") == 1` to get the biologically most relevant consequence per variant.

## Common Recipes

### Recipe: Symbol → Ensembl ID Mapping Table

When to use: Build a lookup table from gene symbols to Ensembl IDs for downstream analysis.

```python
import requests, json, pandas as pd

BASE = "https://rest.ensembl.org"
HEADERS = {"Content-Type": "application/json"}

symbols = ["EGFR", "KRAS", "BRAF", "PIK3CA", "PTEN", "AKT1", "MYC", "RB1"]
r = requests.post(
    f"{BASE}/lookup/symbol/homo_sapiens",
    headers=HEADERS,
    data=json.dumps({"symbols": symbols})
)
data = r.json()
rows = [{"symbol": s, "ensembl_id": d["id"] if d else None,
         "chrom": d["seq_region_name"] if d else None} for s, d in data.items()]
df = pd.DataFrame(rows)
df.to_csv("symbol_to_ensembl.csv", index=False)
print(df.to_string(index=False))
```

### Recipe: Region Gene Overlap

When to use: Find all genes overlapping a genomic interval (e.g., a GWAS locus).

```python
import requests, pandas as pd

BASE = "https://rest.ensembl.org"
HEADERS = {"Content-Type": "application/json"}

chrom, start, end = "17", 43044295, 43125364
r = requests.get(
    f"{BASE}/overlap/region/human/{chrom}:{start}-{end}",
    headers=HEADERS,
    params={"feature": "gene", "biotype": "protein_coding"}
)
genes = r.json()
df = pd.DataFrame([{
    "id": g["id"], "name": g.get("external_name"),
    "start": g["start"], "end": g["end"], "strand": g["strand"]
} for g in genes])
print(df.to_string(index=False))
print(f"\n{len(df)} protein-coding genes in region")
```

### Recipe: Species List

When to use: Check which species are available in Ensembl before querying.

```python
import requests

BASE = "https://rest.ensembl.org"
HEADERS = {"Content-Type": "application/json"}

r = requests.get(f"{BASE}/info/species", headers=HEADERS)
species_list = r.json()["species"]
print(f"Total species: {len(species_list)}")
vertebrates = [s for s in species_list if s.get("division") == "EnsemblVertebrates"]
print(f"Vertebrates: {len(vertebrates)}")
for s in vertebrates[:5]:
    print(f"  {s['common_name']} ({s['name']}): {s['assembly']}")
```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `HTTP 429 Too Many Requests` | Exceeding ~15 req/s rate limit | Add `time.sleep(0.1)` between requests; use batch POST endpoints |
| `HTTP 400 Bad Request` on VEP | Malformed HGVS notation | Verify format: `chr:g.posREF>ALT` (e.g., `17:g.43094692C>T`) |
| `Gene not found` | Gene symbol not in Ensembl | Try alternative symbol; check species name (use `homo_sapiens` not `human` for symbols) |
| Region query returns wrong genes | Assembly mismatch | Set `coord_system_version=GRCh38` or use `grch37.rest.ensembl.org` |
| Old ID not resolving | Retired Ensembl ID | Query `GET /archive/id/{id}` to get current mapping |
| `HTTP 503 Service Unavailable` | Server maintenance | Retry after a few minutes; check Ensembl status at status.ensembl.org |

## Related Skills

- `gget-genomic-databases` — CLI/Python wrapper covering Ensembl + 20 other databases; use for quick lookups without raw API code
- `biopython-molecular-biology` — Biopython's `Entrez` module for NCBI databases (alternative for RefSeq/GenBank queries)
- `kegg-database` — Pathway/metabolic annotations for the same gene set
- `reactome-database` — Pathway enrichment and hierarchy queries

## References

- [Ensembl REST API documentation](https://rest.ensembl.org) — Interactive API explorer and endpoint reference
- [Ensembl Help & Documentation](https://www.ensembl.org/info/docs/api/rest/rest_access.html) — REST API overview
- [Ensembl stable IDs guide](https://www.ensembl.org/info/genome/stable_ids/index.html) — ID versioning policy
- [VEP documentation](https://www.ensembl.org/info/docs/tools/vep/index.html) — Variant Effect Predictor full reference
