---
name: "jaspar-database"
description: "JASPAR 2024 TF binding profiles via REST API and pyJASPAR. Retrieve PFMs/PWMs by TF name, JASPAR ID, species, or structural class. Scan DNA for TFBS; browse by taxon (human, mouse) or TF family (bHLH, zinc finger). Use for motif enrichment input, TFBS scanning, and regulatory sequence analysis. For ChIP-seq peak motif discovery use homer-motif-analysis; for regulatory variant scoring use regulomedb-database."
license: "CC-BY-4.0"
---

# JASPAR Database

## Overview

JASPAR is a curated, open-access database of transcription factor (TF) binding profiles represented as position frequency matrices (PFMs). The 2024 release contains 1,209 profiles in the CORE vertebrate collection, covering 783 TFs with experimentally validated binding data from SELEX, ChIP-seq, and PBM experiments. Access is free via the JASPAR REST API at `https://jaspar.elixir.no/api/v1/` — no authentication required — and through the `pyJASPAR` Python library for matrix retrieval and manipulation.

## When to Use

- Looking up the PWM or PFM for a specific TF by name (e.g., CTCF, SP1, GATA1) to use as motif input for a scanning tool
- Retrieving all JASPAR profiles for a species (e.g., Homo sapiens, Mus musculus) to build a motif library for enrichment analysis
- Scanning a DNA promoter sequence for predicted TF binding sites using a known PWM
- Finding all TFs of a given structural class (bHLH, zinc finger, homeodomain) to build a TF family binding profile set
- Getting metadata for a JASPAR matrix: number of binding sites, information content, GC content, experiment type
- Downloading complete JASPAR collection sets (CORE, UNVALIDATED, CNE) in JASPAR or MEME format for batch analysis
- Use `homer-motif-analysis` instead when you need de novo motif discovery from ChIP-seq peaks; JASPAR is for retrieving known matrices
- For regulatory element annotations tied to a genomic region use `encode-database` or `regulomedb-database`

## Prerequisites

- **Python packages**: `requests`, `pandas`, `matplotlib`, `numpy`
- **Optional**: `pyJASPAR` (Python library wrapping JASPAR REST API with BIOPYTHON motif objects)
- **Data requirements**: TF gene symbols, JASPAR matrix IDs (e.g., `MA0139.1`), or DNA sequences (string or FASTA)
- **Environment**: internet connection; no API key required
- **Rate limits**: no official published limits; use `time.sleep(0.5)` between batch requests

```bash
pip install requests pandas matplotlib numpy
pip install pyJASPAR   # optional; pulls in biopython
```

## Quick Start

```python
import requests

JASPAR_API = "https://jaspar.elixir.no/api/v1"

# Search for CTCF profile in the CORE vertebrate collection
r = requests.get(f"{JASPAR_API}/matrix/", params={
    "search": "CTCF",
    "collection": "CORE",
    "tax_group": "vertebrates",
    "format": "json"
}, timeout=15)
r.raise_for_status()
results = r.json()
print(f"Profiles found: {results['count']}")
for m in results["results"][:3]:
    print(f"  {m['matrix_id']}  {m['name']}  sites={m['sites']}  type={m['type']}")
# Profiles found: 2
#   MA0139.1  CTCF  sites=190  type=ChIP-seq
#   MA1929.1  CTCF  sites=2135  type=ChIP-seq
```

## Core API

### Query 1: Matrix Search

Search for TF profiles by TF name, species, collection, or taxonomic group. Returns a paginated list of matching profile records.

```python
import requests, time

JASPAR_API = "https://jaspar.elixir.no/api/v1"

def jaspar_search(search=None, collection="CORE", tax_id=None, tax_group=None,
                  tf_class=None, tf_family=None, page_size=50):
    """Search JASPAR matrices. Returns list of result dicts."""
    params = {"format": "json", "page_size": page_size}
    if search:      params["search"]     = search
    if collection:  params["collection"] = collection
    if tax_id:      params["tax_id"]     = tax_id
    if tax_group:   params["tax_group"]  = tax_group
    if tf_class:    params["tf_class"]   = tf_class
    if tf_family:   params["tf_family"]  = tf_family

    all_results = []
    url = f"{JASPAR_API}/matrix/"
    while url:
        r = requests.get(url, params=params if url == f"{JASPAR_API}/matrix/" else None, timeout=15)
        r.raise_for_status()
        data = r.json()
        all_results.extend(data["results"])
        url = data.get("next")   # follow pagination
        time.sleep(0.3)
    return all_results

# Example: all CORE vertebrate profiles for GATA family
gata_profiles = jaspar_search(search="GATA", collection="CORE", tax_group="vertebrates")
print(f"GATA profiles: {len(gata_profiles)}")
for m in gata_profiles[:4]:
    print(f"  {m['matrix_id']}  {m['name']:12s}  {m.get('tf_class','')}  sites={m['sites']}")
```

### Query 2: Matrix Retrieval

Fetch the full profile record for a specific matrix ID, including the raw PFM counts, metadata, and TF annotations.

```python
import requests

JASPAR_API = "https://jaspar.elixir.no/api/v1"

def get_matrix(matrix_id):
    """Return full matrix record for a JASPAR ID (e.g. 'MA0139.1')."""
    r = requests.get(f"{JASPAR_API}/matrix/{matrix_id}/", params={"format": "json"}, timeout=15)
    r.raise_for_status()
    return r.json()

m = get_matrix("MA0139.1")   # CTCF
print(f"ID: {m['matrix_id']}  Name: {m['name']}")
print(f"Collection: {m['collection']}  Type: {m['type']}")
print(f"Species: {[s['name'] for s in m.get('species', [])]}")
print(f"UniProt: {m.get('uniprot_ids', [])}")
print(f"Sites: {m['sites']}  Binding sites used to build matrix")
print(f"TF class: {m.get('class_name', 'n/a')}  Family: {m.get('family_name', 'n/a')}")

# PFM structure: dict mapping position (as str) -> {A, C, G, T: count}
pfm = m["pfm"]
n_positions = len(pfm)
print(f"\nPFM length: {n_positions} positions")
print(f"Position 0: {pfm['0']}")   # {A: x, C: y, G: z, T: w}
# Position 0: {'A': 87, 'C': 12, 'G': 22, 'T': 69}
```

### Query 3: PWM Computation from PFM

Convert a raw PFM (count matrix) to a position weight matrix (PWM) using log-odds scoring. The PWM is used for binding site scanning.

```python
import requests, numpy as np

JASPAR_API = "https://jaspar.elixir.no/api/v1"

def pfm_to_pwm(pfm_dict, pseudocount=0.8, background=None):
    """
    Convert JASPAR PFM dict to PWM (log2 odds).
    pfm_dict: dict of str(position) -> {A, C, G, T: float}
    Returns: numpy array shape (4, L), rows = [A, C, G, T]
    """
    if background is None:
        background = {"A": 0.25, "C": 0.25, "G": 0.25, "T": 0.25}
    bases = ["A", "C", "G", "T"]
    L = len(pfm_dict)
    counts = np.array([[pfm_dict[str(i)][b] for i in range(L)] for b in bases], dtype=float)
    counts += pseudocount
    freqs = counts / counts.sum(axis=0, keepdims=True)
    bg = np.array([background[b] for b in bases])[:, None]
    pwm = np.log2(freqs / bg)
    return pwm   # shape (4, L)

r = requests.get(f"{JASPAR_API}/matrix/MA0139.1/", params={"format": "json"}, timeout=15)
pfm = r.json()["pfm"]
pwm = pfm_to_pwm(pfm)

print(f"PWM shape: {pwm.shape}  (4 bases × {pwm.shape[1]} positions)")
print(f"Min score per position: {pwm.min(axis=0)[:5]}")
print(f"Max score per position: {pwm.max(axis=0)[:5]}")
# PWM shape: (19, ) -> transposed view: (4, 19)
# Min score per position: [-2.32 -3.64 -3.64 -1.32 -3.64]
# Max score per position: [ 1.87  1.82  1.87  1.71  1.90]
```

### Query 4: Sequence Scanning

Scan a DNA sequence for TFBS matches by sliding the PWM across the sequence and computing log-odds scores at each position.

```python
import requests, numpy as np

JASPAR_API = "https://jaspar.elixir.no/api/v1"

BASE_IDX = {"A": 0, "C": 1, "G": 2, "T": 3}

def pfm_to_pwm(pfm_dict, pseudocount=0.8):
    bases = ["A", "C", "G", "T"]
    L = len(pfm_dict)
    counts = np.array([[pfm_dict[str(i)][b] for i in range(L)] for b in bases], dtype=float)
    counts += pseudocount
    freqs = counts / counts.sum(axis=0, keepdims=True)
    return np.log2(freqs / 0.25)

def scan_sequence(seq, pwm, threshold_pct=0.80):
    """
    Slide pwm over seq, return hits above threshold_pct of max possible score.
    Returns list of (position, score, strand).
    """
    seq = seq.upper()
    L = pwm.shape[1]
    max_score = pwm.clip(min=0).sum(axis=0).sum()
    min_score = pwm.clip(max=0).sum(axis=0).sum()
    threshold = min_score + threshold_pct * (max_score - min_score)
    hits = []
    for i in range(len(seq) - L + 1):
        window = seq[i:i+L]
        if "N" in window:
            continue
        score = sum(pwm[BASE_IDX[window[j]], j] for j in range(L))
        if score >= threshold:
            hits.append((i, round(score, 3), "+"))
    return hits, max_score, threshold

# Fetch CTCF matrix and scan a synthetic CTCF-like sequence
r = requests.get(f"{JASPAR_API}/matrix/MA0139.1/", params={"format": "json"}, timeout=15)
pfm = r.json()["pfm"]
pwm = pfm_to_pwm(pfm)

# 100 bp sequence with known CTCF consensus embedded
seq = ("GCAGGTTTAAGCTTCCTGGCATTTAAGCTTCCTGGCATTTCCCCAGGGGGCGGAGGCAGAG"
       "CCGCGAGCCGCGAGCCGCGAGCCGCGAGCCGCGAGTTTAAG")
hits, max_score, thresh = scan_sequence(seq, pwm, threshold_pct=0.80)
print(f"Max PWM score: {max_score:.2f}  |  Threshold (80%): {thresh:.2f}")
print(f"Hits: {len(hits)}")
for pos, score, strand in hits:
    print(f"  pos={pos}  score={score:.2f}  {strand}  seq={seq[pos:pos+pwm.shape[1]]}")
```

### Query 5: Taxon Browser

List all JASPAR CORE profiles for a specific organism, identified by NCBI taxonomy ID.

```python
import requests, time, pandas as pd

JASPAR_API = "https://jaspar.elixir.no/api/v1"

# Common taxonomy IDs
TAX_IDS = {
    "Homo sapiens":    9606,
    "Mus musculus":    10090,
    "Rattus norvegicus": 10116,
    "Drosophila melanogaster": 7227,
    "Saccharomyces cerevisiae": 4932,
}

def get_species_profiles(tax_id, collection="CORE"):
    """Return all matrices for a species tax ID."""
    params = {"tax_id": tax_id, "collection": collection, "format": "json", "page_size": 100}
    results = []
    url = f"{JASPAR_API}/matrix/"
    while url:
        r = requests.get(url, params=params if url == f"{JASPAR_API}/matrix/" else None, timeout=15)
        r.raise_for_status()
        data = r.json()
        results.extend(data["results"])
        url = data.get("next")
        time.sleep(0.3)
    return results

human_profiles = get_species_profiles(TAX_IDS["Homo sapiens"])
print(f"Human CORE profiles: {len(human_profiles)}")
df = pd.DataFrame([{
    "matrix_id": m["matrix_id"],
    "name": m["name"],
    "tf_class": m.get("class_name", ""),
    "tf_family": m.get("family_name", ""),
    "sites": m["sites"],
    "type": m["type"],
} for m in human_profiles])
print(df.head(5).to_string(index=False))
print(f"\nExperiment types:\n{df['type'].value_counts().to_string()}")
```

### Query 6: TF Class and Family Browser

Find all profiles belonging to a specific TF structural class or family, useful for building class-specific motif libraries.

```python
import requests, time

JASPAR_API = "https://jaspar.elixir.no/api/v1"

def get_class_profiles(tf_class=None, tf_family=None, collection="CORE", tax_group="vertebrates"):
    """Return all profiles for a TF structural class or family."""
    params = {"collection": collection, "tax_group": tax_group, "format": "json", "page_size": 100}
    if tf_class:  params["tf_class"]  = tf_class
    if tf_family: params["tf_family"] = tf_family
    results = []
    url = f"{JASPAR_API}/matrix/"
    while url:
        r = requests.get(url, params=params if url == f"{JASPAR_API}/matrix/" else None, timeout=15)
        r.raise_for_status()
        data = r.json()
        results.extend(data["results"])
        url = data.get("next")
        time.sleep(0.3)
    return results

# Common TF classes: "Zinc-coordinating", "Basic leucine zipper", "Helix-turn-helix"
# Common TF families: "C2H2 ZF", "bHLH", "bZIP", "Homeodomain"
bhlh = get_class_profiles(tf_family="bHLH", collection="CORE", tax_group="vertebrates")
print(f"bHLH vertebrate profiles: {len(bhlh)}")
for m in bhlh[:5]:
    print(f"  {m['matrix_id']:12s} {m['name']:15s} sites={m['sites']:5d}  {m['type']}")
# bHLH vertebrate profiles: 47
#   MA0006.1     Ahr::Arnt      sites=6    ChIP-seq
#   MA0010.1     Tal1::Gata1    sites=5    SELEX
```

## Key Concepts

### JASPAR Collections

JASPAR organizes profiles into curated collections:

| Collection | Description | Profile count |
|------------|-------------|---------------|
| `CORE` | Manually curated, non-redundant, high-quality profiles | ~1,200 (2024) |
| `CNE` | Profiles derived from conserved noncoding elements | ~100 |
| `UNVALIDATED` | Profiles not yet manually curated | ~1,000 |
| `PHYLOFACTS` | Profiles from phylogenetically constrained sites | ~100 |
| `POLII` | RNA polymerase II binding profiles | ~10 |

For most analyses use `CORE`. The JASPAR CORE 2024 vertebrate collection is the default reference for motif enrichment tools.

### Matrix ID Versioning

JASPAR matrix IDs have the format `MA{number}.{version}` (e.g., `MA0139.1`). A new version is released when the binding data is updated. When scripting, use the versioned ID for reproducibility. Searching by name (e.g., `CTCF`) returns all versions; select the highest-numbered version for the most up-to-date matrix.

### Information Content

The information content (IC) at each position (in bits) measures binding site specificity:

- IC = 2 - H(position), where H is the Shannon entropy
- High IC (close to 2 bits) = near-invariant base (e.g., always A)
- Low IC (close to 0) = little positional preference
- Total IC = sum over all positions; high total IC = more specific binding

```python
import numpy as np

def information_content(pfm_dict, pseudocount=0.8):
    """Compute per-position IC and total IC for a JASPAR PFM."""
    bases = ["A", "C", "G", "T"]
    L = len(pfm_dict)
    counts = np.array([[pfm_dict[str(i)][b] for i in range(L)] for b in bases], dtype=float)
    counts += pseudocount
    freqs = counts / counts.sum(axis=0, keepdims=True)
    entropy = -np.sum(freqs * np.log2(freqs + 1e-12), axis=0)
    ic_per_pos = 2 - entropy
    return ic_per_pos, ic_per_pos.sum()

import requests
r = requests.get("https://jaspar.elixir.no/api/v1/matrix/MA0139.1/",
                 params={"format": "json"}, timeout=15)
pfm = r.json()["pfm"]
ic_pos, total_ic = information_content(pfm)
print(f"Total IC: {total_ic:.2f} bits")
print(f"Max IC position: {ic_pos.argmax()}  ({ic_pos.max():.2f} bits)")
# Total IC: 19.47 bits
# Max IC position: 9  (1.99 bits)
```

## Common Workflows

### Workflow 1: Build a Human TF Motif Library and Export to MEME Format

**Goal**: Download all human CORE profiles and write them in MEME minimal format for use with FIMO, AME, or TOMTOM.

```python
import requests, time, numpy as np

JASPAR_API = "https://jaspar.elixir.no/api/v1"

def get_all_profiles(tax_id=9606, collection="CORE"):
    params = {"tax_id": tax_id, "collection": collection, "format": "json", "page_size": 100}
    results, url = [], f"{JASPAR_API}/matrix/"
    while url:
        r = requests.get(url, params=params if url == f"{JASPAR_API}/matrix/" else None, timeout=15)
        r.raise_for_status()
        data = r.json()
        results.extend(data["results"])
        url = data.get("next")
        time.sleep(0.3)
    return results

def pfm_to_freq(pfm_dict, pseudocount=0.1):
    """Return (4, L) frequency matrix [A, C, G, T]."""
    bases = ["A", "C", "G", "T"]
    L = len(pfm_dict)
    counts = np.array([[pfm_dict[str(i)][b] for i in range(L)] for b in bases], dtype=float)
    counts += pseudocount
    return counts / counts.sum(axis=0, keepdims=True)

profiles = get_all_profiles(tax_id=9606, collection="CORE")
print(f"Downloaded {len(profiles)} human CORE profiles")

meme_lines = [
    "MEME version 4",
    "ALPHABET= ACGT",
    "strands: + -",
    "Background letter frequencies",
    "A 0.25 C 0.25 G 0.25 T 0.25",
    "",
]
for m in profiles:
    pfm = m["pfm"]
    freq = pfm_to_freq(pfm)
    L = freq.shape[1]
    meme_lines.append(f"MOTIF {m['matrix_id']} {m['name']}")
    meme_lines.append(f"letter-probability matrix: alength= 4 w= {L} nsites= {m['sites']}")
    for j in range(L):
        row = " ".join(f"{freq[b, j]:.4f}" for b in range(4))
        meme_lines.append(f"  {row}")
    meme_lines.append("")

output_path = "jaspar_human_core_2024.meme"
with open(output_path, "w") as f:
    f.write("\n".join(meme_lines))
print(f"Written: {output_path}  ({len(profiles)} motifs)")
```

### Workflow 2: Promoter Scan for Multiple TFs and Visualize PWM Logos

**Goal**: Download PWMs for a set of TFs and scan a promoter sequence, then visualize the best-scoring hit as a bar logo.

```python
import requests, numpy as np, time
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

JASPAR_API = "https://jaspar.elixir.no/api/v1"
BASE_IDX = {"A": 0, "C": 1, "G": 2, "T": 3}
BASE_COLORS = {"A": "#2ca02c", "C": "#1f77b4", "G": "#ff7f0e", "T": "#d62728"}

def fetch_pwm(matrix_id, pseudocount=0.8):
    r = requests.get(f"{JASPAR_API}/matrix/{matrix_id}/", params={"format": "json"}, timeout=15)
    r.raise_for_status()
    pfm = r.json()["pfm"]
    L = len(pfm)
    counts = np.array([[pfm[str(i)][b] for i in range(L)] for b in ["A","C","G","T"]], dtype=float)
    counts += pseudocount
    freqs = counts / counts.sum(axis=0, keepdims=True)
    return np.log2(freqs / 0.25), freqs

def scan(seq, pwm, pct=0.80):
    seq = seq.upper()
    L = pwm.shape[1]
    max_s = pwm.clip(min=0).sum()
    min_s = pwm.clip(max=0).sum()
    thresh = min_s + pct * (max_s - min_s)
    return [(i, sum(pwm[BASE_IDX[seq[i+j]], j] for j in range(L)))
            for i in range(len(seq)-L+1) if "N" not in seq[i:i+L]
            and sum(pwm[BASE_IDX[seq[i+j]], j] for j in range(L)) >= thresh]

def plot_logo(freqs, title, outfile):
    """Bar-chart sequence logo from frequency matrix (4, L)."""
    L = freqs.shape[1]
    entropy = -np.sum(freqs * np.log2(freqs + 1e-12), axis=0)
    ic = 2 - entropy
    bases = ["A", "C", "G", "T"]
    fig, ax = plt.subplots(figsize=(max(6, L * 0.5), 2.5))
    bottom = np.zeros(L)
    for idx, base in enumerate(bases):
        heights = freqs[idx] * ic
        ax.bar(range(L), heights, bottom=bottom, color=BASE_COLORS[base], label=base, width=0.8)
        bottom += heights
    ax.set_xticks(range(L))
    ax.set_xticklabels([str(i+1) for i in range(L)], fontsize=7)
    ax.set_ylabel("Information Content (bits)")
    ax.set_title(title, fontsize=10)
    ax.legend(handles=[mpatches.Patch(color=BASE_COLORS[b], label=b) for b in bases],
              loc="upper right", fontsize=7, ncol=4)
    plt.tight_layout()
    plt.savefig(outfile, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Saved {outfile}")

# TP53 promoter-region fragment (GRCh38 chr17:7,687,000-7,687,100)
promoter = ("GCAGAGGCGGAGGATTTGCCTTTTTTCGAGTTGGTGAGAGATCTGGGGCGGGGCAGGGCC"
            "CTGGAACGGCAGGACGGAGAGCAAGGCCGGGGAAGGGCGGGAGCGGGCGGG")

# Scan for SP1 (MA0080.4) and TP53 (MA0106.3) hits
for matrix_id, tf_name in [("MA0080.4", "SP1"), ("MA0106.3", "TP53")]:
    pwm, freqs = fetch_pwm(matrix_id)
    hits = scan(promoter, pwm, pct=0.75)
    print(f"{tf_name} ({matrix_id}): {len(hits)} hits at >=75% threshold")
    for pos, score in hits[:3]:
        print(f"   pos={pos}  score={score:.2f}  {promoter[pos:pos+pwm.shape[1]]}")
    plot_logo(freqs, f"{tf_name} ({matrix_id}) PWM logo", f"{tf_name}_logo.png")
    time.sleep(0.5)
```

### Workflow 3: TF Co-binding Partner Discovery via Shared Matrix Families

**Goal**: Find all TF families that have profiles in JASPAR, then retrieve family members to identify potential co-binding partners of a TF of interest.

```python
import requests, time, pandas as pd
from collections import Counter

JASPAR_API = "https://jaspar.elixir.no/api/v1"

def get_profiles_df(tax_group="vertebrates", collection="CORE"):
    params = {"tax_group": tax_group, "collection": collection, "format": "json", "page_size": 100}
    results, url = [], f"{JASPAR_API}/matrix/"
    while url:
        r = requests.get(url, params=params if url == f"{JASPAR_API}/matrix/" else None, timeout=15)
        r.raise_for_status()
        data = r.json()
        results.extend(data["results"])
        url = data.get("next")
        time.sleep(0.3)
    return pd.DataFrame([{
        "matrix_id": m["matrix_id"],
        "name": m["name"],
        "tf_class": m.get("class_name", "Unknown"),
        "tf_family": m.get("family_name", "Unknown"),
        "sites": m["sites"],
        "type": m["type"],
        "uniprot": ";".join(m.get("uniprot_ids", [])),
    } for m in results])

df = get_profiles_df(tax_group="vertebrates", collection="CORE")
print(f"Total CORE vertebrate profiles: {len(df)}")

# Top TF families
family_counts = df["tf_family"].value_counts()
print(f"\nTop 10 TF families:")
print(family_counts.head(10).to_string())

# Co-binding: find all TFs in the same family as CTCF
ctcf_row = df[df["name"] == "CTCF"].iloc[0]
ctcf_family = ctcf_row["tf_family"]
co_family = df[df["tf_family"] == ctcf_family][["matrix_id", "name", "sites", "type"]]
print(f"\nTFs in {ctcf_family} family (potential CTCF co-binders by class):")
print(co_family.to_string(index=False))
df.to_csv("jaspar_core_vertebrates.csv", index=False)
print(f"\nSaved jaspar_core_vertebrates.csv")
```

## Key Parameters

| Parameter | Endpoint | Default | Range / Options | Effect |
|-----------|----------|---------|-----------------|--------|
| `search` | `/matrix/` | — | Any string (TF name, gene symbol) | Full-text search across name and aliases |
| `collection` | `/matrix/` | — | `CORE`, `UNVALIDATED`, `CNE`, `POLII`, `PHYLOFACTS` | Restricts to a JASPAR sub-collection |
| `tax_group` | `/matrix/` | — | `vertebrates`, `insects`, `plants`, `fungi`, `nematodes`, `urochordates` | Filter by broad taxonomic group |
| `tax_id` | `/matrix/` | — | NCBI taxonomy ID integer (e.g., `9606`) | Restrict to a single species |
| `tf_class` | `/matrix/` | — | `"Zinc-coordinating"`, `"Basic leucine zipper"`, `"Helix-turn-helix"`, etc. | Filter by TF structural class |
| `tf_family` | `/matrix/` | — | `"C2H2 ZF"`, `"bHLH"`, `"bZIP"`, `"Homeodomain"`, etc. | Filter by TF structural family |
| `page_size` | `/matrix/` | 10 | 1–100 | Results per page; use 100 for batch downloads |
| `pseudocount` | PFM→PWM (local) | 0.8 | 0.01–1.0 | Smooths zero-count positions; higher = less extreme PWM values |
| `threshold_pct` | scan (local) | 0.80 | 0.50–0.99 | Fraction of max score required to call a hit; lower = more permissive |

## Best Practices

1. **Pin matrix ID versions for reproducibility**: Use `MA0139.1` (not just `CTCF`) in scripts and manuscripts so results do not silently change across JASPAR releases.

2. **Always add pseudocounts when computing PWMs**: Raw PFMs contain zero counts for rare positions. A zero count produces -inf in log space, eliminating any sequence with that nucleotide. Use `pseudocount = 0.8` (JASPAR recommendation) or `pseudocount = sqrt(sites) / 4`.

3. **Use the CORE collection for standard analyses**: `UNVALIDATED` profiles have not been manually curated and may contain lower-confidence motifs. Reserve `UNVALIDATED` for exploratory analyses.

4. **Respect pagination**: JASPAR returns at most 100 results per page. Always follow the `next` URL in responses when building complete profile sets.

5. **For batch scanning, use FIMO (MEME suite) rather than manual sliding window**: The manual scanning above is educational. For production use, export matrices to MEME format (Workflow 1) and use `fimo --thresh 1e-4 motifs.meme sequence.fa`.

## Common Recipes

### Recipe: Fetch All Versions of a TF's Matrix

When to use: Compare old and new profile versions of the same TF to check for changes.

```python
import requests

JASPAR_API = "https://jaspar.elixir.no/api/v1"

def get_all_versions(tf_name, collection="CORE"):
    r = requests.get(f"{JASPAR_API}/matrix/", params={
        "search": tf_name, "collection": collection, "format": "json", "page_size": 50
    }, timeout=15)
    r.raise_for_status()
    return r.json()["results"]

versions = get_all_versions("SP1")
print(f"SP1 matrix versions in CORE: {len(versions)}")
for m in sorted(versions, key=lambda x: x["matrix_id"]):
    print(f"  {m['matrix_id']:12s}  sites={m['sites']:5d}  type={m['type']}")
# SP1 matrix versions in CORE: 4
#   MA0080.1      sites=   18  type=SELEX
#   MA0080.2      sites=   20  type=SELEX
#   MA0080.3      sites=  146  type=ChIP-seq
#   MA0080.4      sites=  481  type=ChIP-seq
```

### Recipe: Retrieve Matrix in JASPAR Flat-File Format

When to use: Download a matrix in the legacy JASPAR text format for tools that accept it directly.

```python
import requests

JASPAR_API = "https://jaspar.elixir.no/api/v1"

def get_jaspar_format(matrix_id):
    """Return matrix as JASPAR flat-file string."""
    r = requests.get(f"{JASPAR_API}/matrix/{matrix_id}/", params={"format": "jaspar"}, timeout=15)
    r.raise_for_status()
    return r.text

jaspar_str = get_jaspar_format("MA0139.1")
print(jaspar_str[:200])
# >MA0139.1  CTCF
# A [ 87  167  281  56  8  32  15  4  55 ...]
# C [ 12   30   98  42  111  30  ...]
# G [ 22   36  160  40  66  21  ...]
# T [ 69   67  ...  ]

with open("CTCF_MA0139.1.jaspar", "w") as f:
    f.write(jaspar_str)
print("Saved CTCF_MA0139.1.jaspar")
```

### Recipe: pyJASPAR Quick Motif Retrieval

When to use: Retrieve a motif as a BioPython `motifs.Motif` object when downstream tools expect that interface.

```python
# Requires: pip install pyJASPAR
import pyJASPAR

db = pyJASPAR.JASPAR2024(auto_reverse_complement=True)
motif = db.fetch_motif_by_id("MA0139.1")   # CTCF
print(f"Name: {motif.name}")
print(f"Matrix ID: {motif.matrix_id}")
print(f"Length: {len(motif)}")
print(f"Consensus: {motif.consensus}")
# Name: CTCF
# Matrix ID: MA0139.1
# Length: 19
# Consensus: CCGCGNGGNGGCAG

# Fetch multiple motifs for a TF family
motifs = db.fetch_motifs(collection="CORE", tax_id=9606, tf_family="bHLH")
print(f"Human bHLH motifs: {len(motifs)}")
for m in motifs[:3]:
    print(f"  {m.matrix_id}  {m.name}  len={len(m)}")
```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| Empty `results` list from search | TF not in JASPAR, wrong collection, or wrong `tax_group` | Try `collection=None` to search all collections; check TF alias (e.g., NF-kB → RELA) |
| `404 Not Found` for matrix ID | Invalid or misspelled matrix ID | Verify ID format: `MA` + 4 digits + `.` + version (e.g., `MA0139.1`); search by name first |
| `pfm['0']` missing key | Some JASPAR profiles have 0-indexed positions as integers, not strings | Cast position keys: `pfm_dict = {str(k): v for k, v in pfm.items()}` |
| PWM scan produces no hits | Threshold too strict or sequence too short | Lower `threshold_pct` to 0.70; check sequence length vs motif length |
| `pyJASPAR` install fails | Requires Python ≥3.8 and C extensions for BIOPYTHON | Use `requests`-based API directly; pyJASPAR is optional |
| Pagination stops early | `next` field is `null` before expected total | Check `count` field in first response vs `len(results)` after loop |
| High IC positions show wrong base | PFM row order assumed incorrectly | JASPAR always returns `{A, C, G, T}` keys; never assume positional ordering |

## Related Skills

- `homer-motif-analysis` — de novo motif discovery from ChIP-seq or ATAC-seq peak sets; complements JASPAR known-motif library
- `regulomedb-database` — regulatory variant scoring using TF binding evidence overlapping JASPAR motifs
- `encode-database` — download TF ChIP-seq peak files that can be cross-referenced with JASPAR profiles
- `remap-database` — TF binding peak sets from ChIP-seq experiments for binding site validation
- `macs3-peak-calling` — produce ChIP-seq peak BED files for downstream JASPAR motif enrichment

## References

- [JASPAR REST API v1 documentation](https://jaspar.elixir.no/api/v1/) — interactive browser and endpoint reference
- [Castro-Mondragon et al., Nucleic Acids Research 2022](https://doi.org/10.1093/nar/gkab1113) — JASPAR 2022 flagship paper describing collection structure and validation
- [pyJASPAR GitHub repository](https://github.com/asntech/pyjaspar) — Python library wrapping the JASPAR API with BioPython motif objects
- [Fornes et al., Nucleic Acids Research 2020](https://doi.org/10.1093/nar/gkz1001) — JASPAR 2020 paper introducing the CORE 2020 collection
