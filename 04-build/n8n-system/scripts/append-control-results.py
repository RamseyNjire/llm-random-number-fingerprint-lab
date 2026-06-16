#!/usr/bin/env python3
"""Append local RNG control rows to the random-number fingerprint sheet."""

import argparse
import csv
import json
import os
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List

ROOT = Path(__file__).resolve().parents[1]
TEMPLATES_DIR = ROOT / "workflows" / "templates"
DEFAULT_SHEET_ID = os.environ.get("RANDOM_NUMBER_FINGERPRINT_SHEET_ID", "")
DEFAULT_SERVICE_ACCOUNT = os.environ.get("GOOGLE_SERVICE_ACCOUNT_FILE", "")
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

PROMPT_TEXT = "Pick a random integer from 1 to 100. Reply with only the number."

CONTROLS = [
    {
        "case_id": "control_math_random_basic",
        "model_id": "control/math_random",
        "provider_route": "local/v8_math_random",
        "notes": "Local JavaScript Math.random control; not an OpenRouter call.",
    },
    {
        "case_id": "control_crypto_random_basic",
        "model_id": "control/crypto_random",
        "provider_route": "local/node_crypto_random",
        "notes": "Local Node crypto.randomInt control; not an OpenRouter call.",
    },
]


def parse_sheet_id(value: str) -> str:
    value = value.strip()
    if "/spreadsheets/d/" in value:
        return value.split("/spreadsheets/d/", 1)[1].split("/", 1)[0]
    return value


def read_headers() -> List[str]:
    path = TEMPLATES_DIR / "experiment-results-headers.csv"
    with path.open(newline="", encoding="utf-8") as f:
        return next(csv.reader(f))


def generate_js_numbers(repetitions: int) -> Dict[str, List[int]]:
    js = r"""
const crypto = require('node:crypto');
const repetitions = Number(process.argv[process.argv.length - 1]);
const out = {
  "control/math_random": Array.from({ length: repetitions }, () => Math.floor(Math.random() * 100) + 1),
  "control/crypto_random": Array.from({ length: repetitions }, () => crypto.randomInt(1, 101)),
};
process.stdout.write(JSON.stringify(out));
"""
    completed = subprocess.run(
        ["node", "-e", js, str(repetitions)],
        check=True,
        capture_output=True,
        text=True,
    )
    data = json.loads(completed.stdout)
    return {key: [int(value) for value in values] for key, values in data.items()}


def is_prime(n: int) -> bool:
    if n < 2:
        return False
    i = 2
    while i * i <= n:
        if n % i == 0:
            return False
        i += 1
    return True


def bool_text(value: bool) -> str:
    return "TRUE" if value else "FALSE"


def build_result_rows(run_id: str, repetitions: int, headers: Iterable[str]) -> List[List[object]]:
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    generated = generate_js_numbers(repetitions)
    rows: List[List[object]] = []
    counter = 0

    for control in CONTROLS:
        numbers = generated[control["model_id"]]
        for index, parsed in enumerate(numbers, start=1):
            counter += 1
            row = {
                "run_id": run_id,
                "sample_id": f"{run_id}_{counter:06d}",
                "measured_at": now,
                "case_id": control["case_id"],
                "model_id": control["model_id"],
                "provider_label": "Control",
                "prompt_id": "basic_1_100",
                "prompt_text": PROMPT_TEXT,
                "condition_label": "control_rng",
                "temperature": "",
                "top_p": "",
                "max_tokens": "",
                "repetition_index": index,
                "seed_policy": "internal_rng",
                "seed_value": "",
                "response_text": str(parsed),
                "response_value": str(parsed),
                "response_type": "integer_1_100",
                "valid_response": "TRUE",
                "response_parse_error": "",
                "parsed_number": parsed,
                "valid_number": "TRUE",
                "parse_error": "",
                "is_odd": bool_text(parsed % 2 != 0),
                "is_even": bool_text(parsed % 2 == 0),
                "is_prime": bool_text(is_prime(parsed)),
                "is_edge": bool_text(parsed <= 10 or parsed >= 91),
                "is_round": bool_text(parsed % 10 == 0 or parsed % 5 == 0),
                "contains_7": bool_text("7" in str(parsed)),
                "ends_with_7": bool_text(str(parsed).endswith("7")),
                "distance_from_50": abs(parsed - 50),
                "latency_ms": 0,
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
                "cost_estimate_usd": 0,
                "error_status": "",
                "error_message": "",
                "notes": control["notes"],
                "requested_provider_order": "",
                "requested_allow_fallbacks": "",
                "requested_require_parameters": "",
                "requested_provider_ignore": "",
                "reasoning_effort": "",
                "returned_model": control["model_id"],
                "provider_route": control["provider_route"],
                "finish_reason": "control",
                "native_finish_reason": "local",
                "reasoning_tokens": 0,
            }
            rows.append([row.get(header, "") for header in headers])

    return rows


def append_rows(service, spreadsheet_id: str, rows: List[List[object]]) -> None:
    service.spreadsheets().values().append(
        spreadsheetId=spreadsheet_id,
        range="'ExperimentResults'!A1",
        valueInputOption="RAW",
        insertDataOption="INSERT_ROWS",
        body={"values": rows},
    ).execute()


def summarize(rows: List[List[object]], headers: List[str]) -> Dict[str, object]:
    model_idx = headers.index("model_id")
    parsed_idx = headers.index("parsed_number")
    summary = {}
    for model_id in sorted({str(row[model_idx]) for row in rows}):
        values = [int(row[parsed_idx]) for row in rows if row[model_idx] == model_id]
        counts = Counter(values)
        summary[model_id] = {
            "samples": len(values),
            "top_numbers": counts.most_common(5),
            "odd_ratio": round(sum(v % 2 != 0 for v in values) / len(values), 3),
            "contains_7_ratio": round(sum("7" in str(v) for v in values) / len(values), 3),
        }
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Append local RNG controls to ExperimentResults")
    parser.add_argument("--sheet", default=DEFAULT_SHEET_ID, help="Google Sheet ID or URL")
    parser.add_argument("--repetitions", type=int, default=25, help="Samples per control")
    parser.add_argument("--run-id", default="", help="Optional run id override")
    parser.add_argument("--dry-run", action="store_true", help="Print rows summary without appending")
    parser.add_argument(
        "--service-account",
        default=str(DEFAULT_SERVICE_ACCOUNT),
        help="Path to service account JSON key",
    )
    args = parser.parse_args()

    if args.repetitions < 1:
        raise ValueError("--repetitions must be at least 1")
    if not args.sheet:
        raise ValueError("Missing --sheet or RANDOM_NUMBER_FINGERPRINT_SHEET_ID")
    if not args.dry_run and not args.service_account:
        raise ValueError("Missing --service-account or GOOGLE_SERVICE_ACCOUNT_FILE")

    headers = read_headers()
    run_id = args.run_id or "control_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    rows = build_result_rows(run_id, args.repetitions, headers)

    if not args.dry_run:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build

        service_account_path = Path(args.service_account)
        if not service_account_path.exists():
            raise FileNotFoundError(f"Service account file not found: {service_account_path}")

        credentials = service_account.Credentials.from_service_account_file(
            str(service_account_path),
            scopes=SCOPES,
        )
        service = build("sheets", "v4", credentials=credentials)
        append_rows(service, parse_sheet_id(args.sheet), rows)

    print(json.dumps({
        "status": "dry_run" if args.dry_run else "appended",
        "run_id": run_id,
        "rows": len(rows),
        "summary": summarize(rows, headers),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
