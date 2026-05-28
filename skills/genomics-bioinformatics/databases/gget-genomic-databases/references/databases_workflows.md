# gget — Database Directory & Extended Workflows

## Complete Database Directory

### Genomic Reference Databases

| Database | URL | gget Module(s) | Update Frequency | Access Method |
|----------|-----|-----------------|------------------|---------------|
| **Ensembl** | https://ensembl.org | `ref`, `search`, `info`, `seq` | Quarterly (major releases ~112+) | REST API |
| **UCSC Genome Browser** | https://genome.ucsc.edu | `blat` | Continuous | REST API (BLAT server) |

- **Ensembl**: Primary backend for gene search, annotation, and sequence retrieval. Species names use underscore format (`homo_sapiens`, `mus_musculus`). Supports shortcuts: `'human'`, `'mouse'`. Pin `release=N` for reproducibility; each release freezes gene models and coordinates. Max ~1000 Ensembl IDs per `gget.info()` call.
- **UCSC**: Used exclusively by `gget.blat()` for rapid genomic coordinate lookup. Assembly parameter accepts shortcuts (`"human"` = hg38, `"mouse"` = mm39). Results include chromosome, start, end, strand, and percent identity.

### Protein & Structure Databases

| Database | URL | gget Module(s) | Update Frequency | Access Method |
|----------|-----|-----------------|------------------|---------------|
| **UniProt** | https://uniprot.org | `info` | Monthly | REST API (via Ensembl cross-refs) |
| **NCBI Gene** | https://ncbi.nlm.nih.gov/gene | `info` | Continuous | REST API (via Ensembl cross-refs) |
| **RCSB PDB** | https://rcsb.org | `pdb` | Weekly (Wed) | REST API + FTP |
| **AlphaFold DB** | https://alphafold.ebi.ac.uk | `alphafold` | Major releases | Local model (ColabFold/OpenMM) |
| **ELM** | http://elm.eu.org | `elm` | ~Annually | Local download (`gget setup elm`) |

- **UniProt/NCBI**: Queried indirectly through `gget.info()` cross-references. Provides protein names, functions, pathways, and external database links. No separate rate limiting needed beyond Ensembl's.
- **RCSB PDB**: `gget.pdb("7S7U", save=True)` downloads PDB/mmCIF files. Always check PDB before running AlphaFold predictions — PDB lookup is instant vs minutes/hours for prediction.
- **AlphaFold2**: Requires `gget setup alphafold` (~4GB model weights, OpenMM dependency). Runs locally via ColabFold. GPU strongly recommended. For multimers, increase `multimer_recycles` (3-20) for accuracy at the cost of compute time.
- **ELM**: Eukaryotic Linear Motif resource. Requires `gget setup elm` to download the database locally. Returns two DataFrames: ortholog-based motifs and regex-matched motifs.

### Sequence Similarity Databases

| Database | URL | gget Module(s) | Update Frequency | Access Method |
|----------|-----|-----------------|------------------|---------------|
| **NCBI BLAST** | https://blast.ncbi.nlm.nih.gov | `blast` | Continuous | REST API (remote queue) |
| **DIAMOND** (local) | https://github.com/bbuchfink/diamond | `diamond` | User-managed | Local binary |
| **Muscle5** (local) | https://drive5.com/muscle5 | `muscle` | Stable | Local binary |

- **NCBI BLAST**: Remote API with queuing — queries may take 30s-5min. Add `time.sleep(2)` between batch queries. Databases: `nt` (nucleotide), `nr` (non-redundant protein), `swissprot` (curated protein), `pdbaa` (PDB sequences). Use `megablast_off=True` for divergent sequences.
- **DIAMOND**: Fast local protein alignment. No rate limits. Requires a local reference FASTA. Set `sensitivity` from `"fast"` to `"ultra-sensitive"` and `threads` for parallelism.
- **Muscle5**: Local multiple sequence alignment. Input: FASTA file or list of sequences. No external API calls.

### Expression Databases

| Database | URL | gget Module(s) | Update Frequency | Access Method |
|----------|-----|-----------------|------------------|---------------|
| **ARCHS4** | https://maayanlab.cloud/archs4 | `archs4` | ~Quarterly | REST API |
| **CZ CELLxGENE Census** | https://cellxgene.cziscience.com | `cellxgene` | Monthly snapshots | Local download via `cellxgene-census` |
| **Bgee** | https://bgee.org | `bgee` | ~Annually | REST API |

- **ARCHS4**: Massive compendium of uniformly processed RNA-seq data. Two query modes: `which="tissue"` (tissue expression profile) and `which="correlation"` (co-expressed genes). Gene symbols are case-sensitive (`ACE2` for human, `Ace2` for mouse).
- **CELLxGENE Census**: Single-cell RNA-seq atlas. **Case-sensitive gene symbols** — use exact capitalization (`'ACE2'` human, `'Ace2'` mouse). Requires `gget setup cellxgene`. Pin `census_version="2023-07-25"` for reproducibility (`"stable"` and `"latest"` change over time). Returns AnnData objects; use `meta_only=True` for metadata-only queries on large datasets.
- **Bgee**: Ortholog expression across species. Query types: `type="orthologs"` (cross-species homologs) and expression data. Useful for evolutionary expression comparisons.

### Functional & Pathway Databases

| Database | URL | gget Module(s) | Update Frequency | Access Method |
|----------|-----|-----------------|------------------|---------------|
| **Enrichr** | https://maayanlab.cloud/Enrichr | `enrichr` | ~Annually per library | REST API |

- **Enrichr**: Gene set enrichment against 200+ curated libraries. Shortcut databases: `'pathway'` (KEGG_2021_Human), `'transcription'` (ChEA_2016), `'ontology'` (GO_Biological_Process_2021), `'diseases_drugs'` (GWAS_Catalog_2019), `'celltypes'` (PanglaoDB_Augmented_2021). Pass any Enrichr library name directly for custom analyses (e.g., `"Jensen_TISSUES"`). Supports `background_list` for custom background gene sets.

### Disease & Drug Databases

| Database | URL | gget Module(s) | Update Frequency | Access Method |
|----------|-----|-----------------|------------------|---------------|
| **OpenTargets** | https://platform.opentargets.org | `opentargets` | ~Bimonthly | REST API (GraphQL) |
| **cBioPortal** | https://www.cbioportal.org | `cbio` | Continuous | REST API |
| **COSMIC** | https://cancer.sanger.ac.uk/cosmic | `cosmic` | ~Quarterly | Local TSV download (requires account) |

- **OpenTargets**: Comprehensive target-disease-drug platform. Seven resource types: `diseases`, `drugs`, `tractability`, `pharmacogenetics`, `expression`, `depmap`, `interactions`. Input: Ensembl gene ID. Returns scored associations. No authentication required.
- **cBioPortal**: Cancer genomics — mutations, copy number, expression across cancer studies. `gget.cbio_search()` finds studies by keyword. `gget.cbio_plot()` generates alteration heatmaps. Use `data_dir="./cache"` to cache downloaded data for repeated analyses.
- **COSMIC**: Catalogue of Somatic Mutations in Cancer. **Requires free account registration** at https://cancer.sanger.ac.uk/cosmic/register. First use: `gget.cosmic(searchterm="", download_cosmic=True, email="...", password="...")` downloads the full TSV. Subsequent queries run against local TSV file. License restricts redistribution of COSMIC data.

### AI & Utility

| Database | URL | gget Module(s) | Update Frequency | Access Method |
|----------|-----|-----------------|------------------|---------------|
| **OpenAI** | https://openai.com | `gpt` | N/A | REST API (requires API key) |

- **gget.gpt**: Thin wrapper around OpenAI API for natural-language gene/protein queries. Requires `gget setup gpt` and an OpenAI API key. Not genomics-specific; generally prefer direct database queries for reproducible results.

---

## Extended Workflow: Building Reference Indices for RNA-seq

**Goal**: Download and build kallisto|bustools reference indices for single-cell or bulk RNA-seq alignment using gget.

This workflow is primarily bash/CLI-oriented, using `gget ref` to obtain Ensembl reference files and then building indices for the kb-python (kallisto|bustools) pipeline.

```bash
# Step 1: Download reference files for a specific Ensembl release
# Pin release for reproducibility across lab members
gget ref -w dna -w gtf -d -r 112 homo_sapiens
# Output: Homo_sapiens.GRCh38.dna.primary_assembly.fa.gz
#         Homo_sapiens.GRCh38.112.gtf.gz

# Step 2: For mouse (or other species)
gget ref -w dna -w gtf -d -r 112 mus_musculus

# Step 3: Build kallisto index (requires kb-python installed)
kb ref \
  -i index.idx \
  -g t2g.txt \
  -f1 cdna.fa \
  Homo_sapiens.GRCh38.dna.primary_assembly.fa.gz \
  Homo_sapiens.GRCh38.112.gtf.gz

# Step 4: Verify index files exist
ls -lh index.idx t2g.txt cdna.fa
```

```python
# Python equivalent for programmatic pipelines
import gget
import subprocess

# Download with version pinning
ref_links = gget.ref("homo_sapiens", which=["dna", "gtf", "cdna"], release=112)
print(f"Reference URLs: {ref_links}")

# Download files (gget.ref returns URLs; download separately or use -d flag in CLI)
# For cDNA-only index (faster, sufficient for most scRNA-seq):
cdna_links = gget.ref("homo_sapiens", which="cdna", release=112, download=True)
print("cDNA reference downloaded for index building")
```

**Notes**: Always use `release=N` to ensure all lab members build identical indices. Store the release number in your pipeline configuration or README.

---

## Extended Workflow: Disease-Drug Discovery Pipeline

**Goal**: Comprehensive target assessment combining OpenTargets disease associations, pathway enrichment, and cancer genomics for drug discovery target prioritization.

```python
import gget
import pandas as pd
import time

# === Phase 1: Target-Disease Association ===
gene_id = "ENSG00000157764"  # BRAF
gene_symbol = "BRAF"

# Get disease associations with evidence scores
diseases = gget.opentargets(gene_id, resource="diseases", limit=25)
print(f"Disease associations: {len(diseases)}")
print(diseases[["disease_id", "disease_name", "overall_score"]].head(10))

# Get existing drug associations (what's already in trials?)
drugs = gget.opentargets(gene_id, resource="drugs", limit=25)
print(f"\nDrug associations: {len(drugs)}")

# Assess druggability
tractability = gget.opentargets(gene_id, resource="tractability")
print(f"\nTractability modalities: {list(tractability.columns)}")

# === Phase 2: Pathway Context via Enrichment ===
# Get interacting proteins to understand pathway context
interactions = gget.opentargets(gene_id, resource="interactions")
interacting_genes = interactions["targetB_symbol"].tolist()[:30]

# Enrich interacting genes for pathway context
pathway_enrichment = gget.enrichr(
    [gene_symbol] + interacting_genes[:20],
    database="pathway"
)
print(f"\nEnriched KEGG pathways: {len(pathway_enrichment)}")
print(pathway_enrichment[["Term", "Adjusted P-value"]].head(5))

# Disease-specific enrichment
disease_enrichment = gget.enrichr(
    [gene_symbol] + interacting_genes[:20],
    database="diseases_drugs"
)
print(f"Disease/drug enriched terms: {len(disease_enrichment)}")

# === Phase 3: Cancer Genomics Assessment ===
# Search for relevant cancer studies
studies = gget.cbio_search(["melanoma", "lung", "colorectal"])
print(f"\nCancer studies found: {len(studies)}")

# Visualize mutation landscape across cancer types
gget.cbio_plot(
    ["msk_impact_2017"],
    [gene_symbol, "KRAS", "NRAS", "MAP2K1"],  # MAPK pathway genes
    stratification="cancer_type",
    variation_type="mutation_occurrences"
)
print("Cancer genomics heatmap generated")

# === Phase 4: Summary Report ===
print(f"\n{'='*50}")
print(f"Target Assessment Summary: {gene_symbol}")
print(f"  Disease associations: {len(diseases)}")
print(f"  Existing drugs: {len(drugs)}")
print(f"  Protein interactions: {len(interactions)}")
print(f"  Top disease: {diseases.iloc[0]['disease_name'] if len(diseases) > 0 else 'N/A'}")
print(f"  Top pathway: {pathway_enrichment.iloc[0]['Term'] if len(pathway_enrichment) > 0 else 'N/A'}")
```

---

## Extended Workflow: Multi-species Expression Comparison

**Goal**: Compare gene expression across species using Bgee orthologs and ARCHS4 tissue expression data to identify conserved and divergent expression patterns.

```python
import gget
import pandas as pd

# === Step 1: Find orthologs across species ===
human_gene = "ENSG00000169194"  # DPP4/CD26
orthologs = gget.bgee(human_gene, type="orthologs")
print(f"Orthologs found in {len(orthologs)} species")
print(orthologs[["species", "gene_id"]].head(10))

# === Step 2: Get tissue expression for human ===
human_tissue = gget.archs4("DPP4", which="tissue")
print(f"\nHuman DPP4 expression across {len(human_tissue)} tissues")
print(human_tissue.head(5))

# === Step 3: Get tissue expression for mouse ortholog ===
mouse_tissue = gget.archs4("Dpp4", which="tissue", species="mouse")
print(f"\nMouse Dpp4 expression across {len(mouse_tissue)} tissues")
print(mouse_tissue.head(5))

# === Step 4: Get correlated genes in both species ===
human_correlated = gget.archs4("DPP4", which="correlation")
mouse_correlated = gget.archs4("Dpp4", which="correlation", species="mouse")

# Find conserved co-expression partners
human_top = set(human_correlated["gene_symbol"].str.upper().tolist()[:50])
mouse_top = set(mouse_correlated["gene_symbol"].str.upper().tolist()[:50])
conserved = human_top & mouse_top
print(f"\nConserved co-expression partners: {len(conserved)}")
print(f"  Genes: {sorted(conserved)[:10]}")

# === Step 5: Enrichment on conserved partners ===
if len(conserved) >= 5:
    enrichment = gget.enrichr(list(conserved), database="ontology")
    print(f"\nConserved partner enrichment ({len(enrichment)} terms):")
    print(enrichment[["Term", "Adjusted P-value"]].head(5))

# === Step 6: Sequence comparison ===
human_seq = gget.seq(human_gene, translate=True)
# Mouse DPP4 Ensembl ID (from orthologs or manual lookup)
mouse_seq = gget.seq("ENSMUSG00000035000", translate=True)

# Align to assess conservation
alignment = gget.muscle([human_seq, mouse_seq])
print("\nProtein sequence alignment generated")
print("High conservation suggests functional constraint across species")
```

**Notes**: ARCHS4 gene symbols are case-sensitive — use uppercase for human (`DPP4`), title case for mouse (`Dpp4`). Always verify ortholog gene IDs from Bgee before querying ARCHS4.

---

## Data Consistency & Reproducibility Guide

### Version Pinning Strategies

| Database | Pinning Method | Example | Notes |
|----------|---------------|---------|-------|
| Ensembl | `release=N` parameter | `gget.ref("homo_sapiens", release=112)` | Freezes gene models and coordinates |
| CELLxGENE | `census_version` parameter | `gget.cellxgene(gene=["ACE2"], census_version="2023-07-25")` | `"stable"` changes; use date strings |
| COSMIC | Local TSV file | `cosmic_tsv_path="cosmic_v99.tsv"` | Version in filename |
| gget itself | Package version | `pip install gget==0.28.6` | Pin in requirements.txt |
| Enrichr | Library name includes year | `"KEGG_2021_Human"` vs shortcut `"pathway"` | Shortcuts may update; use full name for reproducibility |
| cBioPortal | Study-level | `["msk_impact_2017"]` | Studies are versioned; specify exact study ID |

**Minimal reproducibility block** (include in every analysis script):

```python
import gget
print(f"gget version: {gget.__version__}")
# Record all version pins used in this analysis:
# Ensembl release: 112
# CELLxGENE census: 2023-07-25
# COSMIC: v99
```

### Handling Database Update Breakage

Databases update their schemas, endpoints, and data formats. Common breakage patterns and mitigations:

1. **Ensembl schema changes**: Gene IDs are stable across releases but annotations change. If `gget.info()` returns unexpected columns, update gget: `pip install --upgrade gget`.
2. **CELLxGENE Census API changes**: The Census API evolves rapidly. Pin `census_version` to a specific date. If queries fail after a gget update, check the [Census changelog](https://chanzuckerberg.github.io/cellxgene-census/).
3. **BLAST database updates**: NCBI refreshes nr/nt continuously. E-values and hit rankings may shift between runs weeks apart. For reproducible BLAST, record the date and gget version.
4. **Enrichr library retirement**: Old library versions (e.g., `GO_Biological_Process_2018`) may be removed. Use the most recent year available and document which version you used.

### API Rate Limiting for Large-scale Analyses

| Service | Rate Limit | Recommended Delay | Batch Strategy |
|---------|-----------|-------------------|----------------|
| NCBI BLAST | 1 query/3s (unauthenticated) | `time.sleep(3)` between queries | Submit batches, poll for results |
| Ensembl REST | 15 requests/second | `time.sleep(0.1)` in loops | Batch IDs: up to ~1000 per `gget.info()` call |
| ARCHS4 | ~5 requests/second | `time.sleep(0.5)` in loops | Single gene per query |
| OpenTargets GraphQL | 10 requests/second | `time.sleep(0.2)` in loops | One gene per query |
| CELLxGENE Census | Local after download | No limit | Use `meta_only=True` for large exploratory queries |
| Enrichr | ~5 requests/second | `time.sleep(0.5)` in loops | One gene list per query |
| cBioPortal | ~10 requests/second | `time.sleep(0.2)` in loops | Cache with `data_dir=` parameter |

```python
import gget
import time

# Example: batch querying with rate limiting
gene_ids = ["ENSG00000012048", "ENSG00000139618", "ENSG00000141510"]
results = []
for gene_id in gene_ids:
    diseases = gget.opentargets(gene_id, resource="diseases", limit=10)
    results.append(diseases)
    time.sleep(0.5)  # Respect rate limits
print(f"Queried {len(results)} genes")
```

### Citation Requirements

When publishing results obtained through gget, cite:

1. **gget itself**: Luebbert, L. & Pachter, L. (2023). Efficient querying of genomic reference databases with gget. *Bioinformatics*. https://doi.org/10.1093/bioinformatics/btac836
2. **Underlying databases**: Each database has its own citation requirement. Key citations:
   - Ensembl: Cunningham et al. (2022) Nucleic Acids Research
   - UniProt: The UniProt Consortium (2023) Nucleic Acids Research
   - NCBI BLAST: Altschul et al. (1990) Journal of Molecular Biology
   - OpenTargets: Ochoa et al. (2023) Nucleic Acids Research
   - Enrichr: Kuleshov et al. (2016) Nucleic Acids Research
   - COSMIC: Tate et al. (2019) Nucleic Acids Research (requires account acknowledgment)
   - CELLxGENE Census: CZI Single-Cell Biology (2023) bioRxiv
   - ARCHS4: Lachmann et al. (2018) Nature Communications

Always check individual database citation policies before publication. COSMIC data redistribution is restricted by license.

*Condensed from database_info.md (301 lines) and workflows.md (815 lines) — 1,116 total. Retained: complete database directory, 3 extended workflows, reproducibility guide. Omitted: scripts/ content (3 files, 590 lines — thin CLI wrappers absorbed into Core API). Relocated to SKILL.md: core database overview table, top 3 workflows, basic best practices, reproducibility patterns.*
