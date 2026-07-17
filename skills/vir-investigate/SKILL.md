---
name: vir-investigate
command: vir-audit
aliases:
  - vir-investigate
category: reasoning
tags:
  - vir
  - cognitive
  - rca
version: 1.0.0
license: MIT
repository: https://gitlab.com/hngan.it/ai-workflow-skills
created_at: 2026-07-12
updated_at: 2026-07-12
description: Cognitive investigation skill for Root Cause Analysis (RCA), contradictions detection, and self-doubt evaluations.
runtime_requirements:
  rules: required
  state: required
  approvals: optional
  git: cached
  memory: cached
  rag: lazy
  workspace_scan: none
  environment: none
  version: none
  provider: optional
  usage: none
---

# VIR Investigate Skill Specification

## Purpose

Cognitive investigation skill for Root Cause Analysis (RCA), contradictions detection, and self-doubt evaluations.

---

## 🔒 WORKFLOW RUNTIME & INITIALIZATION CHECK

This Skill interfaces with the centralized Python CLI Runtime Engine:
- **Validate Checkpoint**: Run `python skills/workflow-runtime/scripts/workflow_runtime.py validate --checkpoint "optional"` before taking any action.
- **Progress Tracking**: Update status and log progress using `workflow_runtime.py` when integrated in a workflow session.

---

## 🔒 GLOBAL POLICY REFERENCES

This Skill strictly adheres to the global policies defined in [AI_RULES.md](../../AI_RULES.md):
- **Approval Gate Policy** (Section 1) - Seek explicit confirmation before modifying code or creating files.
- **Memory First Policy** (Section 3) - Consult project summary/memory before source files or user questions.
- **RAG Policy** (Section 4) - Follow retrieval sequence levels.
- **Artifact Policy** (Section 5) - Strictly follow path boundaries and naming formats.

---

This skill manages cognitive reasoning loops, root cause determinations, and contradiction validations.

## 1. Skill Responsibilities
- Correlate raw evidence collections into coherent investigation nodes.
- Compile hypothesis and resolve ui/network data contradictions.
- Assert confidence thresholds scores.

## 2. Invocation & API Boundaries
- **Contracts Consumed**: `Observation`, `Evidence`
- **Contracts Produced**: `Investigation`, `Hypothesis`, `Contradiction`
- **Schemas Consumed**: `evidence_schema`, `observation_schema`
