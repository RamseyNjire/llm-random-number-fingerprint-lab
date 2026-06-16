#!/usr/bin/env python3
"""Enable/disable prompt-battery rows in the live ExperimentCases sheet."""

import argparse
import json
import os
import warnings
from pathlib import Path

warnings.filterwarnings("ignore", category=FutureWarning)

from google.oauth2 import service_account
from googleapiclient.discovery import build

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SHEET_ID = os.environ.get("RANDOM_NUMBER_FINGERPRINT_SHEET_ID", "")
DEFAULT_SERVICE_ACCOUNT = os.environ.get("GOOGLE_SERVICE_ACCOUNT_FILE", "")
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

DEFAULT_SMOKE_MODELS = [
    "openai/gpt-5.5",
    "anthropic/claude-sonnet-4.6",
]
DEFAULT_SMOKE_PROMPTS = [
    "battery_number_1_100",
    "battery_color",
]


def parse_sheet_id(value: str) -> str:
    value = value.strip()
    if "/spreadsheets/d/" in value:
        return value.split("/spreadsheets/d/", 1)[1].split("/", 1)[0]
    return value


def split_csv(value: str):
    return [item.strip() for item in value.split(",") if item.strip()]


def main() -> int:
    parser = argparse.ArgumentParser(description="Configure prompt-battery enabled rows")
    parser.add_argument("--sheet", default=DEFAULT_SHEET_ID, help="Google Sheet ID or URL")
    parser.add_argument("--mode", choices=["disabled", "smoke", "full"], default="disabled")
    parser.add_argument("--smoke-models", default=",".join(DEFAULT_SMOKE_MODELS))
    parser.add_argument("--smoke-prompts", default=",".join(DEFAULT_SMOKE_PROMPTS))
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--service-account",
        default=str(DEFAULT_SERVICE_ACCOUNT),
        help="Path to service account JSON key",
    )
    args = parser.parse_args()

    if not args.sheet:
        raise ValueError("Missing --sheet or RANDOM_NUMBER_FINGERPRINT_SHEET_ID")
    if not args.service_account:
        raise ValueError("Missing --service-account or GOOGLE_SERVICE_ACCOUNT_FILE")

    credentials = service_account.Credentials.from_service_account_file(
        str(Path(args.service_account)),
        scopes=SCOPES,
    )
    service = build("sheets", "v4", credentials=credentials)
    spreadsheet_id = parse_sheet_id(args.sheet)

    values = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range="'ExperimentCases'!A:S",
    ).execute().get("values", [])
    if not values:
        raise ValueError("ExperimentCases has no rows")

    headers = values[0]
    rows = values[1:]
    header_index = {header: i for i, header in enumerate(headers)}
    required = ["enabled", "condition_label", "model_id", "prompt_id", "repetitions"]
    missing = [header for header in required if header not in header_index]
    if missing:
        raise ValueError(f"Missing ExperimentCases columns: {', '.join(missing)}")

    smoke_models = set(split_csv(args.smoke_models))
    smoke_prompts = set(split_csv(args.smoke_prompts))
    enabled_rows = 0
    enabled_calls = 0
    battery_rows = 0

    normalized_rows = []
    for raw in rows:
        row = list(raw) + [""] * (len(headers) - len(raw))
        is_battery = row[header_index["condition_label"]] == "prompt_battery"
        enable = False

        if is_battery:
            battery_rows += 1
            if args.mode == "full":
                enable = True
            elif args.mode == "smoke":
                enable = (
                    row[header_index["model_id"]] in smoke_models
                    and row[header_index["prompt_id"]] in smoke_prompts
                )

        row[header_index["enabled"]] = "TRUE" if enable else "FALSE"
        if enable:
            enabled_rows += 1
            try:
                enabled_calls += int(float(row[header_index["repetitions"]] or 0))
            except ValueError:
                pass
        normalized_rows.append(row[:len(headers)])

    if not args.dry_run:
        service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range="'ExperimentCases'!A1",
            valueInputOption="RAW",
            body={"values": [headers] + normalized_rows},
        ).execute()

    print(json.dumps({
        "status": "dry_run" if args.dry_run else "updated",
        "mode": args.mode,
        "battery_rows": battery_rows,
        "enabled_rows": enabled_rows,
        "estimated_calls": enabled_calls,
        "smoke_models": sorted(smoke_models),
        "smoke_prompts": sorted(smoke_prompts),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
