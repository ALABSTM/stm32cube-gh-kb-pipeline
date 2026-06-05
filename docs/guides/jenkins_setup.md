# Jenkins Setup for STM32Cube Preprocessing

This repository now includes a root Jenkinsfile to automate the preprocessing pipeline.

## What the pipeline does

- Creates a local Python virtual environment on the Jenkins agent.
- Installs runtime dependencies used by ingestion/evaluation scripts.
- Runs the end-to-end workflow:
  - ingestion
  - cleaning
  - enrichment v2
  - similarity
  - chunking
  - stats
  - schema validation
- Optionally exports ST-ready JSON for issues and files.
- Archives JSON/CSV artifacts for traceability.

## Jenkins prerequisites

- Jenkins agent on Windows with Python installed.
- A Jenkins credential named github-token (Secret text) containing a valid GitHub token.
- SCM job pointing to this repository.

## Job parameters

- SKIP_INGESTION: reuse existing raw data instead of fetching from GitHub.
- CONTINUE_ON_ERROR: continue remaining steps after one step fails.
- EXPORT_ST_READY: generate ST-ready JSON exports.
- TARGET_REPO: repository key to export (default STM32CubeH7).
- PYTHON_BIN: Python executable path/name (default python).

## Recommended usage

- CI per commit: set SKIP_INGESTION=true for fast validation.
- Nightly full refresh: set SKIP_INGESTION=false.
- Keep EXPORT_ST_READY=true to publish ready-to-upload KB artifacts.

## Output artifacts

- data/*.json
- datasets/07_delivery/st_ready/**/*.json
- datasets/06_eval_outputs/*.csv
