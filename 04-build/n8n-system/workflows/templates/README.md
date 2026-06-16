# Random Number Fingerprint Workflow Templates

Import-ready starter assets for the LLM random-number fingerprint experiment.

## Files

- `random-number-fingerprint-runner-template.json`
- `experiment-cases-template.csv`
- `experiment-results-headers.csv`

The same importable workflow is also copied to:

- `../active/random-number-fingerprint-experiment-runner.importable.json`

That copy exists so GitHub visitors can find the n8n workflow without knowing to open the templates folder.

## Google Sheet Setup

Create one spreadsheet with 2 tabs:

1. `ExperimentCases`
   - Import `experiment-cases-template.csv`.
   - Enable/disable rows with the `enabled` column.
   - Adjust model IDs to match currently available OpenRouter models.

2. `ExperimentResults`
   - Create headers from `experiment-results-headers.csv`.
   - Treat this as append-only raw data.

## n8n Setup

1. Import `random-number-fingerprint-runner-template.json`.
2. Set Google Sheets credential on both Sheets nodes.
3. Confirm both Google Sheets nodes point to the experiment spreadsheet.
4. Set the OpenRouter credential on the HTTP Request node.
5. Start with a tiny smoke test before enabling hundreds of repetitions.

## First Batch Recommendation

- 5-10 models.
- 1 prompt.
- 25 repetitions per model for smoke testing.
- Then 100-200 repetitions per model once parsing and logging look clean.

## Notes

- Keep raw invalid responses. Format failures are part of the behavioral trace.
- Do not mix too many prompt variants in the first serious run.
- OpenRouter model availability and exact IDs change; confirm model IDs before a large batch.
