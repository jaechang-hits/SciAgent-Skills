<!-- Template: Guide Sub-type (prose-centric) — for entries whose core value is domain
     knowledge, decision frameworks, and best practices rather than runnable code.
     For code-centric entries, use SKILL_TEMPLATE.md (Pipeline) or SKILL_TEMPLATE_TOOLKIT.md.

     Scaffolding shortcut: `.claude/skills/sciagent-skill-creator/` can drop this template
     into the correct category, fill the frontmatter, and append the registry entry for you.

     Note: the optional `tags: [...]` field lives in registry.yaml (entry-level), NOT in the
     SKILL.md frontmatter below. See CLAUDE.md Step 5 "tags field" for when to use it. -->
---
name: "Skill Name Here"
# Description rules (CLAUDE.md Step 5):
#   - Length ≤ 1024 chars; first 120 chars carry discovery weight
#   - Lead with the domain or decision-space keyword — NOT stop verbs (Use/A/An/The/...)
#   - Cross-references ("For X use Y") go at the END
#   - No promotional adjectives (powerful/comprehensive/state-of-the-art/...)
# Good: "scRNA-seq cell-type annotation decision framework. Three-tier strategy: manual markers, CellTypist, popV ensemble transfer. ..."
# Bad:  "A comprehensive guide to single-cell annotation best practices..."
description: "<Domain or decision-space keyword> <what it covers>. <When to consult>. <Disambiguation>."
license: "CC-BY-4.0"
---

# Skill Name Here

## Overview

Brief description of this knowhow entry (2-3 sentences). What domain does it cover? Why is it important for research decisions?

## Key Concepts

<!-- 3+ subsections with clear definitions and explanations. -->

### Concept 1
Definition and explanation.

### Concept 2
Definition and explanation.

### Concept 3
Definition and explanation.

## Decision Framework

<!-- Use BOTH an ASCII tree diagram AND a decision table.
     The tree gives a quick visual overview; the table provides detail. -->

When to choose between different approaches:

```
Question: What is your goal?
├── Goal A → Approach 1 (see Best Practices §1)
├── Goal B → Approach 2 (see Best Practices §2)
└── Goal C
    ├── Sub-condition X → Approach 3
    └── Sub-condition Y → Approach 4
```

| Scenario | Recommended Approach | Rationale |
|----------|---------------------|-----------|
| Scenario 1 | Approach A | Reason |
| Scenario 2 | Approach B | Reason |
| Scenario 3 | Approach C | Reason |

## Best Practices

<!-- 5+ items, numbered. Include rationale for each. -->

1. **Practice 1**: Description and rationale
2. **Practice 2**: Description and rationale
3. **Practice 3**: Description and rationale
4. **Practice 4**: Description and rationale
5. **Practice 5**: Description and rationale

## Common Pitfalls

<!-- 5+ items. Each must include a "How to avoid" sub-item. -->

1. **Pitfall 1**: What goes wrong and why
   - *How to avoid*: Preventive measure
2. **Pitfall 2**: What goes wrong and why
   - *How to avoid*: Preventive measure
3. **Pitfall 3**: What goes wrong and why
   - *How to avoid*: Preventive measure
4. **Pitfall 4**: What goes wrong and why
   - *How to avoid*: Preventive measure
5. **Pitfall 5**: What goes wrong and why
   - *How to avoid*: Preventive measure

## Workflow

<!-- Optional but recommended when the knowhow has a clear sequential process.
     More structured than Protocol Guidelines: include substeps and decision points.
     Use this when there's a well-defined sequence (e.g., manuscript writing, study design). -->

1. **Step 1: Planning**
   - Substep 1a
   - Substep 1b
   - Decision point: If X → proceed to Step 2. If Y → revisit.
2. **Step 2: Execution**
   - Substep 2a
   - Substep 2b
3. **Step 3: Review**
   - Substep 3a
4. **Step 4: Finalization**
   - Substep 4a

## Protocol Guidelines

<!-- Use when there's no single well-defined workflow but rather general procedural guidance.
     High-level steps, not full code — see Related Skills for implementations. -->

1. **Guideline 1**: Description
2. **Guideline 2**: Description
3. **Guideline 3**: Description
4. **Guideline 4**: Description

## Further Reading

<!-- 3+ items with URLs. -->

- [Reference 1](https://example.com) — Description
- [Reference 2](https://example.com) — Description
- [Textbook/Review](https://example.com) — Description

## Related Skills

<!-- Links to relevant SKILL.md entries with brief connection description. -->

- `skill-name-1` — Brief connection to this knowhow
- `skill-name-2` — Brief connection to this knowhow

## Companion Assets

<!-- Optional. List any templates, style files, or other non-code assets
     in the assets/ subdirectory. Only include this section if assets/ exists. -->

- `assets/template.ext` — Description of what this asset provides
