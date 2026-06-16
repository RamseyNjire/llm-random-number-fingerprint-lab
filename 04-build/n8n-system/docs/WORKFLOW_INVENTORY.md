# Workflow Inventory

| Workflow Name | Workflow ID | Purpose | Trigger Type | Schedule/Timing | Inputs | Outputs | Dependencies | Notes |
|---|---|---|---|---|---|---|---|---|
| Random Number Fingerprint - Experiment Runner | `<your-n8n-workflow-id>` | Expands enabled experiment cases, calls OpenRouter, parses number features, appends raw result rows. | Manual | On demand | `ExperimentCases` Google Sheet tab | `ExperimentResults` Google Sheet tab | Google Sheets credential, OpenRouter credential | Bind to your own Google Sheet ID. |

## Rules

- Keep this file updated whenever a workflow is imported, renamed, deleted, or re-scoped.
- Include exact workflow IDs after import into n8n.
- Keep schedule and trigger details explicit if the workflow becomes scheduled later.
