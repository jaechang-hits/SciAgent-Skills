#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6", "google-auth>=2", "requests>=2"]
# ///
"""Sync this repo's skills into the HyperLab skill catalog Google Sheet.

The repo is the source of truth for skill names and descriptions; the sheet is
a mirror that additionally carries hand-written columns the repo does not have
(Korean description, example prompts, category label). Sync is one-way
(repo -> sheet) and every sync adds a new tab, a full snapshot named by its
KST timestamp. Existing tabs are never edited.

Two steps, with an agent filling the hand-written columns in between:

    uv run scripts/sync_skill_catalog.py plan   # diff repo vs latest tab -> plan file
    (fill the empty / needs_review fields in .skill-catalog-plan.json)
    uv run scripts/sync_skill_catalog.py push   # validate, then add the new tab

`plan` compares the working tree with the repo state at the last sync (the
commit recorded on the latest tab, see `METADATA_KEY`) to find added, renamed,
removed and re-described skills. Skills that existed at the last sync but are
absent from the sheet are deliberately excluded from the catalog and ignored.

Without Google credentials, use the CSV path instead (same as the frontend
i18n flow): download the latest tab as CSV, `plan --from-csv <file>
--source-tab <tab title>`, then `push --csv <out>` and import the CSV as a new
tab by hand.

See AGENTS.md "스킬 카탈로그 시트 동기화" for the authoring rules.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING
from zoneinfo import ZoneInfo

import yaml

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence

# ---- Repo-specific settings (the only block that differs between the two skill repos) ----
REPO_ID = "SciAgent-Skills"
ALLOWED_VISIBILITY = ("공개",)
DEFAULT_VISIBILITY = "공개"

# ---- Shared settings ----
SPREADSHEET_ID = "1JrIOLKwTwrcWFbkgc-xh0aL9IeUO8avZXqYsOOGx1P4"
SCOPES = ("https://www.googleapis.com/auth/spreadsheets",)
SHEETS_API = "https://sheets.googleapis.com/v4/spreadsheets"
HEADER = (
    "이름",
    "카테고리(분야)",
    "공개여부",
    "설명(영문)",
    "설명(국문)",
    "프롬프트(영문)",
    "프롬프트(국문)",
    "생성일자",
    "최종 수정일자",
)
NAME, CATEGORY, VISIBILITY, DESC_EN, DESC_KO, PROMPT_EN, PROMPT_KO, CREATED, MODIFIED = HEADER
WRITTEN_FIELDS = (DESC_EN, DESC_KO, PROMPT_EN, PROMPT_KO)
HIDDEN_VISIBILITY = "미노출"
TAB_TITLE_FORMAT = "%Y-%m-%d %H-%M-%S"
KST = ZoneInfo("Asia/Seoul")
METADATA_KEY = f"skill-catalog-sync:{REPO_ID}"
REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = "skills"
DEFAULT_PLAN = REPO_ROOT / ".skill-catalog-plan.json"

# A first prompt must run on its own: no uploads, no earlier turns, no prior results.
_PROMPT_DEPENDENCY_PATTERNS = (
    r"\bupload",
    r"\battach",
    r"\bmy (?:own )?(?:data|file|files|dataset|results?)\b",
    r"\b(?:this|these|that|those|the) (?:file|files|dataset|data I)\b",
    r"\b(?:above|previous|previously|earlier|last) (?:result|results|analysis|step|output|turn)\b",
    r"\bfrom before\b",
    r"업로드",
    r"첨부",
    r"올린",
    r"(?:위|이전|앞|방금)(?:의)? ?(?:결과|분석|단계|출력)",
    r"(?:제|내|우리) (?:데이터|파일)",
    r"이 (?:데이터|파일)",
)
_HANGUL = re.compile(r"[가-힣]")


@dataclass(frozen=True)
class Skill:
    """A skill as declared by its SKILL.md frontmatter."""

    name: str
    description: str
    path: str  # repo-relative SKILL.md path


# ---------------------------------------------------------------- repo side


def parse_frontmatter(text: str) -> dict[str, object]:
    """Returns the YAML frontmatter of a SKILL.md, or {} when absent."""
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    loaded = yaml.safe_load(text[3:end])
    return loaded if isinstance(loaded, dict) else {}


def _skill_from_text(path: str, text: str) -> Skill | None:
    meta = parse_frontmatter(text)
    name = meta.get("name")
    if not isinstance(name, str) or not name.strip():
        return None
    description = " ".join(str(meta.get("description") or "").split())
    return Skill(name=name.strip(), description=description, path=path)


def _index(skills: Iterable[Skill]) -> dict[str, Skill]:
    out: dict[str, Skill] = {}
    for skill in skills:
        if skill.name in out:
            raise SystemExit(f"duplicate skill name {skill.name!r}: {out[skill.name].path} and {skill.path}")
        out[skill.name] = skill
    return out


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(REPO_ROOT), *args], check=True, capture_output=True, text=True
    ).stdout


def skills_in_worktree() -> dict[str, Skill]:
    """Every SKILL.md under skills/ in the working tree, keyed by frontmatter name."""
    found = []
    for skill_md in sorted((REPO_ROOT / SKILLS_DIR).rglob("SKILL.md")):
        rel = skill_md.relative_to(REPO_ROOT).as_posix()
        skill = _skill_from_text(rel, skill_md.read_text(encoding="utf-8"))
        if skill is not None:
            found.append(skill)
    return _index(found)


def skills_at_rev(rev: str) -> dict[str, Skill]:
    """Every SKILL.md under skills/ at a git revision, keyed by frontmatter name."""
    found = []
    for rel in _git("ls-tree", "-r", "--name-only", rev, "--", SKILLS_DIR).splitlines():
        if rel.endswith("/SKILL.md"):
            skill = _skill_from_text(rel, _git("show", f"{rev}:{rel}"))
            if skill is not None:
                found.append(skill)
    return _index(found)


def git_dates(skill_md_path: str) -> tuple[str, str]:
    """(first, last) commit dates of the skill directory; today when uncommitted."""
    skill_dir = str(Path(skill_md_path).parent)
    dates = _git("log", "--format=%cs", "--", skill_dir).split()
    today = dt.datetime.now(KST).date().isoformat()
    return (dates[-1], dates[0]) if dates else (today, today)


def resolve_rev(rev: str) -> str | None:
    """Full SHA for a revision, or None when it is not in this clone."""
    try:
        return _git("rev-parse", "--verify", "--quiet", f"{rev}^{{commit}}").strip() or None
    except subprocess.CalledProcessError:
        return None


def rev_before(when: dt.datetime) -> str | None:
    """Last commit on HEAD at or before `when`."""
    return _git("rev-list", "-1", f"--before={when.isoformat()}", "HEAD").strip() or None


def skills_dirty() -> bool:
    return bool(_git("status", "--porcelain", "--", SKILLS_DIR).strip())


# ---------------------------------------------------------------- plan logic (pure)


def build_plan(
    rows: Sequence[dict[str, str]],
    now: dict[str, Skill],
    base: dict[str, Skill],
    dates: dict[str, tuple[str, str]],
) -> tuple[list[dict[str, object]], list[str]]:
    """Diffs the repo against the sheet rows this repo owns.

    Args:
        rows: Rows of the latest tab, keyed by HEADER.
        now: Skills in the working tree.
        base: Skills at the last sync. A skill in `base` but not in the sheet
            was excluded from the catalog on purpose and is left alone.
        dates: (created, modified) per skill name in `now`.

    Returns:
        (entries, excluded). Each entry is one op: add | rename |
        update_description | remove, with the proposed full row.
    """
    by_name = {r[NAME]: r for r in rows}
    added = [n for n in now if n not in by_name and n not in base]
    removed = [n for n in base if n not in now and n in by_name]
    excluded = sorted(n for n in now if n not in by_name and n in base)

    renames: list[tuple[str, str]] = []
    for old in list(removed):
        match = next((new for new in added if now[new].description == base[old].description), None)
        if match is not None:
            renames.append((old, match))
            removed.remove(old)
            added.remove(match)

    entries: list[dict[str, object]] = []
    for name in added:
        created, modified = dates[name]
        row = dict.fromkeys(HEADER, "")
        row.update({NAME: name, VISIBILITY: DEFAULT_VISIBILITY, CREATED: created, MODIFIED: modified})
        entries.append(_entry("add", now[name], row, needs_review=[CATEGORY, *WRITTEN_FIELDS]))
    for old, new in renames:
        row = {**by_name[old], NAME: new, MODIFIED: dates[new][1]}
        entries.append(_entry("rename", now[new], row, needs_review=[], old_name=old))
    for name in now:
        if name in by_name and name in base and now[name].description != base[name].description:
            row = {**by_name[name], MODIFIED: dates[name][1]}
            entries.append(
                _entry(
                    "update_description",
                    now[name],
                    row,
                    needs_review=list(WRITTEN_FIELDS),
                    previous_description=base[name].description,
                )
            )
    for name in removed:
        entries.append(_entry("remove", base[name], dict(by_name[name]), needs_review=[]))
    return entries, excluded


def _entry(op: str, skill: Skill, row: dict[str, str], *, needs_review: list[str], **extra: str) -> dict[str, object]:
    entry: dict[str, object] = {"op": op, "name": row[NAME], **extra, "skill_path": skill.path}
    entry["repo_description"] = skill.description
    entry["needs_review"] = needs_review
    entry["reviewed"] = not needs_review
    entry["row"] = row
    return entry


def validate_entries(entries: Sequence[dict[str, object]], categories: Iterable[str]) -> list[str]:
    """Returns human-readable problems; empty when the plan can be pushed."""
    problems: list[str] = []
    known = set(categories)
    for entry in entries:
        op, name, row = entry["op"], entry["name"], _row(entry)
        where = f"[{op} {name}]"
        if op == "remove":
            continue
        if not entry.get("reviewed"):
            problems.append(f"{where} reviewed=false: check {entry.get('needs_review')} and set reviewed=true")
        # Internal agent-behaviour skills (미노출) are never invoked by a user, so they carry no prompt.
        optional = (PROMPT_EN, PROMPT_KO) if row.get(VISIBILITY) == HIDDEN_VISIBILITY else ()
        for field in HEADER:
            if field not in optional and not row.get(field, "").strip():
                problems.append(f"{where} {field} is empty")
        if row.get(VISIBILITY) not in ALLOWED_VISIBILITY:
            problems.append(f"{where} 공개여부 must be one of {ALLOWED_VISIBILITY}")
        if row.get(CATEGORY) and row[CATEGORY] not in known:
            problems.append(f"{where} unknown 카테고리 {row[CATEGORY]!r}; pick one of {sorted(known)}")
        for field in (DESC_EN, PROMPT_EN):
            if _HANGUL.search(row.get(field, "")):
                problems.append(f"{where} {field} contains Hangul")
        for field in (DESC_KO, PROMPT_KO):
            if row.get(field) and not _HANGUL.search(row[field]):
                problems.append(f"{where} {field} has no Hangul")
        problems.extend(f"{where} {p}" for p in prompt_problems(row.get(PROMPT_EN, "") + "\n" + row.get(PROMPT_KO, "")))
    return problems


def prompt_problems(prompt: str) -> list[str]:
    """Flags phrasing that makes a prompt depend on uploads or earlier turns."""
    return [
        f"prompt is not stand-alone (matches {pattern!r})"
        for pattern in _PROMPT_DEPENDENCY_PATTERNS
        if re.search(pattern, prompt, flags=re.IGNORECASE)
    ]


def apply_plan(rows: Sequence[dict[str, str]], entries: Sequence[dict[str, object]]) -> list[dict[str, str]]:
    """Returns the new tab's rows: the old rows with every op applied."""
    out = [dict(r) for r in rows]
    for entry in entries:
        op, row = entry["op"], _row(entry)
        names = [r[NAME] for r in out]
        if op == "remove":
            out = [r for r in out if r[NAME] != entry["name"]]
        elif op in ("rename", "update_description"):
            target = str(entry.get("old_name") or entry["name"])
            if target not in names:
                raise SystemExit(f"[{op} {entry['name']}] {target!r} is not in the latest tab; re-run plan")
            out[names.index(target)] = dict(row)
        elif op == "add":
            if row[NAME] in names:
                raise SystemExit(f"[add {row[NAME]}] already in the latest tab; re-run plan")
            same = [i for i, r in enumerate(out) if r[VISIBILITY] == row[VISIBILITY]]
            out.insert(same[-1] + 1 if same else len(out), dict(row))
        else:
            raise SystemExit(f"unknown op {op!r}")
    final = [r[NAME] for r in out]
    duplicates = sorted({n for n in final if final.count(n) > 1})
    if duplicates:
        raise SystemExit(f"duplicate names after applying the plan: {duplicates}")
    return out


def _row(entry: dict[str, object]) -> dict[str, str]:
    row = entry["row"]
    assert isinstance(row, dict)
    return {str(k): str(v) for k, v in row.items()}


# ---------------------------------------------------------------- sheet side


def rows_from_values(values: Sequence[Sequence[str]]) -> list[dict[str, str]]:
    """Maps raw grid values to HEADER-keyed rows; fails loudly on a header change."""
    if not values or tuple(c.strip() for c in values[0][: len(HEADER)]) != HEADER:
        raise SystemExit(f"unexpected sheet header {values[0] if values else []}; expected {list(HEADER)}")
    rows = []
    for raw in values[1:]:
        padded = [*raw, *[""] * (len(HEADER) - len(raw))][: len(HEADER)]
        if padded[0].strip():
            rows.append(dict(zip(HEADER, padded, strict=True)))
    return rows


def parse_tab_time(title: str) -> dt.datetime | None:
    try:
        return dt.datetime.strptime(title, TAB_TITLE_FORMAT).replace(tzinfo=KST)
    except ValueError:
        return None


class SheetClient:
    """Minimal Sheets REST client on Application Default Credentials."""

    def __init__(self) -> None:
        import google.auth
        from google.auth.transport.requests import AuthorizedSession

        credentials, _ = google.auth.default(scopes=list(SCOPES))
        self._session = AuthorizedSession(credentials)

    def _call(self, method: str, url: str, **kwargs: object) -> dict[str, object]:
        response = self._session.request(method, url, **kwargs)
        if response.status_code >= 400:
            raise SystemExit(f"Sheets API {response.status_code}: {response.text[:500]}")
        return response.json()

    def tabs(self) -> list[dict[str, object]]:
        fields = "sheets(properties(sheetId,title,index),developerMetadata(metadataId,metadataKey,metadataValue))"
        data = self._call("GET", f"{SHEETS_API}/{SPREADSHEET_ID}", params={"fields": fields})
        return list(data.get("sheets", []))  # type: ignore[arg-type]

    def values(self, title: str) -> list[list[str]]:
        rng = f"'{title}'!A1:{chr(ord('A') + len(HEADER) - 1)}"
        data = self._call("GET", f"{SHEETS_API}/{SPREADSHEET_ID}/values/{rng}")
        return list(data.get("values", []))  # type: ignore[arg-type]

    def add_snapshot(self, source: dict[str, object], title: str, rows: Sequence[dict[str, str]], sha: str) -> None:
        """Duplicates `source` as a new first tab, then rewrites its values and sync metadata."""
        props = source["properties"]
        assert isinstance(props, dict)
        reply = self._call(
            "POST",
            f"{SHEETS_API}/{SPREADSHEET_ID}:batchUpdate",
            json={
                "requests": [
                    {
                        "duplicateSheet": {
                            "sourceSheetId": props["sheetId"],
                            "insertSheetIndex": 0,
                            "newSheetName": title,
                        }
                    }
                ]
            },
        )
        new_id = reply["replies"][0]["duplicateSheet"]["properties"]["sheetId"]  # type: ignore[index]
        self._call("POST", f"{SHEETS_API}/{SPREADSHEET_ID}/values/'{title}'!A1:Z:clear", json={})
        grid = [list(HEADER), *[[r[h] for h in HEADER] for r in rows]]
        self._call(
            "PUT",
            f"{SHEETS_API}/{SPREADSHEET_ID}/values/'{title}'!A1",
            params={"valueInputOption": "RAW"},
            json={"values": grid},
        )
        self._set_metadata(new_id, source, sha)

    def _set_metadata(self, sheet_id: object, source: dict[str, object], sha: str) -> None:
        # Carry the other repo's sync commit forward and set ours. duplicateSheet
        # may or may not copy metadata, so update what exists and create the rest.
        wanted = {str(m["metadataKey"]): str(m["metadataValue"]) for m in _metadata(source)}
        wanted[METADATA_KEY] = sha
        copied = next((t for t in self.tabs() if t["properties"]["sheetId"] == sheet_id), {})  # type: ignore[index]
        existing = {str(m["metadataKey"]): m["metadataId"] for m in _metadata(copied)}
        requests = []
        for key, value in wanted.items():
            if key in existing:
                requests.append(
                    {
                        "updateDeveloperMetadata": {
                            "dataFilters": [{"developerMetadataLookup": {"metadataId": existing[key]}}],
                            "developerMetadata": {"metadataValue": value},
                            "fields": "metadataValue",
                        }
                    }
                )
            else:
                requests.append(
                    {
                        "createDeveloperMetadata": {
                            "developerMetadata": {
                                "metadataKey": key,
                                "metadataValue": value,
                                "location": {"sheetId": sheet_id},
                                "visibility": "DOCUMENT",
                            }
                        }
                    }
                )
        self._call("POST", f"{SHEETS_API}/{SPREADSHEET_ID}:batchUpdate", json={"requests": requests})


def _metadata(tab: dict[str, object]) -> list[dict[str, object]]:
    return [m for m in tab.get("developerMetadata", []) if str(m.get("metadataKey", "")).startswith("skill-catalog-sync:")]  # type: ignore[union-attr]


def latest_tab(tabs: Sequence[dict[str, object]]) -> dict[str, object]:
    """The newest timestamp-titled tab; the first tab when none is timestamp-titled."""
    timed = [(parse_tab_time(t["properties"]["title"]), t) for t in tabs]  # type: ignore[index]
    timed = [(when, t) for when, t in timed if when is not None]
    if timed:
        return max(timed, key=lambda pair: pair[0])[1]
    return min(tabs, key=lambda t: t["properties"].get("index", 0))  # type: ignore[union-attr]


# ---------------------------------------------------------------- commands


def _read_csv(path: Path) -> list[list[str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return [list(r) for r in csv.reader(handle)]


def _write_csv(path: Path, rows: Sequence[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(HEADER)
        writer.writerows([r[h] for h in HEADER] for r in rows)


def _load_source(args: argparse.Namespace) -> tuple[str, list[dict[str, str]], str | None, SheetClient | None, dict[str, object] | None]:
    """(tab title, rows, recorded sync sha, client, tab) from the sheet or a CSV export."""
    if args.from_csv:
        if not args.source_tab:
            raise SystemExit("--from-csv needs --source-tab <title of the tab the CSV came from>")
        return args.source_tab, rows_from_values(_read_csv(Path(args.from_csv))), None, None, None
    client = SheetClient()
    tab = latest_tab(client.tabs())
    title = str(tab["properties"]["title"])  # type: ignore[index]
    recorded = next((str(m["metadataValue"]) for m in _metadata(tab) if m["metadataKey"] == METADATA_KEY), None)
    return title, rows_from_values(client.values(title)), recorded, client, tab


def _baseline(args: argparse.Namespace, title: str, recorded: str | None) -> str:
    if args.baseline:
        sha = resolve_rev(args.baseline)
        if sha is None:
            raise SystemExit(f"--baseline {args.baseline!r} is not a commit in this clone")
        return sha
    if recorded and (sha := resolve_rev(recorded)):
        return sha
    when = parse_tab_time(title)
    sha = rev_before(when) if when else None
    if sha is None:
        raise SystemExit(f"cannot infer the last-sync commit from tab {title!r}; pass --baseline <rev>")
    print(f"warning: no recorded sync commit on tab {title!r}; using {sha[:10]} (last commit before the tab time). "
          "Pass --baseline to override.", file=sys.stderr)
    return sha


def cmd_plan(args: argparse.Namespace) -> int:
    title, rows, recorded, _, _ = _load_source(args)
    if skills_dirty():
        print("warning: skills/ has uncommitted changes; commit before push", file=sys.stderr)
    base_sha = _baseline(args, title, recorded)
    now = skills_in_worktree()
    entries, excluded = build_plan(rows, now, skills_at_rev(base_sha), {n: git_dates(s.path) for n, s in now.items()})
    plan = {
        "repo": REPO_ID,
        "source_tab": title,
        "baseline": base_sha,
        "head": resolve_rev("HEAD"),
        "categories": sorted({r[CATEGORY] for r in rows if r[CATEGORY]}),
        "allowed_visibility": list(ALLOWED_VISIBILITY),
        "excluded_from_catalog": excluded,
        "entries": entries,
    }
    Path(args.plan).write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    counts = {op: sum(e["op"] == op for e in entries) for op in ("add", "rename", "update_description", "remove")}
    print(f"source tab {title!r}, baseline {base_sha[:10]}: {counts}")
    for entry in entries:
        print(f"  {entry['op']:<19} {entry.get('old_name', '') and str(entry['old_name']) + ' -> '}{entry['name']}")
    print(f"plan written to {args.plan}" if entries else "nothing to sync")
    return 0


def cmd_push(args: argparse.Namespace) -> int:
    plan = json.loads(Path(args.plan).read_text(encoding="utf-8"))
    if plan.get("repo") != REPO_ID:
        raise SystemExit(f"plan is for {plan.get('repo')!r}, this repo is {REPO_ID!r}")
    entries = plan["entries"]
    if not entries:
        print("nothing to sync")
        return 0
    if skills_dirty() and not args.allow_dirty:
        raise SystemExit("skills/ has uncommitted changes; commit first so the recorded sync commit is accurate")
    if plan.get("head") != resolve_rev("HEAD"):
        raise SystemExit("HEAD moved since plan; re-run plan")
    title, rows, _, client, tab = _load_source(args)
    if title != plan["source_tab"]:
        raise SystemExit(f"latest tab is now {title!r}, plan was made from {plan['source_tab']!r}; re-run plan")
    problems = validate_entries(entries, plan["categories"])
    if problems:
        print("plan is not ready:", *problems, sep="\n  ", file=sys.stderr)
        return 1
    new_rows = apply_plan(rows, entries)
    new_title = dt.datetime.now(KST).strftime(TAB_TITLE_FORMAT)
    if args.csv:
        _write_csv(Path(args.csv), new_rows)
        print(f"wrote {len(new_rows)} rows to {args.csv}; import it as a new tab named {new_title!r}")
    if args.dry_run or client is None:
        print(f"dry run: {len(rows)} -> {len(new_rows)} rows, no tab created")
        return 0
    assert tab is not None
    client.add_snapshot(tab, new_title, new_rows, str(plan["head"]))
    print(f"created tab {new_title!r} ({len(rows)} -> {len(new_rows)} rows)")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("plan", "push"):
        p = sub.add_parser(name)
        p.add_argument("--plan", default=str(DEFAULT_PLAN), help="plan file path")
        p.add_argument("--from-csv", default=None, help="read the latest tab from a CSV export instead of the API")
        p.add_argument("--source-tab", default=None, help="title of the tab the CSV was exported from")
    plan_parser, push_parser = sub.choices["plan"], sub.choices["push"]
    plan_parser.add_argument("--baseline", default=None, help="git rev the latest tab was synced from")
    push_parser.add_argument("--dry-run", action="store_true", help="validate and diff only")
    push_parser.add_argument("--csv", default=None, help="also write the new tab to this CSV")
    push_parser.add_argument("--allow-dirty", action="store_true", help="push with uncommitted skills/ changes")
    args = parser.parse_args(argv)
    return cmd_plan(args) if args.command == "plan" else cmd_push(args)


if __name__ == "__main__":
    sys.exit(main())
