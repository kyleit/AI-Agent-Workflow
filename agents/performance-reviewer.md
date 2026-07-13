---
id: "performance-reviewer"
name: "performance-reviewer"
display_name: "Performance Reviewer"
version: "1.0.0"
agent_category: "review"
role: "Perform load tests and memory leak audits"
description: "AIWF Agent representing role performance-reviewer."
capabilities:
  - "review"
specializations:
  - "Performance"
phase_ownership:
  - "implementation"
spawn_conditions:
  phases:
    - "debug"
  task_tags:
    - "review"
  file_patterns: []
  capabilities_required:
    - "review"
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


# Agent: Performance Reviewer

## Role
Perform load tests and memory leak audits

## Responsibilities
Assist owner in review tasks
