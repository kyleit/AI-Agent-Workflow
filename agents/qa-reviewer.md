---
id: "qa-reviewer"
name: "qa-reviewer"
display_name: "Qa Reviewer"
version: "1.0.0"
agent_category: "review"
role: "Perform integration verification audits"
description: "AIWF Agent representing role qa-reviewer."
capabilities:
  - "testing"
  - "verification"
  - "review"
specializations:
  - "Qa"
phase_ownership:
  - "implementation"
spawn_conditions:
  phases:
    - "debug"
  task_tags:
    - "testing"
    - "verification"
    - "review"
  file_patterns: []
  capabilities_required:
    - "testing"
    - "verification"
    - "review"
  confidence_minimum: 0.95
input_contract: "Task constraints and request"
output_contract: "Analysis report and suggestions"
permissions:
  mode: "read-only"
write_mode: "none"
ownership_scope:
  include:
    - "skills/workflow-runtime/tests/**"
    - "tests/**"
    - ".agents/runtime/**"
allowed_reads:
  - "Project Memory"
  - "RAG Indexes"
allowed_writes:
  - "skills/workflow-runtime/tests/"
  - "tests/"
  - ".agents/runtime/"
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
  - "reviewer"
done_criteria: "Report and suggestions generated"
failure_behavior: "report"
retry_policy: {}
observability: "full"
runtime_visibility: true
can_run_in_parallel: true
isolation_required: false
---


# Agent: Qa Reviewer

## Role
Perform integration verification audits

## Responsibilities
Assist owner in review tasks
