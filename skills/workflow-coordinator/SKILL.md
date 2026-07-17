---
name: workflow-coordinator
command: tick
aliases:
  - coordinate
  - dispatch
category: workflow
tags:
  - orchestrator
  - workflow
  - runtime
  - stateless
version: 3.2.0
license: MIT
repository: https://gitlab.com/hngan.it/ai-workflow-skills
created_at: 2026-07-17
updated_at: 2026-07-17
description: Acts as the stateless entry gate and logical manager of the AI Engineering Workflow.
runtime_requirements:
  rules: required
  state: required
  approvals: required
  git: cached
  memory: cached
  rag: cached
  workspace_scan: none
---

# Skill: workflow-coordinator

## Purpose
The workflow-coordinator skill acts as the stateless entry gate and logical manager of the AI Engineering Workflow. It is invoked on every user tick to parse incoming instructions, enforce gates, load/verify split-state files, check active workflow resume priority, and output deterministic suggestions for the next skill to invoke. It explicitly prohibits the creation of background daemons, heartbeat monitors, or resident loops.

## Public APIs
- `python .agents/skills/workflow-coordinator/scripts/coordinator.py tick --prompt "<prompt>" [--work-item "<work-item>"]`
  Executes a single stateless tick. Returns a JSON string output.

## Workflow Integration
- **Before Hooks**:
  - `initialize-workflow` must run to verify that basic folder configuration exists.
- **After Hooks**:
  - Recommends the next skill to execute via the `suggested_next_skill` payload.
- **Runtime Calls**:
  - Reads `.agents/state/context.json`, `.agents/state/workflow.json`, `.agents/state/approvals.json`, `.agents/state/runtime.json`, `.agents/state/tasks.json`.
  - Writes updates to `workflow.json`, `runtime.json`, `events.jsonl`.
- **Data Exchanged**:
  - Output: JSON dict containing exit status and suggested next skill parameters.

## Configuration
Managed via `.agents/workflow.config.json` under `coordinator` block. Supports:
- `coexistence_mode`: Boolean (allows legacy orchestrator shims)
- `enforce_gates`: Boolean (enforces blueprint and approval gates)

## Runtime Commands
- `tick`: Evaluates current state and routes action.

## Provider Strategy
- Fully LLM-provider agnostic. Classification uses either regex/heuristics or standard provider routing defined in `knowledge-runtime` / RAG models without hardcoding API endpoints.

## Backward Compatibility
- Routes legacy commands `orchestrate` and `orchestrator` to `workflow-coordinator tick`.

## Usage Examples
- `python .agents/skills/workflow-coordinator/scripts/coordinator.py tick --prompt "continue"`
- `python .agents/skills/workflow-coordinator/scripts/coordinator.py tick --prompt "fix ticket 25"`

## Extension Points
- Heuristic intent rules can be added in `coordinator.py` to route custom user workflows.

## Limitations
- Does not manage background executions. Cannot run concurrently on the same workspace (locked via session lock).
