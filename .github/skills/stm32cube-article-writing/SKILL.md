---
name: stm32cube-article-writing
description: "Use when: writing project-based articles, report sections, blog-style technical explainers, or polished narrative documentation about the STM32Cube GitHub preprocessing pipeline (ingestion, cleaning, docs_v2, similarity, chunking, evaluation, delivery)."
---

# Purpose

This skill helps produce high-quality, publication-ready articles grounded in this STM32Cube preprocessing repository.

Typical outputs:

- Report sections for PFE/memoire
- Technical articles for internal sharing
- Medium-length architecture explainers
- Comparative write-ups (V1 vs V2, issue docs vs file docs, chunking options)

# Behavior

When this skill is invoked, it must:

1. Stay strictly grounded in this repository (`pipeline/`, `shared/`, `data/`, `datasets/`, `docs/`).
2. Structure the article with clear sections:
   - Context and objective
   - Pipeline architecture and data flow
   - Key design choices and heuristics
   - Evaluation findings (if available)
   - Limitations and improvement roadmap
   - Practical conclusion
3. Explain STM32Cube-specific semantics (layers, components, issue/file schemas, chunking metadata).
4. Use concrete file/script references when relevant (e.g., `pipeline/enrichment/preprocessing_model.py`, `pipeline/evaluation/test_stats_issues_v2.py`).
5. Avoid generic AI prose; prioritize technical clarity, traceability, and actionable insights.
6. If test outputs or JSON examples are provided, integrate them as evidence in the article narrative.
7. Provide copy-ready Markdown that can be placed into `docs/`.

# Suggested Article Template

## Title

A precise title focused on STM32Cube preprocessing V2.

## 1. Context and Goals

- Project scope
- Target repositories/datasets
- Why this preprocessing is needed for RAG

## 2. End-to-End Pipeline

- Ingestion -> cleaning -> docs_v2 enrichment -> similarity -> chunking -> evaluation -> delivery
- Main scripts and outputs at each step

## 3. Data Contracts and Metadata

- Key fields for `docs_issues_v2` and `docs_files_v2`
- Why fields like `layer`, `component`, `issue_kind`, `is_valid` matter

## 4. Quality and Evaluation

- Main distributions and retrieval behavior
- Observed preprocessing biases
- What is robust vs what needs tuning

## 5. Recommendations

- Prioritized technical improvements
- Expected impact on RAG quality

## 6. Conclusion

- Summary of value delivered by the pipeline
- Next milestones

# Style Guidelines

- Keep terminology consistent with STM32Cube and repository naming.
- Prefer concise technical paragraphs over marketing language.
- Use short bullet lists for findings and recommendations.
- Include assumptions explicitly when data is partial.
