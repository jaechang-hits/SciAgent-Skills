---
name: "sequence-analysis"
description: "DNA/protein sequence tasks with Biopython and NCBI: fetch a gene CDS or plasmid by name/accession (E-utilities), identify a sequence by remote BLAST, restriction digest fragment counts (linear vs circular), GC content and Tm, ORFs on both strands, primer checks and binding sites, amino acid substitutions between sequences, Kozak context scoring, and Gibson / restriction cloning primers with vector arms taken from the real plasmid. For Biopython API depth use biopython-sequence-analysis or biopython-molecular-biology; ClinVar lookup of found substitutions is in database-query."
license: "CC-BY-4.0"
---

# Sequence Analysis

## Overview

Quick, checkable molecular biology computations. Fetch real sequences from
NCBI rather than typing them from memory. Output: sequences fetched by name or
accession, BLAST identifications, digest fragment sizes, sequence properties,
ORFs, primer checks and binding sites, substitutions, Kozak scores and
cloning primers built from the real vector.

## When to Use

- Fetching a gene's coding sequence or a plasmid by name or accession
- Identifying an unknown protein or DNA sequence by BLAST
- Predicting restriction fragment sizes on a linear or circular molecule
- Checking primers (Tm, GC, 3' clamp) and where they bind on a template
- Listing amino acid substitutions between a reference and variants
- Designing Gibson or restriction cloning primers against a real vector
- Use `biopython-sequence-analysis` or `biopython-molecular-biology` instead for deeper Biopython API coverage
- For primer design from scratch, use primer3-py instead of the checks here

## Prerequisites

- **Network**: NCBI E-utilities and BLAST. Set `Entrez.email`; without an API key
  stay under 3 requests/s. Remote BLAST takes 30 s to several minutes.
- **Python packages**: `biopython` (examples use Biopython >= 1.80)

```bash
pip install biopython
```

## Quick Start

```python
from Bio import Entrez, Restriction, SeqIO
from Bio.SeqUtils import gc_fraction

Entrez.email = "you@example.org"
puc19 = SeqIO.read(Entrez.efetch(db="nuccore", id="M77789", rettype="fasta", retmode="text"), "fasta")
print(len(puc19), f"GC {100 * gc_fraction(puc19.seq):.1f}%")
print(Restriction.RestrictionBatch(["EcoRI", "HindIII"]).search(puc19.seq, linear=False))
```

## Core API

### Module 1: Fetch Gene and Plasmid Sequences

The gene record gives exact genomic coordinates; fetch that span on the
right strand:

```python
from Bio import Entrez, SeqIO

Entrez.email = "you@example.org"   # required by NCBI

def fetch_gene(symbol, organism="Escherichia coli str. K-12 substr. MG1655"):
    ids = Entrez.read(Entrez.esearch(db="gene", term=f"{symbol}[Gene Name] AND \"{organism}\"[Organism]"))["IdList"]
    if not ids:
        raise ValueError(f"{symbol} not found in {organism}")
    doc = Entrez.read(Entrez.esummary(db="gene", id=ids[0]))["DocumentSummarySet"]["DocumentSummary"][0]
    loc = doc["GenomicInfo"][0]                       # 0-based, inclusive
    start, stop = int(loc["ChrStart"]), int(loc["ChrStop"])
    strand = 1 if start <= stop else 2                # stop < start means minus strand
    h = Entrez.efetch(db="nuccore", id=loc["ChrAccVer"], rettype="fasta", strand=strand,
                      seq_start=min(start, stop) + 1, seq_stop=max(start, stop) + 1)
    return SeqIO.read(h, "fasta")

rec = fetch_gene("rsxD")
seq = str(rec.seq)
print(rec.id, len(seq), seq[:30], "...", seq[-30:])
```

This is the gene span; for multi-exon eukaryotic genes it includes introns -
fetch the RefSeq mRNA/CDS instead (`efetch(db="nuccore", id="NM_...",
rettype="fasta_cds_na")`).

Plasmids by accession (pUC19: `M77789`, 2,686 bp; check the orientation of
the MCS in the record you use):

```python
def fetch_accession(acc, fmt="fasta"):
    return SeqIO.read(Entrez.efetch(db="nuccore", id=acc, rettype=fmt, retmode="text"), fmt)

from Bio.Seq import Seq

puc19 = str(fetch_accession("M77789").seq).upper()
mcs = "GAATTCGAGCTCGGTACCCGGGGATCCTCTAGAGTCGACCTGCAGGCATGCAAGCTT"   # EcoRI ... HindIII
print(len(puc19), "MCS forward at", puc19.find(mcs),
      "| reverse at", puc19.find(str(Seq(mcs).reverse_complement())))   # M77789: reverse, at 232
```

For an unknown accession, search: `Entrez.esearch(db="nuccore",
term="pET-28a[Title] AND complete sequence[Title]")`.

### Module 2: Identify a Sequence (BLAST)

```python
from Bio.Blast import NCBIWWW, NCBIXML

def blast_top_hits(sequence, program="blastp", database="swissprot", n=5):
    """blastp/swissprot for proteins (curated, fast); blastn/nt or core_nt for DNA."""
    handle = NCBIWWW.qblast(program, database, sequence, hitlist_size=n, expect=1e-5)
    record = NCBIXML.read(handle)
    for aln in record.alignments[:n]:
        hsp = aln.hsps[0]
        print(f"{aln.accession:12s} {100 * hsp.identities / hsp.align_length:5.1f}% id  "
              f"cov {hsp.align_length}/{record.query_length}  E={hsp.expect:.1e}  {aln.hit_def[:70]}")
    return record

QUERY = "<protein or DNA sequence>"
rec = blast_top_hits(QUERY)               # DNA: blast_top_hits(QUERY, "blastn", "nt")
```

`hit_def` carries the protein name and organism; get the gene symbol from the
UniProt entry of the top accession (`uniprot-protein-database`). Near-100%
identity over the full query length identifies the protein; lower identity
means a homolog, so report it as such.

### Module 3: Restriction Digest

`search()` returns 1-based positions of the first base after each top-strand
cut:

```python
from Bio import Restriction
from Bio.Seq import Seq

def digest(sequence, enzymes, circular=False):
    s = Seq(sequence.upper())
    rb = Restriction.RestrictionBatch(enzymes)
    hits = rb.search(s, linear=not circular)
    cuts = sorted({p for ps in hits.values() for p in ps})
    for enz, ps in hits.items():
        print(f"{enz} ({enz.site}): {ps}")
    if not cuts:
        return [len(s)]
    if circular:
        return sorted([b - a for a, b in zip(cuts, cuts[1:])] + [len(s) - cuts[-1] + cuts[0]], reverse=True)
    edges = [1, *cuts, len(s) + 1]
    return sorted([b - a for a, b in zip(edges, edges[1:])], reverse=True)

frags = digest(puc19, ["EcoRI", "HindIII"], circular=True)
print(f"{len(frags)} fragments: {frags}")
```

Linear DNA: fragments = cuts + 1; circular: fragments = cuts (one cut gives
one linear molecule). MboI is blocked by Dam methylation on DNA grown in dam+
E. coli; Sau3AI and DpnII cut the same site.

### Module 4: Basic Properties

```python
from Bio.SeqUtils import MeltingTemp as mt
from Bio.SeqUtils import gc_fraction

s = Seq("ATGCGATCGATCGATCGTAG")
print(f"GC {100 * gc_fraction(s):.1f}%")
print(f"Tm nearest-neighbour {mt.Tm_NN(s, Na=50, dnac1=250):.1f} C   Wallace {mt.Tm_Wallace(s):.1f} C")
print("revcomp", s.reverse_complement())
print("protein", s.translate(to_stop=True), "| bacterial table:", s.translate(table=11))
```

Use `Tm_NN` for primers; Wallace (2AT + 4GC) is only a rough check for
< 14 nt.

### Module 5: ORFs on Both Strands

```python
def find_orfs(sequence, min_aa=100, table=1):
    s = Seq(sequence.upper())
    n = len(s)
    orfs = []
    for strand, nuc in [(1, s), (-1, s.reverse_complement())]:
        for frame in range(3):
            used = frame + (n - frame) // 3 * 3
            prot = str(nuc[frame:used].translate(table))
            aa = 0
            for chunk in prot.split("*"):
                m = chunk.find("M")
                if m >= 0 and len(chunk) - m >= min_aa:
                    a = frame + 3 * (aa + m)
                    b = min(frame + 3 * (aa + len(chunk)) + 3, used)   # include stop codon
                    start, end = (a, b) if strand == 1 else (n - b, n - a)
                    orfs.append({"strand": strand, "start": start, "end": end,
                                 "aa": len(chunk) - m, "protein": chunk[m:]})
                aa += len(chunk) + 1
    return sorted(orfs, key=lambda o: o["aa"], reverse=True)

for o in find_orfs(puc19, min_aa=100)[:5]:
    print(o["strand"], o["start"], o["end"], o["aa"], o["protein"][:20])
```

Coordinates are 0-based half-open on the input sequence. An ORF running off
the end without a stop is still reported; check `protein` length against
`end`.

### Module 6: Primer Properties and Binding Sites

```python
def check_primer(p):
    s = Seq(p.upper())
    gc, tm = 100 * gc_fraction(s), mt.Tm_NN(s, Na=50, dnac1=250)
    issues = [msg for bad, msg in [
        (not 18 <= len(s) <= 30, f"length {len(s)}"), (not 40 <= gc <= 60, f"GC {gc:.0f}%"),
        (not 52 <= tm <= 65, f"Tm {tm:.0f} C"), (str(s[-1]) not in "GC", "no 3' G/C clamp")] if bad]
    return {"len": len(s), "gc": round(gc, 1), "tm": round(tm, 1), "issues": issues}

def primer_sites(template, primer, max_mm=1, anchor3=5):
    """Sites on either strand with <= max_mm mismatches and a perfect 3' end of `anchor3` nt."""
    t, p = template.upper(), primer.upper()
    hits = []
    for strand, q in [("+", p), ("-", str(Seq(p).reverse_complement()))]:
        for i in range(len(t) - len(q) + 1):
            w = t[i:i + len(q)]
            mm = sum(a != b for a, b in zip(q, w))
            end_ok = q[-anchor3:] == w[-anchor3:] if strand == "+" else q[:anchor3] == w[:anchor3]
            if mm <= max_mm and end_ok:
                hits.append({"pos": i, "strand": strand, "mismatches": mm})
    return hits

print(check_primer("ATGGTATTCAGAATAGCTAGCTCC"), primer_sites(seq, "ATGGTATTCAGAATAGCTAGCTCC"))
```

For PCR product size: forward site on `+` at `i`, reverse site on `-` at `j`
gives `j + len(reverse) - i` bp. For primer design from scratch use
primer3-py.

### Module 7: Substitutions Between Sequences

```python
from Bio import Align

def substitutions(ref, alt):
    """Amino acid (or base) changes of alt vs ref, 1-based on ref, e.g. 'R317C'."""
    if len(ref) == len(alt):
        return [f"{a}{i + 1}{b}" for i, (a, b) in enumerate(zip(ref, alt)) if a != b]
    aligner = Align.PairwiseAligner(mode="global", open_gap_score=-10, extend_gap_score=-0.5)
    aln = aligner.align(ref, alt)[0]
    out, pos = [], 0
    for a, b in zip(aln[0], aln[1]):
        pos += a != "-"
        if a != b:
            out.append(f"{a}{pos}{b}" if "-" not in (a, b) else f"{'ins' if a == '-' else 'del'}@{pos}")
    return out

options = {"A": "MLLAVLYCLLWSFQTS", "B": "MLLAVLYCLRWSFQTS", "C": "MLLAVLYCLLWSFQTS"}
ref = options["A"]
for k, v in options.items():
    print(k, substitutions(ref, v) or "identical to reference")
```

Then look each change up in ClinVar (`database-query` Step 6) using the
numbering of the isoform that matches your reference. Do not call a variant
benign or pathogenic from amino acid chemistry.

### Module 8: Kozak Context

Vertebrate consensus `gccRccAUGG`: a purine at -3 matters most, then G at
+4 (Kozak 1987):

```python
def kozak_score(seq, aug):
    """aug: 0-based index of the A of AUG. Score 0-4: -3 purine (2), +4 G (1), GCC at -6..-4 (1)."""
    s = seq.upper().replace("U", "T")
    score = 0
    if aug >= 3 and s[aug - 3] in "AG":
        score += 2
    if aug + 3 < len(s) and s[aug + 3] == "G":
        score += 1
    if aug >= 6 and s[aug - 6:aug - 3] == "GCC":
        score += 1
    return score

for name, s in {"A": "CCCUGAUGCCUGCUAGC", "B": "CCACCAUGGCUAAUGAC"}.items():
    i = s.upper().replace("U", "T").find("ATG")
    print(name, kozak_score(s, i), s[max(0, i - 6):i + 4])
```

Scores compare candidates; they are not measured efficiencies. An upstream
AUG before the main start (`find` returns the first) also reduces initiation.

### Module 9: Cloning Primers

Take the vector arms from the real plasmid around the cut site:

```python
def vector_arms(vector, enzyme, arm=30):
    """Flanks of a single-cutter on a circular vector (top strand cut)."""
    enz = getattr(Restriction, enzyme)
    cuts = enz.search(Seq(vector), linear=False)
    assert len(cuts) == 1, f"{enzyme} cuts {len(cuts)} times"
    c = cuts[0] - 1                      # 0-based index of first base after the cut
    v2 = vector + vector                 # handle wrap-around
    c2 = c + len(vector)
    return v2[c2 - arm:c2], v2[c2:c2 + arm]

def gibson_primers(gene, up_arm, down_arm, anneal=22):
    fwd = up_arm + gene[:anneal]
    rev = str(Seq(down_arm).reverse_complement()) + str(Seq(gene[-anneal:]).reverse_complement())
    return fwd, rev

def restriction_primers(gene, enz5, enz3, anneal=20, pad="GCGC"):
    s5, s3 = getattr(Restriction, enz5).site, getattr(Restriction, enz3).site
    return pad + s5 + gene[:anneal], pad + s3 + str(Seq(gene[-anneal:]).reverse_complement())

up, down = vector_arms(puc19, "HindIII")
fwd, rev = gibson_primers(seq, up, down)
print("Gibson F", fwd, check_primer(fwd[-22:])["tm"])
print("Gibson R", rev, check_primer(rev[-22:])["tm"])
print("EcoRI/HindIII", restriction_primers(seq, "EcoRI", "HindIII"))
```

The 5' overhang of a sticky cut sits on one arm; Gibson exonuclease removes
it, so homology can start at the cut. To check a given primer, test that its
5' part occurs in the vector (`primer[:30] in vector`) and its 3' part matches
the gene start (forward) or the reverse complement of the gene end (reverse).
Confirm the restriction sites chosen for restriction cloning do not also cut
inside the insert (`digest(seq, [enz5, enz3])`).

## Common Workflows

### Workflow: Identify a Protein and Look Up Its Variants

Modules 2 and 7, then ClinVar via `database-query`:

```python
from Bio import Entrez, SeqIO

QUERY = "<protein sequence>"
record = blast_top_hits(QUERY, n=3)
top_acc = record.alignments[0].accession
ref_prot = str(SeqIO.read(Entrez.efetch(db="protein", id=top_acc, rettype="fasta", retmode="text"), "fasta").seq)
changes = substitutions(ref_prot, QUERY)
print(f"top hit {top_acc}: {record.alignments[0].hit_def[:60]}")
print("changes vs reference:", changes or "none")
# then: clinvar_protein_change(<gene symbol>, change) from database-query, per change
```

Confirm the reference isoform before looking changes up; numbering differs
between isoforms.

### Workflow: Gibson Cloning into pUC19

Modules 1, 3, 9 and 6 in order - fetch, check the insert has no site for the
linearising enzyme, build primers from the real arms, check them:

```python
gene = str(fetch_gene("rsxD").seq).upper()
vector = str(fetch_accession("M77789").seq).upper()
ENZ = "HindIII"
inside = Restriction.RestrictionBatch([ENZ]).search(Seq(gene), linear=True)
assert not any(inside.values()), f"{ENZ} also cuts the insert at {inside}"
up, down = vector_arms(vector, ENZ, arm=30)
fwd, rev = gibson_primers(gene, up, down, anneal=22)
for name, pr in [("F", fwd), ("R", rev)]:
    print(name, pr, check_primer(pr[-22:]))            # check the annealing part only
print("product size:", len(gene) + 2 * 30, "bp")
```

## Key Parameters

| Parameter | Default | Effect |
|---|---|---|
| `circular` (digest) | False | Circular plasmids: fragments = cuts |
| BLAST `database` | `swissprot` / `nt` | Curated and fast vs comprehensive |
| `Tm_NN` `Na`, `dnac1` | 50 mM, 250 nM | Match your PCR buffer and primer concentration |
| `min_aa` (ORFs) | 100 | Shorter ORFs are common by chance |
| `max_mm`, `anchor3` (binding) | 1, 5 | Off-target binding stringency |
| Gibson `arm` | 30 | 20-40 bp homology is typical |

## Common Recipes

### Recipe: In-silico PCR Product

```python
def pcr_product(template, fwd, rev, max_mm=1):
    f = [h for h in primer_sites(template, fwd, max_mm) if h["strand"] == "+"]
    r = [h for h in primer_sites(template, rev, max_mm) if h["strand"] == "-"]
    products = [(a["pos"], b["pos"] + len(rev)) for a in f for b in r if b["pos"] > a["pos"]]
    return [(s, e, e - s) for s, e in products]

print(pcr_product(seq, "ATGGTATTCAGAATAGCTAGCTCC", str(Seq(seq[-24:]).reverse_complement())))
```

More than one product means off-target priming; tighten `max_mm` or redesign.

### Recipe: Find a Motif (IUPAC) on Both Strands

```python
from Bio.SeqUtils import nt_search

def find_motif(sequence, motif):
    s = sequence.upper()
    fwd = nt_search(s, motif)[1:]                               # first element is the regex used
    rc = str(Seq(motif).reverse_complement())
    rev = nt_search(s, rc)[1:] if rc != motif else []
    return {"+": fwd, "-": rev}

print(find_motif(puc19, "GANTC"))                               # HinfI site, N = any base
```

## Troubleshooting

| Problem | Cause | Fix |
|---|---|---|
| Gene search returns another organism's gene | Organism name too broad | Use the strain name (e.g. `Escherichia coli str. K-12 substr. MG1655`) |
| Fetched gene does not start with ATG | Minus-strand handling or alternative start (GTG/TTG in bacteria) | Check `strand`; bacterial starts can be GTG |
| BLAST times out or HTTP error | NCBI queue | Retry later; use `swissprot` and a shorter query |
| `AttributeError` for an enzyme | Name typo or case | `Restriction.AllEnzymes.get("HindIII")` |
| Fragment count off by one | Linear vs circular | Set `circular=True` for plasmids |
| Substitution positions off | Sequences not aligned / different isoform | Use the alignment path; confirm the reference isoform |
| `HTTP 429` from Entrez | Rate limit | Pause between calls or set `Entrez.api_key` |

## Related Skills

- `biopython-sequence-analysis` - SeqIO, Entrez, BLAST, alignment in depth
- `biopython-molecular-biology` - restriction analysis, motifs, PDB
- `database-query` - ClinVar classification of found substitutions
- `plannotate-plasmid-annotation` - annotate features of a plasmid sequence
- `uniprot-protein-database` - protein entry after BLAST identification

## References

- Cock et al. (2009) Biopython, Bioinformatics: https://doi.org/10.1093/bioinformatics/btp163
- Biopython tutorial: https://biopython.org/docs/latest/Tutorial/index.html
- NCBI E-utilities documentation: https://www.ncbi.nlm.nih.gov/books/NBK25501/
- NCBI BLAST URL API: https://blast.ncbi.nlm.nih.gov/doc/blast-help/developerinfo.html
- Kozak (1987) 5'-noncoding sequences of vertebrate mRNAs, Nucleic Acids Research: https://doi.org/10.1093/nar/15.20.8125
- Gibson et al. (2009) Enzymatic assembly of DNA molecules, Nature Methods: https://doi.org/10.1038/nmeth.1318
