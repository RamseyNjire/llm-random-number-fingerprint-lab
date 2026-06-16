# Runbook

## Smoke Test

1. Confirm the Google Sheet has `ExperimentCases` and `ExperimentResults`.
2. Confirm the imported workflow exists in n8n.
3. Keep only the smoke-test rows enabled in `ExperimentCases`.
4. Run manually.
5. Confirm `ExperimentResults` receives rows with non-empty `response_text` and sensible `valid_number` values.

## First Real Batch

- Use 5-10 models.
- Use one prompt variant.
- Set `repetitions` to `100` or lower for the first real run.
- Avoid seed experiments until the baseline no-seed behavior is logged.
- Append local controls before analysis with `python3 scripts/append-control-results.py --repetitions 25`.
- Rebuild summary tabs and charts with `python3 scripts/build-analysis-tabs.py`.
- Stage the multi-prompt fingerprint battery with `python3 scripts/setup-prompt-battery-cases.py`, then sync `ExperimentCases` before enabling selected rows.

## Prompt Battery Smoke

- Start by enabling 2 models x 2 prompts with `python3 scripts/configure-prompt-battery-run.py --mode smoke`.
- Confirm new rows include `response_value`, `response_type`, and `valid_response`.
- If the smoke run looks clean, enable the full prompt-battery matrix with `python3 scripts/configure-prompt-battery-run.py --mode full`.
- Return to a no-run state with `python3 scripts/configure-prompt-battery-run.py --mode disabled`.
- The full staged battery is 120 cases x 25 repetitions = 3,000 calls.

## Safe Rerun Procedure

- Reruns generate a new `run_id`.
- Do not overwrite or delete raw rows.
- If a model ID fails, disable that case and rerun only the affected model/prompt row.

## Incident Response

1. Identify the failing node in n8n.
2. Check whether the issue is credentials, model ID availability, rate limits, or parsing.
3. Lower `repetitions` and rerun a tiny batch.
4. Record any model/provider-specific failures in the `notes` column.

## Change Rollout Checklist

- [ ] Update workflow JSON or generator script.
- [ ] Regenerate template JSON if the script changed.
- [ ] Deploy with `python3 scripts/deploy-random-number-workflow.py` if the live n8n workflow changed.
- [ ] Run `jq` parse validation.
- [ ] Update data contracts when fields change.
- [ ] Update this runbook if setup steps change.
