#!/usr/bin/env python3
"""Scaffold a new SciAgent-Skills entry.

Non-interactive. The invoking agent collects fields from the user in chat,
then calls this script with explicit args. The script validates everything,
copies the matching template into skills/{category}/{name}/SKILL.md with the
frontmatter substituted, appends a registry entry, and runs `pixi run validate`.

On any failure the script aborts WITHOUT writing partial state. The skills
directory is left untouched and registry.yaml is restored from its in-memory
snapshot.

Usage:
    python scaffold.py \
        --sub-type pipeline \
        --category genomics-bioinformatics \
        --name pydeseq2-differential-expression \
        --description "PyDESeq2 ..." \
        --license MIT \
        --tags databases,literature   # optional

Exit codes:
    0  success
    1  validation failure (no files written)
    2  internal error (template missing, registry malformed, etc.)
"""

from __future__ import annotations

import argparse
import datetime
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
REGISTRY_PATH = ROOT / "registry.yaml"
SKILLS_DIR = ROOT / "skills"
LEGACY_DIR = ROOT / "legacy"
TEMPLATE_DIR = ROOT / "templates"

SUBTYPE_TEMPLATE = {
    "pipeline": "SKILL_TEMPLATE.md",
    "toolkit": "SKILL_TEMPLATE_TOOLKIT.md",
    "database": "SKILL_TEMPLATE_TOOLKIT.md",  # database uses toolkit template w/ DB adaptations
    "guide": "SKILL_TEMPLATE_PROSE.md",
}

NAME_PATTERN = re.compile(r"^[a-z][a-z0-9-]*[a-z0-9]$")
TAG_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]*$")
STOP_VERBS = {"use", "a", "an", "the", "query", "fetch", "run"}


def fail(msg: str) -> None:
    print(f"FAIL: {msg}", file=sys.stderr)
    sys.exit(1)


def existing_names() -> set[str]:
    """Names already present in registry.yaml (regex parse, no YAML dep)."""
    if not REGISTRY_PATH.exists():
        return set()
    pattern = re.compile(r'^\s*-\s*name:\s*"?([a-z][a-z0-9-]*)"?\s*$', re.MULTILINE)
    return set(pattern.findall(REGISTRY_PATH.read_text(encoding="utf-8")))


def legacy_names() -> set[str]:
    if not LEGACY_DIR.exists():
        return set()
    return {p.name for p in LEGACY_DIR.iterdir() if p.is_dir()}


def valid_categories() -> set[str]:
    if not SKILLS_DIR.exists():
        fail(f"skills/ not found at {SKILLS_DIR}")
    return {p.name for p in SKILLS_DIR.iterdir() if p.is_dir()}


def validate_name(name: str) -> None:
    if not NAME_PATTERN.match(name):
        fail(
            f"name '{name}' must match {NAME_PATTERN.pattern} "
            "(lowercase, hyphen-separated, starts with letter, ends alphanumeric)"
        )
    if name in existing_names():
        fail(f"name '{name}' already in registry.yaml")
    if name in legacy_names():
        fail(
            f"name '{name}' exists in legacy/ (deprecated). "
            "Pick a different name or restore the legacy entry instead of creating a parallel one."
        )


def validate_category(category: str) -> None:
    cats = valid_categories()
    if category not in cats:
        fail(
            f"category '{category}' not in skills/ ({sorted(cats)}). "
            "Add the directory first or pick an existing category."
        )


def validate_description(description: str) -> None:
    """Reuse validate_description.py logic by importing it."""
    here = Path(__file__).parent
    sys.path.insert(0, str(here))
    from validate_description import check  # type: ignore

    errors = check(description)
    if errors:
        for e in errors:
            print(f"  description: {e}", file=sys.stderr)
        fail("description failed validation (see above)")


def validate_tags(tags: list[str]) -> None:
    seen = set()
    for t in tags:
        if not TAG_PATTERN.match(t):
            fail(f"tag '{t}' must match {TAG_PATTERN.pattern} (lowercase kebab-case)")
        if t in seen:
            fail(f"tag '{t}' duplicated")
        seen.add(t)


def validate_subtype(sub_type: str) -> None:
    if sub_type not in SUBTYPE_TEMPLATE:
        fail(f"sub-type '{sub_type}' must be one of {sorted(SUBTYPE_TEMPLATE)}")


def render_skill_md(
    template_path: Path, name: str, description: str, license_str: str
) -> str:
    text = template_path.read_text(encoding="utf-8")
    # The templates open with a comment then a frontmatter block. Replace the
    # placeholder name/description/license in the frontmatter only.
    frontmatter_end = text.index("\n---\n", text.index("---") + 3)
    head = text[: frontmatter_end + len("\n---\n")]
    body = text[frontmatter_end + len("\n---\n") :]

    # Replace the three frontmatter fields. Templates use varying quoting; rewrite each line.
    new_head_lines = []
    for line in head.splitlines():
        stripped = line.strip()
        if stripped.startswith("name:"):
            new_head_lines.append(f'name: "{name}"')
        elif stripped.startswith("description:"):
            new_head_lines.append(f'description: "{description}"')
        elif stripped.startswith("license:"):
            new_head_lines.append(f'license: "{license_str}"')
        else:
            new_head_lines.append(line)
    return "\n".join(new_head_lines) + "\n" + body


def append_registry_entry(
    name: str,
    sub_type: str,
    category: str,
    skill_path: str,
    description: str,
    tags: list[str],
) -> str:
    """Return the registry text with the new entry appended. Does NOT write to disk."""
    today = datetime.date.today().isoformat()
    entry_lines = [
        "",
        f'  - name: "{name}"',
        f"    type: skill",
        f"    sub_type: {sub_type}",
        f'    category: "{category}"',
        f'    path: "{skill_path}"',
        f'    description: "{description}"',
        f'    date_added: "{today}"',
    ]
    if tags:
        tag_list = ", ".join(f'"{t}"' for t in tags)
        entry_lines.append(f"    tags: [{tag_list}]")
    appended = "\n".join(entry_lines) + "\n"

    current = REGISTRY_PATH.read_text(encoding="utf-8")
    if not current.endswith("\n"):
        current += "\n"
    return current + appended


def run_validate() -> bool:
    """Run pixi run validate; return True if it exits 0."""
    try:
        proc = subprocess.run(
            ["pixi", "run", "validate"],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        print("WARN: pixi not on PATH; skipping post-scaffold validate", file=sys.stderr)
        return True
    sys.stdout.write(proc.stdout)
    sys.stderr.write(proc.stderr)
    return proc.returncode == 0


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Scaffold a new SciAgent-Skills entry.")
    p.add_argument("--sub-type", required=True, choices=sorted(SUBTYPE_TEMPLATE))
    p.add_argument("--category", required=True)
    p.add_argument("--name", required=True)
    p.add_argument("--description", required=True)
    p.add_argument("--license", required=True, dest="license_str")
    p.add_argument(
        "--tags",
        default="",
        help="Comma-separated list (e.g., databases,literature). Optional.",
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()
    tags = [t.strip() for t in args.tags.split(",") if t.strip()]

    # 1. Validate everything BEFORE touching disk.
    validate_subtype(args.sub_type)
    validate_category(args.category)
    validate_name(args.name)
    validate_description(args.description)
    validate_tags(tags)

    template_path = TEMPLATE_DIR / SUBTYPE_TEMPLATE[args.sub_type]
    if not template_path.exists():
        print(f"INTERNAL: template missing: {template_path}", file=sys.stderr)
        sys.exit(2)

    entry_dir = SKILLS_DIR / args.category / args.name
    skill_path_rel = f"skills/{args.category}/{args.name}/SKILL.md"
    skill_path_abs = ROOT / skill_path_rel

    if entry_dir.exists():
        fail(f"target directory already exists: {entry_dir}")

    rendered = render_skill_md(
        template_path, args.name, args.description, args.license_str
    )
    new_registry = append_registry_entry(
        args.name,
        args.sub_type,
        args.category,
        skill_path_rel,
        args.description,
        tags,
    )

    # 2. Snapshot registry, then write.
    registry_backup = REGISTRY_PATH.read_text(encoding="utf-8")
    entry_dir.mkdir(parents=True)
    skill_path_abs.write_text(rendered, encoding="utf-8")
    REGISTRY_PATH.write_text(new_registry, encoding="utf-8")

    # 3. Run validate; revert on failure.
    if not run_validate():
        REGISTRY_PATH.write_text(registry_backup, encoding="utf-8")
        shutil.rmtree(entry_dir)
        fail("pixi run validate failed; partial scaffold reverted")

    print()
    print(f"OK: created {skill_path_rel}")
    print(f"OK: appended registry entry '{args.name}'")
    print()
    print("Next steps:")
    print(f"  1. Fill in Overview, When to Use, Workflow/Core API, Recipes, References in:")
    print(f"     {skill_path_rel}")
    print("  2. Run `pixi run test` to verify sub-type structural checks (code blocks, tables, sections)")


if __name__ == "__main__":
    main()
