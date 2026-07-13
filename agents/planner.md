---
id: "planner"
name: "planner"
display_name: "Planner"
version: "1.0.0"
agent_category: "planning"
role: "Convert Brainstorming requirements into Plans"
description: "AIWF Agent representing role planner."
capabilities:
  - "planning"
  - "brainstorming"
specializations:
  - "Planner"
phase_ownership:
  - "planning"
spawn_conditions:
  phases:
    - "planning"
  task_tags:
    - "planning"
    - "brainstorming"
  file_patterns: []
  capabilities_required:
    - "planning"
    - "brainstorming"
  confidence_minimum: 0.95
input_contract: "Brainstorming requirements"
output_contract: "Implementation plan docs/plans/FEAT-XXX_*.md"
permissions:
  mode: "scoped-write"
write_mode: "single-writer"
ownership_scope:
  include:
    - "docs/brainstorming/**"
    - "docs/plans/**"
allowed_reads:
  - "Project Memory"
  - "RAG Indexes"
allowed_writes:
  - "docs/brainstorming/"
  - "docs/plans/"
forbidden_actions:
  - "Bypassing test suite"
  - "Silently scaling privileges"
required_skills: []
required_tools: []
tool_allowlist:
  - "*"
model_preferences:
  - "gemini-2.5-flash"
priority: 1
max_concurrency: 1
resource_limits: {}
confidence_threshold:
  brainstorm: 95
  planning: 95
  blueprint: 95
handoff_targets:
  - "architect"
done_criteria: "Plan covers scope and matches template"
failure_behavior: "report"
retry_policy: {}
observability: "full"
runtime_visibility: true
can_run_in_parallel: false
isolation_required: false
---


# Agent: Planner

## Role
Convert Brainstorming requirements into Plans

## Responsibilities
Create formal Implementation Plans
