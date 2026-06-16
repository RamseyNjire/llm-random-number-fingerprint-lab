# Data Contracts

## `ExperimentCases`

- Producer: Google Sheets.
- Consumer: `Read Experiment Cases` -> `Expand Experiment Matrix`.
- Transport: Google Sheets rows.

Required fields:

- `enabled` (`boolean-ish string`) - `TRUE` rows are included.
- `case_id` (`string`) - stable row/case identifier.
- `model_id` (`string`) - exact OpenRouter model ID.
- `provider_label` (`string`) - human-readable lab/provider label.
- `prompt_id` (`string`) - stable prompt variant ID.
- `prompt_text` (`string`) - full user prompt sent to the model.
- `condition_label` (`string`) - experiment condition, usually `model_only`.
- `provider_order` (`string`) - comma-separated OpenRouter provider endpoint tags to try first.
- `allow_fallbacks` (`boolean-ish string`) - `FALSE` pins the request to the listed provider order.
- `require_parameters` (`boolean-ish string`) - when `TRUE`, OpenRouter should only use providers supporting every request parameter.
- `provider_ignore` (`string`) - comma-separated provider endpoint tags to avoid.
- `temperature` (`number`) - OpenRouter sampling parameter.
- `top_p` (`number`) - OpenRouter sampling parameter.
- `max_tokens` (`number`) - low cap is preferred for number-only prompts.
- `repetitions` (`number`) - number of samples to generate for the case.
- `seed_policy` (`string`) - `none`, `fixed`, or `increment`.

Optional fields:

- `seed_start` (`number`) - seed base for fixed/increment policies.
- `notes` (`string`) - human notes copied into output rows.

Validation rules:

- `model_id` must exist in OpenRouter at run time.
- `prompt_text` must be non-empty.
- Start smoke tests with small `repetitions` values.
- `control/*` rows are documented cases only. They are appended by `scripts/append-control-results.py` and should stay disabled in the OpenRouter workflow.

## `ExperimentResults`

- Producer: `Append Experiment Results`.
- Consumer: Google Sheets pivots/charts and later analysis scripts.
- Transport: append-only Google Sheets rows.

Required fields:

- `run_id`, `sample_id`, `measured_at`
- `case_id`, `model_id`, `provider_label`
- `prompt_id`, `prompt_text`, `condition_label`
- `temperature`, `top_p`, `max_tokens`, `repetition_index`
- `seed_policy`, `seed_value`
- `response_text`
- generalized response fields: `response_value`, `response_type`, `valid_response`, `response_parse_error`
- `parsed_number`, `valid_number`, `parse_error`
- feature flags: `is_odd`, `is_even`, `is_prime`, `is_edge`, `is_round`, `contains_7`, `ends_with_7`, `distance_from_50`
- telemetry fields: `latency_ms`, `prompt_tokens`, `completion_tokens`, `total_tokens`, `cost_estimate_usd`
- error/debug fields: `error_status`, `error_message`, `notes`
- requested routing fields: `requested_provider_order`, `requested_allow_fallbacks`, `requested_require_parameters`, `requested_provider_ignore`
- actual routing fields: `returned_model`, `provider_route`, `finish_reason`, `native_finish_reason`, `reasoning_tokens`

Validation rules:

- Keep invalid rows; do not delete them from raw results.
- `valid_number = TRUE` only when the first parsed integer is between 1 and 100.
- `parsed_number` should stay blank for invalid rows so histograms do not include parse failures.
- Local RNG controls use `provider_label = Control`, `condition_label = control_rng`, `finish_reason = control`, and zero token/cost fields.
- `valid_number` is specific to integer 1-100 analysis. Prompt-battery rows should use `valid_response` for categorical prompts like letters, colors, cities, and names.
- New result fields must be appended to the end of `ExperimentResults` so older raw rows remain column-aligned.

## Prompt Battery

- Producer: `scripts/setup-prompt-battery-cases.py`.
- Consumer: `ExperimentCases` and the n8n experiment runner.
- Transport: disabled `ExperimentCases` rows with `condition_label = prompt_battery`.

Current dimensions:

- 12 representative models.
- 10 prompt types.
- 25 repetitions per case.
- 120 disabled rows, or 3,000 model calls if the full battery is enabled.

Prompt-battery response parsing:

- `battery_number_1_100` and `battery_first_number_1_100` -> `integer_1_100`
- `battery_prime_under_100` -> `prime_under_100`
- `battery_letter_a_z` -> `letter_a_z`
- `battery_option_abcd` -> `option_abcd`
- `battery_year_1900_2099` -> `year_1900_2099`
- text choice prompts -> `free_text_choice`
