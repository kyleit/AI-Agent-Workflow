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
  usage: none---

# VIR Memory Update Skill Specification

This skill consolidates long-term experience, promotes baseline assertions, and stores resolved RCA rules.

## 🎯 Global Policies Reference
All operations MUST adhere strictly to the global workflow constraints defined in [AI_RULES.md](../../AI_RULES.md).

## 1. Skill Responsibilities
- Promote new active visual baselines on target routes.
- Format and serialize incremental outcome learnings to vector indexing engines.
- Prune stale history cache entries.

## 2. Invocation & API Boundaries
- **Contracts Consumed**: `Report`, `DigitalTwin`
- **Contracts Produced**: `GoalPlan`
