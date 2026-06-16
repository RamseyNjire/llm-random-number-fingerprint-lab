# Changelog

Use concise operational entries for workflow/system changes.

## Change Entry Template
### YYYY-MM-DD
- Changed:
  - 
- Why:
  - 
- Risk:
  - Low / Medium / High
- Rollback:
  - 

---

## 2026-02-19
- Changed:
  - Added missing starter docs for inventory/changelog/system/contracts/security.
- Why:
  - Complete baseline documentation set expected by README/checklists.
- Risk:
  - Low (documentation only).
- Rollback:
  - Revert this commit.

---

## 2026-03-10
- Changed:
  - Tightened sync/check scripts so allowlisted workflow exports are validated and stale exports are removed.
  - Fixed sync monitoring to emit a single report per run, including failures.
  - Documented local prerequisites and sync behavior in starter docs.
- Why:
  - Make the template safer to reuse across real n8n repos and reduce drift between live workflows and checked-in JSON.
- Risk:
  - Medium (script behavior now fails faster on invalid or missing exports).
- Rollback:
  - Revert this commit.

---

## 2026-05-21
- Changed:
  - Added the random-number fingerprint experiment runner template.
  - Added Google Sheet templates for `ExperimentCases` and `ExperimentResults`.
  - Documented data contracts, workflow inventory, and runbook for smoke testing.
- Why:
  - Create a reproducible first lab for comparing model random-number behavior through OpenRouter.
- Risk:
  - Low (template/docs only until imported into n8n).
- Rollback:
  - Remove the workflow template, CSV templates, and this documentation update.

---

## 2026-05-22
- Changed:
  - Created Google Sheet tabs for the experiment spreadsheet.
  - Deployed `Random Number Fingerprint - Experiment Runner` to n8n as `<your-n8n-workflow-id>`.
  - Bound Google Sheets and OpenRouter credentials.
  - Reduced default enabled rows to a 2-model, 3-repetition smoke test.
  - Expanded `ExperimentCases` with current OpenRouter GPT, Claude, Gemini, Grok, Mistral, DeepSeek, Qwen, and Meta candidate rows.
- Why:
  - Make the lab ready for a low-cost first execution.
  - Avoid prematurely narrowing the experiment to one model per lab.
- Risk:
  - Low (manual-trigger workflow; smoke-test sheet configuration only).
- Rollback:
  - Disable the workflow in n8n or remove `<your-n8n-workflow-id>` from `scripts/workflow-allowlist.txt`.

---

## 2026-05-22 Fix
- Changed:
  - Raised experiment `max_tokens` from 10 to 16 and clamped workflow requests to a 16-token minimum.
  - Added `reasoning_effort` support for GPT/Grok-style reasoning models.
  - Added result metadata fields for returned model, provider route, finish reason, native finish reason, and reasoning-token count.
  - Set GPT/Grok seed rows to `reasoning_effort=minimal` and `max_tokens=64`.
- Why:
  - An early execution failed because Azure-backed `openai/gpt-5.5` rejected `max_output_tokens: 10`; the provider minimum is 16.
  - Another early execution succeeded structurally but GPT-5.5 used the full 16-token cap on hidden reasoning and returned no visible content.
- Risk:
  - Low. Responses should still be number-only, with a controlled reasoning setting and enough output budget to return visible content.
- Rollback:
  - Revert the template and Sheet `max_tokens` / `reasoning_effort` values if OpenRouter/provider behavior changes.

---

## 2026-05-22 Provider Error Handling
- Changed:
  - Set the OpenRouter HTTP node to `neverError=true` so provider/API errors are logged as result rows instead of stopping the full batch.
- Why:
  - One provider-pinned execution failed at item 825 on `meta-llama/llama-3.3-70b-instruct` via AtlasCloud with a generic 400. Because the node was fail-fast, no rows reached `ExperimentResults`.
- Risk:
  - Low. Failed model calls should now appear as invalid rows with error metadata.
- Rollback:
  - Set `neverError=false` if a fail-fast workflow is desired.

---

## 2026-05-22 Provider Pinning
- Changed:
  - Added `provider_order`, `allow_fallbacks`, `require_parameters`, and `provider_ignore` to `ExperimentCases`.
  - Updated the workflow to send OpenRouter's `provider` routing object.
  - Populated preferred provider endpoint tags from OpenRouter endpoint metadata.
  - Disabled `deepseek/deepseek-v3.2-speciale` because no reliable endpoint was returned.
- Why:
  - Provider routing can change outputs and failures, so the baseline should pin one upstream route per model where possible.
- Risk:
  - Medium. Pinning with `allow_fallbacks=FALSE` improves experimental cleanliness but may create logged failures if a provider is temporarily unavailable.
- Rollback:
  - Clear `provider_order` and set `allow_fallbacks=TRUE` to return to OpenRouter default routing.

---

## 2026-05-23 Local RNG Controls
- Changed:
  - Added documented `control/math_random` and `control/crypto_random` case rows.
  - Added `scripts/append-control-results.py` to append local JavaScript RNG control samples into `ExperimentResults`.
- Why:
  - Model outputs need a true random-generator baseline before analysis.
- Risk:
  - Low. Control rows do not call OpenRouter and are marked with `provider_label = Control`.
- Rollback:
  - Delete the appended control rows from `ExperimentResults` by `run_id`, and remove the two control case rows from the template.

---

## 2026-05-23 Analysis Tabs
- Changed:
  - Added `scripts/build-analysis-tabs.py`.
  - Generated `Analysis_ReadMe`, `Analysis_ModelSummary`, `Analysis_NumberHistogram`, `Analysis_ModelNumberHeatmap`, `Analysis_ModelDistributions`, `Analysis_FamilyFavorites`, `Analysis_RunSummary`, and `Analysis_Charts` in the experiment spreadsheet.
  - Added embedded charts for global picked-number distribution, invalid rate by model, entropy by model, and cost by model.
  - Added tab color coding for setup, raw data, analysis, heatmap, charts, and audit views.
  - Added conditional formatting inside analysis tables, red-scale heatmaps, standard deviation metrics, per-model distribution data, and charts for top-number share, standard deviation, and unique-number count.
  - Added prompt-battery analysis tabs and charts after a prompt-battery smoke execution: summary, top responses, model fingerprint, battery heatmap, and battery chart views.
- Why:
  - Turn append-only raw rows into reviewable experiment summaries, first-pass visuals, and a navigable sheet.
- Risk:
  - Low. The script recreates only `Analysis_*` tabs and leaves raw `ExperimentCases` / `ExperimentResults` untouched.
- Rollback:
  - Delete the `Analysis_*` tabs or rerun the script after adjusting the analysis logic.

---

## 2026-05-23 Prompt Battery Setup
- Changed:
  - Added `scripts/setup-prompt-battery-cases.py`.
  - Staged 120 disabled prompt-battery cases in `ExperimentCases`: 12 models x 10 prompt types.
  - Added `PromptBatteryPlan` to the spreadsheet.
  - Added `scripts/configure-prompt-battery-run.py` to switch the live sheet between disabled, smoke, and full prompt-battery modes.
  - Extended the workflow result schema with `response_value`, `response_type`, `valid_response`, and `response_parse_error`.
  - Updated and redeployed workflow `<your-n8n-workflow-id>`.
- Why:
  - Move from a single random-number test toward a multi-prompt behavioral fingerprint.
- Risk:
  - Medium. The workflow schema changed, but new result columns were appended to preserve older row alignment.
- Rollback:
  - Disable prompt-battery rows, restore the previous workflow template, and ignore the appended generalized response columns.
