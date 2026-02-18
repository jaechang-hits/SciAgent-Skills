# Migration Rules

Detailed rules for migrating existing entries. The main CLAUDE.md covers the base migration workflow (rules 1-7b); this file provides extended rules (5b, 8-13), transformation migrations, and emergency recovery.

---

## Rule 5b. Per-Reference-File Disposition (all migrations with 3+ reference files)

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

---

## Rule 8. Handle Long Originals

If the original exceeds ~400 lines, split into: main SKILL.md (core content) + `references/` (detailed API, extended examples) + `assets/` (templates, style files). Target: main file ≤ 400 lines. **Exception**: for Non-Python tools or general-purpose toolkits that consolidated large reference sets, up to 500 lines is acceptable if every section is essential. **Database skill exception**: Database skills with **6+ Core API modules** (one per query type) may extend to **550 lines** before requiring aggressive splitting to references — the per-query-type module structure inherently requires more space. **Small-to-medium originals (400–1,000 total lines)**: target self-contained SKILL.md of 350–500 lines. Create `references/` only if the original has content domains that don't fit inline (50+ additional API functions, detailed schemas, or extended parameter catalogs). When the original has only 1 reference file, `ceil(1/2)` = 1, but going self-contained is acceptable if the entry stays under 500 lines AND all original reference content is demonstrably consolidated inline (documented in Bundled Resources). **Database exception**: for database skills with 6+ Core API modules, the self-contained upper limit is 550 lines (matching the database exception), not 500. **Medium-sized originals (1,000–3,000 total lines)**: target main SKILL.md of 400–500 lines. Create `references/` for capability domains that didn't fit, targeting `ceil(original_references / 2)` new reference files minimum. **Topical consolidation exception for non-stubs**: same as the stub exception — the ceil minimum may be reduced by **1** if: (a) each resulting file covers a coherent thematic domain (e.g., merging layers + transforms into one file because both describe nn module operations), (b) the topical grouping is documented in Bundled Resources, and (c) total capability coverage exceeds 80%. Do not attempt to go self-contained if the result drops below 80% capability coverage — add `references/` instead. **Stub consolidation exception**: when migrating a stub (original main file <25% of total), the new main SKILL.md may extend to **550 lines** even if the original total is below 3,000 lines — stub consolidation necessarily absorbs more inline content than non-stub migrations because the original had most content in references. **Large toolkit exception**: for general-purpose toolkits with **3,000+ total original lines** (main + all references), up to **650 lines** is acceptable — but create additional `references/` for secondary capability domains rather than silently dropping capabilities to stay under 500. Beyond 650, aggressively split into `references/` for the least-frequently-accessed modules. **Code example diversity during full consolidation**: when a large examples/tutorial file (500+ lines) is fully consolidated inline rather than preserved as a separate reference, preserve at least **one runnable code example per distinct model family or technique category** (e.g., one per pretrained model type, one per ML integration pattern, one per visualization method). Full consolidation inherently compresses prose and setup boilerplate effectively, but risks silently dropping advanced code patterns that differ structurally from the basic examples. To prevent this: after consolidation, list the distinct code pattern families from the original examples file and verify each has at least one representative code block in the new entry (Core API, Workflows, or Recipes)

---

## Rule 9. Migrate "Common Pitfalls" from Originals

Classify each original pitfall and route to the correct section:
- *Conceptual anti-patterns* (methodological mistakes, wrong model choice) → **Best Practices** with "Anti-pattern —" prefix
- *Technical errors* (error messages, crashes, wrong output) → **Troubleshooting** table with cause + solution
- *API limitations* (feature not available, threading issues) → **Key Concepts** subsection or **Prerequisites** note
- Every original pitfall should have a home in the new entry — do not silently drop them

---

## Rule 10. Detect Stub Originals

If the original delegates >50% of content to `references/` files (e.g., Core Capabilities sections that only list operations + "See references/X.md"), the original is a **stub**. **Quantitative heuristic**: count the runnable code blocks in the original's main file (excluding references). If the main file has **fewer than 5 code blocks** despite the tool having 50+ capabilities across references, it is almost certainly a stub. Alternatively, if `main_file_lines / total_lines < 0.25` (main file is less than 25% of total content), treat as stub. **Preview code blocks**: code blocks that merely preview a capability with 1-3 lines and redirect to a reference file (e.g., `# See references/X.md for details`) do NOT count toward the code block heuristic — they are teasers, not self-contained examples. Only count code blocks that are independently useful. **Heuristic conflict tiebreaker**: when the two heuristics disagree (e.g., 8 code blocks but line ratio < 0.25), examine whether the main file's code blocks cover **3+ distinct capability domains** (e.g., data loading, model building, evaluation are 3 domains; but 8 code blocks all in "Quick Patterns" is 1 domain). If < 3 domains, treat as stub. **"Lines of real code" definition**: when the guide references "lines of real code" (e.g., the <200 line threshold for stub classification), count **lines inside code fences** in the main file only — prose, headers, and tables do not count. During migration: consolidate the most essential API coverage directly into Core API with inline code blocks — typically 2-3 modules for single-domain tools, or **up to 8 for general-purpose tools** where each reference file represents a distinct capability domain (test: if omitting a reference file would leave a major user task completely uncovered, it needs inline coverage). Only create `references/` for content that genuinely exceeds the main file's capacity (50+ functions, format specs). Do not blindly replicate the stub pattern. **Scale exception**: if the stub has **4+ model/feature categories** each with substantial content (model zoo pattern), retain category-level `references/` files for non-primary categories while documenting the top 2-3 models fully in Core API. **Consolidation depth check**: after consolidation, verify the inline Core API covers the **most common 80% of user tasks**. To verify 80% coverage concretely: list every original Core API module or major section heading. Each module with at least one code block in the new entry counts as "covered." If fewer than 80% of original modules are represented (either inline or in `references/`), add coverage or document omissions with reasons. If advanced patterns (complex query composition, streaming strategies, deployment configurations) serve the remaining 20%, create `references/` for those.

**Stub capability triage** (for stubs with 4+ reference files): Before writing, create a capability inventory by enumerating every distinct capability from each reference file. Classify each as: (a) **must inline** — used in >50% of real-world scripts for this tool type (e.g., select, filter, group_by, joins, concat, unique/dedup, rename for DataFrame tools), (b) **reference file** — important but less frequent, or (c) **omit with reason**. Create at minimum `ceil(original_references / 3)` new reference files for non-primary capability domains (counting only `references/` directory files — see Quality Checklist for denominator definition). This prevents over-aggressive consolidation that drops important capabilities to meet line limits. **Must-inline overflow**: if must-inline capabilities don't fit within the main SKILL.md line limit even at 550 lines, do NOT silently drop them — instead, (a) move the least-critical non-must-inline modules to `references/` to free space, or (b) extend the main file to 600 lines with a documented justification. Dropping fundamental operations (join, sort, rename for DataFrames; CRUD for databases; read/write for I/O tools) to meet line limits is always wrong — these are the operations users reach for first. **Topical consolidation exception**: when logically grouping N original files into fewer thematic reference files (e.g., merging coordinates.md + time.md + cosmology.md into one "coordinates_time_cosmology.md"), the ceil minimum may be reduced by **1** if: (a) each resulting file covers a coherent thematic domain, (b) the topical grouping is documented in Bundled Resources, and (c) total capability coverage exceeds 80%. This prevents the ceil formula from forcing artificial file splits that break natural topical boundaries. **Rule precedence**: the `ceil(original_references / 3)` minimum applies only to **stubs** (main SKILL.md had <200 lines of real code). For **non-stub originals** (main file had >200 lines with real code), use `ceil(original_references / 2)` from Rule 8 as the binding minimum. When both rules could apply, use the higher number

---

## Rule 11. Document Intentional Omissions

When migrating a tool with capabilities that exceed the main file's capacity (e.g., general-purpose tools with 10+ modules), add a brief note at the end of Core API or in a comment listing capabilities intentionally omitted and why (e.g., "Not covered: Geometry, Number Theory, Combinatorics — specialized modules; consult official docs directly"). This prevents future maintainers from thinking capabilities were accidentally missed. **The same rule applies to omitted reference files**: note them at the end of Bundled Resources or as a comment (e.g., "Not migrated: data_visualization_slides.md — content covered by matplotlib-scientific-plotting skill"). **Omission language**: describe omitted capabilities from the **user's task perspective**, not from code-architecture perspective. "Geometric FBA internals" is ambiguous; "Geometric FBA — alternative central-point solver, rarely needed over pFBA" is clear. **Similar function collapsing**: when two functions serve the same analysis pattern with different targets (e.g., `single_gene_deletion` vs `single_reaction_deletion`), showing one with a brief note about the other's existence is acceptable — but the note must be present (e.g., "`single_reaction_deletion` follows the same pattern"). **I/O format completeness**: each supported file format (import/export) counts as a distinct capability. If the original supports N formats and the migration covers N-1, document the omission

---

## Rule 12. Migrating Rich Originals to Guide

When an original exceeds ~500 total lines (main + references) and is reclassified as a prose-centric Guide:
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

---

## Rule 13. Strip Vendor-Specific Metadata

In addition to stripping promotional sections (rule 4), also remove vendor-specific metadata fields from frontmatter (e.g., `metadata.skill-author`, `vendor`, `allowed-tools`). Keep only the standard fields: `name`, `description`, `license`

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
