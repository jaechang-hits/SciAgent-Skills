# Skills — Workflow Guide

This directory contains life sciences **skills** in two flavors: **code-centric** (pipeline/toolkit/database) and **prose-centric** (guide).
Claude Code uses this guide to author new entries when given a topic.

## Directory Layout

```
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

| Sub-type | Characteristics | Examples |
|----------|----------------|----------|
| **Pipeline** | Input→processing→output linear flow; one analysis process | scanpy, AutoDock Vina, DESeq2, STAR aligner |
| **Toolkit** | Collection of independent functional modules; multiple use-cases | RDKit, matplotlib, pandas, BioPython, scikit-learn |
| **Database** | API wrapper for external database queries; search/retrieve pattern | PubChem, KEGG, ChEMBL, UniProt, Ensembl via gget |

**Decision question**: "Can this tool be explained as **one pipeline** (load→process→output), does it require describing **multiple independent modules**, or is it primarily an **API/database accessor**?"

- One pipeline → **Pipeline** → use `templates/SKILL_TEMPLATE.md`
- Multiple modules → **Toolkit** → use `templates/SKILL_TEMPLATE_TOOLKIT.md`
- API/database queries → **Database** → use `templates/SKILL_TEMPLATE_TOOLKIT.md` with database adaptations
- Prose-centric guide → **Guide** → use `templates/SKILL_TEMPLATE_PROSE.md`

> **Type-specific adaptations** (Database, ML model, Model zoo, Platform integration, Non-Python, Visualization, Hardware/protocol, Data infrastructure, Document generation, Hybrid cases, Cross-cutting tools): see `references/tool-type-adaptations.md`

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

**Cross-domain entries**: When an entry spans all scientific domains, place it in the category that best matches the entry's **primary audience**. Note the cross-domain nature in the description field. If no category fits well, prefer `scientific-computing` as the catch-all.

### Step 3. Gather Reference Material

Choose reference sources based on the entry type:

**For code-centric Skills** (primary — use these first):

| Source | When to use | URL pattern |
|--------|-------------|-------------|
| Official documentation | API reference, parameters, usage patterns | `{tool}.readthedocs.io`, `{tool}.org/docs/` |
| GitHub README / examples | Quick start, installation, version notes | `github.com/{org}/{tool}` |
| PyPI / conda-forge | Dependencies, version compatibility | `pypi.org/project/{tool}` |
| Published paper | Algorithms, citation, validation data | DOI link |
| Existing entry to migrate | Baseline for migration (see Migration section) | Local path |

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

1. **Calculate denominator**: Count original main file + ALL reference files total lines. Exclude `scripts/` and `assets/` directories.
2. **Estimate planned main file**: Decide if main SKILL.md will be 300–400 lines or 400–500 lines.
3. **Calculate aggregate retention**: If planned main ÷ original total < 0.45, you CANNOT go self-contained — you need reference files to reach 45–65% aggregate retention.
4. **Plan reference files BEFORE writing**: If aggregate < 0.45, calculate how many reference files you need. Work backward from the 50% target.
5. **Set per-reference-file line budgets**: Target `S × 0.40` lines (40% retention midpoint). For 2-source files, floor is `S × 0.35`; for 3+ source files, floor is `S × 0.30`. Write to the budget on first pass.

**Why this matters**: Authors often commit to "self-contained" consolidation without doing this math, then finish writing and discover they've dropped 20–30% of capabilities silently.

### Step 4. Author the Entry

Create the entry directory and file:

```
skills/{category}/{entry-name}/SKILL.md
```

**Entry name convention**: lowercase, hyphen-separated. Use `{tool-name}-{purpose}` format for clarity (e.g., `pydeseq2-differential-expression`, `scanpy-scrna-seq`).

Use the appropriate template:
- Code-centric (Pipeline) → `templates/SKILL_TEMPLATE.md`
- Code-centric (Toolkit) → `templates/SKILL_TEMPLATE_TOOLKIT.md`
- Prose-centric (Guide) → `templates/SKILL_TEMPLATE_PROSE.md`

#### SKILL.md Format Rules — Pipeline Sub-type

For tools with a linear input→processing→output flow (e.g., scanpy, AutoDock Vina, DESeq2).

1. **Frontmatter** (YAML between `---`): `name`, `description`, `license` (all required)
   - **`license`**: Use the underlying tool's license if known. Default to `CC-BY-4.0` for original content
2. **Sections** (in order): Overview, When to Use (5+ items, user's task perspective), Prerequisites, Quick Start (optional), Workflow (numbered steps, each with code block, 5-8 steps), Key Parameters (table), Key Concepts (optional), Common Recipes (2-4 snippets), Expected Outputs, Troubleshooting (table, 5+ rows), Bundled Resources (optional), References
3. **Code blocks**: **10+ total** (Prerequisites + Workflow + Recipes). Troubleshooting code excluded from count
4. **Description**: max 1024 characters, focused on "when should I use this?"
5. **Code quality**: all code blocks must be runnable as-is with sample data or clear placeholders. Include `print()` statements showing expected output shape/size

> **Bundled resources, Pipeline-with-variants details**: see `references/format-rules-detail.md`

#### SKILL.md Format Rules — Toolkit Sub-type

For tools that are collections of independent functional modules (e.g., RDKit, matplotlib, pandas, BioPython).

1. **Frontmatter** (YAML between `---`): `name`, `description`, `license` (all required)
2. **Sections** (in order): Overview, When to Use (5+ items, include 1-2 alternative tool comparisons), Prerequisites, Quick Start (recommended for 6+ modules), **Core API** (4-8 modules, each with 1-2 code blocks), **Key Concepts** (optional, for non-obvious data models and cross-cutting lookup tables), **Common Workflows** (2-4 end-to-end pipelines, at least 2 runnable), Key Parameters (table with Module column), **Best Practices** (optional, for large toolkits), Common Recipes (2-4 snippets), Troubleshooting (table, 5+ rows), Bundled Resources (optional), Related Skills (optional), References
3. **Code blocks**: **12 minimum** (4-5 modules) or **15+** (6+ modules). Count only Prerequisites, Core API, Common Workflows, Recipes
4. **Description**: max 1024 characters
5. **Code quality**: runnable as-is with sample data or clear placeholders
6. **Expected Outputs** section is **optional** for Toolkit skills
7. **Bundled resources**: same rules as Pipeline sub-type

> **Reference triage, CLI+Python dual interface, Related Skills, Ecosystem tools details**: see `references/format-rules-detail.md`

#### Guide SKILL.md Format Rules — Prose-centric

For entries where the core value is domain knowledge, decision frameworks, and best practices (sub_type: guide).

1. **Frontmatter** (YAML between `---`): `name`, `description`, `license` (all required)
2. **Sections** (in order): Overview, Key Concepts (3+ subsections), Decision Framework (ASCII tree + decision table), Best Practices (5+ items), Common Pitfalls (5+ items, each with "How to avoid"), Workflow (optional), Protocol Guidelines, Further Reading (3+ items), Related Skills
3. **Description**: max 1024 characters, focused on "when should I read this?"

> **Companion assets, bundled resources, adjacent domain content details**: see `references/format-rules-detail.md`

### Step 5. Update registry.yaml

Add the new entry to `registry.yaml`:

```yaml
entries:
  - name: "entry-name"
    type: skill
    sub_type: pipeline    # "pipeline", "toolkit", "database", or "guide"
    category: "genomics-bioinformatics"
    path: "skills/genomics-bioinformatics/entry-name/SKILL.md"
    description: "Brief description"
    date_added: "YYYY-MM-DD"
```

---

### Step 6. Validate

After creating or modifying an entry, run the test suite:

```bash
pixi run test
```

Tests verify registry integrity, frontmatter fields, required sections by sub-type, and content depth (code block counts, line counts). Fix any failures before finalizing.

For quick registry-only validation:

```bash
pixi run validate
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
- [ ] Standard visualization included as Workflow steps, not Recipes
- [ ] Common Recipes has 2-4 self-contained snippets (alternative approaches, not workflow duplicates)
- [ ] Total code blocks ≥ 10
- [ ] Key Parameters table has 5+ rows with defaults and ranges
- [ ] Troubleshooting table has 5+ rows
- [ ] Quick Start section present (optional but strongly recommended)
- [ ] For Pipeline-with-variants: Key Concepts includes model/variant selection guide; Recipes cover each major variant

**Toolkit Skills — code depth:**
- [ ] Core API has 4-8 module subsections, each with 1-2 code blocks (8-16 total)
- [ ] Common Workflows has 2-4 complete end-to-end examples
- [ ] Common Recipes section has 2-4 self-contained snippets
- [ ] Total code blocks ≥ 12 (4-5 modules) or ≥ 15 (6+ modules)
- [ ] Key Parameters table has 5+ rows with defaults and ranges
- [ ] Troubleshooting table has 5+ rows

**Toolkit Skills — content quality:**
- [ ] "When to Use" includes 1-2 alternative tool comparisons
- [ ] Common Workflows combine multiple Core API modules
- [ ] Key Parameters table has Module/Function column for multi-module tools
- [ ] Best Practices section present for large toolkits
- [ ] Related Skills section present for ecosystem tools
- [ ] Ecosystem Integration shown via code snippets if tool is part of a larger ecosystem

**Guide Skills — content depth:**
- [ ] Key Concepts has 3+ subsections with clear definitions
- [ ] Decision Framework includes both ASCII tree diagram AND decision table
- [ ] Best Practices has 5+ items with rationale
- [ ] Common Pitfalls has 5+ items, each with "How to avoid" sub-item
- [ ] Workflow section present if the guide has a clear sequential process
- [ ] **Main SKILL.md is 250+ lines** (for originals with 2,000+ total lines, target 350-400 lines)

**Content quality (all types):**
- [ ] "When to Use" items written from user's task perspective, not keyword-matching
- [ ] References cite sources with URLs (3+ references)
- [ ] Code blocks are runnable as-is (with sample data or clear placeholders)
- [ ] **Code verification**: spot-check at least 2 code blocks — verify function signatures, argument names, return types against official docs
- [ ] **Cross-file consistency**: code examples in SKILL.md and `references/` use consistent API patterns
- [ ] **URL verification**: spot-check primary URLs against official project. Do NOT invent repository URLs
- [ ] No verbatim copy-paste from sources (synthesize and attribute)
- [ ] No promotional or advertising content
- [ ] `registry.yaml` updated with new entry
- [ ] Cross-cutting tools: secondary categories noted in description field
- [ ] (migrations) Capability completeness, pitfall migration, narrative use-case disposition, stub detection checks completed

> **Type-specific additional checks** (Database, ML model, Platform, Visualization, Hardware, Data infra, Model zoo, Document generation, Guide migration, Migration quality): see `references/quality-checklist-by-type.md`

---

## Migrating from Existing Entries

When creating an entry for a topic that already has an existing version to migrate from:

1. **Read the original** as reference material (Step 3), but author a fresh entry following the template — do NOT copy-paste the original's structure
2. **Re-classify**: The original may be code-centric but could be better suited as a prose-centric guide. Always re-evaluate with Step 1 criteria
3. **Bundled resources and assets**:
   - If the original has `references/` files, create new ones adapted to the template format, or omit them if the SKILL.md is self-contained enough
   - If the original has `assets/` (templates, style files): for **Guide** entries, always create a `Companion Assets` section and migrate relevant templates. For code-centric entries, evaluate whether to include as `references/` or omit
   - If the original has `scripts/` (helper Python code): incorporate key script functionality into Core API or Common Recipes code blocks
3b. **Non-markdown reference files** (YAML configs, JSON schemas, INI templates, CSV templates): Consolidate inline if under ~100 useful lines; preserve as `references/` files if they serve as copy-paste templates
4. **Strip promotional content and agent meta-instructions**: Remove advertising, platform promotion, vendor-specific sections, and agent-behavior sections. Skills should contain tool knowledge, not agent prompting
5. **Capability completeness check**: Before writing, list every distinct capability/function in the original (including all reference files). After writing, verify each has a home in the new entry or is documented as intentionally omitted
6. **Improve on weaknesses**: Common issues include missing Key Parameters tables, free-form Troubleshooting, absent Expected Outputs sections, no Best Practices for Toolkits, "When to Use" written from keyword-matching perspective
7. **Keep the strengths**: If the original has deeper content, incorporate that depth into the appropriate template section
7a. **API modernization**: Update outdated API patterns to current conventions. Note the modernization in Bundled Resources
7b. **Narrative use-case sections**: Consolidate "Common Use Cases" etc. into "When to Use" bullets and "Common Workflows". Per-use-case disposition required

> **Extended migration rules** (Rule 5b per-reference-file disposition, Rules 8-13 for long originals/stubs/Guide migrations/omissions, Transformation Migrations, Emergency Recovery): see `references/migration-rules.md`

---

## Progressive Disclosure Integration

All SKILL.md entries follow the same **progressive disclosure** pattern:

1. **Prompt injection**: Only `name` + `description` from frontmatter are injected into the agent's system prompt
2. **On-demand reading**: When the agent decides a skill is relevant, it reads the full file via `read_file`
3. **This keeps prompts lean** while giving agents access to deep domain knowledge
