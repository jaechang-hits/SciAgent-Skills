---
name: gget-genomic-databases
description: "Unified CLI/Python interface to 20+ genomic databases. Gene lookups (Ensembl search/info/seq), BLAST/BLAT, AlphaFold, Enrichr enrichment, OpenTargets disease/drug, CELLxGENE single-cell, cBioPortal/COSMIC cancer, ARCHS4 expression. Spans genomics, proteomics, disease. For batch/advanced BLAST use biopython; for multi-DB Python SDK use bioservices."
license: BSD-2-Clause
---

# gget — Unified Genomic Database Access

## Overview

gget is a command-line and Python package providing unified access to 20+ genomic databases and analysis methods. Query gene information, sequences, protein structures, expression data, and disease associations through a consistent interface. All modules work as both CLI tools and Python functions, returning DataFrames (Python) or JSON/CSV (CLI).

## When to Use

- Looking up gene information (names, IDs, descriptions) across species from Ensembl
- Retrieving nucleotide or protein sequences for Ensembl gene/transcript IDs
- Running BLAST or BLAT searches against standard reference databases
- Predicting protein 3D structures with AlphaFold2 from amino acid sequences
- Performing gene set enrichment analysis (GO, KEGG, disease terms) via Enrichr
- Querying single-cell RNA-seq datasets from CELLxGENE Census
- Finding disease and drug associations for a gene target via OpenTargets
- Downloading Ensembl reference genomes and annotations for a species
- Finding cancer mutations and genomic alterations via cBioPortal or COSMIC
- Getting tissue expression and correlated genes from ARCHS4
- For batch processing or advanced BLAST parameters, use `biopython` instead
- For programmatic multi-database workflows with rate limiting, use `bioservices` instead

## Prerequisites

- **Python packages**: `gget`
- **Optional setup**: Some modules require `gget setup <module>` before first use (alphafold, cellxgene, elm, gpt)
- **Environment**: Clean virtual environment recommended to avoid dependency conflicts
- **API notes**: gget queries remote databases — rate-limit large batch queries with `time.sleep()`. Databases update biweekly; keep gget updated. Max ~1000 Ensembl IDs per `gget.info()` call

```bash
pip install gget

# Optional: setup modules that need additional dependencies
gget setup alphafold   # ~4GB model parameters, requires OpenMM
gget setup cellxgene   # cellxgene-census package
gget setup elm         # local ELM database
```

## Quick Start

```python
import gget

# Search for genes by keyword
results = gget.search(["BRCA1", "tumor suppressor"], species="homo_sapiens")
print(f"Found {len(results)} genes")

# Get detailed gene information (Ensembl + UniProt + NCBI)
info = gget.info(["ENSG00000012048"])
print(f"Gene: {info.iloc[0]['primary_gene_name']}")

# Enrichment analysis on a gene list
enrichment = gget.enrichr(["ACE2", "AGT", "AGTR1"], database="ontology")
print(f"Enriched terms: {len(enrichment)}")
```

## Core API

### Module 1: Reference & Gene Search (ref, search, info, seq)

Query Ensembl for gene references, search by keywords, retrieve gene metadata, and fetch sequences.

```python
import gget

# Search for genes by keyword
results = gget.search(["BRCA1", "tumor suppressor"], species="homo_sapiens")
print(f"Found {len(results)} genes")
print(results[["ensembl_id", "gene_name", "biotype"]].head())

# Get detailed gene information (Ensembl + UniProt + NCBI)
info = gget.info(["ENSG00000012048", "ENSG00000139618"])
print(f"Gene info columns: {list(info.columns)}")
```

```python
import gget

# Retrieve sequences
nucleotide_seqs = gget.seq(["ENSG00000012048"])
protein_seqs = gget.seq(["ENSG00000012048"], translate=True, isoforms=True)
print(f"Retrieved {len(protein_seqs)} isoform sequences")

# Download reference genome files (specify release for reproducibility)
ref_links = gget.ref("homo_sapiens", which="gtf", release=112)
print(f"GTF download link: {ref_links}")
```

### Module 2: Sequence Alignment (blast, blat, muscle, diamond)

BLAST/BLAT remote searches, multiple sequence alignment, and fast local alignment.

```python
import gget
import time

# BLAST against SwissProt (remote API — add delay for batch queries)
blast_results = gget.blast(
    "MKWMFKEDHSLEHRCVESAKIRAKYPDRVPVIVEKVSGSQIVDIDKRKYLVPSDITVAQFMWIIRKRIQLPSEKAIFLFVDKTVPQSR",
    database="swissprot", limit=10
)
print(f"Top hit: {blast_results.iloc[0]['Description']}, E-value: {blast_results.iloc[0]['e-value']}")
time.sleep(2)  # Rate-limit between BLAST queries

# BLAT — find genomic position (UCSC)
blat_results = gget.blat("ATCGATCGATCGATCGATCG", assembly="human")
print(f"Genomic location: chr{blat_results.iloc[0]['chromosome']}:{blat_results.iloc[0]['start']}")
```

```python
import gget

# Multiple sequence alignment with Muscle5
aligned = gget.muscle("sequences.fasta", save=True)

# Fast local alignment with DIAMOND (local, no rate limit needed)
diamond_results = gget.diamond(
    "GGETISAWESQME",
    reference="reference.fasta",
    sensitivity="very-sensitive",
    threads=4
)
print(f"Alignments found: {len(diamond_results)}")
```

### Module 3: Protein Structure (pdb, alphafold, elm)

Download PDB structures, predict structures with AlphaFold2, find linear motifs.

```python
import gget

# Download PDB structure
pdb_data = gget.pdb("7S7U", save=True)

# Predict structure with AlphaFold2 (requires gget setup alphafold)
structure = gget.alphafold(
    "MKWMFKEDHSLEHRCVESAKIRAKYPDRVPVIVEKVSGSQIVDIDKRKYLVPSDITVAQFMWIIRKRIQLPSEKAIFLFVDKTVPQSR",
    plot=True, show_sidechains=True
)
print("Structure prediction complete, PDB file saved")
```

```python
import gget

# Find Eukaryotic Linear Motifs (requires gget setup elm)
ortholog_df, regex_df = gget.elm("LIAQSIGQASFV")
print(f"Ortholog motifs: {len(ortholog_df)}, Regex motifs: {len(regex_df)}")
```

### Module 4: Expression & Correlation (archs4, cellxgene, bgee)

Gene expression, tissue expression, correlated genes, single-cell data.

```python
import gget

# Tissue expression from ARCHS4
tissue_expr = gget.archs4("ACE2", which="tissue")
print(f"Expression across {len(tissue_expr)} tissues")

# Correlated genes from ARCHS4
correlated = gget.archs4("ACE2", which="correlation")
print(f"Top correlated gene: {correlated.iloc[0]['gene_symbol']}")
```

```python
import gget

# Single-cell data from CELLxGENE (requires gget setup cellxgene)
adata = gget.cellxgene(
    gene=["ACE2", "TMPRSS2"],
    tissue="lung",
    cell_type="epithelial cell",
    census_version="2023-07-25"  # pin version for reproducibility
)
print(f"Cells: {adata.n_obs}, Genes: {adata.n_vars}")

# Orthologs and expression from Bgee
orthologs = gget.bgee("ENSG00000169194", type="orthologs")
print(f"Orthologs in {len(orthologs)} species")
```

### Module 5: Disease & Drug Associations (opentargets, enrichr)

Disease associations, drug targets, enrichment analysis.

```python
import gget

# Disease associations from OpenTargets
diseases = gget.opentargets("ENSG00000169194", resource="diseases", limit=10)
print(f"Associated diseases: {len(diseases)}")

# Drug associations
drugs = gget.opentargets("ENSG00000169194", resource="drugs", limit=10)
print(f"Associated drugs: {len(drugs)}")

# OpenTargets resources: diseases, drugs, tractability, pharmacogenetics,
#   expression, depmap, interactions
```

```python
import gget

# Enrichment analysis via Enrichr
# Database shortcuts: 'pathway' (KEGG), 'transcription' (ChEA),
#   'ontology' (GO_BP), 'diseases_drugs' (GWAS), 'celltypes' (PanglaoDB)
enrichment = gget.enrichr(
    ["ACE2", "AGT", "AGTR1", "TMPRSS2", "DPP4"],
    database="ontology"
)
print(f"Enriched terms: {len(enrichment)}")
print(enrichment[["Term", "Adjusted P-value"]].head())
```

### Module 6: Cancer Genomics (cbio, cosmic)

Cancer mutations, copy number alterations, and somatic mutation databases.

```python
import gget

# Search cBioPortal studies
studies = gget.cbio_search(["breast", "lung"])
print(f"Studies found: {len(studies)}")

# Plot cancer genomics heatmap
gget.cbio_plot(
    ["msk_impact_2017"],
    ["AKT1", "ALK", "BRAF"],
    stratification="tissue",
    variation_type="mutation_occurrences"
)
```

```python
import gget

# COSMIC: requires account + local database download
# First-time: gget.cosmic(searchterm="", download_cosmic=True,
#   email="user@example.com", password="xxx", cosmic_project="cancer")
cosmic_results = gget.cosmic("EGFR", cosmic_tsv_path="cosmic_data.tsv", limit=10)
print(f"COSMIC mutations: {len(cosmic_results)}")
```

### Module 7: Mutation Generation & Utilities (mutate, setup)

Generate mutated sequences and manage module dependencies.

```python
import gget
import pandas as pd

# Generate mutated sequences from mutation annotations
mutations_df = pd.DataFrame({
    "seq_ID": ["seq1", "seq1"],
    "mutation": ["c.4G>T", "c.10del"]
})
mutated = gget.mutate(["ATCGCTAAGCTGATCG"], mutations=mutations_df)
print(f"Generated {len(mutated)} mutated sequences")
```

## Key Concepts

### Module Overview

gget organizes 20+ modules by domain. Python interface uses `gget.<module>()`:

| Domain | Modules | Primary Database |
|--------|---------|-----------------|
| Gene reference | `ref`, `search`, `info`, `seq` | Ensembl, UniProt, NCBI |
| Sequence alignment | `blast`, `blat`, `muscle`, `diamond` | NCBI BLAST, UCSC, local |
| Protein structure | `pdb`, `alphafold`, `elm` | RCSB PDB, AlphaFold2, ELM |
| Expression | `archs4`, `cellxgene`, `bgee` | ARCHS4, CZ CELLxGENE, Bgee |
| Disease/drugs | `opentargets`, `enrichr` | OpenTargets, Enrichr |
| Cancer | `cbio`, `cosmic` | cBioPortal, COSMIC |
| Utilities | `mutate`, `setup`, `gpt` | local / OpenAI |

### Output Formats

| Context | Default Format | Alternatives |
|---------|---------------|-------------|
| Python | DataFrame or dict | `json=True` for JSON; `save=True` to file |
| CLI | JSON | `-csv` for CSV; `-o file` to save |
| Sequences | FASTA (seq, mutate) | -- |
| Structures | PDB file (pdb, alphafold) | JSON alignment error data |
| Single-cell | AnnData object (cellxgene) | `meta_only=True` for metadata only |
| Visualization | PNG (cbio plot) | `show=True` for interactive display |

### Enrichr Database Shortcuts

| Shortcut | Full Database Name |
|----------|-------------------|
| `'pathway'` | KEGG_2021_Human |
| `'transcription'` | ChEA_2016 |
| `'ontology'` | GO_Biological_Process_2021 |
| `'diseases_drugs'` | GWAS_Catalog_2019 |
| `'celltypes'` | PanglaoDB_Augmented_2021 |

Custom libraries: pass any Enrichr library name directly (e.g., `"Jensen_TISSUES"`).

### OpenTargets Resources

| Resource | Description |
|----------|------------|
| `diseases` | Disease associations with evidence scores |
| `drugs` | Drug associations and clinical trial data |
| `tractability` | Target tractability assessment |
| `pharmacogenetics` | Pharmacogenetic variants |
| `expression` | Baseline tissue expression |
| `depmap` | DepMap gene-disease effects |
| `interactions` | Protein-protein interactions |

### Reproducibility

Pin database versions for consistent results across analyses:

```python
import gget
# Pin Ensembl release
ref = gget.ref("homo_sapiens", release=112)

# Pin CELLxGENE Census version
adata = gget.cellxgene(gene=["ACE2"], census_version="2023-07-25")

# Always record gget version
print(f"gget version: {gget.__version__}")
```

## Common Workflows

### Workflow 1: Gene Discovery to Functional Analysis

**Goal**: Find genes of interest, get their sequences, and perform enrichment analysis.

```python
import gget

# 1. Search for genes
results = gget.search(["GABA", "receptor"], species="homo_sapiens")
gene_ids = results["ensembl_id"].tolist()[:10]

# 2. Get detailed information
info = gget.info(gene_ids)
print(f"Retrieved info for {len(info)} genes")

# 3. Get protein sequences
sequences = gget.seq(gene_ids, translate=True)

# 4. Find correlated genes
correlated = gget.archs4(info.index[0], which="correlation")

# 5. Enrichment analysis on correlated genes
gene_list = correlated["gene_symbol"].tolist()[:50]
enrichment = gget.enrichr(gene_list, database="ontology")
print(f"Top enriched term: {enrichment.iloc[0]['Term']}")
```

### Workflow 2: Target Validation for Drug Discovery

**Goal**: Investigate a gene's disease associations, druggability, and cancer mutations.

```python
import gget

gene_id = "ENSG00000169194"  # ZBTB16

# 1. Disease associations
diseases = gget.opentargets(gene_id, resource="diseases", limit=20)

# 2. Drug associations
drugs = gget.opentargets(gene_id, resource="drugs")

# 3. Tractability assessment
tractability = gget.opentargets(gene_id, resource="tractability")

# 4. Protein interactions
interactions = gget.opentargets(gene_id, resource="interactions")
print(f"Diseases: {len(diseases)}, Drugs: {len(drugs)}, Interactions: {len(interactions)}")

# 5. Cancer genomics
gget.cbio_plot(["msk_impact_2017"], ["ZBTB16"], stratification="cancer_type")
```

### Workflow 3: Comparative Genomics

**Goal**: Compare a gene across species using orthologs and sequence alignment.

```python
import gget

# 1. Find orthologs
orthologs = gget.bgee("ENSG00000169194", type="orthologs")

# 2. Get sequences for human and mouse
human_seq = gget.seq("ENSG00000169194", translate=True)
mouse_seq = gget.seq("ENSMUSG00000026091", translate=True)

# 3. Align sequences
alignment = gget.muscle([human_seq, mouse_seq])

# 4. Get human protein structure from PDB
pdb_structure = gget.pdb("7S7U")
print("Comparative analysis complete")
```

## Key Parameters

| Parameter | Module(s) | Default | Range / Options | Effect |
|-----------|-----------|---------|-----------------|--------|
| `species` | search, archs4, cellxgene, enrichr | `"homo_sapiens"` | Any Ensembl species; shortcuts: 'human', 'mouse' | Target organism |
| `limit` | blast, opentargets, cosmic | `50` / `100` | `1`-`1000` | Maximum results returned |
| `database` | blast, enrichr | varies | blast: nt/nr/swissprot/pdbaa; enrichr: shortcuts or library names | Target database for query |
| `which` | ref, archs4 | varies | ref: `gtf`,`cdna`,`dna`,`cds`,`pep`; archs4: `correlation`,`tissue` | Data type to retrieve |
| `translate` | seq | `False` | `True`/`False` | Return amino acid instead of nucleotide sequences |
| `resource` | opentargets | `"diseases"` | diseases, drugs, tractability, pharmacogenetics, expression, depmap, interactions | OpenTargets data type |
| `release` | ref, search | latest | Integer Ensembl release number | Pin database version for reproducibility |
| `census_version` | cellxgene | `"stable"` | `"stable"`, `"latest"`, date string | Pin CELLxGENE Census version |
| `sensitivity` | diamond, elm | `"very-sensitive"` | `fast` to `ultra-sensitive` | Alignment sensitivity vs speed |
| `threads` | diamond, elm | `1` | `1`-`N` | CPU threads for alignment |
| `multimer_recycles` | alphafold | `3` | `3`-`20` | Higher = more accurate multimer prediction |

## Best Practices

1. **Pin database versions for reproducibility**: Use `release=112` for Ensembl and `census_version="2023-07-25"` for CELLxGENE to ensure consistent results across analyses.

2. **Rate-limit batch queries**: gget queries remote APIs. Add `time.sleep(2)` between BLAST/BLAT queries in loops. For `gget.info()`, limit to ~1000 IDs per call.

3. **Keep gget updated**: Databases change their structure biweekly. Run `pip install --upgrade gget` regularly to avoid breakage from schema changes.

4. **Use Python interface for pipelines, CLI for exploration**: Python functions return DataFrames suitable for chaining. CLI with `-csv` is better for quick one-off lookups.

5. **Check PDB before running AlphaFold**: `gget.pdb()` is instant; AlphaFold prediction takes minutes to hours. Always check if the structure already exists in PDB.

6. **Use database shortcuts in enrichr**: The shortcuts (`'pathway'`, `'ontology'`, etc.) map to curated Enrichr libraries. For custom analyses, pass any Enrichr library name directly.

7. **Cache cBioPortal data for repeated analyses**: Use `data_dir="./cache"` parameter to avoid re-downloading large cancer genomics datasets.

## Common Recipes

### Recipe: Batch Gene Information Retrieval

When to use: Need information for many genes at once (up to ~1000 IDs per call).

```python
import gget
import time

gene_ids = ["ENSG00000012048", "ENSG00000139618", "ENSG00000141510"]
info = gget.info(gene_ids)
info.to_csv("gene_info_batch.csv")
print(f"Saved info for {len(info)} genes")

# For >1000 genes, batch with rate limiting
all_ids = [f"ENSG{i:011d}" for i in range(2000)]
results = []
for i in range(0, len(all_ids), 500):
    batch = all_ids[i:i+500]
    results.append(gget.info(batch))
    time.sleep(1)
```

### Recipe: Custom Enrichment with Background

When to use: Running enrichment against a custom background gene set.

```python
import gget

# Use specific Enrichr library with background genes
enrichment = gget.enrichr(
    ["ACE2", "AGT", "AGTR1"],
    database="Jensen_TISSUES",
    background_list=["ACE2", "AGT", "AGTR1", "TP53", "BRCA1", "MYC"]
)
print(enrichment[["Term", "Adjusted P-value"]].head())
```

### Recipe: AlphaFold Structure Prediction with Visualization

When to use: Predicting and visualizing protein structures with confidence coloring.

```python
import gget

# Predict with visualization (PAE + 3D structure)
result = gget.alphafold(
    "MKWMFKEDHSLEHRCVESAKIRAKYPDRVPVIVEKVSGSQIVDIDKRKYLVPSDITVAQFMWIIRKRIQLPSEKAIFLFVDKTVPQSR",
    plot=True,
    show_sidechains=True,
    relax=True  # AMBER relaxation for final structure
)
# Output: PDB file + predicted aligned error (PAE) JSON
# PAE heatmap auto-generated with plot=True
```

### Recipe: Download Reference Genome for RNA-seq Pipeline

When to use: Setting up reference files for RNA-seq alignment pipelines.

```bash
# Download GTF and cDNA for human (specific release)
gget ref -w gtf -w cdna -d -r 112 homo_sapiens

# Download genome DNA
gget ref -w dna -d homo_sapiens
```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `ModuleNotFoundError: gget` | Package not installed | `pip install gget` in clean virtual environment |
| `gget setup alphafold` fails | Python version incompatibility | Use Python 3.8-3.10; check `gget --version` |
| Empty BLAST results | Sequence too short or no matches | Try longer sequence, different database, or `megablast_off=True` |
| `cellxgene` gene not found | Case-sensitive gene symbols | Use `'ACE2'` for human, `'Ace2'` for mouse (exact capitalization required) |
| `gget info` timeout | Too many IDs at once | Limit to ~1000 Ensembl IDs per call; batch with `time.sleep()` |
| Database structure changed | gget databases update biweekly | `pip install --upgrade gget` |
| COSMIC authentication error | Missing or expired credentials | Re-enter email/password; check COSMIC account status |
| AlphaFold out of memory | Protein too long for GPU memory | Use shorter sequences or split into domains |
| Different results on re-run | Database updated between runs | Pin versions: `release=112` for Ensembl, `census_version` for CELLxGENE |

## Bundled Resources

2 reference files provide extended coverage of capabilities from the original 3 reference files and 3 script files:

1. **`references/module_parameters.md`** — Consolidates module_reference.md (468 lines). Covers: detailed parameter tables for all 15+ modules with types, defaults, and return value descriptions; CLI vs Python interface differences; setup requirements per module. Relocated inline: most-used module parameters (Core API code blocks), output format summary (Key Concepts table). Omitted: gget gpt module details — trivial OpenAI wrapper, not genomics-specific.

2. **`references/databases_workflows.md`** — Consolidates database_info.md (301 lines) and workflows.md (815 lines). Covers: complete database directory with update frequencies and citation info, extended workflow examples (building reference indices, disease-drug pipeline, multi-species comparative analysis), data consistency and reproducibility guidance. Relocated inline: core database overview (Key Concepts table), top 3 workflows (Common Workflows), reproducibility patterns (Key Concepts). Omitted: scripts/ content (3 files, 590 lines total) — thin wrappers around gget API calls for CLI automation; core patterns absorbed into Core API and Common Workflows. 
## Related Skills

- **biopython** — advanced BLAST parameters, batch sequence processing, GenBank record parsing
- **bioservices** — programmatic multi-database queries with built-in rate limiting (UniProt, KEGG, ChEMBL)
- **anndata-data-structure** — working with AnnData objects returned by `gget.cellxgene()`
- **enrichr** — deeper enrichment analysis with custom gene set libraries

## References

- [gget documentation](https://pachterlab.github.io/gget/) — official docs and tutorials
- [gget GitHub](https://github.com/pachterlab/gget) — source code, issues
- Luebbert, L. & Pachter, L. (2023). Efficient querying of genomic reference databases with gget. *Bioinformatics*. https://doi.org/10.1093/bioinformatics/btac836
