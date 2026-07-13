---
id: "migration-developer"
name: "migration-developer"
display_name: "Migration Developer"
version: "1.0.0"
agent_category: "implementation"
role: "Write data migration and cleanup scripts"
description: "AIWF Agent representing role migration-developer."
capabilities:
  - "backend"
specializations:
  - "Migration"
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


# Agent: Migration Developer

## Role
Write data migration and cleanup scripts

## Responsibilities
Assist owner in implementation tasks
