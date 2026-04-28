---
name: "snpeff-variant-annotation"
description: "Annotate and filter VCF variants with SnpEff and SnpSift. SnpEff predicts functional effects (HIGH/MODERATE/LOW/MODIFIER), genes, transcripts, AA changes, HGVS; SnpSift filters and adds ClinVar/dbSNP. Java CLI with Python subprocess integration. Use ANNOVAR for multi-database annotation; Ensembl VEP for REST API; SnpEff for fast CLI with pre-built genomes."
license: "MIT"
---

# SnpEff + SnpSift — Variant Annotation and Filtering

## Overview

SnpEff annotates variants in VCF files by predicting their functional consequences: impact level (HIGH, MODERATE, LOW, MODIFIER), affected gene and transcript, amino acid change, and HGVS notation. SnpSift is the companion tool for filtering, sorting, and enriching annotated VCFs with external databases such as ClinVar and dbSNP. Together they form a fast, self-contained pipeline for going from raw variant calls to biologically interpretable, filtered variant sets. Both tools are Java-based and are invoked from the command line or Python subprocess; pre-built genome databases (hg38, GRCh37, mm10, and 100+ others) are downloaded with a single command.

## When to Use

- Annotating VCF files from GATK, DeepVariant, bcftools, or other callers with predicted gene-level functional consequences before manual review or downstream filtering
- Prioritizing clinically relevant variants by filtering to HIGH-impact stop-gain, frameshift, and splice-site variants for rare disease or cancer gene panel analysis
- Adding ClinVar pathogenicity classifications and dbSNP rsIDs to a variant set for cross-study comparison or clinical reporting
- Extracting structured, tab-delimited fields (gene, protein change, AF, ClinSig) from annotated VCFs into pandas DataFrames for statistical analysis
- Identifying candidate de novo variants in trio analysis by combining allele frequency thresholds, impact filters, and parent VCF exclusion
- Use **ANNOVAR** instead when comprehensive annotation from multiple databases (gnomAD, CADD, SpliceAI) in a single run is required
- Use **Ensembl VEP** instead when REST API access or VEP-specific plugins (CADD, LOFTEE, SpliceRegion) are needed

## Prerequisites

- **Java**: Java 11+ (required for SnpEff 5.x)
- **SnpEff JAR**: downloaded from the SnpEff releases page or via conda/bioconda
- **Python packages** (optional): `cyvcf2`, `pandas`, `matplotlib`, `seaborn` for Python-side parsing and visualization
- **Reference genome database**: downloaded once per assembly (e.g., `hg38`, `GRCh37`, `mm10`)

> **Check before installing**: The tool may already be available in the current environment (e.g., inside a `pixi` / `conda` env). Run `command -v snpEff` first and skip the install commands below if it returns a path. When running inside a pixi project, invoke the tool via `pixi run snpEff` rather than bare `snpEff`.

```bash
# Download SnpEff JAR
wget https://snpeff.blob.core.windows.net/versions/snpEff_latest_core.zip
unzip snpEff_latest_core.zip
# JAR is at snpEff/snpEff.jar and snpEff/SnpSift.jar

# Or via conda (recommended for reproducibility)
conda install -c bioconda snpeff

# Verify
java -jar snpEff/snpEff.jar -version
# SnpEff 5.2a (build 2024-02-06)

# Install Python packages for downstream parsing
pip install cyvcf2 pandas matplotlib seaborn
```

## Quick Start

```bash
# 1. Download the hg38 genome database (one-time setup, ~1 GB)
java -jar snpEff/snpEff.jar download hg38

# 2. Annotate variants
java -jar snpEff/snpEff.jar \
    -v hg38 \
    input.vcf.gz \
    > annotated.vcf

# 3. Filter to HIGH-impact variants
java -jar snpEff/SnpSift.jar filter \
    "ANN[*].IMPACT = 'HIGH'" \
    annotated.vcf \
    > high_impact.vcf

echo "Done. Check snpEff_summary.html and snpEff_genes.txt for QC stats."
```

## Workflow

### Step 1: Install SnpEff and Download Genome Database

Download and verify the pre-built genome database for your target assembly. Databases include transcript models from Ensembl or UCSC and are built into SnpEff's local cache directory (`~/.snpEff/data/` or `snpEff/data/`).

```bash
# List all available databases (grep for your assembly)
java -jar snpEff/snpEff.jar databases | grep -i "GRCh38\|hg38"

# Download hg38 (Homo sapiens, GRCh38)
java -jar snpEff/snpEff.jar download hg38

# Download GRCh37 (older assemblies still widely used in clinical pipelines)
java -jar snpEff/snpEff.jar download GRCh37.75

# Download mouse mm10
java -jar snpEff/snpEff.jar download mm10

# List installed databases
ls ~/.snpEff/data/
```

### Step 2: Annotate VCF with Functional Effects

Run SnpEff annotation to add `ANN` INFO fields to each variant. The `ANN` field encodes pipe-separated annotations per transcript: `Allele|Effect|Impact|Gene|GeneID|Feature|FeatureID|BioType|Rank|HGVS.c|HGVS.p|cDNA_pos|CDS_pos|Protein_pos|Distance|Errors`.

```bash
# Annotate a gzipped VCF (outputs to stdout, pipe or redirect)
java -Xmx8g -jar snpEff/snpEff.jar \
    -v \
    -stats snpeff_summary.html \
    hg38 \
    input.vcf.gz \
    > annotated.vcf

# Compress and index the output for downstream tools
bgzip annotated.vcf
tabix -p vcf annotated.vcf.gz

echo "Annotated variants in annotated.vcf.gz"
echo "QC report: snpeff_summary.html"
echo "Gene table: snpEff_genes.txt"
```

### Step 3: Filter HIGH-Impact Variants with SnpSift

SnpSift `filter` evaluates boolean expressions over INFO and FORMAT fields. The `ANN[*]` syntax iterates over all transcript annotations for each variant — any matching transcript qualifies the variant.

```bash
# Filter for HIGH-impact variants only (stop-gain, frameshift, splice-site)
java -jar snpEff/SnpSift.jar filter \
    "ANN[*].IMPACT = 'HIGH'" \
    annotated.vcf.gz \
    > high_impact.vcf

# Filter HIGH or MODERATE impact and allele frequency < 1%
# (requires AF in INFO field, e.g., from GATK or gnomAD annotation)
java -jar snpEff/SnpSift.jar filter \
    "(ANN[*].IMPACT = 'HIGH' | ANN[*].IMPACT = 'MODERATE') & (AF < 0.01)" \
    annotated.vcf.gz \
    > rare_functional.vcf

# Count filtered variants
grep -v "^#" high_impact.vcf | wc -l
```

### Step 4: Add ClinVar and dbSNP Annotations

SnpSift `annotate` transfers INFO fields from a reference VCF (ClinVar, dbSNP) to the target VCF by matching on chromosome and position. Download ClinVar and dbSNP VCFs from NCBI FTP before running.

```bash
# Download reference databases (one-time setup)
# ClinVar (GRCh38)
wget https://ftp.ncbi.nlm.nih.gov/pub/clinvar/vcf_GRCh38/clinvar.vcf.gz
wget https://ftp.ncbi.nlm.nih.gov/pub/clinvar/vcf_GRCh38/clinvar.vcf.gz.tbi

# dbSNP (GRCh38, b156 or later)
wget https://ftp.ncbi.nlm.nih.gov/snp/latest_release/VCF/GCF_000001405.40.gz
wget https://ftp.ncbi.nlm.nih.gov/snp/latest_release/VCF/GCF_000001405.40.gz.tbi

# Annotate with ClinVar CLNSIG and CLNDN fields
java -jar snpEff/SnpSift.jar annotate \
    -info CLNSIG,CLNDN,CLNREVSTAT \
    clinvar.vcf.gz \
    annotated.vcf.gz \
    > annotated_clinvar.vcf

# Annotate with dbSNP rsIDs (adds RS field to INFO)
java -jar snpEff/SnpSift.jar annotate \
    GCF_000001405.40.gz \
    annotated_clinvar.vcf \
    > annotated_full.vcf

echo "ClinVar + dbSNP annotations added to annotated_full.vcf"
```

### Step 5: Extract Fields to Tab-Delimited Output

SnpSift `extractFields` converts VCF annotations into a flat table. Use `ANN[0]` to take the first (most severe) transcript annotation, or `ANN[*]` to expand all transcripts.

```bash
# Extract key fields: CHROM, POS, REF, ALT, impact, gene, protein change, AF, ClinVar sig
java -jar snpEff/SnpSift.jar extractFields \
    -s "," \
    -e "." \
    annotated_full.vcf \
    CHROM POS REF ALT \
    "ANN[0].GENE" \
    "ANN[0].EFFECT" \
    "ANN[0].IMPACT" \
    "ANN[0].HGVS_P" \
    "ANN[0].HGVS_C" \
    "ANN[0].FEATUREID" \
    AF \
    CLNSIG \
    CLNDN \
    > variants_table.tsv

# Preview
head -3 variants_table.tsv
# CHROM  POS   REF  ALT  ANN[0].GENE  ANN[0].EFFECT            ANN[0].IMPACT  ...
# chr1   69511 A    G    OR4F5        synonymous_variant        LOW            ...
# chr1   925952 G   A    SAMD11       missense_variant          MODERATE       ...
```

### Step 6: Parse Annotated VCF in Python with cyvcf2

Use `cyvcf2` (or `PyVCF2`) for programmatic VCF parsing in Python. `cyvcf2` wraps htslib and is significantly faster than pure-Python parsers.

```python
import re
import pandas as pd
from cyvcf2 import VCF

records = []

for variant in VCF("annotated_full.vcf.gz"):
    ann_field = variant.INFO.get("ANN")
    if ann_field is None:
        continue

    # Take the first (most severe) annotation transcript
    first_ann = ann_field.split(",")[0].split("|")
    # ANN field columns (0-indexed): allele, effect, impact, gene, gene_id,
    # feature_type, feature_id, biotype, rank, hgvs_c, hgvs_p, ...
    effect   = first_ann[1] if len(first_ann) > 1 else "."
    impact   = first_ann[2] if len(first_ann) > 2 else "."
    gene     = first_ann[3] if len(first_ann) > 3 else "."
    hgvs_p   = first_ann[10] if len(first_ann) > 10 else "."

    records.append({
        "chrom":   variant.CHROM,
        "pos":     variant.POS,
        "ref":     variant.REF,
        "alt":     ",".join(variant.ALT),
        "gene":    gene,
        "effect":  effect,
        "impact":  impact,
        "hgvs_p":  hgvs_p,
        "af":      variant.INFO.get("AF", None),
        "clnsig":  variant.INFO.get("CLNSIG", "."),
    })

df = pd.DataFrame(records)
print(f"Total variants: {len(df)}")
print(df["impact"].value_counts())
# HIGH        342
# MODERATE   4218
# LOW        8903
# MODIFIER  51204
```

### Step 7: Summary Statistics and Consequence Visualization

Generate a bar chart of variant consequences and a count summary by impact tier to prioritize review.

```python
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns

# Consequence counts by impact (df from Step 6)
impact_order = ["HIGH", "MODERATE", "LOW", "MODIFIER"]
impact_counts = df["impact"].value_counts().reindex(impact_order, fill_value=0)

# Top 15 effects within HIGH and MODERATE
top_effects = (
    df[df["impact"].isin(["HIGH", "MODERATE"])]
    ["effect"]
    .str.replace("_", " ")
    .value_counts()
    .head(15)
)

fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Left: impact tier counts
impact_counts.plot(kind="bar", ax=axes[0],
                   color=["#d62728", "#ff7f0e", "#2ca02c", "#aec7e8"],
                   edgecolor="black")
axes[0].set_title("Variant Counts by Impact Tier", fontsize=13)
axes[0].set_xlabel("Impact")
axes[0].set_ylabel("Count")
axes[0].yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x):,}"))
axes[0].tick_params(axis="x", rotation=0)

# Right: top HIGH/MODERATE effects
top_effects.plot(kind="barh", ax=axes[1], color="#1f77b4", edgecolor="black")
axes[1].set_title("Top HIGH/MODERATE Variant Effects", fontsize=13)
axes[1].set_xlabel("Count")
axes[1].invert_yaxis()

plt.tight_layout()
plt.savefig("variant_consequence_summary.png", dpi=150, bbox_inches="tight")
plt.show()
print("Saved: variant_consequence_summary.png")

# Print HIGH-impact gene table
high_genes = (
    df[df["impact"] == "HIGH"]["gene"]
    .value_counts()
    .head(20)
    .rename("n_high_variants")
)
print("\nTop genes with HIGH-impact variants:")
print(high_genes.to_string())
```

## Key Parameters

| Parameter | Default | Range / Options | Effect |
|-----------|---------|-----------------|--------|
| `-Xmx` (JVM heap) | JVM default (~256 MB) | `4g`–`32g` | Prevents `OutOfMemoryError` for large WGS VCFs; set to ~4–8 GB per run |
| `-v` (verbose) | off | flag | Prints per-chromosome progress and summary counts to stderr |
| `-stats` | `snpEff_summary.html` | any `.html` path | Writes interactive QC summary with consequence pie charts and gene tables |
| `-noStats` | off | flag | Disables HTML report generation (faster for batch runs) |
| `-canon` | off | flag | Annotates only the canonical transcript per gene (reduces ANN field size) |
| `-maxAF` | disabled | `0.0`–`1.0` | Skip annotation for variants with population AF above threshold (requires gnomAD in database) |
| `filter` expression (SnpSift) | — | boolean expression | `ANN[*].IMPACT = 'HIGH'`, `AF < 0.001 & DP > 10`, `CLNSIG has 'Pathogenic'` |
| `-s` separator (extractFields) | tab | any string | Field separator in output table; use `","` for CSV |
| `-e` empty value (extractFields) | empty | any string | Placeholder for missing fields; use `"."` for consistency with VCF convention |

## Key Concepts

### ANN Field Structure

Each variant's `ANN` INFO field contains one annotation per predicted transcript consequence, separated by commas. Each annotation is a pipe-delimited string with 16 fields:

```
ANN=T|missense_variant|MODERATE|BRCA1|ENSG00000012048|transcript|ENST00000357654|protein_coding|12/23|c.1234A>T|p.Lys412Met|1234|1234|412|.|
```

The first annotation (index 0) is the most severe consequence. Multiple annotations arise when a variant affects multiple transcripts or genes.

### Impact Levels

| Impact | Variant Types | Typical Priority |
|--------|--------------|-----------------|
| `HIGH` | Stop-gained, frameshift, splice-donor/acceptor, start-lost | Disease candidate; always review |
| `MODERATE` | Missense, in-frame indel, splice-region | Pathogenicity depends on conservation and domain context |
| `LOW` | Synonymous, stop-retained, start-retained | Rarely causal; useful as controls |
| `MODIFIER` | Intronic, intergenic, UTR, downstream | Background; filter out for most analyses |

### HGVS Notation in ANN

SnpEff provides both cDNA (`HGVS.c`, e.g., `c.1234A>T`) and protein (`HGVS.p`, e.g., `p.Lys412Met`) notation. HGVS fields are empty (`.`) for non-coding variants. The `FEATUREID` field contains the Ensembl or RefSeq transcript ID enabling cross-database lookup.

### SnpSift Filter Syntax

SnpSift filter expressions support comparison operators (`=`, `!=`, `<`, `>`), logical operators (`&`, `|`, `!`), and the `has` operator for substring matching. Use `ANN[*]` to match any annotation transcript, `ANN[0]` for first only:

```
# Compound filter: rare + damaging + not in ClinVar benign
(AF < 0.001) & (ANN[*].IMPACT = 'HIGH' | ANN[*].IMPACT = 'MODERATE') & !(CLNSIG has 'Benign')
```

## Common Recipes

### Recipe: Filter De Novo Candidates (Trio Analysis)

Identify rare, functionally damaging variants in a proband that are absent from both parents. Combine allele frequency filtering, impact filtering, and VCF subtraction using SnpSift.

```bash
# Step 1: Annotate proband VCF
java -jar snpEff/snpEff.jar -v hg38 proband.vcf.gz > proband_ann.vcf

# Step 2: Filter rare HIGH/MODERATE variants not in either parent
# Requires proband, mother, and father VCFs to be jointly genotyped or
# use SnpSift filter on a multi-sample VCF
java -jar snpEff/SnpSift.jar filter \
    "(ANN[*].IMPACT = 'HIGH' | ANN[*].IMPACT = 'MODERATE') \
     & (AF < 0.001 | AF = '.') \
     & (GEN[proband].GT != './.') \
     & (GEN[mother].GT = '0/0' | GEN[mother].GT = '0|0') \
     & (GEN[father].GT = '0/0' | GEN[father].GT = '0|0')" \
    proband_ann.vcf \
    > denovo_candidates.vcf

# Step 3: Extract to table for review
java -jar snpEff/SnpSift.jar extractFields \
    denovo_candidates.vcf \
    CHROM POS REF ALT "ANN[0].GENE" "ANN[0].EFFECT" "ANN[0].IMPACT" \
    "ANN[0].HGVS_P" AF CLNSIG \
    > denovo_candidates.tsv

echo "De novo candidates: $(grep -v '^CHROM' denovo_candidates.tsv | wc -l)"
```

### Recipe: Extract Protein-Changing Variants to pandas DataFrame

Load an annotated VCF directly into pandas using SnpSift `extractFields` output for downstream statistical or ML analysis.

```python
import subprocess
import io
import pandas as pd

VCF_IN   = "annotated_full.vcf.gz"
SNPSIFT  = "snpEff/SnpSift.jar"

# Run SnpSift extractFields via subprocess and capture stdout
cmd = [
    "java", "-jar", SNPSIFT, "extractFields",
    "-s", ",", "-e", ".",
    VCF_IN,
    "CHROM", "POS", "REF", "ALT",
    "ANN[0].GENE", "ANN[0].EFFECT", "ANN[0].IMPACT",
    "ANN[0].HGVS_P", "ANN[0].HGVS_C", "ANN[0].FEATUREID",
    "AF", "DP", "CLNSIG", "CLNDN",
]
result = subprocess.run(cmd, capture_output=True, text=True, check=True)
df = pd.read_csv(io.StringIO(result.stdout), sep="\t")
df.columns = [c.replace("ANN[0].", "") for c in df.columns]  # clean column names

# Keep protein-changing variants only
protein_changing = df[df["IMPACT"].isin(["HIGH", "MODERATE"])].copy()
protein_changing["AF"] = pd.to_numeric(protein_changing["AF"], errors="coerce")
protein_changing["DP"] = pd.to_numeric(protein_changing["DP"], errors="coerce")

print(f"Protein-changing variants: {len(protein_changing)}")
print(protein_changing[["GENE", "EFFECT", "IMPACT", "HGVS_P", "AF"]].head(10).to_string(index=False))
```

### Recipe: Build a Custom Genome Database

When working with a non-standard organism or custom assembly, build a SnpEff database from a FASTA + GTF file.

```bash
# 1. Set up directory structure under SnpEff's data directory
GENOME_NAME="my_organism"
mkdir -p snpEff/data/${GENOME_NAME}
cp my_genome.fa snpEff/data/${GENOME_NAME}/sequences.fa
cp my_annotation.gtf snpEff/data/${GENOME_NAME}/genes.gtf

# 2. Add genome entry to snpEff.config
echo "${GENOME_NAME}.genome : My Organism" >> snpEff/snpEff.config

# 3. Build the database
java -jar snpEff/snpEff.jar build \
    -gtf22 \
    -v \
    ${GENOME_NAME}

# 4. Verify
java -jar snpEff/snpEff.jar dump ${GENOME_NAME} | head -20
echo "Custom database built for ${GENOME_NAME}"
```

## Expected Outputs

| File | Format | Contents |
|------|--------|----------|
| `annotated.vcf.gz` | bgzipped VCF | Original variants with `ANN` INFO field; one record per variant |
| `snpEff_summary.html` | HTML | Interactive QC report: consequence pie charts, top genes, transition/transversion ratio |
| `snpEff_genes.txt` | TSV | Per-gene counts of variants by consequence type |
| `high_impact.vcf` | VCF | Subset of variants with `ANN[*].IMPACT = 'HIGH'` |
| `annotated_clinvar.vcf` | VCF | Annotated VCF enriched with `CLNSIG`, `CLNDN`, `CLNREVSTAT` from ClinVar |
| `variants_table.tsv` | TSV | Flat table of extracted fields; one row per variant (first transcript) |
| `variant_consequence_summary.png` | PNG | Bar charts of impact tiers and top consequence types |

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `OutOfMemoryError` during annotation | Default JVM heap too small for WGS VCFs | Add `-Xmx8g` (or `-Xmx16g`) before `-jar`: `java -Xmx8g -jar snpEff.jar ...` |
| `ERROR_CHROMOSOME_NOT_FOUND` for every variant | Chromosome naming mismatch (e.g., `chr1` vs `1`) | Pass `-noCheckChr` flag; or rename contigs in VCF with `bcftools annotate --rename-chrs` |
| `Database not found` error | Genome database not downloaded | Run `java -jar snpEff.jar download hg38`; check `snpEff/data/` directory exists |
| Empty `ANN` field on all variants | Wrong genome database version relative to VCF reference | Confirm VCF uses the same assembly as the database (e.g., hg38 vs GRCh38 — use `GRCh38.86` for Ensembl builds) |
| SnpSift filter returns zero variants | Filter expression syntax error or wrong field name | Test expression on small VCF; check `ANN[*].IMPACT` vs `ANN[0].IMPACT`; wrap expression in quotes |
| `CLNSIG` field missing after `snpSift annotate` | ClinVar VCF not indexed, or contig mismatch | Run `tabix -p vcf clinvar.vcf.gz` before annotating; ensure chromosome names match |
| `extractFields` output missing HGVS_P column | Variant is non-coding or affects UTR/intron | Use `-e "."` flag to fill empty fields; filter to coding variants first |
| Very large `ANN` field (thousands of transcripts) | Variant in a region with many overlapping transcripts | Add `-canon` flag to annotate only canonical transcripts, or use `ANN[0]` in downstream filters |

## References

- [SnpEff Documentation](https://pcingola.github.io/SnpEff/) — comprehensive usage guide, ANN field specification, filter syntax
- [SnpEff GitHub Repository](https://github.com/pcingola/SnpEff) — source code, issue tracker, release notes
- Cingolani P, et al. (2012) "A program for annotating and predicting the effects of single nucleotide polymorphisms, SnpEff: SNPs in the genome of Drosophila melanogaster strain w1118." *Fly* 6(2):80–92. doi:[10.4161/fly.19695](https://doi.org/10.4161/fly.19695)
- [ClinVar VCF FTP](https://ftp.ncbi.nlm.nih.gov/pub/clinvar/) — ClinVar VCF files by assembly
- [cyvcf2 Documentation](https://brentp.github.io/cyvcf2/) — Python VCF parsing library used in Step 6
