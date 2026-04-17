# SciAgent-Skills integration for Cursor
#
# Usage: copy this file to your project's .cursor/rules/ directory:
#   cp .sciagent-skills/integration-templates/cursor-rules.md .cursor/rules/sciagent-skills.md

When performing scientific computing, bioinformatics, cheminformatics, or life science tasks, use the SciAgent-Skills library:

1. Read `.sciagent-skills/registry.yaml` to find relevant skills by matching the `description` field to the current task.
2. Load the full skill by reading the file at the entry's `path`, prefixed with `.sciagent-skills/`. Example: `.sciagent-skills/skills/genomics-bioinformatics/scanpy-scrna-seq/SKILL.md`.
3. Follow the skill's workflow, code examples, and key parameters to guide implementation.

Skill types: pipeline (linear workflow), toolkit (independent modules), database (API wrapper), guide (decision framework).

Skills are independent and each lists its own Python package prerequisites.
