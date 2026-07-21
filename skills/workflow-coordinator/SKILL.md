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

## Continuous Pre-Approval Orchestration
- Treat natural language project requests as coordinator ticks by default. If intent classification is clear, auto-dispatch the matching workflow Skill; do not ask the user to run `/quick-feature`, `/quick-fix`, `/brainstorming`, or another Skill command manually.
- Ask for workflow selection only when the request is genuinely ambiguous, missing required information, or maps to multiple incompatible workflows with similar confidence.
- Route the standard flow as Discovery (`brainstorming`, Product/Requirement Analyst) -> Roadmap Gate for large/multi-phase features (`docs/roadmaps/`, Product Analyst + Planner + Architect) -> Internal Roadmap/Discovery Review (Reviewer/QC) -> Planning (`brainstorming-to-plan`, Planner) -> Internal Plan Review (Reviewer/QC) -> Blueprint (`plan-to-blueprint`, Architect) -> Internal Blueprint Review (Reviewer/QC + relevant specialists) -> Runtime Prompt Select Blueprint Approval.
- Route quick work as Specification (`quick-feature` or `quick-fix`, Planner/Requirement Analyst) -> Internal Spec Review (Reviewer/QC) -> Blueprint (Architect) -> Internal Blueprint Review (Reviewer/QC + relevant specialists) -> Runtime Prompt Select Blueprint Approval.
- Before advancing any pre-approval artifact, require an internal review loop and require the artifact to contain an `Internal Review Evidence` section. If review FAILS, the owning phase agent must state the exact failed points, revise only those points, and repeat review until PASS.
- A phase review PASS requires: document-compliance score `>=95/100`, zero no-go findings, relative-path scan PASS, all checklist rows supported by concrete evidence, and no missing `Internal Review Evidence`.
- Large, multi-phase, system-level, cross-module, or high-risk features require a reviewed Roadmap under `docs/roadmaps/` before Planning. If the Roadmap is missing or review FAILS, keep routing back to `brainstorming` until the Roadmap passes.
- Planning and Blueprint phases must preserve Roadmap phase order and coverage. If either phase discovers a missing capability or phase mismatch, route back to the Roadmap Gate instead of patching downstream artifacts directly.
- If review FAILS, do not create the next artifact yet. The coordinator must return the work to the same phase owner with only the failed-point list and scope boundary.
- Do not create a user approval stop for roadmap, brainstorming, Mini Spec, or Implementation Plan when the workflow can continue without new user information.
- Stop absolutely only after the Technical Blueprint passes internal review and the Agent has requested approval through:
  `aiwf prompt select --question "Approve this Technical Design Blueprint for implementation?" --options "Continue|Cancel" --default "Cancel"`
- Do not replace this final gate with plain chat approval text. If the runtime prompt bridge is unavailable, explicitly report that unavailability and remain stopped at Blueprint Approval.
- Do not approve the Blueprint, inspect more files, run git/tests, or implement code until explicit approval evidence exists.
- If a phase touches frontend design, UI/UX, layout, typography, color, animation, icons, visual hierarchy, frontend components, or design-system decisions, route the phase through `frontend-design` before the artifact is considered reviewable.

## Backward Compatibility
- Routes legacy commands `orchestrate` and `orchestrator` to `workflow-coordinator tick`.

## Usage Examples
- `python .agents/skills/workflow-coordinator/scripts/coordinator.py tick --prompt "continue"`
- `python .agents/skills/workflow-coordinator/scripts/coordinator.py tick --prompt "fix ticket 25"`

## Extension Points
- Heuristic intent rules can be added in `coordinator.py` to route custom user workflows.

## Limitations
- Does not manage background executions. Cannot run concurrently on the same workspace (locked via session lock).
