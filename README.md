# STM32Cube Data Pipeline for ST Knowledge Base

This repository contains the PFE project developed at STMicroelectronics to transform STM32Cube GitHub data into structured, traceable, and upload-ready knowledge for the ST internal AI assistant.

The current project state is centered on:
- industrial preprocessing of STM32Cube repositories,
- multimodal enrichment for visual evidence (Alfred Vision),
- ST-ready delivery exports,
- automated upload to ST AI Bridge KB,
- CI/CD execution in both self-hosted and github-hosted modes.

## Scope and Current Coverage

- Target ecosystem: STM32Cube public repositories (main series and driver sub-repos)
- Coverage: 25 STM32 series configured
- Delivery outputs: 4 artifact families
  - issues cards
  - files cards
  - resolver cases (issue -> PR -> commit)
  - diagnostic cards
- KB target: ST AI Bridge Knowledge Base `#793`
- Operating model: per-series execution with reproducible automation workflows

## End-to-End Functional Architecture

```mermaid
flowchart LR
    A[GitHub Sources<br/>Issues PRs Commits Files PDFs] --> B[Ingestion]
    B --> C[Cleaning V3<br/>Type-aware normalization]
    C --> D[Enrichment V2<br/>Metadata + STM32 heuristics]
    D --> E[Similarity & Linkage<br/>Issue PR Commit chains]
    E --> F[Delivery Export<br/>ST-ready JSON by series]
    F --> G[Upload Automation<br/>Datasources in KB #793]
    G --> H[ST GitHub Analyzer Persona<br/>KB-first retrieval]

    I[Alfred Vision<br/>Image/PDF description] --> D
    I --> F
```

## CI/CD Automation Architecture

```mermaid
flowchart TD
    T[Trigger<br/>manual or scheduled] --> P[Prepare matrix inputs]
    P --> R[Runner availability check]
    R --> Q[Preprocess per series<br/>windows-latest]

    Q --> U{Upload execution target}
    U -->|self-hosted| S[Upload per series<br/>self-hosted runner]
    U -->|github-hosted| C[Upload per series<br/>windows-latest]

    S --> K[ST AI Bridge KB #793]
    C --> K
```

Design intent:
- `github-hosted` path is used for cloud validation and portability.
- `self-hosted` path is used when internal network constraints require local runner execution.

## Repository Layout

```text
PFE_Chatbot_STM32Cube/
├── pipeline/                    # Core preprocessing and export logic
│   ├── ingestion/
│   ├── cleaning/
│   ├── enrichment/
│   ├── similarity/
│   ├── delivery/
│   └── evaluation/
├── pipeline_Automation/         # Workflow orchestration + upload + operational scripts
│   ├── workflow/
│   ├── upload/
│   ├── alfred/
│   └── test_suites/
├── shared/                      # Configs, schemas, shared utils
│   ├── config/
│   ├── schemas/
│   └── utils/
├── datasets/                    # Structured outputs by stage (raw -> delivery)
├── data/                        # Operational/legacy artifacts used by scripts
├── docs/                        # PFE report, workshop material, guides
├── .github/workflows/           # CI/CD workflows
└── requirements.txt
```

## Workflows Used in Production

- `.github/workflows/manual_auto_update_kb.yml`
  - main operational workflow for controlled runs
- `.github/workflows/auto_update_kb.yml`
  - scheduled and manual automated runs
- `.github/workflows/smoke_test_st_api.yml`
  - connectivity/authentication smoke test for ST API

### Supported Modes

- `Prepare`: preprocessing and export only
- `Upload`: upload pre-generated ST-ready outputs only
- `Full`: prepare + upload

### Upload Targets

- `self-hosted`
- `github-hosted`

## Required Secrets (GitHub Actions)

Configure in repository settings:
- `ST_GITHUB_ANALYZER_API_KEY` (required for upload)
- `ST_REMOTE_USER` (recommended)
- one Alfred key alias (or set all three for compatibility)
  - `ST_CHATGPT_API_KEY`
  - `ST_AI_BRIDGE_API_KEY`
  - `ST_API_KEY`
- `RUNNER_CHECK_TOKEN` (recommended for reliable self-hosted availability check)

Compatibility note:
- The three Alfred key names exist for backward compatibility between workflows/scripts.
- Upload authentication uses `ST_GITHUB_ANALYZER_API_KEY`.

## Quick Start (Validation Sequence)

Recommended first validation on a new repo/environment:
1. Run `smoke_test_st_api.yml`.
2. Run `manual_auto_update_kb.yml` with `series=C0`, `mode=Prepare`.
3. Run `manual_auto_update_kb.yml` with `series=C0`, `mode=Upload`, `existing_datasource_mode=Add`.
4. Run `manual_auto_update_kb.yml` with `series=C0`, `mode=Full`.

## Project References

- Main report: `docs/reports/PFE_Report_STM32Cube_Pipeline.tex`
- Workshop guide: `docs/Atelier_Pratique_Pipeline_STM32Cube.md`
- Encadrant run checklist: `docs/guides/st_repo_actions_handover_checklist_fr.md`

## Operational Notes

- This repository contains very large JSON artifacts; first push can be long.
- GitHub Enterprise warnings around 50 MB files are expected for some generated artifacts.
- `.gitignore` does not untrack files already committed in history.

## Internal Usage

Internal STMicroelectronics PFE project.
