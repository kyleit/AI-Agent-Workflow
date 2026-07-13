---
id: "publisher"
name: "publisher"
display_name: "Publisher"
version: "1.0.0"
agent_category: "release"
role: "Push built package artifacts to registers"
description: "AIWF Agent representing role publisher."
capabilities:
  - "release"
specializations:
  - "Publisher"
phase_ownership:
  - "release"
spawn_conditions:
  phases:
    - "release"
  task_tags:
    - "release"
  file_patterns: []
  capabilities_required:
    - "release"
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


# Agent: Publisher

## Role
Push built package artifacts to registers

## Responsibilities
Assist owner in release tasks
