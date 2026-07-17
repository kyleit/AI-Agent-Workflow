---
name: vir-runtime
command: vir-run
aliases:
  - vir-runtime
category: runtime
tags:
  - vir
  - runtime
  - sandbox
version: 1.0.0
license: MIT
repository: https://gitlab.com/hngan.it/ai-workflow-skills
created_at: 2026-07-12
updated_at: 2026-07-12
description: AI-facing instruction contract for the deterministic Visual Intelligence Runtime (VIR). Executes sandboxed observations without cognitive logic.
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

# VIR Runtime Skill Specification

## Purpose

AI-facing instruction contract for the deterministic Visual Intelligence Runtime (VIR). Executes sandboxed observations without cognitive logic.

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

This skill acts as the AI boundary instruction interface for executing sandboxed browser and application operations.

## 1. Skill Responsibilities
- Invoke the canonical runtime (`skills/vir-runtime/scripts/vir_runtime/`) instead of embedding runtime execution code directly.
- Support deterministic API invocation flows.
- Map and yield structured output envelopes complying with schemas contracts.

## 2. Invocation & API Boundaries
- **Runtime APIs Called**:
  - `vir.runtime.browser.launch()`
  - `vir.runtime.sandbox.start_server()`
  - `vir.runtime.process.terminate_tree()`
- **Contracts Consumed**: `RuntimeRequest`
- **Contracts Produced**: `RuntimeResult`
- **Schemas Consumed**: `config_schema`
