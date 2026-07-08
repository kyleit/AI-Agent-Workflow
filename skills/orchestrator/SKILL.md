---
name: orchestrator
command: orchestrate
aliases:
  - orchestrator
  - orchestrate
  - dispatch
  - parallel
category: orchestration
tags:
  - orchestrator
  - workflow
  - parallel
  - multi-agent
  - runtime
version: 1.0.0
description: Top-level autonomous execution orchestrator and single entry point of the framework.
---

# Skill: orchestrator

## Overview
The Orchestrator is the single entry point for all framework workflows. It automatically analyzes user intent, builds the execution DAG, handles file locking, runs tasks in parallel (when beneficial), and merges output, rendering manual skill selection obsolete.

## Orchestrator Responsibilities
1. Only Orchestrator may dispatch agents.
2. Every execution must begin inside Orchestrator.
3. Workers (other Skills) cannot invoke other workers.
4. Workers cannot schedule parallel work, merge outputs, or own workflow state.
5. Only Orchestrator owns workflow, parallel scheduling, dependency graph, merge, conflict resolution, integration, and verification.
6. Workers only execute assigned tasks with restricted write scopes.

## Entry Flow
1. **Load Context**: Load `AI_RULES.md`, `AGENTS.md`, `MANIFEST.json`, `project-profile.json`, memory, RAG, and current session.
2. **Active Workflow Continuation Check**:
   * Before classifying any user request, check the session file (`.agents/.session.json`) for an existing `active_workflow`.
   * If `active_workflow` has `waiting_for` set, and the user's prompt is a continue phrase (e.g., "continue", "tiếp", "tiếp đi", "proceed", "go"):
     * Immediately bypass reclassification.
     * Run the CLI to resume the active workflow:
       ```bash
       python skills/workflow-runtime/scripts/workflow_runtime.py active-workflow resume
       ```
     * Immediately transfer control and execute the instructions of the resumed skill.
     * Stop processing.
3. **Intent Detection & Classification**:
   * If no active workflow is continuation-resumed, classify the user request according to the rules in `software-development-workflow`'s classification matrix.
   * Call `workflow_runtime.py suggest` to persist routing decisions.
   * Present single or ambiguous option layouts, wait for user confirmation via choice protocol, and dispatch to the selected skill via `workflow_runtime.py start`.
4. **Planning & Recommendation (Implementation Phase Only)**:
   * For all early phases (discovery, brainstorming, planning, blueprint generation), execution runs strictly sequentially.
   * When entering Phase 6 (Implementation / Execute) after blueprint approval (checkpoint >= 5), the Orchestrator calculates task splits and write sets:
     * If overlaps exist, recommend Sequential mode.
     * If no overlaps, recommend Parallel mode.
5. **Implementation Choice Prompt**: ONLY when entering Phase 6 (Implementation / Execute), run:
```bash
python3 .agents/skills/workflow-runtime/scripts/workflow_runtime.py prompt select --question "Choose implementation execution mode:" --options "Run implementation in Parallel where safe|Run implementation Sequentially|Re-split implementation tasks|Cancel" --default "Run implementation Sequentially"
```
Wait for user choice and call `workflow-runtime execution mode --mode <choice> --approve` before launching implementation execution.

## Execution Behavior
- **Option 1 (Parallel)**: Launch concurrent workers for task groups having no write_set overlap. Maintain locks registry in `.agents/runtime/file-locks.json`.
- **Option 2 (Sequential)**: Run tasks sequentially in topological DAG order. Ignore all execution groups.
- **Option 3 (Re-split)**: Regenerate task decomposition and plan, then display choice menu again.
- **Option 4 (Cancel)**: Abort execution immediately. Modifies no workspace files.

## Post-Modification Check
- Sau khi bất kỳ Skill nào trong framework được tạo mới hoặc chỉnh sửa, Orchestrator PHẢI khuyến nghị người dùng chạy lệnh xác thực chất lượng Skill để đảm bảo không vi phạm các chính sách an toàn:
  ```bash
  /verify-skill <skill-name>
  ```
