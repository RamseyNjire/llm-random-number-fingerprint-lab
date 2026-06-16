#!/usr/bin/env python3
"""Build summary tables and charts for the random-number fingerprint sheet."""

import argparse
import math
import os
import statistics
import warnings
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

warnings.filterwarnings("ignore", category=FutureWarning)

from google.oauth2 import service_account
from googleapiclient.discovery import build

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SHEET_ID = os.environ.get("RANDOM_NUMBER_FINGERPRINT_SHEET_ID", "")
DEFAULT_SERVICE_ACCOUNT = os.environ.get("GOOGLE_SERVICE_ACCOUNT_FILE", "")
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

ANALYSIS_SHEETS = [
    "Analysis_ReadMe",
    "Analysis_ModelSummary",
    "Analysis_NumberHistogram",
    "Analysis_ModelNumberHeatmap",
    "Analysis_ModelDistributions",
    "Analysis_FamilyFavorites",
    "Analysis_RunSummary",
    "Analysis_BatterySummary",
    "Analysis_BatteryTopResponses",
    "Analysis_BatteryFingerprint",
    "Analysis_BatteryHeatmap",
    "Analysis_BatteryCharts",
    "Analysis_Charts",
]

MAX_UNIFORM_ENTROPY = math.log2(100)
UNIFORM_1_100_STDDEV = math.sqrt((100**2 - 1) / 12)


def parse_sheet_id(value: str) -> str:
    value = value.strip()
    if "/spreadsheets/d/" in value:
        return value.split("/spreadsheets/d/", 1)[1].split("/", 1)[0]
    return value


def safe_float(value) -> float:
    try:
        if value in ("", None):
            return 0.0
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def safe_int(value):
    try:
        if value in ("", None):
            return None
        return int(float(value))
    except (TypeError, ValueError):
        return None


def pct(numerator: float, denominator: float) -> float:
    return numerator / denominator if denominator else 0.0


def entropy(values: Iterable[int]) -> float:
    values = list(values)
    if not values:
        return 0.0
    counts = Counter(values)
    total = len(values)
    return -sum((count / total) * math.log2(count / total) for count in counts.values())


def is_prime(n: int) -> bool:
    if n < 2:
        return False
    i = 2
    while i * i <= n:
        if n % i == 0:
            return False
        i += 1
    return True


def top_text(counts: Counter, limit: int = 5) -> str:
    if not counts:
        return ""
    return ", ".join(f"{number} ({count})" for number, count in counts.most_common(limit))


def top_number(counts: Counter):
    return counts.most_common(1)[0][0] if counts else ""


def top_count(counts: Counter) -> int:
    return counts.most_common(1)[0][1] if counts else 0


def route_text(rows: List[dict]) -> str:
    routes = Counter(row.get("provider_route", "") for row in rows if row.get("provider_route", ""))
    return ", ".join(f"{route} ({count})" for route, count in routes.most_common())


def first_nonempty(rows: List[dict], field: str) -> str:
    for row in rows:
        value = str(row.get(field, "")).strip()
        if value:
            return value
    return ""


def model_label(model_id: str) -> str:
    return model_id.replace("anthropic/", "").replace("openai/", "").replace("google/", "")


def get_rows(service, spreadsheet_id: str) -> List[dict]:
    values = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range="'ExperimentResults'!A:ZZ",
    ).execute().get("values", [])
    if not values:
        return []

    headers = values[0]
    rows = []
    for raw in values[1:]:
        row = {header: raw[i] if i < len(raw) else "" for i, header in enumerate(headers)}
        row["parsed_int"] = safe_int(row.get("parsed_number"))
        row["valid_bool"] = str(row.get("valid_number", "")).strip().upper() == "TRUE"
        row["cost_float"] = safe_float(row.get("cost_estimate_usd"))
        row["latency_float"] = safe_float(row.get("latency_ms"))
        rows.append(row)
    return rows


def summarize_group(rows: List[dict], group_fields: Tuple[str, ...]) -> List[List[object]]:
    groups: Dict[Tuple[str, ...], List[dict]] = defaultdict(list)
    for row in rows:
        groups[tuple(row.get(field, "") for field in group_fields)].append(row)

    output = [[
        *group_fields,
        "total_rows",
        "valid_count",
        "invalid_count",
        "invalid_rate",
        "top_number",
        "top_number_count",
        "top_number_share",
        "top_5_numbers",
        "unique_numbers",
        "mean_number",
        "stddev_number",
        "stddev_vs_uniform",
        "entropy_bits",
        "entropy_vs_uniform",
        "odd_ratio",
        "prime_ratio",
        "contains_7_ratio",
        "ends_with_7_ratio",
        "edge_ratio",
        "round_ratio",
        "provider_routes",
        "total_cost_usd",
        "avg_latency_ms",
        "run_ids",
    ]]

    for key, group_rows in sorted(groups.items(), key=lambda item: item[0]):
        valid_numbers = [
            row["parsed_int"]
            for row in group_rows
            if row["valid_bool"] and row["parsed_int"] is not None
        ]
        counts = Counter(valid_numbers)
        valid_count = len(valid_numbers)
        invalid_count = len(group_rows) - valid_count
        total_cost = sum(row["cost_float"] for row in group_rows)
        latencies = [row["latency_float"] for row in group_rows if row["latency_float"]]
        run_ids = ", ".join(sorted({row.get("run_id", "") for row in group_rows if row.get("run_id", "")}))
        ent = entropy(valid_numbers)
        top = top_number(counts)
        top_n = top_count(counts)
        stddev = statistics.pstdev(valid_numbers) if len(valid_numbers) > 1 else 0

        output.append([
            *key,
            len(group_rows),
            valid_count,
            invalid_count,
            pct(invalid_count, len(group_rows)),
            top,
            top_n,
            pct(top_n, valid_count),
            top_text(counts, 5),
            len(counts),
            statistics.mean(valid_numbers) if valid_numbers else 0,
            stddev,
            pct(stddev, UNIFORM_1_100_STDDEV),
            ent,
            pct(ent, MAX_UNIFORM_ENTROPY),
            pct(sum(number % 2 != 0 for number in valid_numbers), valid_count),
            pct(sum(is_prime(number) for number in valid_numbers), valid_count),
            pct(sum("7" in str(number) for number in valid_numbers), valid_count),
            pct(sum(str(number).endswith("7") for number in valid_numbers), valid_count),
            pct(sum(number <= 10 or number >= 91 for number in valid_numbers), valid_count),
            pct(sum(number % 10 == 0 or number % 5 == 0 for number in valid_numbers), valid_count),
            route_text(group_rows),
            total_cost,
            statistics.mean(latencies) if latencies else 0,
            run_ids,
        ])

    return output


def build_model_summary(rows: List[dict]) -> List[List[object]]:
    return summarize_group(rows, ("provider_label", "model_id", "condition_label"))


def build_family_summary(rows: List[dict]) -> List[List[object]]:
    return summarize_group(rows, ("provider_label",))


def build_run_summary(rows: List[dict]) -> List[List[object]]:
    grouped: Dict[str, List[dict]] = defaultdict(list)
    for row in rows:
        grouped[row.get("run_id", "")].append(row)

    output = [[
        "run_id",
        "total_rows",
        "valid_count",
        "invalid_count",
        "invalid_rate",
        "model_count",
        "models",
        "started_at",
        "ended_at",
        "total_cost_usd",
        "top_5_numbers",
    ]]
    for run_id, group_rows in sorted(grouped.items()):
        valid_numbers = [
            row["parsed_int"]
            for row in group_rows
            if row["valid_bool"] and row["parsed_int"] is not None
        ]
        invalid_count = len(group_rows) - len(valid_numbers)
        measured = sorted(row.get("measured_at", "") for row in group_rows if row.get("measured_at", ""))
        models = sorted({row.get("model_id", "") for row in group_rows if row.get("model_id", "")})
        output.append([
            run_id,
            len(group_rows),
            len(valid_numbers),
            invalid_count,
            pct(invalid_count, len(group_rows)),
            len(models),
            ", ".join(models),
            measured[0] if measured else "",
            measured[-1] if measured else "",
            sum(row["cost_float"] for row in group_rows),
            top_text(Counter(valid_numbers), 5),
        ])
    return output


def build_number_histogram(rows: List[dict]) -> List[List[object]]:
    llm_numbers = [
        row["parsed_int"]
        for row in rows
        if row["valid_bool"] and row["parsed_int"] is not None and row.get("provider_label") != "Control"
    ]
    math_numbers = [
        row["parsed_int"]
        for row in rows
        if row["valid_bool"] and row["parsed_int"] is not None and row.get("model_id") == "control/math_random"
    ]
    crypto_numbers = [
        row["parsed_int"]
        for row in rows
        if row["valid_bool"] and row["parsed_int"] is not None and row.get("model_id") == "control/crypto_random"
    ]
    all_control_numbers = math_numbers + crypto_numbers
    counters = {
        "llm": Counter(llm_numbers),
        "math": Counter(math_numbers),
        "crypto": Counter(crypto_numbers),
        "control": Counter(all_control_numbers),
    }
    totals = {key: sum(counter.values()) for key, counter in counters.items()}

    output = [[
        "number",
        "llm_count",
        "llm_pct",
        "math_random_count",
        "math_random_pct",
        "crypto_random_count",
        "crypto_random_pct",
        "all_control_count",
        "all_control_pct",
        "uniform_expected_pct",
    ]]
    for number in range(1, 101):
        output.append([
            number,
            counters["llm"].get(number, 0),
            pct(counters["llm"].get(number, 0), totals["llm"]),
            counters["math"].get(number, 0),
            pct(counters["math"].get(number, 0), totals["math"]),
            counters["crypto"].get(number, 0),
            pct(counters["crypto"].get(number, 0), totals["crypto"]),
            counters["control"].get(number, 0),
            pct(counters["control"].get(number, 0), totals["control"]),
            0.01,
        ])
    return output


def build_heatmap(rows: List[dict]) -> List[List[object]]:
    groups: Dict[Tuple[str, str, str], List[int]] = defaultdict(list)
    for row in rows:
        if row["valid_bool"] and row["parsed_int"] is not None:
            key = (row.get("provider_label", ""), row.get("model_id", ""), row.get("condition_label", ""))
            groups[key].append(row["parsed_int"])

    output = [["provider_label", "model_id", "condition_label", "valid_count", *range(1, 101)]]
    for key, numbers in sorted(groups.items()):
        counts = Counter(numbers)
        output.append([*key, len(numbers), *[counts.get(number, 0) for number in range(1, 101)]])
    return output


def build_model_distributions(rows: List[dict]) -> List[List[object]]:
    groups: Dict[Tuple[str, str, str], List[int]] = defaultdict(list)
    for row in rows:
        if row["valid_bool"] and row["parsed_int"] is not None:
            key = (row.get("provider_label", ""), row.get("model_id", ""), row.get("condition_label", ""))
            groups[key].append(row["parsed_int"])

    keys = sorted(groups)
    headers = ["number", *[f"{provider} | {model} | {condition}" for provider, model, condition in keys]]
    output = [headers]
    for number in range(1, 101):
        row = [number]
        for key in keys:
            total = len(groups[key])
            count = Counter(groups[key]).get(number, 0)
            row.append(pct(count, total))
        output.append(row)
    return output


def build_charts_data(model_summary: List[List[object]], histogram: List[List[object]]) -> List[List[object]]:
    model_headers = model_summary[0]
    model_rows = model_summary[1:]
    idx = {header: i for i, header in enumerate(model_headers)}

    invalid_rows = sorted(
        model_rows,
        key=lambda row: (row[idx["invalid_rate"]], row[idx["invalid_count"]]),
        reverse=True,
    )[:25]
    entropy_rows = sorted(
        [row for row in model_rows if row[idx["valid_count"]] > 0],
        key=lambda row: row[idx["entropy_bits"]],
    )[:25]
    cost_rows = sorted(model_rows, key=lambda row: row[idx["total_cost_usd"]], reverse=True)[:25]
    top_share_rows = sorted(
        [row for row in model_rows if row[idx["valid_count"]] > 0 and row[idx["provider_label"]] != "Control"],
        key=lambda row: row[idx["top_number_share"]],
        reverse=True,
    )[:25]
    stddev_rows = sorted(
        [row for row in model_rows if row[idx["valid_count"]] > 0],
        key=lambda row: row[idx["stddev_number"]],
    )[:25]
    unique_rows = sorted(
        [row for row in model_rows if row[idx["valid_count"]] > 0],
        key=lambda row: row[idx["unique_numbers"]],
    )[:25]

    rows: List[List[object]] = []
    rows.append(["Global Number Distribution", "", "", "", "", "Top Invalid Rates", "", "", "", "Lowest Entropy", "", "", "", "Top Cost", "", "", "", "Top Number Share", "", "", "", "Lowest Std Dev", "", "", "", "Fewest Unique Numbers", "", ""])
    rows.append(["number", "llm_pct", "math_random_pct", "crypto_random_pct", "", "model", "provider", "invalid_rate", "", "model", "provider", "entropy_bits", "", "model", "provider", "cost_usd", "", "model", "provider", "top_number_share", "", "model", "provider", "stddev_number", "", "model", "provider", "unique_numbers"])
    for i in range(100):
        hist_row = histogram[i + 1]
        invalid = invalid_rows[i] if i < len(invalid_rows) else None
        ent = entropy_rows[i] if i < len(entropy_rows) else None
        cost = cost_rows[i] if i < len(cost_rows) else None
        top_share = top_share_rows[i] if i < len(top_share_rows) else None
        stddev = stddev_rows[i] if i < len(stddev_rows) else None
        unique = unique_rows[i] if i < len(unique_rows) else None
        rows.append([
            hist_row[0],
            hist_row[2],
            hist_row[4],
            hist_row[6],
            "",
            model_label(invalid[idx["model_id"]]) if invalid else "",
            invalid[idx["provider_label"]] if invalid else "",
            invalid[idx["invalid_rate"]] if invalid else "",
            "",
            model_label(ent[idx["model_id"]]) if ent else "",
            ent[idx["provider_label"]] if ent else "",
            ent[idx["entropy_bits"]] if ent else "",
            "",
            model_label(cost[idx["model_id"]]) if cost else "",
            cost[idx["provider_label"]] if cost else "",
            cost[idx["total_cost_usd"]] if cost else "",
            "",
            model_label(top_share[idx["model_id"]]) if top_share else "",
            top_share[idx["provider_label"]] if top_share else "",
            top_share[idx["top_number_share"]] if top_share else "",
            "",
            model_label(stddev[idx["model_id"]]) if stddev else "",
            stddev[idx["provider_label"]] if stddev else "",
            stddev[idx["stddev_number"]] if stddev else "",
            "",
            model_label(unique[idx["model_id"]]) if unique else "",
            unique[idx["provider_label"]] if unique else "",
            unique[idx["unique_numbers"]] if unique else "",
        ])
    return rows


def response_entropy(values: Iterable[str]) -> float:
    values = [value for value in values if value]
    if not values:
        return 0.0
    counts = Counter(values)
    total = len(values)
    return -sum((count / total) * math.log2(count / total) for count in counts.values())


def battery_rows(rows: List[dict]) -> List[dict]:
    return [row for row in rows if row.get("condition_label") == "prompt_battery"]


def build_battery_summary(rows: List[dict]) -> List[List[object]]:
    groups: Dict[Tuple[str, str, str, str], List[dict]] = defaultdict(list)
    for row in battery_rows(rows):
        key = (
            row.get("provider_label", ""),
            row.get("model_id", ""),
            row.get("prompt_id", ""),
            row.get("response_type", ""),
        )
        groups[key].append(row)

    output = [[
        "provider_label",
        "model_id",
        "prompt_id",
        "response_type",
        "total_rows",
        "valid_response_count",
        "invalid_response_count",
        "valid_response_rate",
        "top_response",
        "top_response_count",
        "top_response_share",
        "top_5_responses",
        "unique_responses",
        "response_entropy",
        "provider_routes",
        "total_cost_usd",
        "run_ids",
    ]]
    for key, group_rows in sorted(groups.items()):
        valid_values = [
            row.get("response_value", "")
            for row in group_rows
            if str(row.get("valid_response", "")).upper() == "TRUE" and row.get("response_value", "")
        ]
        counts = Counter(valid_values)
        top = counts.most_common(1)[0][0] if counts else ""
        top_n = counts.most_common(1)[0][1] if counts else 0
        valid_count = len(valid_values)
        invalid_count = len(group_rows) - valid_count
        output.append([
            *key,
            len(group_rows),
            valid_count,
            invalid_count,
            pct(valid_count, len(group_rows)),
            top,
            top_n,
            pct(top_n, valid_count),
            top_text(counts, 5),
            len(counts),
            response_entropy(valid_values),
            route_text(group_rows),
            sum(row["cost_float"] for row in group_rows),
            ", ".join(sorted({row.get("run_id", "") for row in group_rows if row.get("run_id", "")})),
        ])
    return output


def build_battery_top_responses(summary: List[List[object]]) -> List[List[object]]:
    headers = summary[0]
    idx = {header: i for i, header in enumerate(headers)}
    rows = [row for row in summary[1:] if row]
    prompts = sorted({row[idx["prompt_id"]] for row in rows})
    models = sorted({row[idx["model_id"]] for row in rows})
    by_key = {(row[idx["model_id"]], row[idx["prompt_id"]]): row for row in rows}
    output = [["prompt_id", *models]]
    for prompt_id in prompts:
        output.append([
            prompt_id,
            *[
                by_key.get((model_id, prompt_id), [""] * len(headers))[idx["top_5_responses"]]
                if (model_id, prompt_id) in by_key else ""
                for model_id in models
            ],
        ])
    return output


def build_battery_fingerprint(summary: List[List[object]]) -> List[List[object]]:
    headers = summary[0]
    idx = {header: i for i, header in enumerate(headers)}
    rows = [row for row in summary[1:] if row]
    prompts = sorted({row[idx["prompt_id"]] for row in rows})
    models = sorted({row[idx["model_id"]] for row in rows})
    by_key = {(row[idx["model_id"]], row[idx["prompt_id"]]): row for row in rows}
    output = [["model_id", "provider_label", *prompts]]
    provider_by_model = {row[idx["model_id"]]: row[idx["provider_label"]] for row in rows}
    for model_id in models:
        output.append([
            model_id,
            provider_by_model.get(model_id, ""),
            *[
                by_key[(model_id, prompt_id)][idx["top_response"]]
                if (model_id, prompt_id) in by_key else ""
                for prompt_id in prompts
            ],
        ])
    return output


def build_battery_heatmap(summary: List[List[object]]) -> List[List[object]]:
    headers = summary[0]
    idx = {header: i for i, header in enumerate(headers)}
    rows = [row for row in summary[1:] if row]
    prompts = sorted({row[idx["prompt_id"]] for row in rows})
    models = sorted({row[idx["model_id"]] for row in rows})
    by_key = {(row[idx["model_id"]], row[idx["prompt_id"]]): row for row in rows}
    output = [["model_id", "provider_label", *prompts]]
    provider_by_model = {row[idx["model_id"]]: row[idx["provider_label"]] for row in rows}
    for model_id in models:
        output.append([
            model_id,
            provider_by_model.get(model_id, ""),
            *[
                by_key[(model_id, prompt_id)][idx["top_response_share"]]
                if (model_id, prompt_id) in by_key else ""
                for prompt_id in prompts
            ],
        ])
    return output


def build_battery_chart_data(summary: List[List[object]]) -> List[List[object]]:
    headers = summary[0]
    idx = {header: i for i, header in enumerate(headers)}
    rows = [row for row in summary[1:] if row]
    rows = sorted(rows, key=lambda row: (row[idx["prompt_id"]], row[idx["provider_label"]], row[idx["model_id"]]))
    output = [[
        "model_prompt",
        "provider_label",
        "top_response_share",
        "response_entropy",
        "unique_responses",
        "valid_response_rate",
        "total_cost_usd",
    ]]
    for row in rows:
        output.append([
            f"{model_label(row[idx['model_id']])} | {row[idx['prompt_id']].replace('battery_', '')}",
            row[idx["provider_label"]],
            row[idx["top_response_share"]],
            row[idx["response_entropy"]],
            row[idx["unique_responses"]],
            row[idx["valid_response_rate"]],
            row[idx["total_cost_usd"]],
        ])
    return output


def build_readme() -> List[List[object]]:
    return [
        ["Section", "What to look at", "Why it matters"],
        [
            "Start here",
            "Analysis_ModelSummary",
            "Main fingerprint table. Sort by entropy_bits ascending, top_number_share descending, or provider_label.",
        ],
        [
            "Prompt battery setup",
            "PromptBatteryPlan, Analysis_BatterySummary, Analysis_BatteryTopResponses, Analysis_BatteryFingerprint, Analysis_BatteryHeatmap, Analysis_BatteryCharts",
            "The battery views compare model fingerprints across arbitrary choice prompts, not just random-number prompts.",
        ],
        [
            "Raw distribution",
            "Analysis_NumberHistogram",
            "Shows whether LLM picks spike around a few numbers while RNG controls stay broad.",
        ],
        [
            "Fingerprint view",
            "Analysis_ModelNumberHeatmap",
            "Each row is a model and each number 1-100 is a column. Dark red cells reveal favorite numbers.",
        ],
        [
            "Per-model distributions",
            "Analysis_ModelDistributions",
            "Each number is a row and each model is a percentage column, so you can compare individual LLMs against each other.",
        ],
        [
            "Family view",
            "Analysis_FamilyFavorites",
            "Good for spotting lab-level patterns, but treat it as exploratory because model counts differ by family.",
        ],
        [
            "Audit view",
            "Analysis_RunSummary",
            "Use this to separate baseline runs, repair runs, and control runs.",
        ],
        [
            "Current interesting signal",
            "The result is not just that LLMs are not random. The interesting part is that different model families collapse onto different favorite-number clusters.",
            "That is the seed of a fingerprinting thesis.",
        ],
        [
            "Current caveat",
            "Some repaired models include both failed baseline attempts and successful repair attempts in the raw summaries.",
            "For paper-grade claims, build a clean latest-good-run subset before quoting invalid rates.",
        ],
        [
            "Best next experiment",
            "Run a small fingerprint prompt battery across the same models: random integer, random word, pick a color, pick a letter, choose a date, choose a city, choose a password-like token, coin/die variants, and ambiguous preference prompts.",
            "A multi-prompt fingerprint is much harder to dismiss than one random-number prompt.",
        ],
        [
            "Second next experiment",
            "Repeat the same prompt battery at temperature 0, 0.7, 1.0, and 1.5 where supported.",
            "This separates model prior/preferences from sampling randomness.",
        ],
        [
            "Third next experiment",
            "Compare API vs ChatGPT/Claude/Gemini UI manually for a small subset.",
            "This tests whether product wrappers or hidden system prompts change the fingerprint.",
        ],
        [
            "Tab color legend",
            "Green = setup, blue = raw data, charcoal = readme, purple = model summaries, orange = number distribution, red = heatmaps/distributions, teal = family/run audit, gold = charts.",
            "This is just navigation sugar, but the sheet badly needed it.",
        ],
    ]


def recreate_analysis_sheets(service, spreadsheet_id: str, table_shapes: Dict[str, Tuple[int, int]]) -> Dict[str, int]:
    meta = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    existing = {sheet["properties"]["title"]: sheet["properties"]["sheetId"] for sheet in meta.get("sheets", [])}
    delete_requests = [
        {"deleteSheet": {"sheetId": sheet_id}}
        for title, sheet_id in existing.items()
        if title in ANALYSIS_SHEETS
    ]
    if delete_requests:
        service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={"requests": delete_requests},
        ).execute()

    add_requests = []
    for title in ANALYSIS_SHEETS:
        rows, cols = table_shapes[title]
        add_requests.append({
            "addSheet": {
                "properties": {
                    "title": title,
                    "gridProperties": {
                        "rowCount": max(rows + 20, 200),
                        "columnCount": max(cols + 10, 26),
                    },
                }
            }
        })
    service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body={"requests": add_requests}).execute()

    meta = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    return {sheet["properties"]["title"]: sheet["properties"]["sheetId"] for sheet in meta.get("sheets", [])}


def write_table(service, spreadsheet_id: str, title: str, rows: List[List[object]]) -> None:
    service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range=f"'{title}'!A1",
        valueInputOption="RAW",
        body={"values": rows},
    ).execute()


def style_tables(service, spreadsheet_id: str, sheets: Dict[str, int], tables: Dict[str, List[List[object]]]) -> None:
    requests = []
    header_color = {"red": 0.10, "green": 0.33, "blue": 0.42}
    for title, rows in tables.items():
        sheet_id = sheets[title]
        col_count = len(rows[0])
        row_count = len(rows)
        requests.extend([
            {
                "updateSheetProperties": {
                    "properties": {"sheetId": sheet_id, "gridProperties": {"frozenRowCount": 1}},
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
                        "endColumnIndex": col_count,
                    },
                    "cell": {
                        "userEnteredFormat": {
                            "backgroundColorStyle": {"rgbColor": header_color},
                            "textFormat": {
                                "bold": True,
                                "foregroundColorStyle": {"rgbColor": {"red": 1, "green": 1, "blue": 1}},
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
                            "endRowIndex": row_count,
                            "startColumnIndex": 0,
                            "endColumnIndex": col_count,
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
                        "endIndex": min(col_count, 40),
                    }
                }
            },
        ])

    heatmap_id = sheets["Analysis_ModelNumberHeatmap"]
    heatmap_rows = len(tables["Analysis_ModelNumberHeatmap"])
    model_distribution_id = sheets["Analysis_ModelDistributions"]
    model_distribution_rows = len(tables["Analysis_ModelDistributions"])
    model_distribution_cols = len(tables["Analysis_ModelDistributions"][0])
    battery_heatmap_id = sheets["Analysis_BatteryHeatmap"]
    battery_heatmap_rows = len(tables["Analysis_BatteryHeatmap"])
    battery_heatmap_cols = len(tables["Analysis_BatteryHeatmap"][0])
    requests.extend([
        {
            "updateDimensionProperties": {
                "range": {
                    "sheetId": heatmap_id,
                    "dimension": "COLUMNS",
                    "startIndex": 4,
                    "endIndex": 104,
                },
                "properties": {"pixelSize": 36},
                "fields": "pixelSize",
            }
        },
        {
            "addConditionalFormatRule": {
                "rule": {
                    "ranges": [{
                        "sheetId": heatmap_id,
                        "startRowIndex": 1,
                        "endRowIndex": heatmap_rows,
                        "startColumnIndex": 4,
                        "endColumnIndex": 104,
                    }],
                    "gradientRule": {
                        "minpoint": {
                            "type": "MIN",
                            "colorStyle": {"rgbColor": {"red": 1, "green": 1, "blue": 1}},
                        },
                        "midpoint": {
                            "type": "PERCENTILE",
                            "value": "50",
                            "colorStyle": {"rgbColor": {"red": 1, "green": 0.80, "blue": 0.74}},
                        },
                        "maxpoint": {
                            "type": "MAX",
                            "colorStyle": {"rgbColor": {"red": 0.75, "green": 0.08, "blue": 0.10}},
                        },
                    },
                },
                "index": 0,
            }
        },
        {
            "addConditionalFormatRule": {
                "rule": {
                    "ranges": [{
                        "sheetId": model_distribution_id,
                        "startRowIndex": 1,
                        "endRowIndex": model_distribution_rows,
                        "startColumnIndex": 1,
                        "endColumnIndex": model_distribution_cols,
                    }],
                    "gradientRule": {
                        "minpoint": {
                            "type": "MIN",
                            "colorStyle": {"rgbColor": {"red": 1, "green": 1, "blue": 1}},
                        },
                        "midpoint": {
                            "type": "PERCENTILE",
                            "value": "50",
                            "colorStyle": {"rgbColor": {"red": 1, "green": 0.86, "blue": 0.78}},
                        },
                        "maxpoint": {
                            "type": "MAX",
                            "colorStyle": {"rgbColor": {"red": 0.72, "green": 0.04, "blue": 0.08}},
                        },
                    },
                },
                "index": 0,
            }
        },
        {
            "addConditionalFormatRule": {
                "rule": {
                    "ranges": [{
                        "sheetId": battery_heatmap_id,
                        "startRowIndex": 1,
                        "endRowIndex": battery_heatmap_rows,
                        "startColumnIndex": 2,
                        "endColumnIndex": battery_heatmap_cols,
                    }],
                    "gradientRule": {
                        "minpoint": {
                            "type": "MIN",
                            "colorStyle": {"rgbColor": {"red": 1, "green": 1, "blue": 1}},
                        },
                        "midpoint": {
                            "type": "PERCENTILE",
                            "value": "50",
                            "colorStyle": {"rgbColor": {"red": 1, "green": 0.86, "blue": 0.78}},
                        },
                        "maxpoint": {
                            "type": "MAX",
                            "colorStyle": {"rgbColor": {"red": 0.72, "green": 0.04, "blue": 0.08}},
                        },
                    },
                },
                "index": 0,
            }
        },
    ])

    def add_metric_gradient(title: str, column_name: str, low_red: bool = False) -> None:
        headers = tables[title][0]
        if column_name not in headers:
            return
        col = headers.index(column_name)
        sheet_id = sheets[title]
        rows = len(tables[title])
        if low_red:
            min_color = {"red": 0.75, "green": 0.08, "blue": 0.10}
            max_color = {"red": 0.75, "green": 0.90, "blue": 0.65}
        else:
            min_color = {"red": 1, "green": 1, "blue": 1}
            max_color = {"red": 0.75, "green": 0.08, "blue": 0.10}
        requests.append({
            "addConditionalFormatRule": {
                "rule": {
                    "ranges": [{
                        "sheetId": sheet_id,
                        "startRowIndex": 1,
                        "endRowIndex": rows,
                        "startColumnIndex": col,
                        "endColumnIndex": col + 1,
                    }],
                    "gradientRule": {
                        "minpoint": {"type": "MIN", "colorStyle": {"rgbColor": min_color}},
                        "maxpoint": {"type": "MAX", "colorStyle": {"rgbColor": max_color}},
                    },
                },
                "index": 0,
            }
        })

    for sheet_title in ("Analysis_ModelSummary", "Analysis_FamilyFavorites"):
        add_metric_gradient(sheet_title, "invalid_rate")
        add_metric_gradient(sheet_title, "top_number_share")
        add_metric_gradient(sheet_title, "entropy_bits", low_red=True)
        add_metric_gradient(sheet_title, "stddev_number", low_red=True)
        add_metric_gradient(sheet_title, "unique_numbers", low_red=True)

    add_metric_gradient("Analysis_BatterySummary", "top_response_share")
    add_metric_gradient("Analysis_BatterySummary", "response_entropy", low_red=True)
    add_metric_gradient("Analysis_BatterySummary", "unique_responses", low_red=True)
    add_metric_gradient("Analysis_BatterySummary", "valid_response_rate", low_red=True)

    service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body={"requests": requests}).execute()


def color_tabs(service, spreadsheet_id: str) -> None:
    meta = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    sheets = {sheet["properties"]["title"]: sheet["properties"]["sheetId"] for sheet in meta.get("sheets", [])}
    tab_colors = {
        "ExperimentCases": {"red": 0.18, "green": 0.55, "blue": 0.34},
        "ExperimentResults": {"red": 0.13, "green": 0.38, "blue": 0.70},
        "PromptBatteryPlan": {"red": 0.22, "green": 0.60, "blue": 0.48},
        "Analysis_ReadMe": {"red": 0.20, "green": 0.20, "blue": 0.23},
        "Analysis_ModelSummary": {"red": 0.47, "green": 0.24, "blue": 0.70},
        "Analysis_NumberHistogram": {"red": 0.90, "green": 0.48, "blue": 0.17},
        "Analysis_ModelNumberHeatmap": {"red": 0.75, "green": 0.20, "blue": 0.25},
        "Analysis_ModelDistributions": {"red": 0.70, "green": 0.10, "blue": 0.14},
        "Analysis_FamilyFavorites": {"red": 0.16, "green": 0.57, "blue": 0.59},
        "Analysis_RunSummary": {"red": 0.42, "green": 0.48, "blue": 0.55},
        "Analysis_BatterySummary": {"red": 0.55, "green": 0.18, "blue": 0.72},
        "Analysis_BatteryTopResponses": {"red": 0.48, "green": 0.16, "blue": 0.64},
        "Analysis_BatteryFingerprint": {"red": 0.36, "green": 0.12, "blue": 0.52},
        "Analysis_BatteryHeatmap": {"red": 0.70, "green": 0.08, "blue": 0.10},
        "Analysis_BatteryCharts": {"red": 0.92, "green": 0.64, "blue": 0.15},
        "Analysis_Charts": {"red": 0.93, "green": 0.72, "blue": 0.20},
    }
    requests = []
    for title, color in tab_colors.items():
        if title not in sheets:
            continue
        requests.append({
            "updateSheetProperties": {
                "properties": {
                    "sheetId": sheets[title],
                    "tabColorStyle": {"rgbColor": color},
                },
                "fields": "tabColorStyle",
            }
        })
    service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body={"requests": requests}).execute()


def add_charts(service, spreadsheet_id: str, sheets: Dict[str, int]) -> None:
    sheet_id = sheets["Analysis_Charts"]

    def range_obj(start_row, end_row, start_col, end_col):
        return {
            "sheetId": sheet_id,
            "startRowIndex": start_row,
            "endRowIndex": end_row,
            "startColumnIndex": start_col,
            "endColumnIndex": end_col,
        }

    def source(start_row, end_row, start_col, end_col):
        return {"sourceRange": {"sources": [range_obj(start_row, end_row, start_col, end_col)]}}

    def chart_position(row, col, width=760, height=420):
        return {
            "overlayPosition": {
                "anchorCell": {"sheetId": sheet_id, "rowIndex": row, "columnIndex": col},
                "widthPixels": width,
                "heightPixels": height,
            }
        }

    chart_requests = [
        {
            "addChart": {
                "chart": {
                    "spec": {
                        "title": "Global Histogram: LLMs vs RNG Controls",
                        "subtitle": "Percent of valid picks by number",
                        "basicChart": {
                            "chartType": "COLUMN",
                            "legendPosition": "BOTTOM_LEGEND",
                            "axis": [
                                {"position": "BOTTOM_AXIS", "title": "Picked number"},
                                {"position": "LEFT_AXIS", "title": "Share of valid picks"},
                            ],
                            "domains": [{"domain": source(1, 102, 0, 1)}],
                            "series": [
                                {"series": source(1, 102, 1, 2), "targetAxis": "LEFT_AXIS"},
                                {"series": source(1, 102, 2, 3), "targetAxis": "LEFT_AXIS"},
                                {"series": source(1, 102, 3, 4), "targetAxis": "LEFT_AXIS"},
                            ],
                            "headerCount": 1,
                        },
                    },
                    "position": chart_position(0, 31, 900, 420),
                }
            }
        },
        {
            "addChart": {
                "chart": {
                    "spec": {
                        "title": "Invalid Rate by Model",
                        "subtitle": "Top 25 by invalid rate",
                        "basicChart": {
                            "chartType": "BAR",
                            "legendPosition": "NO_LEGEND",
                            "axis": [
                                {"position": "BOTTOM_AXIS", "title": "Invalid rate"},
                                {"position": "LEFT_AXIS", "title": "Model"},
                            ],
                            "domains": [{"domain": source(1, 27, 5, 6)}],
                            "series": [{"series": source(1, 27, 7, 8), "targetAxis": "BOTTOM_AXIS"}],
                            "headerCount": 1,
                        },
                    },
                    "position": chart_position(23, 31, 900, 420),
                }
            }
        },
        {
            "addChart": {
                "chart": {
                    "spec": {
                        "title": "Entropy by Model",
                        "subtitle": "Lowest 25 entropy scores, valid rows only",
                        "basicChart": {
                            "chartType": "BAR",
                            "legendPosition": "NO_LEGEND",
                            "axis": [
                                {"position": "BOTTOM_AXIS", "title": "Entropy bits"},
                                {"position": "LEFT_AXIS", "title": "Model"},
                            ],
                            "domains": [{"domain": source(1, 27, 9, 10)}],
                            "series": [{"series": source(1, 27, 11, 12), "targetAxis": "BOTTOM_AXIS"}],
                            "headerCount": 1,
                        },
                    },
                    "position": chart_position(46, 31, 900, 420),
                }
            }
        },
        {
            "addChart": {
                "chart": {
                    "spec": {
                        "title": "Cost by Model",
                        "subtitle": "Top 25 total USD cost in raw results",
                        "basicChart": {
                            "chartType": "BAR",
                            "legendPosition": "NO_LEGEND",
                            "axis": [
                                {"position": "BOTTOM_AXIS", "title": "USD"},
                                {"position": "LEFT_AXIS", "title": "Model"},
                            ],
                            "domains": [{"domain": source(1, 27, 13, 14)}],
                            "series": [{"series": source(1, 27, 15, 16), "targetAxis": "BOTTOM_AXIS"}],
                            "headerCount": 1,
                        },
                    },
                    "position": chart_position(69, 31, 900, 420),
                }
            }
        },
        {
            "addChart": {
                "chart": {
                    "spec": {
                        "title": "Top Number Share by Model",
                        "subtitle": "How dominant each model's favorite number is",
                        "basicChart": {
                            "chartType": "BAR",
                            "legendPosition": "NO_LEGEND",
                            "axis": [
                                {"position": "BOTTOM_AXIS", "title": "Favorite-number share"},
                                {"position": "LEFT_AXIS", "title": "Model"},
                            ],
                            "domains": [{"domain": source(1, 27, 17, 18)}],
                            "series": [{"series": source(1, 27, 19, 20), "targetAxis": "BOTTOM_AXIS"}],
                            "headerCount": 1,
                        },
                    },
                    "position": chart_position(92, 31, 900, 420),
                }
            }
        },
        {
            "addChart": {
                "chart": {
                    "spec": {
                        "title": "Standard Deviation by Model",
                        "subtitle": "Lowest 25; lower means tighter clustering",
                        "basicChart": {
                            "chartType": "BAR",
                            "legendPosition": "NO_LEGEND",
                            "axis": [
                                {"position": "BOTTOM_AXIS", "title": "Std dev of picked number"},
                                {"position": "LEFT_AXIS", "title": "Model"},
                            ],
                            "domains": [{"domain": source(1, 27, 21, 22)}],
                            "series": [{"series": source(1, 27, 23, 24), "targetAxis": "BOTTOM_AXIS"}],
                            "headerCount": 1,
                        },
                    },
                    "position": chart_position(115, 31, 900, 420),
                }
            }
        },
        {
            "addChart": {
                "chart": {
                    "spec": {
                        "title": "Unique Numbers by Model",
                        "subtitle": "Fewest 25 unique picked numbers",
                        "basicChart": {
                            "chartType": "BAR",
                            "legendPosition": "NO_LEGEND",
                            "axis": [
                                {"position": "BOTTOM_AXIS", "title": "Unique numbers"},
                                {"position": "LEFT_AXIS", "title": "Model"},
                            ],
                            "domains": [{"domain": source(1, 27, 25, 26)}],
                            "series": [{"series": source(1, 27, 27, 28), "targetAxis": "BOTTOM_AXIS"}],
                            "headerCount": 1,
                        },
                    },
                    "position": chart_position(138, 31, 900, 420),
                }
            }
        },
    ]
    service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body={"requests": chart_requests}).execute()


def add_battery_charts(service, spreadsheet_id: str, sheets: Dict[str, int], tables: Dict[str, List[List[object]]]) -> None:
    sheet_id = sheets["Analysis_BatteryCharts"]
    row_count = len(tables["Analysis_BatteryCharts"])
    if row_count <= 1:
        return

    def range_obj(start_row, end_row, start_col, end_col):
        return {
            "sheetId": sheet_id,
            "startRowIndex": start_row,
            "endRowIndex": end_row,
            "startColumnIndex": start_col,
            "endColumnIndex": end_col,
        }

    def source(start_row, end_row, start_col, end_col):
        return {"sourceRange": {"sources": [range_obj(start_row, end_row, start_col, end_col)]}}

    def chart_position(row, col, width=900, height=420):
        return {
            "overlayPosition": {
                "anchorCell": {"sheetId": sheet_id, "rowIndex": row, "columnIndex": col},
                "widthPixels": width,
                "heightPixels": height,
            }
        }

    chart_requests = [
        {
            "addChart": {
                "chart": {
                    "spec": {
                        "title": "Prompt Battery: Top Response Share",
                        "subtitle": "Higher means the model collapsed harder on one answer",
                        "basicChart": {
                            "chartType": "BAR",
                            "legendPosition": "NO_LEGEND",
                            "axis": [
                                {"position": "BOTTOM_AXIS", "title": "Top response share"},
                                {"position": "LEFT_AXIS", "title": "Model | prompt"},
                            ],
                            "domains": [{"domain": source(0, row_count, 0, 1)}],
                            "series": [{"series": source(0, row_count, 2, 3), "targetAxis": "BOTTOM_AXIS"}],
                            "headerCount": 1,
                        },
                    },
                    "position": chart_position(0, 8),
                }
            }
        },
        {
            "addChart": {
                "chart": {
                    "spec": {
                        "title": "Prompt Battery: Response Entropy",
                        "subtitle": "Lower means fewer effective answer choices",
                        "basicChart": {
                            "chartType": "BAR",
                            "legendPosition": "NO_LEGEND",
                            "axis": [
                                {"position": "BOTTOM_AXIS", "title": "Response entropy"},
                                {"position": "LEFT_AXIS", "title": "Model | prompt"},
                            ],
                            "domains": [{"domain": source(0, row_count, 0, 1)}],
                            "series": [{"series": source(0, row_count, 3, 4), "targetAxis": "BOTTOM_AXIS"}],
                            "headerCount": 1,
                        },
                    },
                    "position": chart_position(23, 8),
                }
            }
        },
        {
            "addChart": {
                "chart": {
                    "spec": {
                        "title": "Prompt Battery: Unique Responses",
                        "subtitle": "How many distinct valid answers appeared",
                        "basicChart": {
                            "chartType": "BAR",
                            "legendPosition": "NO_LEGEND",
                            "axis": [
                                {"position": "BOTTOM_AXIS", "title": "Unique responses"},
                                {"position": "LEFT_AXIS", "title": "Model | prompt"},
                            ],
                            "domains": [{"domain": source(0, row_count, 0, 1)}],
                            "series": [{"series": source(0, row_count, 4, 5), "targetAxis": "BOTTOM_AXIS"}],
                            "headerCount": 1,
                        },
                    },
                    "position": chart_position(46, 8),
                }
            }
        },
    ]
    service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body={"requests": chart_requests}).execute()


def main() -> int:
    parser = argparse.ArgumentParser(description="Build random-number fingerprint analysis tabs")
    parser.add_argument("--sheet", default=DEFAULT_SHEET_ID, help="Google Sheet ID or URL")
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

    spreadsheet_id = parse_sheet_id(args.sheet)
    credentials = service_account.Credentials.from_service_account_file(
        str(Path(args.service_account)),
        scopes=SCOPES,
    )
    service = build("sheets", "v4", credentials=credentials)

    rows = get_rows(service, spreadsheet_id)
    if not rows:
        raise ValueError("ExperimentResults has no data rows")

    model_summary = build_model_summary(rows)
    number_histogram = build_number_histogram(rows)
    heatmap = build_heatmap(rows)
    model_distributions = build_model_distributions(rows)
    family_summary = build_family_summary(rows)
    run_summary = build_run_summary(rows)
    charts_data = build_charts_data(model_summary, number_histogram)
    battery_summary = build_battery_summary(rows)
    battery_top_responses = build_battery_top_responses(battery_summary)
    battery_fingerprint = build_battery_fingerprint(battery_summary)
    battery_heatmap = build_battery_heatmap(battery_summary)
    battery_charts = build_battery_chart_data(battery_summary)
    readme = build_readme()

    generated_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    for table in (
        readme,
        model_summary,
        number_histogram,
        heatmap,
        model_distributions,
        family_summary,
        run_summary,
        battery_summary,
        battery_top_responses,
        battery_fingerprint,
        battery_heatmap,
        battery_charts,
        charts_data,
    ):
        table.append([])
        table.append(["generated_at", generated_at])

    tables = {
        "Analysis_ReadMe": readme,
        "Analysis_ModelSummary": model_summary,
        "Analysis_NumberHistogram": number_histogram,
        "Analysis_ModelNumberHeatmap": heatmap,
        "Analysis_ModelDistributions": model_distributions,
        "Analysis_FamilyFavorites": family_summary,
        "Analysis_RunSummary": run_summary,
        "Analysis_BatterySummary": battery_summary,
        "Analysis_BatteryTopResponses": battery_top_responses,
        "Analysis_BatteryFingerprint": battery_fingerprint,
        "Analysis_BatteryHeatmap": battery_heatmap,
        "Analysis_BatteryCharts": battery_charts,
        "Analysis_Charts": charts_data,
    }
    table_shapes = {title: (len(table), max(len(row) for row in table if row)) for title, table in tables.items()}

    sheets = recreate_analysis_sheets(service, spreadsheet_id, table_shapes)
    for title, table in tables.items():
        write_table(service, spreadsheet_id, title, table)
    style_tables(service, spreadsheet_id, sheets, tables)
    add_charts(service, spreadsheet_id, sheets)
    add_battery_charts(service, spreadsheet_id, sheets, tables)
    color_tabs(service, spreadsheet_id)

    print({
        "status": "ok",
        "raw_rows": len(rows),
        "analysis_tabs": ANALYSIS_SHEETS,
        "model_summary_rows": len(model_summary) - 3,
        "heatmap_rows": len(heatmap) - 3,
    })
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
