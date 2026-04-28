---
name: "gnomad-database"
description: "gnomAD v4 population variant frequencies via GraphQL API. Allele counts and frequencies stratified by ancestry (AFR, AMR, EAS, NFE, SAS, FIN, ASJ, MID), gene-level constraint (pLI, LOEUF, missense z), and coverage. Identify rare or constrained variants. For clinical pathogenicity use clinvar-database; for GWAS use gwas-database."
license: "ODbL-1.0"
---

# gnomAD Database

## Overview

The Genome Aggregation Database (gnomAD) is a resource of aggregated exome and genome sequencing data from 730,000+ individuals. It provides population variant frequencies stratified by 9 ancestry groups, gene-level constraint scores (pLI, LOEUF), and read coverage information. Access is free via a GraphQL API at `https://gnomad.broadinstitute.org/api` — no authentication required, no official SDK.

## When to Use

- Checking whether a candidate variant is rare enough to be clinically relevant (AF < 0.1% in all populations)
- Retrieving allele frequencies stratified by ancestry group (AFR, AMR, EAS, NFE, SAS, FIN, ASJ, MID) for a variant
- Identifying all rare loss-of-function variants in a gene for burden testing or candidate prioritization
- Getting gene constraint metrics (pLI, LOEUF) to assess tolerance to loss-of-function variants
- Checking read depth coverage for a region to evaluate if low variant frequency reflects low sequencing coverage
- Filtering a VCF by population frequency — query gnomAD AF to discard common variants before clinical interpretation
- For clinical pathogenicity classifications use `clinvar-database`; gnomAD provides frequency evidence but does not classify pathogenicity
- For GWAS associations at the study level use `gwas-database`; gnomAD is for population frequency lookups

## Prerequisites

- **Python packages**: `requests`, `pandas`, `matplotlib`
- **Data requirements**: gene symbols (e.g., `BRCA1`), variant IDs (`1-69511-A-G` format, or rsIDs)
- **Environment**: internet connection; no API key required
- **Rate limits**: no official published limits; use `time.sleep(0.5)` between requests for polite access; avoid bursts over 10 requests/second

```bash
pip install requests pandas matplotlib
```

## Quick Start

```python
import requests
import time

GNOMAD_API = "https://gnomad.broadinstitute.org/api"

def gnomad_query(query: str, variables: dict = None) -> dict:
    """Execute a gnomAD GraphQL query and return the data payload."""
    payload = {"query": query, "variables": variables or {}}
    r = requests.post(GNOMAD_API, json=payload, timeout=30)
    r.raise_for_status()
    result = r.json()
    if "errors" in result:
        raise ValueError(f"GraphQL errors: {result['errors']}")
    return result["data"]

# Quick check: get pLI for BRCA1
query = """
query GeneConstraint($gene_symbol: String!, $reference_genome: ReferenceGenomeId!) {
  gene(gene_symbol: $gene_symbol, reference_genome: $reference_genome) {
    gnomad_constraint { pLI lof { oe_ci { upper } } }
  }
}
"""
data = gnomad_query(query, {"gene_symbol": "BRCA1", "reference_genome": "GRCh38"})
constraint = data["gene"]["gnomad_constraint"]
print(f"BRCA1 pLI: {constraint['pLI']:.3f}")
print(f"BRCA1 LOEUF: {constraint['lof']['oe_ci']['upper']:.3f}")
# BRCA1 pLI: 0.999
# BRCA1 LOEUF: 0.127
```

## Core API

### Query 1: Gene Variant Query

Fetch all variants in a gene with population allele frequencies. Returns a list of variants with their genome-level frequencies.

```python
import requests, time

GNOMAD_API = "https://gnomad.broadinstitute.org/api"

def gnomad_query(query, variables=None):
    r = requests.post(GNOMAD_API, json={"query": query, "variables": variables or {}}, timeout=30)
    r.raise_for_status()
    result = r.json()
    if "errors" in result:
        raise ValueError(f"GraphQL errors: {result['errors']}")
    return result["data"]

GENE_VARIANTS_QUERY = """
query GeneVariants($gene_symbol: String!, $reference_genome: ReferenceGenomeId!, $dataset: DatasetId!) {
  gene(gene_symbol: $gene_symbol, reference_genome: $reference_genome) {
    gene_id
    gene_name
    variants(dataset: $dataset) {
      variant_id
      rsids
      chrom
      pos
      ref
      alt
      consequence
      lof
      genome {
        an
        ac
        af
        faf95 { popmax popmax_population }
      }
    }
  }
}
"""

data = gnomad_query(GENE_VARIANTS_QUERY, {
    "gene_symbol": "PCSK9",
    "reference_genome": "GRCh38",
    "dataset": "gnomad_r4"
})
variants = data["gene"]["variants"]
print(f"Gene: {data['gene']['gene_name']} ({data['gene']['gene_id']})")
print(f"Total variants: {len(variants)}")
# Filter to rare variants (AF < 0.001)
rare = [v for v in variants if v["genome"] and v["genome"]["af"] is not None and v["genome"]["af"] < 0.001]
print(f"Rare variants (AF < 0.1%): {len(rare)}")
for v in rare[:3]:
    print(f"  {v['variant_id']} | {v['consequence']} | AF={v['genome']['af']:.2e}")
```

### Query 2: Variant Lookup

Fetch detailed information for a single variant by its gnomAD variant ID (CHROM-POS-REF-ALT format) or search by rsID.

```python
VARIANT_QUERY = """
query VariantDetails($variant_id: String!, $dataset: DatasetId!) {
  variant(variant_id: $variant_id, dataset: $dataset) {
    variant_id
    rsids
    chrom
    pos
    ref
    alt
    consequence
    lof
    lof_filter
    lof_flags
    genome {
      an
      ac
      af
      faf95 { popmax popmax_population }
      populations {
        id
        ac
        an
        af
      }
    }
  }
}
"""

data = gnomad_query(VARIANT_QUERY, {
    "variant_id": "1-55039974-G-T",   # PCSK9 p.Tyr142Ter (LoF)
    "dataset": "gnomad_r4"
})
v = data["variant"]
print(f"Variant: {v['variant_id']}")
print(f"rsIDs: {v['rsids']}")
print(f"Consequence: {v['consequence']}  |  LoF: {v['lof']}")
g = v["genome"]
print(f"Genome AF: {g['af']:.2e}  (AC={g['ac']}, AN={g['an']})")
print(f"FAF95 popmax: {g['faf95']['popmax']:.2e} in {g['faf95']['popmax_population']}")
```

### Query 3: Population Frequencies

Retrieve allele frequency broken down by ancestry group for a specific variant.

```python
import pandas as pd

POPULATION_FREQ_QUERY = """
query PopFreqs($variant_id: String!, $dataset: DatasetId!) {
  variant(variant_id: $variant_id, dataset: $dataset) {
    variant_id
    genome {
      populations {
        id
        ac
        an
        af
        homozygote_count
      }
    }
  }
}
"""

ANCESTRY_LABELS = {
    "afr": "African/African American",
    "amr": "Admixed American",
    "eas": "East Asian",
    "fin": "Finnish",
    "nfe": "Non-Finnish European",
    "sas": "South Asian",
    "asj": "Ashkenazi Jewish",
    "mid": "Middle Eastern",
    "oth": "Other",
}

data = gnomad_query(POPULATION_FREQ_QUERY, {
    "variant_id": "1-55039974-G-T",
    "dataset": "gnomad_r4"
})
pops = data["variant"]["genome"]["populations"]

# Filter to top-level ancestry groups (exclude sex-specific)
main_pops = [p for p in pops if p["id"] in ANCESTRY_LABELS and p["an"] > 0]
df = pd.DataFrame(main_pops)
df["label"] = df["id"].map(ANCESTRY_LABELS)
df = df.sort_values("af", ascending=False)
print(df[["label", "ac", "an", "af", "homozygote_count"]].to_string(index=False))
```

### Query 4: Coverage Query

Retrieve per-base read depth coverage for a gene region to assess data completeness.

```python
COVERAGE_QUERY = """
query Coverage($chrom: String!, $start: Int!, $stop: Int!, $dataset: DatasetId!) {
  coverage(dataset: $dataset, chrom: $chrom, start: $start, stop: $stop) {
    pos
    mean
    median
    over_1
    over_10
    over_20
    over_30
    over_100
  }
}
"""

data = gnomad_query(COVERAGE_QUERY, {
    "chrom": "1",
    "start": 55039700,
    "stop": 55040200,
    "dataset": "gnomad_r4"
})
cov = data["coverage"]
print(f"Coverage positions retrieved: {len(cov)}")
if cov:
    avg_mean = sum(c["mean"] for c in cov) / len(cov)
    pct_20x = sum(1 for c in cov if c["over_20"] > 0.9) / len(cov) * 100
    print(f"Average mean depth: {avg_mean:.1f}x")
    print(f"Positions with >90% samples at >=20x: {pct_20x:.1f}%")
    # Example single position
    c = cov[0]
    print(f"\nPosition {c['pos']}: mean={c['mean']:.1f}x, median={c['median']}x")
    print(f"  Fraction >=10x: {c['over_10']:.3f}, >=20x: {c['over_20']:.3f}, >=30x: {c['over_30']:.3f}")
```

### Query 5: Gene Constraint

Retrieve gene-level constraint scores: pLI (probability of loss-of-function intolerance), LOEUF (LoF observed/expected upper bound fraction), and missense z-score.

```python
CONSTRAINT_QUERY = """
query GeneConstraint($gene_symbol: String!, $reference_genome: ReferenceGenomeId!) {
  gene(gene_symbol: $gene_symbol, reference_genome: $reference_genome) {
    gene_id
    gene_name
    gnomad_constraint {
      pLI
      pNull
      pRec
      mis_z
      lof {
        obs
        exp
        oe
        oe_ci { lower upper }
      }
    }
  }
}
"""

genes = ["PCSK9", "BRCA1", "TP53", "TTN"]
print(f"{'Gene':<10} {'pLI':>6} {'LOEUF':>7} {'mis_z':>7}")
print("-" * 35)
for gene in genes:
    data = gnomad_query(CONSTRAINT_QUERY, {"gene_symbol": gene, "reference_genome": "GRCh38"})
    c = data["gene"]["gnomad_constraint"]
    loeuf = c["lof"]["oe_ci"]["upper"]
    print(f"{gene:<10} {c['pLI']:>6.3f} {loeuf:>7.3f} {c['mis_z']:>7.2f}")
    time.sleep(0.5)
# Gene        pLI   LOEUF   mis_z
# PCSK9     0.855   0.543    2.11
# BRCA1     0.999   0.127    3.84
# TP53      0.993   0.191    5.21
# TTN       0.001   0.993   -2.40
```

### Query 6: Variant Search by Region

Fetch all variants in a chromosomal region, useful for targeted panels and regional analyses.

```python
REGION_VARIANTS_QUERY = """
query RegionVariants($chrom: String!, $start: Int!, $stop: Int!,
                     $dataset: DatasetId!, $reference_genome: ReferenceGenomeId!) {
  region(chrom: $chrom, start: $start, stop: $stop,
         reference_genome: $reference_genome) {
    variants(dataset: $dataset) {
      variant_id
      rsids
      pos
      consequence
      lof
      genome {
        af
        ac
        an
        faf95 { popmax }
      }
    }
  }
}
"""

data = gnomad_query(REGION_VARIANTS_QUERY, {
    "chrom": "1",
    "start": 55039974,
    "stop": 55064852,   # PCSK9 coding region
    "dataset": "gnomad_r4",
    "reference_genome": "GRCh38"
})
variants = data["region"]["variants"]
print(f"Variants in region: {len(variants)}")

# Summarize by consequence
from collections import Counter
conseq_counts = Counter(v["consequence"] for v in variants if v["consequence"])
for c, n in conseq_counts.most_common(5):
    print(f"  {c}: {n}")

# Loss-of-function variants
lof_vars = [v for v in variants if v["lof"] == "HC"]
print(f"\nHigh-confidence LoF variants: {len(lof_vars)}")
for v in lof_vars[:3]:
    af = v["genome"]["af"] if v["genome"] else None
    print(f"  {v['variant_id']} | AF={af:.2e}" if af else f"  {v['variant_id']} | AF=NA")
```

## Key Concepts

### gnomAD Data Model

gnomAD v4 has two datasets: `gnomad_r4` (exomes + genomes, GRCh38, 730K+ individuals) and `gnomad_r2_1` (GRCh37, 141K individuals). The API uses a GraphQL schema where variants are accessed either through `gene()`, `region()`, or direct `variant()` lookups. Each variant has separate `exome` and `genome` frequency objects; the `genome` object is preferred for population frequency comparisons.

### Ancestry Groups

gnomAD v4 reports frequencies for 9 top-level ancestry groups identified by genetic ancestry (not self-reported):

| Code | Population | Dataset size (approx) |
|------|-----------|----------------------|
| `afr` | African/African American | 76,000+ |
| `amr` | Admixed American | 45,000+ |
| `eas` | East Asian | 50,000+ |
| `fin` | Finnish | 24,000+ |
| `nfe` | Non-Finnish European | 400,000+ |
| `sas` | South Asian | 80,000+ |
| `asj` | Ashkenazi Jewish | 10,000+ |
| `mid` | Middle Eastern | 5,000+ |
| `oth` | Other/Unknown | varies |

### Filtering Allele Frequency (FAF95)

The `faf95` field provides a one-sided 95% confidence interval lower bound on the allele frequency in the population where the variant is most common. Use this for conservative variant filtering in clinical pipelines — a variant with `faf95.popmax < 0.001` is likely rare enough to warrant clinical investigation.

### Constraint Scores

| Score | Interpretation |
|-------|----------------|
| `pLI > 0.9` | Gene is intolerant to LoF — likely essential |
| `LOEUF < 0.35` | Strong LoF constraint (upper CI of oe ratio) |
| `mis_z > 3.09` | Gene shows significant missense constraint |
| `pLI < 0.1` | Gene tolerates LoF — homozygous LoF variants exist |

## Common Workflows

### Workflow 1: Rare Variant Frequency Report for a Gene

**Goal**: Retrieve all rare (AF < 1%) variants in a gene, stratified by consequence, exported to CSV.

```python
import requests, time, pandas as pd

GNOMAD_API = "https://gnomad.broadinstitute.org/api"

def gnomad_query(query, variables=None):
    r = requests.post(GNOMAD_API, json={"query": query, "variables": variables or {}}, timeout=30)
    r.raise_for_status()
    result = r.json()
    if "errors" in result:
        raise ValueError(result["errors"])
    return result["data"]

GENE_VARIANTS_QUERY = """
query GeneVariants($gene_symbol: String!, $reference_genome: ReferenceGenomeId!, $dataset: DatasetId!) {
  gene(gene_symbol: $gene_symbol, reference_genome: $reference_genome) {
    gene_id gene_name
    variants(dataset: $dataset) {
      variant_id rsids chrom pos ref alt consequence lof lof_filter
      genome {
        an ac af
        faf95 { popmax popmax_population }
        populations { id ac an af }
      }
    }
  }
}
"""

gene = "LDLR"
data = gnomad_query(GENE_VARIANTS_QUERY, {
    "gene_symbol": gene,
    "reference_genome": "GRCh38",
    "dataset": "gnomad_r4"
})

variants = data["gene"]["variants"]
rows = []
for v in variants:
    g = v.get("genome") or {}
    af = g.get("af")
    if af is None or af >= 0.01:   # keep only rare variants
        continue
    rows.append({
        "variant_id": v["variant_id"],
        "rsids": ";".join(v.get("rsids") or []),
        "consequence": v.get("consequence"),
        "lof": v.get("lof"),
        "af_genome": af,
        "ac": g.get("ac"),
        "an": g.get("an"),
        "faf95_popmax": g.get("faf95", {}).get("popmax"),
        "faf95_pop": g.get("faf95", {}).get("popmax_population"),
    })

df = pd.DataFrame(rows)
df = df.sort_values("af_genome")
df.to_csv(f"{gene}_rare_variants.csv", index=False)
print(f"{gene}: {len(variants)} total variants, {len(df)} rare (AF<1%)")
print(df.groupby("consequence")["variant_id"].count().sort_values(ascending=False).head(6))
# LDLR: 2847 total variants, 2631 rare (AF<1%)
# consequence
# missense_variant              1423
# synonymous_variant             512
# splice_region_variant          231
# stop_gained                    198
```

### Workflow 2: Ancestry-Stratified Frequency Visualization

**Goal**: Query a list of variants and produce a barplot of allele frequencies by ancestry group.

```python
import requests, time
import pandas as pd
import matplotlib.pyplot as plt

GNOMAD_API = "https://gnomad.broadinstitute.org/api"

def gnomad_query(query, variables=None):
    r = requests.post(GNOMAD_API, json={"query": query, "variables": variables or {}}, timeout=30)
    r.raise_for_status()
    result = r.json()
    if "errors" in result:
        raise ValueError(result["errors"])
    return result["data"]

POPULATION_FREQ_QUERY = """
query PopFreqs($variant_id: String!, $dataset: DatasetId!) {
  variant(variant_id: $variant_id, dataset: $dataset) {
    variant_id
    genome {
      populations { id ac an af }
    }
  }
}
"""

ANCESTRY_LABELS = {
    "afr": "AFR", "amr": "AMR", "eas": "EAS", "fin": "FIN",
    "nfe": "NFE", "sas": "SAS", "asj": "ASJ", "mid": "MID",
}

variant_id = "1-55039974-G-T"   # PCSK9 p.Tyr142Ter
data = gnomad_query(POPULATION_FREQ_QUERY, {
    "variant_id": variant_id,
    "dataset": "gnomad_r4"
})

pops = data["variant"]["genome"]["populations"]
rows = [{"code": p["id"], "af": p["af"], "ac": p["ac"], "an": p["an"]}
        for p in pops if p["id"] in ANCESTRY_LABELS and p["an"] > 0]
df = pd.DataFrame(rows)
df["label"] = df["code"].map(ANCESTRY_LABELS)
df = df.sort_values("af", ascending=False)

fig, ax = plt.subplots(figsize=(9, 4))
bars = ax.bar(df["label"], df["af"] * 100, color="#4472C4", edgecolor="white")
ax.bar_label(bars, fmt="%.3f%%", fontsize=8, padding=2)
ax.set_xlabel("Ancestry Group")
ax.set_ylabel("Allele Frequency (%)")
ax.set_title(f"gnomAD v4 Population Frequencies\n{variant_id}")
ax.set_ylim(0, df["af"].max() * 150)
plt.tight_layout()
plt.savefig("gnomad_pop_frequencies.png", dpi=150, bbox_inches="tight")
print(f"Saved gnomad_pop_frequencies.png  (n={len(df)} ancestry groups)")
print(df[["label", "af", "ac", "an"]].to_string(index=False))
```

### Workflow 3: Constraint-Guided Gene Prioritization

**Goal**: Score a gene list by constraint metrics and flag LoF-intolerant genes.

```python
import requests, time, pandas as pd

GNOMAD_API = "https://gnomad.broadinstitute.org/api"

def gnomad_query(query, variables=None):
    r = requests.post(GNOMAD_API, json={"query": query, "variables": variables or {}}, timeout=30)
    r.raise_for_status()
    result = r.json()
    if "errors" in result:
        raise ValueError(result["errors"])
    return result["data"]

CONSTRAINT_QUERY = """
query GeneConstraint($gene_symbol: String!, $reference_genome: ReferenceGenomeId!) {
  gene(gene_symbol: $gene_symbol, reference_genome: $reference_genome) {
    gene_id gene_name
    gnomad_constraint {
      pLI pNull pRec mis_z
      lof { obs exp oe oe_ci { lower upper } }
    }
  }
}
"""

gene_list = ["BRCA1", "BRCA2", "PCSK9", "LDLR", "TTN", "CFTR", "HTT"]
records = []
for gene in gene_list:
    try:
        data = gnomad_query(CONSTRAINT_QUERY, {"gene_symbol": gene, "reference_genome": "GRCh38"})
        c = data["gene"]["gnomad_constraint"]
        records.append({
            "gene": gene,
            "pLI": c["pLI"],
            "LOEUF": c["lof"]["oe_ci"]["upper"],
            "mis_z": c["mis_z"],
            "lof_obs": c["lof"]["obs"],
            "lof_exp": c["lof"]["exp"],
            "lof_oe": c["lof"]["oe"],
        })
    except Exception as e:
        print(f"Warning: {gene} failed — {e}")
    time.sleep(0.5)

df = pd.DataFrame(records).sort_values("LOEUF")
df["lof_intolerant"] = df["pLI"] > 0.9
print(df[["gene", "pLI", "LOEUF", "mis_z", "lof_intolerant"]].to_string(index=False))
df.to_csv("constraint_scores.csv", index=False)
print(f"\nLoF-intolerant genes: {df['lof_intolerant'].sum()}/{len(df)}")
```

## Key Parameters

| Parameter | Function/Endpoint | Default | Range / Options | Effect |
|-----------|-------------------|---------|-----------------|--------|
| `dataset` | All variant queries | — | `gnomad_r4`, `gnomad_r2_1`, `gnomad_r3` | Dataset version (GRCh38 for r4/r3, GRCh37 for r2_1) |
| `reference_genome` | gene(), region() | — | `GRCh38`, `GRCh37` | Coordinate system; must match dataset |
| `variant_id` | variant() | — | `CHROM-POS-REF-ALT` string | Identifies the specific variant to query |
| `gene_symbol` | gene() | — | HGNC symbol string | Gene to retrieve; case-insensitive |
| `chrom`, `start`, `stop` | region() | — | valid genomic coordinates | Region boundaries for region queries |
| `faf95.popmax` | variant() genome | — | float 0–1 | Filtering allele frequency (95% CI upper bound); use < 0.001 for rare |
| `lof` filter field | gene() variants | — | `"HC"` (high-confidence), `"LC"` | LoF confidence level |
| `populations.id` | genome.populations | — | `afr`, `amr`, `eas`, `fin`, `nfe`, `sas`, `asj`, `mid`, `oth` | Per-ancestry frequency |

## Best Practices

1. **Use `gnomad_r4` for GRCh38 analyses**: gnomAD v4 is the most current dataset with 730K+ individuals. Use `gnomad_r2_1` only when comparing to GRCh37-based variant calls.

2. **Use `faf95.popmax` for clinical filtering, not overall AF**: The filtering allele frequency accounts for maximum population stratification and provides a more conservative rarity estimate than the global AF.

3. **Add `time.sleep(0.5)` in batch loops**: gnomAD has no published rate limits but the API is shared infrastructure. Polite delays prevent server-side throttling.

4. **Filter `lof == "HC"` for LoF burden analyses**: Low-confidence LoF (`"LC"`) annotations are often in repetitive regions or may be sequencing artifacts. High-confidence (`"HC"`) calls are filtered by LOFTEE.

5. **Check AN before interpreting AF**: Low allele number (AN) means poor coverage in that population. A zero or near-zero AF may reflect absent data, not true rarity. Cross-reference with the coverage query when AN is unexpectedly low.

## Common Recipes

### Recipe: Check if a Variant Is Common in Any Population

When to use: Quick check before clinical interpretation — confirm no ancestry group has AF > 1%.

```python
import requests

GNOMAD_API = "https://gnomad.broadinstitute.org/api"

def is_common_in_any_population(variant_id, threshold=0.01, dataset="gnomad_r4"):
    query = """
    query($variant_id: String!, $dataset: DatasetId!) {
      variant(variant_id: $variant_id, dataset: $dataset) {
        genome { faf95 { popmax popmax_population } af }
      }
    }
    """
    r = requests.post(GNOMAD_API, json={"query": query,
                                         "variables": {"variant_id": variant_id, "dataset": dataset}},
                      timeout=15)
    data = r.json()["data"]["variant"]
    if not data or not data["genome"]:
        return None, "Variant not found in gnomAD"
    af = data["genome"]["af"]
    popmax = data["genome"]["faf95"]["popmax"]
    pop = data["genome"]["faf95"]["popmax_population"]
    is_common = (popmax or 0) >= threshold
    return is_common, f"overall AF={af:.2e}, FAF95 popmax={popmax:.2e} in {pop}"

common, info = is_common_in_any_population("1-55039974-G-T")
print(f"Common: {common}  |  {info}")
# Common: False  |  overall AF=3.2e-05, FAF95 popmax=6.4e-05 in nfe
```

### Recipe: Batch Constraint Lookup

When to use: Score multiple genes from a differential expression or GWAS gene list.

```python
import requests, time, pandas as pd

GNOMAD_API = "https://gnomad.broadinstitute.org/api"

def get_constraint(gene_symbol, reference_genome="GRCh38"):
    query = """
    query($gene_symbol: String!, $reference_genome: ReferenceGenomeId!) {
      gene(gene_symbol: $gene_symbol, reference_genome: $reference_genome) {
        gnomad_constraint { pLI mis_z lof { oe_ci { upper } } }
      }
    }
    """
    r = requests.post(GNOMAD_API, json={"query": query,
                      "variables": {"gene_symbol": gene_symbol, "reference_genome": reference_genome}},
                      timeout=15)
    data = r.json().get("data", {}).get("gene", {})
    if not data or not data.get("gnomad_constraint"):
        return None
    c = data["gnomad_constraint"]
    return {"gene": gene_symbol, "pLI": c["pLI"], "LOEUF": c["lof"]["oe_ci"]["upper"], "mis_z": c["mis_z"]}

genes = ["BRCA1", "BRCA2", "ATM", "CHEK2", "PALB2"]
rows = [r for g in genes for r in [get_constraint(g)] if r]
time.sleep(0.5)   # polite delay per gene in real loop

df = pd.DataFrame(rows)
print(df.to_string(index=False))
# gene     pLI   LOEUF  mis_z
# BRCA1  0.999   0.127   3.84
# BRCA2  1.000   0.176   3.21
```

### Recipe: Export LoF Variants for CADD/ClinVar Cross-Reference

When to use: Get high-confidence LoF variants from gnomAD for downstream annotation.

```python
import requests, pandas as pd

GNOMAD_API = "https://gnomad.broadinstitute.org/api"

def get_lof_variants(gene_symbol, dataset="gnomad_r4", max_af=0.001):
    query = """
    query($gene_symbol: String!, $reference_genome: ReferenceGenomeId!, $dataset: DatasetId!) {
      gene(gene_symbol: $gene_symbol, reference_genome: $reference_genome) {
        variants(dataset: $dataset) {
          variant_id rsids chrom pos ref alt consequence lof
          genome { af ac an }
        }
      }
    }
    """
    r = requests.post(GNOMAD_API, json={"query": query,
                      "variables": {"gene_symbol": gene_symbol, "reference_genome": "GRCh38", "dataset": dataset}},
                      timeout=60)
    variants = r.json()["data"]["gene"]["variants"]
    lof = [v for v in variants
           if v.get("lof") == "HC"
           and v.get("genome") and v["genome"].get("af") is not None
           and v["genome"]["af"] < max_af]
    return pd.DataFrame([{
        "variant_id": v["variant_id"],
        "rsids": ";".join(v.get("rsids") or []),
        "consequence": v["consequence"],
        "af": v["genome"]["af"],
        "ac": v["genome"]["ac"],
    } for v in lof])

df = get_lof_variants("CFTR", max_af=0.001)
print(f"High-confidence LoF variants in CFTR (AF<0.1%): {len(df)}")
print(df.head(5).to_string(index=False))
df.to_csv("CFTR_HC_lof_variants.csv", index=False)
```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `{"errors": [...]}` from GraphQL | Invalid field name, wrong dataset ID, or null gene | Check field names match gnomAD v4 schema; use `gnomad_r4` not `gnomad_v4` |
| Variant returns `None` genome object | Variant only in exome data, not genome | Try accessing `exome` field instead of `genome`; genome is absent for exome-only variants |
| Gene query returns empty variants list | Gene symbol not found or mismatch | Verify HGNC symbol (case-sensitive); use `gene_id` (ENSG ID) as fallback |
| `faf95` returns `null` | Variant is absent or monomorphic in all populations | Check `ac` and `an` — variant may have AC=0 or be filtered |
| `requests.exceptions.Timeout` | Large gene (e.g., TTN) takes >30s | Increase `timeout=120`; for very large genes use region queries instead |
| Population AF is `None` for some groups | Variant not observed in that ancestry | Treat `None` AF as 0 for filtering; check `an` to confirm the group was sequenced |
| `reference_genome` mismatch error | Using GRCh37 coords with `gnomad_r4` | Use `GRCh38` for `gnomad_r4`/`gnomad_r3`; use `GRCh37` only for `gnomad_r2_1` |

## Related Skills

- `clinvar-database` — ClinVar pathogenicity classifications (complement to gnomAD population frequency data)
- `gwas-database` — GWAS Catalog for SNP-trait associations from published GWAS studies
- `ensembl-database` — Ensembl VEP for variant consequence prediction and gene annotation
- `dbsnp-database` — dbSNP for rsID lookup, variant classes, and cross-database ID mapping

## References

- [gnomAD GraphQL API](https://gnomad.broadinstitute.org/api) — Interactive GraphQL explorer and endpoint documentation
- [Karczewski et al., Nature 2020](https://doi.org/10.1038/s41586-020-2308-7) — gnomAD v2.1 flagship paper (constraint metrics, LoF analysis)
- [gnomAD Help & FAQ](https://gnomad.broadinstitute.org/help) — Data model, ancestry definitions, FAF95 explanation
- [gnomAD v4 blog post](https://gnomad.broadinstitute.org/news/2023-11-gnomad-v4-0/) — gnomAD v4 release notes and dataset composition
