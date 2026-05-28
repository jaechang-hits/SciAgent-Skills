---
name: "ucsc-genome-browser"
description: "Query UCSC Genome Browser REST API for DNA sequences, tracks, gene models, and conservation across 100+ assemblies. Retrieve sequence by region, list/fetch BED/bigWig tracks, chromosome sizes, RefSeq/GENCODE gene structures, PhyloP/PhastCons scores. Use for UCSC annotations; Ensembl REST API for Ensembl gene IDs and VEP variant annotation."
license: "Apache-2.0"
---

# UCSC Genome Browser

## Overview

The UCSC Genome Browser REST API at `https://api.genome.ucsc.edu/` provides programmatic access to genome sequences, annotation tracks, and hub data for 100+ assemblies including hg38, mm39, and dm6. The API is free, requires no authentication, and returns JSON. Use it with the `requests` library to fetch DNA sequences for genomic regions, retrieve track data (genes, repeats, conservation), list available tracks, and query chromosome sizes for genome-scale coordinate arithmetic.

## When to Use

- Fetching the reference DNA sequence for any genomic region (e.g., promoter, exon, CRISPR target) across human, mouse, or other assemblies
- Retrieving RefSeq or GENCODE gene structure (exon coordinates, CDS boundaries, strand) for a locus of interest
- Looking up PhyloP or PhastCons conservation scores to assess evolutionary constraint at a variant site
- Listing and querying any of UCSC's 1000+ annotation tracks (repeats, regulatory elements, conservation) for a region
- Getting chromosome sizes for a genome assembly to set up bedtools, pysam, or coverage pipelines
- Accessing public UCSC track hubs (e.g., ENCODE, Roadmap Epigenomics) without downloading data locally
- Use `ensembl-database` instead when you need Ensembl stable IDs, VEP variant annotation, or cross-species comparative genomics via the Ensembl REST API
- For bulk local queries across millions of regions, use `bedtools-genomic-intervals` with pre-downloaded UCSC annotation files

## Prerequisites

- **Python packages**: `requests`, `matplotlib` (for visualization)
- **Data requirements**: genomic coordinates (chrom, start, end in 0-based half-open BED format), genome assembly name (e.g., `hg38`, `mm39`)
- **Environment**: internet connection; no authentication required
- **Rate limits**: no official published limit; add 0.5s delays for batch requests (>100 queries)

```bash
pip install requests matplotlib
```

## Quick Start

```python
import requests

BASE = "https://api.genome.ucsc.edu"

def get_sequence(genome, chrom, start, end):
    """Fetch DNA sequence for a genomic region (0-based, half-open)."""
    r = requests.get(f"{BASE}/getData/sequence",
                     params={"genome": genome, "chrom": chrom,
                             "start": start, "end": end})
    r.raise_for_status()
    return r.json()["dna"]

# Fetch 1 kb around the BRCA1 TSS on hg38
seq = get_sequence("hg38", "chr17", 43044294, 43045294)
print(f"Length: {len(seq)} bp")
print(f"Sequence: {seq[:60]}...")
# Length: 1000 bp
# Sequence: ATGATTGGTGGTTACATGCACAGTTGCTCTGGGAAGTTTCTTCTTCAGTTGAGAAAAGGT...
```

## Core API

### Query 1: Sequence Retrieval

Fetch the reference DNA sequence for any genomic region using the `getData/sequence` endpoint. Coordinates are 0-based, half-open (BED format).

```python
import requests

BASE = "https://api.genome.ucsc.edu"

def get_sequence(genome, chrom, start, end):
    """Return DNA sequence string for the given region."""
    r = requests.get(f"{BASE}/getData/sequence",
                     params={"genome": genome, "chrom": chrom,
                             "start": start, "end": end})
    r.raise_for_status()
    data = r.json()
    return data["dna"]

# TP53 exon 4 region (hg38)
seq = get_sequence("hg38", "chr17", 7676520, 7676620)
print(f"Region: chr17:7,676,520-7,676,620 ({len(seq)} bp)")
print(f"Sequence: {seq}")
```

```python
# Reverse-complement for minus-strand genes
def revcomp(seq):
    comp = str.maketrans("ACGTacgt", "TGCAtgca")
    return seq.translate(comp)[::-1]

# BRCA2 on minus strand (hg38)
seq_fwd = get_sequence("hg38", "chr13", 32315086, 32315186)
seq_rc  = revcomp(seq_fwd)
print(f"Forward: {seq_fwd[:30]}...")
print(f"RevComp: {seq_rc[:30]}...")
```

### Query 2: Track Data Query

Retrieve annotation data (BED records) from any UCSC track for a genomic region.

```python
import requests

BASE = "https://api.genome.ucsc.edu"

def get_track_data(genome, track, chrom, start, end):
    """Fetch annotation records from a UCSC track for a region."""
    r = requests.get(f"{BASE}/getData/track",
                     params={"genome": genome, "track": track,
                             "chrom": chrom, "start": start, "end": end})
    r.raise_for_status()
    data = r.json()
    # Track data is under the key matching the track name
    return data.get(track, data.get("data", []))

# Fetch RepeatMasker annotations in the MYC locus (hg38)
repeats = get_track_data("hg38", "rmsk", "chr8", 127_735_434, 127_742_951)
print(f"Repeat elements in MYC locus: {len(repeats)}")
for r in repeats[:3]:
    print(f"  {r.get('repName', r.get('name'))} | {r['chromStart']}-{r['chromEnd']}")
```

```python
# Fetch CpG islands near a promoter
cpg_islands = get_track_data("hg38", "cpgIslandExt", "chr17", 43_044_000, 43_050_000)
print(f"CpG islands found: {len(cpg_islands)}")
for island in cpg_islands:
    print(f"  {island['name']}: {island['chromStart']}-{island['chromEnd']}, "
          f"obsExp={island.get('obsExp', 'n/a')}")
```

### Query 3: Track List

List all available annotation tracks for a genome assembly to discover what data is available.

```python
import requests

BASE = "https://api.genome.ucsc.edu"

def list_tracks(genome):
    """Return a dict of {track_name: track_metadata} for a genome assembly."""
    r = requests.get(f"{BASE}/list/tracks", params={"genome": genome})
    r.raise_for_status()
    return r.json().get("tracks", {})

tracks = list_tracks("hg38")
print(f"Total tracks in hg38: {len(tracks)}")

# Find conservation-related tracks
conserv = {k: v for k, v in tracks.items() if "conserv" in k.lower() or "phylop" in k.lower()}
for name, meta in list(conserv.items())[:5]:
    print(f"  {name}: {meta.get('shortLabel', '')}")
```

### Query 4: Chromosome Sizes

Get the length of every chromosome (or scaffold) for a genome assembly.

```python
import requests

BASE = "https://api.genome.ucsc.edu"

def get_chrom_sizes(genome):
    """Return {chrom: size_in_bp} for a genome assembly."""
    r = requests.get(f"{BASE}/list/chromosomes", params={"genome": genome})
    r.raise_for_status()
    return r.json().get("chromosomeSizes", {})

sizes = get_chrom_sizes("hg38")
print(f"hg38 chromosome count: {len(sizes)}")

# Show canonical autosomes + sex chromosomes
canonical = {c: sizes[c] for c in sorted(sizes) if c in
             [f"chr{i}" for i in range(1, 23)] + ["chrX", "chrY", "chrM"]}
for chrom, length in sorted(canonical.items(),
                             key=lambda x: int(x[0].replace("chr", "").replace("X", "23").replace("Y", "24").replace("M", "25"))):
    print(f"  {chrom}: {length:,} bp")
```

### Query 5: Gene Annotation

Query RefSeq gene models (exon coordinates, CDS, strand) for a genomic region.

```python
import requests

BASE = "https://api.genome.ucsc.edu"

def get_refgene(genome, chrom, start, end):
    """Retrieve RefSeq gene annotations for a region."""
    r = requests.get(f"{BASE}/getData/track",
                     params={"genome": genome, "track": "refGene",
                             "chrom": chrom, "start": start, "end": end})
    r.raise_for_status()
    return r.json().get("refGene", [])

# Query EGFR gene region (hg38)
genes = get_refgene("hg38", "chr7", 55_019_017, 55_211_628)
for g in genes:
    exon_count = g.get("exonCount", 0)
    print(f"  {g['name2']} ({g['name']}) | {g['strand']} | "
          f"tx: {g['txStart']}-{g['txEnd']} | exons: {exon_count}")
```

```python
# Parse exon intervals from a refGene record
def parse_exons(gene_record):
    """Return list of (exon_start, exon_end) from a refGene record."""
    starts = [int(s) for s in gene_record["exonStarts"].strip(",").split(",") if s]
    ends   = [int(e) for e in gene_record["exonEnds"].strip(",").split(",") if e]
    return list(zip(starts, ends))

genes = get_refgene("hg38", "chr7", 55_019_017, 55_211_628)
if genes:
    g = genes[0]
    exons = parse_exons(g)
    print(f"{g['name2']}: {len(exons)} exons")
    for i, (s, e) in enumerate(exons[:4], 1):
        print(f"  Exon {i}: {s}-{e} ({e-s} bp)")
```

### Query 6: Conservation Scores

Fetch per-base PhyloP or PhastCons conservation scores for a genomic region.

```python
import requests

BASE = "https://api.genome.ucsc.edu"

def get_conservation(genome, track, chrom, start, end):
    """Retrieve per-base conservation scores from a bigWig track."""
    r = requests.get(f"{BASE}/getData/track",
                     params={"genome": genome, "track": track,
                             "chrom": chrom, "start": start, "end": end})
    r.raise_for_status()
    data = r.json()
    # bigWig tracks return a list of {start, end, value} intervals
    return data.get(track, [])

# PhyloP 100-way conservation at TP53 mutation hotspot (hg38)
# chr17:7,676,594 = codon 248 (R248W/Q common hotspot)
scores = get_conservation("hg38", "phyloP100way", "chr17", 7_676_580, 7_676_610)
print(f"PhyloP 100way scores ({len(scores)} intervals):")
for s in scores[:5]:
    print(f"  chr17:{s['start']}-{s['end']}: phyloP = {s['value']:.3f}")
# Positive scores = conserved; negative = fast-evolving
```

### Query 7: Hub Access

Access public UCSC track hubs and list their available assemblies and tracks.

```python
import requests

BASE = "https://api.genome.ucsc.edu"

def list_ucsc_genomes():
    """Return all UCSC-hosted genome assemblies."""
    r = requests.get(f"{BASE}/list/ucscGenomes")
    r.raise_for_status()
    return r.json().get("ucscGenomes", {})

genomes = list_ucsc_genomes()
print(f"Total UCSC genome assemblies: {len(genomes)}")

# Find all human assemblies
human = {k: v for k, v in genomes.items() if "Homo sapiens" in v.get("scientificName", "")}
for name, meta in sorted(human.items()):
    print(f"  {name}: {meta.get('description', '')}")
```

## Key Concepts

### 0-Based vs. 1-Based Coordinates

The UCSC REST API uses **0-based, half-open** intervals (BED format): `start` is inclusive, `end` is exclusive. This matches BED files and Python slicing. The UCSC Genome Browser web interface displays 1-based positions. To convert: API `start = browser_start - 1`, API `end = browser_end`.

```python
# Browser position: chr17:7,676,521-7,676,620 (1-based, closed)
# API query (0-based, half-open):
start_api = 7_676_520   # browser_start - 1
end_api   = 7_676_620   # browser_end unchanged
seq = get_sequence("hg38", "chr17", start_api, end_api)
print(f"Fetched {len(seq)} bp (expected 100)")
```

### Track Data Response Format

Track data returned from `/getData/track` is keyed by track name. BED-like tracks return a list of dicts with `chrom`, `chromStart`, `chromEnd`, `name`, `score`, `strand`. bigWig tracks (conservation, signal) return `{start, end, value}` intervals. Always check the actual key in the response JSON, which matches the `track` parameter name.

## Common Workflows

### Workflow 1: Extract Promoter Sequences for a Gene List

**Goal**: Retrieve 2 kb upstream of the TSS for each gene in a list, for motif analysis or primer design.

```python
import requests
import time

BASE = "https://api.genome.ucsc.edu"
GENOME = "hg38"
PROMOTER_UP = 2000   # bp upstream of TSS

def get_refgene(genome, chrom, start, end):
    r = requests.get(f"{BASE}/getData/track",
                     params={"genome": genome, "track": "refGene",
                             "chrom": chrom, "start": start, "end": end})
    r.raise_for_status()
    return r.json().get("refGene", [])

def get_sequence(genome, chrom, start, end):
    r = requests.get(f"{BASE}/getData/sequence",
                     params={"genome": genome, "chrom": chrom,
                             "start": start, "end": end})
    r.raise_for_status()
    return r.json()["dna"]

def revcomp(seq):
    comp = str.maketrans("ACGTacgt", "TGCAtgca")
    return seq.translate(comp)[::-1]

# Genes of interest: query a known locus for each
gene_loci = {
    "BRCA1": ("chr17", 43_044_294, 43_125_482),
    "TP53":  ("chr17",  7_661_779,  7_687_538),
    "EGFR":  ("chr7",  55_019_017, 55_211_628),
}

results = {}
for gene, (chrom, locus_start, locus_end) in gene_loci.items():
    records = get_refgene(GENOME, chrom, locus_start, locus_end)
    # Pick the longest transcript
    records = [r for r in records if r.get("name2") == gene]
    if not records:
        print(f"  {gene}: not found")
        continue
    g = max(records, key=lambda x: x["txEnd"] - x["txStart"])
    if g["strand"] == "+":
        prom_start = max(0, g["txStart"] - PROMOTER_UP)
        prom_end   = g["txStart"]
    else:
        prom_start = g["txEnd"]
        prom_end   = g["txEnd"] + PROMOTER_UP
    seq = get_sequence(GENOME, chrom, prom_start, prom_end)
    if g["strand"] == "-":
        seq = revcomp(seq)
    results[gene] = {"chrom": chrom, "start": prom_start, "end": prom_end,
                     "strand": g["strand"], "seq": seq}
    print(f"  {gene}: {chrom}:{prom_start}-{prom_end} | strand={g['strand']} | {len(seq)} bp")
    time.sleep(0.5)

# Write FASTA
with open("promoters.fa", "w") as fh:
    for gene, d in results.items():
        fh.write(f">{gene} {d['chrom']}:{d['start']}-{d['end']}({d['strand']})\n")
        fh.write(d["seq"] + "\n")
print(f"\nSaved {len(results)} promoter sequences → promoters.fa")
```

### Workflow 2: Visualize Gene Structure from refGene Track

**Goal**: Draw an exon-intron diagram for a gene using matplotlib from refGene track data.

```python
import requests
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

BASE = "https://api.genome.ucsc.edu"

def get_refgene(genome, chrom, start, end):
    r = requests.get(f"{BASE}/getData/track",
                     params={"genome": genome, "track": "refGene",
                             "chrom": chrom, "start": start, "end": end})
    r.raise_for_status()
    return r.json().get("refGene", [])

def parse_exons(rec):
    starts = [int(s) for s in rec["exonStarts"].strip(",").split(",") if s]
    ends   = [int(e) for e in rec["exonEnds"].strip(",").split(",") if e]
    return list(zip(starts, ends))

# Fetch BRCA1 transcripts (hg38)
genes = get_refgene("hg38", "chr17", 43_044_294, 43_125_482)
brca1 = [g for g in genes if g.get("name2") == "BRCA1"]
print(f"BRCA1 transcripts: {len(brca1)}")

# Plot the canonical transcript (longest)
g = max(brca1, key=lambda x: x["txEnd"] - x["txStart"])
exons = parse_exons(g)
tx_start, tx_end = g["txStart"], g["txEnd"]
cds_start, cds_end = g["cdsStart"], g["cdsEnd"]

fig, ax = plt.subplots(figsize=(12, 2.5))
ax.set_xlim(tx_start - 500, tx_end + 500)
ax.set_ylim(-0.5, 1.5)

# Intron line
ax.hlines(0.5, tx_start, tx_end, color="#555", lw=1.5, zorder=1)

# Exon boxes
for exon_s, exon_e in exons:
    # UTR portion (thin) vs CDS (thick)
    cds_s = max(exon_s, cds_start)
    cds_e = min(exon_e, cds_end)
    # Full exon box (UTR height)
    ax.add_patch(mpatches.FancyBboxPatch(
        (exon_s, 0.25), exon_e - exon_s, 0.5,
        boxstyle="square,pad=0", fc="#a8c4e0", ec="#2c6fad", lw=0.8, zorder=2))
    # CDS box (taller)
    if cds_s < cds_e:
        ax.add_patch(mpatches.FancyBboxPatch(
            (cds_s, 0.15), cds_e - cds_s, 0.7,
            boxstyle="square,pad=0", fc="#2c6fad", ec="#1a4a7a", lw=0.8, zorder=3))

strand_arrow = "→" if g["strand"] == "+" else "←"
ax.set_title(f"{g['name2']} ({g['name']}) {strand_arrow} — hg38 {g['chrom']}:"
             f"{tx_start:,}-{tx_end:,} | {g['exonCount']} exons", fontsize=11)
ax.set_xlabel("Genomic position (bp)")
ax.set_yticks([])
plt.tight_layout()
plt.savefig("brca1_gene_structure.png", dpi=150, bbox_inches="tight")
print("Saved: brca1_gene_structure.png")
plt.show()
```

### Workflow 3: Batch Conservation Score Lookup

**Goal**: Retrieve mean PhyloP conservation for a list of variants or regions.

```python
import requests
import time
import pandas as pd

BASE = "https://api.genome.ucsc.edu"

def get_conservation(genome, track, chrom, start, end):
    r = requests.get(f"{BASE}/getData/track",
                     params={"genome": genome, "track": track,
                             "chrom": chrom, "start": start, "end": end})
    r.raise_for_status()
    return r.json().get(track, [])

# Variants to score (1-based positions → convert to 0-based)
variants = [
    {"id": "rs28897672",  "chrom": "chr17", "pos": 7_676_594},  # TP53 R248
    {"id": "rs80357906",  "chrom": "chr17", "pos": 43_094_692}, # BRCA1
    {"id": "rs1042522",   "chrom": "chr17", "pos": 7_676_147},  # TP53 R72P (common)
]

results = []
for v in variants:
    # Query ±5 bp window around each variant
    scores = get_conservation("hg38", "phyloP100way",
                               v["chrom"], v["pos"] - 6, v["pos"] + 5)
    values = [s["value"] for s in scores]
    mean_score = sum(values) / len(values) if values else float("nan")
    results.append({**v, "phyloP100way_mean": round(mean_score, 3),
                    "n_intervals": len(scores)})
    print(f"  {v['id']}: mean phyloP = {mean_score:.3f}")
    time.sleep(0.5)

df = pd.DataFrame(results)
df.to_csv("variant_conservation.csv", index=False)
print(f"\nSaved → variant_conservation.csv\n{df.to_string(index=False)}")
```

## Key Parameters

| Parameter | Module | Default | Range / Options | Effect |
|-----------|--------|---------|-----------------|--------|
| `genome` | All endpoints | — | `hg38`, `mm39`, `dm6`, any UCSC assembly | Selects the genome assembly |
| `chrom` | Sequence, Track | — | `chr1`–`chrY`, `chrM` | Chromosome name (UCSC `chr`-prefix convention) |
| `start` | Sequence, Track | — | 0–chrom_size | Region start (0-based, inclusive) |
| `end` | Sequence, Track | — | 1–chrom_size | Region end (0-based, exclusive) |
| `track` | `getData/track` | — | Any track name from `list/tracks` | Annotation track to retrieve |
| `hubUrl` | Hub endpoints | — | URL to hub.txt | Access a public or private track hub |

## Best Practices

1. **Use 0-based coordinates throughout**: The API is BED-format; always subtract 1 from 1-based browser positions. Mixing conventions causes silent off-by-one errors.

2. **Add delays for batch queries**: There is no enforced rate limit, but UCSC's servers are shared resources. Insert `time.sleep(0.5)` between requests when processing >50 regions.
   ```python
   import time
   for region in regions:
       seq = get_sequence("hg38", region["chrom"], region["start"], region["end"])
       time.sleep(0.5)
   ```

3. **Discover track names before querying**: Track names (e.g., `refGene`, `cpgIslandExt`) are not always obvious. Call `list/tracks` first to find the correct internal name, then query `/getData/track`.

4. **Handle missing track keys in response**: The JSON key holding track records matches the `track` parameter name. Always use `.get(track, [])` to avoid `KeyError` when a track returns no data in a region.

5. **Download chromosome sizes once and cache**: For pipelines that need sizes across many regions, call `list/chromosomes` once and store the result in a dict rather than re-requesting for each query.

## Common Recipes

### Recipe: Fetch Assembly List and Filter by Organism

When to use: Discover available genome assemblies for a specific species.

```python
import requests

r = requests.get("https://api.genome.ucsc.edu/list/ucscGenomes")
r.raise_for_status()
genomes = r.json()["ucscGenomes"]

# All mouse assemblies
mouse = {k: v for k, v in genomes.items()
         if "Mus musculus" in v.get("scientificName", "")}
for name, meta in sorted(mouse.items()):
    print(f"  {name}: {meta.get('description', '')}")
```

### Recipe: Write BED File from Track Query

When to use: Save UCSC track annotations as a BED file for downstream bedtools or IGV analysis.

```python
import requests

BASE = "https://api.genome.ucsc.edu"

r = requests.get(f"{BASE}/getData/track",
                 params={"genome": "hg38", "track": "refGene",
                         "chrom": "chr7", "start": 55_019_017, "end": 55_211_628})
r.raise_for_status()
records = r.json().get("refGene", [])

with open("egfr_refgene.bed", "w") as fh:
    for rec in records:
        fh.write(f"{rec['chrom']}\t{rec['txStart']}\t{rec['txEnd']}\t"
                 f"{rec.get('name2', rec['name'])}\t0\t{rec['strand']}\n")
print(f"Wrote {len(records)} gene records → egfr_refgene.bed")
```

### Recipe: GC Content for a Sequence

When to use: Compute GC content of a promoter or exon after fetching its sequence.

```python
import requests

seq = requests.get(
    "https://api.genome.ucsc.edu/getData/sequence",
    params={"genome": "hg38", "chrom": "chr17",
            "start": 43_044_294, "end": 43_046_294}
).json()["dna"].upper()

gc = (seq.count("G") + seq.count("C")) / len(seq) * 100
print(f"Region length: {len(seq)} bp | GC content: {gc:.1f}%")
```

### Recipe: Quick Coordinate Validation

When to use: Confirm coordinates are within chromosome bounds before submitting a batch.

```python
import requests

sizes = requests.get("https://api.genome.ucsc.edu/list/chromosomes",
                     params={"genome": "hg38"}).json()["chromosomeSizes"]

def validate(chrom, start, end):
    if chrom not in sizes:
        return f"ERROR: {chrom} not in hg38"
    if start < 0 or end > sizes[chrom] or start >= end:
        return f"ERROR: {chrom}:{start}-{end} out of bounds (chrom size={sizes[chrom]})"
    return "OK"

print(validate("chr17", 43_044_294, 43_125_482))  # OK
print(validate("chr17", -1, 100))                  # ERROR
```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `HTTP 400` on sequence endpoint | Coordinates out of chromosome bounds or `start >= end` | Check chromosome size with `list/chromosomes`; swap start/end if reversed |
| Track query returns empty list | No features in the region for that track | Confirm track exists with `list/tracks`; widen the query window |
| `KeyError` on track response | Response key differs from track parameter | Use `.get(track, data.get("data", []))` to handle variant key names |
| `ConnectionError` or timeout | Network issue or server load | Retry with `requests.Session()` and set `timeout=30`; add `time.sleep(1)` |
| Sequence is all lowercase | Softmasked regions (RepeatMasker) | Call `.upper()` on returned sequence if case is irrelevant to your use |
| Conservation track returns no data | Track not available for that assembly | Check `list/tracks` for the assembly; `phyloP100way` is hg38-only; use `phyloP60way` for mm10 |
| Wrong gene retrieved | Multiple transcripts at locus | Filter by `name2` (gene symbol) and select the longest transcript |

## Related Skills

- `ensembl-database` — Ensembl REST API for gene/transcript annotations with stable Ensembl IDs, VEP variant effects, and cross-species homologs; preferred for Ensembl-centric workflows
- `encode-database` — ENCODE portal for regulatory element datasets (ChIP-seq peaks, ATAC-seq) that feed into UCSC track hubs
- `bedtools-genomic-intervals` — Perform intersection, coverage, and arithmetic on BED files downloaded from UCSC
- `regulomedb-database` — RegulomeDB for regulatory variant scoring, which overlaps UCSC regulatory tracks

## References

- [UCSC REST API documentation](https://genome.ucsc.edu/goldenPath/help/api.html) — full endpoint reference, parameters, and response formats
- [UCSC API base URL](https://api.genome.ucsc.edu/) — interactive endpoint explorer
- [Kent WJ et al. (2002) Genome Res 12:996–1006](https://doi.org/10.1101/gr.229102) — original UCSC Genome Browser paper
- [UCSC Track Database](https://genome.ucsc.edu/cgi-bin/hgTables) — Table Browser to explore track names and schemas
