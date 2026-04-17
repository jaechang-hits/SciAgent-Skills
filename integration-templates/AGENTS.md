# Scientific Skills (SciAgent-Skills)

This project uses [SciAgent-Skills](https://github.com/jaechang-hits/SciAgent-Skills) — 197 life sciences skills for AI coding agents.

## How to use

1. **Discover skills**: Read `.sciagent-skills/registry.yaml`. Each entry has a `description` field — match it to the current task.
2. **Load a skill**: Read the file at the entry's `path`, prefixed with `.sciagent-skills/`. For example, if `path` is `skills/genomics-bioinformatics/scanpy-scrna-seq/SKILL.md`, read `.sciagent-skills/skills/genomics-bioinformatics/scanpy-scrna-seq/SKILL.md`.
3. **Follow the skill**: The SKILL.md contains runnable code examples, key parameters, troubleshooting, and best practices. Use them to guide your implementation.

## Skill types

- **Pipeline** — linear input-to-output workflow (e.g., DESeq2 differential expression)
- **Toolkit** — collection of independent modules (e.g., RDKit cheminformatics)
- **Database** — API wrapper for external data sources (e.g., PubChem, UniProt)
- **Guide** — decision frameworks and best practices (e.g., statistical test selection)

## Tips

- You do NOT need to read the full registry upfront. Search or scan it when a scientific computing task comes up.
- Skills are independent — no inter-skill dependencies.
- Each skill lists its own Python package prerequisites in the Prerequisites section.
