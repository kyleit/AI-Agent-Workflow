---
id: "infrastructure-architect"
name: "infrastructure-architect"
display_name: "Infrastructure Architect"
version: "1.0.0"
agent_category: "architecture"
role: "Design deployment, Docker, and K8s blueprints"
description: "AIWF Agent representing role infrastructure-architect."
capabilities:
  - "architecture"
specializations:
  - "Infrastructure"
phase_ownership:
  - "blueprint"
spawn_conditions:
  phases:
    - "blueprint"
  task_tags:
    - "architecture"
  file_patterns: []
  capabilities_required:
    - "architecture"
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


# Agent: Infrastructure Architect

## Role
Design deployment, Docker, and K8s blueprints

## Responsibilities
Assist owner in architecture tasks
