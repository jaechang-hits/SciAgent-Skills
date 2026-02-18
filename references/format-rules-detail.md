# Format Rules — Detailed Sub-type Rules

Extended rules for each SKILL.md sub-type format. The main CLAUDE.md covers required sections and code block minimums; this file provides detailed guidance on bundled resources, reference triage, dual interfaces, related skills, ecosystem tools, and guide-specific rules.

---

## Pipeline Sub-type — Bundled Resources Detail

(Optional but recommended for complex skills):
- Create a `references/` subdirectory inside the entry folder
- Typical files: `api_reference.md` (function lookup), `plotting_guide.md` (visualization), `standard_workflow.md` (detailed step-by-step with decision points)
- Each reference file provides deeper detail than the SKILL.md itself — agents read them on demand
- List and describe each file in the "Bundled Resources" section of SKILL.md. Each description must include three elements: (1) what the file covers, (2) what original content was relocated inline rather than into the reference (if migrating), and (3) what was intentionally omitted with a one-line reason. This prevents future maintainers from mistaking relocated content for coverage gaps. **Format hint**: for readability, structure longer Bundled Resources descriptions with labeled sub-items or separate sentences per element (e.g., "Covers: ... Relocated inline: ... Omitted: ..."). A single dense paragraph satisfying all three elements often becomes hard to scan

---

## Toolkit Sub-type — Extended Rules

### Code Quality (Rule 5)

All code blocks must be runnable as-is with sample data or clear placeholders. Include `print()` statements showing expected output shape/size. **Simplification guard**: when condensing complex code (e.g., `Lambda(custom_function)` patterns, multi-step pipelines) into simpler examples for the main SKILL.md, ensure the simplified version produces equivalent results. If simplification changes behavior, preserve the correct version in the reference file and note the simplification in the SKILL.md code comment

### Core API vs Common Workflows (Rule 6)

- **Core API**: each subsection covers one functional module (e.g., "Molecular I/O", "Descriptors", "Fingerprints"). Focus on individual functions/classes with short examples
- **Common Workflows**: each is a complete pipeline combining multiple Core API modules for a real use-case (e.g., "Virtual Screening Cascade", "ADMET Profiling"). These are longer, end-to-end examples

### Reference Triage (Rule 9)

(Applies to all Toolkits, not just Database skills): When deciding whether original reference content stays as a `references/` file or gets consolidated inline, prefer consolidating inline when the content is already partially covered by Core API code blocks (e.g., an api_guide that duplicates endpoint parameters shown in Core API). Preserve as external `references/` files content that is purely lookup-oriented (parameter catalogs, field tag tables, query template libraries, 60+ parameter references) where the table format itself is the primary value. **Prefer self-contained SKILL.md** — put essential functions and examples directly in Core API modules. Only split into `references/` when:
- SKILL.md exceeds **~500 lines** even after trimming redundant examples
- The tool has **50+ API functions** worth documenting beyond what Core API covers
- There are **format-specific details** (e.g., file format specs, protocol schemas) that would clutter the main flow
- The tool is a **model zoo with 4+ model categories** — create category-level references (e.g., `models-scrna-seq.md`, `models-spatial.md`) while keeping shared API + top models in SKILL.md
- There are **essential lookup tables** (API version compatibility, hardware compatibility matrices, error code tables) that are too detailed for inline inclusion but too important to omit
- **Do NOT** create `references/` just because the original had them — many originals use stub-like "See: references/X.md" patterns that make the SKILL.md useless without those files. A self-contained SKILL.md with good Core API modules is always better than a stub SKILL.md + detailed references/

### CLI + Python Dual Interface (Rule 10)

If the tool has both CLI and Python interfaces, determine which is the **primary user interface**:
- **Python API is primary** (e.g., gget, pysam): show Python examples in SKILL.md, note CLI equivalents in comments
- **CLI is primary** (e.g., deeptools, samtools, GATK): show bash/CLI examples in SKILL.md. These tools are Python *packages* but their user interface is CLI commands — write code blocks in bash, not Python
- Key test: "Does the user typically write `import tool` or `tool_command --args`?" → Python vs CLI
- Do not duplicate every example in both interfaces — pick the primary one

### Related Skills (Rule 11)

(Optional but recommended for ecosystem tools): After Troubleshooting (or after Bundled Resources if present), add a **Related Skills** section listing connected tools with brief connection descriptions. This is especially important for tools that are part of a larger ecosystem (e.g., anndata → scanpy, scvi-tools; RDKit → datamol, medchem). Format: `- **tool-name** — connection description`. **Non-existent entries**: when referencing a skill that does not yet exist in `registry.yaml`, append `(planned)` to the entry name (e.g., `- **scanpy-scrna-seq** — upstream analysis` vs `- **pathml-spatial-omics (planned)** — multiplexed imaging`). This prevents agents from attempting to read non-existent files

### Ecosystem Tools (Rule 12)

When the tool is part of a well-known ecosystem (scverse, tidyverse, PyTorch ecosystem, etc.), add a brief **"Ecosystem Integration"** subsection inside Common Workflows or as the last Core API module. Show 2-3 code snippets demonstrating how this tool hands off data to other ecosystem members. This prevents users from needing to read multiple skills just to understand the data flow. Keep it brief — full usage of the downstream tool belongs in that tool's own skill

---

## Guide Sub-type — Extended Rules

### Companion Assets (Rule 4)

If the guide has associated templates, style files, or other non-code assets, create an `assets/` subdirectory in the entry folder. List and describe each asset in a "Companion Assets" section after Related Skills. Example: LaTeX templates, configuration files, checklists, quality control checklists

### Bundled Resources (Rule 5)

Guide entries may include a `references/` subdirectory for detailed reference material when the topic has depth exceeding ~400 lines. Describe each file in a "Bundled Resources" section (before Companion Assets). Typical files: detailed design guides, extended parameter tables, curated resource lists, comparison matrices, domain-specific reference cards. Same rules as code-centric skill bundled resources: prefer self-contained SKILL.md, only create `references/` when content genuinely exceeds the main file's capacity

### Adjacent Domain Content (Rule 6)

When the guide naturally extends into adjacent domains (e.g., poster creation → poster presentation, manuscript writing → peer review response), include a brief summary in the Workflow section (1-2 sentences per adjacent topic) and note the adjacent domain in Related Skills. Do not try to cover adjacent domains fully — that's a separate entry
