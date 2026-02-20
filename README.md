# SciCraft

**140 validated scientific skills for AI coding agents** — domain-specific knowledge Claude doesn't already have: genomics pipelines, drug discovery databases, proteomics tools, and more.

[![License: CC-BY-4.0](https://img.shields.io/badge/License-CC--BY--4.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/)
[![Skills](https://img.shields.io/badge/Skills-140-brightgreen.svg)](#whats-inside)
[![Works with](https://img.shields.io/badge/Works_with-Claude_Code-blueviolet.svg)](https://docs.anthropic.com/en/docs/claude-code)
[![CI](https://img.shields.io/github/actions/workflow/status/jaechang-hits/scicraft/validate.yml?label=CI)](https://github.com/jaechang-hits/scicraft/actions)

---

## What makes SciCraft different

- **AI-Native Authoring** — `CLAUDE.md` contains a complete 6-step workflow. Give Claude Code a topic, and it classifies, researches, writes, and validates a production-quality skill automatically.
- **CI-Validated** — every skill passes structural tests: frontmatter fields, required sections, minimum code block counts, and troubleshooting table depth. Run `pixi run test` locally.
- **10+ runnable code blocks per skill** — each skill ships with Key Parameters tables, Troubleshooting matrices, and Expected Outputs so the agent can use them without guessing.

---

## Why SciCraft Exists: Blind Test Results

> **TL;DR** — We tested Claude on 140 life sciences tools *without* SciCraft loaded. It scored 0/5 on 109 of them. That's why this library exists.

Before building SciCraft, we ran a blind validation: ask Claude questions about each tool's API without providing any documentation, then score the answers. The results confirmed the core problem:

| Result | Skills | What it means |
|--------|:------:|---------------|
| Score 0/5 — "no answer found" | 109 / 140 | Claude has no usable knowledge of the tool |
| Score 1–2/5 — partial/hallucinated | 27 / 140 | Claude guesses plausible-but-wrong API names |
| Score 3–5/5 | 4 / 140 | Claude already knows the tool well |

**Low scores are the point.** A score of 0 means Claude said "I don't know" rather than hallucinate — and every one of those tools is now covered by a SciCraft skill. The recommendation column in [`blind_test_results.csv`](blind_test_results.csv) reads `MUST_KEEP` for all 140 entries: these are tools Claude cannot reliably use without grounded documentation.

With a SciCraft skill loaded, the agent reads verified API signatures, parameter tables, and runnable examples — instead of guessing.

---

## How It Works: AI-Native Skill Authoring

SciCraft isn't just a collection of skills — it's a **skill factory**.

The `CLAUDE.md` file encodes a complete 6-step workflow that Claude Code follows to author new skills from scratch:

```
Topic → Step 1: Classify  (pipeline / toolkit / database / guide)
      → Step 2: Category  (11 life sciences domains)
      → Step 3: Research  (official docs, GitHub, PyPI)
      → Step 4: Author    (template → SKILL.md with 10+ code blocks)
      → Step 5: Register  (registry.yaml entry)
      → Step 6: Validate  (pixi run test ✅)
```

### Example: adding a new skill

> **Prompt**: "Add a skill for CellRanger single-cell gene expression"

Claude Code will:
1. Read `CLAUDE.md` and classify CellRanger as a **pipeline** (input → processing → output)
2. Place it in `skills/genomics-bioinformatics/cellranger-scrna-seq/`
3. Fetch docs from the official CellRanger documentation
4. Write `SKILL.md` using `SKILL_TEMPLATE.md` — 8 workflow steps, Key Parameters, Troubleshooting, Expected Outputs
5. Append the entry to `registry.yaml`
6. Run `pixi run test` — all checks pass

**Result**: a production-quality skill in minutes.

The same workflow works for external contributors: clone the repo, describe your topic, and Claude Code handles the rest.

---

## What's Inside

| Category | Skills | Examples |
|----------|:------:|----------|
| Genomics & Bioinformatics | 59 | Scanpy, DESeq2, gnomAD, ENCODE, UCSC, CellTypist, popV, cBioPortal |
| Structural Biology & Drug Discovery | 25 | RDKit, AutoDock Vina, ChEMBL, DailyMed, DDInter, UniChem, GtoPdb, EMDB |
| Cell Biology | 12 | napari, Cellpose, SimpleITK, nnU-Net, pydicom, histolab, FlowIO |
| Scientific Computing | 11 | Snakemake, Nextflow, PyMatGen, NeuroKit2, aeon, pymoo |
| Proteomics & Protein Engineering | 10 | ESM, UniProt, InterPro, PRIDE, PyOpenMS, MaxQuant, matchms |
| Systems Biology & Multi-omics | 9 | COBRApy, LaminDB, Reactome, STRING, libSBML |
| Biostatistics | 4 | PyMC, scikit-survival, pyhealth, clinical-decision-support |
| Lab Automation | 4 | Opentrons, Benchling, PyLabRobot, protocols.io |
| Scientific Writing | 3 | LaTeX posters, openalex, bioRxiv |
| Molecular Biology | 3 | ViennaRNA, pLannotate, sgRNA design guide |

**Skill types:** pipeline, toolkit, database connector, guide

---

## Quick Start

### Step 1: Clone

```bash
git clone https://github.com/jaechang-hits/scicraft.git
```

### Step 2: Load as a Claude Code plugin

```bash
claude --plugin-dir /path/to/scicraft
```

Verify inside Claude Code with `/plugin` — `scicraft` should appear in the Installed tab.

**Persistent installation:**

```
/plugin marketplace add jaechang-hits/scicraft
/plugin install scicraft
```

### Step 3: Use a skill

Invoke skills directly by name:

```
/scicraft:scanpy-scrna-seq
/scicraft:rdkit-cheminformatics
/scicraft:pymc-bayesian-modeling
```

Or just describe your task — the agent finds the relevant skill automatically:

> "Perform differential expression analysis on this RNA-seq count matrix"

#### Alternative: project-level integration

Clone into your project so Claude Code picks up skills via `CLAUDE.md`:

```bash
cd your-project
git clone https://github.com/jaechang-hits/scicraft.git .scicraft
```

Add to your project's `CLAUDE.md`:

```markdown
## Scientific Skills
Reference skills in `.scicraft/skills/` for domain-specific analysis.
Registry: `.scicraft/registry.yaml`
```

---

## Example Use Cases

**Drug Discovery Pipeline**
> "Search ChEMBL for EGFR inhibitors with IC50 < 100 nM, filter with Lipinski rules using RDKit, dock top candidates with AutoDock Vina"

Uses: `chembl-database-bioactivity` → `rdkit-cheminformatics` → `autodock-vina-docking`

**Single-Cell RNA-seq Analysis**
> "Load 10X data, QC filter, normalize, cluster, find marker genes, and annotate cell types"

Uses: `anndata-data-structure` → `scanpy-scrna-seq` → `celltypist-cell-annotation`

**Bayesian Biostatistics**
> "Fit a hierarchical Bayesian model to this clinical trial data with patient-level random effects"

Uses: `pymc-bayesian-modeling`

**Protein Structure Analysis**
> "Get the AlphaFold structure for UniProt P04637, assess confidence, find high-confidence binding regions"

Uses: `uniprot-protein-database` → `alphafold-database-access`

**Copy Number Variation Analysis**
> "Detect CNVs from tumor/normal WGS BAM files, visualize, and annotate with gene overlaps"

Uses: `cnvkit-copy-number` → `bedtools-genomic-intervals`

**Multi-Omics Integration**
> "Integrate RNA-seq and proteomics data, perform pathway enrichment, and visualize network"

Uses: `lamindb-data-management` → `reactome-pathway-database` → `string-protein-networks`

---

## How Skills Work

Each skill is a `SKILL.md` file structured for progressive disclosure:

```
skills/<category>/<skill-name>/
  SKILL.md          # Main file (300–550 lines)
  references/       # Optional deep-dive reference files
  assets/           # Optional templates, configs
```

The agent reads only the `description` field from frontmatter during planning, then loads the full file on demand when the skill is relevant. A `SKILL.md` contains:

- **Frontmatter** — `name`, `description`, `license` (agent discovery)
- **When to Use** — 5+ task-perspective items for routing
- **Prerequisites** — packages, data, environment
- **Quick Start** — minimal copy-paste example
- **Workflow / Core API** — step-by-step pipeline or module-by-module API guide with runnable code
- **Key Parameters** — tunable settings with defaults and ranges
- **Common Recipes** — self-contained snippets for common tasks
- **Troubleshooting** — problem / cause / solution table (5+ rows)
- **Expected Outputs** — shapes, formats, interpretation

---

## Directory Structure

```
scicraft/
├── .claude-plugin/
│   └── plugin.json         # Claude Code plugin manifest
├── .github/
│   ├── workflows/
│   │   └── validate.yml    # CI: runs pixi run test on push/PR
│   └── ISSUE_TEMPLATE/
├── skills/                  # 140 skills organized by category
│   ├── genomics-bioinformatics/
│   ├── structural-biology-drug-discovery/
│   ├── biostatistics/
│   ├── scientific-computing/
│   ├── proteomics-protein-engineering/
│   ├── scientific-writing/
│   ├── systems-biology-multiomics/
│   ├── cell-biology/
│   ├── lab-automation/
│   ├── data-visualization/
│   └── molecular-biology/
├── templates/               # Skill authoring templates
│   ├── SKILL_TEMPLATE.md         # Pipeline skills
│   ├── SKILL_TEMPLATE_TOOLKIT.md # Toolkit skills
│   └── SKILL_TEMPLATE_PROSE.md   # Guide skills
├── registry.yaml            # Index of all 140 skills
├── CLAUDE.md                # 6-step skill authoring workflow
└── tests/                   # Validation test suite
```

---

## Full Skill Index

<details>
<summary>Genomics & Bioinformatics (59 skills)</summary>

| Skill | Type | Description |
|-------|------|-------------|
| anndata-data-structure | toolkit | AnnData format for single-cell data |
| arboreto-grn-inference | pipeline | Gene regulatory network inference |
| archs4-database | database | ARCHS4 uniformly processed RNA-seq expression profiles |
| bcftools-variant-manipulation | toolkit | VCF/BCF variant file operations |
| bedtools-genomic-intervals | toolkit | Genomic interval arithmetic |
| biopython-sequence-analysis | toolkit | BioPython sequence I/O, BLAST, alignment, phylogenetics |
| bioservices-multi-database | toolkit | Multi-database API client |
| bwa-mem2-dna-aligner | pipeline | Ultrafast DNA short-read aligner |
| cbioportal-database | database | cBioPortal cancer genomics (TCGA, mutations, CNA) |
| celltypist-cell-annotation | pipeline | Automated cell type annotation |
| cellxgene-census | database | CZ CELLxGENE Census data access |
| clinpgx-database | database | ClinPGx pharmacogenomics database |
| clinvar-database | database | ClinVar clinical variant database |
| cnvkit-copy-number | pipeline | Copy number variant detection |
| cosmic-database | database | COSMIC cancer mutation database |
| dbsnp-database | database | dbSNP variant database |
| deeptools-ngs-analysis | toolkit | NGS data quality and visualization |
| deseq2-differential-expression | pipeline | Differential gene expression (R) |
| ena-database | database | European Nucleotide Archive access |
| encode-database | database | ENCODE regulatory genomics database |
| ensembl-database | database | Ensembl genome annotation database |
| fastp-fastq-preprocessing | pipeline | FASTQ quality control and trimming |
| featurecounts-rna-counting | pipeline | RNA-seq read counting |
| gatk-variant-calling | pipeline | GATK variant discovery pipeline |
| gget-genomic-databases | toolkit | Gene info retrieval toolkit |
| gene-database | database | NCBI Gene database |
| geo-database | database | NCBI GEO expression database |
| geniml | toolkit | Genomic interval ML embeddings |
| gnomad-database | database | gnomAD population variant database |
| gseapy-gene-enrichment | pipeline | Gene set enrichment analysis |
| gtars | toolkit | Fast BED file processing and tokenization |
| gwas-database | database | GWAS Catalog association database |
| harmony-batch-correction | pipeline | Single-cell batch correction |
| homer-motif-analysis | pipeline | Motif discovery and ChIP-seq analysis |
| jaspar-database | database | JASPAR transcription factor database |
| kegg-database | database | KEGG pathway and gene database |
| macs3-peak-calling | pipeline | ChIP-seq/ATAC-seq peak calling |
| monarch-database | database | Monarch disease-gene-phenotype knowledge graph |
| mouse-phenome-database | database | Mouse Phenome Database phenotype data |
| multiqc-qc-reports | pipeline | Multi-sample QC report aggregation |
| plink2-gwas-analysis | pipeline | GWAS and population genetics |
| popv-cell-annotation | toolkit | Multi-method cell type label transfer |
| prokka-genome-annotation | pipeline | Prokaryotic genome annotation |
| pubmed-database | database | PubMed literature search |
| pydeseq2-differential-expression | pipeline | Differential expression (Python) |
| pysam-genomic-files | toolkit | SAM/BAM/CRAM file manipulation |
| quickgo-database | database | QuickGO gene ontology database |
| regulomedb-database | database | RegulomeDB regulatory variant scoring |
| remap-database | database | ReMap TF ChIP-seq peak database |
| salmon-rna-quantification | pipeline | RNA-seq transcript quantification |
| samtools-bam-processing | toolkit | SAM/BAM utilities |
| scanpy-scrna-seq | pipeline | Single-cell RNA-seq analysis |
| scikit-bio | toolkit | Biological data analysis and diversity metrics |
| scvi-tools-single-cell | toolkit | Deep generative models for single-cell omics |
| single-cell-annotation-guide | guide | Cell type annotation strategy guide |
| snpeff-variant-annotation | pipeline | Variant functional annotation |
| star-rna-seq-aligner | pipeline | RNA-seq splice-aware aligner |
| ucsc-genome-browser | database | UCSC Genome Browser data access |
| etetoolkit | toolkit | Phylogenetic tree analysis and visualization |

</details>

<details>
<summary>Structural Biology & Drug Discovery (25 skills)</summary>

| Skill | Type | Description |
|-------|------|-------------|
| alphafold-database-access | database | AlphaFold structure database |
| autodock-vina-docking | pipeline | Molecular docking simulation |
| chembl-database-bioactivity | database | ChEMBL bioactivity database |
| clinicaltrials-database-search | database | ClinicalTrials.gov study search |
| dailymed-database | database | FDA-approved drug labeling (DailyMed) |
| datamol-cheminformatics | toolkit | Molecular data processing |
| ddinter-database | database | Drug-drug interaction database |
| deepchem | toolkit | Deep learning for drug discovery |
| diffdock | pipeline | Diffusion-based molecular docking |
| drugbank-database-access | database | DrugBank drug database |
| emdb-database | database | Electron Microscopy Data Bank |
| fda-database | database | FDA drug approval database |
| gtopdb-database | database | Guide to Pharmacology receptor/ligand data |
| mdanalysis-trajectory | toolkit | Molecular dynamics trajectory analysis |
| medchem | toolkit | Medicinal chemistry filters and drug-likeness rules |
| molfeat-molecular-featurization | toolkit | Molecular featurization for ML |
| opentargets-database | database | OpenTargets drug-target evidence |
| pdb-database | database | Protein Data Bank structure database |
| pubchem-compound-search | database | PubChem compound database |
| pytdc-therapeutics-data-commons | database | AI-ready drug discovery datasets |
| rdkit-cheminformatics | toolkit | Cheminformatics and molecular analysis |
| rowan | toolkit | Cloud quantum chemistry calculations |
| torchdrug | toolkit | PyTorch drug discovery ML platform |
| unichem-database | database | UniChem cross-database compound IDs |
| zinc-database | database | ZINC purchasable compound database |

</details>

<details>
<summary>Cell Biology (12 skills)</summary>

| Skill | Type | Description |
|-------|------|-------------|
| cellpose-cell-segmentation | pipeline | Deep learning cell segmentation |
| flowio-flow-cytometry | toolkit | FCS file parsing for flow cytometry |
| histolab-wsi-processing | toolkit | Whole slide image processing |
| imaging-data-commons | database | NCI cancer imaging dataset access |
| napari-image-viewer | toolkit | Multi-dimensional image viewer |
| nnunet-segmentation | pipeline | Self-configuring medical image segmentation |
| omero-integration | toolkit | OMERO biological image data management |
| pathml | pipeline | Computational pathology toolkit |
| pydicom-medical-imaging | toolkit | DICOM medical imaging |
| pyimagej-fiji-bridge | toolkit | ImageJ/Fiji Python bridge |
| simpleitk-image-registration | toolkit | Medical image registration and segmentation |
| trackpy-particle-tracking | toolkit | Particle tracking in microscopy |

</details>

<details>
<summary>Proteomics & Protein Engineering (10 skills)</summary>

| Skill | Type | Description |
|-------|------|-------------|
| adaptyv-bio | toolkit | Cell-free protein expression API |
| esm-protein-language-model | toolkit | ESM protein language models |
| hmdb-database | database | Human Metabolome Database |
| interpro-database | database | InterPro protein domain database |
| matchms-spectral-matching | toolkit | Mass spectra similarity matching |
| maxquant-proteomics | pipeline | MaxQuant mass spectrometry analysis |
| metabolomics-workbench-database | database | Metabolomics Workbench REST API |
| pride-database | database | PRIDE proteomics data archive |
| pyopenms-mass-spectrometry | toolkit | OpenMS Python mass spectrometry |
| uniprot-protein-database | database | UniProt protein database |

</details>

<details>
<summary>Systems Biology & Multi-omics (9 skills)</summary>

| Skill | Type | Description |
|-------|------|-------------|
| brenda-database | database | BRENDA enzyme kinetics database |
| cellchat-cell-communication | pipeline | Cell-cell communication inference |
| cobrapy-metabolic-modeling | toolkit | Constraint-based metabolic modeling |
| lamindb-data-management | toolkit | Biological data management |
| libsbml-network-modeling | toolkit | SBML biological network modeling |
| mofaplus-multi-omics | pipeline | Multi-omics factor analysis |
| muon-multiomics-singlecell | toolkit | Multi-modal single-cell analysis |
| reactome-database | database | Reactome pathway database |
| string-database-ppi | database | STRING protein interaction network |

</details>

<details>
<summary>Scientific Computing (11 skills)</summary>

| Skill | Type | Description |
|-------|------|-------------|
| aeon | toolkit | Time series ML and data mining |
| hypogenic-hypothesis-generation | pipeline | LLM-driven hypothesis generation |
| matlab-scientific-computing | toolkit | MATLAB/Octave numerical computing |
| neurokit2 | toolkit | Neurophysiological signal processing |
| nextflow-workflow-engine | toolkit | Dataflow scientific workflow engine |
| neuropixels-analysis | pipeline | Neuropixels electrophysiology analysis |
| pymoo | toolkit | Multi-objective evolutionary optimization |
| pymatgen | toolkit | Materials science structure analysis |
| snakemake-workflow-engine | toolkit | Rule-based scientific workflow engine |
| spikeinterface-electrophysiology | toolkit | Extracellular electrophysiology framework |
| uspto-database | database | USPTO patent data access |

</details>

<details>
<summary>Biostatistics (4 skills)</summary>

| Skill | Type | Description |
|-------|------|-------------|
| clinical-decision-support-documents | guide | Clinical decision support document guidelines |
| pyhealth | toolkit | Healthcare ML from EHR data |
| pymc-bayesian-modeling | pipeline | Bayesian statistical modeling |
| scikit-survival-analysis | toolkit | Survival analysis and time-to-event modeling |

</details>

<details>
<summary>Lab Automation (4 skills)</summary>

| Skill | Type | Description |
|-------|------|-------------|
| benchling-integration | toolkit | Benchling R&D platform SDK |
| opentrons-protocol-api | toolkit | Opentrons liquid handling robot API |
| protocolsio-integration | database | protocols.io experimental protocol access |
| pylabrobot | toolkit | Hardware-agnostic liquid handling automation |

</details>

<details>
<summary>Scientific Writing (3 skills)</summary>

| Skill | Type | Description |
|-------|------|-------------|
| biorxiv-database | database | bioRxiv/medRxiv preprint search |
| latex-research-posters | guide | LaTeX research poster templates |
| openalex-database | database | OpenAlex scholarly literature API |

</details>

<details>
<summary>Molecular Biology (3 skills)</summary>

| Skill | Type | Description |
|-------|------|-------------|
| plannotate-plasmid-annotation | pipeline | Automated plasmid feature annotation |
| sgrna-design-guide | guide | CRISPR sgRNA design decision framework |
| viennarna-structure-prediction | pipeline | RNA secondary structure prediction |

</details>

See [`registry.yaml`](registry.yaml) for the complete index of all 140 skills with names, types, categories, and descriptions.

---

## Contributing

SciCraft is designed so that Claude Code can author new skills with minimal human effort.

### Adding a skill with Claude Code

```
You: "Add a skill for Salmon RNA-seq quantification"

Claude reads CLAUDE.md → classifies as pipeline → picks genomics-bioinformatics
→ fetches salmon.readthedocs.io → writes SKILL.md with 8 workflow steps
→ appends to registry.yaml → runs pixi run test ✅
```

### Adding a skill manually

1. Read `CLAUDE.md` — the full authoring workflow is in Steps 1–6
2. Classify: pipeline / toolkit / database / guide
3. Pick a category from the table above
4. Use the right template from `templates/`
5. Add to `registry.yaml`
6. Run `pixi run test` — all checks must pass

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for the PR checklist and quality requirements.

### Skill request

Open an [issue](https://github.com/jaechang-hits/scicraft/issues/new/choose) using the **Skill Request** template.

---

## Validation

```bash
# Full test suite (structure, frontmatter, code block counts)
pixi run test

# Registry-only validation
pixi run validate
```

The CI pipeline runs `pixi run test` on every push and pull request.

---

## License

Content in this repository is licensed under [CC-BY-4.0](LICENSE). Individual skills note the license of their underlying tools in frontmatter.

## Acknowledgments

SciCraft builds on 100+ open-source scientific Python packages. If you find a skill useful, consider starring the underlying tool's repository and supporting its maintainers.
