# Engineering-Grade STM32Cube GitHub Preprocessing Pipeline

## Executive Summary

The STM32Cube preprocessing pipeline in this repository is not a simple ETL chain. It is a domain-aware normalization and enrichment system that transforms raw GitHub signals into structured technical knowledge for RAG.

Its strongest contribution is the explicit conversion of noisy issue and file text into operational metadata: `layer`, `severity`, `issue_kind`, `component`, `board`, `is_valid`, and similarity links. This enables filter-first retrieval, higher precision for engineering questions, and traceable answers.

The current V2 implementation is already robust for production pilots. The main quality frontier is no longer ingestion coverage, but metadata calibration and context-preserving chunking in edge cases.

## 1. Why This Pipeline Matters

Technical RAG systems fail when they index raw text without structure. In STM32Cube ecosystems, this failure appears as:

- irrelevant retrieval caused by mixed firmware and tooling language,
- weak board-level grounding,
- inability to distinguish bug reports from usage questions,
- poor prioritization when severity is implicit.

The V2 pipeline addresses these failure modes by introducing a staged architecture where cleaning, enrichment, and evaluation are first-class steps.

## 2. Architecture and Execution Model

The canonical entry point is:

- `python -m pipeline.run_full_workflow`

This orchestrator executes 12 stages in sequence, from ingestion to schema validation.

### 2.1 Stage Map

| Stage | Main script | Input | Output | Primary value |
|---|---|---|---|---|
| Ingestion issues | `pipeline/ingestion/fetch_issues.py` | GitHub API | `raw_issues_<repo>.json` | Captures full issue lifecycle context |
| Ingestion files | `pipeline/ingestion/fetch_files.py` | Local STM32Cube repos | `raw_files_<repo>.json` | Captures README/Release Notes/Projects corpus |
| Cleaning issues | `pipeline/cleaning/clean_issues.py` | raw issues | `clean_issues_<repo>.json` | Canonicalizes body + comments |
| Cleaning files | `pipeline/cleaning/clean_files.py` | raw files | `clean_files_<repo>.json` | Normalizes technical file text |
| Enrichment issues V2 | `pipeline/enrichment/issues_to_docs_v2.py` | clean issues | `docs_issues_<repo>_v2.json` | Adds STM32 metadata fields |
| Enrichment files V2 | `pipeline/enrichment/files_to_docs_v2.py` | clean files | `docs_files_<repo>_v2.json` | Adds file semantics and quality flag |
| Similarity issues V2 | `pipeline/similarity/compute_issue_similarity_v2.py` | docs issues v2 | `docs_issues_<repo>_v2_sim.json` | Adds `related_issue_ids` graph signal |
| Chunking issues V2 | `pipeline/chunking/docs_to_chunks_issues_v2.py` | docs issues | `chunks_issues_<repo>_v2.json` | Paragraph chunks with full metadata |
| Chunking files V2 | `pipeline/chunking/docs_to_chunks_files_v2.py` | docs files | `chunks_files_<repo>_v2.json` | Retrieval-ready document slices |
| Stats issues V2 | `pipeline/evaluation/test_stats_issues_v2.py` | docs issues v2 | console distributions | Detects metadata skew and blind spots |
| Stats files V2 | `pipeline/evaluation/test_stats_files_v2.py` | docs files v2 | console distributions | Validates file-type and coverage balance |
| Schema validation | `pipeline/evaluation/validate_schemas.py` | docs/chunks json | pass/fail | Contract safety before delivery |

## 3. V2 Metadata Model: What Makes It Useful for STM32

The quality of this pipeline comes from how it encodes STM32-specific operational meaning.

### 3.1 Issue document semantics

- `layer`: places knowledge in firmware stack perspective (`HAL`, `LL`, `Middleware`, `CubeMX`, `Other`).
- `severity`: creates triage priority (`low`, `medium`, `high`) from lexical and label cues.
- `issue_kind`: separates bug signal from support traffic (`bug_report`, `usage_question`, `configuration_help`, `other`).
- `component`: maps to recurring peripheral/middleware domains (`USB`, `ETH`, `UART`, `ADC`, `DMA`, `CAN`, `FREERTOS`).
- `board`: preserves hardware grounding for board-specific retrieval.
- `is_valid`: quality gate for ingestion into RAG corpora.

### 3.2 File document semantics

- `file_type`: keeps source intent explicit (`root_readme`, `project_readme`, `release_notes`, `doc_readme`, `other`).
- `path` and `example_name`: maintain traceability to concrete STM32 examples.
- `board` and `component`: unify retrieval facets across issue and file sources.

## 4. Heuristics Design and Trade-Offs

Heuristics are implemented in `pipeline/enrichment/preprocessing_model.py` and `pipeline/enrichment/stm32cube_preprocessing_heuristics.py`.

### 4.1 Strengths

- Transparent rules are explainable during evaluation and auditing.
- Low operational cost and deterministic behavior across releases.
- Good alignment with common STM32 vocabulary patterns.

### 4.2 Known limits

- Keyword collisions in multi-topic issues can shift `layer` or `component`.
- Broad board signatures can dominate over specific board names.
- Severity can be influenced by lexical intensity even when impact is moderate.

These limits are manageable, but they should be monitored as quality KPIs, not treated as static behavior.

## 5. Chunking Strategy and RAG Fitness

The current V2 chunking strategy is paragraph-based with configurable maximum size (`max_chars`, default 1200). Each chunk carries full metadata and explicit position (`chunk_index`, `chunk_count`).

### 5.1 Why this is effective

- Improves retrieval precision versus full-document chunks.
- Preserves local semantic coherence for technical sections.
- Enables chunk-neighbor reconstruction when needed.

### 5.2 Where context can still be lost

- Comments can be isolated from the main technical narrative.
- Internal references may rank without enough explanatory context.

A robust serving strategy should retrieve the matched chunk plus chunk 0 for the same document when confidence is low.

## 6. Evidence Snapshot: STM32CubeH7 Issues V2

Using the provided `test_stats_issues_v2.py` output (N=294):

### 6.1 Distribution highlights

- Layers: `HAL 47.6%`, `Middleware 21.4%`, `Other 18.7%`, `CubeMX 8.2%`, `LL 4.1%`.
- Severity: `medium 58.8%`, `high 31.6%`, `low 9.5%`.
- Issue kind: `bug_report 54.4%`, `usage_question 23.1%`, `other 16.0%`, `configuration_help 6.5%`.

### 6.2 Quality interpretation

- The HAL-heavy profile is plausible for STM32Cube support traffic.
- `Other` is still high enough to justify heuristics expansion.
- `high` severity share is significant and should be audited for lexical over-triggering.
- Component concentration (USB/ETH/FREERTOS/UART/ADC) confirms strong domain signal for embedded retrieval.

## 7. Risks That Matter in Production

1. Metadata drift
- Small heuristic changes can shift field distributions and affect retrieval behavior.

2. Board granularity loss
- Generic values such as family-level tags can reduce troubleshooting precision.

3. Chunk-level context gaps
- Answers based on isolated comment chunks may be technically incomplete.

4. Evaluation blind spots
- Console stats alone are insufficient without sample-level precision checks.

## 8. Priority Roadmap (30-60-90)

### 30 days

- Add a labeled audit set (at least 100 issues) for `layer`, `severity`, `issue_kind`, `component`, `board`.
- Baseline per-field precision and confusion matrix snapshots.

### 60 days

- Refine board detection priority: specific board identifiers before generic family tags.
- Expand lexical maps for CubeMX configuration language and middleware aliases.

### 90 days

- Introduce retrieval-aware chunk post-processing:
	- merge weak comment-only chunks,
	- or down-weight comment chunks during ranking,
	- and auto-attach chunk 0 as context recovery.

## 9. Deployment Blueprint for Technical RAG

Recommended ingestion policy:

1. Primary corpora
- `docs_issues_*_v2.json`
- `docs_files_*_v2.json`

2. Optional enrichment
- `docs_issues_*_v2_sim.json` when issue-neighbor expansion is needed.

3. Quality filter
- ingest only records with `is_valid = true`.

4. Retrieval facets to preserve
- `repo`, `mcu_series`, `layer`, `severity`, `issue_kind`, `component`, `board`, `file_type`, `example_name`.

This policy yields strong technical recall while preserving traceability and controllable answer quality.

## 10. Conclusion

This STM32Cube preprocessing pipeline is already a strong engineering asset: reproducible, explainable, and aligned with embedded support workflows. Its value is not only in text extraction, but in turning heterogeneous repository content into a structured technical signal that retrieval can trust.

With a focused metadata audit loop and chunk-context hardening, the project can move from a solid preprocessing baseline to a measurable, production-grade knowledge backbone for STM32 technical assistance.
