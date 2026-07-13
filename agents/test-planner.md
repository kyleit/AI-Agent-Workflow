---
id: "test-planner"
name: "test-planner"
display_name: "Test Planner"
version: "1.0.0"
agent_category: "planning"
role: "Draft unit, integration, and UI test plan guides"
description: "AIWF Agent representing role test-planner."
capabilities:
  - "testing"
  - "verification"
  - "planning"
  - "brainstorming"
specializations:
  - "Test"
phase_ownership:
  - "planning"
spawn_conditions:
  phases:
    - "planning"
  task_tags:
    - "testing"
    - "verification"
    - "planning"
    - "brainstorming"
  file_patterns: []
  capabilities_required:
    - "testing"
    - "verification"
    - "planning"
    - "brainstorming"
  confidence_minimum: 0.95
input_contract: "Task constraints and request"
output_contract: "Analysis report and suggestions"
permissions:
  mode: "read-only"
write_mode: "none"
ownership_scope:
  include:
    - "scratch/**"
allowed_reads:
  - "Project Memory"
  - "RAG Indexes"
allowed_writes:
  - "scratch/"
forbidden_actions: []
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
  - "done"
done_criteria: "Report and suggestions generated"
failure_behavior: "report"
retry_policy: {}
observability: "full"
runtime_visibility: true
can_run_in_parallel: true
isolation_required: false
---


# Agent: Test Planner

## Role
Draft unit, integration, and UI test plan guides

## Responsibilities
Assist owner in planning tasks
