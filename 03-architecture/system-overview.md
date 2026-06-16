# System Overview

## Purpose

Create a reproducible experiment runner that asks many LLMs to "pick a random number" under controlled prompt and sampling conditions, then writes every raw result to Google Sheets for exploratory analysis.

## Core Question

When different models are asked to imitate randomness, do they show stable, model-specific choice patterns?

## Inputs

- `ExperimentCases` tab in Google Sheets:
  - model ID
  - provider/lab label
  - prompt variant
  - temperature/top_p/max_tokens
  - repetition count
  - optional seed policy
- OpenRouter API credential in n8n.
- Google Sheets credential in n8n.

## Processing

1. Manual trigger starts one experiment batch.
2. Workflow reads enabled experiment cases from Google Sheets.
3. Code node expands each case into one row per repetition.
4. HTTP Request node calls OpenRouter chat completions.
5. Parser extracts the raw answer, first integer, validity, and behavioral features.
6. Append node writes one immutable raw row to `ExperimentResults`.

## Outputs

`ExperimentResults` rows with:

- run metadata: `run_id`, `sample_id`, timestamps, model, prompt, parameters
- raw model output
- parsed number and validity
- derived number features: odd/even, prime, edge, round, contains/seven, distance from 50
- API metadata: latency, token usage, cost fields when available
- error/debug fields for invalid or failed calls

## Analysis Surface

Google Sheets should handle the first pass:

- pivot: count of `parsed_number` by `model_id`
- histogram by model
- top 5 numbers per model
- odd/even ratio
- prime ratio
- contains `7` ratio
- entropy by model
- invalid-response rate

Later analysis can move to Python/R once the experiment starts producing signal.
