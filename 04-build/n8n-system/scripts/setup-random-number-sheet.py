#!/usr/bin/env python3
"""Create/update random-number fingerprint tabs + starter rows in Google Sheets."""

import argparse
import csv
import json
import os
from pathlib import Path
from typing import List

from google.oauth2 import service_account
from googleapiclient.discovery import build

ROOT = Path(__file__).resolve().parents[1]
TEMPLATES_DIR = ROOT / "workflows" / "templates"
DEFAULT_SHEET_ID = os.environ.get("RANDOM_NUMBER_FINGERPRINT_SHEET_ID", "")
DEFAULT_SERVICE_ACCOUNT = os.environ.get("GOOGLE_SERVICE_ACCOUNT_FILE", "")
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


def parse_sheet_id(value: str) -> str:
    value = value.strip()
    if "/spreadsheets/d/" in value:
        return value.split("/spreadsheets/d/", 1)[1].split("/", 1)[0]
    return value


def read_csv_rows(path: Path) -> List[List[str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.reader(f))


def cell(value: str) -> dict:
    return {"userEnteredValue": {"stringValue": value}}


def ensure_sheets(service, spreadsheet_id: str, needed_titles: List[str]) -> dict:
    meta = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    existing = {s["properties"]["title"]: s for s in meta.get("sheets", [])}

    requests = []
    for title in needed_titles:
        if title not in existing:
            requests.append({"addSheet": {"properties": {"title": title}}})

    if requests:
        service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={"requests": requests},
        ).execute()
        meta = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
        existing = {s["properties"]["title"]: s for s in meta.get("sheets", [])}

    return existing


def delete_empty_default_sheet(service, spreadsheet_id: str, sheets_by_title: dict) -> None:
    default = sheets_by_title.get("Sheet1")
    if not default:
        return

    values = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range="'Sheet1'!A1:Z100",
    ).execute().get("values", [])

    if values:
        return

    service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={
            "requests": [
                {
                    "deleteSheet": {
                        "sheetId": default["properties"]["sheetId"],
                    }
                }
            ]
        },
    ).execute()


def clear_and_write(service, spreadsheet_id: str, title: str, rows: List[List[str]]) -> None:
    service.spreadsheets().values().clear(
        spreadsheetId=spreadsheet_id,
        range=f"'{title}'",
        body={},
    ).execute()

    service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range=f"'{title}'!A1",
        valueInputOption="RAW",
        body={"values": rows},
    ).execute()


def style_sheet(service, spreadsheet_id: str, title: str, column_count: int) -> None:
    meta = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    sheet = next((s for s in meta.get("sheets", []) if s["properties"]["title"] == title), None)
    if not sheet:
        raise ValueError(f"Missing sheet after creation: {title}")

    sheet_id = sheet["properties"]["sheetId"]
    requests = [
        {
            "updateSheetProperties": {
                "properties": {
                    "sheetId": sheet_id,
                    "gridProperties": {"frozenRowCount": 1},
                },
                "fields": "gridProperties.frozenRowCount",
            }
        },
        {
            "repeatCell": {
                "range": {
                    "sheetId": sheet_id,
                    "startRowIndex": 0,
                    "endRowIndex": 1,
                    "startColumnIndex": 0,
                    "endColumnIndex": column_count,
                },
                "cell": {
                    "userEnteredFormat": {
                        "backgroundColorStyle": {
                            "rgbColor": {"red": 0.10, "green": 0.33, "blue": 0.42}
                        },
                        "textFormat": {
                            "bold": True,
                            "foregroundColorStyle": {
                                "rgbColor": {"red": 1, "green": 1, "blue": 1}
                            },
                        },
                    }
                },
                "fields": "userEnteredFormat(backgroundColorStyle,textFormat)",
            }
        },
        {
            "setBasicFilter": {
                "filter": {
                    "range": {
                        "sheetId": sheet_id,
                        "startRowIndex": 0,
                        "startColumnIndex": 0,
                        "endColumnIndex": column_count,
                    }
                }
            }
        },
        {
            "autoResizeDimensions": {
                "dimensions": {
                    "sheetId": sheet_id,
                    "dimension": "COLUMNS",
                    "startIndex": 0,
                    "endIndex": column_count,
                }
            }
        },
    ]

    service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={"requests": requests},
    ).execute()


def main() -> int:
    parser = argparse.ArgumentParser(description="Setup random-number fingerprint Google Sheet tabs")
    parser.add_argument("--sheet", default=DEFAULT_SHEET_ID, help="Google Sheet ID or URL")
    parser.add_argument(
        "--cases-only",
        action="store_true",
        help="Update only ExperimentCases, preserving existing ExperimentResults rows",
    )
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

    sheet_id = parse_sheet_id(args.sheet)
    service_account_path = Path(args.service_account)
    if not service_account_path.exists():
        raise FileNotFoundError(f"Service account file not found: {service_account_path}")

    credentials = service_account.Credentials.from_service_account_file(
        str(service_account_path),
        scopes=SCOPES,
    )
    service = build("sheets", "v4", credentials=credentials)

    tab_map = {
        "ExperimentCases": TEMPLATES_DIR / "experiment-cases-template.csv",
        "ExperimentResults": TEMPLATES_DIR / "experiment-results-headers.csv",
    }
    if args.cases_only:
        tab_map = {"ExperimentCases": tab_map["ExperimentCases"]}

    sheets_by_title = ensure_sheets(service, sheet_id, list(tab_map.keys()))
    delete_empty_default_sheet(service, sheet_id, sheets_by_title)

    for tab, csv_path in tab_map.items():
        rows = read_csv_rows(csv_path)
        clear_and_write(service, sheet_id, tab, rows)
        style_sheet(service, sheet_id, tab, len(rows[0]))

    print(json.dumps({
        "status": "ok",
        "sheet_id": sheet_id,
        "tabs": list(tab_map.keys()),
        "service_account_email": credentials.service_account_email,
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
