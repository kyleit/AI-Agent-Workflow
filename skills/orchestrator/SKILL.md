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
2. **Workflow Check**: Determine if a workflow already exists; if yes, resume it (reading `approved` in `execution-plan.json`), otherwise create one.
3. **Intent Detection**: Understand user request (bug, feature, memory, release, etc.) and automatically choose the workflow.
4. **Planning & Recommendation (Implementation Phase Only)**:
   - For all early phases (discovery, brainstorming, planning, blueprint generation), execution runs strictly sequentially. Do NOT analyze parallel task splits or prompt the user for execution mode choice during these phases.
   - When entering Phase 6 (Implementation / Execute) after blueprint approval (checkpoint >= 5), the Orchestrator calculates task splits and write sets:
     - If overlaps exist, recommend Sequential mode.
     - If no overlaps, recommend Parallel mode.
5. **Implementation Choice Prompt**: ONLY when entering Phase 6 (Implementation / Execute), display:
```
================================================================================

Implementation is ready.

Choose execution mode:

1. Run implementation in Parallel where safe
2. Run implementation Sequentially
3. Re-split implementation tasks
4. Cancel

================================================================================
```
Wait for user choice and call `workflow-runtime execution mode --mode <choice> --approve` before launching implementation execution.

## Execution Behavior
- **Option 1 (Parallel)**: Launch concurrent workers for task groups having no write_set overlap. Maintain locks registry in `.agents/runtime/file-locks.json`.
- **Option 2 (Sequential)**: Run tasks sequentially in topological DAG order. Ignore all execution groups.
- **Option 3 (Re-split)**: Regenerate task decomposition and plan, then display choice menu again.
- **Option 4 (Cancel)**: Abort execution immediately. Modifies no workspace files.
