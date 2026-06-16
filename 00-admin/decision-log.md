# Decision Log

| Date | Decision | Why | Status |
|---|---|---|---|
| 2026-05-21 | Use n8n + OpenRouter + Google Sheets for the first experiment runner. | This keeps the build accessible, repeatable, and visually inspectable before moving to Python/R analysis. | Accepted |
| 2026-05-21 | Log raw rows before aggregation. | The goal is exploration; raw responses, parse failures, latency, and token usage may all become interesting signals. | Accepted |
| 2026-05-21 | Start with one workflow and one results table. | A small runnable lab beats a full research platform that never gets run. | Accepted |
| 2026-05-21 | Treat random-number outputs as behavioral traces, not provider identification proof. | Fingerprinting may become interesting, but the first result should avoid overclaiming. | Accepted |
