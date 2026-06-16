# LLM Random Number Fingerprint Lab

This repo contains a reproducible experiment for testing how different LLMs respond to arbitrary-choice prompts like:

> Pick a random integer from 1 to 100. Reply with only the number.

The original question came from a meme claiming ChatGPT tends to pick `73`. The more interesting question became: if LLMs are not truly random, do different models have stable arbitrary-choice fingerprints?

## What This Project Tests

The experiment uses:

- `n8n` to orchestrate repeated model calls
- `OpenRouter` to route requests to multiple model providers
- `Google Sheets` to store experiment cases, raw results, and analysis tabs
- local RNG controls to compare LLM outputs against actual random-number generators

The first pass varied mainly:

- model
- prompt

It tried to keep these comparatively steady:

- instruction style
- repetition count
- basic sampling configuration

That means this is not a final statistical proof. It is an exploratory fingerprinting lab. A natural follow-up is to deliberately vary `temperature`, `top_p`, `top_k`, provider routing, reasoning settings, and prompt wording.

## Repo Map

- `04-build/n8n-system/` - runnable n8n workflow templates, scripts, sheet schemas, and operational docs
- `04-build/n8n-system/workflows/active/random-number-fingerprint-experiment-runner.importable.json` - sanitized importable n8n workflow
- `04-build/n8n-system/workflows/templates/` - importable workflow template and Google Sheets CSV headers/starter cases
- `04-build/n8n-system/scripts/` - setup, deployment, control-row, prompt-battery, and analysis scripts
- `02-research/` - research framing and source notes
- `03-architecture/` - system overview and workflow diagrams
- `05-assets/` - optional storytelling/editor packet for the public video narrative

Internal shoot-prep docs and secrets are intentionally excluded.

## Quick Start

1. Create a Google Sheet.
2. Share it with a Google Cloud service account that has Sheets API access.
3. Copy the example environment file:

```bash
cd 04-build/n8n-system
cp .env.example .env
```

4. Fill in `.env` with your n8n URL/API key, Google Sheet ID, credential IDs, and local service-account path.
5. Load the environment variables into your shell:

```bash
set -a
source .env
set +a
```

6. Install Python dependencies used by the Google Sheets scripts:

```bash
python3 -m pip install google-api-python-client google-auth
```

7. Create the sheet tabs and starter experiment rows:

```bash
python3 scripts/setup-random-number-sheet.py \
  --sheet "$RANDOM_NUMBER_FINGERPRINT_SHEET_ID" \
  --service-account "$GOOGLE_SERVICE_ACCOUNT_FILE"
```

8. Build and deploy the n8n workflow:

```bash
node scripts/build-random-number-workflow-template.mjs
python3 scripts/deploy-random-number-workflow.py
```

9. Run the workflow in n8n.
10. Append local RNG controls:

```bash
python3 scripts/append-control-results.py \
  --sheet "$RANDOM_NUMBER_FINGERPRINT_SHEET_ID" \
  --service-account "$GOOGLE_SERVICE_ACCOUNT_FILE" \
  --repetitions 1000
```

11. Build summary tables and charts:

```bash
python3 scripts/build-analysis-tabs.py \
  --sheet "$RANDOM_NUMBER_FINGERPRINT_SHEET_ID" \
  --service-account "$GOOGLE_SERVICE_ACCOUNT_FILE"
```

## Prompt Battery

The repo also includes a prompt-battery mode that goes beyond the basic number prompt:

- number from 1 to 100
- first number that comes to mind
- prime under 100
- letter A-Z
- option A/B/C/D
- color
- city
- everyday object
- year
- made-up first name

To stage battery cases in the template:

```bash
python3 scripts/setup-prompt-battery-cases.py
```

To choose which battery rows are enabled in your live sheet:

```bash
python3 scripts/configure-prompt-battery-run.py \
  --sheet "$RANDOM_NUMBER_FINGERPRINT_SHEET_ID" \
  --service-account "$GOOGLE_SERVICE_ACCOUNT_FILE" \
  --mode smoke
```

Use `--mode full` only when you are ready for the full run and API cost.

## Safety Notes

Do not commit:

- `.env`
- service-account JSON files
- OpenRouter keys
- n8n API keys
- exported workflows with live credential IDs

The public workflow template uses placeholders. Bind your own credentials inside n8n or through the deployment script.

## Caveats

This project is exploratory. LLM outputs can change with:

- model version
- provider route
- sampling settings
- reasoning settings
- prompt wording
- parser strictness
- hidden provider/system behavior

Treat the results as a starting point for investigation, not a final claim about model identity or lineage.
