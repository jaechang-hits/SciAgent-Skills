"""Tests for the repo -> skill catalog sheet sync (pure logic only, no network or git)."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

_SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "sync_skill_catalog.py"
_spec = importlib.util.spec_from_file_location("sync_skill_catalog", _SCRIPT)
assert _spec is not None and _spec.loader is not None
sync = importlib.util.module_from_spec(_spec)
sys.modules["sync_skill_catalog"] = sync
_spec.loader.exec_module(sync)

OWN = sync.DEFAULT_VISIBILITY
OTHER = "공개" if OWN != "공개" else "비공개"


def _row(name: str, visibility: str = OWN, **overrides: str) -> dict[str, str]:
    row = {
        sync.NAME: name,
        sync.CATEGORY: "유전체·생물정보",
        sync.VISIBILITY: visibility,
        sync.DESC_EN: "Does a thing.",
        sync.DESC_KO: "어떤 일을 합니다.",
        sync.PROMPT_EN: "Do the thing for human TP53.",
        sync.PROMPT_KO: "사람 TP53에 대해 해주세요.",
        sync.CREATED: "2026-01-01",
        sync.MODIFIED: "2026-01-01",
    }
    row.update({getattr(sync, k): v for k, v in overrides.items()})
    return row


def _skill(name: str, description: str = "desc") -> object:
    return sync.Skill(name=name, description=description, path=f"skills/{name}/SKILL.md")


def _plan(rows, now, base):
    dates = {s.name: ("2026-10-01", "2026-10-02") for s in now}
    return sync.build_plan(rows, {s.name: s for s in now}, {s.name: s for s in base}, dates)


def test_new_skill_is_added_with_blank_written_fields():
    entries, excluded = _plan([_row("a")], [_skill("a"), _skill("b")], [_skill("a")])
    assert excluded == []
    [entry] = entries
    assert entry["op"] == "add" and entry["name"] == "b" and entry["reviewed"] is False
    row = entry["row"]
    assert row[sync.VISIBILITY] == OWN and row[sync.CREATED] == "2026-10-01"
    assert all(row[f] == "" for f in sync.WRITTEN_FIELDS)


def test_skill_present_at_last_sync_but_absent_from_sheet_is_excluded_not_added():
    entries, excluded = _plan([_row("a")], [_skill("a"), _skill("hidden")], [_skill("a"), _skill("hidden")])
    assert entries == [] and excluded == ["hidden"]


def test_description_change_requires_review_and_keeps_written_text():
    entries, _ = _plan([_row("a")], [_skill("a", "new")], [_skill("a", "old")])
    [entry] = entries
    assert entry["op"] == "update_description"
    assert entry["previous_description"] == "old" and entry["repo_description"] == "new"
    assert entry["row"][sync.DESC_EN] == "Does a thing." and entry["row"][sync.MODIFIED] == "2026-10-02"
    assert set(entry["needs_review"]) == set(sync.WRITTEN_FIELDS)


def test_rename_with_same_description_is_paired_and_needs_no_review():
    entries, _ = _plan([_row("old")], [_skill("new", "same")], [_skill("old", "same")])
    [entry] = entries
    assert entry["op"] == "rename" and entry["old_name"] == "old" and entry["reviewed"] is True
    assert entry["row"][sync.NAME] == "new" and entry["row"][sync.CREATED] == "2026-01-01"


def test_rename_with_changed_description_falls_back_to_remove_and_add():
    entries, _ = _plan([_row("old")], [_skill("new", "b")], [_skill("old", "a")])
    assert sorted(e["op"] for e in entries) == ["add", "remove"]


def test_other_repo_rows_are_never_touched():
    entries, _ = _plan([_row("theirs", OTHER)], [], [])
    assert entries == []


def test_apply_places_add_after_last_row_with_same_visibility():
    rows = [_row("a"), _row("b"), _row("x", OTHER)]
    add = {"op": "add", "name": "c", "row": _row("c")}
    out = sync.apply_plan(rows, [add])
    assert [r[sync.NAME] for r in out] == ["a", "b", "c", "x"]


def test_apply_rename_update_remove_keep_position():
    rows = [_row("a"), _row("b"), _row("c")]
    entries = [
        {"op": "rename", "name": "b2", "old_name": "b", "row": _row("b2")},
        {"op": "update_description", "name": "a", "row": _row("a", DESC_EN="Changed.")},
        {"op": "remove", "name": "c", "row": _row("c")},
    ]
    out = sync.apply_plan(rows, entries)
    assert [r[sync.NAME] for r in out] == ["a", "b2"]
    assert out[0][sync.DESC_EN] == "Changed."
    assert rows[0][sync.DESC_EN] == "Does a thing."  # input not mutated


def test_apply_rejects_stale_plan():
    with pytest.raises(SystemExit):
        sync.apply_plan([_row("a")], [{"op": "update_description", "name": "gone", "row": _row("gone")}])


def _entry(row: dict[str, str], op: str = "add") -> dict[str, object]:
    return {"op": op, "name": row[sync.NAME], "reviewed": True, "row": row}


def test_validate_accepts_complete_entry():
    assert sync.validate_entries([_entry(_row("a"))], ["유전체·생물정보"]) == []


def test_validate_flags_empty_unreviewed_and_unknown_category():
    entry = {**_entry(_row("a", DESC_KO="", CATEGORY="새 분야")), "reviewed": False}
    problems = "\n".join(sync.validate_entries([entry], ["유전체·생물정보"]))
    assert "reviewed=false" in problems and "설명(국문) is empty" in problems and "unknown 카테고리" in problems


def test_validate_rejects_visibility_owned_by_the_other_repo():
    problems = sync.validate_entries([_entry(_row("a", OTHER))], ["유전체·생물정보"])
    assert any("공개여부" in p for p in problems)


def test_validate_checks_language_of_each_column():
    entry = _entry(_row("a", DESC_EN="한글 설명", PROMPT_KO="English only"))
    problems = "\n".join(sync.validate_entries([entry], ["유전체·생물정보"]))
    assert "설명(영문) contains Hangul" in problems and "프롬프트(국문) has no Hangul" in problems


@pytest.mark.parametrize(
    "prompt",
    [
        "Analyse the file I uploaded.",
        "Cluster my data by pattern.",
        "Plot the previous results as a heatmap.",
        "업로드한 파일로 분석해주세요.",
        "이전 결과를 정리해주세요.",
        "제 데이터로 클러스터링해주세요.",
    ],
)
def test_prompt_lint_rejects_dependent_prompts(prompt: str):
    assert sync.prompt_problems(prompt)


@pytest.mark.parametrize(
    "prompt",
    [
        "Profile aspirin, imatinib and sorafenib for ADMET and flag anything with hERG risk.",
        "Combine three example single-cell objects into one and save it.",
        "예시 time series 데이터를 패턴별로 클러스터링해주세요.",
        "I want a one-page summary as a .hwpx file I can open in Hangul.",
    ],
)
def test_prompt_lint_accepts_stand_alone_prompts(prompt: str):
    assert sync.prompt_problems(prompt) == []


def test_rows_from_values_rejects_header_drift_and_pads_short_rows():
    with pytest.raises(SystemExit):
        sync.rows_from_values([["name", "category"]])
    rows = sync.rows_from_values([list(sync.HEADER), ["a", "cat"], [""]])
    assert rows == [dict(zip(sync.HEADER, ["a", "cat", *[""] * 7], strict=True))]


def test_parse_frontmatter_normalises_folded_description():
    text = "---\nname: x\ndescription: >\n  line one\n  line two\n---\nbody"
    skill = sync._skill_from_text("skills/x/SKILL.md", text)
    assert skill == sync.Skill(name="x", description="line one line two", path="skills/x/SKILL.md")


def test_load_env_file_parses_frontend_style_dotenv(tmp_path: Path):
    env_file = tmp_path / ".env.local"
    env_file.write_text(
        "# comment\nGOOGLE_SERVICE_ACCOUNT_EMAIL=sa@p.iam.gserviceaccount.com\n"
        "GOOGLE_PRIVATE_KEY=-----BEGIN\\nabc\\n-----END\n"
        'export QUOTED="a b"\nNOEQUALS\n',
        encoding="utf-8",
    )
    env = sync.load_env_file(env_file)
    assert env["GOOGLE_SERVICE_ACCOUNT_EMAIL"] == "sa@p.iam.gserviceaccount.com"
    assert env["GOOGLE_PRIVATE_KEY"] == "-----BEGIN\\nabc\\n-----END"
    assert env["QUOTED"] == "a b" and "NOEQUALS" not in env
    assert sync.load_env_file(tmp_path / "missing") == {}


def test_service_account_info_unescapes_key_and_requires_both_vars():
    info = sync.service_account_info({sync.SA_EMAIL_ENV: "sa@x", sync.SA_KEY_ENV: "-----BEGIN\\nabc\\n-----END"})
    assert info == {"client_email": "sa@x", "private_key": "-----BEGIN\nabc\n-----END", "token_uri": sync.TOKEN_URI}
    assert sync.service_account_info({}) is None
    with pytest.raises(SystemExit):
        sync.service_account_info({sync.SA_EMAIL_ENV: "sa@x"})
