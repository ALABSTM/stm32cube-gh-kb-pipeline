---
name: stm32cube_preprocessing_contract
description: "Contract describing how the STM32Cube Preprocessing Agent collaborates with its skills."
agents: ["STM32Cube Preprocessing Agent"]
skills: ["analyzestats", "documentjsonschema", "chunkingstrategies"]
---

# STM32Cube Preprocessing Contract

## Purpose

This contract defines how the **STM32Cube Preprocessing Agent** should use its skills to support the STM32Cube preprocessing PFE project.

## Agent

- **STM32Cube Preprocessing Agent**
  - Main role: analyze and document the STM32Cube preprocessing pipeline (ingestion, preprocessing V2, JSON outputs, tests, evaluation).
  - Uses workspace files under `src/`, `data/`, `docs/`, `test/`.

## Skills

- **analyzestats**
  - Used when the user provides outputs from:
    - `test_stats_issues_v2.py`
    - `test_stats_files_v2.py`
  - Expected behavior:
    - summarize key distributions (layer, severity, file_type, board, component, etc.),
    - highlight potential biases or anomalies,
    - suggest bullet points for the Evaluation section.

- **document_json_schema**
  - Used when the user provides one or more JSON examples from:
    - `docs_issues_*_v2.json`
    - `docs_issues_*_v2_sim.json`
    - `docs_files_*_v2.json`
    - `chunks_issues_*_v2.json`
    - `chunks_files_*_v2.json`
  - Expected behavior:
    - infer field names, types, and meaning,
    - generate Markdown JSON schema documentation for `docs/json_schemas.md`.

- **chunking_strategies**
  - Used when the user describes or evaluates different chunking configurations (V1_full, V2_paragraph, V2_small, etc.).
  - Expected behavior:
    - compare configurations,
    - explain trade-offs (noise vs context length) in a RAG setting,
    - propose written guidelines for `docs/chunking_strategies.md` and the Evaluation section.

## Workflow (high-level)

1. When the user shares **stats outputs**, the agent should invoke/align with:
   - `analyzestats`.

2. When the user shares **JSON examples** of pipeline outputs, the agent should invoke/align with:
   - `document_json_schema`.

3. When the user discusses **chunking configurations and evaluation**, the agent should invoke/align with:
   - `chunking_strategies`.




  