# Contributing to SciAgent-Skills

Thank you for your interest in contributing! SciAgent-Skills is designed so that Claude Code can author new skills with minimal effort — but human contributions are equally welcome.

## Two ways to add a skill

### Option A: Let Claude Code do it

Open Claude Code in the SciCraft repo and type:

```
Add a skill for <tool name>
```

Claude Code reads `CLAUDE.md`, follows the 6-step workflow, and produces a validated `SKILL.md`. Review the output, then open a PR.

### Option B: Write it yourself

1. Read `CLAUDE.md` — the full authoring workflow is in Steps 1–6
2. Classify your topic: pipeline / toolkit / database / guide
3. Choose a category directory under `skills/`
4. Copy the right template from `templates/`
5. Fill in the template following the format rules in `CLAUDE.md`
6. Add an entry to `registry.yaml`
7. Run `pixi run test` — all checks must pass before opening a PR

## Quality requirements

Every skill must pass `pixi run test`. The test suite checks:

- Frontmatter: `name`, `description`, `license` fields present; `description` ≤ 1024 chars
- Required sections present in the correct order (varies by skill type)
- Minimum code block count: ≥ 10 for pipelines, ≥ 12 for toolkits
- Troubleshooting table: ≥ 5 rows
- Key Parameters table: ≥ 5 rows
- `registry.yaml` entry present and consistent with the file

## Running tests locally

```bash
# Install pixi if needed
curl -fsSL https://pixi.sh/install.sh | bash

# Install dependencies
pixi install

# Run the full test suite
pixi run test

# Registry-only validation
pixi run validate
```

## PR checklist

Before opening a pull request, confirm:

- `pixi run test` passes
- `registry.yaml` is updated
- Code blocks run as-is with sample data or clear placeholders
- No verbatim copy-paste from third-party sources
- References section includes URLs for all cited sources

## Reporting issues

Use the issue templates:
- **Bug report** — errors in existing skill files (wrong code, broken links, incorrect parameters)
- **Skill request** — tools or topics you'd like to see covered

## License

By contributing, you agree that your work will be released under [CC-BY-4.0](LICENSE).
