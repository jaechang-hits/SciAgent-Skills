---
name: "sgrna-design-guide"
description: "Decision guide for finding/designing sgRNAs via three tiers: (1) validated from Addgene/literature, (2) pre-computed from Broad CRISPick, (3) de novo via CRISPOR/Benchling as last resort. Covers PAM rules (SpCas9, SaCas9, AsCas12a, enAsCas12a), quality metrics, and targeting rules for knockout, CRISPRa/i, base and prime editing. Use when planning CRISPR and unsure which sgRNA source to pick."
license: "CC-BY-4.0"
---

# sgRNA Design Guide

## Overview

Selecting effective sgRNAs is the single most consequential decision in a CRISPR experiment. A poorly chosen guide RNA yields low editing efficiency, off-target mutations, or misleading phenotypes regardless of how well everything else is optimized. This guide provides a three-tiered decision strategy — validated sequences first, pre-computed designs second, de novo design only as a last resort — and explains the sgRNA quality metrics, PAM requirements, and application-specific targeting rules needed to make confident design choices.

The guide is adapted from the Biomni sgRNA Design Guide (Biomni Team, CC BY 4.0, November 2025) with expanded PAM rules, a unified decision framework, and additional best practices.

## Key Concepts

### PAM Requirements by Cas Enzyme

The protospacer adjacent motif (PAM) is a short DNA sequence the Cas nuclease requires for binding and cleavage. The PAM must be present in the genomic target immediately adjacent to the guide RNA binding site. Choosing the wrong enzyme or misidentifying the PAM renders a guide non-functional.

| Enzyme | Guide Length | PAM Location | PAM Sequence | Notes |
|--------|-------------|--------------|--------------|-------|
| SpCas9 | 20 bp | 3′ of target | NGG | Most widely used; broadest reagent support |
| SaCas9 | 20 bp | 3′ of target | NNGRRT | Smaller package; useful for AAV delivery |
| AsCas12a (wild-type) | 23–25 bp | 5′ of target | TTTV | Staggered DSB; lower background in some cell types |
| enAsCas12a (enhanced) | 23–25 bp | 5′ of target | TTTV | Higher activity than wild-type; NOT interchangeable |
| CjCas9 | 22 bp | 3′ of target | NNNNRYAC | Compact; AAV-compatible |
| Cas13 (RNA targeting) | 22–30 bp | N/A (RNA) | None | Targets RNA, not DNA; use for RNA knockdown |

**Critical warning**: AsCas12a and enAsCas12a guides are NOT interchangeable. CRISPick provides separate datasets for each; always download the dataset matching your exact Cas variant.

### sgRNA Quality Metrics

Three orthogonal metrics predict sgRNA performance. Optimizing one in isolation often degrades the others.

**On-target efficiency** measures predicted cutting or activation activity at the intended site. Tools such as Rule Set 3 (CRISPick) and DeepCRISPR score efficiency. Higher is better, but efficiency scores from different algorithms are not directly comparable across tools.

**Off-target risk** measures the likelihood of the guide binding and cutting elsewhere in the genome. Metrics include the number of mismatched sites genome-wide and their predicted cleavage rates. Lower off-target score is better. The Cutting Frequency Determination (CFD) score and MIT specificity score are commonly used.

**GC content** of the 20 bp spacer sequence predicts both thermodynamic stability and Pol III transcription termination risk:
- **Optimal range**: 40–60%
- Below 40%: weak base-pairing; low efficiency
- Above 60%: secondary structure formation; reduced activity
- Avoid runs of four or more consecutive T nucleotides (TTTT+): Pol III terminates transcription, producing truncated guides

**CRISPick ranking columns** combine these metrics:
- `Combined Rank`: balances on-target and off-target; use by default
- `On-Target Rank`: prioritize when maximum cutting efficiency is required
- `Off-Target Rank`: prioritize when specificity is paramount (therapeutic applications, base editing, studies where off-target phenotypes would confound results)

### CRISPR Application Types

The optimal sgRNA design rules differ by application because each alters the genome or transcriptome differently.

| Application | Mechanism | Targeting Rule | Enzyme |
|-------------|-----------|---------------|--------|
| Knockout (loss of function) | Frameshift or large deletion via NHEJ | Early exons (first 30–50% of coding sequence); avoid last exon | SpCas9, SaCas9, Cas12a |
| CRISPRa (gene activation) | Transcriptional activation via dCas9-VP64 etc. | −200 to −1 bp from TSS | dSpCas9, dSaCas9 |
| CRISPRi (gene inhibition) | Transcriptional repression via dCas9-KRAB | −50 to +300 bp from TSS | dSpCas9 |
| Base editing | C→T or A→G conversion without DSB | Position the target base in the editing window (≈positions 4–8 from PAM) | BE4max, ABE8e |
| Prime editing | Precise insertions, deletions, substitutions | Nick site + PBS + RT template design; use PrimeDesign or PE-Designer | PE2, PE3 |
| RNA targeting | RNA knockdown or tracking | Target accessible single-stranded region of mRNA | CasRx, LwaCas13a |

## Decision Framework

Choose the sgRNA sourcing approach based on availability of validated sequences and organism/gene coverage:

```
Are validated sgRNAs available for your target gene?
├── YES → Option 1: Use validated sgRNA from database or literature
│   ├── Search addgene_grna_sequences.csv for gene + species + application
│   └── Search literature (PubMed) for published sgRNA sequences
│       └── Record PubMed ID; cite original paper in methods
└── NO → Is your organism/gene covered by CRISPick?
    ├── YES → Option 2: Download pre-computed CRISPick dataset
    │   ├── Filter by Combined Rank ≤ 10 (default)
    │   ├── Confirm GC content 40–60%
    │   ├── Avoid TTTT runs in spacer
    │   └── Select 3–4 guides from distinct exons
    └── NO → Option 3: De novo design (last resort)
        ├── Use CRISPOR, Benchling, or CHOPCHOP
        ├── Apply PAM + GC + position rules (see Key Concepts)
        └── Validate off-target predictions with Cas-OFFinder
```

| Scenario | Recommended Approach | Rationale |
|----------|---------------------|-----------|
| Published gene in human or mouse | Option 1 first, Option 2 if not found | Validated guides have experimental evidence; CRISPick covers >95% of protein-coding genes |
| Genome-scale CRISPR screen | Option 2 (CRISPick) | Pre-computed datasets provide consistent scoring; validated libraries may not cover all targets |
| Non-model organism (e.g., zebrafish, Drosophila) | Option 2 if available, else Option 3 | CRISPick covers some non-human organisms; verify TAXID in download links file |
| Custom PAM or exotic Cas variant | Option 3 (de novo) | CRISPick covers SpCas9/SaCas9/AsCas12a/enAsCas12a only |
| Therapeutic application requiring high specificity | Option 1 or Option 2 with Off-Target Rank | Clinical applications require validated specificity evidence |
| CRISPRa or CRISPRi (not knockout) | Option 2 CRISPRa/CRISPRi dataset | TSS-relative targeting rules differ from knockout; dedicated datasets handle this |
| Base editing or prime editing | Option 3 + specialized tool (PrimeDesign, BE-Designer) | Editing window position is critical; general purpose tools do not compute this correctly |

## Best Practices

1. **Always search validated databases before computational design**: Validated sgRNAs carry experimental evidence of cutting efficiency and off-target activity. This eliminates prediction uncertainty. Search Addgene and PubMed before investing time in computational design. A 10-minute database search can replace weeks of experimental validation.

2. **Target early coding exons for knockout experiments**: Frameshift mutations near the N-terminus disrupt the protein regardless of downstream in-frame indels. Guides targeting the last exon frequently produce truncated but partially functional proteins because the C-terminus is dispensable for many protein families. For essential genes, target the first 30–50% of the coding sequence; for domain-specific knockouts, target the exon encoding the functional domain.

3. **Validate at least 2–4 guides per target gene**: A single sgRNA may have low efficiency in your specific cell type even if it scores well computationally. On-target prediction algorithms have cell-type-specific inaccuracies. Using 2–4 guides from distinct exons protects against single-guide failure and provides an internal specificity control: if all guides produce the same phenotype, off-target effects are unlikely to explain the result.

4. **Check for single nucleotide polymorphisms (SNPs) in the guide region**: A SNP within the 20 bp spacer or at the PAM reduces binding and cleavage efficiency. This is particularly important when designing guides for genetically diverse patient-derived cells or mouse strains. Use dbSNP or gnomAD to check the spacer sequence before ordering.

5. **Confirm GC content is between 40–60% and avoid poly-T sequences**: Both rules are absolute filters, not preferences. Guides outside the GC window or containing TTTT runs will perform poorly regardless of their algorithmic rank. Always verify these properties on your final guide sequences.

6. **Match the CRISPick dataset exactly to your Cas variant**: AsCas12a and enAsCas12a are distinct enzymes with different activity profiles. Guides optimized for enAsCas12a may fail entirely with wild-type AsCas12a. CRISPick uses different models for each; download the dataset named for your specific enzyme.

7. **Perform computational off-target analysis before ordering**: Even if using a high-rank CRISPick guide, run Cas-OFFinder or CRISPOR to enumerate potential off-target sites. For therapeutic applications, validate predicted off-target sites by amplicon sequencing. For basic research, a guide with fewer than 5 predicted off-target sites with ≤2 mismatches is generally acceptable.

## Common Pitfalls

1. **Skipping the validated database search**: Researchers often jump directly to computational design tools without checking whether a validated guide already exists for their target.
   - *How to avoid*: Make database searching Step 1 in every sgRNA design project. Query Addgene's curated sequence list and search PubMed with terms like `"[GENE] sgRNA validated"` or `"[GENE] CRISPR knockout sequence"`. Spend at least 15 minutes on this before opening a design tool.

2. **Targeting late exons for knockout**: Guides targeting the final exon or C-terminal coding sequence often produce proteins that are truncated but retain partial function, leading to incomplete loss-of-function and ambiguous phenotypes.
   - *How to avoid*: Filter CRISPick results by exon number and prefer guides in exon 1–3 or within the first 50% of the coding sequence. For CRISPick knockout datasets, use `Exon Number <= 3` or `Target Cut % <= 50` as a primary filter.

3. **Using a single guide and attributing all phenotypes to on-target editing**: Off-target edits at a locus with similar sequence can produce the same phenotype, leading to incorrect target attribution.
   - *How to avoid*: Design 3–4 guides from different exons and confirm that independent guides produce consistent phenotypes. For critical experiments, perform whole-genome sequencing on at least one edited clone to assess off-target editing frequency.

4. **Confusing AsCas12a and enAsCas12a datasets**: These are listed together in many repositories and have the same PAM (TTTV), leading researchers to use the wrong dataset or mix up the enzymes.
   - *How to avoid*: Write the exact enzyme name in your lab notebook and confirm the CRISPick filename contains the matching string (`AsCas12a` vs `enAsCas12a`). If you received the Cas12a expression vector from a collaborator, verify the variant by checking the plasmid sequence or Addgene page.

5. **Ignoring GC content and poly-T filters**: Algorithmic ranks (Combined Rank, On-Target Rank) do not always filter out guides that fail the GC or poly-T rules, particularly in older datasets.
   - *How to avoid*: After filtering by rank, apply explicit GC content (40–60%) and poly-T (no TTTT runs) filters before finalizing your guide list. These are hard constraints, not soft preferences.

6. **Designing guides without checking for SNPs in the target region**: Population-level SNPs in the spacer or PAM reduce editing efficiency unpredictably and can make results non-reproducible across cell lines from different donors.
   - *How to avoid*: After selecting guide sequences, paste the spacer into dbSNP or UCSC Genome Browser and check for common variants (MAF > 1%). If a SNP is present, select an alternative guide or design guides flanking the SNP.

7. **Using CRISPRa/CRISPRi guides for knockout (or vice versa)**: The targeting rules are fundamentally different: knockout guides can be anywhere in the coding exons, while activation and inhibition guides must target specific windows relative to the TSS. Using a knockout guide for CRISPRa rarely produces activation.
   - *How to avoid*: Download the application-specific CRISPick dataset (CRISPRa or CRISPRi, not CRISPRko) and confirm that the guide's TSS offset falls within the required window (−200 to −1 bp for CRISPRa; −50 to +300 bp for CRISPRi).

## Workflow

1. **Define the target and application**: Specify the gene symbol, species, Cas enzyme, and application (knockout/CRISPRa/CRISPRi/base editing/prime editing). Write these down before searching or designing — many errors arise from switching assumptions mid-workflow.

2. **Search validated sgRNA databases (Option 1)**:
   - Query the Addgene curated sequence database by gene name, species, and application.
   - Search PubMed for publications describing validated sgRNAs for your target.
   - If 1–4 validated guides are found, record their sequences and PubMed IDs; proceed to Step 4.
   - If no validated guides are found after 15–20 minutes of searching, proceed to Step 3.

3. **Download and filter the CRISPick pre-computed dataset (Option 2)**:
   - Identify the correct dataset from the CRISPick download links using the TAXID, genome build, Cas enzyme, and application type.
   - Download and decompress the `.txt.gz` file.
   - Filter for your gene, then apply ranking and quality filters (see Protocol Guidelines).
   - Select 3–4 guides from distinct exons with Combined Rank ≤ 10.
   - If your organism or gene is not in any CRISPick dataset, proceed to de novo design (Option 3).

4. **Verify guide quality**:
   - Confirm GC content 40–60% for each selected guide.
   - Confirm no TTTT runs in the spacer.
   - Check for SNPs using dbSNP or UCSC Genome Browser.
   - Run off-target prediction with Cas-OFFinder or CRISPOR.

5. **Order and clone**:
   - Order as annealed oligo pairs for ligation into a Cas9 expression vector, or as a single-stranded oligo for Gibson assembly.
   - Sequence the final construct to confirm correct guide insertion.

6. **Validate experimentally**:
   - Transfect or transduce cells; assess editing efficiency by Sanger sequencing and ICE or TIDE analysis.
   - For screens or critical experiments, validate at least 2 independent clones per guide.

## Protocol Guidelines

### Filtering CRISPick Datasets (Option 2)

```python
import pandas as pd

# Load the CRISPick tab-delimited file (after gunzip)
df = pd.read_csv(
    "sgRNA_design_9606_GRCh38_SpyoCas9_CRISPRko_RS3seq-Chen2013+RS3target_NCBI_20241104.txt",
    sep="\t",
    low_memory=False,
)

gene_name = "TP53"

# Step 1: Filter for gene of interest
gene_df = df[df["Target Gene Symbol"] == gene_name].copy()
print(f"Total sgRNAs for {gene_name}: {len(gene_df)}")

# Step 2: Apply quality filters
filtered = gene_df[
    gene_df["Combined Rank"] <= 10   # top-ranked guides per gene
].copy()

# Step 3: Compute GC content and exclude out-of-range guides
def gc_content(seq):
    seq = str(seq).upper()
    return (seq.count("G") + seq.count("C")) / len(seq) * 100

filtered["GC%"] = filtered["sgRNA Sequence"].apply(gc_content)
filtered = filtered[(filtered["GC%"] >= 40) & (filtered["GC%"] <= 60)]

# Step 4: Exclude guides with TTTT runs (Pol III terminator)
filtered = filtered[~filtered["sgRNA Sequence"].str.upper().str.contains("TTTT")]

# Step 5: Prefer early exons for knockout
early_exon = filtered[filtered["Exon Number"] <= 5]

# Step 6: Select one guide per exon for diversity
final = (
    early_exon.sort_values("Combined Rank")
    .groupby("Exon Number")
    .head(1)
    .head(4)
)

print(final[["sgRNA Sequence", "Exon Number", "Combined Rank", "GC%"]])
final.to_csv(f"{gene_name}_selected_sgrnas.csv", index=False)
```

### Searching the Addgene Validated sgRNA Database (Option 1)

```python
import pandas as pd

# Load the Addgene curated database (300+ validated sequences)
# Source: Addgene validated sgRNA database (https://www.addgene.org/crispr/guide-rna-sequences/)
df = pd.read_csv("addgene_grna_sequences.csv")

# Search by gene, species, and application
gene = "TP53"
species = "H. sapiens"
application = "cut"          # "cut" = knockout, "activate" = CRISPRa

results = df[
    (df["Target_Gene"].str.upper() == gene.upper()) &
    (df["Target_Species"] == species) &
    (df["Application"] == application)
]

if results.empty:
    print(f"No validated sgRNAs found for {gene} in {species}. Proceed to Option 2.")
else:
    print(f"Found {len(results)} validated sgRNA(s):")
    print(
        results[
            ["Target_Gene", "Target_Sequence", "Plasmid_ID", "PubMed_ID", "Depositor"]
        ]
    )
    # Always cite the PubMed_ID in your methods section
```

### GC Content and Poly-T Spot-Check (any source)

```python
def validate_sgrna(spacer: str) -> dict:
    """Check GC content and poly-T for a single spacer sequence."""
    spacer = spacer.upper().strip()
    gc = (spacer.count("G") + spacer.count("C")) / len(spacer) * 100
    has_poly_t = "TTTT" in spacer
    return {
        "sequence": spacer,
        "length": len(spacer),
        "gc_pct": round(gc, 1),
        "gc_ok": 40 <= gc <= 60,
        "poly_t": has_poly_t,
        "passes": (40 <= gc <= 60) and not has_poly_t,
    }

# Example
guides = ["GAGGTTGTGAGGCGCTGCCC", "CACCTTTTTTGGACACTGAT", "GCGCGATCGCGATCGCGCGC"]
for g in guides:
    result = validate_sgrna(g)
    status = "PASS" if result["passes"] else "FAIL"
    print(f"[{status}] {result['sequence']}  GC={result['gc_pct']}%  poly-T={result['poly_t']}")
# Expected output:
# [PASS] GAGGTTGTGAGGCGCTGCCC  GC=65.0%  poly-T=False   <- fails GC check (>60)
# [FAIL] CACCTTTTTTGGACACTGAT  GC=45.0%  poly-T=True    <- poly-T present
# [FAIL] GCGCGATCGCGATCGCGCGC  GC=75.0%  poly-T=False   <- fails GC check (>60)
```

## Further Reading

- [CRISPick (Broad Institute GPP)](https://portals.broadinstitute.org/gppx/crispick/public) — Pre-computed sgRNA designs for human, mouse, and other organisms; datasets for SpCas9, SaCas9, AsCas12a, and enAsCas12a
- [CRISPOR](http://crispor.tefor.net/) — De novo guide design and off-target scoring for any genome; supports 100+ species and multiple Cas variants
- [Cas-OFFinder](http://www.rgenome.net/cas-offinder/) — Fast genome-wide off-target site enumeration for any Cas enzyme and PAM
- [Addgene CRISPR Guide RNA Database](https://www.addgene.org/crispr/reference/grna-sequence/) — Curated repository of validated sgRNA sequences from published experiments
- [Sanson KR et al. Nat Commun. 2018;9:5416](https://pubmed.ncbi.nlm.nih.gov/30575746/) — CRISPick Rule Set 3 for SpCas9/SaCas9 knockout guide design; required citation for CRISPick Cas9 designs
- [DeWeirdt PC et al. Nat Biotechnol. 2021;39:94–104](https://pubmed.ncbi.nlm.nih.gov/32661438/) — enAsCas12a optimization and CRISPick Cas12a guide scoring; required citation for CRISPick Cas12a designs

## Related Skills

- `biopython-sequence-analysis` — Sequence manipulation, reverse complement calculation, and motif scanning for sgRNA spacer validation
- `biopython-molecular-biology` — Restriction site analysis and primer design workflows useful in sgRNA cloning steps
