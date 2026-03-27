---
name: stm32cube_preprocessing_contract
description: "Contract describing how the STM32Cube Preprocessing Agent uses its skills to analyze the pipeline outputs and produce documentation artifacts."
agents: ["STM32Cube Preprocessing Agent"]
skills: ["analyzestats", "document_json_schema", "chunking_strategies"]
---

# Handoffs & Contracts – STM32Cube Preprocessing

This contract defines the main artifacts, their formats and the handoffs between the preprocessing pipeline and the STM32Cube Preprocessing Agent.

## 1) Preprocessing pipeline -> input artifacts

The Python preprocessing pipeline produces the following artifacts:

- `data/docs_issues_<repo>_v2.json`
  - Enriched issues with fields: `layer`, `severity`, `issue_kind`, `board`, `component`, `is_valid`, etc.

- `data/docs_issues_<repo>_v2_sim.json`
  - Same as `docs_issues_v2` plus `related_issue_ids` (similar issues).

- `data/docs_files_<repo>_v2.json`
  - Enriched files (README, Release Notes, Projects) with fields: `file_type`, `board`, `component`, `example_name`, `is_valid`, etc.

- `data/chunks_issues_<repo>_v2.json`
  - Chunked issues (multi-chunks per issue) with metadata.

- `data/chunks_files_<repo>_v2.json`
  - Chunked files (multi-chunks per file) with metadata.

The test scripts produce textual stats and evaluation outputs:

- `python -m src.scripts.test_stats_issues_v2` → console stats on issues.
- `python -m src.scripts.test_stats_files_v2`  → console stats on files.
- `python -m src.scripts.test_tfidf_search_issues_v2` → TF-IDF search examples on issue chunks.
- `python -m src.scripts.test_tfidf_search_files_v2`  → TF-IDF search examples on file chunks.

These outputs are the **inputs** for the STM32Cube Preprocessing Agent.

## 2) STM32Cube Preprocessing Agent – documentation artifacts

The agent reads:

- JSON samples from:
  - `docs_issues_*_v2.json`, `docs_issues_*_v2_sim.json`
  - `docs_files_*_v2.json`
  - `chunks_issues_*_v2.json`
  - `chunks_files_*_v2.json`
- Textual outputs from:
  - `test_stats_issues_v2.py`, `test_stats_files_v2.py`
  - `test_tfidf_search_issues_v2.py`, `test_tfidf_search_files_v2.py`

And writes / helps maintain the following documentation artifacts under `docs/`:

1. `docs/architecture_preprocessing_v2.md`
   - Description of the overall data flow:
     - ingestion -> cleaning -> preprocessing V2 -> similarity -> chunking.
   - Scripts involved and main JSON artifacts.

2. `docs/json_schemas.md`
   - JSON schema documentation for:
     - `docs_issues_v2`, `docs_issues_v2_sim`
     - `docs_files_v2`
     - `chunks_issues_v2`
     - `chunks_files_v2`
   - For each field: name, type, meaning, optional/required.

3. `docs/chunking_strategies.md`
   - Description and comparison of chunking configurations:
     - `V1_full` (1 doc = 1 chunk),
     - `V2_paragraph` (paragraph-based, max_chars ≈ 1200),
     - `V2_small` (paragraph-based, max_chars ≈ 600),
     - (optionally) `V2_sections` for Markdown sections.
   - Advantages, limitations, and recommendations for RAG.

4. `docs/evaluation.md`
   - Summary of evaluation results based on:
     - stats scripts,
     - TF-IDF search examples,
     - analysis of different chunking strategies.
   - Bullet points and conclusions on preprocessing best practices.

## 3) Skills usage

- **Skill `analyzestats`**
  - Trigger: user provides outputs from `test_stats_issues_v2.py` or `test_stats_files_v2.py`.
  - Agent reads the stats and produces:
    - 2–4 bullet points summarizing the distributions (layer, severity, file_type, board, component, etc.).
    - Potential biases or anomalies in preprocessing heuristics.
    - Sentences that can be copied into `docs/evaluation.md`.

- **Skill `document_json_schema`**
  - Trigger: user provides example JSON objects from `docs_*_v2` or `chunks_*_v2`.
  - Agent infers the schema and writes:
    - Markdown sections for `docs/json_schemas.md`:
      - field names, types, meanings, optional/required status.

- **Skill `chunking_strategies`**
  - Trigger: user describes chunking configurations and/or provides evaluation results (TF-IDF comparisons).
  - Agent produces:
    - A structured comparison of chunking configurations.
    - Recommendations for RAG.
    - Text suitable for `docs/chunking_strategies.md` and for the Evaluation section.

## 4) General rules

- The preprocessing pipeline **never** calls the agent at runtime: all artifacts (`docs_*`, `chunks_*`) are produced by Python scripts only.
- The agent **only** produces documentation artifacts and analysis (Markdown text, explanations) and optionally proposes edits to files under `docs/`.
- All documentation generated with the help of the agent must be reviewed and validated by the user before being committed.