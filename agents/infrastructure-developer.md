---
id: "infrastructure-developer"
name: "infrastructure-developer"
display_name: "Infrastructure Developer"
version: "1.0.0"
agent_category: "implementation"
role: "Write Dockerfiles and compose setups"
description: "AIWF Agent representing role infrastructure-developer."
capabilities:
  - "backend"
specializations:
  - "Infrastructure"
phase_ownership:
  - "implementation"
spawn_conditions:
  phases:
    - "implementation"
  task_tags:
    - "backend"
  file_patterns: []
  capabilities_required:
    - "backend"
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


# Agent: Infrastructure Developer

## Role
Write Dockerfiles and compose setups

## Responsibilities
Assist owner in implementation tasks
