# Quality Checklist — Type-Specific Sections

Additional quality checks by skill sub-type. The main CLAUDE.md contains universal checklist items (Frontmatter, Structure, Pipeline code depth, Toolkit code depth, Toolkit content quality, Guide content depth, Content quality). This file covers type-specific additional checks.

---

## Database Skills — additional checks

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

---

## Toolkit-specific additional checks

- [ ] Key Concepts section present if tool has non-obvious data model (DictList, sparse matrices, sign conventions, etc.)
- [ ] Cross-cutting lookup tables (data types, mode options, chunk size guides) placed in Key Concepts, not embedded in Core API
- [ ] Text-only workflows are used only for simple combinations, not complex operations

---

## ML model skills — additional checks

- [ ] Prerequisites documents GPU/VRAM requirements and cloud API alternative
- [ ] Key Concepts includes model selection guide (table comparing variants)
- [ ] Core API organized by capability (generation, embedding, prediction), not architecture

---

## Platform integration skills — additional checks

- [ ] Prerequisites documents all authentication methods the platform supports (not just API key + OAuth)
- [ ] Core API organized by capability domain (CRUD within each domain; non-CRUD domains like events, analytics have own modules)
- [ ] Error handling patterns for auth failures, rate limits, pagination included (with typed exceptions if SDK provides them)
- [ ] Non-CRUD capabilities (event streaming, data warehouse, webhooks) covered if platform supports them

---

## Visualization toolkit skills — additional checks

- [ ] Core API includes a "Styling & Theming" module covering palettes, themes, and global config
- [ ] Core API organized by plot category, not abstraction level
- [ ] Key Concepts documents dual-interface patterns (if any) as comparison table
- [ ] Modern/declarative API mentioned if available (separate module or Key Concepts subsection)

---

## Database skills with scale-dependent queries — additional checks

- [ ] Key Concepts includes "Query Strategy" decision table (condition → approach → module)
- [ ] At least one Common Workflow shows the size-estimation → strategy-selection → query execution sequence

---

## Document generation Guide Skills — additional checks

- [ ] Companion Assets section present with LaTeX/PPTX templates in `assets/` subdirectory
- [ ] Non-template assets (checklists, reference cards) migrated from original `assets/` if applicable
- [ ] Mandatory requirements prefixed with **"MANDATORY:"** in Best Practices (use for requirements where violation guarantees failure; regular items for quality degradation)
- [ ] Workflow names specific visual elements to generate (figure types, table types)
- [ ] Related Skills lists operational dependencies (plotting tools, template engines), not just informational references
- [ ] Adjacent domain content summarized briefly in Workflow (not fully covered)

---

## Guide skill migration from rich originals — additional checks

- [ ] If original exceeded 500 total lines: `references/` created for deep-dive content
- [ ] Content triage: Key Concepts (what/why), Best Practices (always do), Workflow (how), `references/` (deep dive)
- [ ] All original capabilities have a home in SKILL.md or `references/`
- [ ] Each original reference file explicitly dispositioned: migrated, consolidated into SKILL.md body, or omitted with documented reason
- [ ] Intentional omissions documented (in Bundled Resources section or comment)
- [ ] Guide-format assets routed to `references/` (not `assets/`); only directly-usable files (templates, configs) in `assets/`

---

## Model zoo skills — additional checks

- [ ] Model Selection Guide table leads with Data Modality column, then Model, Key Feature, Use When
- [ ] Key Concepts documents the unified API pattern (e.g., setup→train→extract) prominently
- [ ] Top 2-3 models have full Core API sections with code
- [ ] Remaining models appear in Model Selection Guide table (coverage acknowledged even without inline code)
- [ ] For 4+ model categories: `references/` files organized by category

---

## Hardware/protocol tool skills — additional checks

- [ ] Key Concepts documents protocol file structure (metadata, entry point, runtime constraints)
- [ ] Common Workflows are complete, standalone protocol files (not fragmented snippets)
- [ ] Hardware differences table present (robot types, deck slots, module compatibility)
- [ ] Prerequisites specifies simulation command for code verification

---

## Data infrastructure tool skills — additional checks

- [ ] Core API organized by data lifecycle stage (ingest, annotate, validate, query, track lineage)
- [ ] Integrations treated as core capability (Core API module or dedicated Workflow), not afterthought
- [ ] Setup/deployment patterns documented (beyond minimal Prerequisites) for self-hosted tools
- [ ] If 5+ external integrations: `references/integrations.md` or dedicated Core API module present

---

## Migration quality — additional checks

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
- [ ] **Aggregate retention sanity check — FINAL GATE**: new entry total (main SKILL.md + all references) should retain **45-65%** of original total lines (main + all references). **Below 45% = entry is incomplete and must be revised before commit.** Values within 1% of boundary (44-45%) are acceptable ONLY if: (a) capability coverage check confirms 80%+ of original capabilities are present, AND (b) all omissions are documented in Bundled Resources and condensation notes. Above 65% suggests insufficient condensation. **Self-contained consolidation exception**: when going self-contained and absorbing all reference files inline, retention up to 75% is acceptable IF: (a) the original total is under 1,000 lines, (b) reference files represent >60% of original total content, and (c) no content is fabricated to fill space. This is structurally inevitable when a large reference file is consolidated inline alongside a thin original main file. **Code-to-Guide reclassification exception**: when substantial agent-behavior content is stripped (>15% of original), the 45% floor may be relaxed to 40% provided capability coverage exceeds 80% and all stripping decisions are documented — agent-behavior content is structural overhead of the original format, not domain capability. **Denominator definition**: "original total lines" = main SKILL.md + all `references/` files. Exclude `scripts/` and `assets/`. **Optional scripts inclusion**: when scripts/ are substantially migrated inline (not just omitted), you may optionally include script lines for accuracy, though not required. **Script compression expectation**: scripts migrated inline compress to 10-25% of original (more aggressive than reference 40-60%) because boilerplate/docstrings/imports are stripped. **If aggregate falls below 45%**, see "Emergency Recovery" section in `migration-rules.md` before finalizing.
