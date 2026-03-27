---
name: analyzestats
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
4. When the user provides test outputs, help interpret them in terms of preprocessing quality and potential improvements.
5. When relevant, suggest improvements to the preprocessing heuristics or test scripts based on the statistical analysis (e.g., if `is_valid` is mostly false for a certain board, maybe the validation rules are too strict for that board).
6. Always provide structured, actionable insights that can be directly used to update documentation or guide preprocessing improvements.
7. When the user provides statistical outputs from test scripts (e.g. test_stats_issues_v2.py, test_stats_files_v2.py), you should use the `analyzestats` skill to summarize the main observations and point out potential biases or anomalies in the preprocessing.

# Example
**User input:**

```Stats for docs_issues_B-L475E-IOT01A_v2.json:
- Total issues: 100
- By layer:
  - HAL: 50
  - Middleware: 5
  - BSP: 30
  - System: 15
- By severity:

  - High: 60
  - Medium: 30
  - Low: 10
- By issue_kind:
  - Bug: 70
  - Enhancement: 20
  - Question: 10
``` 
**Expected analysis:**
- The majority of issues (50%) are related to the HAL layer, which may indicate that this layer is more prone to issues or that the preprocessing heuristics are more effective at identifying HAL-related issues.
- The severity distribution is skewed towards high severity (60%), which could suggest that the preprocessing is effectively prioritizing more critical issues, but it could also indicate a bias in the issue selection or labeling process.
- The issue_kind distribution shows that most issues are classified as bugs (70%), which is expected
but could also reflect a potential underrepresentation of enhancements and questions in the dataset. It may be worth reviewing the issue selection criteria to ensure a more balanced representation of different issue types.
