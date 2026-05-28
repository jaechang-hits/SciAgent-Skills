---
name: "regulomedb-database"
description: "Query RegulomeDB v2 GET REST API to score variants for regulatory function and retrieve overlapping evidence (TF binding, histone marks, DNase peaks, footprints, motifs, eQTLs, chromatin state). Scores range 1a (strongest) to 7 (none). Use for GWAS hit prioritization, regulatory variant annotation, cis-regulatory discovery. Use clinvar-database for pathogenicity; gwas-database for trait associations."
license: "CC-BY-4.0"
---

# RegulomeDB Database

## Overview

RegulomeDB integrates large-scale functional genomics data (ENCODE, Roadmap Epigenomics) to score genetic variants for regulatory potential. Each variant receives a ranking from 1a (highest regulatory confidence: eQTL + TF + DNase + motif + chromatin) to 7 (no known regulatory function). The v2 API is exposed as **GET** `https://regulomedb.org/regulome-search/`; the legacy POST `/regulome-search/`, POST `/regulome-summary/`, and GET `/regulome-datasets/` JSON endpoints are no longer functional (return `regulome-notfound` stubs or 500). Access is free and requires no authentication.

## When to Use

- Prioritizing GWAS hits for regulatory follow-up — identify which SNPs land in active regulatory elements
- Annotating a VCF or variant list with regulatory scores to filter to functionally relevant variants
- Identifying which transcription factors bind near a variant of interest (via the `@graph` evidence rows)
- Checking whether a non-coding variant overlaps a QTL and active chromatin simultaneously (`features.QTL`)
- Retrieving all annotated rsIDs in a genomic region for cis-regulatory analysis (region query with `nearby_snps`)
- Use `clinvar-database` instead when you need clinical pathogenicity classifications; RegulomeDB scores regulatory function, not germline disease association
- Use `gwas-database` instead when you want published GWAS associations with traits

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

BASE = "https://regulomedb.org"

def regulome_score(variant, genome="GRCh38"):
    """Score a single variant (rsID or chr:pos-pos) via the GET /regulome-search/ endpoint."""
    r = requests.get(
        f"{BASE}/regulome-search/",
        params={"regions": variant, "genome": genome, "format": "json"},
        timeout=30,
    )
    r.raise_for_status()
    d = r.json()
    rs = d.get("regulome_score", {})
    vs = d.get("variants", [])
    return {
        "query": variant,
        "ranking": rs.get("ranking"),           # 1a / 1b / ... / 7
        "probability": float(rs.get("probability", 0)),
        "rsids": vs[0].get("rsids") if vs else [],
        "chrom": vs[0].get("chrom") if vs else None,
        "pos": vs[0].get("start") if vs else None,
    }

print(regulome_score("rs4946036"))
# {'query': 'rs4946036', 'ranking': '7', 'probability': 0.18412,
#  'rsids': ['rs4946036'], 'chrom': 'chr6', 'pos': 114819799}
```

## Core API

### Query 1: Score a Single Variant (rsID or position)

The GET `/regulome-search/` endpoint accepts an rsID or coordinate as `regions=`. Returns a `regulome_score` block (probability, ranking, tissue-specific scores) plus `features` flags and the per-dataset `@graph` evidence rows.

```python
import requests

BASE = "https://regulomedb.org"

def score_variant(variant, genome="GRCh38"):
    """Return the regulome_score block and resolved coordinates."""
    r = requests.get(
        f"{BASE}/regulome-search/",
        params={"regions": variant, "genome": genome, "format": "json"},
        timeout=30,
    )
    r.raise_for_status()
    d = r.json()
    rs = d.get("regulome_score", {})
    vs = d.get("variants", [])
    feats = d.get("features", {})
    print(f"Variant   : {variant}")
    print(f"Resolved  : {vs[0]['chrom']}:{vs[0]['start']} ({', '.join(vs[0].get('rsids', []))})")
    print(f"Ranking   : {rs.get('ranking')}  prob={rs.get('probability')}")
    print(f"Features  : ChIP={feats['ChIP']} Chromatin_accessibility={feats['Chromatin_accessibility']} "
          f"QTL={feats['QTL']} Footprint={feats['Footprint']} PWM_matched={feats['PWM_matched']}")
    return d

# Strong-regulatory locus example
score_variant("chr11:5226739-5226740")
# Ranking: 1a (HBB beta-globin promoter, multi-evidence)
```

```python
# Score by chromosomal position alone
score_variant("chr17:7670000-7670001")  # TP53 region
```

### Query 2: Region Scan — List Annotated Variants in a Window

A range query returns up to `limit` resolved variants (`variants[]`) and all `@graph` evidence rows in the window, plus `nearby_snps` (rsIDs adjacent to the resolved hits).

```python
import requests, pandas as pd

BASE = "https://regulomedb.org"

def scan_region(chrom, start, end, genome="GRCh38", limit=200):
    """List variants in a region with their resolved positions and overlapping rsIDs."""
    r = requests.get(
        f"{BASE}/regulome-search/",
        params={"regions": f"{chrom}:{start}-{end}", "genome": genome,
                "format": "json", "limit": limit},
        timeout=60,
    )
    r.raise_for_status()
    d = r.json()
    variants = d.get("variants", [])
    print(f"Variants in {chrom}:{start}-{end}: {len(variants)} (total indexed = {d.get('total')})")
    rows = [{"rsids": ", ".join(v.get("rsids", [])),
             "chrom": v.get("chrom"),
             "start": v.get("start"),
             "end": v.get("end")} for v in variants]
    return pd.DataFrame(rows)

df = scan_region("chr11", 5226000, 5227000)
print(df.head(10).to_string(index=False))
```

### Query 3: Full Evidence — Parse the `@graph` Rows

Each `@graph[i]` row is one experimental piece of evidence overlapping the query. Fields: `method, target_label, biosample_ontology{term_name, organ_slims, classification}, dataset, file, value, chrom, start, end, strand, ancestry, disease_term_name`.

```python
import requests, pandas as pd

BASE = "https://regulomedb.org"

def evidence_rows(variant, genome="GRCh38"):
    r = requests.get(
        f"{BASE}/regulome-search/",
        params={"regions": variant, "genome": genome, "format": "json"},
        timeout=60,
    )
    r.raise_for_status()
    g = r.json().get("@graph", [])
    rows = []
    for row in g:
        bs = row.get("biosample_ontology") or {}
        rows.append({
            "method": row.get("method"),
            "target_label": row.get("target_label"),
            "biosample": bs.get("term_name"),
            "organ_slims": ", ".join(bs.get("organ_slims") or []),
            "dataset": row.get("dataset", "").split("/")[-2] if row.get("dataset") else None,
            "value": row.get("value"),
        })
    return pd.DataFrame(rows)

df_evidence = evidence_rows("chr11:5226739-5226740")
# Each method is one of: ChIP-seq, Histone ChIP-seq, ATAC-seq, DNase-seq,
# footprints, PWMs, chromatin state, eQTLs
print(df_evidence["method"].value_counts())
```

### Query 4: TF ChIP-seq Hits — Filter Evidence by Method

To list the transcription factors binding near a variant, filter `@graph` rows where `method == "ChIP-seq"` and read `target_label` + `biosample_ontology.term_name`.

```python
import requests, pandas as pd

BASE = "https://regulomedb.org"

def tf_binding(variant, genome="GRCh38"):
    r = requests.get(f"{BASE}/regulome-search/",
                     params={"regions": variant, "genome": genome, "format": "json"},
                     timeout=60)
    r.raise_for_status()
    rows = []
    for g in r.json().get("@graph", []):
        if g.get("method") != "ChIP-seq":
            continue
        bs = g.get("biosample_ontology") or {}
        rows.append({
            "tf": g.get("target_label"),
            "biosample": bs.get("term_name"),
            "classification": bs.get("classification"),
        })
    return pd.DataFrame(rows)

df_tfs = tf_binding("chr11:5226739-5226740")
print(f"TF ChIP-seq peaks overlapping query: {len(df_tfs)}")
print(df_tfs.groupby("tf").size().sort_values(ascending=False).head(10))
```

### Query 5: Tissue-Specific Regulatory Score

`regulome_score.tissue_specific_scores` maps ~50 tissues to per-tissue regulatory probabilities (0–1). Rank tissues to identify where the variant has the strongest regulatory signal.

```python
import requests, pandas as pd

BASE = "https://regulomedb.org"

def tissue_scores(variant, genome="GRCh38", top_n=10):
    r = requests.get(f"{BASE}/regulome-search/",
                     params={"regions": variant, "genome": genome, "format": "json"},
                     timeout=30)
    r.raise_for_status()
    ts = r.json().get("regulome_score", {}).get("tissue_specific_scores", {})
    s = pd.Series({k: float(v) for k, v in ts.items()})
    return s.sort_values(ascending=False).head(top_n)

print("Top tissues by regulatory probability for chr11:5226739-5226740:")
print(tissue_scores("chr11:5226739-5226740"))
```

### Query 6: Nearby SNPs — List rsIDs Adjacent to a Position

`nearby_snps` carries dbSNP rsIDs near the resolved coordinates, with reference/alt allele frequencies (when GnomAD-indexed).

```python
import requests, pandas as pd

BASE = "https://regulomedb.org"

def nearby(variant, genome="GRCh38"):
    r = requests.get(f"{BASE}/regulome-search/",
                     params={"regions": variant, "genome": genome, "format": "json"},
                     timeout=30)
    r.raise_for_status()
    rows = []
    for s in r.json().get("nearby_snps", []):
        rows.append({
            "rsid": s.get("rsid"),
            "chrom": s.get("chrom"),
            "pos": s.get("coordinates", {}).get("gte"),
            "type": s.get("variation_type"),
            "maf": s.get("maf"),
        })
    return pd.DataFrame(rows)

df_nearby = nearby("rs4946036")
print(f"Nearby SNPs to rs4946036: {len(df_nearby)}")
print(df_nearby.head(10).to_string(index=False))
```

## Key Concepts

### RegulomeDB Scoring Schema

RegulomeDB ranks encode the strength of evidence overlapping a variant. The `regulome_score.ranking` string is one of:

| Ranking | Evidence | Confidence |
|---------|----------|------------|
| 1a | eQTL + TF + DNase + motif + matched footprint | Highest |
| 1b–1f | Multi-evidence (sub-ranks reflect which inputs match) | Very high |
| 2a | TF binding + DNase + motif | High |
| 2b | TF binding + any DNase (no motif required) | High |
| 2c | TF binding + DNase (limited) | Moderate-high |
| 3a | DNase + motif (no TF ChIP-seq) | Moderate |
| 3b | Motif only (no DNase) | Moderate |
| 4 | Single TF binding evidence | Low-moderate |
| 5 | DNase peak only | Low |
| 6 | Other regulatory evidence | Minimal |
| 7 | No known regulatory function | None |

`regulome_score.probability` is the numeric model score (0–1) underlying the discrete ranking.

### `features` Booleans vs `@graph` Detail

`features` is a high-level summary — boolean flags indicating presence of `ChIP`, `Chromatin_accessibility`, `Footprint`, `PWM`, `QTL`, etc. For per-dataset detail (which exact TF / cell type / experiment), iterate `@graph[]` and filter by `method`.

### Variant Input Formats

`regions=` accepts:

```python
# rsID — resolved server-side to current-build coordinates
"rs4946036"

# Single-position range
"chr11:5226739-5226740"

# Wider region (returns multiple variants[] entries + larger @graph)
"chr11:5226000-5227000"
```

## Common Workflows

### Workflow 1: GWAS Hit Prioritization

**Goal**: Score a list of GWAS lead SNPs and rank by regulatory confidence.

```python
import requests, time, pandas as pd
import matplotlib.pyplot as plt

BASE = "https://regulomedb.org"

gwas_snps = ["rs7903146", "rs10811661", "rs1801282", "rs4946036",
             "rs2268177", "rs10830963", "rs1111875"]

records = []
for snp in gwas_snps:
    r = requests.get(f"{BASE}/regulome-search/",
                     params={"regions": snp, "genome": "GRCh38", "format": "json"},
                     timeout=30)
    r.raise_for_status()
    d = r.json()
    rs = d.get("regulome_score", {})
    feats = d.get("features", {})
    g = d.get("@graph", [])
    tfs = sorted({row["target_label"] for row in g
                  if row.get("method") == "ChIP-seq" and row.get("target_label")})
    records.append({
        "snp": snp,
        "ranking": rs.get("ranking"),
        "probability": float(rs.get("probability", 0)),
        "has_qtl": feats.get("QTL", False),
        "tf_count": len(tfs),
        "num_evidence_rows": len(g),
    })
    time.sleep(0.3)

df = pd.DataFrame(records).sort_values("probability", ascending=False)
print(df.to_string(index=False))
df.to_csv("gwas_regulatory_priority.csv", index=False)

fig, ax = plt.subplots(figsize=(8, 4))
ax.bar(df["snp"], df["probability"], color="steelblue", edgecolor="black")
ax.set_ylabel("Regulatory probability")
ax.set_title("GWAS lead-SNP regulatory probabilities")
plt.xticks(rotation=45, ha="right")
plt.tight_layout()
plt.savefig("gwas_score_distribution.png", dpi=150, bbox_inches="tight")
```

### Workflow 2: Locus Evidence Profile

**Goal**: Summarize the methods underlying the score at a locus (e.g., HBB promoter).

```python
import requests, pandas as pd
import matplotlib.pyplot as plt

BASE = "https://regulomedb.org"

def locus_profile(region, genome="GRCh38"):
    r = requests.get(f"{BASE}/regulome-search/",
                     params={"regions": region, "genome": genome, "format": "json"},
                     timeout=60)
    r.raise_for_status()
    d = r.json()
    rs = d.get("regulome_score", {})
    g = d.get("@graph", [])
    counts = pd.Series([row.get("method") for row in g]).value_counts()
    print(f"\n=== {region} | ranking={rs.get('ranking')} prob={rs.get('probability')} ===")
    print(counts.to_string())
    return counts

counts = locus_profile("chr11:5226739-5226740")  # HBB

fig, ax = plt.subplots(figsize=(8, 4))
counts.plot(kind="barh", color="seagreen", ax=ax)
ax.set_xlabel("Evidence rows in @graph")
ax.set_title("Regulatory evidence by method (HBB promoter)")
plt.tight_layout()
plt.savefig("locus_evidence_profile.png", dpi=150, bbox_inches="tight")
```

## Key Parameters

| Parameter | Endpoint | Default | Range / Options | Effect |
|-----------|----------|---------|-----------------|--------|
| `regions` | GET /regulome-search/ | required | rsID, `chrN:start-end`, or `chrN:pos-pos` | Variant/region to score |
| `genome` | GET /regulome-search/ | `"GRCh38"` | `"GRCh38"`, `"GRCh37"` | Reference genome assembly |
| `format` | GET /regulome-search/ | `"html"` | `"json"`, `"tsv"`, `"html"` | Use `"json"` for programmatic access |
| `limit` | GET /regulome-search/ | `200` | `1`–`1000` | Max resolved variants in `variants[]` for region queries |
| `from` | GET /regulome-search/ | `0` | non-negative int | Offset for paging through large `@graph` lists |

## Best Practices

1. **Use GET, not POST.** The POST `/regulome-search/`, POST `/regulome-summary/`, and GET `/regulome-datasets/` JSON endpoints return a `regulome-notfound` stub or HTTP 500. Only `GET /regulome-search/?regions=...&genome=...&format=json` returns real data.

2. **Read `regulome_score.ranking`, not `regulomedb_score`.** The field used to be named `regulomedb_score` in legacy docs; the live API exposes it as `regulome_score.ranking` (string like `"1a"`, `"7"`).

3. **Add `time.sleep(0.3)` between calls.** RegulomeDB has no published rate limit, but polite spacing prevents intermittent 502s under load.

4. **Score 7 ≠ "no regulation".** Score 7 means absence of evidence in RegulomeDB's curated datasets, not biological absence of regulation. Cross-check with ENCODE/Roadmap directly via `encode-database` for negative results.

5. **For tissue specificity, use `tissue_specific_scores`.** The single `ranking` is an aggregate; the per-tissue probabilities reveal where the variant has the strongest regulatory signal.

6. **Watch the GRCh37 vs GRCh38 build.** rsIDs are auto-resolved to the requested build, but coordinate-based `regions=chrN:start-end` queries are build-specific — pass the matching `genome=` value.

## Common Recipes

### Recipe: Quick Score Lookup

When to use: One-off check before kicking off a larger pipeline.

```python
import requests

def quick_score(variant, genome="GRCh38"):
    r = requests.get("https://regulomedb.org/regulome-search/",
                     params={"regions": variant, "genome": genome, "format": "json"},
                     timeout=20)
    r.raise_for_status()
    rs = r.json().get("regulome_score", {})
    print(f"{variant}: ranking={rs.get('ranking')}  prob={rs.get('probability')}")

quick_score("rs4946036")             # ranking=7 prob=0.18412
quick_score("chr11:5226739-5226740") # ranking=1a (HBB promoter)
```

### Recipe: Filter Variants to High-Confidence Regulatory Set

```python
import requests, time, pandas as pd

HIGH_CONF = {"1a", "1b", "1c", "1d", "1e", "1f", "2a", "2b"}

def high_conf_only(variants, genome="GRCh38"):
    keep = []
    for v in variants:
        r = requests.get("https://regulomedb.org/regulome-search/",
                         params={"regions": v, "genome": genome, "format": "json"},
                         timeout=30)
        ranking = r.json().get("regulome_score", {}).get("ranking")
        if ranking in HIGH_CONF:
            keep.append({"variant": v, "ranking": ranking})
        time.sleep(0.3)
    return pd.DataFrame(keep)

df = high_conf_only(["rs4946036", "rs7903146", "chr11:5226739-5226740"])
print(df.to_string(index=False))
```

### Recipe: QTL-Linked Variants

When to use: Find variants with `features.QTL == True`, i.e. those overlapping a curated QTL row in `@graph` (method `"QTLs"`).

```python
import requests, time, pandas as pd

def qtl_overlap(variants, genome="GRCh38"):
    rows = []
    for v in variants:
        r = requests.get("https://regulomedb.org/regulome-search/",
                         params={"regions": v, "genome": genome, "format": "json"},
                         timeout=30)
        d = r.json()
        if not d.get("features", {}).get("QTL"):
            time.sleep(0.3); continue
        for g in d.get("@graph", []):
            if g.get("method") == "QTLs":
                rows.append({
                    "variant": v,
                    "ranking": d.get("regulome_score", {}).get("ranking"),
                    "qtl_target": g.get("target_label"),
                    "value": g.get("value"),
                    "biosample": (g.get("biosample_ontology") or {}).get("term_name"),
                })
        time.sleep(0.3)
    return pd.DataFrame(rows)

print(qtl_overlap(["rs4946036", "chr11:5226739-5226740"]))
```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| Response body `{"@id":"/regulome-notfound","@type":["regulome-help"]...}` | Using the legacy POST `/regulome-search/` with a JSON body | Switch to GET with `regions=` query param + `format=json` |
| HTTP 500 | Hitting the deprecated `/regulome-summary/` endpoint | Endpoint is dead; aggregate counts client-side from `@graph[].method` |
| `KeyError: 'regulomedb_score'` | Field renamed | Use `regulome_score.ranking` (string) and `regulome_score.probability` (float-as-string) |
| `peaks` / `eqtls` / `assay_type` missing | Old schema | Iterate `@graph[]` and filter by `method` (`ChIP-seq`, `DNase-seq`, `Histone ChIP-seq`, `ATAC-seq`, `footprints`, `PWMs`, `QTLs`, `chromatin state`) |
| Empty `variants[]` for an rsID | rsID not in RegulomeDB index or build mismatch | Try the chr:pos form; check `genome=` matches the coordinates |
| Region search returns 0 `@graph` rows | Region size too small or in an uncharacterized chromosome | Widen the window to ≥ 200 bp; avoid alt contigs (`chrUn_*`, `*_random`) |
| Region query truncates at 200 results | Default `limit=200` | Pass `limit=1000` or page with `from=0,200,400,...` |

## Related Skills

- `gwas-database` — NHGRI-EBI GWAS Catalog for published SNP-trait associations; pair with RegulomeDB to prioritize GWAS hits
- `clinvar-database` — Clinical pathogenicity classifications; complements RegulomeDB's functional regulatory evidence
- `encode-database` — Direct ENCODE REST API access for the TF ChIP-seq / ATAC-seq peak sets that underlie RegulomeDB scores
- `ensembl-database` — Variant annotation and gene coordinate lookup; use to map rsIDs to genomic positions before region queries

## References

- [RegulomeDB Official Help](https://regulomedb.org/regulome-help/) — Documentation and scoring schema
- [RegulomeDB search endpoint](https://regulomedb.org/regulome-search/) — Main REST API entry point (GET only)
- Boyle AP et al. "Annotation of functional variation in personal genomes using RegulomeDB." *Genome Research* 22(9): 1790–1797 (2012). https://doi.org/10.1101/gr.137323.112
- Dong S et al. "Annotating genomic variants and their functional effects using RegulomeDB 2.0." *Bioinformatics* 35(24): 5341–5343 (2019). https://doi.org/10.1093/bioinformatics/btz560
