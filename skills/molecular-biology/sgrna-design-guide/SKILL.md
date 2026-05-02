---
name: sgrna-design-guide
description: Three-tiered sgRNA design guide using validated Addgene sequences, CRISPick pre-computed datasets, or de novo design rules for CRISPR experiments
license: open
---

# sgRNA Design Guide: Three-Tiered Approach

---

## Metadata

**Short Description**: Comprehensive guide for finding or designing sgRNAs using validated sequences, CRISPick datasets, or de novo design tools.

**Authors**: Ohagent Team

**Version**: 1.0

**Last Updated**: November 2025

**License**: CC BY 4.0

**Commercial Use**: Allowed

## Citations and Acknowledgments

### If you use validated sgRNAs from our database (Option 1):
- **Database Source**: Addgene (https://www.addgene.org)
- **Citation**: Always cite the original publication associated with each sgRNA using the PubMed ID provided in the database
- **Acknowledgment**: "Validated sgRNA sequences obtained from Addgene (https://www.addgene.org/crispr/reference/grna-sequence/)"

### If you use CRISPick designs (Option 2):
- **Acknowledgment Statement**: "Guide designs provided by the CRISPick web tool of the GPP at the Broad Institute"
- **Citation for Cas9 designs (SpCas9, SaCas9)**: Sanson KR, et al. Optimized libraries for CRISPR-Cas9 genetic screens with multiple modalities. Nat Commun. 2018;9(1):5416. PMID: 30575746
- **Citation for Cas12a designs (AsCas12a, enAsCas12a)**: DeWeirdt PC, et al. Optimization of AsCas12a for combinatorial genetic screens in human cells. Nat Biotechnol. 2021;39(1):94-104. PMID: 32661438
  - Note: This paper describes enAsCas12a optimization; specify which variant you used in your methods

---

## Overview

This guide provides a three-tiered approach to sgRNA design, prioritizing validated sequences before moving to computational predictions. Always start with Option 1 and proceed to subsequent options only if needed.

## Key Concepts

### Validated sgRNA Databases (Tier 1)

Validated sgRNAs are guide sequences that have been experimentally tested in published work, with documented cell line, cutting efficiency, and (often) off-target characterization. Addgene curates such sequences alongside the deposited plasmids that carry them, and a downloadable CSV (`addgene_grna_sequences.csv`) provides a searchable index keyed by gene symbol, target species, and application (cut / activate / RNA targeting). Using a validated sgRNA is preferred because the largest source of CRISPR experimental failure is poor on-target activity that would have been detected during the original validation.

### Computational sgRNA Scoring (Tier 2)

When no validated sgRNA exists, pre-computed genome-scale designs from the Broad Institute's CRISPick service are the next best option. CRISPick provides 238 datasets covering multiple genomes, Cas variants, and applications, with each candidate guide ranked by **on-target efficiency** (how reliably it cuts), **off-target specificity** (how unlikely it is to cut elsewhere), and a **combined rank** that balances both. The on-target models behind CRISPick are Sanson 2018 (Cas9) and DeWeirdt 2021 (Cas12a). Combined Rank is the recommended default; use On-Target or Off-Target rank only when the experiment specifically prioritizes one over the other.

### Off-Target Stringency and PAM Compatibility

PAM (Protospacer Adjacent Motif) requirements differ by Cas variant: SpCas9 needs NGG (3'), SaCas9 needs NNGRRT (3'), AsCas12a and enAsCas12a need TTTV (5'). Critically, **AsCas12a and enAsCas12a are different enzymes**: enAsCas12a is an engineered variant with broadened activity, and guides optimized for one will not perform identically on the other. Always match the CRISPick dataset to the exact Cas variant used in the lab. Off-target stringency thresholds (typically `Off-Target Rank` or a CFD-style score) trade specificity against the size of the candidate pool — tighter thresholds yield fewer but cleaner guides.

### De Novo Design Rules (Tier 3)

When neither validated sequences nor pre-computed datasets cover the target (non-model organism, custom locus, etc.), apply rule-based design: 20 bp protospacer for SpCas9/SaCas9 (23–25 bp for Cas12a), GC content 40–60%, avoid TTTT (Pol III terminator) and homopolymer runs >4. Target location matters: early exons (first 50% of coding sequence) for knockout, −200 to +1 from TSS for CRISPRa, −50 to +300 from TSS for CRISPRi.

## Decision Framework

```
sgRNA design decision tree
└── Does Addgene database (Tier 1) contain a validated sgRNA for your gene + species + application?
    ├── Yes -> Use the validated sgRNA(s); cite the original PubMed reference
    └── No  -> Run advanced literature search (mandatory before Tier 2)
        ├── Found in literature -> Use the literature sgRNA; cite the paper
        └── Still no match -> Is the target organism + Cas variant covered by a CRISPick dataset (Tier 2)?
            ├── Yes -> Download dataset, filter by gene, sort by Combined Rank
            │         └── Pick top 3-4 sgRNAs (ideally from different exons for redundancy)
            └── No  -> De novo design (Tier 3) using 20 bp / PAM / GC / avoid-TTTT rules
                      └── Validate experimentally (Sanger / T7E1 / amplicon-seq)
```

| Situation | Recommended tier | Rationale |
|-----------|------------------|-----------|
| Common human/mouse gene with prior CRISPR publications | Tier 1 (Addgene + literature) | Validated sequences come with measured cutting efficiency; lowest experimental risk |
| Genome-scale screen of a model organism | Tier 2 (CRISPick) | Pre-computed datasets cover whole genomes with consistent scoring |
| Single human gene knockout, no Addgene hit | Tier 2 (CRISPick GRCh38 SpCas9 CRISPRko), filter by Combined Rank | Best balance of efficiency and specificity for one-off knockouts |
| CRISPRa / CRISPRi experiment | Tier 2 with the matching `CRISPRa` / `CRISPRi` dataset | Activation/inhibition models target proximal-promoter windows, not coding exons |
| Cas12a (AsCas12a vs enAsCas12a) | Tier 2 with the **exact** Cas12a variant dataset | Guides for one variant are not interchangeable with the other |
| Non-model organism not covered by CRISPick | Tier 3 (de novo rules) | No high-throughput training data exists; rule-based design + experimental validation |
| Small custom locus (e.g., engineered cassette) | Tier 3 | Locus is not in any reference genome; design directly against the target sequence |
| Maximum specificity required (e.g., therapeutic application) | Tier 2 sorted by **Off-Target Rank** | Prioritize guides with the fewest predicted off-target sites |
| Maximum cutting efficiency required (e.g., difficult cell line) | Tier 2 sorted by **On-Target Rank** | Accept slightly higher off-target risk in exchange for activity |

## Best Practices

1. **Always exhaust Tier 1 before moving to Tier 2.** Even if `addgene_grna_sequences.csv` returns no rows, run the literature search step (Method 2). Many validated sgRNAs are published in supplementary materials but never deposited at Addgene.
2. **Match the CRISPick dataset to the exact Cas variant.** AsCas12a and enAsCas12a are distinct enzymes; SpCas9 and SaCas9 require different PAMs. Using the wrong dataset wastes experimental resources.
3. **Use Combined Rank as the default selector.** It balances on-target efficiency and off-target specificity; reach for `On-Target Rank` or `Off-Target Rank` only when the experiment has a specific reason to prioritize one.
4. **Order 3–4 sgRNAs per target gene, ideally from different exons.** A single guide can fail for reasons unrelated to its predicted score (chromatin context, secondary structure, PCR drop-out). Redundancy is cheap insurance.
5. **For knockouts, target the first 50% of the coding sequence.** N-terminal cuts are most likely to produce a true loss-of-function via NMD; C-terminal cuts can leave partially functional protein.
6. **For CRISPRa, design within −200 to +1 bp of the TSS; for CRISPRi, within −50 to +300 bp.** Effector activity drops sharply outside these windows.
7. **Validate experimentally.** Even high-ranked guides fail ~20–30% of the time. Confirm editing with Sanger sequencing, T7E1, ICE, or amplicon-seq before committing to phenotype assays.
8. **Cite the original validation paper for Tier 1, and CRISPick + Sanson 2018 / DeWeirdt 2021 for Tier 2.** Reproducibility depends on traceable provenance for every guide sequence.

## Common Pitfalls

- **Pitfall: Skipping the literature search step (Method 2) when the Addgene CSV returns no hits.**
  - *How to avoid*: Treat Method 2 as mandatory; many validated guides only appear in published supplementary materials.

- **Pitfall: Using AsCas12a guides with enAsCas12a (or vice versa) because both share TTTV PAM.**
  - *How to avoid*: Match the CRISPick dataset filename's Cas tag (`AsCas12a` vs `enAsCas12a`) to the exact enzyme variant used at the bench.

- **Pitfall: Sorting by On-Target Rank only and ending up with high-activity, low-specificity guides that produce off-target editing.**
  - *How to avoid*: Use Combined Rank as the default; only deviate when the experiment explicitly requires extreme efficiency or specificity.

- **Pitfall: Designing a single sgRNA per gene and concluding "the guide doesn't work" when one fails.**
  - *How to avoid*: Always order and test 3–4 guides per gene from independent loci/exons.

- **Pitfall: Targeting late exons or 3' UTRs for knockout.** Truncated proteins from late-exon edits are often partially functional and confound phenotype interpretation.
  - *How to avoid*: For knockouts, restrict candidates to the first 50% of the coding sequence (or the first 3 exons).

- **Pitfall: Using a CRISPRko dataset for a CRISPRa or CRISPRi experiment.** The protospacer windows are different — coding exons for knockout, proximal promoter for activation/inhibition.
  - *How to avoid*: Download the dataset whose application tag (`CRISPRko` / `CRISPRa` / `CRISPRi`) matches the experiment.

- **Pitfall: Designing guides containing `TTTT`.** This sequence terminates RNA Pol III transcription, so the sgRNA simply will not be expressed from a U6 promoter.
  - *How to avoid*: Always filter de novo designs (and double-check Tier 1/2 picks) against `TTTT` and homopolymer runs >4.

- **Pitfall: Failing to cite the original publication for a validated sgRNA.**
  - *How to avoid*: Record the `PubMed_ID` from the Addgene CSV (or the DOI from the literature search) as part of the design record and include it in the methods section.

## Option 1: Search Validated sgRNA Sequences (Recommended First)

### 1.1 Search for Validated sgRNAs

**IMPORTANT**: You MUST complete BOTH Method 1 AND Method 2 before proceeding to Option 2. Do not skip Method 2 even if Method 1 finds no results.

#### Method 1: Search Our Database (Fastest)

We maintain a curated database of 300+ validated sgRNA sequences from Addgene with experimental evidence.

**Location**: `resource/addgene_grna_sequences.csv` (relative to this skill directory)

**Search the database**:
```python
import pandas as pd

# Load the database
df = pd.read_csv('addgene_grna_sequences.csv')

# Search for your gene
gene_name = "TP53"
results = df[df['Target_Gene'].str.upper() == gene_name.upper()]

# Filter by species and application
results_filtered = results[
    (results['Target_Species'] == 'H. sapiens') &
    (results['Application'] == 'cut')  # or 'activate', 'RNA targeting'
]

# Display results with references
print(results_filtered[['Target_Gene', 'Target_Sequence',
                        'Plasmid_ID', 'PubMed_ID', 'Depositor']])
```

**Database columns**:
- `Target_Gene`: Gene symbol
- `Target_Species`: Organism (H. sapiens, M. musculus, etc.)
- `Target_Sequence`: 20bp sgRNA sequence (5' to 3')
- `Application`: cut (knockout), activate (CRISPRa), RNA targeting (CRISPRi)
- `Cas9_Species`: S. pyogenes, S. aureus, etc.
- `Plasmid_ID`: Addgene plasmid number
- `Plasmid_URL`: Direct link to plasmid page
- `PubMed_ID`: **Publication reference** (cite this in your work)
- `PubMed_URL`: Direct link to paper
- `Depositor`: Research lab that contributed the sequence

#### Method 2: Advanced Web Search (REQUIRED - Do Not Skip)

**CRITICAL**: Even if Method 1 found no results, you MUST perform this literature search before moving to Option 2. Many validated sgRNAs are published in literature but not in the Addgene database.

Use `advanced_web_search_claude` from `ohagent.tool.literature` to find validated sgRNAs from literature and databases:

```python
from ohagent.tool.literature import advanced_web_search_claude

# Example usage
results = advanced_web_search_claude("sgRNA TP53 validated H. sapiens experimental")
```

**Search queries to try (use multiple):**
```
"sgRNA" OR "guide RNA" "[GENE_NAME]" validated experimental
"CRISPR knockout" "[GENE_NAME]" sgRNA sequence validated
"[GENE_NAME]" sgRNA "cutting efficiency" OR "on-target"
"[GENE_NAME]" "guide sequence" CRISPR validated
```

**Example for TP53:**
```
"sgRNA" "TP53" validated "H. sapiens" experimental
"CRISPR knockout" "TP53" guide sequence validated
```

**What to search for in results:**
- Published papers with validated sgRNA sequences
- Supplementary materials containing sgRNA sequences
- Other CRISPR databases (e.g., GenScript, Horizon Discovery)
- Laboratory protocols with specific sgRNA sequences

**IMPORTANT**: Spend adequate time searching literature. Look through at least the first 10-15 search results and check supplementary materials of relevant papers.

#### What to Do with Results:

**If you find matching sgRNAs (from either method):**
1. **Record the sgRNA sequence** (20bp target sequence)
2. **Note the reference**:
   - From database: Use `PubMed_ID` to cite the original paper
   - From web search: Record the publication DOI/PubMed ID
3. **Record validation details**: Cell line, cutting efficiency, any reported off-targets


**Example result format:**
```
Gene: TP53
sgRNA sequence: GAGGTTGTGAGGCGCTGCCC
Species: H. sapiens (human)
Application: Knockout (cut)
Reference: PubMed ID 24336569 (Ran et al., 2013)
Validation: Tested in HEK293T cells, 85% cutting efficiency
```

**If no matches found in BOTH Method 1 AND Method 2:**
Only then proceed to **Option 2: Download CRISPick Dataset**



## Option 2: Download Pre-Computed sgRNAs from CRISPick

### When to Use This Option?
- No validated sgRNAs found in Addgene
- Need comprehensive coverage of a gene
- Want multiple sgRNA options with predicted scores
- Working with genome-scale screening

### 2.1 Overview of CRISPick

**CRISPick** (from Broad Institute GPP) provides pre-computed sgRNA designs for entire genomes with 238 available datasets covering:
- Human (GRCh38, GRCh37)
- Mouse (GRCm38, GRCm39)
- Dog, Cow, Monkey, and other model organisms
- Multiple Cas enzymes (SpCas9, SaCas9, AsCas12a, enAsCas12a)
  - **IMPORTANT**: AsCas12a and enAsCas12a are DIFFERENT enzymes
  - **AsCas12a**: Wild-type Acidaminococcus sp. Cas12a
  - **enAsCas12a**: Enhanced variant with improved activity
  - **Critical**: sgRNAs designed for enAsCas12a may NOT work with wild-type AsCas12a
  - Always match the dataset to your specific Cas12a variant
- Different applications (knockout, activation, inhibition)

### 2.2 Find the Download Link

**All 238 download links are available in**: `resource/CRISPick_download_links.txt` (relative to this skill directory)

#### Step 1: Understand File Naming Convention

Files are named: `sgRNA_design_{TAXID}_{GENOME}_{CAS}_{APPLICATION}_{ALGORITHM}_{SOURCE}_{DATE}.txt.gz`

**Common datasets:**

| Organism | Genome | Cas9 | Application | Search Pattern |
|-|--||-|-|
| Human | GRCh38 | SpCas9 | Knockout | `9606_GRCh38_SpyoCas9_CRISPRko` |
| Human | GRCh38 | SpCas9 | Activation | `9606_GRCh38_SpyoCas9_CRISPRa` |
| Human | GRCh38 | SaCas9 | Knockout | `9606_GRCh38_SaurCas9_CRISPRko` |
| Mouse | GRCm38 | SpCas9 | Knockout | `10090_GRCm38_SpyoCas9_CRISPRko` |
| Mouse | GRCm38 | SpCas9 | Activation | `10090_GRCm38_SpyoCas9_CRISPRa` |

**Key components:**
- **TAXID**: `9606` (Human), `10090` (Mouse), `9615` (Dog), `9913` (Cow)
- **CAS**:
  - `SpyoCas9` (SpCas9, NGG PAM)
  - `SaurCas9` (SaCas9, NNGRRT PAM)
  - `AsCas12a` (Wild-type Cas12a, TTTV PAM)
  - `enAsCas12a` (Enhanced Cas12a, TTTV PAM)
  - **WARNING**: Do NOT use AsCas12a datasets if you have enAsCas12a, and vice versa
- **APPLICATION**: `CRISPRko` (knockout), `CRISPRa` (activation), `CRISPRi` (inhibition)

#### Step 2: Find Your Download URL

```bash
# Search the download links file
grep "9606_GRCh38_SpyoCas9_CRISPRko" resource/CRISPick_download_links.txt

# Or for mouse
grep "10090_GRCm38_SpyoCas9_CRISPRko" resource/CRISPick_download_links.txt
```

#### Step 3: Download and Extract

```bash
# Copy the URL from download_links.txt, then:
wget [PASTE_URL_HERE]

# Extract the file
gunzip sgRNA_design_*.txt.gz
```

**File sizes**: Knockout (300-700 MB), Activation (50-100 MB), Summary files (1-3 MB)

### 2.4 Understanding the File Format

The `.txt` file is tab-delimited. Column names differ between knockout and activation/inhibition datasets.

**Essential Columns (All files):**
- **sgRNA Sequence**: The 20bp guide RNA sequence (5' to 3')
- **Target Gene Symbol**: Gene name (e.g., "TP53", "BRCA1")
- **Combined Rank**: Overall ranking (lower = better) - **Use this by default**
- **On-Target Rank**: Ranking by efficiency only (lower = better)
- **Off-Target Rank**: Ranking by specificity only (lower = better)
- **PAM Sequence**: The PAM sequence (e.g., "AGG", "TGG")

**Knockout-specific columns:**
- **sgRNA Cut Position (1-based)**: Genomic coordinate of cut site
- **Exon Number**: Which exon is targeted
- **Target Cut %**: Percentage of protein affected

**Activation/Inhibition-specific columns:**
- **sgRNA 'Cut' Position**: Position relative to gene
- **sgRNA 'Cut' Site TSS Offset**: Distance from transcription start site (bp)
- **DHS Score**: DNase hypersensitivity score (for CRISPRa)

### 2.5 Extract and Select sgRNAs

#### Step 1: Load Data and Filter for Your Gene

```python
import pandas as pd

# Load the dataset
df = pd.read_csv('sgRNA_design_9606_GRCh38_SpyoCas9_CRISPRko_*.txt',
                 sep='\t', low_memory=False)

# Filter for your gene
gene_name = "TP53"
gene_sgrnas = df[df['Target Gene Symbol'] == gene_name].copy()

print(f"Found {len(gene_sgrnas)} sgRNAs for {gene_name}")
```

#### Step 2: Select Top sgRNAs

**Default: Use Combined Rank (balances efficiency and specificity)**
```python
# Sort by Combined Rank (lower is better)
top_sgrnas = gene_sgrnas.nsmallest(10, 'Combined Rank')

print(top_sgrnas[['sgRNA Sequence', 'Combined Rank',
                   'Exon Number', 'sgRNA Cut Position (1-based)']])
```

**Option A: Prioritize On-Target Efficiency**
```python
# Sort by On-Target Rank (for maximum cutting efficiency)
efficient_sgrnas = gene_sgrnas.nsmallest(10, 'On-Target Rank')
```

**Option B: Prioritize Off-Target Specificity**
```python
# Sort by Off-Target Rank (for maximum specificity)
specific_sgrnas = gene_sgrnas.nsmallest(10, 'Off-Target Rank')
```

#### Step 3: Filter by Custom Criteria (Optional)

**Filter by Exon Number:**
```python
# Target specific exon (e.g., exon 5)
exon5_sgrnas = gene_sgrnas[gene_sgrnas['Exon Number'] == 5]
top_exon5 = exon5_sgrnas.nsmallest(5, 'Combined Rank')
```

**Filter by Genomic Position:**
```python
# Target specific genomic range
position_filtered = gene_sgrnas[
    (gene_sgrnas['sgRNA Cut Position (1-based)'] >= 7572000) &
    (gene_sgrnas['sgRNA Cut Position (1-based)'] <= 7575000)
]
```

**Target Early Exons for Knockout:**
```python
# Get sgRNAs from first 3 exons
early_exons = gene_sgrnas[gene_sgrnas['Exon Number'] <= 3]
top_early = early_exons.nsmallest(10, 'Combined Rank')
```

**Filter by Target Cut Percentage:**
```python
# Target sgRNAs that affect significant portion of protein
high_impact = gene_sgrnas[gene_sgrnas['Target Cut %'] <= 50]  # Cut in first 50%
top_high_impact = high_impact.nsmallest(10, 'Combined Rank')
```

#### Step 4: Select Multiple sgRNAs for Validation

```python
# Get top 4 sgRNAs from different exons for redundancy
final_selection = gene_sgrnas.sort_values('Combined Rank').groupby('Exon Number').head(1).head(4)

# Save results
final_selection.to_csv(f'{gene_name}_selected_sgRNAs.csv', index=False)

print("\nSelected sgRNAs:")
print(final_selection[['sgRNA Sequence', 'Exon Number', 'Combined Rank']])
```

### 2.6 What to Do with Results

**Once you have selected sgRNAs:**
1. Choose **3-4 sgRNAs** (use Combined_Rank by default)

**If dataset doesn't cover your gene or organism:**
Proceed to **Option 3: De Novo sgRNA Design**



## Option 3: General sgRNA Design Guidelines (Last Resort)

### When to Use This Option?
- Gene not covered in CRISPick datasets
- Non-model organism
- Custom design requirements

### General Design Rules

#### Essential Requirements:
1. **Length**:
   - 20 bp for SpCas9 and SaCas9
   - 23-25 bp for Cas12a variants (AsCas12a, enAsCas12a)
2. **PAM sequence**:
   - **SpCas9**: Requires **NGG** immediately after target (3' end)
   - **SaCas9**: Requires **NNGRRT** immediately after target (3' end)
   - **AsCas12a** (wild-type): Requires **TTTV** before target (5' end)
   - **enAsCas12a** (enhanced): Requires **TTTV** before target (5' end)
   - **CRITICAL**: Guides designed for enAsCas12a may not work with wild-type AsCas12a due to different activity profiles
3. **GC content**: 40-60% is optimal
4. **Avoid**:
   - TTTT sequences (terminates transcription)
   - Long runs of same nucleotide (>4 repeats)

#### Target Location:
- **For knockout**: Target early exons (first 50% of gene)
- **For activation**: Target -200 to +1 bp from transcription start site (TSS)
- **For inhibition**: Target -50 to +300 bp from TSS

#### Best Practices:
- **Test 3-4 different sgRNAs** per target gene
- Select sgRNAs with high efficiency scores (>0.5) and minimal off-targets
- Validate experimentally with Sanger sequencing



## Quick Start Examples

### Example 1: Knockout TP53 in Human Cells

**Step 1**: Check Addgene
```python
df = pd.read_csv('addgene_grna_sequences.csv')
tp53_results = df[(df['Target_Gene'] == 'TP53') &
                  (df['Target_Species'] == 'H. sapiens') &
                  (df['Application'] == 'cut')]
# Result: Found 0 entries -> Proceed to Option 2
```

**Step 2**: Download CRISPick dataset
```bash
# Download human GRCh38 SpCas9 knockout dataset
wget https://portals.broadinstitute.org/gppx/public/sgrna_design/api/downloads/\
sgRNA_design_9606_GRCh38_SpyoCas9_CRISPRko_RS3seq-Chen2013+RS3target_NCBI_20241104.txt.gz

gunzip sgRNA_design_9606_GRCh38_SpyoCas9_CRISPRko_*.txt.gz
```

**Step 3**: Extract TP53 sgRNAs
```python
df = pd.read_csv('sgRNA_design_9606_GRCh38_SpyoCas9_CRISPRko_*.txt', sep='\t')
tp53 = df[df['Gene_Symbol'] == 'TP53']
top_sgrnas = tp53[
    (tp53['sgRNA_score'] > 0.6) &
    (tp53['Off_target_stringency'] > 0.5)
].sort_values('sgRNA_score', ascending=False).head(4)

print(top_sgrnas[['sgRNA_sequence', 'sgRNA_score', 'Exon_ID']])
```

### Example 2: Activate OCT4 in Human iPSCs

**Step 1**: Check Addgene
```python
oct4_results = df[(df['Target_Gene'] == 'OCT4') &
                  (df['Application'] == 'activate')]
# Found 1 validated sgRNA!
print(oct4_results['Target_Sequence'].values[0])
# Use this sequence
```



**Remember**: Always start with validated sequences (Option 1), then move to pre-computed designs (Option 2), and only use de novo design (Option 3) when necessary. Testing 3-4 sgRNAs per gene is standard practice regardless of prediction scores.

## References

- Addgene CRISPR sgRNA reference sequences: https://www.addgene.org/crispr/reference/grna-sequence/
- CRISPick (Broad Institute GPP) pre-computed sgRNA designs: https://portals.broadinstitute.org/gppx/crispick/public
- Sanson KR, Hanna RE, Hegde M, et al. "Optimized libraries for CRISPR-Cas9 genetic screens with multiple modalities." Nat Commun. 2018;9(1):5416. PMID: 30575746. https://doi.org/10.1038/s41467-018-07901-8
- DeWeirdt PC, Sanson KR, Sangree AK, et al. "Optimization of AsCas12a for combinatorial genetic screens in human cells." Nat Biotechnol. 2021;39(1):94-104. PMID: 32661438. https://doi.org/10.1038/s41587-020-0600-6
- Doench JG, Fusi N, Sullender M, et al. "Optimized sgRNA design to maximize activity and minimize off-target effects of CRISPR-Cas9." Nat Biotechnol. 2016;34(2):184-191. https://doi.org/10.1038/nbt.3437
- Ran FA, Hsu PD, Wright J, et al. "Genome engineering using the CRISPR-Cas9 system." Nat Protoc. 2013;8(11):2281-2308. PMID: 24336569. https://doi.org/10.1038/nprot.2013.143
- Zetsche B, Heidenreich M, Mohanraju P, et al. "Multiplex gene editing by CRISPR-Cpf1 using a single crRNA array." Nat Biotechnol. 2017;35(1):31-34. https://doi.org/10.1038/nbt.3737
