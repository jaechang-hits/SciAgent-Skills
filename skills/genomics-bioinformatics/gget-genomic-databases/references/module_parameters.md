# gget — Module Parameter Reference

## ref — Reference Genome Retrieval

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `species` | str | *required* | Species in Genus_species format or shortcuts ('human', 'mouse') |
| `which` | str | All | File types: `gtf`, `cdna`, `dna`, `cds`, `cdrna`, `pep` |
| `release` | int | Latest | Ensembl release number (pin for reproducibility) |
| `list_species` | bool | False | List available vertebrate species |
| `list_iv_species` | bool | False | List available invertebrate species |
| `download` | bool | False | Download files directly (requires curl) |
| `ftp` | bool | False | Return only FTP links |
| `out` | str | None | JSON file path for results |

Returns: JSON with FTP links, release numbers, dates, file sizes.

## search — Gene Search

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `searchwords` | str/list | *required* | Search terms (case-insensitive) |
| `species` | str | *required* | Target species or Ensembl core database name |
| `release` | int | Latest | Ensembl release number |
| `id_type` | str | `'gene'` | Return type: `'gene'` or `'transcript'` |
| `andor` | str | `'or'` | `'or'` matches ANY term; `'and'` requires ALL terms |
| `limit` | int | None | Maximum results to return |

Returns: ensembl_id, gene_name, ensembl_description, biotype, URL.

## info — Gene/Transcript Metadata

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `ens_ids` | str/list | *required* | Ensembl IDs (also WormBase, FlyBase) |
| `ncbi` | bool | True | Set False to disable NCBI data retrieval |
| `uniprot` | bool | True | Set False to disable UniProt data retrieval |
| `pdb` | bool | False | Include PDB identifiers in output |

Limit: ~1000 IDs per call to avoid server errors.

Returns: UniProt ID, NCBI gene ID, gene name, synonyms, protein names, biotype, canonical transcript.

## blast — NCBI BLAST Search

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `sequence` | str | *required* | Sequence string or path to FASTA/.txt file |
| `program` | str | Auto-detect | `blastn`, `blastp`, `blastx`, `tblastn`, `tblastx` |
| `database` | str | nt or nr | Nucleotide: `nt`, `refseq_rna`, `pdbnt`. Protein: `nr`, `swissprot`, `pdbaa`, `refseq_protein` |
| `limit` | int | 50 | Maximum hits returned |
| `expect` | float | 10.0 | E-value cutoff |
| `low_comp_filt` | bool | False | Enable low-complexity region filtering |
| `megablast_off` | bool | False | Disable MegaBLAST (blastn only; use for short/divergent sequences) |

Returns: Description, Scientific Name, Taxid, Max Score, Query Coverage, E-value, % Identity.

## blat — UCSC Genome BLAT

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `sequence` | str | *required* | Sequence string or path to FASTA/.txt file |
| `seqtype` | str | Auto-detect | `'DNA'`, `'protein'`, `'translated%20RNA'`, `'translated%20DNA'` |
| `assembly` | str | `'human'` (hg38) | Target assembly: `hg38`, `mm39`, `taeGut2`, etc. |

Returns: genome, query size, chromosome, start/end, matches, mismatches, alignment %.

## diamond — Fast Local Alignment

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `query` | str/list | *required* | Query sequences or FASTA file |
| `reference` | str/list | *required* | Reference sequences or FASTA file |
| `sensitivity` | str | `'very-sensitive'` | Levels: `fast`, `mid-sensitive`, `sensitive`, `more-sensitive`, `very-sensitive`, `ultra-sensitive` |
| `threads` | int | 1 | CPU threads for parallel alignment |
| `diamond_db` | str | None | Path to save/reuse DIAMOND database |
| `translated` | bool | False | Enable nucleotide-to-amino-acid translated alignment |
| `diamond_binary` | str | Auto-detect | Custom path to DIAMOND installation |

Returns: Identity %, sequence lengths, match positions, gap openings, E-values, bit scores.

## alphafold — Structure Prediction

Setup: `gget setup alphafold` (~4GB download, requires OpenMM).

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `sequence` | str/list | *required* | Amino acid sequence(s) or FASTA file; multiple sequences trigger multimer |
| `multimer_recycles` | int | 3 | Recycling iterations for multimers (3-20; higher = more accurate) |
| `multimer_for_monomer` | bool | False | Apply multimer model to single-chain inputs |
| `relax` | bool | False | AMBER relaxation for final structure refinement |
| `out` | str | timestamped | Output folder path |
| `plot` | bool | True | *Python only.* Generate 3D structure + PAE heatmap visualization |
| `show_sidechains` | bool | True | *Python only.* Include side chains in 3D plot |

Returns: PDB structure file, JSON predicted aligned error (PAE) data, optional 3D plot.

## elm — Eukaryotic Linear Motifs

Setup: `gget setup elm`.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `sequence` | str | *required* | Amino acid sequence or UniProt accession |
| `sensitivity` | str | `'very-sensitive'` | DIAMOND alignment sensitivity (same levels as diamond module) |
| `threads` | int | 1 | CPU threads for DIAMOND alignment |
| `uniprot` | bool | False | Treat input as UniProt accession instead of raw sequence |
| `expand` | bool | False | Include additional protein names, organisms, references in output |
| `diamond_binary` | str | Auto-detect | Custom path to DIAMOND binary |

Returns two DataFrames: (1) **ortholog_df** — motifs from orthologous proteins; (2) **regex_df** — motifs matched by regex in input sequence.

## cellxgene — Single-Cell Census Data

Setup: `gget setup cellxgene`.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `gene` | list | *required* | Gene names or Ensembl IDs (**case-sensitive**: 'ACE2' human, 'Ace2' mouse) |
| `species` | str | `'homo_sapiens'` | `'homo_sapiens'` or `'mus_musculus'` |
| `tissue` | list | None | Filter by tissue type(s) |
| `cell_type` | list | None | Filter by cell type(s) |
| `disease` | list | None | Filter by disease condition(s) |
| `development_stage` | list | None | Filter by developmental stage(s) |
| `sex` | list | None | Filter by sex |
| `assay` | list | None | Filter by assay technology |
| `dataset_id` | list | None | Filter by CELLxGENE dataset ID(s) |
| `donor_id` | list | None | Filter by donor ID(s) |
| `ethnicity` | list | None | Filter by ethnicity/self-reported ancestry |
| `suspension_type` | list | None | Filter by suspension type |
| `census_version` | str | `'stable'` | `'stable'`, `'latest'`, or date string (e.g., `'2023-07-25'`) for reproducibility |
| `ensembl` | bool | False | Input genes are Ensembl IDs |
| `meta_only` | bool | False | Return cell metadata only (no expression matrix) |

Returns: AnnData object with count matrices and cell/gene metadata.

## enrichr — Enrichment Analysis

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `genes` | list | *required* | Gene symbols or Ensembl IDs |
| `database` | str | *required* | Enrichr library name or shortcut (see below) |
| `species` | str | `'human'` | `human`, `mouse`, `fly`, `yeast`, `worm`, `fish` |
| `background_list` | list | None | Background gene set for custom enrichment |
| `kegg_out` | str | None | Directory path to save KEGG pathway images |
| `plot` | bool | False | *Python only.* Generate graphical results |

**Database shortcuts:**

| Shortcut | Full Library Name |
|----------|-------------------|
| `'pathway'` | KEGG_2021_Human |
| `'transcription'` | ChEA_2016 |
| `'ontology'` | GO_Biological_Process_2021 |
| `'diseases_drugs'` | GWAS_Catalog_2019 |
| `'celltypes'` | PanglaoDB_Augmented_2021 |

Any Enrichr library name can be passed directly (e.g., `"Jensen_TISSUES"`).

Returns: Terms with adjusted p-values, overlap counts, combined scores.

## opentargets — Disease/Drug Associations

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `ens_id` | str | *required* | Ensembl gene ID |
| `resource` | str | `'diseases'` | `diseases`, `drugs`, `tractability`, `pharmacogenetics`, `expression`, `depmap`, `interactions` |
| `limit` | int | None | Maximum results |

**Resource-specific filter parameters:**

| Resource | Filter Parameter | Description |
|----------|-----------------|-------------|
| `drugs` | `filter_disease` | Filter drug results by disease |
| `pharmacogenetics` | `filter_drug` | Filter pharmacogenetic results by drug |
| `expression` | `filter_tissue` | Filter by tissue |
| `expression` | `filter_anat_sys` | Filter by anatomical system |
| `expression` | `filter_organ` | Filter by organ |
| `depmap` | `filter_tissue` | Filter DepMap results by tissue |
| `interactions` | `filter_protein_a` | Filter by first interactor |
| `interactions` | `filter_protein_b` | Filter by second interactor |
| `interactions` | `filter_gene_b` | Filter by interacting gene |

Returns: Disease/drug associations with evidence scores, tractability assessments, expression data, interactions.

## cbio — Cancer Genomics (cBioPortal)

### cbio_search

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `keywords` | list | *required* | Search terms for cBioPortal studies |

### cbio_plot

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `study_ids` | list | *required* | cBioPortal study ID(s) |
| `genes` | list | *required* | Gene names or Ensembl IDs |
| `stratification` | str | None | `tissue`, `cancer_type`, `cancer_type_detailed`, `study_id`, `sample` |
| `variation_type` | str | None | `mutation_occurrences`, `cna_nonbinary`, `sv_occurrences`, `cna_occurrences`, `Consequence` |
| `filter` | str | None | Column filter (e.g., `'study_id:msk_impact_2017'`) |
| `data_dir` | str | `./gget_cbio_cache` | Cache directory for downloaded data |
| `figure_dir` | str | `./gget_cbio_figures` | Output directory for figures |
| `title` | str | None | Custom figure title |
| `dpi` | int | 100 | Figure resolution |
| `show` | bool | False | Display plot in interactive window |
| `no_confirm` | bool | False | Skip download confirmation prompts |

Returns: PNG heatmap figure saved to figure_dir.

## cosmic — COSMIC Cancer Mutations

Requires COSMIC account. Commercial use requires license.

### Query mode

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `searchterm` | str | *required* | Gene name, Ensembl ID, mutation, or sample ID |
| `cosmic_tsv_path` | str | *required* | Path to local COSMIC TSV database file |
| `limit` | int | 100 | Maximum results |

### Download mode

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `download_cosmic` | bool | False | Activate download mode |
| `cosmic_project` | str | None | `cancer`, `census`, `cell_line`, `resistance`, `genome_screen`, `targeted_screen` |
| `cosmic_version` | str | Latest | COSMIC version to download |
| `grch_version` | int | None | Reference genome version: `37` or `38` |
| `gget_mutate` | bool | False | Format download for gget mutate compatibility |
| `email` | str | *required* | COSMIC account email |
| `password` | str | *required* | COSMIC account password |

Returns: Mutation data from COSMIC database.

## mutate — Mutation Sequence Generation

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `sequences` | str/list | *required* | FASTA file path or list of nucleotide sequences |
| `mutations` | str/DataFrame | *required* | CSV/TSV file path or DataFrame with mutation annotations |
| `mut_column` | str | `'mutation'` | Column name containing mutation strings (e.g., `'c.4G>T'`, `'c.10del'`) |
| `seq_id_column` | str | `'seq_ID'` | Column name containing sequence identifiers |
| `mut_id_column` | str | None | Optional column name for mutation identifiers |
| `k` | int | 30 | Length of flanking sequences on each side of mutation |

Returns: Mutated sequences in FASTA format.

*Condensed from module_reference.md (468 lines). Retained: all module parameter tables with types and defaults. Omitted: gget gpt module (trivial OpenAI wrapper). Relocated to SKILL.md: most-used parameters in Core API code, Key Parameters summary table, output format table.*
