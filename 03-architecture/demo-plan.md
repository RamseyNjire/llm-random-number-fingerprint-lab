# Demo Plan

## Build Demo

1. Open the Google Sheet and show `ExperimentCases`.
2. Enable a tiny smoke batch: 2 models, 1 prompt, 3 repetitions.
3. Run the n8n workflow manually.
4. Watch rows append to `ExperimentResults`.
5. Show pivot/histogram output.

## First Real Batch

- 10-15 models.
- 1 prompt.
- 100-200 repetitions per model.
- `temperature = 1`, `top_p = 1`, no seed.

## Episode Seed

The hook is not "AI is bad at randomness." The more interesting story is that models inherit human-like concepts of randomness, and different labs/models may leave different behavioral traces.
