---
name: analyze_stats
description: "Analyze statistical outputs of the STM32Cube preprocessing V2 (layers, severities, file_types, boards, components, etc.)."
---

# Purpose

This skill helps analyze the statistical outputs of the STM32Cube preprocessing V2.

The input to this skill is typically:

- Console outputs from:
  - `test_stats_issues_v2.py`
  - `test_stats_files_v2.py`
- Or small JSON/text snippets with distributions of:
  - `layer`, `severity`, `issue_kind`
  - `file_type`, `board`, `component`, `is_valid`, etc.

# Behavior

When this skill is invoked, it must:

1. Parse the textual statistics provided by the user.
2. Produce a concise analysis with:
   - 2–4 bullet points summarizing the main observations.
   - Optional remarks about potential issues or biases in the preprocessing (e.g., too many `severity=high`, almost no `Middleware` layer, etc.).
3. Stay grounded in the STM32Cube preprocessing context (do not generalize to unrelated projects).