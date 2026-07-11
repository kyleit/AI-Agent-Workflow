---
name: vir-verify
command: vir-check
aliases:
  - vir-verify
category: quality
tags:
  - vir
  - verify
  - gate
version: 1.0.0
author:
  name: Kyle Dang
  email: kyleit@klexpress.net
license: MIT
repository: https://gitlab.com/hngan.it/ai-workflow-skills
created_at: 2026-07-12
updated_at: 2026-07-12
description: Final quality gate verification skill applying weighted consensus, visual audits, and SDLC compliance rules.
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

# VIR Verify Skill Specification

This skill serves as the final quality-gate evaluator enforcing visual compliance and SDLC threshold checks.

## 🎯 Global Policies Reference
All operations MUST adhere strictly to the global workflow constraints defined in [AI_RULES.md](../../AI_RULES.md).

## 1. Skill Responsibilities
- Evaluate blueprint alignment and workflow gates blockers.
- Compute weighted consensus scores, downgrading vetoes that lack explicit evidence reference coordinates.
- Flag final PASS/FAIL execution statuses.

## 2. Invocation & API Boundaries
- **Contracts Consumed**: `Investigation`, `VisualFinding`
- **Contracts Produced**: `QualityGate`, `Report`
