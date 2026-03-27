---
name: documentjsonschema
description: "Generate human-readable JSON schema documentation for the STM32Cube preprocessing outputs (docs_*, chunks_*)."
---

# Purpose

This skill helps generate clear, human-readable documentation for the JSON outputs produced by the STM32Cube preprocessing pipeline:

- `docs_issues_*_v2.json`
- `docs_issues_*_v2_sim.json`
- `docs_files_*_v2.json`
- `chunks_issues_*_v2.json`
- `chunks_files_*_v2.json`

# Behavior

When this skill is invoked, it must:

1. Take as input one or more JSON examples (single objects) from the output files above.
2. Infer the JSON schema:
   - field names,
   - expected types (string, int, bool, list, etc.),
   - meaning of each field in the STM32Cube context,
   - whether the field is optional or required.
3. Produce Markdown documentation suitable for a file like `docs/json_schemas.md`, organized with:
   - a title for each JSON type (e.g. "Schema docs_issues_v2"),
   - a bullet list or table describing each field.
4. Stay grounded in this project: explanations must be specific to STM32Cube preprocessing.