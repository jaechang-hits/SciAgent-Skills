#!/usr/bin/env python3
"""Validate registry.yaml: check all entries point to existing SKILL.md files
with valid YAML frontmatter."""

import sys
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parent.parent
REGISTRY_PATH = ROOT / "registry.yaml"
REQUIRED_FRONTMATTER = {"name", "description"}


def parse_frontmatter(skill_path: Path) -> dict:
    """Extract YAML frontmatter from a SKILL.md file."""
    text = skill_path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}
    end = text.index("---", 3)
    return yaml.safe_load(text[3:end]) or {}


def validate() -> list[str]:
    errors: list[str] = []

    if not REGISTRY_PATH.exists():
        errors.append(f"Registry not found: {REGISTRY_PATH}")
        return errors

    with open(REGISTRY_PATH, encoding="utf-8") as f:
        registry = yaml.safe_load(f)

    entries = registry.get("entries", [])
    if not entries:
        errors.append("Registry has no entries")
        return errors

    seen_names: set[str] = set()
    for i, entry in enumerate(entries):
        name = entry.get("name", f"<entry {i}>")

        # Duplicate name check
        if name in seen_names:
            errors.append(f"Duplicate entry name: {name}")
        seen_names.add(name)

        # Required registry fields
        for field in ("name", "path", "category", "description"):
            if not entry.get(field):
                errors.append(f"[{name}] Missing registry field: {field}")

        # File existence
        skill_path = ROOT / entry.get("path", "")
        if not skill_path.exists():
            errors.append(f"[{name}] SKILL.md not found: {entry.get('path')}")
            continue

        # Frontmatter validation
        fm = parse_frontmatter(skill_path)
        missing = REQUIRED_FRONTMATTER - set(fm.keys())
        if missing:
            errors.append(f"[{name}] Missing frontmatter: {missing}")

        # Name consistency
        if fm.get("name") and fm["name"] != name:
            errors.append(
                f"[{name}] Frontmatter name mismatch: "
                f"registry='{name}' vs file='{fm['name']}'"
            )

    return errors


def main():
    errors = validate()
    if errors:
        print(f"FAILED — {len(errors)} error(s):", file=sys.stderr)
        for e in errors:
            print(f"  ✗ {e}", file=sys.stderr)
        sys.exit(1)
    else:
        print(f"OK — {len(yaml.safe_load(REGISTRY_PATH.read_text())['entries'])} entries validated")


if __name__ == "__main__":
    main()
