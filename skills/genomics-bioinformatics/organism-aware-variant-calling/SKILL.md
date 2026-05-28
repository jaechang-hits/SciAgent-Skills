---
name: organism-aware-variant-calling
description: "Variant calling and variant-set analysis that respects the source organism's biology — ploidy selection, reference→species inference, and re-call workflows when an inherited VCF was produced with wrong parameters. Bacterial samples are haploid; eukaryotic samples vary."
license: MIT
---

# Organism-Aware Variant Calling

## Overview

Variant calling parameters — especially **ploidy** — must match the source organism's biology. Bacterial samples called with diploid defaults yield systematically wrong SNP counts, Ts/Tv ratios, and false-heterozygous calls. This guide covers how to verify the organism context before analysis and how to re-call when an inherited VCF used wrong parameters.

Apply this guide before any of: counting variants, computing Ts/Tv, dN/dS, SNP density, allele frequencies, or anything else that assumes the VCF accurately reflects the underlying genome.

## Key Concepts

### Ploidy and what it does to a variant caller

Ploidy is the number of complete chromosome sets in a cell. Variant callers model genotypes against an assumed ploidy: at ploidy 2 a site can be 0/0, 0/1, or 1/1; at ploidy 1 only 0 or 1. A wrong assumption distorts genotype likelihoods, allele-balance filters, and downstream counts. Bacteria and archaea are haploid (one chromosome copy) so any "heterozygous" call in a bacterial isolate is biologically meaningless — it usually signals contamination, a mixed population, or a caller misconfiguration.

### Caller defaults and the inherited-VCF trap

Both GATK HaplotypeCaller and `bcftools call` default to ploidy = 2 because their first-class use case is human germline analysis. This default is correct for mammals and most plants but **wrong for any bacterial or viral sample**, and inherited VCFs do not self-validate — a file named `_raw_variants.vcf` may have been generated with parameters that don't match its organism. Always inspect the `##GATKCommandLine` and `##reference` lines of the header before trusting a call set.

### Reference assembly determines organism — and ploidy

NCBI assembly accessions (`GCF_*`, `GCA_*`) deterministically map to an organism, which in turn dictates the correct ploidy. ASM584v2 (GCF_000005845.2) → *E. coli* K-12 → ploidy 1. GRCh38 → *H. sapiens* → ploidy 2. Resolving the reference is therefore the single most informative pre-call step.

### Ts/Tv as a sanity check on call-set health

Human WGS typically shows transition/transversion ratios of ≈ 2.0–2.1; bacterial isolates vs. a close reference ≈ 2.5–3.0; viral samples vary by lineage. A Ts/Tv that drops well below the expected range is a fingerprint of false-heterozygous calls inflating the transversion count — the canonical symptom of a ploidy mismatch on a haploid sample.

## Decision Framework

### Step 0 — Identify the Organism Before Anything Else

Inspect what is already in the workspace. Standard locations:

**Reference FASTA header**
```bash
head -1 reference.fna
# >NC_000913.3 Escherichia coli str. K-12 substr. MG1655, complete genome
```

**Existing VCF metadata** (the most important check for inherited VCFs)
```bash
grep -E "^##(reference|contig|GATKCommandLine)" sample.vcf | head -5
# ##reference=file:///path/to/GCF_000005845.2_ASM584v2_genomic.fna
# ##contig=<ID=NC_000913.3,length=4641652>
# ##GATKCommandLine=...--sample-ploidy 2...   ← red flag for bacterial sample
```

**BAM header**
```bash
samtools view -H sample.bam | grep -E "^@(SQ|PG)" | head -5
```

**Reference accession → organism**

| Accession                  | Organism                              | Ploidy |
|----------------------------|---------------------------------------|--------|
| GCF_000005845.2 (ASM584v2) | *Escherichia coli* K-12 MG1655        | 1      |
| GCF_000195955.2            | *Mycobacterium tuberculosis* H37Rv    | 1      |
| GCF_000006765.1            | *Pseudomonas aeruginosa* PAO1         | 1      |
| GCF_000009045.1            | *Bacillus subtilis* 168               | 1      |
| GCF_000146045.2            | *Saccharomyces cerevisiae* S288C      | 1 or 2 |
| GCF_000001405.40 (GRCh38)  | *Homo sapiens*                        | 2      |
| GCF_000001635.27 (GRCm39)  | *Mus musculus*                        | 2      |
| GCA_009858895.3            | SARS-CoV-2                            | 1      |

If only an assembly accession is provided, resolve it via `https://www.ncbi.nlm.nih.gov/datasets/genome/{accession}/` before proceeding.

### Step 1 — Pick Ploidy by Organism Class

| Organism class                  | Ploidy | Caller flag                                  |
|---------------------------------|--------|----------------------------------------------|
| Bacteria, archaea (any)         | 1      | `--sample-ploidy 1` / `--ploidy 1`           |
| Most viruses                    | 1      | same                                         |
| Haploid yeast / fungal strains  | 1      | same                                         |
| Mammals, most plants            | 2      | default (no flag needed)                     |
| Polyploid plants (e.g. wheat 6n)| n      | `--sample-ploidy n` / `--ploidy n`           |
| Cancer / tumor / heterogeneous  | mixed  | use tumor-aware caller (Mutect2, Strelka2)   |
| Pooled bacterial / viral        | mixed  | use frequency-based caller (LoFreq, VarScan) |

Bacterial isolates are **always** ploidy = 1 even when DNA prep yields many genome copies — the genome itself is single-copy.

### Step 2 — Decide Whether to Re-call

- If `##GATKCommandLine ... --sample-ploidy P` matches the organism's correct ploidy: keep using the VCF.
- If it does not match (typical case: bacterial sample called at ploidy=2): re-call from the BAM. See *Best Practices* below.
- If no BAM is available: filter the existing diploid VCF to homozygous-alt only as a partial workaround (loses some sensitivity).

## Best Practices

- **Inspect the reference FASTA, VCF, and BAM headers as Step 0 of any analysis** — `head -1 reference.fna`, `grep ^## sample.vcf`, and `samtools view -H sample.bam | grep ^@SQ` together reveal the organism, the assembly accession, and the caller parameters used. Do this before any downstream computation, not after.

- **Re-call from BAM with bcftools when an inherited VCF has the wrong ploidy** — `bcftools mpileup -f reference.fna sample.sorted.bam -Ou | bcftools call --ploidy 1 -mv -Oz -o sample.recalled.vcf.gz` then index with `bcftools index`. Fast, scriptable, no Java/jar dependency.

- **Re-call with GATK HaplotypeCaller when staying on the GATK Best-Practices path** — `gatk HaplotypeCaller --reference reference.fna --input sample.sorted.bam --sample-ploidy 1 --output sample.recalled.vcf`. Use this when the rest of your pipeline (BQSR, VQSR, joint-calling) is already GATK-based.

- **Use a partial fix only when re-calling is impossible** — `bcftools view -g hom sample.diploid.vcf -Oz -o sample.hom.vcf.gz` keeps homozygous-alt records and drops false-het noise from diploid calls on haploid samples. This is a last resort; it does not recover variants the caller missed under the wrong ploidy.

- **Always sanity-check Ts/Tv against organism expectations after (re-)calling** — `bcftools stats sample.vcf.gz | grep TSTV`. Human WGS ≈ 2.0–2.1, bacterial vs. close reference ≈ 2.5–3.0. Values more than ~20% off should trigger a header / parameter re-inspection before publishing the statistic.

- **Record the organism, reference accession, caller, and ploidy in the analysis output** — log them next to every variant statistic you report. Future readers and reviewers can validate or rerun without guessing your assumptions, and parameter mismatches surface immediately during peer review or re-analysis.

## Common Pitfalls

- **Trusting `*_raw_variants.vcf` blindly.** GATK default is ploidy = 2, and "raw" in a filename does not imply correctness for any organism. **How to avoid:** always grep `##GATKCommandLine` for `--sample-ploidy` and `##reference` for the assembly before using the file for any statistic.

- **Computing Ts/Tv on a diploid-called bacterial VCF.** False heterozygous sites bias the transversion count downward; Ts/Tv comes out artificially low (e.g., 2.55 instead of the expected ~2.7). **How to avoid:** verify the VCF was called at the organism's correct ploidy before computing Ts/Tv; if not, re-call from BAM first.

- **Mixing reference assembly versions.** ASM584v2 and newer *E. coli* K-12 builds have different contig IDs, and BAM/VCF/FASTA produced against one will silently fail against another. **How to avoid:** if `##contig` IDs in the VCF don't match your reference FASTA headers, **don't** proceed — re-align to the matching reference before re-calling.

- **Yeast diploid assumption.** *S. cerevisiae* has both haploid and diploid life stages, and the strain dictates which is correct. **How to avoid:** check strain notes (lab S288C is typically haploid; SK1/Y55 industrial strains are often diploid) **instead of** assuming a default; consult strain metadata when in doubt.

- **Pooled or metagenomic samples treated as single-organism.** Single-organism ploidy heuristics break for pooled DNA, multi-strain cultures, and metagenomes. **How to avoid:** **don't** use germline callers with a fixed ploidy; instead use frequency-based callers (LoFreq, VarScan in pooled mode) and report allele frequencies, not genotypes.

- **Cancer / tumor samples called with germline callers.** Diploid germline callers misclassify somatic variants and miss subclonal events. **How to avoid:** **never** use HaplotypeCaller or `bcftools call` on tumor BAMs; use somatic-aware callers (Mutect2, Strelka2) **instead**.

- **Re-using a `.fai` index from a different reference.** A zero-byte or mismatched `.fai` will silently break `bcftools mpileup` or return empty calls. **How to avoid:** when in doubt, **always** re-run `samtools faidx reference.fna` before calling, especially after copying reference files between systems.

## Quick Inference Examples

| Header / accession seen in workspace                                | Organism            | Ploidy | Action if existing VCF is ploidy=2 |
|---------------------------------------------------------------------|---------------------|--------|------------------------------------|
| `>NC_000913.3 Escherichia coli str. K-12 substr. MG1655`            | E. coli             | 1      | re-call with `--ploidy 1`          |
| `GCF_000005845.2_ASM584v2_genomic.fna`                              | E. coli K-12        | 1      | re-call                            |
| `>NC_002516.2 Pseudomonas aeruginosa PAO1`                          | P. aeruginosa       | 1      | re-call                            |
| `>NC_000962.3 Mycobacterium tuberculosis H37Rv`                     | M. tuberculosis     | 1      | re-call                            |
| `GRCh38_no_alt_analysis_set.fasta` / `GCF_000001405.40`             | H. sapiens          | 2      | usually no change                  |
| `>MN908947.3 Severe acute respiratory syndrome coronavirus 2`       | SARS-CoV-2          | 1      | viral pipelines default to 1       |

## Related Skills

- `gatk-variant-calling` — full GATK Best Practices germline pipeline (human diploid focus)
- `bcftools-variant-manipulation` — VCF subsetting, filtering, stats
- `samtools-bam-processing` — BAM indexing, header inspection, sorting
- `vcf-variant-filtering` — quality filtering with FILTER column and INFO fields
- `bwa-mem2-dna-aligner` — short-read alignment before calling

## References

- GATK HaplotypeCaller documentation (Broad Institute): https://gatk.broadinstitute.org/hc/en-us/articles/360037225632-HaplotypeCaller
- bcftools manual — `call` command and `--ploidy` option: https://samtools.github.io/bcftools/bcftools.html#call
- NCBI Datasets — assembly accession to organism lookup: https://www.ncbi.nlm.nih.gov/datasets/genome/
- Olson, N. D. et al. (2015). *Best practices for evaluating single nucleotide variant calling methods for microbial genomics.* Frontiers in Genetics 6:235. https://doi.org/10.3389/fgene.2015.00235
- DePristo, M. A. et al. (2011). *A framework for variation discovery and genotyping using next-generation DNA sequencing data.* Nature Genetics 43:491–498. https://doi.org/10.1038/ng.806
- Wikipedia — Transitions and transversions (Ts/Tv background): https://en.wikipedia.org/wiki/Transversion
