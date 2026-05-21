---
name: "remap-database"
description: "Access ReMap 2022 TF ChIP-seq peaks via per-TF BED downloads (https://remap.univ-amu.fr/storage/remap2022/.../MACS2/TF/{TF}/). REST API at remap2022.univ-amu.fr/api/v1/ is currently unreachable (backend on port 802 refuses connections); BED downloads + local pandas/pybedtools is the working path. Use jaspar-database for PWM motifs; encode-database for raw ENCODE tracks."
license: "CC-BY-4.0"
---

# ReMap TF ChIP-seq Database (BED-Download Access)

## Overview

> **API status (verified live 2026-05): the REST API at `remap2022.univ-amu.fr/api/v1/` is unreachable.** Every `/api/*` URL issues a 301 redirect to port 802, which refuses TCP connections (ECONNREFUSED). The web frontend is alive; only the API backend is dead. The official BED download URLs continue to serve — this skill uses them as the primary access path.

ReMap 2022 is an integrated catalogue of public TF ChIP-seq, ChIP-exo, and DAP-seq experiments (≈ 8,000 datasets, ≈ 1,210 TFs, ≈ 800 million peaks across human and other species). Two flavours are served:

- **Per-TF "non-redundant" (NR) BED files** — peak summit-clustered across all experiments for one TF, one assembly. Tens of MB per TF.
- **Per-TF "all" BED files** — every peak from every experiment for one TF (no clustering). Hundreds of MB to a few GB.
- **Bulk NR / CRM files** — atlas-wide non-redundant peaks (~1.5 GB) and cis-regulatory modules (~200 MB).

No authentication is required.

## When to Use

- Listing TF ChIP-seq peaks near a gene or in a region (intersect a per-TF NR BED with your query interval)
- Finding which TFs bind a regulatory element (intersect a small region with several per-TF NRs, or with the bulk NR atlas)
- Generating co-occupancy matrices across a TF panel
- Building enhancer/promoter TF-binding annotation tracks at scale
- Computing cell-type-specific TF occupancy (NR `name` field exposes cell-type provenance per peak)
- Use `jaspar-database` instead when you need PWM motif scoring rather than experimental peak overlap
- Use `encode-database` when you need the raw ENCODE experiment-level metadata / files rather than ReMap's harmonised peak sets

## Prerequisites

- **Python packages**: `requests`, `pandas`, `pybedtools` (optional but recommended for interval intersections)
- **Disk**: tens of MB per TF (NR) up to a few GB (per-TF "all"); bulk NR ≈ 1.5 GB
- **Bedtools binary**: only required if you use `pybedtools` (`pixi run` will already have it inside the env when added to `pixi.toml`; otherwise `apt install bedtools`)
- **No API key** required

```bash
pip install requests pandas pybedtools
# Optional system dep for pybedtools (skip if bedtools is already on PATH):
# conda install -c bioconda bedtools
```

## Quick Start

```python
import requests, gzip, io, pandas as pd

ROOT = "https://remap.univ-amu.fr/storage/remap2022"

def remap_per_tf_url(tf, assembly="hg38", flavour="nr"):
    """flavour ∈ {'nr', 'all'}. NR is non-redundant (clustered) — usually what you want."""
    return f"{ROOT}/{assembly}/MACS2/TF/{tf}/remap2022_{tf}_{flavour}_macs2_{assembly}_v1_0.bed.gz"

# Download CTCF non-redundant peaks (~22 MB)
url = remap_per_tf_url("CTCF", "hg38", "nr")
print("URL:", url)
buf = requests.get(url, timeout=120).content
df = pd.read_csv(io.BytesIO(gzip.decompress(buf)), sep="\t", header=None,
                 names=["chrom", "start", "end", "name", "score", "strand",
                        "thickStart", "thickEnd", "itemRgb"])
print(f"CTCF non-redundant peaks: {len(df):,}")
print(df.head(3).to_string(index=False))
```

## Core API

### Module 1: Download a Per-TF BED

```python
import requests, gzip, io, pandas as pd

ROOT = "https://remap.univ-amu.fr/storage/remap2022"

def fetch_remap_bed(tf, assembly="hg38", flavour="nr"):
    """Stream-download a ReMap BED into a pandas DataFrame.
    flavour='nr' for non-redundant (clustered, small), 'all' for full per-experiment."""
    url = f"{ROOT}/{assembly}/MACS2/TF/{tf}/remap2022_{tf}_{flavour}_macs2_{assembly}_v1_0.bed.gz"
    r = requests.get(url, timeout=300)
    r.raise_for_status()
    df = pd.read_csv(io.BytesIO(gzip.decompress(r.content)),
                     sep="\t", header=None, low_memory=False,
                     names=["chrom", "start", "end", "name", "score", "strand",
                            "thickStart", "thickEnd", "itemRgb"])
    return df

ctcf = fetch_remap_bed("CTCF", "hg38", "nr")
print(f"CTCF NR peaks: {len(ctcf):,}; chroms covered: {ctcf['chrom'].nunique()}")
```

### Module 2: Parse the `name` Field

The `name` column encodes the TF and the cell types contributing to each peak — but the format **differs by flavour**:

| Flavour | `name` encoding | Example |
|---------|------------------|---------|
| Per-TF NR | `TF:cell1,cell2,...` (colon + comma list) | `CTCF:HeLa-S3,K562,GM12878` |
| Per-TF "all" / bulk "all" | `EXPERIMENT.TF.CELL_TYPE` (dots) | `GSE91099.CTCF.HeLa-S3` |
| Bulk NR | `TF:CELL_TYPE` (one cell type) | `CTCF:HeLa-S3` |
| CRM (cis-regulatory module) | comma-separated TF list; peak count in `score` | `CTCF,RAD21,SMC1A` |

```python
def parse_nr_name(name):
    """Per-TF NR encoding: 'TF:cell1,cell2,...' → (tf, [cells])."""
    if ":" not in name:
        return name, []
    tf, cells = name.split(":", 1)
    return tf, [c for c in cells.split(",") if c]

# Distribution of cell types in CTCF NR
from collections import Counter
cells = Counter()
for nm in ctcf["name"].head(5000):
    _, cs = parse_nr_name(nm)
    cells.update(cs)
print("Top cell types contributing to CTCF NR peaks:")
for c, n in cells.most_common(8):
    print(f"  {c}: {n}")
```

### Module 3: Intersect with a Region

```python
import pandas as pd

def peaks_in_region(bed_df, chrom, start, end):
    """Return rows of bed_df overlapping the half-open interval [start, end)."""
    sel = ((bed_df["chrom"] == chrom)
           & (bed_df["start"] < end)
           & (bed_df["end"] > start))
    return bed_df.loc[sel].copy()

# CTCF peaks within ±20 kb of the MYC promoter (hg38: chr8:127,735,434)
myc_peaks = peaks_in_region(ctcf, "chr8", 127_715_434, 127_755_434)
print(f"CTCF NR peaks near MYC: {len(myc_peaks)}")
print(myc_peaks[["chrom", "start", "end", "score"]].head().to_string(index=False))
```

### Module 4: Intersect with a Gene (via Ensembl coordinates)

```python
import requests, gzip, io, pandas as pd
ROOT = "https://remap.univ-amu.fr/storage/remap2022"

def gene_coordinates(gene_symbol, assembly="GRCh38", flank=10_000):
    """Resolve a gene to genomic coordinates via Ensembl REST."""
    r = requests.get(f"https://rest.ensembl.org/lookup/symbol/homo_sapiens/{gene_symbol}",
                     headers={"Accept": "application/json"}, timeout=30)
    r.raise_for_status()
    g = r.json()
    chrom = "chr" + str(g["seq_region_name"])
    return chrom, max(0, g["start"] - flank), g["end"] + flank

def tf_peaks_at_gene(tf, gene_symbol, flank=10_000, assembly="hg38"):
    chrom, start, end = gene_coordinates(gene_symbol, flank=flank)
    url = f"{ROOT}/{assembly}/MACS2/TF/{tf}/remap2022_{tf}_nr_macs2_{assembly}_v1_0.bed.gz"
    df = pd.read_csv(io.BytesIO(gzip.decompress(requests.get(url, timeout=300).content)),
                     sep="\t", header=None, low_memory=False,
                     names=["chrom","start","end","name","score","strand",
                            "thickStart","thickEnd","itemRgb"])
    return df[(df["chrom"] == chrom) & (df["start"] < end) & (df["end"] > start)]

myc_tp53 = tf_peaks_at_gene("TP53", "MYC", flank=20_000)
print(f"TP53 NR peaks ± 20 kb of MYC: {len(myc_tp53)}")
print(myc_tp53.head(3).to_string(index=False))
```

### Module 5: Cell-Type Filter

```python
def filter_by_cell(bed_df, cell_pattern):
    """Keep per-TF-NR peaks whose name field includes a cell-type matching cell_pattern."""
    def has_cell(name):
        if ":" not in name:
            return False
        _, cells = name.split(":", 1)
        return any(cell_pattern.lower() in c.lower() for c in cells.split(","))
    return bed_df[bed_df["name"].apply(has_cell)].copy()

k562_ctcf = filter_by_cell(ctcf, "K562")
print(f"CTCF NR peaks present in K562: {len(k562_ctcf):,}")
```

### Module 6: TF Co-Occupancy at a Region

```python
import requests, gzip, io, pandas as pd
ROOT = "https://remap.univ-amu.fr/storage/remap2022"

def has_peak(tf, chrom, start, end, assembly="hg38"):
    """True if the per-TF NR BED has any peak overlapping the region."""
    url = f"{ROOT}/{assembly}/MACS2/TF/{tf}/remap2022_{tf}_nr_macs2_{assembly}_v1_0.bed.gz"
    r = requests.get(url, timeout=300)
    if r.status_code != 200:
        return False
    df = pd.read_csv(io.BytesIO(gzip.decompress(r.content)),
                     sep="\t", header=None, low_memory=False,
                     names=["chrom","start","end","name","score","strand",
                            "thickStart","thickEnd","itemRgb"])
    return ((df["chrom"] == chrom) & (df["start"] < end) & (df["end"] > start)).any()

# MYC promoter region
hits = {tf: has_peak(tf, "chr8", 127_735_000, 127_736_000)
        for tf in ["CTCF", "TP53", "MYC", "RAD21"]}
print(hits)
```

## Key Concepts

### File Layout

```
https://remap.univ-amu.fr/storage/remap2022/{assembly}/MACS2/
├── remap2022_nr_macs2_{assembly}_v1_0.bed.gz     # bulk NR atlas (≈1.5 GB hg38)
├── remap2022_crm_macs2_{assembly}_v1_0.bed.gz    # cis-regulatory modules (≈200 MB)
└── TF/
    └── {TF}/
        ├── remap2022_{TF}_nr_macs2_{assembly}_v1_0.bed.gz     # per-TF NR (small)
        └── remap2022_{TF}_all_macs2_{assembly}_v1_0.bed.gz    # per-TF all experiments
```

Supported assemblies: `hg38` (human), `hg19`, `mm10` (mouse), `dm6` (Drosophila), `ara` (Arabidopsis).

### BED Columns

Standard 9-column BED (header omitted in the gzipped file):

| Column | Meaning |
|--------|---------|
| `chrom`, `start`, `end` | Half-open genomic interval (0-based) |
| `name` | TF + cell-type provenance (encoding differs by flavour — see Module 2) |
| `score` | UCSC `score` field (0–1000). For CRM rows it carries the count of TFs at the module. |
| `strand` | `.` (TF binding has no strand) |
| `thickStart`, `thickEnd` | UCSC display fields; equal `start`/`end` for ReMap |
| `itemRgb` | Display colour |

### NR vs "All"

- **NR ("non-redundant")** — peaks summit-clustered across all contributing experiments for that TF. Smaller, faster, sufficient for "which regions does this TF bind?" questions.
- **"All"** — every peak from every experiment. Use when you need experiment-level provenance (e.g. counting peaks per replicate) or per-cell-type peak coordinates without clustering.

## Common Workflows

### Workflow 1: TF Binding Around a Gene

```python
import requests, gzip, io, pandas as pd

ROOT = "https://remap.univ-amu.fr/storage/remap2022"

def gene_coords(symbol, flank=20_000):
    r = requests.get(f"https://rest.ensembl.org/lookup/symbol/homo_sapiens/{symbol}",
                     headers={"Accept": "application/json"}, timeout=30)
    r.raise_for_status()
    g = r.json()
    return "chr" + str(g["seq_region_name"]), g["start"] - flank, g["end"] + flank

def remap_bed(tf, assembly="hg38", flavour="nr"):
    url = f"{ROOT}/{assembly}/MACS2/TF/{tf}/remap2022_{tf}_{flavour}_macs2_{assembly}_v1_0.bed.gz"
    r = requests.get(url, timeout=300); r.raise_for_status()
    return pd.read_csv(io.BytesIO(gzip.decompress(r.content)),
                       sep="\t", header=None, low_memory=False,
                       names=["chrom","start","end","name","score","strand",
                              "thickStart","thickEnd","itemRgb"])

def tf_peaks_near_gene(tf, gene, flank=20_000):
    df = remap_bed(tf)
    chrom, lo, hi = gene_coords(gene, flank=flank)
    return df[(df["chrom"] == chrom) & (df["start"] < hi) & (df["end"] > lo)]

panel = ["CTCF", "TP53", "MYC", "RAD21"]
counts = {tf: len(tf_peaks_near_gene(tf, "CDKN1A", flank=20_000)) for tf in panel}
print("Peaks ± 20 kb of CDKN1A:")
for tf, n in sorted(counts.items(), key=lambda kv: -kv[1]):
    print(f"  {tf:6s}: {n}")
```

### Workflow 2: Cell-Type Restricted TF Occupancy Matrix

```python
import requests, gzip, io, pandas as pd
ROOT = "https://remap.univ-amu.fr/storage/remap2022"

def per_tf_nr(tf, assembly="hg38"):
    url = f"{ROOT}/{assembly}/MACS2/TF/{tf}/remap2022_{tf}_nr_macs2_{assembly}_v1_0.bed.gz"
    r = requests.get(url, timeout=300); r.raise_for_status()
    return pd.read_csv(io.BytesIO(gzip.decompress(r.content)),
                       sep="\t", header=None, low_memory=False,
                       names=["chrom","start","end","name","score","strand",
                              "thickStart","thickEnd","itemRgb"])

def has_cell(name, cell):
    if ":" not in name: return False
    _, cs = name.split(":", 1)
    return any(cell.lower() in c.lower() for c in cs.split(","))

# Build a matrix: TFs × cell types, value = K562/HeLa peak counts in a region
panel = ["CTCF", "TP53", "RAD21"]
cells = ["K562", "HeLa", "GM12878"]
region = ("chr8", 127_700_000, 127_800_000)  # MYC locus
matrix = pd.DataFrame(0, index=panel, columns=cells, dtype=int)

for tf in panel:
    df = per_tf_nr(tf)
    in_region = df[(df["chrom"] == region[0])
                   & (df["start"] < region[2])
                   & (df["end"] > region[1])]
    for cell in cells:
        matrix.loc[tf, cell] = in_region["name"].apply(lambda n: has_cell(n, cell)).sum()

print("TF NR peaks at MYC locus by cell type:")
print(matrix.to_string())
```

## Key Parameters

| Parameter | Where | Default | Range / Options | Effect |
|-----------|-------|---------|-----------------|--------|
| `assembly` | BED URL | `hg38` | `hg38`, `hg19`, `mm10`, `dm6`, `ara` | Genome build |
| `flavour` | BED URL | `nr` | `nr`, `all` | Non-redundant (small) vs full per-experiment (large) |
| `tf` | BED URL | required | TF symbol (case-sensitive, matches ReMap naming) | Selects per-TF file |
| `flank` (in workflows) | client-side | `10_000` | non-negative int (bp) | Padding added around gene coordinates |
| `chrom` / `start` / `end` | client-side | required | half-open BED interval, 0-based | Query window |

## Best Practices

1. **Prefer the per-TF NR BED**: tens of MB, fast to download, sufficient for "where does TF X bind?" questions. Only fall back to "all" when you need experiment-level provenance.
2. **Cache downloads on disk** — files don't change between releases (`remap2022_..._v1_0.bed.gz`); avoid re-downloading on every call. A simple `if Path(cache).exists(): use cache else: download` wrapper is enough.
3. **Use `pybedtools` for large-scale intersections** — pandas works for one or two regions, but for VCFs / whole-genome panels, push to `pybedtools.BedTool(...).intersect(...)`.
4. **Match assembly to your query coordinates** — coordinates from hg19 pipelines must use the `hg19` BED; ReMap does not auto-liftover.
5. **`name` encoding differs across flavours** — see the table in Module 2. Build a small parser per flavour rather than a one-size-fits-all regex.
6. **The REST API is currently dead** — every `/api/v1/*` URL redirects to a port-802 backend that refuses TCP. Do not depend on it; use BED downloads.

## Common Recipes

### Recipe: List Cell Types in a Per-TF NR

```python
from collections import Counter

def cells_in(bed_df):
    cnt = Counter()
    for n in bed_df["name"]:
        if ":" in n:
            cnt.update(n.split(":", 1)[1].split(","))
    return cnt

# `ctcf` from Module 1
top = cells_in(ctcf).most_common(10)
for c, n in top:
    print(f"  {c}: {n}")
```

### Recipe: Cache Downloads on Disk

```python
from pathlib import Path
import requests, gzip, io, pandas as pd

ROOT = "https://remap.univ-amu.fr/storage/remap2022"
CACHE = Path("./remap_cache"); CACHE.mkdir(exist_ok=True)

def cached_remap(tf, assembly="hg38", flavour="nr"):
    fname = f"remap2022_{tf}_{flavour}_macs2_{assembly}_v1_0.bed.gz"
    path = CACHE / fname
    if not path.exists():
        url = f"{ROOT}/{assembly}/MACS2/TF/{tf}/{fname}"
        r = requests.get(url, timeout=300); r.raise_for_status()
        path.write_bytes(r.content)
    with gzip.open(path, "rb") as fh:
        return pd.read_csv(fh, sep="\t", header=None, low_memory=False,
                           names=["chrom","start","end","name","score","strand",
                                  "thickStart","thickEnd","itemRgb"])

ctcf_cached = cached_remap("CTCF")
print(f"CTCF NR (cached path): {len(ctcf_cached):,} peaks")
```

### Recipe: TFs at a Single Position via Bulk NR (Heavy)

When you need every TF that touches a small region, downloading per-TF BEDs one at a time is slow. The 1.5 GB bulk NR carries one row per (TF, cell) pair and is faster for many-TF queries — assuming you can hold or stream it.

```python
# Sketch — bulk NR is ~1.5 GB; recommended only with disk cache + tabix/pybedtools.
BULK_NR = "https://remap.univ-amu.fr/storage/remap2022/hg38/MACS2/remap2022_nr_macs2_hg38_v1_0.bed.gz"
# Skipped end-to-end execution here to avoid a 1.5 GB download in the example.
# In practice: download once, build a tabix index with `tabix -p bed`, then query intervals.
```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `ConnectionRefusedError` on `/api/v1/*` | REST API backend (port 802) is down | Use BED downloads (this skill's primary path). Track ReMap's announcements for restoration. |
| HTTP 404 on a per-TF URL | TF name case mismatch, or TF not present in that assembly | Check ReMap's "download" web page for the canonical TF symbol; some TFs are mouse-only |
| `name`-field parser yields empty cell lists | You're parsing the wrong flavour | Per-TF NR uses `TF:cell,cell,...`; per-TF "all" uses `EXPERIMENT.TF.CELL`; see Module 2 table |
| `MemoryError` reading bulk NR | 1.5 GB uncompressed; doesn't fit easily into RAM | Stream-read with `pandas.read_csv(chunksize=...)` or build a tabix index and query intervals |
| Wrong-build coordinates | hg19 query against hg38 BED (or vice versa) | Re-fetch the BED with the matching `assembly=` |
| `pybedtools` ImportError | `bedtools` binary not on PATH | `conda install -c bioconda bedtools` or skip pybedtools (pandas-only path works) |
| Slow per-TF download in a loop | Re-downloading every iteration | Use the "Cache Downloads on Disk" recipe |

## Related Skills

- `jaspar-database` — PWM motifs for the same TFs (binding-site sequence vs experimental peaks)
- `encode-database` — Raw ENCODE experiment metadata and per-experiment peak files (ReMap is the harmonised superset)
- `ensembl-database` — Gene coordinate / transcript lookups for region-around-gene queries
- `ucsc-genome-browser` — Visualise BED tracks alongside the genome browser
- `regulomedb-database` — Regulatory variant scoring; ReMap peaks underlie some of its TF evidence

## References

- [ReMap 2022 — downloads](https://remap.univ-amu.fr/download_page) — Per-TF and bulk NR / CRM BED files
- [ReMap atlas paper (NAR 2022)](https://doi.org/10.1093/nar/gkab996) — Hammal F et al., *Nucleic Acids Research* 50(D1): D316–D325
- [ReMap 2020 paper (NAR 2020)](https://doi.org/10.1093/nar/gkz945) — Chèneby J et al., *Nucleic Acids Research* 48(D1): D180–D188
- [ReMap home](https://remap.univ-amu.fr/)
