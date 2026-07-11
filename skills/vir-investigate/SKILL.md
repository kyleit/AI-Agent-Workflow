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
author:
  name: Kyle Dang
  email: kyleit@klexpress.net
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

This skill manages cognitive reasoning loops, root cause determinations, and contradiction validations.

## 🎯 Global Policies Reference
All operations MUST adhere strictly to the global workflow constraints defined in [AI_RULES.md](../../AI_RULES.md).

## 1. Skill Responsibilities
- Correlate raw evidence collections into coherent investigation nodes.
- Compile hypothesis and resolve ui/network data contradictions.
- Assert confidence thresholds scores.

## 2. Invocation & API Boundaries
- **Contracts Consumed**: `Observation`, `Evidence`
- **Contracts Produced**: `Investigation`, `Hypothesis`, `Contradiction`
- **Schemas Consumed**: `evidence_schema`, `observation_schema`
