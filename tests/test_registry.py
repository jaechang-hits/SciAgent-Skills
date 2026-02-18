"""Tests for registry integrity and SKILL.md format."""

import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from validate_registry import parse_frontmatter, validate  # noqa: E402


REGISTRY_PATH = ROOT / "registry.yaml"


@pytest.fixture
def registry():
    with open(REGISTRY_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


@pytest.fixture
def entries(registry):
    return registry.get("entries", [])


class TestRegistryIntegrity:
    def test_no_validation_errors(self):
        errors = validate()
        assert errors == [], f"Validation errors:\n" + "\n".join(errors)

    def test_entries_not_empty(self, entries):
        assert len(entries) > 0

    def test_no_duplicate_names(self, entries):
        names = [e["name"] for e in entries]
        assert len(names) == len(set(names)), f"Duplicates: {[n for n in names if names.count(n) > 1]}"

    def test_no_duplicate_paths(self, entries):
        paths = [e["path"] for e in entries]
        assert len(paths) == len(set(paths)), f"Duplicates: {[p for p in paths if paths.count(p) > 1]}"


class TestSkillFiles:
    def test_all_skill_files_exist(self, entries):
        missing = []
        for entry in entries:
            path = ROOT / entry["path"]
            if not path.exists():
                missing.append(entry["name"])
        assert missing == [], f"Missing SKILL.md files: {missing}"

    def test_frontmatter_has_required_fields(self, entries):
        bad = []
        for entry in entries:
            path = ROOT / entry["path"]
            if not path.exists():
                continue
            fm = parse_frontmatter(path)
            if not fm.get("name") or not fm.get("description"):
                bad.append(entry["name"])
        assert bad == [], f"Missing name/description in frontmatter: {bad}"

    def test_skill_files_not_empty(self, entries):
        empty = []
        for entry in entries:
            path = ROOT / entry["path"]
            if path.exists() and path.stat().st_size < 100:
                empty.append(entry["name"])
        assert empty == [], f"Nearly empty SKILL.md files: {empty}"


class TestSkillDiscovery:
    """Ensure all SKILL.md files on disk are registered."""

    def test_all_skill_files_registered(self, entries):
        registered_paths = {e["path"] for e in entries}
        skills_dir = ROOT / "skills"
        on_disk = set()
        for skill_md in skills_dir.rglob("SKILL.md"):
            rel = str(skill_md.relative_to(ROOT))
            on_disk.add(rel)

        unregistered = on_disk - registered_paths
        assert unregistered == set(), f"SKILL.md files not in registry: {unregistered}"
