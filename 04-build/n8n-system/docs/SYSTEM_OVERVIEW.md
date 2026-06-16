# System Overview

## Purpose

Run repeatable random-number prompt experiments across OpenRouter models and append raw observations to Google Sheets.

## In Scope

- Manual experiment batches.
- OpenRouter chat completion calls.
- Google Sheets read/append operations.
- Parsing first integer from model responses.
- Derived feature flags for first-pass analysis.

## Out of Scope

- Automated provider identification claims.
- Statistical significance reports.
- Scheduled long-running data collection.
- Tool-backed random-number control condition.

## Upstream Dependencies

- n8n instance.
- OpenRouter API credential.
- Google Sheets credential.
- Google Sheet with `ExperimentCases` and `ExperimentResults` tabs.

## Downstream Outputs

- Append-only rows in `ExperimentResults`.
- Sheet pivots/charts built manually on top of raw rows.

## Runtime Model

- Trigger: manual.
- Batch size: controlled by enabled rows and `repetitions` in `ExperimentCases`.
- Retry/backfill: rerun small batches with a new `run_id`; do not edit previous raw rows.

## Ownership

- Business/content owner: Ramsey / Intellom8.
- Technical owner: project maintainer.
- Escalation path: pause large batches, inspect n8n execution, then rerun only failed scope.
