#!/usr/bin/env python3
"""Lint a SciAgent-Skills `description` field.

Used both by `scaffold.py` (programmatic check) and as a standalone CLI for
authors who want to test a description before scaffolding.

Rules enforced (mirrors CLAUDE.md Step 5 "Description writing rules"):

1. Length: hard ceiling 1024 chars (also enforced by tests/test_skill_quality.py).
2. First-120-char keyword carrier: the first word must NOT be a stop verb
   (`Use`, `A`, `An`, `The`, `Query`, `Fetch`, `Run`). Leading with the tool
   or domain name is the goal.
3. No promotional adjectives (`powerful`, `comprehensive`, `state-of-the-art`,
   `cutting-edge`). These waste tokens and add no discovery signal.
4. Description must not start with `>` (YAML block scalar) — keep it inline
   for grep/search consistency.

Usage:
    # CLI form
    python validate_description.py "MyTool short-form description..."

    # Importable
    from validate_description import check
    errors = check(description_text)

Exit codes (CLI):
    0  description passes
    1  one or more rule violations (printed to stderr)
"""

from __future__ import annotations

import re
import sys

MAX_LEN = 1024
STOP_VERBS = {"use", "a", "an", "the", "query", "fetch", "run"}
PROMO_WORDS = {
    "powerful",
    "comprehensive",
    "state-of-the-art",
    "cutting-edge",
    "world-class",
    "best-in-class",
    "industry-leading",
}


def first_word(text: str) -> str:
    text = text.lstrip().lstrip('"').lstrip("'")
    match = re.match(r"[A-Za-z][A-Za-z0-9-]*", text)
    return match.group(0).lower() if match else ""


def check(description: str) -> list[str]:
    errors: list[str] = []
    description = description.strip()

    if not description:
        errors.append("empty description")
        return errors

    if len(description) > MAX_LEN:
        errors.append(f"length {len(description)} exceeds {MAX_LEN}")

    if description.startswith(">"):
        errors.append("must not start with YAML block scalar '>' — keep inline")

    fw = first_word(description)
    if fw in STOP_VERBS:
        errors.append(
            f"first word '{fw}' is a stop verb. "
            "Lead with the tool name or domain (e.g., 'PyDESeq2 ...', not 'Use PyDESeq2 to ...')"
        )

    lowered = description.lower()
    for word in PROMO_WORDS:
        if re.search(rf"\b{re.escape(word)}\b", lowered):
            errors.append(
                f"promotional word '{word}' adds no discovery signal — remove it"
            )

    return errors


def main() -> None:
    if len(sys.argv) != 2:
        print(
            "Usage: validate_description.py \"<description>\"",
            file=sys.stderr,
        )
        sys.exit(2)

    errors = check(sys.argv[1])
    if errors:
        for e in errors:
            print(f"FAIL: {e}", file=sys.stderr)
        sys.exit(1)

    print("OK")


if __name__ == "__main__":
    main()
