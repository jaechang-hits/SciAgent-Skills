---
name: "biopython-molecular-biology"
description: "Computational molecular biology toolkit for sequence manipulation, file I/O (FASTA/GenBank/PDB), NCBI database access (Entrez), BLAST automation, pairwise/multiple sequence alignment, protein structure analysis (Bio.PDB), and phylogenetic tree construction. Use for batch sequence processing, custom bioinformatics pipelines, format conversion, and programmatic PubMed/GenBank queries. For quick gene lookups use gget; for multi-service REST APIs use bioservices."
license: "Biopython License (BSD-like)"
---

# Biopython: Computational Molecular Biology Toolkit

## Overview

Biopython is the standard open-source Python library for computational molecular biology, providing modular APIs for sequence handling, biological file parsing, NCBI database access, BLAST searches, protein structure analysis, and phylogenetics. It supports Python 3 and requires NumPy.

## When to Use

- Parse and convert biological file formats (FASTA, GenBank, FASTQ, PDB, mmCIF, PHYLIP)
- Fetch sequences or publications from NCBI databases (GenBank, PubMed, Protein) programmatically
- Run and parse BLAST searches (remote NCBI or local BLAST+)
- Perform pairwise or multiple sequence alignments with custom scoring
- Analyze 3D protein structures — distances, angles, DSSP, superimposition
- Build and visualize phylogenetic trees from sequence alignments
- Calculate sequence statistics (GC content, molecular weight, melting temperature)
- Batch-process thousands of sequences with custom filtering logic
- Use `pysam` instead for reading SAM/BAM/CRAM alignment files and working with mapped reads; use `scikit-bio` instead for advanced ecological diversity metrics

## Prerequisites

- **Python packages**: `biopython`, `numpy`, `matplotlib` (for tree visualization)
- **Data requirements**: Sequence files (FASTA, GenBank, FASTQ) or accession IDs for NCBI access
- **Environment**: Python 3.8+; NCBI Entrez requires email registration

```bash
pip install biopython numpy matplotlib
```

## Quick Start

```python
from Bio import SeqIO
from Bio.Seq import Seq
from Bio.SeqUtils import gc_fraction

# Parse a FASTA file and compute basic statistics
records = list(SeqIO.parse("sequences.fasta", "fasta"))
print(f"Sequences loaded: {len(records)}")

seq = records[0].seq
print(f"ID: {records[0].id}")
print(f"Length: {len(seq)} bp")
print(f"GC content: {gc_fraction(seq)*100:.1f}%")
print(f"Reverse complement: {seq.reverse_complement()[:30]}...")
print(f"Protein translation: {seq.translate()[:10]}...")
```

## Core API

### Module 1: Sequence Objects (Bio.Seq)

Create and manipulate DNA, RNA, and protein sequences.

```python
from Bio.Seq import Seq

# Create sequence and perform standard operations
dna = Seq("ATGGCCATTGTAATGGGCCGCTGAAAGGGTGCCCGATAG")
print(f"Length: {len(dna)} bp")
print(f"Complement: {dna.complement()}")
print(f"Reverse complement: {dna.reverse_complement()}")
print(f"Transcription: {dna.transcribe()}")
print(f"Translation: {dna.translate()}")
print(f"Translation (to stop): {dna.translate(to_stop=True)}")
# Length: 39 bp
# Translation: MAIVMGR*KGAR*
# Translation (to stop): MAIVMGR
```

```python
from Bio.Seq import Seq

# Alternative genetic codes (e.g., mitochondrial)
mito_dna = Seq("ATGGCCATTGTAATGGGCCGCTGA")
std_protein = mito_dna.translate(table=1)      # Standard
mito_protein = mito_dna.translate(table=2)     # Vertebrate mitochondrial
print(f"Standard:      {std_protein}")
print(f"Mitochondrial: {mito_protein}")

# Find all start codons
coding_dna = Seq("ATGAAACCCATGGGGTTTAAATAG")
positions = [i for i in range(len(coding_dna) - 2) if coding_dna[i:i+3] == "ATG"]
print(f"ATG positions: {positions}")
# ATG positions: [0, 9]
```

### Module 2: Sequence I/O (Bio.SeqIO)

Read, write, and convert biological file formats.

```python
from Bio import SeqIO

# Parse FASTA file — returns SeqRecord iterator
records = list(SeqIO.parse("sequences.fasta", "fasta"))
print(f"Loaded {len(records)} sequences")
for rec in records[:3]:
    print(f"  {rec.id}: {len(rec.seq)} bp — {rec.description}")

# Parse GenBank — rich annotation access
for rec in SeqIO.parse("genome.gb", "genbank"):
    print(f"{rec.id}: {len(rec.features)} features, {len(rec.seq)} bp")
    for feat in rec.features[:5]:
        print(f"  {feat.type}: {feat.location}")

# Convert between formats
count = SeqIO.convert("input.gb", "genbank", "output.fasta", "fasta")
print(f"Converted {count} records: GenBank → FASTA")
```

```python
from Bio import SeqIO
from Bio.SeqRecord import SeqRecord
from Bio.Seq import Seq

# Write sequences to file
records = [
    SeqRecord(Seq("ATCGATCG"), id="seq1", description="test sequence 1"),
    SeqRecord(Seq("GCTAGCTA"), id="seq2", description="test sequence 2"),
]
count = SeqIO.write(records, "output.fasta", "fasta")
print(f"Wrote {count} records to output.fasta")

# Filter sequences by length (streaming — memory efficient)
long_seqs = (rec for rec in SeqIO.parse("large_file.fasta", "fasta") if len(rec.seq) >= 200)
count = SeqIO.write(long_seqs, "filtered.fasta", "fasta")
print(f"Kept {count} sequences >= 200 bp")

# Index large FASTA for random access
idx = SeqIO.index("large_file.fasta", "fasta")
print(f"Indexed {len(idx)} sequences")
rec = idx["target_sequence_id"]
print(f"Retrieved: {rec.id}, {len(rec.seq)} bp")
```

### Module 3: NCBI Database Access (Bio.Entrez)

Programmatic search and download from NCBI databases.

```python
from Bio import Entrez, SeqIO

Entrez.email = "your.email@example.com"
# Entrez.api_key = "your_key"  # Optional: 10 req/s instead of 3 req/s

# Search PubMed
handle = Entrez.esearch(db="pubmed", term="CRISPR Cas9 2024", retmax=5)
results = Entrez.read(handle)
handle.close()
print(f"Found {results['Count']} articles, retrieved {len(results['IdList'])} IDs")
print(f"IDs: {results['IdList']}")

# Fetch GenBank record by accession
handle = Entrez.efetch(db="nucleotide", id="EU490707", rettype="gb", retmode="text")
record = SeqIO.read(handle, "genbank")
handle.close()
print(f"{record.id}: {record.description}")
print(f"Length: {len(record.seq)} bp, Features: {len(record.features)}")
```

```python
from Bio import Entrez
import time

Entrez.email = "your.email@example.com"

# Batch download with rate limiting
handle = Entrez.esearch(db="protein", term="insulin[Protein Name] AND human[Organism]", retmax=20)
results = Entrez.read(handle)
handle.close()

# Fetch summaries in batch
ids = results["IdList"][:10]
handle = Entrez.esummary(db="protein", id=",".join(ids))
summaries = Entrez.read(handle)
handle.close()

for doc in summaries:
    print(f"  {doc['AccessionVersion']}: {doc['Title'][:60]}...")
print(f"\nFetched {len(summaries)} protein summaries")
```

### Module 4: BLAST Operations (Bio.Blast)

Run and parse BLAST searches against NCBI or local databases.

```python
from Bio.Blast import NCBIWWW, NCBIXML

# Remote BLAST search (nucleotide)
query_seq = "ATCGATCGATCGATCGATCGATCGATCGATCG"
result_handle = NCBIWWW.qblast("blastn", "nt", query_seq, hitlist_size=5)
blast_record = NCBIXML.read(result_handle)
result_handle.close()

print(f"Query: {blast_record.query[:50]}")
print(f"Database: {blast_record.database}")
print(f"Hits: {len(blast_record.alignments)}")

for aln in blast_record.alignments[:3]:
    hsp = aln.hsps[0]
    print(f"\n  {aln.title[:60]}...")
    print(f"  E-value: {hsp.expect:.2e}, Identity: {hsp.identities}/{hsp.align_length}")
    print(f"  Score: {hsp.score}, Bits: {hsp.bits:.1f}")
```

```python
from Bio.Blast.Applications import NcbiblastpCommandline
from Bio.Blast import NCBIXML

# Local BLAST (requires BLAST+ installed)
blastp_cline = NcbiblastpCommandline(
    query="query.fasta",
    db="swissprot",
    evalue=1e-5,
    outfmt=5,  # XML output
    out="blast_results.xml",
    num_threads=4,
)
print(f"Command: {blastp_cline}")
# stdout, stderr = blastp_cline()  # Execute

# Parse local BLAST XML results
with open("blast_results.xml") as f:
    for record in NCBIXML.parse(f):
        print(f"Query: {record.query}")
        for aln in record.alignments[:3]:
            print(f"  Hit: {aln.hit_def[:50]}, E={aln.hsps[0].expect:.2e}")
```

### Module 5: Pairwise Alignment (Bio.Align)

Global and local pairwise sequence alignment with customizable scoring.

```python
from Bio import Align

# Global alignment
aligner = Align.PairwiseAligner()
aligner.mode = "global"
aligner.match_score = 2
aligner.mismatch_score = -1
aligner.open_gap_score = -5
aligner.extend_gap_score = -0.5

alignments = aligner.align("ACCGGTAACG", "ACGGTAAC")
print(f"Score: {alignments.score}")
print(f"Number of alignments: {len(alignments)}")
print(f"Best alignment:\n{alignments[0]}")
```

```python
from Bio import Align
from Bio.Align import substitution_matrices

# Protein alignment with BLOSUM62
aligner = Align.PairwiseAligner()
aligner.mode = "local"
aligner.substitution_matrix = substitution_matrices.load("BLOSUM62")
aligner.open_gap_score = -10
aligner.extend_gap_score = -0.5

seq1 = "MVLSPADKTNVKAAWGKVGAHAGEYGAEALERMFLSFPTTKTYFPHFDLSH"
seq2 = "MVHLTPEEKSAVTALWGKVNVDEVGGEALGRLLVVYPWTQRFFESFGDLST"
alignments = aligner.align(seq1, seq2)
print(f"Score: {alignments.score}")
print(f"Best alignment:\n{alignments[0]}")
```

### Module 6: Protein Structure Analysis (Bio.PDB)

Parse PDB/mmCIF files and analyze 3D protein structures.

```python
from Bio.PDB import PDBParser, PPBuilder

# Parse PDB structure
parser = PDBParser(QUIET=True)
structure = parser.get_structure("1CRN", "1crn.pdb")

# Navigate SMCRA hierarchy: Structure > Model > Chain > Residue > Atom
model = structure[0]
for chain in model:
    residues = list(chain.get_residues())
    print(f"Chain {chain.id}: {len(residues)} residues")

# Extract sequence from structure
ppb = PPBuilder()
for pp in ppb.build_peptides(structure):
    print(f"Peptide: {pp.get_sequence()[:50]}... ({len(pp.get_sequence())} aa)")

# Calculate CA-CA distance
chain_a = model["A"]
ca1 = chain_a[10]["CA"]
ca2 = chain_a[20]["CA"]
distance = ca1 - ca2
print(f"CA distance (res 10-20): {distance:.2f} Angstrom")
```

```python
from Bio.PDB import PDBParser, Superimposer
import numpy as np

# Structure superimposition (RMSD calculation)
parser = PDBParser(QUIET=True)
struct1 = parser.get_structure("s1", "structure1.pdb")
struct2 = parser.get_structure("s2", "structure2.pdb")

# Get CA atoms for alignment
atoms1 = [res["CA"] for res in struct1[0]["A"].get_residues() if "CA" in res]
atoms2 = [res["CA"] for res in struct2[0]["A"].get_residues() if "CA" in res]

# Superimpose (requires same number of atoms)
n = min(len(atoms1), len(atoms2))
sup = Superimposer()
sup.set_atoms(atoms1[:n], atoms2[:n])
sup.apply(struct2.get_atoms())
print(f"RMSD: {sup.rms:.3f} Angstrom over {n} CA atoms")
```

### Module 7: Phylogenetics (Bio.Phylo)

Build, manipulate, and visualize phylogenetic trees.

```python
from Bio import Phylo, AlignIO
from Bio.Phylo.TreeConstruction import DistanceCalculator, DistanceTreeConstructor
import io

# Build tree from multiple sequence alignment
alignment = AlignIO.read("aligned_sequences.fasta", "fasta")
print(f"Alignment: {len(alignment)} sequences, {alignment.get_alignment_length()} positions")

# Calculate distance matrix and build NJ tree
calculator = DistanceCalculator("identity")
dm = calculator.get_distance(alignment)
print(f"Distance matrix:\n{dm}")

constructor = DistanceTreeConstructor()
nj_tree = constructor.nj(dm)
upgma_tree = constructor.upgma(dm)

# Visualize
Phylo.draw_ascii(nj_tree)

# Save tree
Phylo.write(nj_tree, "tree.nwk", "newick")
print("Saved tree.nwk")
```

### Module 8: Sequence Utilities (Bio.SeqUtils)

Compute sequence statistics and physicochemical properties.

```python
from Bio.Seq import Seq
from Bio.SeqUtils import gc_fraction, molecular_weight, MeltingTemp

dna = Seq("ATCGATCGATCGATCGATCG")
print(f"GC content: {gc_fraction(dna):.2%}")
print(f"Molecular weight: {molecular_weight(dna, seq_type='DNA'):.2f} Da")
print(f"Melting temp (basic): {MeltingTemp.Tm_Wallace(dna):.1f} C")
print(f"Melting temp (NN):    {MeltingTemp.Tm_NN(dna):.1f} C")

# Protein analysis
from Bio.SeqUtils.ProtParam import ProteinAnalysis
protein = ProteinAnalysis("MVLSPADKTNVKAAWGKVGAHAGEYGAEALERMFLSFPTTK")
print(f"\nProtein MW: {protein.molecular_weight():.2f} Da")
print(f"Isoelectric point: {protein.isoelectric_point():.2f}")
print(f"Aromaticity: {protein.aromaticity():.4f}")
print(f"Instability index: {protein.instability_index():.2f}")
print(f"GRAVY: {protein.gravy():.4f}")
aa_pct = protein.get_amino_acids_percent()
print(f"Top 3 amino acids: {sorted(aa_pct.items(), key=lambda x: -x[1])[:3]}")
```

## Common Workflows

### Workflow 1: Gene Sequence Retrieval and Analysis Pipeline

**Goal**: Fetch a gene from NCBI, analyze its properties, translate to protein, and compute statistics.

```python
from Bio import Entrez, SeqIO
from Bio.Seq import Seq
from Bio.SeqUtils import gc_fraction
from Bio.SeqUtils.ProtParam import ProteinAnalysis

Entrez.email = "your.email@example.com"

# Step 1: Fetch gene from GenBank
handle = Entrez.efetch(db="nucleotide", id="NM_007294.4", rettype="gb", retmode="text")
record = SeqIO.read(handle, "genbank")
handle.close()
print(f"Gene: {record.description}")
print(f"Length: {len(record.seq)} bp")

# Step 2: Extract CDS
cds_features = [f for f in record.features if f.type == "CDS"]
if cds_features:
    cds = cds_features[0]
    cds_seq = cds.location.extract(record).seq
    print(f"CDS: {len(cds_seq)} bp, GC: {gc_fraction(cds_seq):.2%}")

    # Step 3: Translate
    protein_seq = cds_seq.translate(to_stop=True)
    print(f"Protein: {len(protein_seq)} aa")
    print(f"First 30 aa: {protein_seq[:30]}...")

    # Step 4: Protein properties
    analysis = ProteinAnalysis(str(protein_seq))
    print(f"MW: {analysis.molecular_weight():.0f} Da")
    print(f"pI: {analysis.isoelectric_point():.2f}")
    print(f"Instability: {analysis.instability_index():.1f}")
    print(f"GRAVY: {analysis.gravy():.3f}")
```

### Workflow 2: Comparative Sequence Analysis with BLAST and Phylogeny

**Goal**: BLAST a protein sequence, fetch homologs, align, and build a phylogenetic tree.

```python
from Bio.Blast import NCBIWWW, NCBIXML
from Bio import Entrez, SeqIO, AlignIO, Phylo
from Bio.Phylo.TreeConstruction import DistanceCalculator, DistanceTreeConstructor
from Bio.Align.Applications import MuscleCommandline
import time

Entrez.email = "your.email@example.com"

# Step 1: BLAST search
query = "MVLSPADKTNVKAAWGKVGAHAGEYGAEALERMFLSFPTTKTYFPHFDLSH"
result_handle = NCBIWWW.qblast("blastp", "swissprot", query, hitlist_size=10)
blast_record = NCBIXML.read(result_handle)
print(f"BLAST hits: {len(blast_record.alignments)}")

# Step 2: Collect homolog accessions
accessions = []
for aln in blast_record.alignments[:8]:
    acc = aln.accession
    accessions.append(acc)
    print(f"  {acc}: E={aln.hsps[0].expect:.2e}, {aln.hit_def[:50]}...")

# Step 3: Fetch sequences and save for alignment
handle = Entrez.efetch(db="protein", id=",".join(accessions), rettype="fasta", retmode="text")
records = list(SeqIO.parse(handle, "fasta"))
handle.close()
SeqIO.write(records, "homologs.fasta", "fasta")
print(f"Saved {len(records)} homolog sequences")

# Step 4: Align (requires MUSCLE installed)
# muscle_cline = MuscleCommandline(input="homologs.fasta", out="aligned.fasta")
# muscle_cline()

# Step 5: Build phylogenetic tree from alignment
alignment = AlignIO.read("aligned.fasta", "fasta")
calculator = DistanceCalculator("blosum62")
dm = calculator.get_distance(alignment)
tree = DistanceTreeConstructor().nj(dm)
Phylo.draw_ascii(tree)
Phylo.write(tree, "homologs.nwk", "newick")
print("Saved phylogenetic tree to homologs.nwk")
```

### Workflow 3: Batch Sequence Processing and Quality Filtering

**Goal**: Process a large FASTQ/FASTA dataset — filter by quality/length, compute statistics, and export.

```python
from Bio import SeqIO
from Bio.SeqUtils import gc_fraction
import pandas as pd

# Step 1: Stream through large file and collect stats
stats = []
passed = []

for rec in SeqIO.parse("reads.fastq", "fastq"):
    seq_len = len(rec.seq)
    gc = gc_fraction(rec.seq)
    avg_qual = sum(rec.letter_annotations["phred_quality"]) / seq_len

    stats.append({"id": rec.id, "length": seq_len, "gc": gc, "avg_qual": avg_qual})

    # Filter: length >= 100 and avg quality >= 20
    if seq_len >= 100 and avg_qual >= 20:
        passed.append(rec)

# Step 2: Summary statistics
df = pd.DataFrame(stats)
print(f"Total reads: {len(df)}")
print(f"Passed QC:   {len(passed)} ({len(passed)/len(df)*100:.1f}%)")
print(f"\nLength:  mean={df['length'].mean():.0f}, median={df['length'].median():.0f}")
print(f"GC:      mean={df['gc'].mean():.2%}, std={df['gc'].std():.2%}")
print(f"Quality: mean={df['avg_qual'].mean():.1f}, min={df['avg_qual'].min():.1f}")

# Step 3: Export filtered reads
count = SeqIO.write(passed, "filtered_reads.fastq", "fastq")
print(f"\nExported {count} filtered reads to filtered_reads.fastq")

# Step 4: Save statistics
df.to_csv("read_statistics.csv", index=False)
print(f"Saved statistics to read_statistics.csv")
```

## Key Parameters

| Parameter | Module | Default | Range / Options | Effect |
|-----------|--------|---------|-----------------|--------|
| `Seq.translate(table=)` | Bio.Seq | `1` (Standard) | `1`-`33` | NCBI genetic code table for translation |
| `Seq.translate(to_stop=)` | Bio.Seq | `False` | `True`, `False` | Stop at first stop codon vs translate entire sequence |
| `SeqIO.parse(format=)` | Bio.SeqIO | — | `"fasta"`, `"genbank"`, `"fastq"`, `"phylip"` | File format for parsing |
| `Entrez.email` | Bio.Entrez | (required) | Valid email | NCBI requires email for tracking; set before any Entrez call |
| `Entrez.api_key` | Bio.Entrez | `None` | NCBI API key string | Increases rate limit from 3 to 10 requests/second |
| `PairwiseAligner.mode` | Bio.Align | `"global"` | `"global"`, `"local"` | Needleman-Wunsch vs Smith-Waterman algorithm |
| `PairwiseAligner.open_gap_score` | Bio.Align | `-1` | `-20` to `0` | Penalty for opening a gap; more negative = fewer gaps |
| `PairwiseAligner.substitution_matrix` | Bio.Align | None | `"BLOSUM62"`, `"BLOSUM45"`, `"PAM250"` | Scoring matrix for protein alignment |
| `PDBParser(QUIET=)` | Bio.PDB | `False` | `True`, `False` | Suppress parser warnings for non-standard PDB files |
| `DistanceCalculator(model=)` | Bio.Phylo | `"identity"` | `"identity"`, `"blosum62"` | Distance model for tree construction |

## Common Recipes

### Recipe: Restriction Enzyme Analysis

When to use: Find restriction sites in a DNA sequence for cloning design.

```python
from Bio.Seq import Seq
from Bio.Restriction import EcoRI, BamHI, HindIII, RestrictionBatch, Analysis

seq = Seq("GAATTCAAAGGATCCTTTTAAGCTTGGGAATTC")

# Single enzyme
print(f"EcoRI cuts at: {EcoRI.search(seq)}")
print(f"BamHI cuts at: {BamHI.search(seq)}")

# Batch analysis
batch = RestrictionBatch([EcoRI, BamHI, HindIII])
analysis = Analysis(batch, seq)
result = analysis.full()
for enzyme, sites in result.items():
    if sites:
        print(f"{enzyme}: cuts at positions {sites}")
```

### Recipe: Motif Discovery and Position Weight Matrix

When to use: Analyze transcription factor binding sites or consensus patterns.

```python
from Bio import motifs
from Bio.Seq import Seq

# Create motif from observed binding sites
instances = [
    Seq("TACGAT"),
    Seq("TAGCAT"),
    Seq("TACGGT"),
    Seq("TAGCAT"),
    Seq("TACGAT"),
]
m = motifs.create(instances)
print(f"Consensus: {m.consensus}")
print(f"Degenerate: {m.degenerate_consensus}")
print(f"\nPosition Weight Matrix:")
print(m.counts)

# Score a new sequence against the motif
pwm = m.counts.normalize(pseudocounts=0.5)
pssm = pwm.log_odds()
test_seq = Seq("AATACGATCCC")
for pos, score in pssm.search(test_seq, threshold=0.0):
    print(f"  Position {pos}: score={score:.2f}")
```

### Recipe: GenomeDiagram — Visualize Genomic Features

When to use: Create a circular or linear genome map from a GenBank file.

```python
from Bio import SeqIO
from Bio.Graphics import GenomeDiagram
from reportlab.lib import colors
from reportlab.lib.units import cm

# Load annotated genome
record = SeqIO.read("plasmid.gb", "genbank")

# Create diagram
diagram = GenomeDiagram.Diagram(record.name)
track = diagram.new_track(1, name="Annotated Features", greytrack=True)
feature_set = track.new_set()

# Color features by type
color_map = {"CDS": colors.blue, "gene": colors.green, "promoter": colors.red}
for feature in record.features:
    if feature.type in color_map:
        feature_set.add_feature(feature, color=color_map[feature.type], label=True, label_size=8)

# Draw circular map
diagram.draw(format="circular", circular=True, pagesize=(20*cm, 20*cm), start=0, end=len(record))
diagram.write("genome_map.pdf", "PDF")
print(f"Saved genome_map.pdf ({len(record.features)} features)")
```

### Recipe: Batch PubMed Literature Search

When to use: Programmatically search and download publication metadata.

```python
from Bio import Entrez
import time

Entrez.email = "your.email@example.com"

# Search PubMed with complex query
query = "(CRISPR[Title]) AND (2024[Date - Publication]) AND (review[Publication Type])"
handle = Entrez.esearch(db="pubmed", term=query, retmax=100)
results = Entrez.read(handle)
handle.close()
print(f"Found {results['Count']} articles")

# Fetch abstracts in batches
ids = results["IdList"]
batch_size = 20
articles = []
for i in range(0, len(ids), batch_size):
    batch = ids[i:i+batch_size]
    handle = Entrez.efetch(db="pubmed", id=",".join(batch), rettype="xml")
    records = Entrez.read(handle)
    handle.close()
    for article in records["PubmedArticle"]:
        info = article["MedlineCitation"]["Article"]
        title = info.get("ArticleTitle", "N/A")
        abstract = info.get("Abstract", {}).get("AbstractText", ["N/A"])[0]
        articles.append({"title": title, "abstract": str(abstract)[:200]})
    time.sleep(0.4)  # Rate limiting

for a in articles[:5]:
    print(f"  {a['title'][:70]}...")
print(f"\nRetrieved {len(articles)} articles")
```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `HTTPError 400` from Entrez | Invalid accession/ID or malformed query | Validate accessions; check query syntax with NCBI web interface first |
| `HTTPError 429` (Too Many Requests) | Exceeding NCBI rate limit (3 req/s) | Set `Entrez.api_key` for 10 req/s; add `time.sleep(0.4)` between calls |
| `ValueError: No records found` in `SeqIO.read()` | Empty file or wrong format string | Use `SeqIO.parse()` to check if file has records; verify format matches actual content |
| `Bio.PDB.PDBExceptions.PDBConstructionWarning` | Non-standard atoms or occupancy issues | Use `PDBParser(QUIET=True)` or fix PDB with `pdb-tools`; check for alternate conformations |
| BLAST search times out | Large query or busy NCBI servers | Use local BLAST+ for large-scale searches; set `NCBIWWW.qblast(hitlist_size=N)` to limit results |
| `Alignment has sequences of different lengths` | Unaligned sequences passed to AlignIO | Align sequences first with MUSCLE/Clustal before loading as alignment |
| `SeqIO.index()` raises `ValueError` | Duplicate IDs in FASTA file | Deduplicate IDs with `SeqIO.to_dict()` or pre-process with `awk` |
| `ImportError: No module named Bio` | Biopython not installed in active environment | `pip install biopython`; verify with `python -c "import Bio; print(Bio.__version__)"` |
| `translate()` gives unexpected `*` | Stop codons in middle of sequence | Check reading frame; use `Seq.translate(table=N)` with correct genetic code |
| GenomeDiagram blank output | No features matched filter criteria | Check `feature.type` values in your GenBank file; print types to debug |

## References

- [Biopython Tutorial and Cookbook](https://biopython.org/docs/latest/Tutorial/) — Official comprehensive tutorial
- [Biopython API Documentation](https://biopython.org/docs/latest/api/) — Complete API reference
- [Cock, P.J.A. et al. (2009) Bioinformatics 25:1422-1423](https://doi.org/10.1093/bioinformatics/btp163) — Original Biopython paper
- [NCBI Entrez Programming Utilities](https://www.ncbi.nlm.nih.gov/books/NBK25497/) — E-utilities documentation for programmatic NCBI access
- [Biopython GitHub Repository](https://github.com/biopython/biopython) — Source code, issues, and release notes
