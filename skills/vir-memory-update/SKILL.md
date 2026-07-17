---
name: vir-memory-update
command: vir-learn
aliases:
  - vir-memory-update
category: memory
tags:
  - vir
  - memory
  - learning
version: 1.0.0
license: MIT
repository: https://gitlab.com/hngan.it/ai-workflow-skills
created_at: 2026-07-12
updated_at: 2026-07-12
description: Memory consolidation skill promoting visual baselines and compiling lessons learned outcomes.
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

# VIR Memory Update Skill Specification

## Purpose

Memory consolidation skill promoting visual baselines and compiling lessons learned outcomes.

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

This skill consolidates long-term experience, promotes baseline assertions, and stores resolved RCA rules.

## 1. Skill Responsibilities
- Promote new active visual baselines on target routes.
- Format and serialize incremental outcome learnings to vector indexing engines.
- Prune stale history cache entries.

## 2. Invocation & API Boundaries
- **Contracts Consumed**: `Report`, `DigitalTwin`
- **Contracts Produced**: `GoalPlan`
