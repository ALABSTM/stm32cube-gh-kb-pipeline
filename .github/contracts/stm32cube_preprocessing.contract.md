---
name: stm32cube_preprocessing_contract
description: "Contract describing how the STM32Cube Preprocessing Agent collaborates with its skills for preprocessing and ST-ready delivery outputs."
agents: ["STM32Cube Preprocessing Agent"]
skills: ["analyze-stats", "document-json-schema", "chunking-strategies"]
---

# STM32Cube Preprocessing Contract

## Purpose

This contract defines how the STM32Cube Preprocessing Agent should use its skills to support the STM32Cube preprocessing and ST-ready delivery workflow.

## Agent

- **STM32Cube Preprocessing Agent**
  - Main role: analyze, validate, and document the STM32Cube pipeline from ingestion to KB-ready delivery exports.
  - Uses workspace files under `pipeline/`, `shared/`, `data/`, `datasets/`, `docs/`.
  - Prioritizes durable fixes in generators and quality gates over manual one-off patches.

## Active execution paths

- Ingestion: `pipeline/ingestion/*`
- Cleaning: `pipeline/cleaning/*`
- Enrichment: `pipeline/enrichment/*`
- Similarity: `pipeline/similarity/*`
- Chunking: `pipeline/chunking/*`
- Evaluation: `pipeline/evaluation/*`
- Delivery: `pipeline/delivery/*`

Utility entry points:

- Full workflow: `python -m pipeline.run_full_workflow`
- Full workflow with delivery exports: `python -m pipeline.run_full_workflow --export-st-ready`
- Common options: `--skip-ingestion`, `--continue-on-error`
- Schema checks: `python -m pipeline.evaluation.validate_schemas`

Targeted delivery exports:

- `python -m pipeline.delivery.export_st_ready_issues --repo STM32CubeH7`
- `python -m pipeline.delivery.export_st_ready_files --repo STM32CubeH7`
- `python -m pipeline.delivery.export_st_ready_resolver_cases --repo STM32CubeH7`
- `python -m pipeline.delivery.export_st_ready_diagnostic_cards --repo STM32CubeH7`

## Skills

- **analyze-stats**
  - Used when the user provides outputs from:
    - `test_stats_issues_v2.py`
    - `test_stats_files_v2.py`
  - Expected behavior:
    - summarize key distributions (layer, severity, file_type, board, component, etc.),
    - highlight potential biases or anomalies,
    - check consistency against delivery summaries when relevant,
    - suggest bullet points for the Evaluation section.

- **document-json-schema**
  - Used when the user provides one or more JSON examples from:
    - `docs_issues_*_v2.json`
    - `docs_issues_*_v2_sim.json`
    - `docs_files_*_v2.json`
    - `chunks_issues_*_v2.json`
    - `chunks_files_*_v2.json`
    - `st_ready_issues_*.json`
    - `st_ready_files_*.json`
    - `st_ready_resolver_cases_*.json`
    - `st_ready_diagnostic_cards_*.json`
  - Expected behavior:
    - infer field names, types, and meaning,
    - document root format expectations (array vs object key),
    - generate Markdown JSON schema documentation for `docs/json_schemas.md`.

- **chunking-strategies**
  - Used when the user describes or evaluates different chunking configurations (V1_full, V2_paragraph, V2_small, etc.).
  - Expected behavior:
    - compare configurations,
    - explain trade-offs (noise vs context length) in a RAG setting,
    - propose written guidelines for `docs/chunking_strategies.md` and the Evaluation section.

## Workflow (high-level)

1. When the user shares stats outputs, the agent should invoke/align with:
  - `analyze-stats`.

2. When the user shares JSON examples of pipeline outputs, the agent should invoke/align with:
  - `document-json-schema`.

3. When the user discusses chunking configurations and evaluation, the agent should invoke/align with:
  - `chunking-strategies`.

4. When the user reports KB retrieval failures, the agent should first improve generator quality (query aliases, technical anchors, signal filtering, evidence refs) before manual file-specific overrides.

## Output quality checks

- Root JSON format matches consumer expectations.
- Summary counts are coherent with exported payload size.
- Diagnostic cards contain useful `query_aliases`, `keywords`, and `evidence_refs`.
- High-value troubleshooting cases include lexical anchors used in real queries.




  