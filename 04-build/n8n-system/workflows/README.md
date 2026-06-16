# Workflows

- `active/`: visible importable workflow JSON for this public repo
- `archive/`: old or superseded workflow exports
- `templates/`: generator output, sheet CSV templates, and setup notes

The public `active/` workflow is sanitized: it has no live n8n workflow ID and no credential IDs. Import it into n8n, bind your own Google Sheets and OpenRouter credentials, and point it at your own spreadsheet.

After editing a workflow in n8n, export JSON back into `active/` and commit it only after removing private credential IDs.
