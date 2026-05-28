---
name: sciagent-skill-creator
description: |
  Scaffold a new SciAgent-Skills entry. Picks pipeline/toolkit/database/guide template,
  creates skills/{category}/{name}/SKILL.md with valid frontmatter, appends the
  registry.yaml entry, runs validation. Enforces name uniqueness, kebab-case,
  description keyword rules, schema rules from CLAUDE.md.

  TRIGGER when user says (any language): "add a SciAgent skill", "add a skill for <X>",
  "create new skill", "create a SKILL.md for <X>", "scaffold a skill", "new skill entry",
  "register a skill", "신규 skill 추가", "스킬 만들어줘", "스킬 생성", "skill 만들어",
  or any request to add a new SKILL.md to this repo. ALWAYS invoke this skill BEFORE
  writing to skills/ or registry.yaml.

  DO NOT TRIGGER when: editing existing entry's content (just edit the file directly);
  migrating an existing entry (read CLAUDE.md "Migrating from Existing Entries" first);
  only updating registry.yaml without creating a new SKILL.md.
---

# SciAgent Skill Creator

Repo-local scaffolder for `skills/` entries. Mechanizes the boilerplate from `CLAUDE.md` Steps 1, 2, 4, 5, 6 so authoring effort stays on *content* (When to Use, Workflow, Recipes, References) and not on field plumbing.

## When to invoke this skill

- User asks for a new SciAgent skill entry on a specific tool, library, database, or guide topic
- User invokes `/sciagent-skill-creator` directly
- The agent is about to hand-edit `registry.yaml` and create a `skills/<cat>/<name>/SKILL.md` from scratch — use this instead

Do **not** invoke for:
- Editing an existing entry's content (just edit the file)
- Migrating an existing entry (read `CLAUDE.md` "Migrating from Existing Entries" first — the scaffolder generates a skeleton, but migration requires content judgment)
- Updating `registry.yaml` only (use a normal edit)

## What you need to collect from the user

Before calling the scaffold script, gather these — in conversation, not via flags hidden from the user:

1. **Topic** — concrete tool/library/concept name. Reject vague topics ("ML stuff") with a clarifying question.
2. **Sub-type** — `pipeline` | `toolkit` | `database` | `guide`. Use the decision rule from CLAUDE.md Step 1b. If unsure, ask the user.
3. **Category** — primary category directory. List the table from `CLAUDE.md` Step 2 if the user is unsure.
4. **Entry name** — kebab-case slug. Convention: `{tool-name}-{purpose}` (e.g., `pydeseq2-differential-expression`). Confirm with the user.
5. **License** — underlying tool's license. Default to `CC-BY-4.0` for original prose-only content.
6. **Description** — 1-2 sentences, max 1024 chars. Lead with tool/domain keyword in the first 120 chars. Anti-patterns are in CLAUDE.md Step 5 "Description writing rules".
7. **Tags** (optional) — only if the entry meaningfully spans multiple categories (e.g., literature DB stored under `scientific-writing`, tag with `["databases", "literature"]`).

## Duplicate check before scaffolding

Before calling the scaffold script, search the registry and `legacy/` for similar names:

```bash
grep -i "<topic-keyword>" registry.yaml
ls legacy/ | grep -i "<topic-keyword>"
```

If a near-duplicate exists, surface it to the user before continuing. Authoring a parallel entry usually means the existing one needs updating, not duplication.

## How to run the scaffolder

Call `scripts/scaffold.py` with explicit arguments. The script is **non-interactive** — the agent provides all values:

```bash
python .claude/skills/sciagent-skill-creator/scripts/scaffold.py \
  --sub-type pipeline \
  --category genomics-bioinformatics \
  --name my-tool-purpose \
  --description "MyTool short-form description starting with the tool name. Brief on inputs, outputs, when to pick this over alternatives." \
  --license MIT \
  --tags databases,literature   # optional, comma-separated
```

Behavior:

1. Validates name (kebab-case, not already in `registry.yaml`, not in `legacy/`)
2. Validates category exists as a directory under `skills/`
3. Validates description with `validate_description.py` (length + first-120-char keyword lead)
4. Validates tags (kebab-case if provided)
5. Creates `skills/{category}/{name}/SKILL.md` from the matching template, substituting frontmatter fields
6. Appends a new entry to `registry.yaml` with `date_added` = today (UTC)
7. Runs `pixi run validate` to confirm the registry is still well-formed
8. Prints next steps (fill in Overview, Workflow, Recipes, References)

On any validation failure, the script aborts without writing anything. Fix the offending value and re-run.

## After scaffolding

The generated SKILL.md is a **skeleton with placeholders**. The agent's remaining job:

1. Fill `Overview`, `When to Use`, `Prerequisites`, `Workflow` / `Core API` / `Key Concepts`, `Common Recipes`, `Troubleshooting`, `References`
2. Match the section structure required by the sub-type (see CLAUDE.md Step 4 format rules)
3. Run `pixi run test` — full suite, not just `validate` — to catch sub-type-specific structural failures (code block counts, table row counts, section presence)

The scaffold script does not pretend to write content. Content stays with the agent and the source material.

## Content authoring rules (what NOT to bake into a SKILL.md)

Skills document a tool's *analysis surface*, not the consumer's *house style*. A SKILL.md is read by many agents for many downstream tasks — visual choices that fit one analysis brief leak into every future invocation. Strip the following before committing:

- **Color palettes, cmaps, themes** — no hex codes (`#08306b`), no `LinearSegmentedColormap.from_list(...)`, no `ListedColormap([...])`, no prescribed `cmap=` arguments unless the cmap *is* the tool's API (e.g., a tool that ships its own palette). Let matplotlib pick defaults; the consumer overrides downstream.
- **Per-replicate / per-condition color dicts** — e.g., `colors = {"rep1": "#1f77b4", ...}`. Matplotlib auto-cycles colors.
- **Font choices, dpi presets, figure sizes tuned for one report** — `figsize=(8, 4)` for a routine line plot is fine; `figsize=(12, 4)` chosen to fit a slide deck is not.
- **One-shot user-brief specifics** — if the user asked for "blue for low, red for high" in *their* analysis, that belongs in their code, not the skill. The skill teaches *how to compute* phi/psi density; *how to color it* is consumer choice.
- **Hardcoded paths beyond the tool's defaults** — `"figures/"`, `"results/"`, `f"{pdb_id}_protein.pdb"` are fine as illustrative outputs; `"/Users/me/proj42/output"` is not.

What to keep: the analysis logic, the data shape, the units, the parameter semantics, the expected output *structure* (columns, axes, units), and any visual choice the tool itself enforces.

Rule of thumb: if a downstream consumer would *override* the choice, don't ship the choice in the skill.

## Writing style: be succinct

A SKILL.md is reference material for agents, not a tutorial. Token cost matters — every line is paid for on every retrieval. Write like documentation, not like a walkthrough:

- **One sentence per section intro, not a paragraph.** Drop hedging ("typically", "in general", "you may want to"), filler ("note that", "it's worth mentioning"), and softeners. State the rule.
- **Comments inside code blocks earn their place.** Only annotate non-obvious lines — units, gotchas, why this parameter. Don't restate what the code already says (`# load the trajectory` above `traj = md.load(...)` is noise).
- **Code over prose when possible.** A four-line code block beats a paragraph describing the same call. The agent runs the code; the prose is for what the code can't show.
- **No preamble before code.** "The following snippet demonstrates how one might..." → delete. The header and code speak for themselves.
- **No closing recap.** Each section ends when the information ends. No "In summary..." or "As shown above...".
- **Cut redundancy across sections.** If Workflow Step 2 already shows the parameter, the Key Parameters table row doesn't need to re-explain it — just list it.
- **Tables for enumerations, not bullets.** Parameters, troubleshooting, codes → table. Prose lists waste vertical space.

Target density: a reader scanning the file should reach the next code block within ~5 lines of prose. If a section's prose is longer than its code, tighten the prose.

## Files in this skill

- `SKILL.md` — this file (when/how/what)
- `scripts/scaffold.py` — non-interactive scaffolder (create files, append registry, run validate)
- `scripts/validate_description.py` — description linter (length + first-120-char keyword rule). Reused by `scaffold.py` and standalone.

## Failure modes to surface to the user

- Name already exists → suggest a different suffix
- Category not in list → present the category table and ask
- Description starts with stop-verb (`Use`, `A`, `An`, `The`, `Query`) → rewrite leading with the tool name
- Description too long → trim disambiguation tail; keep keyword carrier
- `pixi run validate` fails after scaffold → the registry is in an inconsistent state, abort and revert the partial write (the script does this automatically; report the validator output verbatim)
