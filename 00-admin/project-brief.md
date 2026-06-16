# Project Brief

## Summary

- Project: LLM Random Number Fingerprint Lab
- Source idea note: conversation seed, 2026-05-21
- Episode type: build-first research lab
- Best-fit series: Build With Me / AI fundamentals
- Audience: AI builders, automation operators, and curious technical creators

## Goal

Build a small n8n experiment runner that asks many models the same random-number prompts, logs raw results to Google Sheets, and makes it easy to spot patterns before forming a thesis.

## Viewer Promise

The viewer will understand why "LLM choice" is not the same thing as tool-backed randomness, and they will be able to copy a simple OpenRouter + n8n + Google Sheets experiment pattern.

## Core Deliverables

- Import-ready n8n workflow template.
- Google Sheet schema for experiment cases and raw results.
- Seed model/prompt matrix covering popular open and closed model families.
- First-pass analysis fields for number distributions, odd/even, prime, edge avoidance, round-number avoidance, and `7` affinity.

## Success Criteria

- Raw result rows append reliably to Google Sheets.
- Every row records model ID, prompt variant, parameters, raw response, parsed number, and parse validity.
- The first smoke test can run against 2-3 models without manual row cleanup.
- The setup can scale to 100-200 repetitions per model.

## Risks

- OpenRouter model IDs and availability may change.
- Some providers may ignore unsupported parameters such as `seed`.
- A single prompt is not enough to identify a provider reliably.
- n8n rate limits or provider limits may require smaller batches.

## Next Actions

- [x] Create project workspace from the n8n starter.
- [x] Define experiment data contracts.
- [x] Add starter Google Sheet CSV templates.
- [x] Add import-ready n8n workflow template.
- [x] Create a real Google Sheet from the templates.
- [x] Import workflow into n8n and bind credentials.
- [ ] Run a small smoke test against 2-3 models.
- [ ] Run first real batch and review patterns.
