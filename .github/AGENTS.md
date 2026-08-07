# Agentic Architecture — STM32Cube Preprocessing Pipeline

## Overview

This repository uses a single specialized agent to analyze, validate, and document the STM32Cube preprocessing and ST-ready delivery pipeline.

## Agent

| Agent | File | Role |
|-------|------|------|
| **STM32Cube Preprocessing Agent** | `agents/STM32CubePreprocessing.agent.md` | Pipeline analysis, validation, and technical documentation (ingestion → cleaning → enrichment → similarity → chunking → delivery) |

## Supporting Files

| File | Purpose |
|------|---------|
| `instructions/STM32CubePreprocessing.md` | Detailed operating instructions for the agent |
| `contracts/stm32cube_preprocessing.contract.md` | Contract defining the agent's inputs/outputs and boundaries |
| `scripts/smoke_test_st_api.py` | Smoke test script for validating ST API/delivery readiness |
| `workflows/` | CI automation tied to the preprocessing pipeline |

## Design Principles

1. **Read before write**: Always inspect current pipeline state before modifying scripts or docs.
2. **Legacy `src/` is not the source of truth**: Active code lives under `pipeline/` and `shared/`.
3. **Schema-validated outputs**: All ST-ready delivery JSON must pass `validate_schemas.py`.
4. **Durable fixes over patches**: Diagnose retrieval/generation gaps and fix root causes, not one-off manual edits.
