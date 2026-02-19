---
name: "dbsnp-database"
description: "Query NCBI dbSNP for SNP records by rsID, gene, or genomic region via E-utilities (esearch, efetch, epost) and NCBI Variation Services REST API. Retrieve allele data, minor allele frequency, variant class (SNV, indel, MNV), clinical significance links, and cross-database IDs (ClinVar, dbVar, 1000G). Free access; 3 req/sec without API key, 10 req/sec with key. For clinical pathogenicity classifications use clinvar-database; for population frequencies use gnomad-database."
license: "CC0-1.0"
---

# dbSNP Database

## Overview

NCBI dbSNP is the primary public repository for short human genetic variants, cataloguing over 1 billion SNPs, indels, and MNVs with allele frequencies, functional annotations, and cross-references to ClinVar, gnomAD, and 1000 Genomes. Variants are identified by stable rsIDs (reference SNP cluster IDs). Access is free via two APIs: the legacy NCBI E-utilities and the newer NCBI Variation Services REST API, which returns structured JSON.

## When to Use

- Looking up allele frequencies and variant class for a known rsID
- Searching all dbSNP variants in a gene or chromosomal region by name or coordinates
- Resolving rsIDs to genomic coordinates (GRCh38/GRCh37) and HGVS notation
- Checking whether a variant of interest has clinical significance links to ClinVar entries
- Batch-fetching hundreds of rsIDs efficiently using epost+efetch history server
- Cross-referencing a list of variant positions to dbSNP rsIDs for downstream annotation
- For clinical pathogenicity classifications use `clinvar-database`; dbSNP provides IDs and frequency but not curated clinical significance
- For population frequency stratified by ancestry use `gnomad-database`; dbSNP MAF is a single aggregate frequency

## Prerequisites

- **Python packages**: `requests`, `pandas`, `matplotlib`, `xml.etree.ElementTree` (stdlib)
- **Data requirements**: rsIDs (`rs80357906`), gene symbols, or chromosomal coordinates
- **Environment**: internet connection; NCBI Entrez email required for E-utilities (set `email` parameter)
- **Rate limits**: 3 requests/second without API key; 10 requests/second with free NCBI API key. Register at https://www.ncbi.nlm.nih.gov/account/ — add `&api_key=YOUR_KEY` to all requests

```bash
pip install requests pandas matplotlib
# xml.etree.ElementTree is part of Python stdlib — no additional install needed
```

## Quick Start

```python
import requests
import json

EMAIL = "your@email.com"      # required by NCBI policy
BASE_EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
BASE_VARIATION = "https://api.ncbi.nlm.nih.gov/variation/v0"

def fetch_snp_by_rsid(rsid: str) -> dict:
    """Fetch a dbSNP record by rsID using the NCBI Variation Services API (structured JSON)."""
    rs_num = str(rsid).lstrip("rs")
    r = requests.get(f"{BASE_VARIATION}/refsnp/{rs_num}", timeout=15)
    r.raise_for_status()
    return r.json()

record = fetch_snp_by_rsid("rs80357906")
print(f"rsID: rs{record['refsnp_id']}")
print(f"Organism: {record.get('organism', {}).get('common_name')}")
print(f"SNP class: {record.get('primary_snapshot_data', {}).get('variant_type')}")
# rsID: rs80357906
# Organism: human
# SNP class: snv
```

## Core API

### Query 1: rsID Lookup via E-utilities

Fetch the full SNP record for a single rsID using efetch with `db=snp`. Returns an XML document with alleles, placements, and frequency data.

```python
import requests
import xml.etree.ElementTree as ET

EMAIL = "your@email.com"
BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

def efetch_snp_xml(rsid: str) -> ET.Element:
    """Fetch dbSNP XML record for a single rsID."""
    rs_num = str(rsid).lstrip("rs")
    r = requests.get(f"{BASE}/efetch.fcgi",
                     params={"db": "snp", "id": rs_num,
                             "rettype": "xml", "retmode": "xml",
                             "email": EMAIL},
                     timeout=20)
    r.raise_for_status()
    return ET.fromstring(r.text)

root = efetch_snp_xml("rs80357906")

# Parse allele placements from the XML
for docsum in root.iter("DocumentSummary"):
    rs_id = docsum.get("uid")
    snp_class = docsum.findtext("SNP_CLASS", "Unknown")
    maf = docsum.findtext("MAF", "N/A")
    maf_allele = docsum.findtext("MAFALLELE", "N/A")
    chr_pos = docsum.findtext("CHRPOS", "N/A")
    gene = docsum.findtext("GENES/GENE_E/NAME", "N/A")
    clin_sig = docsum.findtext("CLINICAL_SIGNIFICANCE", "N/A")
    print(f"rs{rs_id} | Class: {snp_class} | MAF: {maf} ({maf_allele})")
    print(f"  Position: {chr_pos} | Gene: {gene} | ClinSig: {clin_sig}")
```

```python
# Fetch using ESummary for structured JSON (preferred for batch)
def esummary_snp(rsid: str) -> dict:
    rs_num = str(rsid).lstrip("rs")
    r = requests.get(f"{BASE}/esummary.fcgi",
                     params={"db": "snp", "id": rs_num,
                             "retmode": "json", "email": EMAIL},
                     timeout=15)
    r.raise_for_status()
    result = r.json()["result"]
    return result.get(rs_num, {})

rec = esummary_snp("rs80357906")
print(f"rs{rec.get('snp_id')}:")
print(f"  Class       : {rec.get('snp_class')}")
print(f"  MAF         : {rec.get('maf')} ({rec.get('mafallele')})")
print(f"  ChrPos      : {rec.get('chrpos')}")
print(f"  ClinSig     : {rec.get('clinical_significance')}")
print(f"  FxnClass    : {rec.get('fxn_class')}")
```

### Query 2: Gene Variant Search

Search dbSNP for all variants in a gene using esearch. Returns a list of rsIDs matching the gene.

```python
import requests

EMAIL = "your@email.com"
BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

def esearch_snp(query: str, retmax: int = 100) -> tuple[list, int]:
    """Search dbSNP using a query string. Returns (id_list, total_count)."""
    r = requests.get(f"{BASE}/esearch.fcgi",
                     params={"db": "snp", "term": query,
                             "retmax": retmax, "retmode": "json",
                             "email": EMAIL},
                     timeout=15)
    r.raise_for_status()
    result = r.json()["esearchresult"]
    return result["idlist"], int(result["count"])

# All variants in BRCA1
ids, total = esearch_snp("BRCA1[gene] AND human[orgn]", retmax=20)
print(f"BRCA1 variants in dbSNP: {total:,} total")
print(f"First 5 rsIDs: {['rs' + i for i in ids[:5]]}")

# Only clinical variants (linked to ClinVar)
ids_clin, total_clin = esearch_snp(
    "BRCA1[gene] AND human[orgn] AND clinsig[filter]", retmax=50)
print(f"BRCA1 variants with clinical significance: {total_clin:,}")
```

### Query 3: Chromosomal Region Search

Search for all variants in a genomic region using chromosome coordinates.

```python
import requests

EMAIL = "your@email.com"
BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

def search_region(chrom: str, start: int, stop: int,
                  assembly: str = "GRCh38", retmax: int = 200) -> tuple[list, int]:
    """Find all dbSNP variants in a chromosomal region."""
    query = f"{chrom}[CHR] AND {start}:{stop}[CHRPOS37]" if assembly == "GRCh37" else \
            f"{chrom}[CHR] AND {start}:{stop}[CHRPOS]"
    r = requests.get(f"{BASE}/esearch.fcgi",
                     params={"db": "snp", "term": query,
                             "retmax": retmax, "retmode": "json",
                             "email": EMAIL},
                     timeout=20)
    r.raise_for_status()
    result = r.json()["esearchresult"]
    return result["idlist"], int(result["count"])

# PCSK9 exon 4 region (GRCh38)
ids, total = search_region("1", 55039700, 55040200)
print(f"Variants in chr1:55039700-55040200: {total:,} total")
print(f"Retrieved {len(ids)} rsIDs: {['rs' + i for i in ids[:5]]}")
```

### Query 4: Variant Summary — MAF, Alleles, Clinical Significance

Retrieve structured summary data for variant records using ESummary, extracting MAF, alleles, and database cross-links.

```python
import requests, json

EMAIL = "your@email.com"
BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

def fetch_snp_summaries(rsids: list) -> dict:
    """Fetch ESummary records for a list of rsIDs. Returns dict keyed by rs number."""
    ids_str = ",".join(str(r).lstrip("rs") for r in rsids)
    r = requests.post(f"{BASE}/esummary.fcgi",
                      data={"db": "snp", "id": ids_str,
                            "retmode": "json", "email": EMAIL},
                      timeout=20)
    r.raise_for_status()
    return r.json()["result"]

rsids = ["rs80357906", "rs80357220", "rs28897672", "rs1801133"]
result = fetch_snp_summaries(rsids)

for rs_num in rsids:
    uid = str(rs_num).lstrip("rs")
    rec = result.get(uid, {})
    print(f"\n{rs_num}:")
    print(f"  Class        : {rec.get('snp_class', 'N/A')}")
    print(f"  MAF          : {rec.get('maf', 'N/A')} allele={rec.get('mafallele', 'N/A')}")
    print(f"  Location     : {rec.get('chrpos', 'N/A')}")
    print(f"  ClinSig      : {rec.get('clinical_significance', 'N/A')}")
    print(f"  Function     : {rec.get('fxn_class', 'N/A')}")
```

### Query 5: Batch rsID Query with EPost+EFetch

Efficiently upload hundreds of rsIDs to the NCBI history server using EPost, then retrieve them in batches with EFetch.

```python
import requests, time, pandas as pd

EMAIL = "your@email.com"
BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

def epost_ids(id_list: list) -> tuple[str, str]:
    """Upload rsIDs to NCBI history server. Returns (WebEnv, query_key)."""
    ids_str = ",".join(str(i).lstrip("rs") for i in id_list)
    r = requests.post(f"{BASE}/epost.fcgi",
                      data={"db": "snp", "id": ids_str, "email": EMAIL},
                      timeout=30)
    r.raise_for_status()
    import xml.etree.ElementTree as ET
    root = ET.fromstring(r.text)
    webenv = root.findtext("WebEnv")
    query_key = root.findtext("QueryKey")
    return webenv, query_key

def efetch_history(webenv: str, query_key: str,
                   retstart: int = 0, retmax: int = 100) -> dict:
    """Retrieve records from NCBI history server using ESummary."""
    r = requests.get(f"{BASE}/esummary.fcgi",
                     params={"db": "snp", "WebEnv": webenv,
                             "query_key": query_key, "retstart": retstart,
                             "retmax": retmax, "retmode": "json",
                             "email": EMAIL},
                     timeout=30)
    r.raise_for_status()
    return r.json()["result"]

rsid_batch = ["rs80357906", "rs80357220", "rs28897672", "rs1801133",
              "rs429358", "rs7412", "rs1800497"]

webenv, query_key = epost_ids(rsid_batch)
print(f"Posted {len(rsid_batch)} IDs | WebEnv: {webenv[:40]}...")

records = []
for start in range(0, len(rsid_batch), 100):
    result = efetch_history(webenv, query_key, retstart=start, retmax=100)
    for uid in result.get("uids", []):
        rec = result[uid]
        records.append({
            "rsid": f"rs{uid}",
            "snp_class": rec.get("snp_class"),
            "maf": rec.get("maf"),
            "maf_allele": rec.get("mafallele"),
            "chrpos": rec.get("chrpos"),
            "clinical_sig": rec.get("clinical_significance"),
        })
    time.sleep(0.5)

df = pd.DataFrame(records)
print(f"\nRetrieved {len(df)} records:")
print(df.to_string(index=False))
```

### Query 6: NCBI Variation Services API

The newer REST API returns structured JSON with detailed allele placements, frequencies, and variant type annotations. Preferred for programmatic rsID resolution.

```python
import requests
import pandas as pd

BASE_VARIATION = "https://api.ncbi.nlm.nih.gov/variation/v0"

def fetch_refsnp(rsid: str) -> dict:
    """Fetch structured JSON from NCBI Variation Services API."""
    rs_num = str(rsid).lstrip("rs")
    r = requests.get(f"{BASE_VARIATION}/refsnp/{rs_num}", timeout=15)
    r.raise_for_status()
    return r.json()

def parse_allele_frequencies(record: dict) -> list:
    """Extract allele frequencies from a Variation Services record."""
    freqs = []
    snapshot = record.get("primary_snapshot_data", {})
    allele_annotations = snapshot.get("allele_annotations", [])
    for ann in allele_annotations:
        for freq in ann.get("frequency", []):
            freqs.append({
                "allele": ann.get("allele"),
                "study": freq.get("study_name"),
                "allele_count": freq.get("allele_count"),
                "total_count": freq.get("total_count"),
                "observation": freq.get("observation", {}).get("allele_count"),
            })
    return freqs

record = fetch_refsnp("rs1800497")   # DRD2 Taq1A variant
print(f"rsID: rs{record['refsnp_id']}")
print(f"Variant type: {record.get('primary_snapshot_data', {}).get('variant_type')}")

placements = record.get("primary_snapshot_data", {}).get("placements_with_allele", [])
for placement in placements[:2]:
    seq_id = placement.get("seq_id")
    is_top = placement.get("is_ptlp")
    for allele in placement.get("alleles", []):
        spdi = allele.get("allele", {}).get("spdi", {})
        print(f"  Placement: {seq_id} | SPDI: {spdi.get('inserted_sequence')}")

freqs = parse_allele_frequencies(record)
if freqs:
    df_freq = pd.DataFrame(freqs[:5])
    print(f"\nAllele frequencies ({len(freqs)} entries):")
    print(df_freq.to_string(index=False))
```

## Key Concepts

### rsID vs. ss ID (Submitted SNP)

dbSNP uses two IDs: **rs IDs** (Reference SNP cluster IDs) are stable public identifiers assigned after clustering submitted variants. **ss IDs** (Submitted SNP IDs) are assigned to individual laboratory submissions before clustering. Use rs IDs for all queries — ss IDs are internal and submission-specific. A single rs ID may cluster multiple ss IDs from different submissions.

### MAF vs. Clinical Significance

- **MAF (Minor Allele Frequency)**: The aggregate frequency of the minor allele across all dbSNP submissions. This is a population-level statistic aggregated from 1000 Genomes, gnomAD, TOPMED, and other studies. It does not indicate whether the variant is pathogenic.
- **Clinical significance**: A link field pointing to ClinVar classifications (Pathogenic, VUS, Benign, etc.). A variant can have a very low MAF (rare) yet be classified as Benign, or a moderate MAF yet be Pathogenic in a specific context (e.g., founder variants). Use `clinvar-database` for the full pathogenicity record.

### Variant Classes in dbSNP

| Class | Description | Example |
|-------|-------------|---------|
| `snv` | Single nucleotide variant (A>T) | rs80357906 |
| `indel` | Insertion or deletion | rs786201005 |
| `mnv` | Multi-nucleotide variant | rs1057519737 |
| `ins` | Pure insertion | rs113993960 |
| `del` | Pure deletion | rs66767301 |
| `microsatellite` | STR (short tandem repeat) | rs5030655 |

## Common Workflows

### Workflow 1: Batch rsID Annotation from a Variant List

**Goal**: Given a list of rsIDs from a variant call pipeline, retrieve MAF, position, and clinical significance for all variants in one run.

```python
import requests, time, pandas as pd

EMAIL = "your@email.com"
BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

def epost_snp(rsids):
    ids = ",".join(str(r).lstrip("rs") for r in rsids)
    r = requests.post(f"{BASE}/epost.fcgi",
                      data={"db": "snp", "id": ids, "email": EMAIL}, timeout=30)
    r.raise_for_status()
    import xml.etree.ElementTree as ET
    root = ET.fromstring(r.text)
    return root.findtext("WebEnv"), root.findtext("QueryKey")

def esummary_history(webenv, query_key, start, retmax=100):
    r = requests.get(f"{BASE}/esummary.fcgi",
                     params={"db": "snp", "WebEnv": webenv,
                             "query_key": query_key, "retstart": start,
                             "retmax": retmax, "retmode": "json", "email": EMAIL},
                     timeout=30)
    r.raise_for_status()
    return r.json()["result"]

# Example: VCF post-processing — annotate a list of called variants
variant_rsids = [
    "rs80357906", "rs80357220", "rs28897672", "rs1801133",
    "rs429358", "rs7412", "rs1800497", "rs2230199",
]

print(f"Posting {len(variant_rsids)} rsIDs to NCBI history server...")
webenv, query_key = epost_snp(variant_rsids)

records = []
for start in range(0, len(variant_rsids), 100):
    result = esummary_history(webenv, query_key, start=start, retmax=100)
    for uid in result.get("uids", []):
        rec = result[uid]
        records.append({
            "rsid": f"rs{uid}",
            "snp_class": rec.get("snp_class"),
            "maf": rec.get("maf"),
            "maf_allele": rec.get("mafallele"),
            "chrpos_grch38": rec.get("chrpos"),
            "gene": rec.get("genes", [{}])[0].get("name") if rec.get("genes") else None,
            "clinical_significance": rec.get("clinical_significance"),
            "fxn_class": rec.get("fxn_class"),
        })
    time.sleep(0.5)

df = pd.DataFrame(records)
df.to_csv("variant_annotations.csv", index=False)
print(f"Annotated {len(df)} variants → variant_annotations.csv")
print(df[["rsid", "snp_class", "maf", "chrpos_grch38", "clinical_significance"]].to_string(index=False))
```

### Workflow 2: Gene Variant Class Distribution Visualization

**Goal**: Search all dbSNP variants in a gene and plot their variant class distribution.

```python
import requests, time
import pandas as pd
import matplotlib.pyplot as plt

EMAIL = "your@email.com"
BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

def search_gene_variants(gene: str, retmax: int = 500) -> list:
    r = requests.get(f"{BASE}/esearch.fcgi",
                     params={"db": "snp", "term": f"{gene}[gene] AND human[orgn]",
                             "retmax": retmax, "retmode": "json", "email": EMAIL},
                     timeout=20)
    r.raise_for_status()
    return r.json()["esearchresult"]["idlist"]

def fetch_summaries_batch(ids: list, batch_size: int = 100) -> list:
    records = []
    for i in range(0, len(ids), batch_size):
        batch = ids[i:i+batch_size]
        ids_str = ",".join(batch)
        r = requests.post(f"{BASE}/esummary.fcgi",
                          data={"db": "snp", "id": ids_str,
                                "retmode": "json", "email": EMAIL},
                          timeout=30)
        r.raise_for_status()
        result = r.json()["result"]
        for uid in result.get("uids", []):
            rec = result[uid]
            records.append({"rsid": f"rs{uid}", "snp_class": rec.get("snp_class", "unknown")})
        time.sleep(0.5)
    return records

gene = "CFTR"
print(f"Searching dbSNP for {gene} variants...")
ids = search_gene_variants(gene, retmax=300)
print(f"Found {len(ids)} IDs; fetching summaries...")

records = fetch_summaries_batch(ids)
df = pd.DataFrame(records)
class_counts = df["snp_class"].value_counts()

# Plot variant class distribution
fig, ax = plt.subplots(figsize=(8, 5))
colors = ["#4472C4", "#ED7D31", "#A9D18E", "#FF0000", "#FFC000", "#7030A0"]
bars = ax.bar(class_counts.index, class_counts.values,
              color=colors[:len(class_counts)], edgecolor="white")
ax.bar_label(bars, padding=3, fontsize=9)
ax.set_xlabel("Variant Class")
ax.set_ylabel("Count")
ax.set_title(f"dbSNP Variant Classes in {gene} (n={len(df)})")
plt.tight_layout()
plt.savefig(f"{gene}_variant_classes.png", dpi=150, bbox_inches="tight")
print(f"Saved {gene}_variant_classes.png")
print(class_counts.to_string())
# snv                 241
# indel                38
# mnv                  12
# del                   7
# ins                   2
```

## Key Parameters

| Parameter | Function/Endpoint | Default | Range / Options | Effect |
|-----------|-------------------|---------|-----------------|--------|
| `db` | All E-utilities | required | `"snp"` | Database selector; must be `"snp"` for dbSNP queries |
| `id` | efetch, esummary, epost | required | rsID number(s) without `rs` prefix | Variant identifier(s) to fetch |
| `term` | esearch | required | dbSNP query string | Search expression with field tags: `[gene]`, `[CHR]`, `[CHRPOS]`, `[rs]`, `clinsig[filter]` |
| `retmax` | esearch | `20` | `1`–`10000` | Maximum records returned per search |
| `retmode` | esearch, esummary | `"xml"` | `"json"`, `"xml"` | Response format; use `"json"` for easy parsing |
| `rettype` | efetch | `"docsum"` | `"docsum"`, `"xml"` | Record type for efetch responses |
| `WebEnv` + `query_key` | esummary, efetch | — | from epost response | History server tokens for batch retrieval |
| `email` | All E-utilities | required | valid email string | NCBI policy; used for rate attribution |
| `api_key` | All E-utilities | optional | NCBI API key string | Raises rate limit from 3 to 10 req/sec |

## Best Practices

1. **Register for a free NCBI API key**: Adds `api_key=YOUR_KEY` to requests and triples your rate limit (3 → 10 req/sec) with no other changes. Register at https://www.ncbi.nlm.nih.gov/account/.

2. **Use epost+esummary for batches of more than 10 rsIDs**: Avoid looping individual efetch calls. EPost uploads all IDs in one request to the history server; subsequent ESummary calls retrieve them in configurable batches of up to 500.

3. **Prefer NCBI Variation Services API for structured JSON**: The `/variation/v0/refsnp/{rs_num}` endpoint returns a fully structured JSON with SPDI allele representations, placements, and frequency tables. Easier to parse than E-utilities XML for modern applications.

4. **Check `snp_class` before interpreting MAF**: Indels and MNVs use different allele counting conventions than SNVs. Treat multi-allelic sites carefully — the reported MAF may refer to one allele among several.

5. **Combine dbSNP with ClinVar lookups**: dbSNP records the `clinical_significance` field as a string (e.g., `"pathogenic"`) but does not contain submitter details, review status, or HGVS details. Use `clinvar-database` for the full pathogenicity record when clinical interpretation is required.

## Common Recipes

### Recipe: Quick rsID Existence and Class Check

When to use: Check whether a variant is registered in dbSNP before downstream annotation.

```python
import requests

EMAIL = "your@email.com"

def check_rsid(rsid: str) -> dict:
    """Check if an rsID exists in dbSNP and return basic info."""
    rs_num = str(rsid).lstrip("rs")
    r = requests.get(
        "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi",
        params={"db": "snp", "id": rs_num, "retmode": "json", "email": EMAIL},
        timeout=10
    )
    result = r.json().get("result", {})
    rec = result.get(rs_num, {})
    if not rec or "error" in rec:
        return {"rsid": rsid, "found": False}
    return {
        "rsid": rsid,
        "found": True,
        "snp_class": rec.get("snp_class"),
        "chrpos": rec.get("chrpos"),
        "maf": rec.get("maf"),
        "clinical_significance": rec.get("clinical_significance"),
    }

for rsid in ["rs80357906", "rs9999999999", "rs1800497"]:
    info = check_rsid(rsid)
    if info["found"]:
        print(f"{rsid}: {info['snp_class']} | pos={info['chrpos']} | MAF={info['maf']}")
    else:
        print(f"{rsid}: NOT FOUND in dbSNP")
# rs80357906: snv | pos=17:43094692 | MAF=0.000008
# rs9999999999: NOT FOUND in dbSNP
# rs1800497: snv | pos=11:113270828 | MAF=0.3517
```

### Recipe: Resolve Gene Variants to rsIDs and Coordinates

When to use: Convert a gene name to a list of rsIDs for use in downstream tools (PLINK, ANNOVAR, etc.).

```python
import requests, time, pandas as pd

EMAIL = "your@email.com"
BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

def gene_to_rsids(gene: str, max_variants: int = 200) -> pd.DataFrame:
    """Search dbSNP for a gene and return rsIDs with GRCh38 coordinates."""
    # Step 1: search
    r = requests.get(f"{BASE}/esearch.fcgi",
                     params={"db": "snp", "term": f"{gene}[gene] AND human[orgn]",
                             "retmax": max_variants, "retmode": "json", "email": EMAIL},
                     timeout=15)
    r.raise_for_status()
    ids = r.json()["esearchresult"]["idlist"]
    if not ids:
        return pd.DataFrame()
    time.sleep(0.4)

    # Step 2: fetch summaries
    r2 = requests.post(f"{BASE}/esummary.fcgi",
                       data={"db": "snp", "id": ",".join(ids),
                             "retmode": "json", "email": EMAIL},
                       timeout=30)
    r2.raise_for_status()
    result = r2.json()["result"]
    rows = []
    for uid in result.get("uids", []):
        rec = result[uid]
        rows.append({
            "rsid": f"rs{uid}",
            "chrpos_grch38": rec.get("chrpos"),
            "snp_class": rec.get("snp_class"),
            "maf": rec.get("maf"),
        })
    return pd.DataFrame(rows)

df = gene_to_rsids("APOE", max_variants=50)
print(f"APOE variants retrieved: {len(df)}")
print(df.head(8).to_string(index=False))
df.to_csv("APOE_rsids.csv", index=False)
```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `HTTP 429` or connection refused | Rate limit exceeded (3 req/sec) | Add `time.sleep(0.35)` between requests; register for API key to get 10 req/sec |
| ESummary returns `{"error": "Invalid uid"}` | rsID does not exist in dbSNP | Check rsID spelling; verify with NCBI browser; variant may be a novel call not yet in dbSNP |
| `esearch` returns 0 results for a gene | Gene symbol mismatch or missing `human[orgn]` filter | Try adding `AND human[orgn]`; check NCBI gene symbol at https://www.ncbi.nlm.nih.gov/gene |
| MAF field is empty or `"."` | Variant has no population frequency data in dbSNP | Use gnomAD via `gnomad-database` for population frequencies; not all rsIDs have MAF |
| Variation Services API returns 404 | rsID not found or wrong URL format | Confirm integer rs number (no `rs` prefix) in `/refsnp/{rs_num}` endpoint |
| EPost XML parsing fails | Non-XML response (rate limit HTML error page) | Check response status code first; add retry logic with `time.sleep(1)` |
| Batch efetch returns fewer records than posted | Some rsIDs were merged or retired | Cross-check against NCBI merge history; retired rsIDs redirect to current active rs |

## Related Skills

- `clinvar-database` — ClinVar pathogenicity classifications for variants identified by rsID (complement to dbSNP)
- `gnomad-database` — Population allele frequencies by ancestry group (more detailed than dbSNP MAF)
- `gwas-database` — GWAS Catalog for SNP-trait associations from published GWAS studies
- `ensembl-database` — Ensembl REST API for variant consequences and gene annotations
- `snpeff-variant-annotation` — Annotate VCF files with SnpEff and SnpSift, which adds dbSNP rsIDs and functional predictions

## References

- [NCBI E-utilities for dbSNP](https://www.ncbi.nlm.nih.gov/snp/docs/entrez_help/) — E-utilities field tags and query syntax specific to dbSNP
- [NCBI Variation Services API](https://api.ncbi.nlm.nih.gov/variation/v0/) — REST API documentation and interactive Swagger UI
- [Sherry et al., Nucleic Acids Research 2001](https://doi.org/10.1093/nar/29.1.308) — dbSNP original description paper
- [NCBI E-utilities Reference](https://www.ncbi.nlm.nih.gov/books/NBK25499/) — Full E-utilities API reference (applies to all NCBI databases)
