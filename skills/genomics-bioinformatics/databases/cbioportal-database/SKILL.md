---
name: "cbioportal-database"
description: "Cancer genomics (TCGA et al.) via cBioPortal REST API. Retrieve somatic mutations, CNAs, expression, clinical data (survival/stage/treatment) across thousands of studies. Use for TMB, oncoprints, survival analysis. For population frequencies use gnomad-database; for drug-gene interactions use dgidb-database."
license: "AGPL-3.0"
---

# cBioPortal Database

## Overview

cBioPortal for Cancer Genomics is a public repository of cancer genomics data including TCGA, ICGC, and hundreds of curated studies spanning 100+ cancer types. It provides somatic mutation profiles, copy number alterations (CNA), gene expression, clinical data (survival, stage, treatment history), and methylation data for tens of thousands of patient samples. Data is accessible via a REST API at `https://www.cbioportal.org/api/` with no authentication required.

## When to Use

- Retrieving somatic mutation profiles (variant type, amino acid change) for a gene across TCGA studies
- Querying copy number alteration data (amplification, deep deletion) for candidate cancer driver genes
- Accessing clinical data — overall survival, disease-free survival, tumor stage — for survival curve analysis
- Identifying which cancer studies have molecular profiling data for a specific cancer type (e.g., breast, lung)
- Downloading gene expression (RNA-seq FPKM/RSEM) data from specific TCGA cohorts for differential expression analysis
- Correlating genomic alterations with clinical outcomes in a specific study
- Use `gnomad-database` instead when you need population-level variant allele frequencies in healthy individuals
- For drug-gene interaction lookups use `dgidb-database`; cBioPortal provides the genomic alteration data, not drug interaction annotations

## Prerequisites

- **Python packages**: `requests`, `pandas`, `matplotlib`
- **Data requirements**: Entrez gene symbols (e.g., `TP53`), cBioPortal study IDs (e.g., `tcga_brca`), molecular profile IDs
- **Environment**: internet connection; no API key required
- **Rate limits**: no strict rate limits; use `time.sleep(0.2)` between batch requests for polite access

```bash
pip install requests pandas matplotlib
```

## Quick Start

```python
import requests
import pandas as pd

BASE_URL = "https://www.cbioportal.org/api"

def cbio_get(endpoint, params=None):
    """GET request to cBioPortal REST API, returns parsed JSON."""
    r = requests.get(f"{BASE_URL}/{endpoint}", params=params,
                     headers={"Accept": "application/json"}, timeout=30)
    r.raise_for_status()
    return r.json()

# List available cancer types
cancer_types = cbio_get("cancer-types")
print(f"Total cancer types: {len(cancer_types)}")
# Total cancer types: 87

# Find TCGA breast cancer study
studies = cbio_get("studies", params={"keyword": "breast"})
brca = [s for s in studies if "tcga_brca" in s["studyId"]]
if brca:
    s = brca[0]
    print(f"Study: {s['name']}")
    print(f"  studyId: {s['studyId']}")
    print(f"  Samples: {s['allSampleCount']}")
# Study: Breast Invasive Carcinoma (TCGA, PanCancer Atlas)
#   studyId: brca_tcga_pan_can_atlas_2018
#   Samples: 1084
```

## Core API

### Query 1: Cancer Types and Studies

List available cancer types and find studies by cancer type or keyword.

```python
import requests
import pandas as pd

BASE_URL = "https://www.cbioportal.org/api"

def cbio_get(endpoint, params=None):
    r = requests.get(f"{BASE_URL}/{endpoint}", params=params,
                     headers={"Accept": "application/json"}, timeout=30)
    r.raise_for_status()
    return r.json()

# Get all cancer types
cancer_types = cbio_get("cancer-types")
ct_df = pd.DataFrame(cancer_types)[["cancerTypeId", "name", "dedicatedColor"]]
print(f"Cancer types: {len(ct_df)}")
print(ct_df.head(5).to_string(index=False))

# Find all studies for a cancer type
lung_studies = cbio_get("studies", params={"keyword": "lung adenocarcinoma"})
print(f"\nLung adenocarcinoma studies: {len(lung_studies)}")
for s in lung_studies[:3]:
    print(f"  {s['studyId']:40s}  n={s['allSampleCount']}")
```

```python
# Get detailed study metadata including available data types
study_id = "brca_tcga_pan_can_atlas_2018"
study = cbio_get(f"studies/{study_id}")
print(f"Study: {study['name']}")
print(f"  Reference genome: {study.get('referenceGenome', 'n/a')}")
print(f"  All sample count: {study['allSampleCount']}")

# List molecular profiles for the study
profiles = cbio_get("molecular-profiles", params={"studyId": study_id})
print(f"\nMolecular profiles ({len(profiles)} total):")
for p in profiles:
    print(f"  {p['molecularProfileId']:55s}  [{p['molecularAlterationType']}]")
```

### Query 2: Somatic Mutations

Retrieve mutation data for a gene or set of genes in a study's mutation profile.

```python
import requests, json
import pandas as pd

BASE_URL = "https://www.cbioportal.org/api"

def cbio_post(endpoint, body):
    """POST request to cBioPortal REST API."""
    r = requests.post(f"{BASE_URL}/{endpoint}", json=body,
                      headers={"Accept": "application/json",
                               "Content-Type": "application/json"},
                      timeout=60)
    r.raise_for_status()
    return r.json()

def cbio_get(endpoint, params=None):
    r = requests.get(f"{BASE_URL}/{endpoint}", params=params,
                     headers={"Accept": "application/json"}, timeout=30)
    r.raise_for_status()
    return r.json()

# Get all samples for a study
study_id = "brca_tcga_pan_can_atlas_2018"
samples = cbio_get(f"studies/{study_id}/samples", params={"projection": "ID"})
sample_ids = [s["sampleId"] for s in samples]
print(f"Total samples: {len(sample_ids)}")

# Mutation profile ID follows pattern: {studyId}_mutations
profile_id = f"{study_id}_mutations"

# Fetch mutations for TP53 (Entrez gene ID = 7157)
body = {
    "sampleIds": sample_ids[:200],   # first 200 samples
    "entrezGeneIds": [7157]           # TP53
}
mutations = cbio_post(f"molecular-profiles/{profile_id}/mutations/fetch", body)
print(f"TP53 mutations in first 200 samples: {len(mutations)}")

# Summarize by mutation type
mut_df = pd.DataFrame(mutations)
print("\nMutation type distribution:")
print(mut_df["mutationType"].value_counts().head(8).to_string())
# Missense_Mutation    102
# Nonsense_Mutation     28
# Splice_Site           14
# Frame_Shift_Del       12
```

### Query 3: Copy Number Alterations

Fetch discrete CNA data (amplification = 2, gain = 1, diploid = 0, loss = -1, deep deletion = -2).

```python
import requests
import pandas as pd

BASE_URL = "https://www.cbioportal.org/api"

def cbio_post(endpoint, body):
    r = requests.post(f"{BASE_URL}/{endpoint}", json=body,
                      headers={"Accept": "application/json",
                               "Content-Type": "application/json"},
                      timeout=60)
    r.raise_for_status()
    return r.json()

def cbio_get(endpoint, params=None):
    r = requests.get(f"{BASE_URL}/{endpoint}", params=params,
                     headers={"Accept": "application/json"}, timeout=30)
    r.raise_for_status()
    return r.json()

study_id = "brca_tcga_pan_can_atlas_2018"
# CNA profile: discrete copy number data
cna_profile_id = f"{study_id}_gistic"   # GISTIC-derived discrete CNA

samples = cbio_get(f"studies/{study_id}/samples", params={"projection": "ID"})
sample_ids = [s["sampleId"] for s in samples][:300]

# Fetch CNA for ERBB2 (Entrez 2064) and MYC (Entrez 4609)
body = {
    "sampleIds": sample_ids,
    "entrezGeneIds": [2064, 4609]   # ERBB2, MYC
}
cna_data = cbio_post(
    f"molecular-profiles/{cna_profile_id}/molecular-data/fetch", body
)
print(f"CNA records retrieved: {len(cna_data)}")

cna_df = pd.DataFrame(cna_data)
# CNA values: 2=amplification, 1=gain, 0=diploid, -1=loss, -2=deep deletion
cna_label = {2: "AMP", 1: "GAIN", 0: "DIPLOID", -1: "LOSS", -2: "HOMDEL"}

print("\nERBB2 CNA distribution:")
erbb2 = cna_df[cna_df["entrezGeneId"] == 2064]
erbb2_counts = erbb2["value"].map(lambda x: cna_label.get(int(x), str(x))).value_counts()
print(erbb2_counts.to_string())
# DIPLOID    210
# AMP         62
# GAIN        18
# LOSS        10
```

### Query 4: Clinical Data

Retrieve per-sample or per-patient clinical attributes including survival, tumor stage, and treatment.

```python
import requests
import pandas as pd

BASE_URL = "https://www.cbioportal.org/api"

def cbio_get(endpoint, params=None):
    r = requests.get(f"{BASE_URL}/{endpoint}", params=params,
                     headers={"Accept": "application/json"}, timeout=30)
    r.raise_for_status()
    return r.json()

study_id = "brca_tcga_pan_can_atlas_2018"

# List available clinical attributes for this study
attrs = cbio_get(f"studies/{study_id}/clinical-attributes")
attr_df = pd.DataFrame(attrs)[["clinicalAttributeId", "displayName", "datatype", "patientAttribute"]]
print(f"Clinical attributes: {len(attr_df)}")
# Show survival-related attributes
survival_attrs = attr_df[attr_df["clinicalAttributeId"].str.contains("SURVIVAL|MONTHS|STATUS", na=False)]
print(survival_attrs[["clinicalAttributeId", "displayName"]].to_string(index=False))

# Fetch OS_STATUS and OS_MONTHS for all patients
clinical = cbio_get(f"studies/{study_id}/clinical-data",
                    params={"clinicalDataType": "PATIENT",
                            "projection": "DETAILED"})
clin_df = pd.DataFrame(clinical)
# Pivot to patient × attribute matrix
clin_pivot = clin_df.pivot_table(
    index="patientId", columns="clinicalAttributeId",
    values="value", aggfunc="first"
)
print(f"\nPatients: {len(clin_pivot)}")
if "OS_STATUS" in clin_pivot.columns:
    print("OS status counts:")
    print(clin_pivot["OS_STATUS"].value_counts().to_string())
# OS status counts:
# 0:LIVING    765
# 1:DECEASED  319
```

### Query 5: Gene Expression Data

Retrieve mRNA expression values (RSEM or FPKM) from RNA-seq profiles.

```python
import requests
import pandas as pd

BASE_URL = "https://www.cbioportal.org/api"

def cbio_post(endpoint, body):
    r = requests.post(f"{BASE_URL}/{endpoint}", json=body,
                      headers={"Accept": "application/json",
                               "Content-Type": "application/json"},
                      timeout=60)
    r.raise_for_status()
    return r.json()

def cbio_get(endpoint, params=None):
    r = requests.get(f"{BASE_URL}/{endpoint}", params=params,
                     headers={"Accept": "application/json"}, timeout=30)
    r.raise_for_status()
    return r.json()

study_id = "brca_tcga_pan_can_atlas_2018"
# RNA-seq profile (RSEM normalized values)
rna_profile_id = f"{study_id}_rna_seq_v2_mrna_median_normed_log2"

samples = cbio_get(f"studies/{study_id}/samples", params={"projection": "ID"})
sample_ids = [s["sampleId"] for s in samples][:100]

# Fetch expression for ESR1 (Entrez 2099), ERBB2 (2064), PGR (5241)
body = {
    "sampleIds": sample_ids,
    "entrezGeneIds": [2099, 2064, 5241]   # ESR1, ERBB2, PGR
}
expr_data = cbio_post(
    f"molecular-profiles/{rna_profile_id}/molecular-data/fetch", body
)
expr_df = pd.DataFrame(expr_data)
print(f"Expression records: {len(expr_df)}")

# Pivot to gene × sample matrix
expr_pivot = expr_df.pivot_table(
    index="sampleId", columns="entrezGeneId", values="value"
)
expr_pivot.columns = ["ERBB2", "ESR1", "PGR"]   # rename by gene symbol
print(f"\nExpression matrix: {expr_pivot.shape}")
print(expr_pivot.describe().round(2))
```

### Query 6: Gene Details and Batch Lookup

Look up gene metadata (symbol, Entrez ID, type) required to construct mutation and CNA queries.

```python
import requests
import pandas as pd

BASE_URL = "https://www.cbioportal.org/api"

def cbio_get(endpoint, params=None):
    r = requests.get(f"{BASE_URL}/{endpoint}", params=params,
                     headers={"Accept": "application/json"}, timeout=30)
    r.raise_for_status()
    return r.json()

def cbio_post(endpoint, body):
    r = requests.post(f"{BASE_URL}/{endpoint}", json=body,
                      headers={"Accept": "application/json",
                               "Content-Type": "application/json"},
                      timeout=30)
    r.raise_for_status()
    return r.json()

# Single gene lookup by Hugo symbol
gene = cbio_get("genes/TP53")
print(f"TP53: entrezGeneId={gene['entrezGeneId']}, type={gene['type']}")
# TP53: entrezGeneId=7157, type=protein-coding

# Batch gene lookup — convert Hugo symbols to Entrez IDs
gene_symbols = ["BRCA1", "BRCA2", "TP53", "PIK3CA", "PTEN", "KRAS", "EGFR"]
body = {"geneIds": gene_symbols, "geneIdType": "HUGO_GENE_SYMBOL"}
gene_list = cbio_post("genes/fetch", body)

gene_map = {g["hugoGeneSymbol"]: g["entrezGeneId"] for g in gene_list}
gene_df = pd.DataFrame(gene_list)[["hugoGeneSymbol", "entrezGeneId", "type"]]
print(f"\nResolved {len(gene_df)} genes:")
print(gene_df.to_string(index=False))
# hugoGeneSymbol  entrezGeneId            type
#          BRCA1         672   protein-coding
#          BRCA2         675   protein-coding
#           TP53        7157   protein-coding
```

### Query 7: Visualization — Mutation Frequency Barplot

Plot mutation frequency across TCGA studies for a cancer driver gene.

```python
import requests, time
import pandas as pd
import matplotlib.pyplot as plt

BASE_URL = "https://www.cbioportal.org/api"

def cbio_get(endpoint, params=None):
    r = requests.get(f"{BASE_URL}/{endpoint}", params=params,
                     headers={"Accept": "application/json"}, timeout=30)
    r.raise_for_status()
    return r.json()

def cbio_post(endpoint, body):
    r = requests.post(f"{BASE_URL}/{endpoint}", json=body,
                      headers={"Accept": "application/json",
                               "Content-Type": "application/json"},
                      timeout=60)
    r.raise_for_status()
    return r.json()

# Focus on a curated set of TCGA PanCancer Atlas studies
STUDIES = {
    "brca_tcga_pan_can_atlas_2018": "BRCA",
    "luad_tcga_pan_can_atlas_2018": "LUAD",
    "coad_tcga_pan_can_atlas_2018": "COAD",
    "prad_tcga_pan_can_atlas_2018": "PRAD",
    "gbm_tcga_pan_can_atlas_2018": "GBM",
}

GENE_ENTREZ = 7157   # TP53
GENE_SYMBOL = "TP53"

rows = []
for study_id, label in STUDIES.items():
    try:
        samples = cbio_get(f"studies/{study_id}/samples", params={"projection": "ID"})
        sample_ids = [s["sampleId"] for s in samples]
        n_total = len(sample_ids)
        profile_id = f"{study_id}_mutations"
        body = {"sampleIds": sample_ids, "entrezGeneIds": [GENE_ENTREZ]}
        muts = cbio_post(f"molecular-profiles/{profile_id}/mutations/fetch", body)
        mutated_samples = len({m["sampleId"] for m in muts})
        rows.append({"study": label, "n_mutated": mutated_samples,
                     "n_total": n_total,
                     "freq": mutated_samples / n_total * 100})
        time.sleep(0.2)
    except Exception as e:
        print(f"  Skipping {study_id}: {e}")

df = pd.DataFrame(rows).sort_values("freq", ascending=True)

fig, ax = plt.subplots(figsize=(7, 4))
bars = ax.barh(df["study"], df["freq"], color="#C0392B", edgecolor="white")
ax.bar_label(bars, labels=[f"{v:.0f}%  (n={n})" for v, n in zip(df["freq"], df["n_mutated"])],
             padding=4, fontsize=9)
ax.set_xlabel(f"{GENE_SYMBOL} Mutation Frequency (%)")
ax.set_title(f"{GENE_SYMBOL} Somatic Mutation Frequency\nacross TCGA PanCancer Atlas Studies")
ax.set_xlim(0, df["freq"].max() * 1.3)
plt.tight_layout()
plt.savefig(f"{GENE_SYMBOL}_mutation_frequency.png", dpi=150, bbox_inches="tight")
print(f"Saved {GENE_SYMBOL}_mutation_frequency.png")
print(df[["study", "n_mutated", "n_total", "freq"]].to_string(index=False))
```

## Key Concepts

### cBioPortal Data Model

cBioPortal organizes data in a three-tier hierarchy: **Cancer Studies** → **Molecular Profiles** → **Sample-level data**. A single study (e.g., `brca_tcga_pan_can_atlas_2018`) contains multiple molecular profiles, each covering one data type. Before querying mutation or expression data, always retrieve the molecular profile list with `GET /molecular-profiles?studyId={studyId}` to confirm the correct profile ID.

### Molecular Profile ID Conventions

| Data Type | Typical Profile ID Suffix | Alteration Type |
|-----------|--------------------------|-----------------|
| Somatic mutations | `_mutations` | `MUTATION_EXTENDED` |
| Discrete CNA (GISTIC) | `_gistic` | `COPY_NUMBER_ALTERATION` |
| Continuous CNA (log2) | `_log2CNA` | `COPY_NUMBER_ALTERATION` |
| RNA-seq (log2 RSEM) | `_rna_seq_v2_mrna_median_normed_log2` | `MRNA_EXPRESSION` |
| Methylation | `_methylation_hm27` or `_hm450` | `METHYLATION` |

Not all studies have all profile types. Always verify with `GET /molecular-profiles?studyId={studyId}`.

### Entrez Gene IDs

The REST API mutation and molecular data endpoints require **Entrez Gene IDs** (integers), not Hugo symbols. Use `GET /genes/{hugoSymbol}` or `POST /genes/fetch` to resolve symbols to IDs before batch queries.

## Common Workflows

### Workflow 1: Somatic Mutation Landscape for a Gene Panel

**Goal**: Retrieve mutations for multiple cancer driver genes across an entire TCGA study and export to CSV.

```python
import requests, time
import pandas as pd

BASE_URL = "https://www.cbioportal.org/api"

def cbio_get(endpoint, params=None):
    r = requests.get(f"{BASE_URL}/{endpoint}", params=params,
                     headers={"Accept": "application/json"}, timeout=30)
    r.raise_for_status()
    return r.json()

def cbio_post(endpoint, body):
    r = requests.post(f"{BASE_URL}/{endpoint}", json=body,
                      headers={"Accept": "application/json",
                               "Content-Type": "application/json"},
                      timeout=120)
    r.raise_for_status()
    return r.json()

study_id = "luad_tcga_pan_can_atlas_2018"
profile_id = f"{study_id}_mutations"

# Resolve gene symbols to Entrez IDs
gene_symbols = ["KRAS", "EGFR", "TP53", "BRAF", "STK11", "KEAP1", "RB1"]
gene_list = cbio_post("genes/fetch",
                       {"geneIds": gene_symbols, "geneIdType": "HUGO_GENE_SYMBOL"})
gene_map = {g["entrezGeneId"]: g["hugoGeneSymbol"] for g in gene_list}
entrez_ids = list(gene_map.keys())

# Fetch all samples
samples = cbio_get(f"studies/{study_id}/samples", params={"projection": "ID"})
sample_ids = [s["sampleId"] for s in samples]
print(f"Study: {study_id} — {len(sample_ids)} samples")

# Batch mutations in chunks of 500 samples to avoid timeouts
chunk_size = 500
all_muts = []
for i in range(0, len(sample_ids), chunk_size):
    chunk = sample_ids[i:i + chunk_size]
    body = {"sampleIds": chunk, "entrezGeneIds": entrez_ids}
    muts = cbio_post(f"molecular-profiles/{profile_id}/mutations/fetch", body)
    all_muts.extend(muts)
    time.sleep(0.1)

mut_df = pd.DataFrame(all_muts)
mut_df["hugoSymbol"] = mut_df["entrezGeneId"].map(gene_map)
print(f"Total mutations: {len(mut_df)}")
print("\nMutation counts per gene:")
print(mut_df.groupby("hugoSymbol")["sampleId"].nunique()
      .sort_values(ascending=False).to_string())

mut_df.to_csv(f"{study_id}_driver_mutations.csv", index=False)
print(f"\nSaved: {study_id}_driver_mutations.csv")
```

### Workflow 2: Survival Analysis — CNA Status vs. Overall Survival

**Goal**: Compare overall survival between patients with ERBB2 amplification vs. diploid/loss in TCGA BRCA.

```python
import requests
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

BASE_URL = "https://www.cbioportal.org/api"

def cbio_get(endpoint, params=None):
    r = requests.get(f"{BASE_URL}/{endpoint}", params=params,
                     headers={"Accept": "application/json"}, timeout=30)
    r.raise_for_status()
    return r.json()

def cbio_post(endpoint, body):
    r = requests.post(f"{BASE_URL}/{endpoint}", json=body,
                      headers={"Accept": "application/json",
                               "Content-Type": "application/json"},
                      timeout=60)
    r.raise_for_status()
    return r.json()

study_id = "brca_tcga_pan_can_atlas_2018"
cna_profile_id = f"{study_id}_gistic"

# Get all samples
samples = cbio_get(f"studies/{study_id}/samples", params={"projection": "ID"})
sample_ids = [s["sampleId"] for s in samples]

# Fetch ERBB2 CNA (Entrez 2064)
cna_data = cbio_post(
    f"molecular-profiles/{cna_profile_id}/molecular-data/fetch",
    {"sampleIds": sample_ids, "entrezGeneIds": [2064]}
)
cna_df = pd.DataFrame(cna_data)[["sampleId", "value"]].rename(columns={"value": "erbb2_cna"})
cna_df["erbb2_cna"] = cna_df["erbb2_cna"].astype(int)
cna_df["erbb2_status"] = cna_df["erbb2_cna"].map(
    {2: "Amplified", 1: "Gain", 0: "Diploid", -1: "Loss", -2: "Deep Deletion"})

# Fetch clinical data (OS_STATUS, OS_MONTHS)
clinical = cbio_get(f"studies/{study_id}/clinical-data",
                    params={"clinicalDataType": "PATIENT", "projection": "DETAILED"})
clin_df = pd.DataFrame(clinical)
clin_pivot = clin_df.pivot_table(
    index="patientId", columns="clinicalAttributeId", values="value", aggfunc="first"
).reset_index()

# Map samples to patients
sample_patient = cbio_get(f"studies/{study_id}/samples", params={"projection": "DETAILED"})
sp_df = pd.DataFrame(sample_patient)[["sampleId", "patientId"]]

# Merge CNA + clinical via patient ID
merged = (cna_df
          .merge(sp_df, on="sampleId")
          .merge(clin_pivot[["patientId", "OS_STATUS", "OS_MONTHS"]],
                 on="patientId", how="inner"))
merged = merged.dropna(subset=["OS_STATUS", "OS_MONTHS"])
merged["OS_MONTHS"] = pd.to_numeric(merged["OS_MONTHS"], errors="coerce")
merged["event"] = (merged["OS_STATUS"] == "1:DECEASED").astype(int)

# Simple Kaplan-Meier-style plot (manual step function)
def km_curve(df, time_col="OS_MONTHS"):
    times = sorted(df[time_col].dropna().values)
    surv = []
    s = 1.0
    n = len(times)
    for i, t in enumerate(times):
        s *= (1 - 1 / (n - i))
        surv.append((t, s))
    return surv

fig, ax = plt.subplots(figsize=(8, 5))
colors = {"Amplified": "#C0392B", "Diploid": "#2980B9"}
for status, color in colors.items():
    grp = merged[merged["erbb2_status"] == status]
    if len(grp) < 10:
        continue
    km = km_curve(grp)
    times = [0] + [x[0] for x in km]
    surv  = [1.0] + [x[1] for x in km]
    ax.step(times, surv, where="post", color=color,
            label=f"ERBB2 {status} (n={len(grp)})", lw=2)

ax.set_xlabel("Overall Survival (months)")
ax.set_ylabel("Survival Probability")
ax.set_title("ERBB2 CNA Status vs. Overall Survival\nTCGA BRCA (PanCancer Atlas)")
ax.legend()
ax.set_ylim(0, 1.05)
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig("erbb2_survival.png", dpi=150, bbox_inches="tight")
print(f"Saved erbb2_survival.png")
print(f"ERBB2 Amplified: {(merged['erbb2_status']=='Amplified').sum()} samples")
print(f"ERBB2 Diploid:   {(merged['erbb2_status']=='Diploid').sum()} samples")
```

### Workflow 3: Multi-Study Alteration Frequency Heatmap

**Goal**: Build a gene × cancer-type alteration frequency matrix across TCGA studies.

```python
import requests, time
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

BASE_URL = "https://www.cbioportal.org/api"

def cbio_get(endpoint, params=None):
    r = requests.get(f"{BASE_URL}/{endpoint}", params=params,
                     headers={"Accept": "application/json"}, timeout=30)
    r.raise_for_status()
    return r.json()

def cbio_post(endpoint, body):
    r = requests.post(f"{BASE_URL}/{endpoint}", json=body,
                      headers={"Accept": "application/json",
                               "Content-Type": "application/json"},
                      timeout=90)
    r.raise_for_status()
    return r.json()

STUDIES = {
    "brca_tcga_pan_can_atlas_2018": "BRCA",
    "luad_tcga_pan_can_atlas_2018": "LUAD",
    "coad_tcga_pan_can_atlas_2018": "COAD",
    "gbm_tcga_pan_can_atlas_2018":  "GBM",
}
GENE_SYMBOLS = ["TP53", "KRAS", "PIK3CA", "EGFR", "PTEN"]

# Resolve genes
gene_list = cbio_post("genes/fetch",
                       {"geneIds": GENE_SYMBOLS, "geneIdType": "HUGO_GENE_SYMBOL"})
gene_map = {g["entrezGeneId"]: g["hugoGeneSymbol"] for g in gene_list}
entrez_ids = list(gene_map.keys())

freq_matrix = pd.DataFrame(index=GENE_SYMBOLS, columns=list(STUDIES.values()), dtype=float)

for study_id, label in STUDIES.items():
    try:
        samples = cbio_get(f"studies/{study_id}/samples", params={"projection": "ID"})
        sample_ids = [s["sampleId"] for s in samples]
        n_total = len(sample_ids)
        profile_id = f"{study_id}_mutations"
        body = {"sampleIds": sample_ids, "entrezGeneIds": entrez_ids}
        muts = cbio_post(f"molecular-profiles/{profile_id}/mutations/fetch", body)
        mut_df = pd.DataFrame(muts) if muts else pd.DataFrame()
        for eid, symbol in gene_map.items():
            if mut_df.empty:
                freq_matrix.loc[symbol, label] = 0.0
            else:
                n_mut = mut_df[mut_df["entrezGeneId"] == eid]["sampleId"].nunique()
                freq_matrix.loc[symbol, label] = n_mut / n_total * 100
        time.sleep(0.2)
    except Exception as e:
        print(f"  {label}: {e}")

freq_matrix = freq_matrix.fillna(0).astype(float)

fig, ax = plt.subplots(figsize=(7, 4))
im = ax.imshow(freq_matrix.values, cmap="YlOrRd", aspect="auto", vmin=0, vmax=80)
ax.set_xticks(range(len(freq_matrix.columns)))
ax.set_xticklabels(freq_matrix.columns, rotation=30, ha="right")
ax.set_yticks(range(len(freq_matrix.index)))
ax.set_yticklabels(freq_matrix.index)
for i in range(len(freq_matrix.index)):
    for j in range(len(freq_matrix.columns)):
        val = freq_matrix.iloc[i, j]
        ax.text(j, i, f"{val:.0f}%", ha="center", va="center", fontsize=9,
                color="white" if val > 40 else "black")
plt.colorbar(im, ax=ax, label="Mutation Frequency (%)")
ax.set_title("Somatic Mutation Frequency — TCGA PanCancer Atlas")
plt.tight_layout()
plt.savefig("mutation_frequency_heatmap.png", dpi=150, bbox_inches="tight")
print("Saved mutation_frequency_heatmap.png")
print(freq_matrix.to_string())
```

## Key Parameters

| Parameter | Function/Endpoint | Default | Range / Options | Effect |
|-----------|-------------------|---------|-----------------|--------|
| `studyId` | All study endpoints | — | any valid cBioPortal study ID | Selects the cancer study |
| `molecularProfileId` | mutations/fetch, molecular-data/fetch | — | `{studyId}_mutations`, `{studyId}_gistic`, etc. | Selects the data type profile |
| `entrezGeneIds` | mutations/fetch, molecular-data/fetch | — | list of integer Entrez IDs | Genes to query; use `POST /genes/fetch` to resolve symbols |
| `sampleIds` | mutations/fetch, molecular-data/fetch | — | list of sample ID strings | Samples to retrieve; use `GET /studies/{id}/samples` for all |
| `clinicalDataType` | clinical-data | `"SAMPLE"` | `"SAMPLE"`, `"PATIENT"` | Whether to return sample-level or patient-level clinical attributes |
| `projection` | samples, clinical-data | `"SUMMARY"` | `"ID"`, `"SUMMARY"`, `"DETAILED"`, `"META"` | Response verbosity; `"ID"` fastest for ID-only fetches |
| `keyword` | studies | `""` | free text | Filter studies by name/cancer type keyword |

## Best Practices

1. **Fetch sample IDs before data queries**: All mutation and molecular data endpoints require explicit `sampleIds`. Retrieve them with `GET /studies/{studyId}/samples?projection=ID` before each query.

2. **Verify profile IDs from the API**: Profile IDs are not guaranteed to follow the `_mutations` / `_gistic` pattern in every study. Always confirm with `GET /molecular-profiles?studyId={studyId}` rather than guessing.

3. **Chunk large sample sets**: The API can time out on requests with thousands of sample IDs. Batch requests in chunks of 500 samples with `time.sleep(0.1)` between chunks.

4. **Use Entrez IDs, not Hugo symbols, in data fetch endpoints**: The mutation and molecular data endpoints accept `entrezGeneIds` (integers). Resolve symbols first with `POST /genes/fetch`.

5. **Don't hard-code Entrez IDs**: Gene IDs can be looked up dynamically via the API. Hard-coded IDs become incorrect if the gene model changes. Use `POST /genes/fetch` to resolve gene symbols at runtime.

## Common Recipes

### Recipe: List All Molecular Profiles for a Study

When to use: Before running any data query — verify which profile IDs are available.

```python
import requests

BASE_URL = "https://www.cbioportal.org/api"

def cbio_get(endpoint, params=None):
    r = requests.get(f"{BASE_URL}/{endpoint}", params=params,
                     headers={"Accept": "application/json"}, timeout=30)
    r.raise_for_status()
    return r.json()

study_id = "brca_tcga_pan_can_atlas_2018"
profiles = cbio_get("molecular-profiles", params={"studyId": study_id})
for p in profiles:
    print(f"{p['molecularProfileId']:55s}  {p['molecularAlterationType']}")
# brca_tcga_pan_can_atlas_2018_mutations          MUTATION_EXTENDED
# brca_tcga_pan_can_atlas_2018_gistic             COPY_NUMBER_ALTERATION
# brca_tcga_pan_can_atlas_2018_log2CNA            COPY_NUMBER_ALTERATION
# brca_tcga_pan_can_atlas_2018_rna_seq_v2_mrna_median_normed_log2  MRNA_EXPRESSION
```

### Recipe: Download Full Mutation MAF for a Study

When to use: Export all somatic mutations from a study into MAF-compatible format for downstream analysis.

```python
import requests, time
import pandas as pd

BASE_URL = "https://www.cbioportal.org/api"

def cbio_get(endpoint, params=None):
    r = requests.get(f"{BASE_URL}/{endpoint}", params=params,
                     headers={"Accept": "application/json"}, timeout=60)
    r.raise_for_status()
    return r.json()

def cbio_post(endpoint, body):
    r = requests.post(f"{BASE_URL}/{endpoint}", json=body,
                      headers={"Accept": "application/json",
                               "Content-Type": "application/json"},
                      timeout=120)
    r.raise_for_status()
    return r.json()

study_id = "coad_tcga_pan_can_atlas_2018"
profile_id = f"{study_id}_mutations"

samples = cbio_get(f"studies/{study_id}/samples", params={"projection": "ID"})
sample_ids = [s["sampleId"] for s in samples]

all_mutations = []
for i in range(0, len(sample_ids), 300):
    chunk = sample_ids[i:i + 300]
    muts = cbio_post(f"molecular-profiles/{profile_id}/mutations/fetch",
                     {"sampleIds": chunk, "entrezGeneIds": []})  # empty = all genes
    all_mutations.extend(muts)
    time.sleep(0.1)

mut_df = pd.DataFrame(all_mutations)
cols = ["hugoGeneSymbol", "sampleId", "chr", "startPosition", "endPosition",
        "referenceAllele", "variantAllele", "mutationType",
        "proteinChange", "variantType"]
available = [c for c in cols if c in mut_df.columns]
mut_df[available].to_csv(f"{study_id}_mutations.csv", index=False)
print(f"Saved {len(mut_df)} mutations → {study_id}_mutations.csv")
```

### Recipe: Query Patient-Level Clinical Attribute

When to use: Extract a specific clinical variable (e.g., tumor stage, age at diagnosis) for all patients.

```python
import requests
import pandas as pd

BASE_URL = "https://www.cbioportal.org/api"

def cbio_get(endpoint, params=None):
    r = requests.get(f"{BASE_URL}/{endpoint}", params=params,
                     headers={"Accept": "application/json"}, timeout=30)
    r.raise_for_status()
    return r.json()

study_id = "brca_tcga_pan_can_atlas_2018"

# Fetch a specific clinical attribute for all patients
attr_id = "TUMOR_STAGE"
clinical = cbio_get(f"studies/{study_id}/clinical-data",
                    params={"clinicalDataType": "PATIENT",
                            "projection": "DETAILED"})

clin_df = pd.DataFrame(clinical)
if "clinicalAttributeId" in clin_df.columns:
    stage_df = clin_df[clin_df["clinicalAttributeId"] == attr_id][["patientId", "value"]]
    print(f"Patients with {attr_id} annotation: {len(stage_df)}")
    print(stage_df["value"].value_counts().head(10).to_string())
```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `404 Not Found` on profile endpoint | Molecular profile does not exist for study | List profiles with `GET /molecular-profiles?studyId={id}`; confirm the profile ID |
| Empty mutations list | Gene has no mutations in the selected samples/profile | Verify study has a mutation profile; check sample IDs belong to the same study |
| `requests.exceptions.Timeout` | Large sample set (>1000) in a single request | Chunk requests to 300–500 samples; increase `timeout` to 120s |
| `entrezGeneIds` key error in response | Hugo symbol passed instead of Entrez ID | Use `POST /genes/fetch` to resolve symbols to integer Entrez IDs first |
| CNA values returned as strings | `value` field is string in JSON | Cast with `pd.to_numeric()` or `int(value)` before comparison |
| Expression profile not found | Study uses non-standard profile naming | Check profile list; look for `MRNA_EXPRESSION` alteration type in `GET /molecular-profiles` |
| Survival analysis has many NA values | Clinical attribute absent for some patients | Use `dropna()` on OS columns; check attribute availability with `GET /studies/{id}/clinical-attributes` |

## Related Skills

- `gnomad-database` — population variant allele frequencies for healthy cohorts (complement to cBioPortal somatic data)
- `cnvkit-copy-number` — CNVkit pipeline for generating SEG/CNA files that can be loaded into cBioPortal
- `pydeseq2-differential-expression` — differential expression analysis that can be applied to cBioPortal RNA-seq exports

## References

- [cBioPortal API Swagger UI](https://www.cbioportal.org/api/swagger-ui) — interactive REST API explorer with all endpoints
- [cBioPortal GitHub](https://github.com/cBioPortal/cbioportal) — source code and issue tracker
- [Cerami E et al., Cancer Discovery 2012](https://doi.org/10.1158/2159-8290.CD-12-0095) — original cBioPortal paper
- [Gao J et al., Science Signaling 2013](https://doi.org/10.1126/scisignal.2004088) — integrative analysis methods using cBioPortal
- [TCGA PanCancer Atlas](https://www.cell.com/pb-assets/consortium/pancanceratlas/pancani3/index.html) — primary data source for PanCancer Atlas studies
