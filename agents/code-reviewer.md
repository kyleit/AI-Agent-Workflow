---
id: "code-reviewer"
name: "code-reviewer"
display_name: "Code Reviewer"
version: "1.0.0"
agent_category: "review"
role: "Review source code styles and logic rules"
description: "AIWF Agent representing role code-reviewer."
capabilities:
  - "review"
specializations:
  - "Code"
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


# Agent: Code Reviewer

## Role
Review source code styles and logic rules

## Responsibilities
Assist owner in review tasks
