---
name: "biopython-sequence-analysis"
description: "Biopython toolkit for sequence analysis workflows: parse FASTA/FASTQ/GenBank/GFF with SeqIO, query NCBI databases via Entrez (esearch/efetch/elink), run remote and local BLAST with result parsing, perform pairwise and multiple sequence alignment (PairwiseAligner, MUSCLE/ClustalW), and build/visualize phylogenetic trees (Phylo module). Use for gene family studies, phylogenomics, comparative genomics, and programmatic NCBI pipelines. For PCR design, restriction digestion, and cloning workflows use biopython-molecular-biology; for SAM/BAM alignments use pysam."
license: "Biopython License (BSD-like)"
---

# Biopython: Sequence Analysis Toolkit

## Overview

Biopython provides a comprehensive suite of modules for sequence-centric bioinformatics: reading and writing every major biological file format (FASTA, FASTQ, GenBank, GFF), querying NCBI databases programmatically, running BLAST searches and parsing results, aligning sequences pairwise or in multiple-sequence alignments, and building and visualizing phylogenetic trees. This skill focuses on analysis workflows — from NCBI data retrieval through alignment to phylogenetic inference.

For PCR primer design, restriction enzyme digestion, cloning simulation, protein structure analysis (Bio.PDB), and molecular weight/Tm calculations, see **biopython-molecular-biology**.

## When to Use

- Download a gene family from NCBI Nucleotide/Protein, align sequences, and construct a phylogenetic tree
- Parse GenBank or GFF3 annotation files and extract CDS sequences for a set of features
- Run a BLAST search against NCBI `nt` or `nr`, filter significant hits, and fetch their full sequences
- Compute pairwise sequence identities or score alignments with BLOSUM62/PAM250 matrices
- Index a large multi-FASTA or FASTQ file with `SeqIO.index()` for random-access retrieval without loading all sequences into RAM
- Convert between sequence formats (FASTA ↔ GenBank ↔ FASTQ ↔ PHYLIP) in a single call
- Traverse, root, prune, and annotate a Newick or Nexus phylogenetic tree programmatically
- Use **pysam** instead when working with SAM/BAM/CRAM alignment files and mapped reads
- Use **scikit-bio** instead when you need ecological diversity metrics (UniFrac, beta diversity) or ordination methods such as PCoA
- Use **gget** instead for quick gene lookups and one-liner NCBI queries without writing an Entrez pipeline

## Prerequisites

- **Python packages**: `biopython`, `numpy`, `matplotlib`
- **Optional tools**: MUSCLE or ClustalW installed locally (for `Bio.Align.Applications` wrappers)
- **NCBI access**: Set `Entrez.email` before any E-utilities call; obtain a free API key at https://www.ncbi.nlm.nih.gov/account/ for 10 req/s (default is 3 req/s)
- **Local BLAST**: BLAST+ installed separately (`conda install -c bioconda blast`) for offline searches

```bash
pip install biopython numpy matplotlib
conda install -c bioconda blast  # optional, for local BLAST
```

## Quick Start

```python
from Bio import SeqIO, Entrez
from Bio.SeqUtils import gc_fraction

# Fetch a GenBank record and display basic stats
Entrez.email = "your.email@example.com"
handle = Entrez.efetch(db="nucleotide", id="NM_007294", rettype="gb", retmode="text")
record = SeqIO.read(handle, "genbank")
handle.close()

print(f"ID: {record.id}")
print(f"Length: {len(record.seq)} bp")
print(f"GC content: {gc_fraction(record.seq)*100:.1f}%")
print(f"Features: {len(record.features)}")
print(f"First feature: {record.features[0].type} at {record.features[0].location}")
# ID: NM_007294.4
# Length: 7207 bp
# GC content: 47.3%
# Features: 9
```

## Core API

### Module 1: SeqIO — File Parsing and Format Conversion

`Bio.SeqIO` reads and writes every major sequence format (FASTA, FASTQ, GenBank, EMBL, PHYLIP, Nexus). `SeqIO.parse()` returns an iterator of `SeqRecord` objects; `SeqIO.index()` builds an on-disk or in-memory dictionary for large files.

```python
from Bio import SeqIO

# Parse FASTA and FASTQ
fasta_records = list(SeqIO.parse("sequences.fasta", "fasta"))
print(f"FASTA: {len(fasta_records)} sequences")

# FASTQ: access quality scores
for rec in SeqIO.parse("reads.fastq", "fastq"):
    quals = rec.letter_annotations["phred_quality"]
    avg_q = sum(quals) / len(quals)
    print(f"  {rec.id}: {len(rec.seq)} bp, mean Q={avg_q:.1f}")
    break  # show one example

# Parse GenBank with feature access
for rec in SeqIO.parse("chromosome.gb", "genbank"):
    cdss = [f for f in rec.features if f.type == "CDS"]
    print(f"{rec.id}: {len(cdss)} CDS features")
    for cds in cdss[:3]:
        gene = cds.qualifiers.get("gene", ["unknown"])[0]
        print(f"  {gene}: {cds.location}")
```

```python
from Bio import SeqIO

# SeqIO.index() for random access without loading all records
# Useful for large reference FASTA files (genomes, nr database subsets)
idx = SeqIO.index("large_genome.fasta", "fasta")
print(f"Index contains {len(idx)} sequences")

# Retrieve specific sequences by ID in O(1)
target = idx["chr1"]
print(f"chr1: {len(target.seq):,} bp")
region = target.seq[1_000_000:1_001_000]
print(f"Region [1M-1M+1kb]: {region[:60]}...")

# Format conversion: GenBank → FASTA in one call
n = SeqIO.convert("annotation.gb", "genbank", "sequences.fasta", "fasta")
print(f"Converted {n} records to FASTA")
```

### Module 2: Seq and SeqRecord — Sequence Objects and Feature Annotations

`Bio.Seq` represents a biological sequence with in-place operations. `Bio.SeqRecord` wraps a `Seq` with an ID, description, and a dictionary of feature annotations. Features use `FeatureLocation` with strand (+1, -1).

```python
from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord
from Bio.SeqFeature import SeqFeature, FeatureLocation
from Bio.SeqUtils import gc_fraction, MeltingTemp

dna = Seq("ATGAAACCCGGGTTTTAA")
print(f"GC content: {gc_fraction(dna)*100:.1f}%")
print(f"Reverse complement: {dna.reverse_complement()}")
print(f"Transcript: {dna.transcribe()}")
print(f"Translation: {dna.translate()}")
print(f"Translation (to stop): {dna.translate(to_stop=True)}")

# Tm calculation for a short primer
primer = Seq("ATGAAACCCGGG")
tm = MeltingTemp.Tm_Wallace(primer)
print(f"Tm (Wallace): {tm:.1f}°C")
```

```python
from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord
from Bio.SeqFeature import SeqFeature, FeatureLocation

# Build a SeqRecord with annotated features
gene_seq = Seq("ATGAAACCCGGGTTTTAAATCGATCG" * 10)
record = SeqRecord(gene_seq, id="MY_GENE_001", description="synthetic example gene")

# Annotate a CDS feature
cds = SeqFeature(
    FeatureLocation(0, 18, strand=+1),
    type="CDS",
    qualifiers={"gene": ["myGene"], "product": ["hypothetical protein"]}
)
record.features.append(cds)

# Extract and translate the feature
cds_seq = cds.location.extract(record.seq)
protein = cds_seq.translate(to_stop=True)
print(f"CDS: {cds_seq}")
print(f"Protein: {protein}")

# Slice record preserving feature annotations
sub = record[0:60]
print(f"Subrecord: {len(sub.seq)} bp, {len(sub.features)} features")
```

### Module 3: Entrez — Programmatic NCBI Database Access

`Bio.Entrez` wraps the NCBI E-utilities API: `esearch` finds records matching a query, `efetch` retrieves full records, `elink` finds related records across databases, and `esummary` returns document summaries. Always set `Entrez.email` and respect the 3 req/s rate limit (10 req/s with API key).

```python
from Bio import Entrez, SeqIO
import time

Entrez.email = "your.email@example.com"
# Entrez.api_key = "YOUR_API_KEY"  # for 10 req/s

# esearch: find IDs matching a query
handle = Entrez.esearch(db="nucleotide", term="BRCA1[Gene] AND Homo sapiens[Organism] AND mRNA[Filter]", retmax=10)
search_results = Entrez.read(handle)
handle.close()

print(f"Total hits: {search_results['Count']}")
ids = search_results["IdList"]
print(f"Retrieved IDs: {ids}")

# efetch: download full GenBank records
for acc_id in ids[:3]:
    handle = Entrez.efetch(db="nucleotide", id=acc_id, rettype="gb", retmode="text")
    record = SeqIO.read(handle, "genbank")
    handle.close()
    print(f"  {record.id}: {len(record.seq)} bp — {record.description[:60]}")
    time.sleep(0.4)  # stay within rate limit
```

```python
from Bio import Entrez
import time

Entrez.email = "your.email@example.com"

# elink: cross-database links (e.g., PubMed article → related nucleotide sequences)
handle = Entrez.elink(dbfrom="pubmed", db="nucleotide", id="29087512")
link_results = Entrez.read(handle)
handle.close()

linked_ids = []
for linkset in link_results:
    for db_links in linkset.get("LinkSetDb", []):
        if db_links["DbTo"] == "nucleotide":
            linked_ids = [lnk["Id"] for lnk in db_links["Link"]]
            break

print(f"Nucleotide sequences linked to PubMed 29087512: {len(linked_ids)}")
print(f"First IDs: {linked_ids[:5]}")

# esummary: lightweight metadata without downloading full records
if linked_ids:
    handle = Entrez.esummary(db="nucleotide", id=",".join(linked_ids[:5]))
    summaries = Entrez.read(handle)
    handle.close()
    for doc in summaries:
        print(f"  {doc['AccessionVersion']}: {doc['Title'][:70]}")
```

### Module 4: BLAST — Remote and Local Sequence Similarity Search

`Bio.Blast.NCBIWWW.qblast()` submits queries to NCBI BLAST servers and returns XML handles. `Bio.Blast.NCBIXML.parse()` (or `.read()` for single queries) yields `Blast` objects with `alignments` and `hsps`. For large-scale searches, use local BLAST+ via `subprocess`.

```python
from Bio.Blast import NCBIWWW, NCBIXML
from Bio.Seq import Seq

# Remote BLASTP against Swiss-Prot (small, reviewed database)
query = Seq("MTEYKLVVVGAGGVGKSALTIQLIQNHFVDEYDPTIEDSY")
result_handle = NCBIWWW.qblast("blastp", "swissprot", str(query), hitlist_size=10)

# Parse results
blast_record = NCBIXML.read(result_handle)
print(f"Query: {blast_record.query}")
print(f"Database: {blast_record.database}")
print(f"Hits: {len(blast_record.alignments)}")

E_VALUE_THRESH = 1e-5
for alignment in blast_record.alignments[:5]:
    for hsp in alignment.hsps:
        if hsp.expect < E_VALUE_THRESH:
            identity_pct = hsp.identities / hsp.align_length * 100
            print(f"\n  Hit: {alignment.title[:70]}")
            print(f"  E-value: {hsp.expect:.2e}, Identity: {identity_pct:.1f}%, Score: {hsp.score}")
            print(f"  Query:  {hsp.query[:60]}")
            print(f"  Match:  {hsp.match[:60]}")
            print(f"  Sbjct:  {hsp.sbjct[:60]}")
```

```python
import subprocess
from Bio.Blast import NCBIXML
from Bio import SeqIO

# Local BLAST+ via subprocess (faster for large batches)
# Requires: makeblastdb and blastp installed (conda install -c bioconda blast)

# Step 1: Build a local database from a FASTA file
subprocess.run(
    ["makeblastdb", "-in", "ref_proteins.fasta", "-dbtype", "prot", "-out", "ref_db"],
    check=True
)

# Step 2: Run blastp against local database
result = subprocess.run(
    ["blastp", "-query", "query.fasta", "-db", "ref_db",
     "-outfmt", "5",           # XML output for NCBIXML parsing
     "-evalue", "1e-5",
     "-num_threads", "4",
     "-out", "blast_results.xml"],
    check=True
)

# Step 3: Parse XML results
with open("blast_results.xml") as fh:
    for blast_rec in NCBIXML.parse(fh):
        print(f"Query: {blast_rec.query_id}")
        for aln in blast_rec.alignments[:3]:
            hsp = aln.hsps[0]
            print(f"  Hit: {aln.hit_id}, E={hsp.expect:.2e}, Id={hsp.identities}/{hsp.align_length}")
```

### Module 5: Phylo — Tree Parsing, Manipulation, and Visualization

`Bio.Phylo` reads Newick, Nexus, PhyloXML, and NeXML formats. Trees are represented as `Clade` objects with nested children. Key methods: `find_clades()` (generator over nodes), `common_ancestor()`, `distance()`, `root_with_outgroup()`, and `prune()`. Visualization uses matplotlib.

```python
from Bio import Phylo
import io

# Parse a Newick tree from a string
newick = "((Homo_sapiens:0.01, Pan_troglodytes:0.012):0.08, (Mus_musculus:0.15, Rattus_norvegicus:0.14):0.12, Drosophila_melanogaster:0.85);"
tree = Phylo.read(io.StringIO(newick), "newick")

print(f"Number of terminals: {tree.count_terminals()}")
print(f"Total branch length: {tree.total_branch_length():.3f}")
print(f"Terminals: {[t.name for t in tree.get_terminals()]}")

# Root with outgroup and compute distances
tree.root_with_outgroup("Drosophila_melanogaster")
human = tree.find_any("Homo_sapiens")
chimp = tree.find_any("Pan_troglodytes")
mouse = tree.find_any("Mus_musculus")
print(f"\nDistance Human–Chimp: {tree.distance(human, chimp):.4f}")
print(f"Distance Human–Mouse: {tree.distance(human, mouse):.4f}")

# Traverse all internal nodes
for clade in tree.find_clades(order="level"):
    if not clade.is_terminal():
        children = [c.name or "internal" for c in clade.clades]
        print(f"  Internal node → {children}")
```

```python
from Bio import Phylo
import matplotlib.pyplot as plt
import io

newick = "((Homo_sapiens:0.01, Pan_troglodytes:0.012):0.08, (Mus_musculus:0.15, Rattus_norvegicus:0.14):0.12, Drosophila_melanogaster:0.85);"
tree = Phylo.read(io.StringIO(newick), "newick")
tree.root_with_outgroup("Drosophila_melanogaster")
tree.ladderize()   # sort clades by size for a clean layout

# Annotate bootstrap support (if present in node labels)
for clade in tree.find_clades():
    if clade.confidence is not None:
        clade.name = f"{clade.confidence:.0f}"

fig, ax = plt.subplots(figsize=(8, 5))
Phylo.draw(tree, axes=ax, do_show=False, show_confidence=True)
ax.set_title("Primate + Outgroup Phylogeny")
plt.tight_layout()
plt.savefig("phylogeny.png", dpi=150, bbox_inches="tight")
print("Saved phylogeny.png")
```

### Module 6: PairwiseAligner — Pairwise Sequence Alignment

`Bio.Align.PairwiseAligner` replaces the legacy `pairwise2` module (deprecated since Biopython 1.80). It supports local and global alignment, gap open/extend penalties, and any substitution matrix from `Bio.Align.substitution_matrices`.

```python
from Bio.Align import PairwiseAligner, substitution_matrices

# Global protein alignment with BLOSUM62
aligner = PairwiseAligner()
aligner.mode = "global"
aligner.substitution_matrix = substitution_matrices.load("BLOSUM62")
aligner.open_gap_score = -11
aligner.extend_gap_score = -1

seq1 = "MTEYKLVVVGAGGVGKSALTIQLIQNHFVDEYDPTIEDSY"
seq2 = "MTEYKLVVVGAVGVGKSALTIQLIQNHFVDEYDPTIEDSY"  # G12V variant

alignments = aligner.align(seq1, seq2)
best = alignments[0]
print(f"Score: {best.score:.1f}")
print(f"Number of alignments: {aligner.score(seq1, seq2):.0f} (score only, faster)")
print(best)   # formatted alignment string

identity = sum(a == b for a, b in zip(*best) if a != "-") / best.shape[1]
print(f"Identity: {identity*100:.1f}%")
```

```python
from Bio.Align import PairwiseAligner, substitution_matrices

# Local DNA alignment
aligner = PairwiseAligner()
aligner.mode = "local"
aligner.match_score = 2
aligner.mismatch_score = -1
aligner.open_gap_score = -5
aligner.extend_gap_score = -0.5

query = "ACGTACGTACGT"
subject = "TTTTACGTACGTACGTTTTT"
alignments = list(aligner.align(query, subject))
print(f"Local alignments found: {len(alignments)}")
best = alignments[0]
print(f"Score: {best.score}")
print(f"Aligned region in subject: [{best.coordinates[1][0]}:{best.coordinates[1][-1]}]")
print(best)

# Batch pairwise identity matrix
seqs = ["ACGTACGT", "ACGTATGT", "TTGTACGT", "ACGTACGG"]
n = len(seqs)
aligner2 = PairwiseAligner(mode="global", match_score=1, mismatch_score=-1)
print("\nPairwise identity matrix:")
for i in range(n):
    row = []
    for j in range(n):
        score = aligner2.score(seqs[i], seqs[j])
        max_len = max(len(seqs[i]), len(seqs[j]))
        row.append(f"{score/max_len:.2f}")
    print("  " + "  ".join(row))
```

## Key Concepts

### SeqRecord and Feature Coordinates

`SeqRecord` stores sequence metadata and a list of `SeqFeature` objects. Features use zero-based, half-open `FeatureLocation(start, end, strand)` — the same convention as Python slicing. Use `feature.location.extract(record.seq)` to obtain the strand-correct subsequence. Compound locations (e.g., spliced exons) use `CompoundLocation`.

```python
from Bio import SeqIO

# Extract all CDS protein translations from a GenBank record
for rec in SeqIO.parse("gene.gb", "genbank"):
    for feat in rec.features:
        if feat.type == "CDS":
            gene = feat.qualifiers.get("gene", ["?"])[0]
            product = feat.qualifiers.get("product", ["unknown"])[0]
            cds_nt = feat.location.extract(rec.seq)
            protein = cds_nt.translate(to_stop=True)
            print(f"{gene} ({product}): {len(protein)} aa — {protein[:10]}...")
```

### Phylo Clade Objects

A `Clade` is both a node and the subtree rooted at that node. Terminal clades (leaves) have `.name` set; internal clades may have `.confidence` (bootstrap) and `.branch_length`. Use `tree.find_clades()` with `terminal=True/False` to filter. The root is `tree.root` (also a `Clade`). `Phylo.read()` returns a `Tree` wrapper; `tree.root` gives the root `Clade`.

## Common Workflows

### Workflow 1: Gene Family Phylogeny — NCBI Download → MUSCLE Alignment → Tree

**Goal**: Download all BRCA1 orthologs from Vertebrata, align with MUSCLE, and build a neighbor-joining tree.

```python
import subprocess
import time
from Bio import Entrez, SeqIO, Phylo, AlignIO
from Bio.Align import MultipleSeqAlignment
import matplotlib.pyplot as plt

Entrez.email = "your.email@example.com"

# Step 1: Search NCBI Protein for BRCA1 orthologs
handle = Entrez.esearch(
    db="protein",
    term="BRCA1[Gene] AND Vertebrata[Organism] AND RefSeq[Filter]",
    retmax=20
)
results = Entrez.read(handle); handle.close()
ids = results["IdList"]
print(f"Found {results['Count']} sequences, using {len(ids)}")

# Step 2: Fetch sequences in FASTA format
handle = Entrez.efetch(db="protein", id=",".join(ids), rettype="fasta", retmode="text")
with open("brca1_orthologs.fasta", "w") as fh:
    fh.write(handle.read())
handle.close()
print(f"Saved {len(ids)} sequences to brca1_orthologs.fasta")
time.sleep(1)

# Step 3: Align with MUSCLE (must be installed: conda install -c bioconda muscle)
subprocess.run(
    ["muscle", "-align", "brca1_orthologs.fasta", "-output", "brca1_aligned.fasta"],
    check=True
)
alignment = AlignIO.read("brca1_aligned.fasta", "fasta")
print(f"Alignment: {len(alignment)} sequences × {alignment.get_alignment_length()} columns")

# Step 4: Build a neighbor-joining tree using Bio.Phylo + distance matrix
from Bio.Phylo.TreeConstruction import DistanceCalculator, DistanceTreeConstructor

calculator = DistanceCalculator("identity")
dm = calculator.get_distance(alignment)
constructor = DistanceTreeConstructor(calculator, method="nj")
tree = constructor.build_tree(alignment)

# Step 5: Root and save
tree.root_at_midpoint()
tree.ladderize()
Phylo.write(tree, "brca1_nj.nwk", "newick")
print("Saved NJ tree to brca1_nj.nwk")

# Step 6: Visualize
fig, ax = plt.subplots(figsize=(10, 8))
Phylo.draw(tree, axes=ax, do_show=False)
ax.set_title("BRCA1 Ortholog NJ Tree")
plt.tight_layout()
plt.savefig("brca1_tree.png", dpi=150, bbox_inches="tight")
print("Saved brca1_tree.png")
```

### Workflow 2: BLAST Pipeline — FASTA Query → Remote BLAST → Fetch Top Hits

**Goal**: Take a query FASTA, BLAST against NCBI `nr`, filter significant hits, retrieve full GenBank records for the top matches, and write a summary CSV.

```python
import csv
import time
from Bio import SeqIO, Entrez
from Bio.Blast import NCBIWWW, NCBIXML

Entrez.email = "your.email@example.com"

# Step 1: Load query sequence
query_record = SeqIO.read("query.fasta", "fasta")
print(f"Query: {query_record.id} ({len(query_record.seq)} aa)")

# Step 2: Remote BLAST against nr protein database
print("Submitting BLAST job (may take 1-5 minutes)...")
result_handle = NCBIWWW.qblast(
    "blastp", "nr", str(query_record.seq),
    hitlist_size=20,
    expect=1e-5,
    word_size=6,
    matrix_name="BLOSUM62"
)

# Step 3: Parse results and filter
E_THRESH = 1e-5
MIN_IDENTITY = 50.0
top_hits = []

blast_record = NCBIXML.read(result_handle)
for alignment in blast_record.alignments:
    for hsp in alignment.hsps:
        if hsp.expect > E_THRESH:
            continue
        identity_pct = hsp.identities / hsp.align_length * 100
        if identity_pct < MIN_IDENTITY:
            continue
        accession = alignment.accession
        top_hits.append({
            "accession": accession,
            "title": alignment.title[:80],
            "length": alignment.length,
            "score": hsp.score,
            "evalue": hsp.expect,
            "identity_pct": round(identity_pct, 1),
            "coverage": round(hsp.align_length / blast_record.query_length * 100, 1),
        })

print(f"Filtered to {len(top_hits)} significant hits")

# Step 4: Fetch full GenBank records for top 5 hits
accessions = [h["accession"] for h in top_hits[:5]]
time.sleep(1)
handle = Entrez.efetch(db="protein", id=",".join(accessions), rettype="gb", retmode="text")
gb_records = list(SeqIO.parse(handle, "genbank"))
handle.close()
SeqIO.write(gb_records, "top_blast_hits.gb", "genbank")
print(f"Saved {len(gb_records)} full GenBank records to top_blast_hits.gb")

# Step 5: Write CSV summary
with open("blast_summary.csv", "w", newline="") as fh:
    writer = csv.DictWriter(fh, fieldnames=top_hits[0].keys())
    writer.writeheader()
    writer.writerows(top_hits)
print(f"Saved blast_summary.csv ({len(top_hits)} hits)")
```

### Workflow 3: FASTQ Quality Filter and Format Pipeline

**Goal**: Read a FASTQ file, filter reads by mean quality and length, and output a FASTA for downstream alignment.

```python
from Bio import SeqIO
from Bio.SeqUtils import gc_fraction

input_fastq = "raw_reads.fastq"
output_fasta = "filtered_reads.fasta"
MIN_QUAL = 20     # mean Phred quality
MIN_LEN = 100     # minimum read length
MAX_LEN = 300     # maximum read length

def passes_qc(record, min_q=MIN_QUAL, min_l=MIN_LEN, max_l=MAX_LEN):
    quals = record.letter_annotations["phred_quality"]
    mean_q = sum(quals) / len(quals)
    length = len(record.seq)
    return mean_q >= min_q and min_l <= length <= max_l

kept = 0
total = 0
with open(output_fasta, "w") as out_fh:
    for record in SeqIO.parse(input_fastq, "fastq"):
        total += 1
        if passes_qc(record):
            # Convert FASTQ → FASTA (drops quality scores)
            SeqIO.write(record, out_fh, "fasta")
            kept += 1

print(f"Total reads: {total:,}")
print(f"Passed QC: {kept:,} ({kept/total*100:.1f}%)")
print(f"Saved to: {output_fasta}")
```

## Key Parameters

| Parameter | Module / Function | Default | Range / Options | Effect |
|-----------|------------------|---------|-----------------|--------|
| `retmax` | `Entrez.esearch()` | `20` | `1`–`10000` | Max IDs returned per search; use history server for >10000 |
| `hitlist_size` | `NCBIWWW.qblast()` | `50` | `1`–`5000` | Max BLAST alignments returned |
| `expect` | `NCBIWWW.qblast()` | `10.0` | `1e-100`–`1000` | E-value cutoff for BLAST hit reporting |
| `matrix_name` | `NCBIWWW.qblast()` | `"BLOSUM62"` | `"BLOSUM45"`, `"BLOSUM80"`, `"PAM250"` | Substitution matrix; BLOSUM62 for general use |
| `mode` | `PairwiseAligner` | `"global"` | `"global"`, `"local"` | Needleman-Wunsch (global) vs Smith-Waterman (local) |
| `open_gap_score` | `PairwiseAligner` | `-1` | Negative float | Penalty for opening a gap; increase magnitude to penalize more |
| `extend_gap_score` | `PairwiseAligner` | `0` | Negative float | Per-residue gap extension penalty |
| `method` | `DistanceTreeConstructor` | `"nj"` | `"nj"`, `"upgma"` | NJ (unrooted) vs UPGMA (rooted, assumes clock) |
| `format` | `Phylo.read/write()` | required | `"newick"`, `"nexus"`, `"phyloxml"` | Tree file format |
| `rettype` | `Entrez.efetch()` | required | `"fasta"`, `"gb"`, `"xml"` | Record format returned; pair with matching SeqIO format string |

## Best Practices

1. **Always set `Entrez.email`** and respect rate limits. NCBI blocks IPs that exceed 3 req/s without a key. Add `time.sleep(0.4)` between requests in loops, or use `Entrez.api_key` for 10 req/s.
   ```python
   from Bio import Entrez
   import time
   Entrez.email = "your.email@institution.edu"
   Entrez.api_key = "YOUR_API_KEY"    # from https://www.ncbi.nlm.nih.gov/account/
   # In any batch loop: time.sleep(0.11)  # ~9 req/s with key
   ```

2. **Use `SeqIO.index()` for large FASTA files** instead of `list(SeqIO.parse(...))`. Loading all records into a list consumes O(N) memory; `index()` reads only the byte offsets and fetches records on demand.
   ```python
   # Bad for large files: loads everything into RAM
   # records = {r.id: r for r in SeqIO.parse("genome.fasta", "fasta")}

   # Good: on-disk index, O(1) access
   from Bio import SeqIO
   idx = SeqIO.index("genome.fasta", "fasta")
   rec = idx["chr22"]          # fetches only this record
   ```

3. **Use `PairwiseAligner` not the legacy `pairwise2`**. `Bio.pairwise2` is deprecated since Biopython 1.80 and will be removed. `PairwiseAligner` is faster, supports substitution matrices directly, and returns `Alignment` objects with coordinate arrays.

4. **Close Entrez handles immediately** after reading. Handles are HTTP connections; leaving them open risks timeouts and resource exhaustion.
   ```python
   handle = Entrez.efetch(db="nucleotide", id="NM_007294", rettype="gb", retmode="text")
   record = SeqIO.read(handle, "genbank")
   handle.close()    # do not skip this
   ```

5. **Prefer local BLAST for batch searches**. Remote `NCBIWWW.qblast()` is suitable for ad hoc queries but can queue for minutes on NCBI servers. For screening >100 sequences, build a local BLAST+ database with `makeblastdb` and call `blastp`/`blastn` via `subprocess` with `-outfmt 5` (XML) for `NCBIXML` parsing.

6. **Root trees before measuring distances**. `Phylo.distance()` measures the sum of branch lengths along the path between two nodes. On an unrooted tree, the path is still unique, but midpoint-rooting or outgroup-rooting makes biological sense for visualizations and clade assertions.

7. **Strip alignment gaps before building SeqRecord collections**. BLAST and alignment results may include gap characters (`-`). `Seq` operations like `.translate()` will raise errors on gapped sequences; strip with `seq.replace("-", "")` or use `ungap()`.

## Common Recipes

### Recipe: Batch Entrez Fetch with History Server

When to use: Downloading more than 500 records from NCBI — avoids URL length limits and keeps search results server-side.

```python
from Bio import Entrez, SeqIO
import time

Entrez.email = "your.email@example.com"

# Search and store results on NCBI history server
handle = Entrez.esearch(db="nucleotide", term="16S rRNA[Gene] AND Bacteria[Organism]",
                        retmax=500, usehistory="y")
results = Entrez.read(handle); handle.close()
webenv = results["WebEnv"]
query_key = results["QueryKey"]
count = int(results["Count"])
print(f"Total: {count} sequences")

# Fetch in batches of 200
batch_size = 200
all_records = []
for start in range(0, min(count, 1000), batch_size):
    handle = Entrez.efetch(
        db="nucleotide", rettype="fasta", retmode="text",
        retstart=start, retmax=batch_size,
        webenv=webenv, query_key=query_key
    )
    batch = list(SeqIO.parse(handle, "fasta"))
    handle.close()
    all_records.extend(batch)
    print(f"  Fetched {len(all_records)}/{min(count, 1000)}")
    time.sleep(0.5)

SeqIO.write(all_records, "16S_sequences.fasta", "fasta")
print(f"Saved {len(all_records)} sequences")
```

### Recipe: Parse GFF3 with Sequence Features

When to use: Extract gene/CDS sequences from a GFF3 annotation paired with a reference FASTA.

```python
from Bio import SeqIO

# Load genome FASTA into indexed dict
genome = SeqIO.to_dict(SeqIO.parse("genome.fasta", "fasta"))

# Parse GFF3 manually (Biopython does not have a native GFF3 parser;
# use the gffutils package for complex queries, or parse directly for simple cases)
genes = []
with open("annotation.gff3") as fh:
    for line in fh:
        if line.startswith("#") or not line.strip():
            continue
        fields = line.strip().split("\t")
        if len(fields) < 9 or fields[2] != "CDS":
            continue
        chrom, _, feat_type, start, end, _, strand, _, attrs = fields
        start, end = int(start) - 1, int(end)   # GFF3 is 1-based
        if chrom not in genome:
            continue
        seq = genome[chrom].seq[start:end]
        if strand == "-":
            seq = seq.reverse_complement()
        attr_dict = dict(kv.split("=") for kv in attrs.strip().split(";") if "=" in kv)
        gene_id = attr_dict.get("gene_id", attr_dict.get("ID", "unknown"))
        genes.append((gene_id, seq, strand))

print(f"Extracted {len(genes)} CDS features")
for gid, seq, strand in genes[:3]:
    print(f"  {gid} ({strand}): {len(seq)} bp — protein: {seq.translate(to_stop=True)[:8]}...")
```

### Recipe: Compute a Pairwise Identity Matrix from a Multiple Alignment

When to use: Quickly assess sequence diversity within an alignment file (FASTA, PHYLIP, Clustal) and identify outlier sequences.

```python
from Bio import AlignIO
import numpy as np

alignment = AlignIO.read("aligned_sequences.fasta", "fasta")
n = len(alignment)
names = [rec.id for rec in alignment]
length = alignment.get_alignment_length()

# Build identity matrix
identity_matrix = np.zeros((n, n))
for i in range(n):
    for j in range(n):
        if i == j:
            identity_matrix[i, j] = 1.0
            continue
        matches = sum(
            a == b and a != "-"
            for a, b in zip(str(alignment[i].seq), str(alignment[j].seq))
        )
        aligned_cols = sum(a != "-" and b != "-"
                           for a, b in zip(str(alignment[i].seq), str(alignment[j].seq)))
        identity_matrix[i, j] = matches / aligned_cols if aligned_cols else 0.0

print("Pairwise identity matrix:")
print(f"{'':20s} " + "  ".join(f"{n[:8]:>8s}" for n in names))
for i, name in enumerate(names):
    row = "  ".join(f"{identity_matrix[i,j]*100:8.1f}" for j in range(n))
    print(f"{name[:20]:20s} {row}")

# Find most divergent pair
min_id = np.min(identity_matrix[identity_matrix > 0])
idx = np.unravel_index(np.argmin(np.where(identity_matrix > 0, identity_matrix, 1)), identity_matrix.shape)
print(f"\nMost divergent pair: {names[idx[0]]} vs {names[idx[1]]} ({min_id*100:.1f}%)")
```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `urllib.error.HTTPError: 429 Too Many Requests` | Exceeding NCBI rate limit (3 req/s) | Add `time.sleep(0.4)` between calls, or register a free API key at https://www.ncbi.nlm.nih.gov/account/ for 10 req/s |
| `RuntimeError: Too many requests were made without pausing` | NCBI detects rapid-fire requests | Set `Entrez.email` (required), reduce loop frequency, batch IDs into comma-joined strings in a single `efetch` call |
| `Bio.Application.ApplicationError: blastall not found` | Legacy `blastall` replaced by BLAST+ | Replace `NcbiblastpCommandline` with `subprocess.run(["blastp", ...])` and BLAST+ tools |
| `AttributeError: 'PairwiseAligner' object has no attribute 'align'` | Biopython < 1.78 | Upgrade: `pip install --upgrade biopython` (PairwiseAligner requires ≥ 1.72; stable from 1.78) |
| `Bio.pairwise2` deprecation warning | Using the legacy pairwise2 API | Replace with `from Bio.Align import PairwiseAligner` (removed in Biopython 1.84+) |
| `ValueError: Sequence contains letters not in the alphabet` | Non-standard characters (e.g., `N`, ambiguity codes) in sequence before `translate()` | Strip or replace ambiguous bases; use `seq.translate(table=1)` which handles ambiguous codons |
| Empty BLAST results / `StopIteration` from `NCBIXML.read()` | Empty or malformed XML; network timeout; query too short | Check query sequence length (>10 aa recommended); switch from `.read()` to `.parse()` and check `blast_record.alignments` length |
| `Phylo.draw()` hangs or produces blank plot | Missing matplotlib backend | Call `import matplotlib; matplotlib.use("Agg")` before importing Phylo for headless environments |
| `TreeConstruction` distance matrix dimension mismatch | Alignment contains duplicate IDs | Deduplicate SeqRecord IDs before constructing the alignment: `{r.id: r for r in records}.values()` |

## Related Skills

- **biopython-molecular-biology** — restriction digestion, PCR primer design, protein structure analysis (Bio.PDB), molecular weight and Tm calculations; complement to this skill
- **pysam-genomic-files** — SAM/BAM/CRAM alignment file access, pileup, and region queries; use when working with read alignments
- **scikit-bio** — ecological diversity statistics (UniFrac, Bray-Curtis), ordination (PCoA), and microbiome analysis; more specialized than Biopython's phylogenetics for diversity analyses
- **gget-genomic-databases** — one-liner gene lookups, BLAST, and database queries without setting up an Entrez pipeline
- **etetoolkit** — advanced phylogenetic tree visualization, annotation with NCBI taxonomy, and publication-quality tree rendering

## References

- [Biopython Tutorial and Cookbook](https://biopython.org/DIST/docs/tutorial/Tutorial.html) — comprehensive official tutorial (Chapters 2, 5, 6, 7, 9, 11)
- [Biopython API Reference](https://biopython.org/docs/latest/api/) — complete module and class documentation
- [GitHub: biopython/biopython](https://github.com/biopython/biopython) — source, changelog, and issue tracker
- [NCBI E-utilities Documentation](https://www.ncbi.nlm.nih.gov/books/NBK25499/) — Entrez API reference for esearch, efetch, elink, esummary
- [PairwiseAligner Migration Guide](https://biopython.org/docs/latest/api/Bio.Align.html) — replacing the deprecated `Bio.pairwise2` module
