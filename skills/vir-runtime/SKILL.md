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
  usage: none---

# VIR Runtime Skill Specification

This skill acts as the AI boundary instruction interface for executing sandboxed browser and application operations.

## 🎯 Global Policies Reference
All operations MUST adhere strictly to the global workflow constraints defined in [AI_RULES.md](../../AI_RULES.md).

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

## 3. Python VAR (Visual Agentic Runtime) Execution

Python VAR provides a Hexagonal Architecture execution backend for visual observations and agentic verification.

### Usage Commands:
- Capture page observation:
  `python skills/vir-runtime/scripts/var_dispatch.py run --url "http://localhost:3000"`
- Run autonomous agent loop:
  `python skills/vir-runtime/scripts/var_dispatch.py agent --url "http://localhost:3000" --goal "Verify UI layout"`
- Run Quality Gate check:
  `python skills/vir-runtime/scripts/var_dispatch.py check --baseline "comp_1" --current "obs_1"`

