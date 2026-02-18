"""Tests for SKILL.md quality: frontmatter fields, registry fields, sections, content depth."""

import re
import sys
from datetime import date
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from validate_registry import parse_frontmatter  # noqa: E402

REGISTRY_PATH = ROOT / "registry.yaml"
SKILLS_DIR = ROOT / "skills"

VALID_SUB_TYPES = {"pipeline", "toolkit", "database", "guide"}
VALID_CATEGORIES = {d.name for d in SKILLS_DIR.iterdir() if d.is_dir()}


def _load_entries():
    with open(REGISTRY_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f).get("entries", [])


def count_code_blocks(text: str) -> int:
    """Count fenced code blocks (pairs of ```)."""
    return text.count("```") // 2


def extract_sections(text: str) -> set:
    """Return the set of H2 section headings in a markdown file."""
    return set(re.findall(r"^## .+", text, re.MULTILINE))


def count_lines(path: Path) -> int:
    return len(path.read_text(encoding="utf-8").splitlines())


ALL_ENTRIES = _load_entries()
PIPELINE_ENTRIES = [e for e in ALL_ENTRIES if e.get("sub_type") == "pipeline"]
TOOLKIT_ENTRIES = [e for e in ALL_ENTRIES if e.get("sub_type") == "toolkit"]
GUIDE_ENTRIES = [e for e in ALL_ENTRIES if e.get("sub_type") == "guide"]
CODE_ENTRIES = [e for e in ALL_ENTRIES if e.get("sub_type") != "guide"]


def entry_id(entry):
    return entry["name"]


# ---------------------------------------------------------------------------
# TestFrontmatterQuality
# ---------------------------------------------------------------------------

class TestFrontmatterQuality:
    """Verify SKILL.md frontmatter field constraints."""

    @pytest.mark.parametrize("entry", ALL_ENTRIES, ids=entry_id)
    def test_license_field_exists(self, entry):
        path = ROOT / entry["path"]
        if not path.exists():
            pytest.skip(f"SKILL.md not found: {entry['path']}")
        fm = parse_frontmatter(path)
        assert "license" in fm, f"[{entry['name']}] Missing 'license' field in frontmatter"

    @pytest.mark.parametrize("entry", ALL_ENTRIES, ids=entry_id)
    def test_description_max_length(self, entry):
        path = ROOT / entry["path"]
        if not path.exists():
            pytest.skip(f"SKILL.md not found: {entry['path']}")
        fm = parse_frontmatter(path)
        desc = fm.get("description", "")
        assert len(desc) <= 1024, (
            f"[{entry['name']}] description is {len(desc)} chars, max is 1024"
        )

    @pytest.mark.parametrize("entry", ALL_ENTRIES, ids=entry_id)
    def test_name_max_length(self, entry):
        path = ROOT / entry["path"]
        if not path.exists():
            pytest.skip(f"SKILL.md not found: {entry['path']}")
        fm = parse_frontmatter(path)
        name = fm.get("name", "")
        assert len(name) <= 64, (
            f"[{entry['name']}] name is {len(name)} chars, max is 64"
        )


# ---------------------------------------------------------------------------
# TestRegistryFields
# ---------------------------------------------------------------------------

class TestRegistryFields:
    """Verify registry.yaml field validity for each entry."""

    @pytest.mark.parametrize("entry", ALL_ENTRIES, ids=entry_id)
    def test_sub_type_valid(self, entry):
        sub_type = entry.get("sub_type")
        assert sub_type in VALID_SUB_TYPES, (
            f"[{entry['name']}] sub_type '{sub_type}' not in {VALID_SUB_TYPES}"
        )

    @pytest.mark.parametrize("entry", ALL_ENTRIES, ids=entry_id)
    def test_type_is_skill(self, entry):
        assert entry.get("type") == "skill", (
            f"[{entry['name']}] type must be 'skill', got '{entry.get('type')}'"
        )

    @pytest.mark.parametrize("entry", ALL_ENTRIES, ids=entry_id)
    def test_category_matches_directory(self, entry):
        category = entry.get("category", "")
        assert category in VALID_CATEGORIES, (
            f"[{entry['name']}] category '{category}' has no matching directory under skills/"
        )

    @pytest.mark.parametrize("entry", ALL_ENTRIES, ids=entry_id)
    def test_date_added_is_valid_iso(self, entry):
        date_str = entry.get("date_added", "")
        assert date_str, f"[{entry['name']}] Missing 'date_added' field"
        try:
            date.fromisoformat(str(date_str))
        except ValueError:
            pytest.fail(
                f"[{entry['name']}] date_added '{date_str}' is not a valid ISO date (YYYY-MM-DD)"
            )

    @pytest.mark.parametrize("entry", ALL_ENTRIES, ids=entry_id)
    def test_path_matches_category(self, entry):
        path = entry.get("path", "")
        category = entry.get("category", "")
        assert path.startswith(f"skills/{category}/"), (
            f"[{entry['name']}] path '{path}' does not start with 'skills/{category}/'"
        )


# ---------------------------------------------------------------------------
# TestSectionStructure
# ---------------------------------------------------------------------------

class TestSectionStructure:
    """Verify required H2 sections exist by sub_type."""

    def _sections(self, entry) -> set:
        path = ROOT / entry["path"]
        if not path.exists():
            pytest.skip(f"SKILL.md not found: {entry['path']}")
        return extract_sections(path.read_text(encoding="utf-8"))

    @pytest.mark.parametrize("entry", ALL_ENTRIES, ids=entry_id)
    def test_has_overview(self, entry):
        assert "## Overview" in self._sections(entry), (
            f"[{entry['name']}] Missing '## Overview'"
        )

    @pytest.mark.parametrize("entry", CODE_ENTRIES, ids=entry_id)
    def test_has_when_to_use(self, entry):
        """Guides use Further Reading instead of When to Use; check code-centric only."""
        assert "## When to Use" in self._sections(entry), (
            f"[{entry['name']}] Missing '## When to Use'"
        )

    @pytest.mark.parametrize("entry", PIPELINE_ENTRIES, ids=entry_id)
    def test_pipeline_sections(self, entry):
        sections = self._sections(entry)
        required = {"## Workflow", "## Key Parameters", "## Troubleshooting", "## References"}
        missing = required - sections
        assert not missing, f"[{entry['name']}] Missing pipeline sections: {missing}"

    @pytest.mark.parametrize("entry", TOOLKIT_ENTRIES, ids=entry_id)
    def test_toolkit_sections(self, entry):
        sections = self._sections(entry)
        required = {"## Key Parameters", "## Troubleshooting"}
        missing = required - sections
        assert not missing, f"[{entry['name']}] Missing toolkit sections: {missing}"

    @pytest.mark.parametrize("entry", GUIDE_ENTRIES, ids=entry_id)
    def test_guide_sections(self, entry):
        sections = self._sections(entry)
        required = {"## Key Concepts", "## Decision Framework", "## Best Practices", "## Common Pitfalls"}
        missing = required - sections
        assert not missing, f"[{entry['name']}] Missing guide sections: {missing}"


# ---------------------------------------------------------------------------
# TestContentDepth
# ---------------------------------------------------------------------------

class TestContentDepth:
    """Verify code block counts and line counts meet minimum thresholds."""

    @pytest.mark.parametrize("entry", PIPELINE_ENTRIES, ids=entry_id)
    def test_pipeline_code_blocks(self, entry):
        path = ROOT / entry["path"]
        if not path.exists():
            pytest.skip(f"SKILL.md not found: {entry['path']}")
        count = count_code_blocks(path.read_text(encoding="utf-8"))
        assert count >= 10, (
            f"[{entry['name']}] Pipeline has {count} code blocks, minimum is 10"
        )

    @pytest.mark.parametrize("entry", TOOLKIT_ENTRIES, ids=entry_id)
    def test_toolkit_code_blocks(self, entry):
        path = ROOT / entry["path"]
        if not path.exists():
            pytest.skip(f"SKILL.md not found: {entry['path']}")
        count = count_code_blocks(path.read_text(encoding="utf-8"))
        assert count >= 10, (
            f"[{entry['name']}] Toolkit has {count} code blocks, minimum is 10"
        )

    @pytest.mark.parametrize("entry", GUIDE_ENTRIES, ids=entry_id)
    def test_guide_minimum_lines(self, entry):
        path = ROOT / entry["path"]
        if not path.exists():
            pytest.skip(f"SKILL.md not found: {entry['path']}")
        lines = count_lines(path)
        assert lines >= 100, (
            f"[{entry['name']}] Guide has {lines} lines, minimum is 100"
        )

    @pytest.mark.parametrize("entry", ALL_ENTRIES, ids=entry_id)
    def test_references_contain_url(self, entry):
        path = ROOT / entry["path"]
        if not path.exists():
            pytest.skip(f"SKILL.md not found: {entry['path']}")
        text = path.read_text(encoding="utf-8")

        ref_match = re.search(
            r"^## References\s*\n(.*?)(?=^## |\Z)", text, re.MULTILINE | re.DOTALL
        )
        further_match = re.search(
            r"^## Further Reading\s*\n(.*?)(?=^## |\Z)", text, re.MULTILINE | re.DOTALL
        )

        has_url = (ref_match and "http" in ref_match.group(1)) or (
            further_match and "http" in further_match.group(1)
        )
        assert has_url, (
            f"[{entry['name']}] No URLs found in '## References' or '## Further Reading'"
        )
