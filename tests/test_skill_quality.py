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
        assert count >= 12, (
            f"[{entry['name']}] Toolkit has {count} code blocks, minimum is 12"
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

    @pytest.mark.parametrize("entry", ALL_ENTRIES, ids=entry_id)
    def test_references_minimum_three_items(self, entry):
        """References or Further Reading must contain at least 3 reference items."""
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

        section_text = ""
        if ref_match:
            section_text += ref_match.group(1)
        if further_match:
            section_text += further_match.group(1)

        # Count reference items: lines starting with - or a number (1. 2. etc.)
        items = re.findall(r"^\s*[-*]\s+\S|^\s*\d+\.\s+\S", section_text, re.MULTILINE)
        assert len(items) >= 3, (
            f"[{entry['name']}] References/Further Reading has {len(items)} items, minimum is 3"
        )

    @pytest.mark.parametrize("entry", CODE_ENTRIES, ids=entry_id)
    def test_when_to_use_minimum_items(self, entry):
        """When to Use section must have at least 5 bullet-point items."""
        path = ROOT / entry["path"]
        if not path.exists():
            pytest.skip(f"SKILL.md not found: {entry['path']}")
        text = path.read_text(encoding="utf-8")

        match = re.search(
            r"^## When to Use\s*\n(.*?)(?=^## |\Z)", text, re.MULTILINE | re.DOTALL
        )
        if not match:
            pytest.fail(f"[{entry['name']}] Missing '## When to Use' section")

        bullets = re.findall(r"^\s*[-*]", match.group(1), re.MULTILINE)
        assert len(bullets) >= 5, (
            f"[{entry['name']}] '## When to Use' has {len(bullets)} items, minimum is 5"
        )

    @pytest.mark.parametrize("entry", CODE_ENTRIES, ids=entry_id)
    def test_key_parameters_minimum_rows(self, entry):
        """Key Parameters table must have at least 5 data rows."""
        path = ROOT / entry["path"]
        if not path.exists():
            pytest.skip(f"SKILL.md not found: {entry['path']}")
        text = path.read_text(encoding="utf-8")

        match = re.search(
            r"^## Key Parameters\s*\n(.*?)(?=^## |\Z)", text, re.MULTILINE | re.DOTALL
        )
        if not match:
            pytest.fail(f"[{entry['name']}] Missing '## Key Parameters' section")

        # Count table rows: lines starting with | but NOT the header or separator
        section = match.group(1)
        table_rows = re.findall(r"^\|[^|]+\|", section, re.MULTILINE)
        # Exclude header row (contains letters) and separator row (contains dashes only)
        data_rows = [r for r in table_rows
                     if not re.match(r"^\|[-| :]+\|$", r.strip())]
        # First row is the header, remaining are data rows
        n_data = max(0, len(data_rows) - 1)
        assert n_data >= 5, (
            f"[{entry['name']}] '## Key Parameters' has {n_data} data rows, minimum is 5"
        )

    @pytest.mark.parametrize("entry", CODE_ENTRIES, ids=entry_id)
    def test_troubleshooting_minimum_rows(self, entry):
        """Troubleshooting table must have at least 5 data rows."""
        path = ROOT / entry["path"]
        if not path.exists():
            pytest.skip(f"SKILL.md not found: {entry['path']}")
        text = path.read_text(encoding="utf-8")

        match = re.search(
            r"^## Troubleshooting\s*\n(.*?)(?=^## |\Z)", text, re.MULTILINE | re.DOTALL
        )
        if not match:
            pytest.fail(f"[{entry['name']}] Missing '## Troubleshooting' section")

        section = match.group(1)
        table_rows = re.findall(r"^\|[^|]+\|", section, re.MULTILINE)
        data_rows = [r for r in table_rows
                     if not re.match(r"^\|[-| :]+\|$", r.strip())]
        n_data = max(0, len(data_rows) - 1)
        assert n_data >= 5, (
            f"[{entry['name']}] '## Troubleshooting' has {n_data} data rows, minimum is 5"
        )

    @pytest.mark.parametrize("entry", PIPELINE_ENTRIES, ids=entry_id)
    def test_pipeline_has_expected_outputs(self, entry):
        """Pipeline entries must have '## Expected Outputs' section."""
        path = ROOT / entry["path"]
        if not path.exists():
            pytest.skip(f"SKILL.md not found: {entry['path']}")
        text = path.read_text(encoding="utf-8")
        assert "## Expected Outputs" in text, (
            f"[{entry['name']}] Missing '## Expected Outputs' section (required for pipeline)"
        )

    @pytest.mark.parametrize("entry", GUIDE_ENTRIES, ids=entry_id)
    def test_guide_best_practices_minimum_items(self, entry):
        """Guide Best Practices must have at least 5 items."""
        path = ROOT / entry["path"]
        if not path.exists():
            pytest.skip(f"SKILL.md not found: {entry['path']}")
        text = path.read_text(encoding="utf-8")

        match = re.search(
            r"^## Best Practices\s*\n(.*?)(?=^## |\Z)", text, re.MULTILINE | re.DOTALL
        )
        if not match:
            pytest.fail(f"[{entry['name']}] Missing '## Best Practices' section")

        items = re.findall(r"^\s*\d+\.\s+\S|^\s*[-*]\s+\S", match.group(1), re.MULTILINE)
        assert len(items) >= 5, (
            f"[{entry['name']}] '## Best Practices' has {len(items)} items, minimum is 5"
        )

    @pytest.mark.parametrize("entry", GUIDE_ENTRIES, ids=entry_id)
    def test_guide_common_pitfalls_minimum_items(self, entry):
        """Guide Common Pitfalls must have at least 5 items."""
        path = ROOT / entry["path"]
        if not path.exists():
            pytest.skip(f"SKILL.md not found: {entry['path']}")
        text = path.read_text(encoding="utf-8")

        match = re.search(
            r"^## Common Pitfalls\s*\n(.*?)(?=^## |\Z)", text, re.MULTILINE | re.DOTALL
        )
        if not match:
            pytest.fail(f"[{entry['name']}] Missing '## Common Pitfalls' section")

        items = re.findall(r"^\s*\d+\.\s+\S|^\s*[-*]\s+\S", match.group(1), re.MULTILINE)
        assert len(items) >= 5, (
            f"[{entry['name']}] '## Common Pitfalls' has {len(items)} items, minimum is 5"
        )


# ---------------------------------------------------------------------------
# TestDatabaseAndToolkitStructure
# ---------------------------------------------------------------------------

DATABASE_ENTRIES = [e for e in ALL_ENTRIES if e.get("sub_type") == "database"]
TOOLKIT_AND_DB_ENTRIES = [e for e in ALL_ENTRIES if e.get("sub_type") in {"database", "toolkit"}]


def _count_modules(text: str) -> int:
    """Count numbered module/query subsections (### Module N or ### Query N)."""
    return len(re.findall(r"^### (?:Module|Query) \d", text, re.MULTILINE))


# Toolkits with 6+ Core API modules
LARGE_TOOLKIT_ENTRIES = [
    e for e in TOOLKIT_ENTRIES
    if _count_modules((ROOT / e["path"]).read_text(encoding="utf-8"))
    >= 6
    if (ROOT / e["path"]).exists()
]


class TestDatabaseAndToolkitStructure:
    """Verify database and toolkit specific structural requirements."""

    @pytest.mark.parametrize("entry", TOOLKIT_AND_DB_ENTRIES, ids=entry_id)
    def test_has_core_api_section(self, entry):
        """Database and toolkit entries must have '## Core API' or '## Workflow' section."""
        path = ROOT / entry["path"]
        if not path.exists():
            pytest.skip(f"SKILL.md not found: {entry['path']}")
        text = path.read_text(encoding="utf-8")
        has_core_api = "## Core API" in text
        has_workflow = "## Workflow" in text
        assert has_core_api or has_workflow, (
            f"[{entry['name']}] Missing '## Core API' or '## Workflow' section "
            "(required for database/toolkit sub_types)"
        )

    @pytest.mark.parametrize("entry", TOOLKIT_AND_DB_ENTRIES, ids=entry_id)
    def test_has_common_workflows_or_recipes(self, entry):
        """Database and toolkit entries must have Common Workflows or Common Recipes."""
        path = ROOT / entry["path"]
        if not path.exists():
            pytest.skip(f"SKILL.md not found: {entry['path']}")
        sections = set(re.findall(r"^## .+", path.read_text(encoding="utf-8"), re.MULTILINE))
        has_workflows = "## Common Workflows" in sections
        has_recipes = "## Common Recipes" in sections
        assert has_workflows or has_recipes, (
            f"[{entry['name']}] Missing both '## Common Workflows' and '## Common Recipes'; "
            "at least one is required for database/toolkit entries"
        )

    @pytest.mark.parametrize("entry", LARGE_TOOLKIT_ENTRIES, ids=entry_id)
    def test_large_toolkit_has_quick_start(self, entry):
        """Toolkit entries with 6+ Core API modules must have a '## Quick Start' section."""
        path = ROOT / entry["path"]
        if not path.exists():
            pytest.skip(f"SKILL.md not found: {entry['path']}")
        text = path.read_text(encoding="utf-8")
        n_modules = _count_modules(text)
        assert "## Quick Start" in text, (
            f"[{entry['name']}] Toolkit has {n_modules} modules but is missing '## Quick Start' "
            "(required for toolkits with 6+ Core API modules)"
        )

    @pytest.mark.parametrize("entry", TOOLKIT_ENTRIES, ids=entry_id)
    def test_toolkit_when_to_use_has_alternative_comparison(self, entry):
        """Toolkit 'When to Use' must mention at least one alternative tool (routing guidance)."""
        path = ROOT / entry["path"]
        if not path.exists():
            pytest.skip(f"SKILL.md not found: {entry['path']}")
        text = path.read_text(encoding="utf-8")

        wtu_match = re.search(
            r"^## When to Use\s*\n(.*?)(?=^## |\Z)", text, re.MULTILINE | re.DOTALL
        )
        if not wtu_match:
            pytest.fail(f"[{entry['name']}] Missing '## When to Use' section")

        wtu_text = wtu_match.group(1)
        # Accept any of these routing patterns (within a single line):
        # "use X instead", "prefer X", "For [condition] use Y", "→ use X",
        # "use X when", "Alternatives:", "instead of"
        has_alternative = bool(re.search(
            r"instead|alternative|prefer (?!to )|"  # "instead", "alternatives", "prefer "
            r"→ use |"                               # arrow shorthand "→ use X"
            r"\bfor\b.{1,250}\buse\b|"              # "For [condition], use [tool]"
            r"\buse\b.{1,250}\bwhen\b",             # "Use [tool] when [condition]"
            wtu_text,
            re.IGNORECASE,
        ))
        assert has_alternative, (
            f"[{entry['name']}] '## When to Use' does not mention any alternative tool. "
            "Add a bullet like: '- Use `other-tool` instead when [condition]'"
        )
