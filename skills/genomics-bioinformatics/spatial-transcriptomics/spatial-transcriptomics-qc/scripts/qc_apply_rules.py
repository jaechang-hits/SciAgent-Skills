#!/usr/bin/env python3
"""Preview or apply one explicit spatial-QC filtering rule set.

Recommendation rows are descriptive only. A caller must name the exact
``rule_set_id`` to evaluate. Applying the mask additionally requires a D2
approval record whose digest matches the rules and AND/OR logic exactly.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd


NUMERIC_OPERATORS = {"lt", "le", "gt", "ge", "outside", "inside"}
BOOLEAN_OPERATORS = {"true", "false"}
MISSING_OPERATORS = {"is_na", "not_na"}
REQUIRED_RULE_COLUMNS = {
    "rule_set_id", "rule_id", "metric", "operator", "threshold",
    "upper_threshold",
}


def _to_nullable_bool(series: pd.Series) -> pd.Series:
    """Parse Boolean values without interpreting missing values as False."""
    normalized = series.astype("string").str.strip().str.lower()
    mapping = {
        "true": True, "t": True, "1": True, "yes": True,
        "false": False, "f": False, "0": False, "no": False,
    }
    unknown = normalized.dropna()[~normalized.dropna().isin(mapping)]
    if not unknown.empty:
        raise ValueError(f"non-boolean values: {sorted(unknown.unique())[:5]}")
    return normalized.map(mapping).astype("boolean")


def apply_rule(metrics: pd.DataFrame, rule: pd.Series) -> pd.Series:
    """Return removal matches. Missing values match only explicit NA rules."""
    column = str(rule["metric"])
    operator = str(rule["operator"]).strip().lower()
    rule_id = rule.get("rule_id", "<unknown>")
    if column not in metrics:
        raise KeyError(f"rule {rule_id}: missing metric column {column!r}")
    raw = metrics[column]
    if operator in MISSING_OPERATORS:
        return raw.isna() if operator == "is_na" else raw.notna()
    if operator in BOOLEAN_OPERATORS:
        values = _to_nullable_bool(raw)
        return values.eq(operator == "true").fillna(False).astype(bool)
    if operator not in NUMERIC_OPERATORS:
        raise ValueError(f"rule {rule_id}: unsupported operator {operator!r}")
    values = pd.to_numeric(raw, errors="coerce")
    lower = float(rule["threshold"])
    if operator == "lt":
        result = values < lower
    elif operator == "le":
        result = values <= lower
    elif operator == "gt":
        result = values > lower
    elif operator == "ge":
        result = values >= lower
    else:
        upper = float(rule["upper_threshold"])
        if lower > upper:
            raise ValueError(f"rule {rule_id}: lower threshold exceeds upper")
        inside = values.between(lower, upper, inclusive="both")
        # pandas.Series.between() returns False for NA. Negating that Boolean
        # would therefore turn missing values into outside matches. Missing
        # values are removable only through an explicit is_na rule.
        result = (~inside & values.notna()) if operator == "outside" else inside
    return result.fillna(False).astype(bool)


def select_rule_set(rules: pd.DataFrame, rule_set_id: str) -> pd.DataFrame:
    missing = REQUIRED_RULE_COLUMNS.difference(rules.columns)
    if missing:
        raise ValueError(f"rules file missing columns: {sorted(missing)}")
    selected = rules[rules["rule_set_id"].astype(str) == str(rule_set_id)].copy()
    if selected.empty:
        raise ValueError(f"rule_set_id {rule_set_id!r} was not found")
    if selected["rule_id"].astype(str).duplicated().any():
        raise ValueError("selected rule set contains duplicate rule_id values")
    return selected


def rule_set_digest(rules: pd.DataFrame, logic: str) -> str:
    """Fingerprint the exact approved rule content and combination logic."""
    columns = ["rule_id", "metric", "operator", "threshold", "upper_threshold"]
    normalized = []
    for row in rules[columns].sort_values("rule_id", kind="stable").itertuples(index=False):
        normalized.append([None if pd.isna(value) else str(value) for value in row])
    payload = {"logic": logic.upper(), "rules": normalized}
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def validate_approval_record(record: dict, rule_set_id: str, logic: str,
                             digest: str) -> None:
    expected = {
        "approved": True,
        "rule_set_id": str(rule_set_id),
        "logic": logic.upper(),
        "rule_set_digest": digest,
    }
    mismatches = [key for key, value in expected.items() if record.get(key) != value]
    if mismatches:
        raise ValueError(
            "D2 approval does not match the final rule set: " + ", ".join(mismatches)
        )


def calculate_matches(metrics: pd.DataFrame, rules: pd.DataFrame,
                      logic: str) -> tuple[pd.DataFrame, list[str]]:
    out = metrics.copy()
    match_columns: list[str] = []
    for _, rule in rules.iterrows():
        name = f"rule__{rule['rule_id']}"
        out[name] = apply_rule(out, rule)
        match_columns.append(name)
    out["selected_filter_match"] = (
        out[match_columns].all(axis=1)
        if logic.upper() == "AND"
        else out[match_columns].any(axis=1)
    )
    return out, match_columns


def impact_table(metrics: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    rows = []
    for name in columns:
        count = int(metrics[name].sum())
        rows.append({
            "result": name, "count": count, "total": len(metrics),
            "percent": 100 * count / len(metrics) if len(metrics) else 0.0,
        })
    return pd.DataFrame(rows)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--metrics", required=True)
    parser.add_argument("--rules", required=True)
    parser.add_argument("--rule-set-id", required=True)
    parser.add_argument("--logic", choices=["AND", "OR"], required=True)
    parser.add_argument("--mode", choices=["preview", "apply"], default="preview")
    parser.add_argument("--approval-record", help="D2 JSON required in apply mode")
    parser.add_argument("--id-column", default="observation_id")
    parser.add_argument("--group-column")
    parser.add_argument("--output-prefix", default="qc_recommendation")
    args = parser.parse_args(argv)

    metrics = pd.read_csv(args.metrics, sep="\t", dtype={args.id_column: str})
    rules = pd.read_csv(args.rules, sep="\t")
    if args.id_column not in metrics or metrics[args.id_column].duplicated().any():
        raise ValueError("ID column is missing or contains duplicates")
    selected = select_rule_set(rules, args.rule_set_id)
    digest = rule_set_digest(selected, args.logic)
    if args.mode == "apply":
        if not args.approval_record:
            raise ValueError("apply mode requires --approval-record from D2")
        record = json.loads(Path(args.approval_record).read_text(encoding="utf-8"))
        validate_approval_record(record, args.rule_set_id, args.logic, digest)

    matched, individual = calculate_matches(metrics, selected, args.logic)
    result_columns = individual + ["selected_filter_match"]
    prefix = Path(args.output_prefix)
    matched.to_csv(prefix.with_name(prefix.name + "_matches.tsv"), sep="\t", index=False)
    selected.to_csv(prefix.with_name(prefix.name + "_selected_rules.tsv"), sep="\t", index=False)
    impact_table(matched, result_columns).to_csv(
        prefix.with_name(prefix.name + "_impact_overall.tsv"), sep="\t", index=False)
    if args.group_column:
        if args.group_column not in matched:
            raise KeyError(f"missing group column {args.group_column!r}")
        grouped = []
        for group, frame in matched.groupby(args.group_column, dropna=False):
            table = impact_table(frame, result_columns)
            table.insert(0, args.group_column, group)
            grouped.append(table)
        pd.concat(grouped, ignore_index=True).to_csv(
            prefix.with_name(prefix.name + "_impact_by_group.tsv"), sep="\t", index=False)
    manifest = {
        "mode": args.mode,
        "rule_set_id": str(args.rule_set_id),
        "logic": args.logic,
        "rule_set_digest": digest,
        "approved_for_filtering": args.mode == "apply",
        "n_rules": len(selected),
        "n_observations": len(matched),
        "n_filter_matches": int(matched["selected_filter_match"].sum()),
    }
    prefix.with_name(prefix.name + "_rule_set.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
