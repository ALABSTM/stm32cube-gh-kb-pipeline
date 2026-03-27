# STM32Cube Preprocessing Project – Global Instructions

## Project Overview

This repository implements a V2 preprocessing pipeline for STM32Cube GitHub public data (issues and files).  
The goal is to produce a **RAG-ready knowledge base** that can be indexed by a RAG engine (vector DB + LLM), without re-implementing the RAG itself.

The main steps are:

1. **Ingestion**
   - `fetch_issues.py`: fetch GitHub issues for STM32Cube repositories (e.g. STM32CubeH7, STM32CubeH5).
   - `fetch_files.py`: collect relevant files from cloned STM32Cube repositories (`README`, `Release_Notes`, `Projects/*/README`, etc.).

2. **Cleaning**
   - `clean_issues.py`: normalize issue texts, merge comments, build a `clean_text` representation → `clean_issues_<repo>.json`.
   - `clean_files.py`: normalize file contents, classify file types (root_readme, project_readme, release_notes, doc_readme, other) → `clean_files_<repo>.json`.

3. **Preprocessing V2**
   - `PreprocessingModelIssuesV2` → `docs_issues_<repo>_v2.json`
     - Adds fields: `layer`, `severity`, `issue_kind`, `board`, `component`, `is_valid`, etc.
   - `PreprocessingModelFilesV2` → `docs_files_<repo>_v2.json`
     - Adds fields: `file_type`, `board`, `component`, `example_name`, `is_valid`, etc.

4. **Similarity & Chunking**
   - `compute_issue_similarity_v2.py` → `docs_issues_<repo>_v2_sim.json` with `related_issue_ids`.
   - `docs_to_chunks_issues_v2.py` → `chunks_issues_<repo>_v2.json`.
   - `docs_to_chunks_files_v2.py` → `chunks_files_<repo>_v2.json`.

## JSON Outputs

The main JSON outputs are:

- `docs_issues_<repo>_v2.json`         – enriched issues.
- `docs_issues_<repo>_v2_sim.json`     – enriched issues + `related_issue_ids`.
- `docs_files_<repo>_v2.json`          – enriched files (README, Projects, Release Notes).
- `chunks_issues_<repo>_v2.json`       – chunked issues (RAG-ready).
- `chunks_files_<repo>_v2.json`        – chunked files (RAG-ready).

All agents and skills should assume this structure when answering questions or generating documentation.

## Evaluation & Tests

The evaluation is mainly based on:

- **Stats scripts**:
  - `test_stats_issues_v2.py`
  - `test_stats_files_v2.py`
- **TF-IDF search scripts**:
  - `test_tfidf_search_issues_v2.py`
  - `test_tfidf_search_files_v2.py`

Agents can use these scripts' outputs to reason about data quality, detect biases and help write the Evaluation section of the report.