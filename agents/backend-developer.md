---
id: "backend-developer"
name: "backend-developer"
display_name: "Backend Developer"
version: "1.0.0"
agent_category: "implementation"
role: "Write backend service code and integration tests"
description: "AIWF Agent representing role backend-developer."
capabilities:
  - "backend"
specializations:
  - "Backend"
phase_ownership:
  - "implementation"
spawn_conditions:
  phases:
    - "implementation"
  task_tags:
    - "backend"
  file_patterns:
    - "**/*.go"
    - "**/*.py"
    - "**/api/**"
    - "**/service/**"
  capabilities_required:
    - "backend"
  confidence_minimum: 0.95
input_contract: "Task constraints and request"
output_contract: "Analysis report and suggestions"
permissions:
  mode: "scoped-write"
write_mode: "single-writer"
ownership_scope:
  include:
    - "sources/backend/**"
    - "skills/**"
    - ".agents/skills/**"
allowed_reads:
  - "Project Memory"
  - "RAG Indexes"
allowed_writes:
  - "sources/backend/"
  - "skills/"
  - ".agents/skills/"
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
  - "qa-reviewer"
done_criteria: "Report and suggestions generated"
failure_behavior: "report"
retry_policy: {}
observability: "full"
runtime_visibility: true
can_run_in_parallel: true
isolation_required: false
---


# Agent: Backend Developer

## Role
Write backend service code and integration tests

## Responsibilities
Assist owner in implementation tasks
