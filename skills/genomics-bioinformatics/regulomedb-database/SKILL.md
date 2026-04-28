---
name: "regulomedb-database"
description: "Query RegulomeDB v2 REST API to score variants for regulatory function and retrieve overlapping evidence (TF binding, histone marks, DNase peaks, eQTLs, motifs). Score single rsID/position, batch lists, region searches, and full annotations. Scores range 1a (strongest: eQTL+TF+DNase+motif) to 7 (none). Use for GWAS hit prioritization, regulatory variant annotation, cis-regulatory discovery. Use clinvar-database for pathogenicity; gwas-database for trait associations."
license: "CC-BY-4.0"
---

# RegulomeDB Database

## Overview

RegulomeDB integrates large-scale functional genomics data (ENCODE, Roadmap Epigenomics) to score genetic variants for regulatory potential. Each variant receives a score from 1a (highest regulatory confidence: eQTL + TF binding + DNase accessibility + motif + chromatin) to 7 (no known regulatory function). The v2 REST API supports single-variant queries, batch scoring, and region-based searches. Access is free and requires no authentication.

## When to Use

- Prioritizing GWAS hits for regulatory follow-up — identify which SNPs land in active regulatory elements
- Annotating a VCF or variant list with regulatory scores to filter to functionally relevant variants
- Identifying which transcription factors bind near a variant of interest
- Checking whether a non-coding variant overlaps an eQTL and active chromatin simultaneously
- Retrieving all high-confidence regulatory variants in a genomic region for cis-regulatory analysis
- Use `clinvar-database` instead when you need clinical pathogenicity classifications (ClinSig); RegulomeDB is for regulatory function, not germline disease association
- Use `gwas-database` instead when you want published GWAS associations with traits; RegulomeDB scores regulatory evidence regardless of trait association

## Prerequisites

- **Python packages**: `requests`, `pandas`, `matplotlib`
- **Data requirements**: rsIDs (e.g., `rs4946036`), genomic positions (`chr1:1000000`), or region coordinates (`chr1:1000000-2000000`)
- **Genome build**: GRCh38 (default) or GRCh37; specify in all requests
- **Rate limits**: No published rate limits; use `time.sleep(0.3)` between requests in batch workflows

```bash
pip install requests pandas matplotlib
```

## Quick Start

```python
import requests

def regulome_score(variant, genome="GRCh38"):
    """Score a single variant (rsID or chr:pos) for regulatory function."""
    r = requests.post(
        "https://regulomedb.org/regulome-search/",
        json={"variants": [variant], "genome": genome, "limit": 1},
        headers={"Content-Type": "application/json"}
    )
    r.raise_for_status()
    data = r.json()
    hits = data.get("variants", [])
    if not hits:
        return None
    v = hits[0]
    return {"rsid": variant, "score": v.get("regulomedb_score"), "chrom": v.get("chrom"), "pos": v.get("start")}

result = regulome_score("rs4946036")
print(f"Variant: {result['rsid']}  Score: {result['score']}  Position: {result['chrom']}:{result['pos']}")
# Variant: rs4946036  Score: 1b  Position: chr5:1295228
```

## Core API

### Query 1: Variant Scoring — Single rsID or Genomic Position

Post a single variant to the main search endpoint and retrieve its regulatory score.

```python
import requests

BASE = "https://regulomedb.org"

def score_variant(variant, genome="GRCh38"):
    """
    Score a single variant for regulatory potential.
    variant: rsID (e.g. 'rs4946036') or chr:pos (e.g. 'chr5:1295228')
    Returns: dict with score, coordinates, and hit count.
    """
    r = requests.post(
        f"{BASE}/regulome-search/",
        json={"variants": [variant], "genome": genome, "limit": 10},
        headers={"Content-Type": "application/json"},
        timeout=30
    )
    r.raise_for_status()
    data = r.json()
    hits = data.get("variants", [])
    if not hits:
        print(f"{variant}: no RegulomeDB annotation found")
        return None
    v = hits[0]
    print(f"Variant  : {v.get('rsids', [variant])}")
    print(f"Score    : {v.get('regulomedb_score')}")
    print(f"Location : {v.get('chrom')}:{v.get('start')}-{v.get('end')}")
    print(f"Evidence : {v.get('num_peaks', 0)} overlapping peaks")
    return v

result = score_variant("rs4946036")
```

```python
# Query by genomic coordinate instead of rsID
result = score_variant("chr17:43092919", genome="GRCh38")
# Covers TP53 region
```

### Query 2: Batch Variant Scoring — Multiple Variants

Score a list of variants in a single POST request; handle large lists in batches of 100.

```python
import requests, time, pandas as pd

BASE = "https://regulomedb.org"

def batch_score_variants(variants, genome="GRCh38", batch_size=100):
    """
    Score multiple variants and return a DataFrame of results.
    variants: list of rsIDs or chr:pos strings
    Returns: pd.DataFrame with columns [variant, score, chrom, pos, num_peaks]
    """
    records = []
    for i in range(0, len(variants), batch_size):
        batch = variants[i:i + batch_size]
        r = requests.post(
            f"{BASE}/regulome-search/",
            json={"variants": batch, "genome": genome, "limit": batch_size},
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        r.raise_for_status()
        data = r.json()
        for v in data.get("variants", []):
            records.append({
                "query": batch[len(records) % batch_size] if len(records) < len(batch) else "",
                "rsids": "; ".join(v.get("rsids", [])),
                "score": v.get("regulomedb_score"),
                "chrom": v.get("chrom"),
                "pos": v.get("start"),
                "num_peaks": v.get("num_peaks", 0),
            })
        if i + batch_size < len(variants):
            time.sleep(0.3)

    df = pd.DataFrame(records)
    print(f"Scored {len(df)} variants out of {len(variants)} queried")
    print(df["score"].value_counts().sort_index())
    return df

gwas_hits = [
    "rs4946036", "rs12345678", "rs7903146", "rs10811661",
    "rs1801282", "rs1799853", "rs662799",  "rs2268177"
]
df = batch_score_variants(gwas_hits)
df.to_csv("gwas_hits_regulome_scores.csv", index=False)
print(df[["rsids", "score", "chrom", "pos"]].head())
```

### Query 3: Region Search — Find Regulatory Variants in a Genomic Window

Retrieve all annotated variants within a chromosomal region using the GET endpoint.

```python
import requests, pandas as pd

BASE = "https://regulomedb.org"

def search_region(chrom, start, end, genome="GRCh38", limit=200):
    """
    Find all RegulomeDB-annotated variants in a genomic region.
    Returns: pd.DataFrame of variants with scores.
    """
    params = {
        "regions": f"{chrom}:{start}-{end}",
        "genome": genome,
        "limit": limit,
    }
    r = requests.get(f"{BASE}/regulome-search/", params=params, timeout=60)
    r.raise_for_status()
    data = r.json()
    variants = data.get("variants", [])
    print(f"Found {len(variants)} annotated variants in {chrom}:{start}-{end}")

    records = []
    for v in variants:
        records.append({
            "rsids": "; ".join(v.get("rsids", [])),
            "score": v.get("regulomedb_score"),
            "chrom": v.get("chrom"),
            "start": v.get("start"),
            "end": v.get("end"),
            "num_peaks": v.get("num_peaks", 0),
        })
    return pd.DataFrame(records)

# Search the BRCA1 promoter region (GRCh38)
df_region = search_region("chr17", 43_044_295, 43_125_370)
# Score 1a/1b = highest regulatory confidence
high_conf = df_region[df_region["score"].isin(["1a", "1b", "2a", "2b"])]
print(f"High-confidence regulatory variants: {len(high_conf)}")
print(df_region.sort_values("score").head(10).to_string(index=False))
```

### Query 4: Annotation Details — Full Regulatory Evidence for a Variant

Retrieve the complete evidence set for a variant: TF names, histone marks, eQTL status, motif hits.

```python
import requests

BASE = "https://regulomedb.org"

def get_annotation_details(variant, genome="GRCh38"):
    """
    Fetch full regulatory annotation details for a single variant.
    Returns raw JSON response with peak-level evidence.
    """
    r = requests.post(
        f"{BASE}/regulome-search/",
        json={"variants": [variant], "genome": genome, "limit": 1},
        headers={"Content-Type": "application/json"},
        timeout=30
    )
    r.raise_for_status()
    data = r.json()
    hits = data.get("variants", [])
    if not hits:
        print(f"No annotation found for {variant}")
        return None

    v = hits[0]
    print(f"=== {variant} | Score: {v.get('regulomedb_score')} ===")

    # Evidence breakdown
    peaks = v.get("peaks", [])
    tf_peaks = [p for p in peaks if p.get("assay_type") == "TF ChIP-seq"]
    dnase_peaks = [p for p in peaks if p.get("assay_type") == "DNase-seq"]
    histone_peaks = [p for p in peaks if "histone" in p.get("assay_type", "").lower()]

    print(f"TF binding sites    : {len(tf_peaks)}")
    print(f"DNase-seq peaks     : {len(dnase_peaks)}")
    print(f"Histone mark peaks  : {len(histone_peaks)}")

    # List unique TFs
    tfs = sorted(set(p.get("target", {}).get("label", "Unknown") for p in tf_peaks))
    print(f"TFs bound ({len(tfs)}): {', '.join(tfs[:10])}{'...' if len(tfs) > 10 else ''}")

    eqtls = v.get("eqtls", [])
    print(f"eQTL associations   : {len(eqtls)}")
    for eq in eqtls[:3]:
        print(f"  Gene: {eq.get('gene_name')}  Tissue: {eq.get('tissue')}")

    return v

detail = get_annotation_details("rs4946036")
```

### Query 5: Summary Statistics — Score Distribution in a Region

Get counts of variants by regulatory score category using the summary endpoint.

```python
import requests

BASE = "https://regulomedb.org"

def get_region_summary(chrom, start, end, genome="GRCh38"):
    """
    Retrieve summary statistics: count of variants per score category in a region.
    Returns: dict mapping score → count.
    """
    r = requests.post(
        f"{BASE}/regulome-summary/",
        json={"regions": [f"{chrom}:{start}-{end}"], "genome": genome},
        headers={"Content-Type": "application/json"},
        timeout=30
    )
    r.raise_for_status()
    data = r.json()
    summary = data.get("summary", {})
    print(f"Regulatory score summary for {chrom}:{start}-{end}")
    score_order = ["1a", "1b", "2a", "2b", "2c", "3a", "3b", "4", "5", "6", "7"]
    for score in score_order:
        count = summary.get(score, 0)
        bar = "#" * min(count, 40)
        print(f"  Score {score:3s}: {count:5d}  {bar}")
    total = sum(summary.values())
    print(f"  Total annotated: {total}")
    return summary

# TP53 locus region summary
summary = get_region_summary("chr17", 7_661_779, 7_687_538)
```

### Query 6: Dataset Information — Available Regulatory Datasets

List the regulatory datasets (cell types, assay types) included in RegulomeDB.

```python
import requests, pandas as pd

BASE = "https://regulomedb.org"

def list_datasets(assay_type=None):
    """
    List available regulatory datasets (cell types and assay types).
    assay_type: optional filter, e.g. 'TF ChIP-seq', 'DNase-seq', 'Histone ChIP-seq'
    Returns: pd.DataFrame of datasets.
    """
    params = {"format": "json"}
    if assay_type:
        params["assay_type"] = assay_type

    r = requests.get(f"{BASE}/regulome-datasets/", params=params, timeout=30)
    r.raise_for_status()
    data = r.json()
    datasets = data.get("datasets", [])
    print(f"Total datasets: {len(datasets)}")

    records = []
    for ds in datasets[:20]:  # show first 20
        records.append({
            "dataset_id": ds.get("@id", "").split("/")[-2],
            "assay_type": ds.get("assay_type"),
            "biosample": ds.get("biosample_term_name"),
            "target": ds.get("target", {}).get("label", ""),
        })
    df = pd.DataFrame(records)
    print(df.to_string(index=False))
    return df

df_datasets = list_datasets(assay_type="TF ChIP-seq")
print(f"\nUnique cell types: {df_datasets['biosample'].nunique()}")
```

## Key Concepts

### RegulomeDB Scoring Schema

RegulomeDB scores encode the type and strength of regulatory evidence overlapping a variant:

| Score | Evidence | Regulatory Confidence |
|-------|----------|-----------------------|
| 1a | eQTL + TF binding + DNase + motif + chromatin | Highest |
| 1b | TF binding + DNase + motif + chromatin (no eQTL) | Very high |
| 2a | TF binding + DNase + motif | High |
| 2b | TF binding + DNase (no motif) | High |
| 2c | TF binding only (with DNase) | Moderate-high |
| 3a | DNase + motif | Moderate |
| 3b | Motif only | Moderate |
| 4 | Single TF binding evidence | Low-moderate |
| 5 | Chromatin accessibility only | Low |
| 6 | Other regulatory evidence | Minimal |
| 7 | No known regulatory function | None |

Scores 1a–2b are the most actionable for prioritizing GWAS hits or regulatory variant interpretation. Score 7 means the variant has not been overlapped by any ENCODE/Roadmap regulatory dataset.

### Variant Input Formats

RegulomeDB accepts three input formats for variants:

```python
# Format 1: rsID (resolved to GRCh38 coordinates internally)
variants_rsid = ["rs4946036", "rs7903146", "rs12345678"]

# Format 2: chr:pos (single nucleotide position)
variants_pos = ["chr5:1295228", "chr10:112998251", "chr3:185511687"]

# Format 3: chr:start-end (short range, typically SNP-sized)
variants_range = ["chr17:43092919-43092920", "chr7:117548628-117548629"]

# Mix all formats in one request
mixed = variants_rsid + variants_pos
```

## Common Workflows

### Workflow 1: GWAS Hit Prioritization

**Goal**: Take a list of GWAS lead SNPs and identify which have strong regulatory evidence for functional follow-up.

```python
import requests, time, pandas as pd
import matplotlib.pyplot as plt

BASE = "https://regulomedb.org"

# GWAS lead SNPs from a type 2 diabetes GWAS
gwas_snps = [
    "rs7903146",   # TCF7L2 locus
    "rs10811661",  # CDKN2A/B locus
    "rs1801282",   # PPARG locus
    "rs4946036",   # PCSK1 locus
    "rs2268177",   # HNF4A locus
    "rs11605924",  # CRY2 locus
    "rs10830963",  # MTNR1B locus
    "rs1111875",   # HHEX locus
]

records = []
for snp in gwas_snps:
    r = requests.post(
        f"{BASE}/regulome-search/",
        json={"variants": [snp], "genome": "GRCh38", "limit": 1},
        headers={"Content-Type": "application/json"},
        timeout=30
    )
    r.raise_for_status()
    data = r.json()
    hits = data.get("variants", [])
    if hits:
        v = hits[0]
        peaks = v.get("peaks", [])
        tfs = [p.get("target", {}).get("label", "") for p in peaks if p.get("assay_type") == "TF ChIP-seq"]
        records.append({
            "snp": snp,
            "score": v.get("regulomedb_score"),
            "num_peaks": v.get("num_peaks", 0),
            "num_tfs": len(set(tfs)),
            "has_eqtl": len(v.get("eqtls", [])) > 0,
        })
    else:
        records.append({"snp": snp, "score": "7", "num_peaks": 0, "num_tfs": 0, "has_eqtl": False})
    time.sleep(0.3)

df = pd.DataFrame(records)
df["score_numeric"] = df["score"].str.replace("a", ".1").str.replace("b", ".2").str.replace("c", ".3").astype(float)
df_sorted = df.sort_values("score_numeric")

print("=== GWAS Hit Regulatory Prioritization ===")
print(df_sorted[["snp", "score", "num_peaks", "num_tfs", "has_eqtl"]].to_string(index=False))
print(f"\nHigh-confidence variants (score ≤ 2b): {(df['score_numeric'] <= 2.2).sum()}")
df_sorted.to_csv("gwas_regulatory_priority.csv", index=False)

# Bar chart of score distribution
fig, ax = plt.subplots(figsize=(10, 4))
score_counts = df["score"].value_counts().sort_index()
ax.bar(score_counts.index, score_counts.values, color="steelblue", edgecolor="black")
ax.set_xlabel("RegulomeDB Score")
ax.set_ylabel("Number of Variants")
ax.set_title("Regulatory Score Distribution of GWAS Lead SNPs")
plt.tight_layout()
plt.savefig("gwas_score_distribution.png", dpi=150, bbox_inches="tight")
print("Saved gwas_score_distribution.png")
```

### Workflow 2: TF Binding Heatmap for a Variant Set

**Goal**: Retrieve annotation details for multiple variants and visualize which TFs bind near each variant.

```python
import requests, time, pandas as pd
import matplotlib.pyplot as plt
import numpy as np

BASE = "https://regulomedb.org"

variants = ["rs4946036", "rs7903146", "rs10811661", "rs1801282", "rs2268177"]

all_tfs = set()
variant_tfs = {}

for snp in variants:
    r = requests.post(
        f"{BASE}/regulome-search/",
        json={"variants": [snp], "genome": "GRCh38", "limit": 1},
        headers={"Content-Type": "application/json"},
        timeout=30
    )
    r.raise_for_status()
    data = r.json()
    hits = data.get("variants", [])
    if not hits:
        variant_tfs[snp] = {}
        continue
    v = hits[0]
    peaks = v.get("peaks", [])
    tfs = [p.get("target", {}).get("label", "Unknown")
           for p in peaks if p.get("assay_type") == "TF ChIP-seq"]
    tf_counts = {}
    for tf in tfs:
        tf_counts[tf] = tf_counts.get(tf, 0) + 1
    variant_tfs[snp] = tf_counts
    all_tfs.update(tf_counts.keys())
    time.sleep(0.3)

# Build heatmap matrix
tf_list = sorted(all_tfs - {"Unknown"})[:30]  # top 30 unique TFs
matrix = np.zeros((len(variants), len(tf_list)))
for i, snp in enumerate(variants):
    for j, tf in enumerate(tf_list):
        matrix[i, j] = variant_tfs[snp].get(tf, 0)

fig, ax = plt.subplots(figsize=(max(14, len(tf_list) * 0.5), len(variants) * 0.8 + 2))
im = ax.imshow(matrix, cmap="YlOrRd", aspect="auto")
ax.set_xticks(range(len(tf_list)))
ax.set_xticklabels(tf_list, rotation=90, fontsize=8)
ax.set_yticks(range(len(variants)))
ax.set_yticklabels(variants, fontsize=9)
ax.set_title("TF ChIP-seq Peak Overlap per Variant (peak count)")
plt.colorbar(im, ax=ax, label="Number of overlapping peaks")
plt.tight_layout()
plt.savefig("variant_tf_heatmap.png", dpi=150, bbox_inches="tight")
print(f"Saved variant_tf_heatmap.png  ({len(variants)} variants × {len(tf_list)} TFs)")
```

## Key Parameters

| Parameter | Endpoint | Default | Range / Options | Effect |
|-----------|----------|---------|-----------------|--------|
| `variants` | POST /regulome-search/ | required | list of rsIDs or chr:pos | Variants to score |
| `genome` | All | `"GRCh38"` | `"GRCh38"`, `"GRCh37"` | Reference genome assembly |
| `limit` | POST /regulome-search/ | `10` | `1`–`1000` | Max variants returned per request |
| `regions` | GET /regulome-search/ | required | `"chrN:start-end"` | Genomic region for region search |
| `assay_type` | GET /regulome-datasets/ | — | `"TF ChIP-seq"`, `"DNase-seq"`, `"Histone ChIP-seq"` | Filter datasets by assay |
| `format` | GET endpoints | `"json"` | `"json"`, `"tsv"` | Response format |

## Best Practices

1. **Interpret scores in context**: Scores 1a–2b indicate multi-evidence regulatory annotation, but do not guarantee causality. A score of 7 means absence of evidence in RegulomeDB's curated datasets, not evidence of absence of regulation.

2. **Use region search for locus-level analysis**: When analyzing a GWAS locus, use `GET /regulome-search/?regions=` to retrieve all annotated variants in the LD block, then filter by score and linkage disequilibrium data.

3. **Add `time.sleep(0.3)` in loops**: RegulomeDB has no published rate limit, but polite usage prevents server load issues that produce connection timeouts in long batch runs.

4. **Cross-reference eQTL data**: Variants with score 1a have RegulomeDB-integrated eQTL evidence. Always verify eQTL tissue specificity (GTEx tissue list in the `eqtls` field) before drawing biological conclusions.

5. **Prefer rsIDs over coordinates for reproducibility**: When sharing results, store rsIDs alongside coordinates — RegulomeDB's internal coordinate system is GRCh38, and position-based queries are build-specific.

## Common Recipes

### Recipe: Check Score for a Single rsID

When to use: Quick lookup for one variant before running a full batch analysis.

```python
import requests

def quick_score(rsid, genome="GRCh38"):
    r = requests.post(
        "https://regulomedb.org/regulome-search/",
        json={"variants": [rsid], "genome": genome, "limit": 1},
        headers={"Content-Type": "application/json"},
        timeout=20
    )
    r.raise_for_status()
    hits = r.json().get("variants", [])
    score = hits[0].get("regulomedb_score") if hits else "not found"
    print(f"{rsid}: RegulomeDB score = {score}")
    return score

quick_score("rs4946036")   # Expected: 1b (strong regulatory evidence)
quick_score("rs12345678")  # Expected: 5 or 7 (weak/no evidence)
```

### Recipe: Filter Variants to High-Confidence Regulatory Set

When to use: Downstream prioritization — keep only variants with strong regulatory evidence (scores 1a–2b).

```python
import pandas as pd

df = pd.read_csv("gwas_regulatory_priority.csv")

REGULATORY_SCORES = {"1a", "1b", "2a", "2b"}
high_conf = df[df["score"].isin(REGULATORY_SCORES)].copy()
print(f"Total variants   : {len(df)}")
print(f"High-confidence  : {len(high_conf)}  ({100 * len(high_conf) / len(df):.1f}%)")
print(high_conf[["snp", "score", "num_tfs", "has_eqtl"]].to_string(index=False))
high_conf.to_csv("high_confidence_regulatory_variants.csv", index=False)
```

### Recipe: Identify eQTL-Linked Regulatory Variants

When to use: Integrate RegulomeDB eQTL evidence to find variants that affect gene expression through regulatory elements.

```python
import requests, time

BASE = "https://regulomedb.org"

def get_eqtl_variants(variant_list, genome="GRCh38"):
    """Return variants that have both high regulatory score and eQTL evidence."""
    eqtl_variants = []
    for snp in variant_list:
        r = requests.post(
            f"{BASE}/regulome-search/",
            json={"variants": [snp], "genome": genome, "limit": 1},
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        r.raise_for_status()
        hits = r.json().get("variants", [])
        if not hits:
            time.sleep(0.3)
            continue
        v = hits[0]
        eqtls = v.get("eqtls", [])
        score = v.get("regulomedb_score", "7")
        if eqtls and score in {"1a", "1b", "2a", "2b"}:
            for eq in eqtls:
                eqtl_variants.append({
                    "snp": snp,
                    "score": score,
                    "gene": eq.get("gene_name"),
                    "tissue": eq.get("tissue"),
                    "slope": eq.get("slope"),
                })
        time.sleep(0.3)
    return eqtl_variants

snps = ["rs4946036", "rs7903146", "rs10811661"]
results = get_eqtl_variants(snps)
for r in results:
    print(f"{r['snp']}  Score={r['score']}  Gene={r['gene']}  Tissue={r['tissue']}")
```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `HTTP 400` on POST request | Malformed JSON body or missing `Content-Type` header | Add `headers={"Content-Type": "application/json"}` and use `json=` kwarg, not `data=` |
| Empty `variants` list in response | Variant not in RegulomeDB index | Try alternate input format (rsID → chr:pos, or vice versa); some rare variants are absent |
| `ConnectionError` or timeout | Server timeout on large batch | Reduce batch size to 50; add `time.sleep(0.5)` between batches |
| Score is `"7"` for all variants | Using GRCh37 coordinates with `genome="GRCh38"` | Specify `"genome": "GRCh37"` or liftover coordinates to GRCh38 before querying |
| `peaks` field is empty but score is not `"7"` | Score assigned from summary-level evidence, not peak-level | Scores are computed from multiple evidence types; peak list may be incomplete in API response |
| Region search returns 0 results | Region is too small or on an uncharacterized chromosome | Use at least 10 kb windows; avoid alternative contigs (chrUn_*, random_*) |

## Related Skills

- `gwas-database` — NHGRI-EBI GWAS Catalog for published SNP-trait associations; use alongside RegulomeDB to prioritize GWAS hits
- `clinvar-database` — Clinical pathogenicity classifications; complements RegulomeDB's functional regulatory evidence
- `encode-database` — Direct ENCODE REST API access for TF ChIP-seq and ATAC-seq peak sets that underlie RegulomeDB scores
- `ensembl-database` — Variant annotation and gene coordinate lookup; use to map rsIDs to genomic positions

## References

- [RegulomeDB Official Help](https://regulomedb.org/regulome-help/) — Full documentation and scoring schema
- [RegulomeDB API endpoint](https://regulomedb.org/regulome-search/) — Main REST API endpoint reference
- Boyle AP et al. "Annotation of functional variation in personal genomes using RegulomeDB." *Genome Research* 22(9): 1790–1797 (2012). https://doi.org/10.1101/gr.137323.112
- Dong S et al. "Annotating genomic variants and their functional effects using RegulomeDB 2.0." *Bioinformatics* 35(24): 5341–5343 (2019). https://doi.org/10.1093/bioinformatics/btz560
