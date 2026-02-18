# Skills — Workflow Guide

This directory contains life sciences **skills** in two flavors: **code-centric** (pipeline/toolkit/database) and **prose-centric** (guide).
Claude Code uses this guide to author new entries when given a topic.

## Directory Layout

```
skills_and_knowhow/
├── CLAUDE.md              ← you are here
├── registry.yaml          ← index of all entries
├── templates/
│   ├── SKILL_TEMPLATE.md          ← Pipeline-style skills (code-centric)
│   ├── SKILL_TEMPLATE_TOOLKIT.md  ← Toolkit-style skills (code-centric)
│   └── SKILL_TEMPLATE_PROSE.md    ← Guide-style skills (prose-centric)
└── skills/                ← all entries (SKILL.md per entry)
    ├── molecular-biology/
    ├── genomics-bioinformatics/
    ├── proteomics-protein-engineering/
    ├── structural-biology-drug-discovery/
    ├── systems-biology-multiomics/
    ├── cell-biology/
    ├── biostatistics/
    ├── data-visualization/
    ├── lab-automation/
    ├── scientific-computing/
    └── scientific-writing/
```

---

## Workflow: Topic → Entry (5 Steps)

When given a topic (e.g., "CRISPR guide RNA design"), follow these steps:

### Step 1. Classify — Code-centric vs Prose-centric, then Sub-type

#### 1a. Code-centric vs Prose-centric

All entries are Skills (SKILL.md). Choose the content style:

| Criteria | → Code-centric (pipeline/toolkit/database) | → Prose-centric (guide) |
|----------|---------------------------------------------|------------------------|
| Primary content | Executable code, pipelines, tool usage | Concepts, decision frameworks, best practices |
| Code blocks | 3+ substantial, runnable examples | Optional; illustrative only |
| User action | "Run this analysis" | "Understand this domain" |
| Example | "DESeq2 differential expression pipeline" | "When to use bulk vs single-cell RNA-seq" |

**Rule of thumb**: If the entry's core value is *running code*, it's code-centric. If it's *making informed decisions*, it's prose-centric (guide).

#### 1b. Sub-type

For code-centric entries, classify the sub-type (pipeline/toolkit/database). For prose-centric entries, the sub-type is always `guide`.

For code-centric entries:

| Sub-type | Characteristics | Examples |
|----------|----------------|----------|
| **Pipeline** | Input→processing→output linear flow; one analysis process | scanpy, AutoDock Vina, DESeq2, STAR aligner |
| **Toolkit** | Collection of independent functional modules; multiple use-cases | RDKit, matplotlib, pandas, BioPython, scikit-learn |
| **Database** | API wrapper for external database queries; search/retrieve pattern | PubChem, KEGG, ChEMBL, UniProt, Ensembl via gget |

**Decision question**: "Can this tool be explained as **one pipeline** (load→process→output), does it require describing **multiple independent modules**, or is it primarily an **API/database accessor**?"

- One pipeline → **Pipeline** → use `templates/SKILL_TEMPLATE.md`
- Multiple modules → **Toolkit** → use `templates/SKILL_TEMPLATE_TOOLKIT.md`
- API/database queries → **Database** → use `templates/SKILL_TEMPLATE_TOOLKIT.md` with database adaptations (see Database Skills section below)
- Prose-centric guide → **Guide** → use `templates/SKILL_TEMPLATE_PROSE.md`

**Database skills**: Tools that wrap external databases/APIs (e.g., PubChemPy, gget, bioservices) use the Toolkit template but with these adaptations. **Boundary clarification**: tools that download static dataset files for local use (e.g., TDC, torchvision datasets, Hugging Face datasets) are NOT database skills even though they access remote servers — database skills involve interactive query-response patterns against a live API or structured data file. Dataset-download tools should be classified as Toolkit without database adaptations. **Local XML/file databases** (e.g., HMDB, DrugBank XML) that users query by parsing structured data files ARE database skills — the distinguishing factor is the query-response interaction pattern against structured records, not whether the data source is remote. For local-file databases: rate limits are N/A (note this explicitly in Prerequisites), and `time.sleep()` patterns are unnecessary:
- "Core API" modules correspond to **query types** (e.g., "Compound Search", "Similarity Search", "Bioactivity Access"), not library modules. **For SDK-based tools** (e.g., `chembl_webresource_client`), "query type" maps to the SDK's entity/endpoint categories (e.g., `new_client.molecule`, `new_client.target`, `new_client.activity`) — each entity category becomes a Core API module
- Add an **"API Rate Limits"** note in Prerequisites or as a subsection of Key Parameters
- Include `time.sleep()` patterns in code examples to demonstrate rate-limit compliance. **SDK exception**: for tools with a dedicated Python client that handles rate limiting internally (e.g., `chembl_webresource_client`), documenting rate limiting as client-managed in Prerequisites/Best Practices is sufficient — adding `time.sleep()` would be misleading
- Key Parameters table should include a "Function/Endpoint" column instead of "Module"
- **When a Database skill has 5+ API operations** sharing a base URL (e.g., KEGG with 7 operations), define a reusable helper function in Quick Start. Core API sections should use this helper rather than repeating raw HTTP calls in every code block. This prevents import/URL boilerplate repetition and keeps the file readable. **Non-uniform endpoint exception**: when 1-2 endpoints have URL patterns that deviate from the common structure (e.g., positional parameters, special path formats), document those endpoints with direct `requests.get()` calls instead of forcing them through the helper. Add a brief note explaining the deviation (e.g., "Note: MetStat uses positional semicolons, not the standard context/input/value pattern"). **Accuracy always takes precedence over helper function consistency** — inventing plausible-looking but incorrect syntax to fit the helper is the most common Database skill accuracy failure. **SDK exception**: for tools with a dedicated Python client (e.g., `new_client.molecule`), the client object itself serves as the helper — no additional wrapper function needed
- **Reference files enumerating available databases/tables/search fields** should be consolidated into a Key Concepts subsection (e.g., "Available Databases", "Searchable Fields") rather than dropped silently during migration
- **If the database returns data that is conventionally visualized** (e.g., PAE matrices as heatmaps, pLDDT distributions as bar plots, interaction networks), include at least one visualization code block in Common Workflows or Recipes. Database skills should not stop at data retrieval — showing what users do with the data prevents a common capability gap. **Delegation to Related Skills** is acceptable only if the Related Skills entry is explicitly listed in the Related Skills section AND covers equivalent visualization — otherwise include inline. **`plot=True` parameters**: a code block that passes `plot=True` (or equivalent rendering parameter) to an API function counts as a visualization code block if the output is a rendered figure — no separate matplotlib/plotly code is required in that case
- **If the database requires an external identifier as input** (e.g., UniProt accession for AlphaFold, gene symbol → Ensembl ID for expression databases), include a brief ID resolution snippet in Quick Start or Prerequisites, or explicitly note in Prerequisites which upstream tool provides the required identifiers (e.g., "Requires UniProt accession — use uniprot-protein-database skill for ID mapping from PDB/gene name")
- **For API reference files covering 6+ endpoints**: migrate the top 4-5 most-used endpoints with full parameter code blocks into Core API sections, and place the remaining endpoints in the Key Concepts endpoint summary table with parameter notes. Document this consolidation explicitly in the Bundled Resources section. **Reference triage**: prefer consolidating inline files whose content is already partially covered in Core API code (e.g., an api_reference that duplicates endpoint parameters). Preserve as external `references/` files that are purely lookup-oriented (field tag tables, query template libraries) where the table format itself is the primary value
- **Per-section line budgets** (Database skills with 6 modules, 550-line target): Frontmatter+Overview+When to Use+Prerequisites: ~40 lines. Quick Start: ~30 lines. Core API (6 modules): ~200 lines (~35/module average — complex modules like search/query may use 50+ lines if simpler modules use 15-20; the per-module number is an average, not a hard cap). Key Concepts: ~50 lines. Common Workflows (3): ~90 lines (~30 each). Key Parameters+Best Practices: ~30 lines. Common Recipes (3): ~50 lines (~17 each). Troubleshooting+Bundled Resources+Related Skills+References: ~60 lines. **For 7+ module database skills**: extend Core API budget to ~250 lines (keeping ~35/module). If this pushes the total above 550, either merge the 2 most closely related contexts into one module (e.g., Gene + Protein), or move the 1-2 least-used contexts to a compact table in Key Concepts with parameter notes instead of full code blocks. **Write to budget on first pass** — do not write expansively and then trim iteratively, as this wastes effort and risks cutting important content. Code blocks should target 10-20 lines (Core API), 20-30 lines (Workflows), 10-15 lines (Recipes)

**Hybrid cases**: Some tools have both a canonical workflow AND independent modules/model types. Use this decision heuristic:
- If the tool has **one workflow with interchangeable model variants** (e.g., PyMC: same 8-step Bayesian cycle for any model type; GATK: same pipeline for any organism) → **Pipeline** with model variants documented in **Common Recipes** as "Recipe: {Model Type}" (e.g., "Recipe: Hierarchical Model", "Recipe: Logistic Regression"). **Recipe completeness**: every model type listed in the Key Concepts Model Variants table must either have a full Recipe with code OR an explicit note redirecting to `references/` or documenting omission. When adding all variant Recipes would exceed the main file line limit, prioritize the **3-4 most common variants** as full Recipes and note remaining variants with "see references/" or "see official docs" — but these redirections must appear in the Model Variants table, not be silently absent
- If the tool has **independent modules that CAN be used in pipelines** but are also useful standalone (e.g., BioPython, scikit-learn) → **Toolkit** with linear use-cases in **Common Workflows**
- Key test: "Does the user always follow the same steps, just plugging in different models/parameters?" → Pipeline. "Does the user pick different modules for entirely different tasks?" → Toolkit

**Document generation topics** (e.g., latex-posters, clinical-decision-support, scientific-slides, pptx-posters): These produce structured documents (LaTeX/PDF, PPTX) from templates + domain knowledge. Classify as **Guide** (prose-centric) when the core value is *knowing the document structure, formatting rules, and domain standards* (e.g., GRADE grading, CONSORT reporting). Classify as code-centric only if the tool has a standalone Python API for programmatic document generation. For Guide document-generation entries:
- Use the `Companion Assets` section to include LaTeX templates, style files, or example documents in an `assets/` subdirectory
- In the `Workflow` section, name specific figure types and visual elements that should be generated (e.g., "Kaplan-Meier curves with number-at-risk tables")
- In `Best Practices`, prefix mandatory requirements with **"MANDATORY:"** to distinguish from recommended practices (e.g., "**MANDATORY:** Every poster must include at least 2 figures")
- In `Related Skills`, list the tools needed for figure/table generation (matplotlib, plotly, scientific-schematics) as operational dependencies, not just informational references

**ML model / deep learning tools** (e.g., ESM, AlphaFold, transformers): Pretrained model wrappers that require GPU or cloud API. Classify as **Toolkit** with these adaptations:
- In **Prerequisites**, document: (1) GPU/VRAM requirements per model size, (2) cloud API alternative if available, (3) model weight download size
- Add a **Key Concepts** section with a "Model Selection Guide" table comparing model variants (name, size, VRAM, use case)
- In **Core API**, organize by **capability** (generation, embedding, prediction), not by model architecture internals
- If the tool has both local and cloud API modes, show local examples in Core API and cloud API as a separate module or Recipe
- In **Key Parameters**, include inference parameters (temperature, num_steps, batch_size) alongside API parameters
- Note: code verification may be impossible without GPU — annotate expected output shapes/values in comments rather than relying on `print()` statements for correctness

**Model zoo frameworks** (e.g., scvi-tools, Hugging Face transformers, torchvision): Frameworks with **5+ models** sharing a unified API but targeting different data modalities or tasks. Classify as **Toolkit** with these adaptations:
- In **Core API**, document the 2-3 most important/common models as full sections with code. For remaining models, mention in the Model Selection Guide table only — do NOT try to cover all models inline
- The **Model Selection Guide** table (in Key Concepts) is the primary navigation aid. Structure columns as: **Data Modality** → **Model** → **Key Feature** → **Use When**. Lead with modality (what experiment did you run?), then analysis goal
- In **Key Concepts**, document the **unified API pattern** (e.g., `setup→create→train→extract`) prominently — this is the user's primary mental model for navigating the zoo
- When there are **4+ model categories** (e.g., RNA-seq, ATAC-seq, multimodal, spatial), create `references/` files organized by category (e.g., `models-scrna-seq.md`, `models-spatial.md`). The main SKILL.md covers shared API + top models; references cover the full zoo
- This differs from the "Pipeline-with-variants" pattern (PyMC): Pipeline-with-variants has one workflow with interchangeable components; Model zoos have one API with models targeting fundamentally different data types

**Platform integration tools** (e.g., benchling-integration, latchbio-integration, omero-integration): SaaS platform connectors requiring API credentials. Classify as **Toolkit** (Database sub-type adaptations) with these additions:
- In **Prerequisites**, document authentication setup — enumerate **all methods the platform supports** (API key, OAuth, SSO/OIDC, etc.), not just the most common ones. Don't assume only API key and OAuth exist
- Organize Core API by **capability domain** (e.g., registry CRUD, inventory management, event streaming, analytics), not by internal SDK structure. CRUD organization applies within each domain, but some domains are not CRUD — event subscriptions, data warehousing, webhooks, and analytics are separate interaction patterns that need their own Core API modules
- Include error handling patterns for authentication failures, rate limits, and pagination. If the SDK provides **typed exception classes** (e.g., `NotFoundError`, `ValidationError`), show granular catch blocks rather than a single generic catch
- Note in description that the skill requires an active platform account
- Platform integrations often have extensive API surfaces. Consider creating `references/` for: (a) REST API endpoint reference (for non-SDK users or debugging), (b) detailed authentication guide (if 3+ auth methods), (c) advanced SDK patterns (custom HTTP clients, multi-tenant config)

**Non-Python tools** (e.g., MATLAB, R packages): Tools where the primary runtime is not Python. Classify as **Toolkit** with these adaptations:
- Show code examples in the tool's native language (MATLAB, R), not Python
- In Prerequisites, note installation requirements for the external runtime
- If Python integration exists (e.g., `matlab.engine`, `rpy2`) AND the tool will be used alongside Python-based agents/tools, promote Python integration to a **full Core API module** (not just a Recipe) with bidirectional examples (calling Python from the tool AND calling the tool from Python). Include data type conversion tables in a Key Concepts subsection
- In the description, note the primary language so agents know what code to generate
- For tools with **multiple runtimes or compatibility layers** (MATLAB/Octave, Python 2/3, R/Bioconductor versions), compatibility differences count as a capability domain. Add a Key Concepts subsection covering the most impactful differences (5-10 items), or a `references/` file if differences exceed 20 items

**Visualization toolkits** (e.g., seaborn, plotly, bokeh, altair): Tools where nearly every module produces a visual output. Classify as **Toolkit** with these adaptations:
- Organize Core API by **plot category** (Distribution, Categorical, Relational, Matrix, etc.), not by abstraction level
- Include a **"Styling & Theming"** module in Core API covering palettes, themes, contexts, and global configuration — this is a cross-cutting concern that applies to all other modules
- In **Key Concepts**, document any dual-interface patterns (e.g., seaborn's axes-level vs figure-level functions, plotly Express vs Graph Objects) as a comparison table
- If the library has a modern declarative API alongside its traditional API (e.g., `seaborn.objects`, Altair), cover the traditional API in Core API and mention the modern API in a Key Concepts subsection or dedicated Core API module

**Database skills with scale-dependent queries** (e.g., CELLxGENE Census, large genomic databases): When the tool requires different query strategies depending on data scale (e.g., in-memory for <100k rows vs streaming for >100k), add:
- A **"Query Strategy"** subsection in Key Concepts with a decision table: condition → recommended approach → Core API module reference
- In Common Workflows, show at least one workflow that includes the size-estimation → strategy-selection → query execution sequence

**Hardware/protocol tools** (e.g., Opentrons, PyLabRobot, instrument control APIs): Tools where the output is a structured file (protocol, configuration) uploaded to and executed by hardware. Classify as **Toolkit** with these adaptations:
- In **Key Concepts**, document the **protocol file structure** — mandatory elements (metadata, entry points), runtime constraints (restricted imports, execution model), and hardware-specific requirements (deck layouts, labware compatibility)
- In **Common Workflows**, each workflow should be a **complete, standalone protocol file** that users can copy whole-file and adapt. Do NOT fragment protocols into module-level snippets — the value is seeing the full parameterized protocol. End workflows with the deployment step (e.g., "save and simulate with `opentrons_simulate protocol.py`")
- In **Key Concepts** or **Prerequisites**, add a hardware differences table (e.g., OT-2 vs Flex deck slots, pipette models, module support) and physical constraints (slot conflicts, labware-module compatibility)
- The code quality rule "runnable as-is" means **simulatable** for protocol tools — specify the simulation command in Prerequisites
- See also: migration handling of whole-file template scripts below

**Data infrastructure tools** (e.g., LaminDB, DVC, Kedro, latchbio): Tools whose primary purpose is data management, versioning, lineage tracking, or provenance — not analysis itself. Classify as **Toolkit** with these adaptations:
- Organize Core API by **data lifecycle stage** (ingest/create, annotate/validate, query/filter, track lineage, organize/version) rather than by independent functional modules
- **Integrations are a core capability**, not an afterthought. If the tool integrates with 5+ external systems (workflow managers, MLOps, storage backends), treat integrations as a Core API module or dedicated Common Workflow. Create `references/integrations.md` if >3 integration patterns have substantial code
- **Setup and deployment** is also a core capability for self-hosted infrastructure. Migrate deployment patterns (local dev, cloud production, multi-user) to a Core API module "Setup & Deployment" or `references/setup-deployment.md`. Prerequisites covers only minimal first-time setup
- Key test to distinguish from Platform Integration tools: "Is this self-hosted open-source or a SaaS platform requiring an account?" Data infrastructure = self-hosted; Platform = SaaS

**Cross-cutting tools**: If a tool spans multiple categories (e.g., gget covers genomics, proteomics, and disease data), classify under the **primary use-case category** and note the secondary categories in the description. The agent's skill matching uses the description field, not the directory path.

### Step 2. Choose Category

Pick the best-fit category directory under `skills/`:

| Category | Scope |
|----------|-------|
| `molecular-biology` | PCR, cloning, CRISPR, gene expression, central dogma, gene regulation |
| `genomics-bioinformatics` | NGS, alignment, variant calling, RNA-seq, genome architecture |
| `proteomics-protein-engineering` | Mass spec (proteomics AND metabolomics), protein design, structure prediction |
| `structural-biology-drug-discovery` | Docking, virtual screening, ADMET, drug design principles |
| `systems-biology-multiomics` | Pathway analysis, multi-omics integration, network biology |
| `cell-biology` | Imaging, flow cytometry, cell culture analysis, digital pathology |
| `biostatistics` | Statistical tests, experimental design, power analysis, study design |
| `data-visualization` | Plotting libraries, figure generation, scientific graphics |
| `lab-automation` | Robotics, LIMS, automated protocols |
| `scientific-computing` | General-purpose math/computation: symbolic math, numerical methods, MATLAB, data infrastructure, ML tools, geospatial, EDA, reproducibility |
| `scientific-writing` | Paper structure, figure design, peer review, research ideation and brainstorming, presentation skills |

**Cross-domain entries**: When an entry spans all scientific domains (e.g., exploratory data analysis, data visualization methodology, reproducibility frameworks), place it in the category that best matches the entry's **primary audience** — who will search for this? Note the cross-domain nature in the description field so agent skill-matching works across categories. If no category fits well, prefer `scientific-computing` (for tool/computation/methodology topics) as the catch-all category

### Step 3. Gather Reference Material

Choose reference sources based on the entry type:

**For code-centric Skills** (primary — use these first):

| Source | When to use | URL pattern |
|--------|-------------|-------------|
| Official documentation | API reference, parameters, usage patterns | `{tool}.readthedocs.io`, `{tool}.org/docs/` |
| GitHub README / examples | Quick start, installation, version notes | `github.com/{org}/{tool}` |
| PyPI / conda-forge | Dependencies, version compatibility | `pypi.org/project/{tool}` |
| Published paper | Algorithms, citation, validation data | DOI link |
| Existing claude-scientific-skills entry | Baseline for migration (see Migration section) | Local path |

**For wet-lab / protocol-heavy Skills** (secondary):

| Source | License | URL |
|--------|---------|-----|
| protocols.io | CC-BY | https://www.protocols.io/ |
| Bio-protocol | CC-BY | https://bio-protocol.org/ |
| OpenWetWare | CC-BY-SA | https://openwetware.org/ |
| STAR Protocols | CC-BY | https://star-protocols.cell.com/ |
| Galaxy Training | CC-BY | https://training.galaxyproject.org/ |
| Bioconductor workflows | Artistic-2.0 | https://bioconductor.org/packages/ |

**Rules**:
- Always cite the source in the References section
- Respect license terms (CC-BY requires attribution)
- Prefer peer-reviewed protocols and official docs over blog posts
- Adapt and synthesize; do NOT copy-paste verbatim

### Pre-Write Retention Budget Check (for migrations)

**Before writing ANY entry from an existing source**, determine whether you need reference files by performing this budget check:

1. **Calculate denominator**: Count original main file + ALL reference files total lines. Exclude `scripts/` and `assets/` directories (they convert to inline code or different structures).
2. **Estimate planned main file**: Decide if main SKILL.md will be 300–400 lines or 400–500 lines.
3. **Calculate aggregate retention**: If planned main ÷ original total < 0.45, you CANNOT go self-contained — you need reference files to reach 45–65% aggregate retention.
4. **Plan reference files BEFORE writing**: If aggregate < 0.45, calculate how many reference files you need. Use the formula: planned aggregate = (planned main lines + planned references lines) / original total. Work backward: if you want 50% aggregate and original is 2,000 lines, you need 1,000 lines total. If planned main is 450, you need 550 lines in references. **For stubs (3,000+ total lines)**: the main SKILL.md at 550-650 lines still leaves a large gap. Example: 3,500-line original needs ~1,575 lines at 45%. Main at 600 leaves ~975 lines needed in references — that's 2-3 substantial reference files at 300-500 lines each, NOT one 100-line file. Plan the reference file count AND line budgets together.

5. **Set per-reference-file line budgets**: For each planned reference file, calculate its target line count BEFORE writing. Formula: if a reference file consolidates N original files totaling S lines, target `S × 0.40` lines (40% retention midpoint). For 2-source files, floor is `S × 0.35`; for 3+ source files, floor is `S × 0.30`. Write to the budget — do not write expansively and then trim, as iterative trimming wastes effort and risks cutting important content to meet arbitrary targets. **Compact-first writing**: write reference files to their target budget on the first pass. If the first draft exceeds the target by >15%, restructure before continuing rather than trimming line-by-line after completion.

**Why this matters**: Authors often commit to "self-contained" consolidation without doing this math, then finish writing and discover they've dropped 20–30% of capabilities silently. Do the calculation on paper BEFORE opening the text editor. This prevents post-hoc over-compression and silent capability loss.

### Step 4. Author the Entry

Create the entry directory and file:

```
skills_and_knowhow/skills/{category}/{entry-name}/SKILL.md
```

**Entry name convention**: lowercase, hyphen-separated. Use `{tool-name}-{purpose}` format for clarity (e.g., `pydeseq2-differential-expression`, `scanpy-scrna-seq`). The tool name alone (e.g., `pydeseq2`) is acceptable but a descriptive suffix is preferred when the tool serves a specific analysis type.

Use the appropriate template:
- Code-centric (Pipeline) → `templates/SKILL_TEMPLATE.md`
- Code-centric (Toolkit) → `templates/SKILL_TEMPLATE_TOOLKIT.md`
- Prose-centric (Guide) → `templates/SKILL_TEMPLATE_PROSE.md`

#### SKILL.md Format Rules — Pipeline Sub-type (claude-scientific-skills compatible)

For tools with a linear input→processing→output flow (e.g., scanpy, AutoDock Vina, DESeq2).

1. **Frontmatter** (YAML between `---`): `name`, `description`, `license` (all required)
   - **`license`**: Use the underlying tool's license if known (e.g., `MIT` for PyDESeq2). Default to `CC-BY-4.0` for original content
2. **Sections** (in order):
   - Overview — what this skill does, 2-3 sentences
   - When to Use — bullet list of use cases (5+ items). Write from the **user's task perspective** (e.g., "Identifying differentially expressed genes between conditions"), NOT from the agent's keyword-matching perspective
   - Prerequisites — required packages/data/environment
   - Quick Start (optional but recommended) — complete minimal pipeline in a single code block (10-20 lines). Lets users copy-paste and run immediately without reading the full Workflow
   - Workflow — numbered steps, **each step has its own code block** (target 5-8 steps). **Visualization steps** (plots that are standard output of the pipeline) belong here as Workflow steps, not in Common Recipes
   - Key Parameters — table of tunable parameters with defaults, ranges, and effects
   - **Key Concepts** (optional — use when the tool has essential reference material): Prior/distribution selection guides, diagnostic threshold tables, domain-specific terminology. Place after Key Parameters. For Pipeline-with-variants tools (see Hybrid cases), include a "Model Variants" or "Selection Guide" subsection showing which variant to use when
   - Common Recipes — 2-4 self-contained snippets for **alternative approaches or optional extensions** beyond the main workflow (e.g., batch correction, multi-contrast testing, QC diagnostics). For Pipeline-with-variants tools, use Recipes to show each model variant (e.g., "Recipe: Hierarchical Model", "Recipe: Logistic Regression") with full code. Do NOT duplicate Workflow steps here
   - Expected Outputs — list of output files/figures with descriptions
   - Troubleshooting — table of problem/cause/solution (5+ rows). Code snippets within Troubleshooting cells are encouraged but do NOT count toward the code block minimum
   - Bundled Resources (optional) — describe any `references/` files included with the entry
   - References — sources with URLs
3. **Code blocks**: **each Workflow step must have 1 code block** (typically 5-8 total in Workflow) + **each Recipe must have 1 code block** (2-4 additional) + Quick Start (1, optional). Total target: **10+ code blocks** (counted from Prerequisites + Workflow + Recipes only)
4. **Description**: max 1024 characters, focused on the agent's decision ("when should I use this?")
5. **Code quality**: all code blocks must be runnable as-is with sample data or clear placeholders. Include `print()` statements showing expected output shape/size
6. **Bundled resources** (optional but recommended for complex skills):
   - Create a `references/` subdirectory inside the entry folder
   - Typical files: `api_reference.md` (function lookup), `plotting_guide.md` (visualization), `standard_workflow.md` (detailed step-by-step with decision points)
   - Each reference file provides deeper detail than the SKILL.md itself — agents read them on demand
   - List and describe each file in the "Bundled Resources" section of SKILL.md. Each description must include three elements: (1) what the file covers, (2) what original content was relocated inline rather than into the reference (if migrating), and (3) what was intentionally omitted with a one-line reason. This prevents future maintainers from mistaking relocated content for coverage gaps. **Format hint**: for readability, structure longer Bundled Resources descriptions with labeled sub-items or separate sentences per element (e.g., "Covers: ... Relocated inline: ... Omitted: ..."). A single dense paragraph satisfying all three elements often becomes hard to scan

#### SKILL.md Format Rules — Toolkit Sub-type

For tools that are collections of independent functional modules with multiple use-cases (e.g., RDKit, matplotlib, pandas, BioPython).

1. **Frontmatter** (YAML between `---`): `name`, `description`, `license` (all required)
2. **Sections** (in order):
   - Overview — what this toolkit does, 2-3 sentences
   - When to Use — bullet list of use cases (5+ items). For Toolkits, **include 1-2 comparison notes** stating when to use alternative tools instead (e.g., "For quick gene lookups use gget instead"; "For high-level molecular API use datamol instead"). This helps agents route to the right skill. **For domain-spanning toolkits** (tools that touch multiple scientific domains, e.g., PyG covers molecular, social, knowledge graphs, point clouds): scope alternative comparisons to the **primary competing tool** (e.g., DGL for PyG) and the **nearest non-overlapping tool** (e.g., NetworkX for PyG). Do not list alternatives for every sub-domain — note sub-domain coverage in the description field for agent routing instead. **Paradigm-level alternatives are acceptable**: when the tool represents a distinct computational paradigm (e.g., discrete-event simulation), alternatives may be paradigm-level (e.g., "For continuous-time ODE systems, use SciPy solve_ivp") rather than same-task-different-tool comparisons
   - Prerequisites — required packages/data/environment. For database skills, include API rate limits here
   - Quick Start (optional — recommended for toolkits with 6+ Core API modules) — minimal example showing the most common use-case in a single code block (5-15 lines). Omit for small toolkits (4-5 modules) where the first Core API module already serves as an entry point. **Always recommended for Database skills** regardless of module count — showing the typical query-retrieve-analyze pattern in a single block is essential for this sub-type
   - **Core API** — functional modules organized by subsection (4-8 modules), each with 1-2 code blocks
   - **Key Concepts** (optional but recommended when the tool has a non-obvious data model) — explain domain-specific abstractions that users must understand to read the code correctly (e.g., AnnData's `obs`/`var`/`layers` structure, COBRApy's `DictList`, exchange reaction sign conventions, sparse matrix vs dense). 2-4 subsections with short code examples. Place after Core API, before Common Workflows. **Also use Key Concepts for cross-cutting lookup tables** that don't belong to a single Core API module — e.g., data type reference tables, mode option tables (r/r+/w/a/w-), chunk size calculation guides, error code tables, **enumeration catalogs** (supported unit lists, supported file formats, available coordinate frames). These should appear in Key Concepts even if they are referenced from within individual Core API modules. Purely enumerative content (catalogs of supported X) that doesn't fit into code blocks belongs here as compact tables, not silently omitted. **Enumeration in code comments**: when migrating enumeration catalogs (enrichment categories, supported formats, response sections, statistical methods) that are too detailed for a standalone table but must not be silently dropped, listing them in a code comment within the relevant Core API block is an acceptable compact approach (e.g., `# Categories: GO, KEGG, Pfam, InterPro, SMART, UniProt Keywords`). This is preferable to omitting the enumeration entirely
   - **Common Workflows** — end-to-end use-case pipelines (2-4 workflows). At least **2 must be complete runnable code blocks** (text-only workflows do NOT count toward this minimum). For large toolkits (6+ modules), additional workflows may be text-only numbered steps **only if they are conceptually simple combinations of Core API modules**. **Never use text-only format for complex, error-prone operations** (e.g., model building from scratch, custom pipeline construction) — these always need executable code even if it makes the file longer. Text workflows should reference which Core API modules they use. **Decision heuristic**: a workflow qualifies as text-only if (a) every step maps 1:1 to a single Core API subsection already having a code block (i.e., the step uses exactly one module's function — not two modules' outputs combined), AND (b) the workflow introduces no new parameters, error conditions, or type conversions beyond what the referenced Core API block already shows. If any step requires chaining outputs from multiple Core API calls, handling new data types, or configuring parameters not shown in Core API, write full code. **Cross-reference exception**: when a text-only workflow step references two modules but the combination is a well-known pattern already shown in a code block elsewhere in the entry (e.g., in Core API or Recipes), the text-only format is acceptable provided the cross-reference is explicit (e.g., "Step 4: Add event signaling for backpressure — see Core API Module 3 barrier pattern"). **Reference file code exception**: a text-only workflow in the main SKILL.md is acceptable for complex multi-module pipelines if a full code version exists in a `references/` file — but the text-only workflow must explicitly cross-reference the reference file (e.g., "See references/api_workflows.md Workflow A for complete code")
   - Key Parameters — table of tunable parameters with defaults, ranges, and effects. For Toolkit skills, add a **Module** column (or **Function/Endpoint** for database skills) to indicate which module each parameter belongs to. For universal parameters that apply across all modules, the Module column can say "All" or be omitted if the tool doesn't have clearly distinct modules
   - **Best Practices** (optional but recommended for large toolkits) — important usage patterns, anti-patterns, and domain-specific guidelines (e.g., "Always use Pipelines in scikit-learn", "Use OO interface in matplotlib"). 3-7 items with brief code examples where helpful. **Performance micro-patterns** (operator shortcuts like `<<` for fast assignment, string formatting helpers, pre-computation tricks) belong here with code snippets — they are too small for their own Core API section but too important to omit
   - Common Recipes — 2-4 self-contained snippets for additional tasks
   - Troubleshooting — table of problem/cause/solution (5+ rows). If a solution requires multi-line code, use a **hybrid format**: table for simple fixes + separate subsections for code-heavy solutions. **Troubleshooting vs Common Pitfalls**: Troubleshooting covers *technical errors* (error messages, crashes, wrong output). If the tool also has *conceptual pitfalls* (methodological mistakes, wrong model choice), add them as numbered items inside the **Best Practices** section as "Anti-patterns" or weave them into Best Practices as "Don't..." items. Do NOT create a separate "Common Pitfalls" section for code-centric Skills — that pattern is reserved for Guide (prose-centric) entries
   - Bundled Resources (optional) — describe any `references/` files included with the entry
   - References — sources with URLs
3. **Code blocks**: Core API (8-16 blocks, 1-2 per module) + Common Workflows (2-4 blocks) + Recipes (2-4 blocks) + Prerequisites (1). **Simple minimum**: **12 code blocks** (for toolkits with 4-5 modules) or **15+ code blocks** (for toolkits with 6+ modules). Count only blocks in Prerequisites, Core API, Common Workflows, and Common Recipes — Troubleshooting code snippets are excluded
4. **Description**: max 1024 characters, focused on the agent's decision ("when should I use this?")
5. **Code quality**: all code blocks must be runnable as-is with sample data or clear placeholders. Include `print()` statements showing expected output shape/size. **Simplification guard**: when condensing complex code (e.g., `Lambda(custom_function)` patterns, multi-step pipelines) into simpler examples for the main SKILL.md, ensure the simplified version produces equivalent results. If simplification changes behavior, preserve the correct version in the reference file and note the simplification in the SKILL.md code comment
6. **Core API vs Common Workflows**:
   - **Core API**: each subsection covers one functional module (e.g., "Molecular I/O", "Descriptors", "Fingerprints"). Focus on individual functions/classes with short examples
   - **Common Workflows**: each is a complete pipeline combining multiple Core API modules for a real use-case (e.g., "Virtual Screening Cascade", "ADMET Profiling"). These are longer, end-to-end examples
7. **Expected Outputs** section is **optional** for Toolkit skills (use-cases vary too much for a single outputs list)
8. **Bundled resources**: same rules as Pipeline sub-type
9. **Reference triage** (applies to all Toolkits, not just Database skills): When deciding whether original reference content stays as a `references/` file or gets consolidated inline, prefer consolidating inline when the content is already partially covered by Core API code blocks (e.g., an api_guide that duplicates endpoint parameters shown in Core API). Preserve as external `references/` files content that is purely lookup-oriented (parameter catalogs, field tag tables, query template libraries, 60+ parameter references) where the table format itself is the primary value. **Prefer self-contained SKILL.md** — put essential functions and examples directly in Core API modules. Only split into `references/` when:
   - SKILL.md exceeds **~500 lines** even after trimming redundant examples
   - The tool has **50+ API functions** worth documenting beyond what Core API covers
   - There are **format-specific details** (e.g., file format specs, protocol schemas) that would clutter the main flow
   - The tool is a **model zoo with 4+ model categories** — create category-level references (e.g., `models-scrna-seq.md`, `models-spatial.md`) while keeping shared API + top models in SKILL.md
   - There are **essential lookup tables** (API version compatibility, hardware compatibility matrices, error code tables) that are too detailed for inline inclusion but too important to omit
   - **Do NOT** create `references/` just because the original had them — many originals use stub-like "See: references/X.md" patterns that make the SKILL.md useless without those files. A self-contained SKILL.md with good Core API modules is always better than a stub SKILL.md + detailed references/
10. **CLI + Python dual interface**: If the tool has both CLI and Python interfaces, determine which is the **primary user interface**:
   - **Python API is primary** (e.g., gget, pysam): show Python examples in SKILL.md, note CLI equivalents in comments
   - **CLI is primary** (e.g., deeptools, samtools, GATK): show bash/CLI examples in SKILL.md. These tools are Python *packages* but their user interface is CLI commands — write code blocks in bash, not Python
   - Key test: "Does the user typically write `import tool` or `tool_command --args`?" → Python vs CLI
   - Do not duplicate every example in both interfaces — pick the primary one
11. **Related Skills** (optional but recommended for ecosystem tools): After Troubleshooting (or after Bundled Resources if present), add a **Related Skills** section listing connected tools with brief connection descriptions. This is especially important for tools that are part of a larger ecosystem (e.g., anndata → scanpy, scvi-tools; RDKit → datamol, medchem). Format: `- **tool-name** — connection description`. **Non-existent entries**: when referencing a skill that does not yet exist in `registry.yaml`, append `(planned)` to the entry name (e.g., `- **scanpy-scrna-seq** — upstream analysis` vs `- **pathml-spatial-omics (planned)** — multiplexed imaging`). This prevents agents from attempting to read non-existent files
12. **Ecosystem tools**: When the tool is part of a well-known ecosystem (scverse, tidyverse, PyTorch ecosystem, etc.), add a brief **"Ecosystem Integration"** subsection inside Common Workflows or as the last Core API module. Show 2-3 code snippets demonstrating how this tool hands off data to other ecosystem members. This prevents users from needing to read multiple skills just to understand the data flow. Keep it brief — full usage of the downstream tool belongs in that tool's own skill

#### Guide SKILL.md Format Rules — Prose-centric (progressive disclosure compatible)

For entries where the core value is domain knowledge, decision frameworks, and best practices (sub_type: guide).

1. **Frontmatter** (YAML between `---`): `name`, `description`, `license` (all required, same spec as code-centric SKILL.md)
2. **Sections** (in order):
   - Overview — what this guide covers, 2-3 sentences
   - Key Concepts — core terminology and definitions (3+ subsections)
   - Decision Framework — flowchart or decision tree for common choices. Use ASCII tree diagrams and/or decision tables
   - Best Practices — do's with rationale (5+ items, numbered)
   - Common Pitfalls — don'ts with explanations (5+ items). Each pitfall must include a "*How to avoid*" sub-item
   - **Workflow** (optional but recommended when the guide has a clear process) — high-level numbered steps for the standard process. More structured than Protocol Guidelines: include substeps and decision points. Use this when there's a well-defined sequence (e.g., manuscript development: Planning → Drafting → Revision → Submission)
   - Protocol Guidelines — high-level protocol steps (not full code). Use when there's no single well-defined workflow but rather general procedural guidance
   - Further Reading — curated references with URLs (3+ items)
   - Related Skills — links to relevant SKILL.md entries with brief connection description
3. **Description**: max 1024 characters, focused on the agent's decision ("when should I read this?")
4. **Companion assets**: If the guide has associated templates, style files, or other non-code assets, create an `assets/` subdirectory in the entry folder. List and describe each asset in a "Companion Assets" section after Related Skills. Example: LaTeX templates, configuration files, checklists, quality control checklists
5. **Bundled resources**: Guide entries may include a `references/` subdirectory for detailed reference material when the topic has depth exceeding ~400 lines. Describe each file in a "Bundled Resources" section (before Companion Assets). Typical files: detailed design guides, extended parameter tables, curated resource lists, comparison matrices, domain-specific reference cards. Same rules as code-centric skill bundled resources: prefer self-contained SKILL.md, only create `references/` when content genuinely exceeds the main file's capacity
6. **Adjacent domain content**: When the guide naturally extends into adjacent domains (e.g., poster creation → poster presentation, manuscript writing → peer review response), include a brief summary in the Workflow section (1-2 sentences per adjacent topic) and note the adjacent domain in Related Skills. Do not try to cover adjacent domains fully — that's a separate entry

### Step 5. Update registry.yaml

Add the new entry to `skills_and_knowhow/registry.yaml`:

```yaml
entries:
  - name: "entry-name"
    type: skill
    sub_type: pipeline    # "pipeline", "toolkit", "database", or "guide". Use "guide" for prose-centric entries. Use "database" for tools whose primary purpose is querying/accessing an external database via API or local XML/file parsing (e.g., DrugBank, ChEMBL, PubMed). Use "toolkit" for general-purpose libraries even if they include some database access
    category: "genomics-bioinformatics"
    path: "skills/genomics-bioinformatics/entry-name/SKILL.md"
    description: "Brief description"
    date_added: "YYYY-MM-DD"
```

---

## Quality Checklist

Before finalizing any entry, verify:

**Frontmatter:**
- [ ] Has `name`, `description`, `license` fields
- [ ] `description` ≤ 1024 characters
- [ ] `name` ≤ 64 characters
- [ ] `license` matches the underlying tool's license (or CC-BY-4.0 for original content)

**Structure:**
- [ ] All entries use SKILL.md filename
- [ ] Correct sub-type: Pipeline, Toolkit, Database (code-centric) or Guide (prose-centric) — see Step 1b
- [ ] All required sections present in correct order (see format rules above)
- [ ] Entry directory name is lowercase, hyphen-separated (`{tool-name}-{purpose}` preferred)

**Pipeline Skills — code depth:**
- [ ] Each Workflow step has its own code block (5-8 steps)
- [ ] Standard visualization (volcano plot, heatmap, etc.) included as Workflow steps, not Recipes
- [ ] Common Recipes section has 2-4 self-contained snippets (alternative approaches, not workflow duplicates)
- [ ] Total code blocks ≥ 10 (Prerequisites + Workflow + Recipes; Troubleshooting code excluded)
- [ ] Key Parameters table has 5+ rows with defaults and ranges
- [ ] Troubleshooting table has 5+ rows
- [ ] Quick Start section present (optional but strongly recommended for Pipeline skills)
- [ ] For Pipeline-with-variants: Key Concepts includes model/variant selection guide
- [ ] For Pipeline-with-variants: Common Recipes covers each major model variant with full code (or Model Variants table explicitly redirects to references/docs for overflow variants)

**Toolkit Skills — code depth:**
- [ ] Core API has 4-8 module subsections, each with 1-2 code blocks (8-16 total)
- [ ] Common Workflows has 2-4 complete end-to-end examples (each combines multiple Core API modules)
- [ ] Common Recipes section has 2-4 self-contained snippets
- [ ] Total code blocks ≥ 12 (4-5 modules) or ≥ 15 (6+ modules)
- [ ] Key Parameters table has 5+ rows with defaults and ranges
- [ ] Troubleshooting table has 5+ rows

**Toolkit Skills — content quality:**
- [ ] "When to Use" includes 1-2 alternative tool comparisons (e.g., "For X use Y instead")
- [ ] Common Workflows combine multiple Core API modules (not just repeat a single module's usage)
- [ ] Key Parameters table has Module/Function column for multi-module tools
- [ ] Best Practices section present for large toolkits (scikit-learn, matplotlib, etc.)
- [ ] Related Skills section present for ecosystem tools (anndata→scanpy, etc.)
- [ ] Ecosystem Integration shown via code snippets if tool is part of a larger ecosystem

**Database Skills — additional checks:**
- [ ] API rate limits documented in Prerequisites or Key Parameters
- [ ] Code examples include `time.sleep()` or rate-limit compliance patterns (or rate limiting documented as client-managed for SDK-based tools)
- [ ] Core API modules organized by query type (not by internal implementation)
- [ ] For 5+ operations: helper function defined in Quick Start and reused in Core API, OR Python SDK client object used directly
- [ ] If database returns visualizable data (matrices, distributions): at least one visualization code block in Workflows/Recipes
- [ ] If database requires external identifier input: ID resolution documented in Quick Start/Prerequisites or upstream tool noted
- [ ] Pagination/result iteration behavior documented (automatic pagination, streaming, cursor-based, or SDK-handled) — essential for large result sets
- [ ] Database/table/field catalogs from reference files consolidated into Key Concepts (not silently dropped). When the original has N field/schema tables, ALL N must appear — do not selectively migrate some while dropping others
- [ ] For APIs returning deeply nested JSON with multiple sub-modules (e.g., ClinicalTrials.gov's protocolSection/derivedSection/resultsSection): Key Concepts response structure table enumerates ALL top-level response sections, not just the most-used ones. Mark rarely-accessed sections with a brief note (e.g., "derivedSection — auto-computed fields; rarely queried directly") rather than omitting them entirely
- [ ] For 6+ endpoint APIs: top endpoints have full code in Core API, remaining in Key Concepts endpoint summary table
- [ ] UI/web interface features (saved searches, email alerts, export buttons, RSS feeds) either included as a non-code subsection in Key Concepts/Best Practices, or documented as omitted with reason (e.g., "UI features omitted — programmatic equivalents covered via API")
- [ ] References section includes official documentation URL, SDK/client repository URL, and example notebooks (if available) — these are essential for users who need to go beyond the skill file

**Guide Skills — content depth:**
- [ ] Key Concepts has 3+ subsections with clear definitions
- [ ] Decision Framework includes both ASCII tree diagram AND decision table
- [ ] Best Practices has 5+ items with rationale
- [ ] Common Pitfalls has 5+ items, each with "How to avoid" sub-item
- [ ] Workflow section present if the guide has a clear sequential process
- [ ] **Main SKILL.md is 250+ lines** (below 250 = insufficient coverage; see Rule 12 target). For originals with 2,000+ total lines, target 350-400 lines

**Content quality (all types):**
- [ ] "When to Use" items written from user's task perspective, not keyword-matching
- [ ] References cite sources with URLs (3+ references)
- [ ] Code blocks are runnable as-is (with sample data or clear placeholders)
- [ ] **Code verification**: spot-check at least 2 code blocks by mentally tracing the API calls — verify function signatures, argument names, and return types match the official docs. Common errors: wrong argument order, nonexistent parameters, incorrect return type assumptions. **REST API URL trace**: for Database skills using helper functions, trace the full URL each code block would generate (by substituting the helper's URL template with actual arguments) and compare against the documented endpoint patterns for EVERY context/module — not just the first one tested. This catches the common failure where a helper works for 5 of 7 endpoints but generates invalid URLs for the remaining 2
- [ ] **Cross-file consistency**: verify that code examples in SKILL.md and `references/` use consistent API patterns and parameter values. Common errors: different parameter format strings (e.g., `"morgan"` vs `"morgan2"`), different method names for the same operation (e.g., `filterPeakMap` vs `filterExperiment`), modernized API in one file but original API in another. Spot-check at least 1 shared API call that appears in both SKILL.md and a reference file
- [ ] **URL verification**: spot-check the tool's primary URLs (documentation site, repository, package index) against the original or official project. Do NOT invent repository URLs — verify by searching if unsure. Common error: guessing GitHub URLs when the project is on GitLab, Bitbucket, or a custom domain
- [ ] No verbatim copy-paste from sources (synthesize and attribute)
- [ ] No promotional or advertising content (strip from ALL entries, not just migrations)
- [ ] `registry.yaml` updated with new entry
- [ ] Cross-cutting tools: secondary categories noted in description field
- [ ] **Capability completeness** (migrations): every capability in the original is covered or intentionally omitted with reason
- [ ] **Pitfall migration** (migrations): every original "Common Pitfalls" item routed to Best Practices (anti-pattern), Troubleshooting (tech error), or Key Concepts (limitation)
- [ ] **Narrative use-case disposition** (migrations): if original had "Common Use Cases", "Applications", or similar narrative sections, per-use-case disposition documented (each use case mapped to When to Use, Common Workflows, Recipes, or omitted with reason — see rule 7b)
- [ ] **Stub detection** (migrations): if original delegates to `references/`, consolidated essential content into inline Core API/Workflow

**Toolkit-specific additional checks:**
- [ ] Key Concepts section present if tool has non-obvious data model (DictList, sparse matrices, sign conventions, etc.)
- [ ] Cross-cutting lookup tables (data types, mode options, chunk size guides) placed in Key Concepts, not embedded in Core API
- [ ] Text-only workflows are used only for simple combinations, not complex operations

**ML model skills — additional checks:**
- [ ] Prerequisites documents GPU/VRAM requirements and cloud API alternative
- [ ] Key Concepts includes model selection guide (table comparing variants)
- [ ] Core API organized by capability (generation, embedding, prediction), not architecture

**Platform integration skills — additional checks:**
- [ ] Prerequisites documents all authentication methods the platform supports (not just API key + OAuth)
- [ ] Core API organized by capability domain (CRUD within each domain; non-CRUD domains like events, analytics have own modules)
- [ ] Error handling patterns for auth failures, rate limits, pagination included (with typed exceptions if SDK provides them)
- [ ] Non-CRUD capabilities (event streaming, data warehouse, webhooks) covered if platform supports them

**Visualization toolkit skills — additional checks:**
- [ ] Core API includes a "Styling & Theming" module covering palettes, themes, and global config
- [ ] Core API organized by plot category, not abstraction level
- [ ] Key Concepts documents dual-interface patterns (if any) as comparison table
- [ ] Modern/declarative API mentioned if available (separate module or Key Concepts subsection)

**Database skills with scale-dependent queries — additional checks:**
- [ ] Key Concepts includes "Query Strategy" decision table (condition → approach → module)
- [ ] At least one Common Workflow shows the size-estimation → strategy-selection → query execution sequence

**Document generation Guide Skills — additional checks:**
- [ ] Companion Assets section present with LaTeX/PPTX templates in `assets/` subdirectory
- [ ] Non-template assets (checklists, reference cards) migrated from original `assets/` if applicable
- [ ] Mandatory requirements prefixed with **"MANDATORY:"** in Best Practices (use for requirements where violation guarantees failure; regular items for quality degradation)
- [ ] Workflow names specific visual elements to generate (figure types, table types)
- [ ] Related Skills lists operational dependencies (plotting tools, template engines), not just informational references
- [ ] Adjacent domain content summarized briefly in Workflow (not fully covered)

**Guide skill migration from rich originals — additional checks:**
- [ ] If original exceeded 500 total lines: `references/` created for deep-dive content
- [ ] Content triage: Key Concepts (what/why), Best Practices (always do), Workflow (how), `references/` (deep dive)
- [ ] All original capabilities have a home in SKILL.md or `references/`
- [ ] Each original reference file explicitly dispositioned: migrated, consolidated into SKILL.md body, or omitted with documented reason
- [ ] Intentional omissions documented (in Bundled Resources section or comment)
- [ ] Guide-format assets routed to `references/` (not `assets/`); only directly-usable files (templates, configs) in `assets/`

**Model zoo skills — additional checks:**
- [ ] Model Selection Guide table leads with Data Modality column, then Model, Key Feature, Use When
- [ ] Key Concepts documents the unified API pattern (e.g., setup→train→extract) prominently
- [ ] Top 2-3 models have full Core API sections with code
- [ ] Remaining models appear in Model Selection Guide table (coverage acknowledged even without inline code)
- [ ] For 4+ model categories: `references/` files organized by category

**Hardware/protocol tool skills — additional checks:**
- [ ] Key Concepts documents protocol file structure (metadata, entry point, runtime constraints)
- [ ] Common Workflows are complete, standalone protocol files (not fragmented snippets)
- [ ] Hardware differences table present (robot types, deck slots, module compatibility)
- [ ] Prerequisites specifies simulation command for code verification

**Data infrastructure tool skills — additional checks:**
- [ ] Core API organized by data lifecycle stage (ingest, annotate, validate, query, track lineage)
- [ ] Integrations treated as core capability (Core API module or dedicated Workflow), not afterthought
- [ ] Setup/deployment patterns documented (beyond minimal Prerequisites) for self-hosted tools
- [ ] If 5+ external integrations: `references/integrations.md` or dedicated Core API module present

**Migration quality — additional checks:**
- [ ] Intentional omissions documented (for tools with capabilities exceeding main file capacity), including omitted reference files
- [ ] Stub consolidation covers 80% of common user tasks (advanced patterns in references/ if needed)
- [ ] Original `references/` files read and included in capability enumeration (not just main SKILL.md)
- [ ] Per-reference-file disposition documented for all originals with 3+ reference files (applies to all sub-types)
- [ ] Troubleshooting consistency: every problem/solution in Troubleshooting table references a feature actually documented in the entry (no orphaned references to undocumented modules)
- [ ] Silent omission final check completed: capability list diffed against entry content, all gaps either covered or documented
- [ ] **Bundled Resources post-verification**: MANDATORY STEP — do this AFTER all reference files are complete, not before. Re-read each `references/` file and rewrite the corresponding Bundled Resources description to match actual content. Common error: claiming content was "omitted" when it was actually included, or vice versa. **Mechanical verification process**: (1) For each "relocated to [Section]" claim in Bundled Resources, use grep to search the target section in the new SKILL.md and confirm the capability is actually present. (2) For each "omitted" topic, verify it's not mentioned anywhere in the entry. (3) Verify line-count math: claimed retained lines + omitted lines should sum to original file size. False relocation claims (e.g., "relocated to Module 4" when Module 4 doesn't cover the topic) are the most common Bundled Resources error — this verification catches them. **Do not skip this step.** If Bundled Resources descriptions don't match actual content, the entry is incomplete.
- [ ] Reference file count: for medium-sized originals (1,000-3,000 total lines), verify `references/` has at least `ceil(original_references / 2)` files. **"original_references"** counts only files in the original's `references/` directory — `scripts/` and `assets/` files are handled separately (scripts → inline code, assets → `assets/`). Do NOT go self-contained if this would drop below 80% capability coverage. **Reference count ≠ retention sufficiency**: meeting the ceil minimum with very short reference files does NOT satisfy the 45% aggregate target. After confirming reference file count, verify: `(main lines + sum of reference lines) / original total ≥ 0.45`. If the ceil minimum produces insufficient aggregate, add more reference files or expand existing ones until the 45% floor is met
- [ ] Pre-write capability budget: if original has 50+ distinct capabilities (across main + all references), confirm `references/` files were planned before writing
- [ ] **Condensation notes are MANDATORY on every migrated reference file**. At the end of each `references/` file, add: "Condensed from original: [X] lines. Retained: [list topics]. Omitted: [list topics] — reason." Format it as a visible section (not a hidden comment). **For multi-source files consolidating 2+ originals**: list omissions separately per source (e.g., "Omitted from api_reference.md: experimental endpoints. Omitted from workflows.md: deprecated patterns"). **Relocation exception**: if content was relocated to main SKILL.md (not dropped), include combined coverage calculation in the condensation note: "Combined coverage: [retained lines] + [~relocated lines in SKILL.md] = [X]% of [Y] original lines." Combined coverage must be ≥ 40% to justify standalone retention below 40%. **Combined coverage is NOT optional** — every multi-source reference file that claims relocation must include the calculation with actual line numbers. Absence of this calculation is a checklist failure. **Multi-file consolidation**: when consolidating 2+ original files into 1 reference file, standalone retention floors: 2 originals → 35% floor, 3+ originals → 30% floor (combined coverage must ≥ 40% in both cases). **Content overlap**: if original files share overlapping content (e.g., database descriptions repeated in both API reference and workflows), deduct overlapping lines from denominator and document: "~80 lines of overlapping database descriptions deducted from 1,116-line denominator." **Catalog omissions**: for catalog files (format catalogs, endpoint catalogs, distribution lists), document omissions at category level (e.g., "Omitted: 5 rarely-used continuous distributions") not per-item.
- [ ] Self-contained consolidation check (when going self-contained): verify retention of: (a) data format schemas users need for parsing, (b) error handling/HTTP status code tables, (c) response field documentation for non-obvious APIs. These are frequently dropped during consolidation but are consulted by users mid-debugging
- [ ] **Aggregate retention sanity check — FINAL GATE**: new entry total (main SKILL.md + all references) should retain **45-65%** of original total lines (main + all references). **Below 45% = entry is incomplete and must be revised before commit.** Values within 1% of boundary (44-45%) are acceptable ONLY if: (a) capability coverage check confirms 80%+ of original capabilities are present, AND (b) all omissions are documented in Bundled Resources and condensation notes. Above 65% suggests insufficient condensation. **Self-contained consolidation exception**: when going self-contained and absorbing all reference files inline, retention up to 75% is acceptable IF: (a) the original total is under 1,000 lines, (b) reference files represent >60% of original total content, and (c) no content is fabricated to fill space. This is structurally inevitable when a large reference file is consolidated inline alongside a thin original main file. **Code-to-Guide reclassification exception**: when substantial agent-behavior content is stripped (>15% of original), the 45% floor may be relaxed to 40% provided capability coverage exceeds 80% and all stripping decisions are documented — agent-behavior content is structural overhead of the original format, not domain capability. **Denominator definition**: "original total lines" = main SKILL.md + all `references/` files. Exclude `scripts/` and `assets/`. **Optional scripts inclusion**: when scripts/ are substantially migrated inline (not just omitted), you may optionally include script lines for accuracy, though not required. **Script compression expectation**: scripts migrated inline compress to 10-25% of original (more aggressive than reference 40-60%) because boilerplate/docstrings/imports are stripped. **If aggregate falls below 45%**, see "Emergency Recovery" section below before finalizing.

---

## Transformation Migrations (Prose-to-Code)

When the original is a **prose-heavy documentation page with zero or near-zero runnable code** (e.g., HMDB's 465 lines of XML field descriptions with no Python code), the standard 45-65% retention framework does not apply — the migration is a structural transformation, not a compression exercise.

**Detection**: If the original main SKILL.md has **fewer than 3 runnable code blocks** AND is predominantly descriptive prose (field catalogs, data dictionaries, web interface descriptions), treat as a transformation migration.

**Evaluation criteria** (substitute for retention percentage):
1. **Capability coverage**: every original capability (data fields, query patterns, use cases) has a home in the new entry
2. **Template compliance**: all required sections present with correct structure
3. **Code quality**: new code blocks are runnable and demonstrate actual API usage for each capability
4. The new entry MAY be larger than the original — this is expected when transforming prose into executable code patterns

**Line budgets for transformation migrations**: Use the standard sub-type line limits (400 for Pipeline, 500 for Toolkit, 550 for Database with 6+ modules) as the upper bound. Do NOT use the original's line count as a constraint — a 200-line prose original can legitimately become a 500-line code-heavy skill.

---

## Emergency Recovery: Aggregate Retention Below 45%

If you complete an entry and calculate aggregate retention below 45%, the entry is under-condensed and likely has silent capability loss. **Do NOT commit.** Instead:

1. **Verify condensation notes exist** on all reference files. Missing notes indicate incomplete migrations.
2. **List all omitted capabilities** by category (e.g., "survival analysis tests", "effect size measures"). Use condensation notes + Bundled Resources to enumerate what was dropped.
3. **For each capability category with >10% omitted**: create or expand a `references/` file to restore inline coverage. Aim for 80% coverage per category minimum.
4. **Recalculate aggregate retention** after adding/expanding reference files. If still below 45%:
   - **Check for real capability loss**: Are entire capability categories missing? (e.g., all count models, all reliability measures) That's capability loss — not acceptable.
   - **Check for over-consolidation**: Did you try to cram 2,000 lines of originals into 400-line main SKILL.md? Split more content to `references/`.
   - **Verify per-reference retention**: If individual reference files show 25% retention or lower, they are severely compressed — restore content or document the consolidation justification in Bundled Resources.
5. **Final gate**: Only finalize the entry if aggregate ≥ 45% AND all omissions are documented AND no capability categories are entirely missing. Entries below 45% require explicit review and justification before merge.

**Prevention**: Use the "Pre-Write Retention Budget Check" (Section 3) to plan before writing. Most entries below 45% indicate insufficient reference file planning or failed scope boundaries.

**Mandatory pre-commit gate**: Before committing ANY migrated entry, compute and report: `(wc -l SKILL.md + wc -l references/*.md) / original_total_lines`. If < 0.45, do not commit. Apply emergency recovery steps above. This check takes 10 seconds and prevents the most common migration failure mode.

---

## Migrating from claude-scientific-skills

When creating a skills_and_knowhow entry for a topic that already exists in `claude-scientific-skills/`:

1. **Read the original** as reference material (Step 3), but author a fresh entry following the template — do NOT copy-paste the original's structure
2. **Re-classify**: The original may be code-centric but could be better suited as a prose-centric guide (e.g., `scientific-writing` is knowledge-centric despite being a SKILL.md). Always re-evaluate with Step 1 criteria
3. **Bundled resources and assets**:
   - If the original has `references/` files (e.g., `api_reference.md`), create new ones adapted to the template format, or omit them if the SKILL.md is self-contained enough
   - If the original has `assets/` (templates, style files): for **Guide** entries, always create a `Companion Assets` section and migrate relevant templates to `assets/`. For code-centric entries, evaluate whether to include as `references/` or omit
   - If the original has `scripts/` (helper Python code): for code-centric entries, incorporate key script functionality into Core API or Common Recipes code blocks. **Exception**: if `scripts/` contains **standalone template files or script generators** (e.g., Opentrons protocols users copy whole-file, workflow generators that produce bash pipelines, analysis pipeline templates), preserve the resulting complete scripts as full code blocks in Common Recipes or Common Workflows — do NOT disassemble into module-level snippets. **Script delegation to Related Skills**: script functionality may be delegated to Related Skills (rather than inlined) if: (a) the script primarily wraps a different library's API (e.g., a matplotlib visualization script, a networkx graph layout script) rather than the migrated tool's own API, AND (b) the Related Skills entry covers equivalent functionality. Note the delegation in Bundled Resources. **Thin-wrapper script shortcut**: if a script file consists entirely of thin wrappers around the SDK (each function ≤5 lines, no business logic beyond calling the API and formatting output), a summary disposition is sufficient — list which Core API modules absorbed each function without enumerating every parameter. Save detailed per-function disposition for scripts with non-trivial logic (data transformation, multi-step pipelines, custom algorithms). **Conceptual/educational script functions**: functions that are primarily conceptual guides with pseudocode or educational commentary (e.g., `cross_validation_comparison()` explaining k-fold CV strategy) should be routed to `references/` as explanatory content or to Key Concepts as guidance — they are not thin wrappers but also not executable code patterns. Document their disposition as "conceptual guide → references/X.md" or "guide content → Key Concepts". **Per-script disposition**: for originals with `scripts/` containing reusable classes or utilities, enumerate the key classes/functions from each script and document their disposition in the Bundled Resources section (e.g., "benchmark_model.py: GCN/GAT/SAGE training patterns → Core API + Common Workflows; MultiResourceMonitor class → omitted, simplified version in references/"). This parallels the per-reference-file disposition rule. For **Guide** entries, list the script purposes in the `Workflow` section (e.g., "Step 6: Generate figures — create Kaplan-Meier curves, forest plots, waterfall plots using matplotlib/plotly") and point to Related Skills for implementation details. Do not create a standalone `scripts/` directory in Guide entries
3b. **Non-markdown reference files** (YAML configs, JSON schemas, INI templates, CSV templates): Consolidate inline into Key Concepts or Prerequisites if under ~100 useful lines; preserve as `references/` files with their original extension if they serve as copy-paste templates that users need whole-file. Document the disposition in Bundled Resources the same way as markdown reference files
4. **Strip promotional content and agent meta-instructions**: Remove any advertising, platform promotion, or vendor-specific sections (e.g., "Suggest Using X Platform", "Try X For Complex Workflows"). No need to document promotional section removal in Bundled Resources — these are not capabilities. Also strip **agent-behavior sections** — sections titled "Handling User Requests", "Example Interactions", "Response Approach", or "Key Reminders" that instruct the reading AI on conversation behavior rather than documenting the tool. **Interspersed agent-behavior content**: agent-behavior instructions are often woven throughout otherwise-useful sections rather than isolated under obvious titles (e.g., "Engage as an equal thought partner" in a Core Principles section, "close with encouragement" in a Workflow phase, interaction style directives, "the user should be doing X% of the talking" meta-instructions). In such cases, extract the domain knowledge and strip the conversational instructions rather than removing the entire section. Skills should contain tool knowledge, not agent prompting. This applies to ALL entries, not just migrations. **Reclassification signal**: entries whose primary content is agent conversation instructions with domain knowledge embedded should be reclassified as Guide (prose-centric) — strip the agent-behavior instructions and preserve the domain knowledge
5. **Capability completeness check**: Before writing, list every distinct capability/function in the original. **Capability granularity**: algorithm variants targeting the same output type (e.g., `all_pairs_shortest_paths` vs `single_source_shortest_paths`, `kruskal` vs `prim` for MST) count as **one capability** with a note about available variants. Truly independent functional patterns (different input/output types, different problem domains) count as separate capabilities. For tools with 100+ API functions, aim for 50-80 capability groups rather than per-function enumeration. **When the original has `references/` files, read ALL reference files and include them in the capability enumeration** — they often contain capabilities not mentioned in the main SKILL.md. Capabilities in `references/` are first-class capabilities of the tool, not optional or secondary. After writing, verify each has a home in the new entry (Core API module, Workflow, Recipe, or Key Concepts). If a capability was intentionally omitted, note why. Common silent omissions: gapfilling, geometric variants, advanced query types, visualization helpers, event/webhook integrations, non-CRUD capabilities (data warehouse, analytics), data type catalogs, error handling patterns, version compatibility notes, **downstream tool integration examples** (e.g., parsing output into BioPython records, building NetworkX graphs from interaction data, loading results into Pandas DataFrames). Integration examples are capabilities if the original demonstrates a non-trivial pattern — include them in Ecosystem Integration or Related Skills, or document their omission.
   **Pre-write capability budgeting**: Before writing, count the total distinct capabilities from the original (including all reference files). If the count exceeds **50 capabilities**, you almost certainly need `references/` files — plan them before writing. For medium-sized originals (1,000-3,000 lines), use this heuristic: 5 Core API modules × ~8 capabilities inline each = ~40 capabilities inline max. Capabilities beyond that need `references/` or documented omission

### Rule 5b. Per-Reference-File Disposition (all migrations with 3+ reference files)

**CRITICAL: This rule applies to ALL migrations** (code-centric and prose-centric). When the original has 3+ reference files, you MUST explicitly decide the fate of each file. This is NOT optional.

**For each original reference file**, decide:
- **(a) Migrate** — Create a new `references/` file with condensation note
- **(b) Consolidate** — Absorb content into the main SKILL.md (specify target sections: Core API Module X, Best Practices, Key Concepts, Workflow Step N, etc.)
- **(c) Omit** — Drop entirely (document reason in Bundled Resources)

**Documentation requirements**:
- When documenting disposition, name the specific target section (e.g., "best_practices.md → consolidated into Best Practices section") rather than vague statements like "consolidated into body"
- **Partial consolidation**: when an original reference file is partially migrated (some content consolidated inline, some omitted), document BOTH portions — disposition (b) for the consolidated portions with target sections, and disposition (c) for the omitted portions with reasons
- **Fully-consolidated files** (content absorbed into main SKILL.md with NO corresponding reference file): document in Bundled Resources with full detail as if it were a condensation note (what was retained and where, what was omitted, line counts). Example: "file_io.md (349 lines) → fully consolidated: Core API Module 1 (~45 lines) + Key Concepts format table (~20 lines). Combined coverage: ~65/349 = 19% standalone, but all critical patterns represented. Omitted: streaming consumer pattern — rarely used in standard workflows"
- **All decisions go in Bundled Resources** before finalizing the entry

**Why this matters**: Missing per-reference-file disposition is the #1 indicator of silent capability loss. If you cannot explain where every original reference file went, you have likely dropped capabilities without documenting them.

**Silent omission final check**: After writing the new entry, diff the capability list against the entry content. Every capability must be either: (a) present in the entry, or (b) documented as intentionally omitted with reason. Flag any capability with no documented home — this is the most common migration quality issue.
6. **Improve on weaknesses**: Common issues in claude-scientific-skills entries include:
   - Missing Key Parameters tables
   - Free-form Troubleshooting (not in table format)
   - Absent Expected Outputs sections
   - No Best Practices section for Toolkits
   - "When to Use" written from keyword-matching perspective instead of user task perspective
   - Missing rate limit guidance for database/API skills
7. **Keep the strengths**: If the original has deeper content (e.g., more input format examples, richer design formula explanations, good Best Practices), incorporate that depth into the appropriate template section
7a. **API modernization**: When the original uses outdated API patterns (deprecated endpoints, old response formats, removed parameters), update to current API conventions during migration. Note the modernization briefly in Bundled Resources (e.g., "API examples updated to UniProt REST API v2 response format"). Do not preserve deprecated patterns for backward compatibility — the entry should reflect current best practice. **Version annotation**: when modernizing API patterns based on inference rather than verified documentation (e.g., changing score access from tuple indexing to dict-style access), annotate the assumed version in a code comment or Bundled Resources note (e.g., "Updated to matchms >= 0.18 API — verify against installed version"). This prevents silent breakage for users on older versions
7b. **Narrative use-case sections**: Original sections like "Common Use Cases", "Applications", or "Example Scenarios" that list domain-specific use cases should be consolidated into "When to Use" bullets (for actionable triggers) and "Common Workflows" descriptions (for end-to-end examples). Do not silently drop narrative use-case content — it maps to template sections even though its format differs. **Per-use-case disposition**: when consolidating, enumerate each use case and state its destination (e.g., "Find Kinase Inhibitors → Workflow 1, Virtual Screening → Recipe, Drug Repurposing → omitted: trivial loop pattern"). Do not use blanket statements like "consolidated into Workflows"
8. **Handle long originals**: If the original exceeds ~400 lines, split into: main SKILL.md (core content) + `references/` (detailed API, extended examples) + `assets/` (templates, style files). Target: main file ≤ 400 lines. **Exception**: for Non-Python tools or general-purpose toolkits that consolidated large reference sets, up to 500 lines is acceptable if every section is essential. **Database skill exception**: Database skills with **6+ Core API modules** (one per query type) may extend to **550 lines** before requiring aggressive splitting to references — the per-query-type module structure inherently requires more space. **Small-to-medium originals (400–1,000 total lines)**: target self-contained SKILL.md of 350–500 lines. Create `references/` only if the original has content domains that don't fit inline (50+ additional API functions, detailed schemas, or extended parameter catalogs). When the original has only 1 reference file, `ceil(1/2)` = 1, but going self-contained is acceptable if the entry stays under 500 lines AND all original reference content is demonstrably consolidated inline (documented in Bundled Resources). **Database exception**: for database skills with 6+ Core API modules, the self-contained upper limit is 550 lines (matching the database exception), not 500. **Medium-sized originals (1,000–3,000 total lines)**: target main SKILL.md of 400–500 lines. Create `references/` for capability domains that didn't fit, targeting `ceil(original_references / 2)` new reference files minimum. **Topical consolidation exception for non-stubs**: same as the stub exception — the ceil minimum may be reduced by **1** if: (a) each resulting file covers a coherent thematic domain (e.g., merging layers + transforms into one file because both describe nn module operations), (b) the topical grouping is documented in Bundled Resources, and (c) total capability coverage exceeds 80%. Do not attempt to go self-contained if the result drops below 80% capability coverage — add `references/` instead. **Stub consolidation exception**: when migrating a stub (original main file <25% of total), the new main SKILL.md may extend to **550 lines** even if the original total is below 3,000 lines — stub consolidation necessarily absorbs more inline content than non-stub migrations because the original had most content in references. **Large toolkit exception**: for general-purpose toolkits with **3,000+ total original lines** (main + all references), up to **650 lines** is acceptable — but create additional `references/` for secondary capability domains rather than silently dropping capabilities to stay under 500. Beyond 650, aggressively split into `references/` for the least-frequently-accessed modules. **Code example diversity during full consolidation**: when a large examples/tutorial file (500+ lines) is fully consolidated inline rather than preserved as a separate reference, preserve at least **one runnable code example per distinct model family or technique category** (e.g., one per pretrained model type, one per ML integration pattern, one per visualization method). Full consolidation inherently compresses prose and setup boilerplate effectively, but risks silently dropping advanced code patterns that differ structurally from the basic examples. To prevent this: after consolidation, list the distinct code pattern families from the original examples file and verify each has at least one representative code block in the new entry (Core API, Workflows, or Recipes)
9. **Migrate "Common Pitfalls" from originals**: Classify each original pitfall and route to the correct section:
   - *Conceptual anti-patterns* (methodological mistakes, wrong model choice) → **Best Practices** with "Anti-pattern —" prefix
   - *Technical errors* (error messages, crashes, wrong output) → **Troubleshooting** table with cause + solution
   - *API limitations* (feature not available, threading issues) → **Key Concepts** subsection or **Prerequisites** note
   - Every original pitfall should have a home in the new entry — do not silently drop them
10. **Detect stub originals**: If the original delegates >50% of content to `references/` files (e.g., Core Capabilities sections that only list operations + "See references/X.md"), the original is a **stub**. **Quantitative heuristic**: count the runnable code blocks in the original's main file (excluding references). If the main file has **fewer than 5 code blocks** despite the tool having 50+ capabilities across references, it is almost certainly a stub. Alternatively, if `main_file_lines / total_lines < 0.25` (main file is less than 25% of total content), treat as stub. **Preview code blocks**: code blocks that merely preview a capability with 1-3 lines and redirect to a reference file (e.g., `# See references/X.md for details`) do NOT count toward the code block heuristic — they are teasers, not self-contained examples. Only count code blocks that are independently useful. **Heuristic conflict tiebreaker**: when the two heuristics disagree (e.g., 8 code blocks but line ratio < 0.25), examine whether the main file's code blocks cover **3+ distinct capability domains** (e.g., data loading, model building, evaluation are 3 domains; but 8 code blocks all in "Quick Patterns" is 1 domain). If < 3 domains, treat as stub. **"Lines of real code" definition**: when the guide references "lines of real code" (e.g., the <200 line threshold for stub classification), count **lines inside code fences** in the main file only — prose, headers, and tables do not count. During migration: consolidate the most essential API coverage directly into Core API with inline code blocks — typically 2-3 modules for single-domain tools, or **up to 8 for general-purpose tools** where each reference file represents a distinct capability domain (test: if omitting a reference file would leave a major user task completely uncovered, it needs inline coverage). Only create `references/` for content that genuinely exceeds the main file's capacity (50+ functions, format specs). Do not blindly replicate the stub pattern. **Scale exception**: if the stub has **4+ model/feature categories** each with substantial content (model zoo pattern), retain category-level `references/` files for non-primary categories while documenting the top 2-3 models fully in Core API. **Consolidation depth check**: after consolidation, verify the inline Core API covers the **most common 80% of user tasks**. To verify 80% coverage concretely: list every original Core API module or major section heading. Each module with at least one code block in the new entry counts as "covered." If fewer than 80% of original modules are represented (either inline or in `references/`), add coverage or document omissions with reasons. If advanced patterns (complex query composition, streaming strategies, deployment configurations) serve the remaining 20%, create `references/` for those.
    **Stub capability triage** (for stubs with 4+ reference files): Before writing, create a capability inventory by enumerating every distinct capability from each reference file. Classify each as: (a) **must inline** — used in >50% of real-world scripts for this tool type (e.g., select, filter, group_by, joins, concat, unique/dedup, rename for DataFrame tools), (b) **reference file** — important but less frequent, or (c) **omit with reason**. Create at minimum `ceil(original_references / 3)` new reference files for non-primary capability domains (counting only `references/` directory files — see Quality Checklist for denominator definition). This prevents over-aggressive consolidation that drops important capabilities to meet line limits. **Must-inline overflow**: if must-inline capabilities don't fit within the main SKILL.md line limit even at 550 lines, do NOT silently drop them — instead, (a) move the least-critical non-must-inline modules to `references/` to free space, or (b) extend the main file to 600 lines with a documented justification. Dropping fundamental operations (join, sort, rename for DataFrames; CRUD for databases; read/write for I/O tools) to meet line limits is always wrong — these are the operations users reach for first. **Topical consolidation exception**: when logically grouping N original files into fewer thematic reference files (e.g., merging coordinates.md + time.md + cosmology.md into one "coordinates_time_cosmology.md"), the ceil minimum may be reduced by **1** if: (a) each resulting file covers a coherent thematic domain, (b) the topical grouping is documented in Bundled Resources, and (c) total capability coverage exceeds 80%. This prevents the ceil formula from forcing artificial file splits that break natural topical boundaries. **Rule precedence**: the `ceil(original_references / 3)` minimum applies only to **stubs** (main SKILL.md had <200 lines of real code). For **non-stub originals** (main file had >200 lines with real code), use `ceil(original_references / 2)` from Rule 8 as the binding minimum. When both rules could apply, use the higher number
11. **Document intentional omissions**: When migrating a tool with capabilities that exceed the main file's capacity (e.g., general-purpose tools with 10+ modules), add a brief note at the end of Core API or in a comment listing capabilities intentionally omitted and why (e.g., "Not covered: Geometry, Number Theory, Combinatorics — specialized modules; consult official docs directly"). This prevents future maintainers from thinking capabilities were accidentally missed. **The same rule applies to omitted reference files**: note them at the end of Bundled Resources or as a comment (e.g., "Not migrated: data_visualization_slides.md — content covered by matplotlib-scientific-plotting skill"). **Omission language**: describe omitted capabilities from the **user's task perspective**, not from code-architecture perspective. "Geometric FBA internals" is ambiguous; "Geometric FBA — alternative central-point solver, rarely needed over pFBA" is clear. **Similar function collapsing**: when two functions serve the same analysis pattern with different targets (e.g., `single_gene_deletion` vs `single_reaction_deletion`), showing one with a brief note about the other's existence is acceptable — but the note must be present (e.g., "`single_reaction_deletion` follows the same pattern"). **I/O format completeness**: each supported file format (import/export) counts as a distinct capability. If the original supports N formats and the migration covers N-1, document the omission
12. **Migrating rich originals to Guide**: When an original exceeds ~500 total lines (main + references) and is reclassified as a prose-centric Guide:
    - **Target line count**: SKILL.md main file: **250–400 lines minimum**. Entries below 250 lines almost always indicate insufficient coverage of Key Concepts, Decision Framework, or Best Practices sections. If the original exceeds 2,000 total lines, aim for the upper range (350-400 lines)
    - **Create `references/`**: For detailed reference material that exceeds main file capacity. Typical Guide references: design guides, extended parameter tables, curated resource lists, comparison matrices, domain-specific standards
    - **Content triage**: Key Concepts covers the "what and why" (~30% of original depth). Best Practices covers the "always do this" (top 10–15 rules). Workflow covers the "how" (process steps). `references/` covers the "deep dive" (content users consult mid-task: color palettes, typography tables, layout patterns, detailed comparison charts)
    - **Capability completeness**: Same rule as code-centric entries — enumerate original capabilities, verify each has a home in SKILL.md or `references/`. **Capability granularity for Guides**: treat each distinct statistical test type, effect size measure, reporting template, or decision criterion as a separate capability. Minor variants (e.g., Hedges' g as bias-corrected Cohen's d) can be consolidated with a note, but should not be silently dropped
    - **Per-reference-file disposition**: When the original has 3+ reference files, explicitly decide the fate of each: (a) migrate as a new `references/` file, (b) consolidate into the SKILL.md body if under ~150 lines, or (c) omit with documented reason (e.g., "vendor-specific", "superseded by Related Skills entry"). Do not silently drop reference files
    - **Homogeneous catalog consolidation**: When N original reference files share the same schema (e.g., all are format catalogs with identical fields, or all are test/method catalogs), consolidating into fewer files is appropriate for structure. However, **preserve per-entry depth** even if file count is reduced. A 6-file catalog becoming 1 file is fine structurally; reducing 6-line-per-entry depth to 1-line table cells is not — that loses actionable detail. For catalog consolidation, keep at least 2-3 fields per entry (not just name + description). Apply the `ceil(original_references / 3)` minimum file count rule here too
    - **Reference file trimming guidance**: When migrating reference files, aim for **40–60% retention** (i.e., the new file retains 40–60% of the original's content). Preserve all distinct capability types (test variants, effect size measures, reporting templates, model types) even if code examples are shortened. Do NOT drop entire capability categories (e.g., all survival analysis tests, all agreement/reliability measures) to save space — consolidate with shorter examples instead. If a migrated reference file has >60% content reduction, review for unintended capability loss. **Per-reference budget calculation**: for each reference file, multiply original line count × 0.45 to get the minimum target. Example: 661-line original → target ≥ 297 lines (not 220)
    - **Within-file omission documentation**: When a migrated reference file is significantly shorter than the original (>50% reduction), add a brief note at the end listing major topics removed (e.g., "Condensed from original: omitted survival analysis tests, agreement/reliability measures, count outcome models — consult original or official documentation for these topics"). This complements per-reference-file disposition (which covers entire files) by documenting omissions *within* migrated files
    - **Code in Guide references**: Guide `references/` files may contain code examples when the code is **illustrative** (e.g., showing how to call a power analysis function, demonstrating a PyMC model structure). The code should demonstrate usage patterns, not form a complete executable pipeline. This is consistent with the Guide rule "Code blocks: Optional; illustrative only" — the same principle extends to references
    - **Non-template assets**: Migrate checklists, reference cards, and quality control documents from original `assets/` to new `assets/` alongside templates. These are not code but provide standalone utility. **Guide-format assets** (design guides, protocol guides, how-to documents) should go to `references/` not `assets/` — `assets/` is for files users copy and use directly (templates, config files, checklists)
    - **Vendor-neutral scripts**: If the original has scripts/ with both vendor-dependent and vendor-neutral utilities, the vendor-dependent scripts are stripped (rule 4). Vendor-neutral utility scripts (e.g., PDF converters, validators) should be mentioned in Protocol Guidelines or Workflow with a brief description of their purpose
13. **Strip vendor-specific metadata**: In addition to stripping promotional sections (rule 4), also remove vendor-specific metadata fields from frontmatter (e.g., `metadata.skill-author`, `vendor`, `allowed-tools`). Keep only the standard fields: `name`, `description`, `license`

---

## Progressive Disclosure Integration

All SKILL.md entries (code-centric and prose-centric) follow the same **progressive disclosure** pattern used by `skills_middleware.py`:

1. **Prompt injection**: Only `name` + `description` from frontmatter are injected into the agent's system prompt
2. **On-demand reading**: When the agent decides a skill is relevant, it reads the full file via `read_file`
3. **This keeps prompts lean** while giving agents access to deep domain knowledge

The middleware reads from both `claude-scientific-skills/` and `skills_and_knowhow/` paths as configured in `skills_config.yaml`.
