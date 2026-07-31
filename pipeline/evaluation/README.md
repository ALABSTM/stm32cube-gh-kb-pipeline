# pipeline/evaluation

This folder contains the **evaluation stage** of the STM32Cube preprocessing
pipeline. Its scripts run quality checks on the outputs of every other stage
(ingestion, cleaning, enrichment, similarity, linkage, delivery) and on the
deployed ST AI Bridge knowledge base / persona itself. They are read-mostly
diagnostic tools: most scripts print reports to the console or write
CSV/JSON/Markdown/Excel/PNG reports under `datasets/06_eval_outputs/` or
`datasets/07_delivery/st_ready/evaluation_report/`, without mutating the
pipeline's core datasets.

Typical uses:

- Spot-check data quality right after a stage runs (`run_full_evaluation.py`).
- Produce chart/Excel deliverables for the PFE report (`generate_evaluation_report.py`).
- Audit config vs. GitHub submodules before an ingestion run (`audit_config_submodules.py`).
- Audit issue<->PR/commit linkage and resolver/diagnostic delivery exports (`run_linkage_delivery_audit.py`).
- Check Alfred image-description enrichment quality (`eval_image_descriptions.py`).
- Benchmark KB retrieval strategies and the full persona (chat) pipeline
  against curated question sets (`run_kb_query_strategy_eval.py`,
  `run_persona_kb_eval.py`).
- Compare offline (manual) vs. online (ST Quality Index) scoring of the same
  benchmark (`compare_offline_online_quality.py`).
- Inspect chunk size distributions (`inspect_chunks_size.py`).

## Scripts (this batch)

- **`audit_config_submodules.py`** — Diffs each `shared/config/config_<series>.json`
  against the GitHub submodules declared in its series repo's `.gitmodules`,
  reporting (or fixing, with `--fix`) missing repo entries.
  Run: `python pipeline/evaluation/audit_config_submodules.py [--fix] [--no-fail]`

- **`compare_offline_online_quality.py`** — Merges manually-scored offline
  benchmark CSVs with online ST Quality Index scores and produces per-scope
  averages plus A/B deltas (CSV + Markdown).
  Run: `python pipeline/evaluation/compare_offline_online_quality.py [--offline-scored-csv PATH] [--online-scores-csv PATH]`

- **`eval_image_descriptions.py`** — Scans enriched issues/files docs for
  Alfred image descriptions and reports success/failure rates and sample
  short/low-quality descriptions.
  Run: `python pipeline/evaluation/eval_image_descriptions.py --repo STM32CubeH7` or `--all`

- **`generate_evaluation_report.py`** — Renders matplotlib charts and an
  Excel workbook summarizing quality metrics for every pipeline stage;
  optionally compiles a LaTeX report to PDF.
  Run: `python pipeline/evaluation/generate_evaluation_report.py --repo STM32CubeH7 [--all] [--pdf]`

- **`inspect_chunks_size.py`** — Minimal script printing chunk count and
  min/max/avg text length for the STM32CubeH7 issues/files chunk files.
  Run: `python pipeline/evaluation/inspect_chunks_size.py`

- **`run_full_evaluation.py`** — Console-based, text-report evaluation of
  all five pipeline stages (ingestion/cleaning/enrichment/similarity/delivery)
  for one or all repos, with a compact summary table.
  Run: `python pipeline/evaluation/run_full_evaluation.py --repo STM32CubeH7 [--all]`

- **`run_kb_query_strategy_eval.py`** — Benchmarks raw KB retrieval
  (`service=kb`, `type=kb-query`) against a question set for a named search
  strategy (semantic threshold / doc counts), recording top-1/top-3 hit rates.
  Run: `python pipeline/evaluation/run_kb_query_strategy_eval.py --run-id R1 --strategy-id S1_SEMANTIC_08`

- **`run_linkage_delivery_audit.py`** — Batch-runs resolver/diagnostic
  delivery exports, validates the issue-linkage JSON against its schema,
  checks summary-count coherence, and reports why issues remain "unlinked".
  Run: `python pipeline/evaluation/run_linkage_delivery_audit.py [--repo REPO ...] [--audit-repo REPO] [--skip-export]`

- **`run_persona_kb_eval.py`** — Benchmarks the full ST GitHub Analyzer
  persona (retrieval + LLM answer) against a question set, checking expected
  keywords (correctness proxy) and forbidden patterns (hallucination proxy).
  Run: `python pipeline/evaluation/run_persona_kb_eval.py --run-id R1 --strategy-id S1_SEMANTIC_08`

<!-- MORE-SCRIPTS-TO-APPEND -->
