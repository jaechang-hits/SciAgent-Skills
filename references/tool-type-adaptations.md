# Tool-Type-Specific Adaptations

Detailed sub-type adaptation rules for Step 1b classification. The main CLAUDE.md covers the base Pipeline/Toolkit/Database/Guide classification; this file provides type-specific extensions.

---

## Database Skills

Tools that wrap external databases/APIs (e.g., PubChemPy, gget, bioservices) use the Toolkit template but with these adaptations. **Boundary clarification**: tools that download static dataset files for local use (e.g., TDC, torchvision datasets, Hugging Face datasets) are NOT database skills even though they access remote servers — database skills involve interactive query-response patterns against a live API or structured data file. Dataset-download tools should be classified as Toolkit without database adaptations. **Local XML/file databases** (e.g., HMDB, DrugBank XML) that users query by parsing structured data files ARE database skills — the distinguishing factor is the query-response interaction pattern against structured records, not whether the data source is remote. For local-file databases: rate limits are N/A (note this explicitly in Prerequisites), and `time.sleep()` patterns are unnecessary:
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

---

## Hybrid Cases

Some tools have both a canonical workflow AND independent modules/model types. Use this decision heuristic:
- If the tool has **one workflow with interchangeable model variants** (e.g., PyMC: same 8-step Bayesian cycle for any model type; GATK: same pipeline for any organism) → **Pipeline** with model variants documented in **Common Recipes** as "Recipe: {Model Type}" (e.g., "Recipe: Hierarchical Model", "Recipe: Logistic Regression"). **Recipe completeness**: every model type listed in the Key Concepts Model Variants table must either have a full Recipe with code OR an explicit note redirecting to `references/` or documenting omission. When adding all variant Recipes would exceed the main file line limit, prioritize the **3-4 most common variants** as full Recipes and note remaining variants with "see references/" or "see official docs" — but these redirections must appear in the Model Variants table, not be silently absent
- If the tool has **independent modules that CAN be used in pipelines** but are also useful standalone (e.g., BioPython, scikit-learn) → **Toolkit** with linear use-cases in **Common Workflows**
- Key test: "Does the user always follow the same steps, just plugging in different models/parameters?" → Pipeline. "Does the user pick different modules for entirely different tasks?" → Toolkit

---

## Document Generation Topics

(e.g., latex-posters, clinical-decision-support, scientific-slides, pptx-posters): These produce structured documents (LaTeX/PDF, PPTX) from templates + domain knowledge. Classify as **Guide** (prose-centric) when the core value is *knowing the document structure, formatting rules, and domain standards* (e.g., GRADE grading, CONSORT reporting). Classify as code-centric only if the tool has a standalone Python API for programmatic document generation. For Guide document-generation entries:
- Use the `Companion Assets` section to include LaTeX templates, style files, or example documents in an `assets/` subdirectory
- In the `Workflow` section, name specific figure types and visual elements that should be generated (e.g., "Kaplan-Meier curves with number-at-risk tables")
- In `Best Practices`, prefix mandatory requirements with **"MANDATORY:"** to distinguish from recommended practices (e.g., "**MANDATORY:** Every poster must include at least 2 figures")
- In `Related Skills`, list the tools needed for figure/table generation (matplotlib, plotly, scientific-schematics) as operational dependencies, not just informational references

---

## ML Model / Deep Learning Tools

(e.g., ESM, AlphaFold, transformers): Pretrained model wrappers that require GPU or cloud API. Classify as **Toolkit** with these adaptations:
- In **Prerequisites**, document: (1) GPU/VRAM requirements per model size, (2) cloud API alternative if available, (3) model weight download size
- Add a **Key Concepts** section with a "Model Selection Guide" table comparing model variants (name, size, VRAM, use case)
- In **Core API**, organize by **capability** (generation, embedding, prediction), not by model architecture internals
- If the tool has both local and cloud API modes, show local examples in Core API and cloud API as a separate module or Recipe
- In **Key Parameters**, include inference parameters (temperature, num_steps, batch_size) alongside API parameters
- Note: code verification may be impossible without GPU — annotate expected output shapes/values in comments rather than relying on `print()` statements for correctness

---

## Model Zoo Frameworks

(e.g., scvi-tools, Hugging Face transformers, torchvision): Frameworks with **5+ models** sharing a unified API but targeting different data modalities or tasks. Classify as **Toolkit** with these adaptations:
- In **Core API**, document the 2-3 most important/common models as full sections with code. For remaining models, mention in the Model Selection Guide table only — do NOT try to cover all models inline
- The **Model Selection Guide** table (in Key Concepts) is the primary navigation aid. Structure columns as: **Data Modality** → **Model** → **Key Feature** → **Use When**. Lead with modality (what experiment did you run?), then analysis goal
- In **Key Concepts**, document the **unified API pattern** (e.g., `setup→create→train→extract`) prominently — this is the user's primary mental model for navigating the zoo
- When there are **4+ model categories** (e.g., RNA-seq, ATAC-seq, multimodal, spatial), create `references/` files organized by category (e.g., `models-scrna-seq.md`, `models-spatial.md`). The main SKILL.md covers shared API + top models; references cover the full zoo
- This differs from the "Pipeline-with-variants" pattern (PyMC): Pipeline-with-variants has one workflow with interchangeable components; Model zoos have one API with models targeting fundamentally different data types

---

## Platform Integration Tools

(e.g., benchling-integration, latchbio-integration, omero-integration): SaaS platform connectors requiring API credentials. Classify as **Toolkit** (Database sub-type adaptations) with these additions:
- In **Prerequisites**, document authentication setup — enumerate **all methods the platform supports** (API key, OAuth, SSO/OIDC, etc.), not just the most common ones. Don't assume only API key and OAuth exist
- Organize Core API by **capability domain** (e.g., registry CRUD, inventory management, event streaming, analytics), not by internal SDK structure. CRUD organization applies within each domain, but some domains are not CRUD — event subscriptions, data warehousing, webhooks, and analytics are separate interaction patterns that need their own Core API modules
- Include error handling patterns for authentication failures, rate limits, and pagination. If the SDK provides **typed exception classes** (e.g., `NotFoundError`, `ValidationError`), show granular catch blocks rather than a single generic catch
- Note in description that the skill requires an active platform account
- Platform integrations often have extensive API surfaces. Consider creating `references/` for: (a) REST API endpoint reference (for non-SDK users or debugging), (b) detailed authentication guide (if 3+ auth methods), (c) advanced SDK patterns (custom HTTP clients, multi-tenant config)

---

## Non-Python Tools

(e.g., MATLAB, R packages): Tools where the primary runtime is not Python. Classify as **Toolkit** with these adaptations:
- Show code examples in the tool's native language (MATLAB, R), not Python
- In Prerequisites, note installation requirements for the external runtime
- If Python integration exists (e.g., `matlab.engine`, `rpy2`) AND the tool will be used alongside Python-based agents/tools, promote Python integration to a **full Core API module** (not just a Recipe) with bidirectional examples (calling Python from the tool AND calling the tool from Python). Include data type conversion tables in a Key Concepts subsection
- In the description, note the primary language so agents know what code to generate
- For tools with **multiple runtimes or compatibility layers** (MATLAB/Octave, Python 2/3, R/Bioconductor versions), compatibility differences count as a capability domain. Add a Key Concepts subsection covering the most impactful differences (5-10 items), or a `references/` file if differences exceed 20 items

---

## Visualization Toolkits

(e.g., seaborn, plotly, bokeh, altair): Tools where nearly every module produces a visual output. Classify as **Toolkit** with these adaptations:
- Organize Core API by **plot category** (Distribution, Categorical, Relational, Matrix, etc.), not by abstraction level
- Include a **"Styling & Theming"** module in Core API covering palettes, themes, contexts, and global configuration — this is a cross-cutting concern that applies to all other modules
- In **Key Concepts**, document any dual-interface patterns (e.g., seaborn's axes-level vs figure-level functions, plotly Express vs Graph Objects) as a comparison table
- If the library has a modern declarative API alongside its traditional API (e.g., `seaborn.objects`, Altair), cover the traditional API in Core API and mention the modern API in a Key Concepts subsection or dedicated Core API module

---

## Database Skills with Scale-Dependent Queries

(e.g., CELLxGENE Census, large genomic databases): When the tool requires different query strategies depending on data scale (e.g., in-memory for <100k rows vs streaming for >100k), add:
- A **"Query Strategy"** subsection in Key Concepts with a decision table: condition → recommended approach → Core API module reference
- In Common Workflows, show at least one workflow that includes the size-estimation → strategy-selection → query execution sequence

---

## Hardware/Protocol Tools

(e.g., Opentrons, PyLabRobot, instrument control APIs): Tools where the output is a structured file (protocol, configuration) uploaded to and executed by hardware. Classify as **Toolkit** with these adaptations:
- In **Key Concepts**, document the **protocol file structure** — mandatory elements (metadata, entry points), runtime constraints (restricted imports, execution model), and hardware-specific requirements (deck layouts, labware compatibility)
- In **Common Workflows**, each workflow should be a **complete, standalone protocol file** that users can copy whole-file and adapt. Do NOT fragment protocols into module-level snippets — the value is seeing the full parameterized protocol. End workflows with the deployment step (e.g., "save and simulate with `opentrons_simulate protocol.py`")
- In **Key Concepts** or **Prerequisites**, add a hardware differences table (e.g., OT-2 vs Flex deck slots, pipette models, module support) and physical constraints (slot conflicts, labware-module compatibility)
- The code quality rule "runnable as-is" means **simulatable** for protocol tools — specify the simulation command in Prerequisites
- See also: migration handling of whole-file template scripts in `migration-rules.md`

---

## Data Infrastructure Tools

(e.g., LaminDB, DVC, Kedro, latchbio): Tools whose primary purpose is data management, versioning, lineage tracking, or provenance — not analysis itself. Classify as **Toolkit** with these adaptations:
- Organize Core API by **data lifecycle stage** (ingest/create, annotate/validate, query/filter, track lineage, organize/version) rather than by independent functional modules
- **Integrations are a core capability**, not an afterthought. If the tool integrates with 5+ external systems (workflow managers, MLOps, storage backends), treat integrations as a Core API module or dedicated Common Workflow. Create `references/integrations.md` if >3 integration patterns have substantial code
- **Setup and deployment** is also a core capability for self-hosted infrastructure. Migrate deployment patterns (local dev, cloud production, multi-user) to a Core API module "Setup & Deployment" or `references/setup-deployment.md`. Prerequisites covers only minimal first-time setup
- Key test to distinguish from Platform Integration tools: "Is this self-hosted open-source or a SaaS platform requiring an account?" Data infrastructure = self-hosted; Platform = SaaS

---

## Cross-Cutting Tools

If a tool spans multiple categories (e.g., gget covers genomics, proteomics, and disease data), classify under the **primary use-case category** and note the secondary categories in the description. The agent's skill matching uses the description field, not the directory path.
