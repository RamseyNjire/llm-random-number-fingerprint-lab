#!/usr/bin/env python3
"""Create/update the random-number fingerprint workflow in n8n."""

import json
import socket
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Dict, Optional, Tuple

ROOT = Path(__file__).resolve().parents[1]
ENV_FILE = ROOT / ".env"
TEMPLATES_DIR = ROOT / "workflows" / "templates"
ALLOWLIST_FILE = ROOT / "scripts" / "workflow-allowlist.txt"
DEFAULT_SHEET_ID = "YOUR_GOOGLE_SHEET_ID"

WORKFLOW = {
    "template": "random-number-fingerprint-runner-template.json",
    "name": "Random Number Fingerprint - Experiment Runner",
}


def load_env() -> Dict[str, str]:
    env: Dict[str, str] = {}
    if not ENV_FILE.exists():
        return env
    for raw_line in ENV_FILE.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]
        env[key.strip()] = value
    return env


ENV = load_env()
BASE_URL = ENV.get("N8N_BASE_URL", "").rstrip("/")
API_KEY = ENV.get("N8N_API_KEY", "")

if not BASE_URL or not API_KEY:
    print("Missing N8N_BASE_URL or N8N_API_KEY in .env", file=sys.stderr)
    sys.exit(1)


def api_request(method: str, path: str, payload: Optional[dict] = None):
    body = None
    headers = {
        "X-N8N-API-KEY": API_KEY,
        "Accept": "application/json",
    }
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(
        f"{BASE_URL}{path}",
        data=body,
        headers=headers,
        method=method,
    )
    for attempt in range(1, 4):
        try:
            with urllib.request.urlopen(req, timeout=60) as response:
                content = response.read().decode("utf-8")
                return json.loads(content) if content else {}
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"{method} {path} failed with {exc.code}: {detail}") from exc
        except (urllib.error.URLError, TimeoutError, socket.timeout):
            if attempt == 3:
                raise
            time.sleep(2 * attempt)


def api_get(path: str):
    return api_request("GET", path)


def api_post(path: str, payload: Optional[dict] = None):
    return api_request("POST", path, payload)


def api_put(path: str, payload: dict):
    return api_request("PUT", path, payload)


def find_workflow_by_name(name: str):
    data = api_get("/api/v1/workflows?limit=250").get("data", [])
    for item in data:
        if item.get("name") == name:
            return item
    return None


def strip_for_write(workflow: dict):
    return {
        "name": workflow["name"],
        "nodes": workflow["nodes"],
        "connections": workflow["connections"],
        "settings": workflow.get("settings", {}),
    }


def discover_google_sheets_credential() -> Optional[Tuple[str, str]]:
    env_id = ENV.get("N8N_GOOGLE_SHEETS_CREDENTIAL_ID", "").strip()
    env_name = ENV.get("N8N_GOOGLE_SHEETS_CREDENTIAL_NAME", "").strip() or "Google Sheets account"
    if env_id:
        return env_id, env_name

    return None


def discover_openrouter_credential() -> Optional[Tuple[str, str]]:
    env_id = ENV.get("N8N_OPENROUTER_CREDENTIAL_ID", "").strip()
    env_name = ENV.get("N8N_OPENROUTER_CREDENTIAL_NAME", "").strip() or "OpenRouter account"
    if env_id:
        return env_id, env_name

    return None


def apply_sheet_id(workflow: dict, sheet_id: str):
    for node in workflow.get("nodes", []):
        if str(node.get("type", "")).startswith("n8n-nodes-base.googleSheets"):
            node.setdefault("parameters", {})["documentId"] = {
                "__rl": True,
                "mode": "id",
                "value": sheet_id,
            }


def apply_credentials(workflow: dict, google_credential: Optional[Tuple[str, str]], openrouter_credential: Optional[Tuple[str, str]]):
    google_bound = 0
    openrouter_bound = 0

    for node in workflow.get("nodes", []):
        node_type = str(node.get("type", ""))
        params = node.get("parameters", {}) or {}

        if google_credential and node_type.startswith("n8n-nodes-base.googleSheets"):
            cred_id, cred_name = google_credential
            if not isinstance(node.get("credentials"), dict):
                node["credentials"] = {}
            node["credentials"]["googleSheetsOAuth2Api"] = {
                "id": cred_id,
                "name": cred_name,
            }
            google_bound += 1

        is_http_openrouter = (
            node_type == "n8n-nodes-base.httpRequest"
            and str(params.get("authentication", "")) == "predefinedCredentialType"
            and str(params.get("nodeCredentialType", "")) == "openRouterApi"
        )
        if openrouter_credential and is_http_openrouter:
            cred_id, cred_name = openrouter_credential
            if not isinstance(node.get("credentials"), dict):
                node["credentials"] = {}
            node["credentials"]["openRouterApi"] = {
                "id": cred_id,
                "name": cred_name,
            }
            openrouter_bound += 1

    return google_bound, openrouter_bound


def main() -> int:
    sheet_id = ENV.get("RANDOM_NUMBER_FINGERPRINT_SHEET_ID", "").strip() or DEFAULT_SHEET_ID
    if sheet_id == DEFAULT_SHEET_ID:
        print("Missing RANDOM_NUMBER_FINGERPRINT_SHEET_ID in .env", file=sys.stderr)
        return 1

    template_path = TEMPLATES_DIR / WORKFLOW["template"]
    template = json.loads(template_path.read_text())
    template["name"] = WORKFLOW["name"]
    apply_sheet_id(template, sheet_id)

    google_credential = discover_google_sheets_credential()
    openrouter_credential = discover_openrouter_credential()
    google_bound, openrouter_bound = apply_credentials(template, google_credential, openrouter_credential)

    existing = find_workflow_by_name(WORKFLOW["name"])
    payload = strip_for_write(template)

    if existing:
        result = api_put(f"/api/v1/workflows/{existing['id']}", payload)
        workflow_id = result.get("id") or existing["id"]
        action = "updated"
    else:
        result = api_post("/api/v1/workflows", payload)
        workflow_id = result["id"]
        action = "created"

    ALLOWLIST_FILE.write_text(
        "\n".join([
            "# Auto-managed by scripts/deploy-random-number-workflow.py",
            "# Random number fingerprint workflow IDs",
            str(workflow_id),
            "",
        ])
    )

    print(json.dumps({
        "status": "ok",
        "action": action,
        "workflow_id": workflow_id,
        "workflow_name": WORKFLOW["name"],
        "sheet_id": sheet_id,
        "google_sheets_nodes_bound": google_bound,
        "openrouter_nodes_bound": openrouter_bound,
        "allowlist": str(ALLOWLIST_FILE),
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
