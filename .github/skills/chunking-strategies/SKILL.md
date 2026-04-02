---
name: chunking-strategies
description: "Use when: comparing chunking configurations (V1_full, V2_paragraph, V2_small, V2_sections), interpreting TF-IDF retrieval trade-offs, and writing chunking recommendations for docs/chunking_strategies.md or evaluation sections."
---

# Purpose

This skill helps reason about and document chunking strategies used in the STM32Cube preprocessing pipeline.

# Behavior

When this skill is invoked, it must:

1. Take as input one or more chunking configurations (e.g. V1_full, V2_paragraph, V2_small, V2_sections) and optionally evaluation results from `pipeline/evaluation/test_tfidf_search_issues_v2.py` or `pipeline/evaluation/test_tfidf_search_files_v2.py`.
2. Compare the configurations in terms of:
   - segmentation strategy (per document, per paragraph, per section),
   - typical chunk size,
   - impact on noise vs. context completeness in a RAG setting.
3. Suggest advantages, limitations and recommendations for each configuration.
4. Produce Markdown text that can be used in `docs/chunking_strategies.md` or in the Evaluation section of the report.
5. Stay focused on STM32Cube and this project's pipeline.
