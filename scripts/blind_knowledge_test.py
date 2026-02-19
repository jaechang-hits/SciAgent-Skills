#!/usr/bin/env python3
"""
Phase 2: Blind Knowledge Test for SciCraft skills.

Tests whether Claude already knows the core API/concepts for each skill
without reading the SKILL.md file. Skills where Claude scores >95% correct
are candidates for removal (they add context cost without adding knowledge).

Usage:
    python scripts/blind_knowledge_test.py --all
    python scripts/blind_knowledge_test.py --skill scanpy-scrna-seq
    python scripts/blind_knowledge_test.py --category genomics-bioinformatics
    python scripts/blind_knowledge_test.py --output results.csv

Requirements:
    pip install boto3 pyyaml python-dotenv

Environment (.env file):
    AWS_ACCESS_KEY_ID=...
    AWS_SECRET_ACCESS_KEY=...
    AWS_DEFAULT_REGION=us-east-1   # or your Bedrock region
    BEDROCK_MODEL_ID=us.anthropic.claude-sonnet-4-5   # model for blind answers
    BEDROCK_JUDGE_MODEL_ID=us.anthropic.claude-haiku-4-5-20251001  # model for judging

Scoring:
    >95% correct  → REMOVE candidate (Claude already knows it well)
    70-95%        → KEEP (skill adds value)
    <70%          → MUST KEEP (core skill value)
"""

import argparse
import csv
import json
import os
import re
import sys
import time
from pathlib import Path

try:
    import boto3
    import yaml
    from dotenv import load_dotenv
except ImportError as e:
    print(f"Missing dependency: {e}")
    print("Install with: pip install boto3 pyyaml python-dotenv")
    sys.exit(1)

REPO_ROOT = Path(__file__).parent.parent
REGISTRY_PATH = REPO_ROOT / "registry.yaml"

QUESTION_TEMPLATES = {
    "pipeline": [
        "What is the first step in the {name} pipeline and what does it produce?",
        "What file formats does {name} accept as input?",
        "What is the key function/command to run the main analysis in {name}?",
        "What does {name} output and how do you interpret the results?",
        "What is one critical parameter you must configure when running {name}?",
    ],
    "toolkit": [
        "What are the 3 most important modules or classes in the {name} library?",
        "How do you load or initialize data with {name}?",
        "What is the primary use case for {name} vs its closest alternative?",
        "Name one key function in {name} and describe its return value.",
        "Write the Python import statement that starts a typical {name} workflow.",
    ],
    "database": [
        "What is the main database that {name} accesses, and approximately how many records does it contain?",
        "How do you perform a basic search query using {name} in Python?",
        "What authentication is required for {name} and what are the rate limits?",
        "What data format does {name} return results in (JSON, DataFrame, etc.)?",
        "What is a specific endpoint URL or Python function call in {name} for retrieving data by ID?",
    ],
    "guide": [
        "What is the main decision framework described in {name}?",
        "What are the 3 most important best practices covered in {name}?",
        "What specific common pitfall does {name} warn against?",
        "What is the recommended step-by-step workflow outlined in {name}?",
        "What specific tools or resources does {name} recommend?",
    ],
}

JUDGE_PROMPT = """You are evaluating whether an AI correctly answered questions about a scientific tool WITHOUT having access to documentation.

Tool: {name} (sub_type: {sub_type})
Tool description: {description}

Questions and AI answers:
{qa_pairs}

Score each answer strictly:
- CORRECT (1.0): Answer is accurate AND specific to this exact tool (correct function names, parameter names, return types, database sizes, etc.)
- PARTIAL (0.5): Answer is partially correct, or correct but too vague/generic (could apply to multiple tools)
- INCORRECT (0.0): Answer is wrong, fabricated specific details, or essentially "I don't know"

Be STRICT: If the AI says something generic like "load data with load()" without the actual function name, score as PARTIAL.
If the AI invents plausible-sounding but wrong details, score as INCORRECT.

Return ONLY a JSON object:
{{"scores": [1.0, 0.5, 0.0, 1.0, 1.0], "total": 3.5, "max": 5, "percentage": 70.0, "notes": "one sentence explanation"}}"""


def load_registry():
    with open(REGISTRY_PATH) as f:
        data = yaml.safe_load(f)
    return data["entries"]


def load_env(env_path=None):
    """Load .env file from given path or search common locations."""
    if env_path:
        load_dotenv(env_path)
        return

    candidates = [
        REPO_ROOT / ".env",
        Path.home() / ".env",
        Path.home() / "work" / ".env",
        Path(".env"),
    ]
    for path in candidates:
        if path.exists():
            load_dotenv(path)
            print(f"Loaded .env from {path}")
            return

    # Fall through — may already be in environment
    print("No .env file found; using existing environment variables")


def make_bedrock_client():
    region = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")
    return boto3.client("bedrock-runtime", region_name=region)


def invoke_claude(client, model_id, prompt, max_tokens=1024):
    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": prompt}],
    }
    response = client.invoke_model(
        modelId=model_id,
        body=json.dumps(body),
        contentType="application/json",
        accept="application/json",
    )
    result = json.loads(response["body"].read())
    return result["content"][0]["text"]


def generate_questions(entry):
    sub_type = entry["sub_type"]
    templates = QUESTION_TEMPLATES.get(sub_type, QUESTION_TEMPLATES["toolkit"])
    return [t.format(name=entry["name"]) for t in templates]


def ask_blind(client, model_id, entry, questions):
    """Ask the model about the tool without any documentation."""
    prompt = (
        f"Answer these 5 questions about the scientific tool '{entry['name']}' "
        f"({entry['sub_type']}). Answer from your training knowledge — be as specific as "
        f"possible with exact function names, parameter names, and values.\n\n"
    )
    for i, q in enumerate(questions, 1):
        prompt += f"{i}. {q}\n"

    return invoke_claude(client, model_id, prompt, max_tokens=1200)


def judge_answers(client, judge_model_id, entry, questions, answers_text):
    """Use a fast model to score the answers."""
    qa_pairs = ""
    for i, q in enumerate(questions, 1):
        qa_pairs += f"Q{i}: {q}\n"
        # Try to extract the answer for question i
        pattern = rf"(?:^|\n){i}[.)]\s*(.*?)(?=\n\d+[.)]|\Z)"
        match = re.search(pattern, answers_text, re.DOTALL)
        answer = match.group(1).strip() if match else "(no answer found)"
        qa_pairs += f"A{i}: {answer[:300]}\n\n"

    prompt = JUDGE_PROMPT.format(
        name=entry["name"],
        sub_type=entry["sub_type"],
        description=entry["description"][:400],
        qa_pairs=qa_pairs,
    )

    response = invoke_claude(client, judge_model_id, prompt, max_tokens=256)
    match = re.search(r"\{[^{}]+\}", response, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    return {"scores": [], "total": 0, "max": 5, "percentage": 0.0, "notes": "parse error"}


def classify(percentage):
    if percentage > 95:
        return "REMOVE"
    elif percentage >= 70:
        return "KEEP"
    else:
        return "MUST_KEEP"


def test_skill(bedrock, answer_model, judge_model, entry, verbose=False):
    name = entry["name"]
    questions = generate_questions(entry)

    if verbose:
        print(f"\n  Questions for {name}:")
        for i, q in enumerate(questions, 1):
            print(f"    {i}. {q}")

    answers = ask_blind(bedrock, answer_model, entry, questions)
    time.sleep(0.3)

    result = judge_answers(bedrock, judge_model, entry, questions, answers)
    time.sleep(0.3)

    pct = result.get("percentage", 0.0)
    rec = classify(pct)

    if verbose:
        print(f"  Score: {result.get('total', 0):.1f}/{result.get('max', 5)} ({pct:.0f}%) → {rec}")
        print(f"  Notes: {result.get('notes', '')}")

    return {
        "name": name,
        "sub_type": entry["sub_type"],
        "category": entry["category"],
        "score": result.get("total", 0),
        "max": result.get("max", 5),
        "percentage": pct,
        "recommendation": rec,
        "notes": result.get("notes", ""),
    }


def main():
    parser = argparse.ArgumentParser(description="Blind knowledge test for SciCraft skills (AWS Bedrock)")
    parser.add_argument("--all", action="store_true", help="Test all skills")
    parser.add_argument("--skill", help="Test a specific skill by name")
    parser.add_argument("--category", help="Test all skills in a category")
    parser.add_argument("--output", default="blind_test_results.csv", help="Output CSV file")
    parser.add_argument("--env", help="Path to .env file")
    parser.add_argument(
        "--answer-model",
        default=None,
        help="Bedrock model ID for blind answers (default: BEDROCK_MODEL_ID env var or claude-sonnet-4-5)",
    )
    parser.add_argument(
        "--judge-model",
        default=None,
        help="Bedrock model ID for judging (default: BEDROCK_JUDGE_MODEL_ID env var or claude-haiku-4-5)",
    )
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    load_env(args.env)

    answer_model = (
        args.answer_model
        or os.environ.get("BEDROCK_MODEL_ID")
        or "us.anthropic.claude-sonnet-4-5-20250929-v1:0"
    )
    judge_model = (
        args.judge_model
        or os.environ.get("BEDROCK_JUDGE_MODEL_ID")
        or "us.anthropic.claude-sonnet-4-5-20250929-v1:0"
    )

    print(f"Answer model : {answer_model}")
    print(f"Judge model  : {judge_model}")

    bedrock = make_bedrock_client()
    entries = load_registry()

    # Filter
    if args.skill:
        entries = [e for e in entries if e["name"] == args.skill]
        if not entries:
            print(f"Skill '{args.skill}' not found in registry")
            sys.exit(1)
    elif args.category:
        entries = [e for e in entries if e["category"] == args.category]
        if not entries:
            print(f"No skills found for category '{args.category}'")
            sys.exit(1)
    elif not args.all:
        parser.print_help()
        sys.exit(0)

    print(f"\nTesting {len(entries)} skill(s)...\n")

    results = []
    for i, entry in enumerate(entries, 1):
        print(f"[{i:3d}/{len(entries)}] {entry['name']:<50s}", end="", flush=True)
        try:
            result = test_skill(bedrock, answer_model, judge_model, entry, verbose=args.verbose)
            results.append(result)
            marker = {"REMOVE": "✗", "KEEP": "~", "MUST_KEEP": "✓"}[result["recommendation"]]
            print(f"{result['percentage']:5.0f}%  {marker} {result['recommendation']}")
        except Exception as e:
            print(f" ERROR: {e}")
            results.append({
                "name": entry["name"],
                "sub_type": entry["sub_type"],
                "category": entry["category"],
                "score": -1, "max": 5, "percentage": -1,
                "recommendation": "ERROR", "notes": str(e),
            })

    # Save CSV
    output_path = Path(args.output)
    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["name", "sub_type", "category", "score", "max",
                        "percentage", "recommendation", "notes"],
        )
        writer.writeheader()
        writer.writerows(results)

    print(f"\nResults saved to {output_path}")

    # Summary
    remove_list = [r for r in results if r["recommendation"] == "REMOVE"]
    keep_list   = [r for r in results if r["recommendation"] == "KEEP"]
    must_list   = [r for r in results if r["recommendation"] == "MUST_KEEP"]
    err_list    = [r for r in results if r["recommendation"] == "ERROR"]

    print(f"\n{'='*60}")
    print(f"SUMMARY  ({len(results)} skills tested)")
    print(f"{'='*60}")
    print(f"  ✗ REMOVE candidates (>95%): {len(remove_list)}")
    print(f"  ~ KEEP          (70-95%):   {len(keep_list)}")
    print(f"  ✓ MUST KEEP      (<70%):    {len(must_list)}")
    if err_list:
        print(f"  ! ERRORS:                   {len(err_list)}")

    if remove_list:
        print(f"\nRemoval candidates:")
        for r in sorted(remove_list, key=lambda x: -x["percentage"]):
            print(f"  {r['name']:<50s} {r['percentage']:.0f}%")


if __name__ == "__main__":
    main()
