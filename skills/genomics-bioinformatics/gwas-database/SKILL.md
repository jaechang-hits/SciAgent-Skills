---
name: gwas-database
description: "NHGRI-EBI GWAS Catalog REST API for SNP-trait associations from published GWAS. Query studies, associations, variants, traits, genes, summary stats. Build PRS candidates, analyze pleiotropy, fetch stats for Manhattan plots. No auth."
license: Apache-2.0
---

# GWAS Catalog Database — SNP-Trait Association Queries

## Overview

The NHGRI-EBI GWAS Catalog is a curated collection of published genome-wide association studies, mapping SNP-trait associations with genomic context. The REST API provides programmatic access to studies, associations, variants, traits, genes, and summary statistics. All responses are HAL+JSON with embedded `_links` for pagination.

## When to Use

- Finding genetic variants associated with a disease or trait (e.g., "which SNPs are linked to type 2 diabetes?")
- Retrieving genome-wide significant associations for a specific variant (rs ID)
- Exploring the genetic architecture of complex traits (number of loci, effect sizes)
- Checking variant pleiotropy (how many traits a single SNP affects)
- Downloading summary statistics for meta-analysis or polygenic risk score construction
- Identifying published GWAS studies by disease, gene, or PubMed ID
- Cross-referencing EFO trait ontology terms with GWAS evidence
- Building candidate gene lists from GWAS association regions
- For **drug target validation from GWAS hits**, use `opentargets-database` instead
- For **variant functional annotation** (consequence prediction, regulatory impact), use Ensembl VEP via `gget`

## Prerequisites

```bash
pip install requests matplotlib numpy
```

**API access**:
- **No authentication** required -- fully open access
- **Rate limits**: no official limit, but add `time.sleep(0.2)` between requests to be courteous
- **Base URL**: `https://www.ebi.ac.uk/gwas/rest/api`
- **Response format**: HAL+JSON with `_embedded` data and `_links` for pagination
- **Pagination**: default 20 results per page; max 500 via `size` parameter

## Quick Start

```python
import requests
import time

BASE = "https://www.ebi.ac.uk/gwas/rest/api"

def gwas_get(endpoint, params=None):
    """GWAS Catalog REST API helper with rate limiting and pagination support."""
    url = f"{BASE}/{endpoint}"
    resp = requests.get(url, params=params or {})
    resp.raise_for_status()
    time.sleep(0.2)
    return resp.json()

# Find studies for a trait keyword
data = gwas_get("studies/search/findByDiseaseTrait", {"diseaseTrait": "diabetes"})
studies = data["_embedded"]["studies"]
print(f"Found {len(studies)} studies for 'diabetes'")
for s in studies[:3]:
    print(f"  {s['accessionId']}: {s.get('title', 'N/A')[:80]}")
```

## Core API

### Module 1: Study Search

Search GWAS studies by disease trait keyword or PubMed ID.

```python
# Search studies by disease trait
data = gwas_get("studies/search/findByDiseaseTrait", {"diseaseTrait": "breast cancer"})
studies = data["_embedded"]["studies"]
for s in studies[:5]:
    pubmed = s.get("publicationInfo", {}).get("pubmedId", "N/A")
    print(f"  {s['accessionId']} | PMID:{pubmed} | {s.get('title', '')[:60]}")

time.sleep(0.2)

# Search by PubMed ID
data = gwas_get("studies/search/findByPubmedId", {"pubmedId": "25673413"})
studies = data["_embedded"]["studies"]
print(f"Studies from PMID 25673413: {len(studies)}")
for s in studies:
    print(f"  {s['accessionId']}: {s.get('diseaseTrait', {}).get('trait', 'N/A')}")
```

### Module 2: Association Queries

Retrieve SNP-trait associations filtered by trait (EFO term), variant, or p-value.

```python
# Associations for a trait by EFO URI
efo_uri = "http://www.ebi.ac.uk/efo/EFO_0001360"  # Type 2 diabetes
data = gwas_get("efoTraits/EFO_0001360/associations", {"size": 50})
assocs = data["_embedded"]["associations"]
print(f"Associations for T2D: {len(assocs)}")

for a in assocs[:5]:
    pval = a.get("pvalue", None)
    loci = a.get("loci", [])
    genes = []
    for locus in loci:
        for gene in locus.get("authorReportedGenes", []):
            genes.append(gene.get("geneName", ""))
    snps = [r.get("snps", [{}])[0].get("rsId", "N/A")
            for r in a.get("loci", [{}])[0].get("strongestRiskAlleles", [])]
    print(f"  rs={snps} | p={pval} | genes={genes}")
```

```python
# Associations for a specific variant
data = gwas_get("singleNucleotidePolymorphisms/rs7903146/associations", {"size": 100})
assocs = data["_embedded"]["associations"]
print(f"Associations for rs7903146: {len(assocs)}")
for a in assocs[:5]:
    trait = a.get("efoTraits", [{}])[0].get("trait", "N/A") if a.get("efoTraits") else "N/A"
    print(f"  p={a.get('pvalue')} | OR={a.get('orPerCopyNum', 'N/A')} | trait={trait}")
```

### Module 3: Variant Lookup

Query variant details by rsID, chromosomal region, or cytogenetic band.

```python
# Lookup single variant
data = gwas_get("singleNucleotidePolymorphisms/rs7903146")
loc = data.get("locations", [{}])[0]
print(f"rs7903146: chr{loc.get('chromosomeName', '?')}:{loc.get('chromosomePosition', '?')}")
print(f"  Functional class: {data.get('functionalClass', 'N/A')}")
print(f"  Merged into: {data.get('merged', 'N/A')}")

time.sleep(0.2)

# Search variants by chromosomal region
data = gwas_get("singleNucleotidePolymorphisms/search/findByChromBpLocationRange",
                {"chrom": "10", "bpStart": "114750000", "bpEnd": "114800000", "size": 50})
snps = data["_embedded"]["singleNucleotidePolymorphisms"]
print(f"Variants in chr10:114750000-114800000: {len(snps)}")
for v in snps[:5]:
    print(f"  {v['rsId']}: {v.get('functionalClass', 'N/A')}")
```

```python
# Search variants by cytogenetic band
data = gwas_get("singleNucleotidePolymorphisms/search/findByCytogeneticBand",
                {"cytogeneticBand": "10q25.2", "size": 50})
snps = data["_embedded"]["singleNucleotidePolymorphisms"]
print(f"Variants at 10q25.2: {len(snps)}")
```

### Module 4: Trait Search

Browse and search EFO-mapped traits in the GWAS Catalog.

```python
# Search traits by keyword
data = gwas_get("efoTraits/search/findByDescription", {"description": "alzheimer", "size": 20})
traits = data["_embedded"]["efoTraits"]
print(f"Traits matching 'alzheimer': {len(traits)}")
for t in traits[:5]:
    print(f"  {t['shortForm']}: {t['trait']}")

time.sleep(0.2)

# Get specific trait by EFO ID
data = gwas_get("efoTraits/EFO_0000249")  # Alzheimer disease
print(f"Trait: {data['trait']}")
print(f"  URI: {data['uri']}")
```

### Module 5: Summary Statistics

Access study-level summary statistics for downstream analysis (meta-analysis, PRS).

```python
# List studies with available summary statistics
data = gwas_get("studies/search/findByFullPvalueSet", {"fullPvalueSet": True, "size": 10})
studies = data["_embedded"]["studies"]
print(f"Studies with summary stats (first page): {len(studies)}")
for s in studies[:5]:
    print(f"  {s['accessionId']}: {s.get('diseaseTrait', {}).get('trait', 'N/A')[:50]}")

time.sleep(0.2)

# Get summary statistics metadata for a specific study
data = gwas_get(f"studies/{studies[0]['accessionId']}/summaryStatistics")
print(f"Summary stats available: {data}")
```

```python
# Download summary statistics file (FTP)
# Summary statistics are hosted on the GWAS Catalog FTP, not the REST API
import urllib.request

study_id = "GCST006867"  # Example study
ftp_base = "http://ftp.ebi.ac.uk/pub/databases/gwas/summary_statistics"
# Actual paths vary by study; check the study page for the download link
# Example: ftp_base/{study_id}/{study_id}.tsv.gz
url = f"{ftp_base}/{study_id}"
print(f"Summary stats FTP directory: {url}")
# Use requests.get() or urllib to download the .tsv.gz file
```

### Module 6: Gene and Publication Search

Find GWAS associations by gene name or retrieve publication metadata.

```python
# Search associations by gene
data = gwas_get("singleNucleotidePolymorphisms/search/findByGene",
                {"geneName": "BRCA1", "size": 50})
snps = data["_embedded"]["singleNucleotidePolymorphisms"]
print(f"Variants near BRCA1: {len(snps)}")
for v in snps[:5]:
    locs = v.get("locations", [{}])
    pos = locs[0].get("chromosomePosition", "?") if locs else "?"
    print(f"  {v['rsId']}: chr{locs[0].get('chromosomeName', '?')}:{pos}")

time.sleep(0.2)

# Get study publication details
data = gwas_get("studies/GCST000392")
pub = data.get("publicationInfo", {})
print(f"Study: {data['accessionId']}")
print(f"  Author: {pub.get('author', {}).get('fullname', 'N/A')}")
print(f"  Journal: {pub.get('publication', 'N/A')}")
print(f"  PMID: {pub.get('pubmedId', 'N/A')}")
print(f"  Date: {pub.get('publicationDate', 'N/A')}")
```

## Key Concepts

### Data Entities and Relationships

The GWAS Catalog organizes data as interconnected entities:

| Entity | Description | Key Identifier | Example |
|--------|-------------|---------------|---------|
| **Study** | A published GWAS experiment | GCST accession (e.g., `GCST000392`) | Wellcome Trust Case Control Consortium study |
| **Association** | A SNP-trait association with p-value and effect size | Internal ID | rs7903146 associated with T2D at p=1e-40 |
| **Variant (SNP)** | A single nucleotide polymorphism | rs number (e.g., `rs7903146`) | TCF7L2 variant |
| **Trait** | A disease/phenotype mapped to EFO ontology | EFO ID (e.g., `EFO_0001360`) | Type 2 diabetes mellitus |
| **Gene** | A gene near or harboring GWAS variants | Gene symbol (e.g., `TCF7L2`) | Transcription factor 7-like 2 |

**Relationships**: Study --(reports)--> Association --(involves)--> Variant + Trait. Variants map to genomic positions and nearby genes.

### HAL+JSON Response Structure

All API responses follow HAL (Hypertext Application Language) format:

| Top-level Section | Contents | Access Pattern |
|-------------------|----------|----------------|
| `_embedded` | Primary data objects (studies, associations, etc.) | `response["_embedded"]["studies"]` |
| `_links` | Navigation links (self, next, prev, first, last) | `response["_links"]["next"]["href"]` |
| `page` | Pagination metadata (size, totalElements, totalPages, number) | `response["page"]["totalElements"]` |

### Genome-wide Significance

The standard genome-wide significance threshold is **p <= 5 x 10^-8**, correcting for approximately 1 million independent tests across the human genome. Associations below this threshold are considered suggestive. The GWAS Catalog includes associations at various significance levels -- always check p-values when filtering results.

### Key Identifiers

- **GCST IDs**: GWAS Catalog study accessions (e.g., `GCST000392`)
- **rs numbers**: dbSNP reference SNP identifiers (e.g., `rs7903146`)
- **EFO terms**: Experimental Factor Ontology for trait standardization (e.g., `EFO_0001360` for type 2 diabetes)
- **Cytogenetic bands**: Chromosomal location notation (e.g., `10q25.2`)

## Common Workflows

### Workflow 1: Disease Genetic Architecture

**Goal**: Map the genetic landscape of a disease by collecting all genome-wide significant loci.

```python
import requests, time

BASE = "https://www.ebi.ac.uk/gwas/rest/api"

def gwas_get(endpoint, params=None):
    url = f"{BASE}/{endpoint}"
    resp = requests.get(url, params=params or {})
    resp.raise_for_status()
    time.sleep(0.2)
    return resp.json()

# Step 1: Find trait EFO ID
traits = gwas_get("efoTraits/search/findByDescription",
                  {"description": "schizophrenia", "size": 5})
efo_id = traits["_embedded"]["efoTraits"][0]["shortForm"]
print(f"Using EFO: {efo_id}")

# Step 2: Get all associations for this trait
all_assocs = []
page = 0
while True:
    data = gwas_get(f"efoTraits/{efo_id}/associations",
                    {"size": 500, "page": page})
    assocs = data["_embedded"]["associations"]
    all_assocs.extend(assocs)
    if page >= data["page"]["totalPages"] - 1:
        break
    page += 1

# Step 3: Filter genome-wide significant
significant = [a for a in all_assocs if a.get("pvalue") and a["pvalue"] < 5e-8]
print(f"Total associations: {len(all_assocs)}, genome-wide significant: {len(significant)}")

# Step 4: Extract variant and effect details
for a in significant[:10]:
    risk_alleles = a.get("loci", [{}])[0].get("strongestRiskAlleles", [])
    snp = risk_alleles[0].get("snps", [{}])[0].get("rsId", "N/A") if risk_alleles else "N/A"
    or_val = a.get("orPerCopyNum", "N/A")
    beta = a.get("betaNum", "N/A")
    print(f"  {snp} | p={a['pvalue']:.2e} | OR={or_val} | beta={beta}")
```

### Workflow 2: Variant Pleiotropy Analysis

**Goal**: Determine how many distinct traits a single variant is associated with.

```python
import requests, time

BASE = "https://www.ebi.ac.uk/gwas/rest/api"

def gwas_get(endpoint, params=None):
    url = f"{BASE}/{endpoint}"
    resp = requests.get(url, params=params or {})
    resp.raise_for_status()
    time.sleep(0.2)
    return resp.json()

rs_id = "rs7903146"  # Well-known pleiotropic variant

# Get all associations for this variant
data = gwas_get(f"singleNucleotidePolymorphisms/{rs_id}/associations", {"size": 500})
assocs = data["_embedded"]["associations"]

# Collect unique traits
trait_set = {}
for a in assocs:
    for t in a.get("efoTraits", []):
        tid = t.get("shortForm", "unknown")
        if tid not in trait_set:
            trait_set[tid] = {
                "trait": t.get("trait", "N/A"),
                "best_pval": a.get("pvalue", 1),
                "count": 0
            }
        trait_set[tid]["count"] += 1
        if a.get("pvalue") and a["pvalue"] < trait_set[tid]["best_pval"]:
            trait_set[tid]["best_pval"] = a["pvalue"]

print(f"{rs_id} is associated with {len(trait_set)} distinct traits:")
for tid, info in sorted(trait_set.items(), key=lambda x: x[1]["best_pval"]):
    print(f"  {tid}: {info['trait']} (best p={info['best_pval']:.2e}, n={info['count']})")
```

### Workflow 3: Summary Statistics Manhattan Plot

**Goal**: Download summary statistics for a study and create a Manhattan plot.

```python
import numpy as np
import matplotlib.pyplot as plt
import csv, gzip, io, requests

# Simulated summary statistics for demonstration
# In practice: download from GWAS Catalog FTP
# url = "http://ftp.ebi.ac.uk/pub/databases/gwas/summary_statistics/GCSTXXXXXX/..."
# resp = requests.get(url); data = gzip.decompress(resp.content)

np.random.seed(42)
n_snps = 5000
chroms = np.random.choice(range(1, 23), size=n_snps)
positions = np.random.randint(1, 250_000_000, size=n_snps)
pvalues = np.random.uniform(0, 1, size=n_snps)
# Add some "hits"
pvalues[:20] = 10 ** np.random.uniform(-15, -8, size=20)

# Manhattan plot
log_p = -np.log10(pvalues)
chrom_offsets = {}
running_offset = 0
for c in range(1, 23):
    chrom_offsets[c] = running_offset
    running_offset += 250_000_000

x_positions = [positions[i] + chrom_offsets[chroms[i]] for i in range(n_snps)]
colors = ["#1f77b4" if c % 2 == 0 else "#ff7f0e" for c in chroms]

fig, ax = plt.subplots(figsize=(14, 5))
ax.scatter(x_positions, log_p, c=colors, s=4, alpha=0.6)
ax.axhline(y=-np.log10(5e-8), color="red", linestyle="--", linewidth=0.8,
           label="Genome-wide significance (p=5e-8)")
ax.axhline(y=-np.log10(1e-5), color="blue", linestyle=":", linewidth=0.5,
           label="Suggestive (p=1e-5)")
ax.set_xlabel("Chromosome")
ax.set_ylabel("-log10(p-value)")
ax.set_title("GWAS Manhattan Plot")
ax.legend(fontsize=8)

# Chromosome labels
tick_positions = [chrom_offsets[c] + 125_000_000 for c in range(1, 23)]
ax.set_xticks(tick_positions)
ax.set_xticklabels([str(c) for c in range(1, 23)], fontsize=7)
plt.tight_layout()
plt.savefig("manhattan_plot.png", dpi=300, bbox_inches="tight")
print("Saved manhattan_plot.png")
```

## Key Parameters

| Parameter | Function/Endpoint | Default | Range / Options | Effect |
|-----------|-------------------|---------|-----------------|--------|
| `size` | All paginated endpoints | `20` | `1`-`500` | Results per page |
| `page` | All paginated endpoints | `0` | `0`-`totalPages-1` | Page number (0-indexed) |
| `diseaseTrait` | `studies/search/findByDiseaseTrait` | -- | Any string | Trait keyword search |
| `pubmedId` | `studies/search/findByPubmedId` | -- | Valid PMID | Study lookup by publication |
| `geneName` | `snps/search/findByGene` | -- | Gene symbol | Variants near a gene |
| `chrom`, `bpStart`, `bpEnd` | `snps/search/findByChromBpLocationRange` | -- | chr:start-end | Regional variant query |
| `cytogeneticBand` | `snps/search/findByCytogeneticBand` | -- | e.g., `10q25.2` | Variants by cytogenetic band |
| `fullPvalueSet` | `studies/search/findByFullPvalueSet` | -- | `True`/`False` | Filter studies with summary stats |
| `description` | `efoTraits/search/findByDescription` | -- | Any string | Trait keyword search |

## Best Practices

1. **Paginate large result sets**: Default page size is 20; set `size=500` and loop over pages for complete data retrieval. Check `page.totalElements` to know the full count before iterating.

2. **Use EFO IDs for precise trait queries**: Free-text search may return related but different traits. Look up the exact EFO ID first, then query associations by EFO ID for precision.

3. **Always check p-values**: The catalog contains associations at various significance levels. Filter to p < 5e-8 for genome-wide significant results unless you specifically need suggestive associations.

4. **Be ancestry-aware**: Effect sizes and allele frequencies vary across populations. Check the `initialSampleSize` and `replicationSampleSize` fields to understand the ancestry composition of each study.

5. **Add rate-limiting delays**: Although no official limit exists, `time.sleep(0.2)` between requests prevents server overload and avoids temporary blocks.

6. **Cache frequently accessed data**: Study and trait metadata rarely change. Cache results locally when running batch analyses to reduce redundant API calls.

7. **Anti-pattern -- Don't rely solely on reported genes**: Author-reported genes may not be the causal gene. Cross-reference with functional annotation tools and eQTL databases for biological interpretation.

## Common Recipes

### Recipe 1: Cross-Reference with PGS Catalog

Identify polygenic scores available for a GWAS trait.

```python
import requests, time

# Step 1: Get EFO ID from GWAS Catalog
BASE = "https://www.ebi.ac.uk/gwas/rest/api"
traits = requests.get(f"{BASE}/efoTraits/search/findByDescription",
                      params={"description": "coronary artery disease"}).json()
efo_id = traits["_embedded"]["efoTraits"][0]["shortForm"]
time.sleep(0.2)

# Step 2: Query PGS Catalog for scores using same EFO
pgs_url = f"https://www.pgscatalog.org/rest/score/search?trait_id={efo_id}"
pgs_data = requests.get(pgs_url).json()
print(f"PGS scores for {efo_id}: {pgs_data.get('count', 0)}")
for score in pgs_data.get("results", [])[:5]:
    print(f"  {score['id']}: {score['name']} (variants: {score.get('variants_number', '?')})")
```

### Recipe 2: Regional Association Summary

Collect all GWAS associations in a genomic region.

```python
import requests, time

BASE = "https://www.ebi.ac.uk/gwas/rest/api"

# Query region: chr9:21,900,000-22,200,000 (CDKN2A/2B locus)
data = requests.get(f"{BASE}/singleNucleotidePolymorphisms/search/findByChromBpLocationRange",
                    params={"chrom": "9", "bpStart": "21900000",
                            "bpEnd": "22200000", "size": 200}).json()
time.sleep(0.2)
snps = data["_embedded"]["singleNucleotidePolymorphisms"]
print(f"Variants in CDKN2A/2B locus: {len(snps)}")

# Get associations for each variant
region_assocs = []
for v in snps[:10]:  # Limit for demo
    rs = v["rsId"]
    try:
        a_data = requests.get(f"{BASE}/singleNucleotidePolymorphisms/{rs}/associations",
                              params={"size": 50}).json()
        time.sleep(0.2)
        for a in a_data["_embedded"]["associations"]:
            for t in a.get("efoTraits", []):
                region_assocs.append({"rsId": rs, "trait": t["trait"],
                                      "pvalue": a.get("pvalue")})
    except Exception:
        continue

print(f"Total associations in region: {len(region_assocs)}")
```

### Recipe 3: Effect Size Forest Plot

Visualize effect sizes across studies for a single variant.

```python
import matplotlib.pyplot as plt
import numpy as np
import requests, time

BASE = "https://www.ebi.ac.uk/gwas/rest/api"
data = requests.get(f"{BASE}/singleNucleotidePolymorphisms/rs1801282/associations",
                    params={"size": 100}).json()
time.sleep(0.2)
assocs = data["_embedded"]["associations"]

# Extract OR values (filter to those with OR data)
entries = []
for a in assocs:
    or_val = a.get("orPerCopyNum")
    ci_text = a.get("range", "")
    trait = a.get("efoTraits", [{}])[0].get("trait", "N/A") if a.get("efoTraits") else "N/A"
    if or_val and or_val > 0:
        entries.append({"trait": trait[:30], "or": or_val, "ci": ci_text})

if entries:
    fig, ax = plt.subplots(figsize=(8, max(3, len(entries) * 0.4)))
    y_pos = range(len(entries))
    ors = [e["or"] for e in entries]
    labels = [f"{e['trait']} (OR={e['or']:.2f})" for e in entries]
    ax.barh(y_pos, [np.log(o) for o in ors], color=["#d62728" if o > 1 else "#2ca02c" for o in ors])
    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, fontsize=8)
    ax.axvline(x=0, color="black", linewidth=0.8)
    ax.set_xlabel("log(OR)")
    ax.set_title("rs1801282 (PPARG) Effect Sizes")
    plt.tight_layout()
    plt.savefig("forest_plot.png", dpi=300, bbox_inches="tight")
    print(f"Saved forest_plot.png with {len(entries)} entries")
```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `404 Not Found` | Invalid GCST, rs ID, or EFO ID | Verify identifier exists via search endpoint first |
| Empty `_embedded` | No results for query | Broaden search terms or check spelling; try partial match |
| `ConnectionError` / timeout | EBI server temporarily down | Retry with exponential backoff; check https://www.ebi.ac.uk/gwas/status |
| Truncated results | Default pagination (20 per page) | Set `size=500` and iterate over `page` parameter |
| Missing OR/beta values | Not all associations report effect sizes | Check both `orPerCopyNum` and `betaNum` fields; some studies report only p-values |
| Stale data | Catalog updated quarterly | Check `lastUpdateDate` on studies; re-query if needed |
| `KeyError: '_embedded'` | Endpoint returns single object, not list | Direct lookups (by ID) return a single object; `_embedded` only appears in search/list results |
| Summary stats unavailable | Not all studies deposit summary stats | Filter with `findByFullPvalueSet=True` to find studies with available data |

## Bundled Resources

### `references/api_endpoints.md`

**Covers**: Complete endpoint catalog for all 6 REST API groups (studies, associations, variants, traits, genes, summary statistics) with query parameters, plus response field tables for the main entity types (association fields, study fields, variant fields), HTTP error codes, and pagination patterns.

**Relocated inline**: Core query patterns and the most common endpoints are demonstrated in Core API modules with full code examples. HAL+JSON structure and key identifier formats are in Key Concepts.

**Omitted from original api_reference.md (794 lines)**: Advanced query composition patterns (multi-parameter chaining beyond what Core API shows), child/parent trait traversal details, detailed changelog/versioning notes. These are specialized and covered by EBI documentation.

## Related Skills

- **gget-genomic-databases** -- gene lookups, variant annotation, BLAST (upstream ID resolution)
- **ensembl-database (planned)** -- variant effect prediction, regulatory annotations
- **opentargets-database (planned)** -- drug target validation from GWAS hits
- **clinvar-database (planned)** -- clinical variant interpretation
- **bioservices-multi-database** -- cross-database queries integrating GWAS with pathway data

## References

- [GWAS Catalog website](https://www.ebi.ac.uk/gwas/) -- main portal for browsing and searching
- [GWAS Catalog REST API documentation](https://www.ebi.ac.uk/gwas/rest/docs/api) -- official API reference
- [GWAS Catalog GitHub](https://github.com/EBISPOT/goci) -- source code and issue tracker
- [Summary Statistics FTP](http://ftp.ebi.ac.uk/pub/databases/gwas/summary_statistics/) -- bulk summary statistics downloads
- [PGS Catalog](https://www.pgscatalog.org/) -- polygenic score database using GWAS data
