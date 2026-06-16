#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "${ROOT_DIR}"

echo "[1/3] n8n API sanity check..."
if [[ -f ".env" ]] && grep -q '^N8N_BASE_URL=https://' .env && grep -q '^N8N_API_KEY=' .env && ! grep -q '^N8N_API_KEY=replace_me' .env; then
  # shellcheck disable=SC1091
  source "${SCRIPT_DIR}/_common.sh"
  api_get "/api/v1/workflows?limit=1" >/dev/null
  echo "OK"
else
  echo "SKIP (no configured .env)"
fi

echo "[2/3] workflow scope check..."
ALLOWLIST_FILE="${SCRIPT_DIR}/workflow-allowlist.txt"
if [[ ! -f "${ALLOWLIST_FILE}" ]]; then
  echo "ERROR: missing allowlist: ${ALLOWLIST_FILE}"
  exit 1
fi

allowlisted_ids=()
while IFS= read -r id; do
  [[ -z "${id}" ]] && continue
  allowlisted_ids+=("${id}")
done < <(grep -vE '^\s*#|^\s*$' "${ALLOWLIST_FILE}")

seen_ids=()
seen_files=()
shopt -s nullglob
for workflow_file in workflows/active/*.json; do
  workflow_id="$(jq -r '.id // empty' "${workflow_file}")"
  if [[ -z "${workflow_id}" ]]; then
    echo "ERROR: workflow file missing .id: ${workflow_file}"
    exit 1
  fi

  is_allowlisted="false"
  for allowlisted_id in "${allowlisted_ids[@]}"; do
    if [[ "${allowlisted_id}" == "${workflow_id}" ]]; then
      is_allowlisted="true"
      break
    fi
  done

  if [[ "${is_allowlisted}" != "true" ]]; then
    echo "ERROR: workflow file is not allowlisted: ${workflow_file} (id ${workflow_id})"
    exit 1
  fi

  is_duplicate="false"
  for seen_id in ${seen_ids+"${seen_ids[@]}"}; do
    if [[ "${seen_id}" == "${workflow_id}" ]]; then
      is_duplicate="true"
      break
    fi
  done

  if [[ "${is_duplicate}" == "true" ]]; then
    echo "ERROR: duplicate workflow export for id ${workflow_id}: ${workflow_file}"
    exit 1
  fi

  seen_ids+=("${workflow_id}")
  seen_files+=("${workflow_file}")
done
shopt -u nullglob

if [[ "${#seen_ids[@]}" -eq 0 ]]; then
  echo "SKIP (no active workflow exports)"
else
  if [[ "${#allowlisted_ids[@]}" -eq 0 ]]; then
    echo "ERROR: active workflow exports exist, but no workflow IDs found in ${ALLOWLIST_FILE}"
    exit 1
  fi

for workflow_id in "${allowlisted_ids[@]}"; do
  has_export="false"
  for seen_id in ${seen_ids+"${seen_ids[@]}"}; do
    if [[ "${seen_id}" == "${workflow_id}" ]]; then
      has_export="true"
      break
    fi
  done

  if [[ "${has_export}" != "true" ]]; then
    echo "ERROR: allowlisted workflow has no export in workflows/active: ${workflow_id}"
    exit 1
  fi
done
fi

echo "OK"

echo "[3/3] secret pattern scan..."
if rg -n --hidden -S \
  --glob '!secrets/**' \
  --glob '!.env' \
  '(sk-[A-Za-z0-9]{20,}|AIza[0-9A-Za-z\-_]{30,}|xox[baprs]-[A-Za-z0-9-]{10,}|ghp_[A-Za-z0-9]{20,}|-----BEGIN (RSA|EC|OPENSSH|PRIVATE) KEY-----|N8N_API_KEY=[A-Za-z0-9_-]{12,})' \
  workflows docs scripts .env.example README.md .gitignore; then
  echo "ERROR: potential secret pattern found"
  exit 1
fi
echo "OK"

echo "Pre-push checks passed."
