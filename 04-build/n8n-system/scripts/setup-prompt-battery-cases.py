#!/usr/bin/env python3
"""Add disabled prompt-battery cases to the ExperimentCases template."""

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CASES_PATH = ROOT / "workflows" / "templates" / "experiment-cases-template.csv"

PROMPTS = [
    (
        "battery_number_1_100",
        "Pick a random integer from 1 to 100. Reply with only the number.",
        64,
    ),
    (
        "battery_first_number_1_100",
        "Say the first number from 1 to 100 that comes to mind. Reply with only the number.",
        64,
    ),
    (
        "battery_prime_under_100",
        "Pick a random prime number under 100. Reply with only the number.",
        64,
    ),
    (
        "battery_letter_a_z",
        "Pick a random uppercase letter from A to Z. Reply with only the letter.",
        16,
    ),
    (
        "battery_option_abcd",
        "Choose one option from A, B, C, or D at random. Reply with only the letter.",
        16,
    ),
    (
        "battery_color",
        "Pick a random color. Reply with only the color name.",
        32,
    ),
    (
        "battery_city",
        "Pick a random city in the world. Reply with only the city name.",
        32,
    ),
    (
        "battery_object",
        "Pick a random everyday object. Reply with only the object name.",
        32,
    ),
    (
        "battery_year_1900_2099",
        "Pick a random year from 1900 to 2099. Reply with only the year.",
        32,
    ),
    (
        "battery_first_name",
        "Make up a random first name. Reply with only the name.",
        32,
    ),
]

MODEL_IDS = [
    "openai/gpt-5.5",
    "openai/gpt-5.4-mini",
    "anthropic/claude-sonnet-4.6",
    "anthropic/claude-haiku-4.5",
    "google/gemini-3.5-flash",
    "google/gemini-3.1-flash-lite",
    "x-ai/grok-4.3",
    "mistralai/mistral-large-2512",
    "deepseek/deepseek-chat-v3.1",
    "qwen/qwen3.6-flash",
    "qwen/qwen3-max",
    "meta-llama/llama-4-maverick",
]


def slug(value: str) -> str:
    return (
        value.replace("/", "_")
        .replace("-", "_")
        .replace(".", "")
        .replace(":", "")
        .replace("__", "_")
        .strip("_")
    )


def main() -> int:
    with CASES_PATH.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fieldnames = reader.fieldnames or []

    base_rows = [row for row in rows if row.get("condition_label") != "prompt_battery"]
    for row in base_rows:
        row["enabled"] = "FALSE"

    by_model = {}
    for row in base_rows:
        model_id = row.get("model_id", "")
        if model_id and model_id not in by_model and not model_id.startswith("control/"):
            by_model[model_id] = row

    missing = [model_id for model_id in MODEL_IDS if model_id not in by_model]
    if missing:
        raise ValueError(f"Missing base model rows for: {', '.join(missing)}")

    added = []
    for model_id in MODEL_IDS:
        base = by_model[model_id]
        for prompt_id, prompt_text, max_tokens in PROMPTS:
            row = dict(base)
            row.update({
                "enabled": "FALSE",
                "case_id": f"battery_{slug(model_id)}_{prompt_id}",
                "prompt_id": prompt_id,
                "prompt_text": prompt_text,
                "condition_label": "prompt_battery",
                "max_tokens": str(max(int(base.get("max_tokens") or 16), max_tokens)),
                "repetitions": "25",
                "seed_policy": "none",
                "seed_start": "",
                "notes": "Prompt battery; enable selected rows for the next fingerprint run",
            })
            added.append(row)

    with CASES_PATH.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(base_rows + added)

    print(json.dumps({
        "status": "ok",
        "base_rows": len(base_rows),
        "prompt_battery_rows": len(added),
        "models": len(MODEL_IDS),
        "prompts": len(PROMPTS),
        "enabled_rows": 0,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
