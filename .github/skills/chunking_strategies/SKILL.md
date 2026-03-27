---
name: chunkingstrategies
description: "Help compare and document different chunking configurations (V1_full, V2_paragraph, V2_small, etc.) for STM32Cube RAG."
---

# Purpose

This skill helps reason about and document chunking strategies used in the STM32Cube preprocessing pipeline.

# Behavior

When this skill is invoked, it must:

1. Take as input a description of one or more chunking configurations (e.g. V1_full, V2_paragraph, V2_small, V2_sections) and optionally some evaluation results (TF-IDF search, examples).
2. Compare the configurations in terms of:
   - segmentation strategy (per document, per paragraph, per section),
   - typical chunk size,
   - impact on noise vs. context completeness in a RAG setting.
3. Suggest advantages, limitations and recommendations for each configuration.
4. Produce Markdown text that can be used in `docs/chunking_strategies.md` or in the Evaluation section of the report.
5. Stay focused on STM32Cube and this project’s pipeline.