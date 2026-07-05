---
name: workflow-runtime
command: runtime
aliases:
  - engine
category: runtime
tags:
  - runtime
  - controller
  - session
version: 2.5.0
author:
  name: Kyle Dang
  email: kyleit@klexpress.net
  website: https://www.klexpress.net
license: MIT
repository: https://gitlab.com/hngan.it/ai-workflow-skills
created_at: 2026-07-03
updated_at: 2026-07-03
description: Runtime controller for the AI Engineering Workflow. Manages execution session state (.session.json), validates context health, detects context drift, updates checkpoints, supports recovery via resume-workflow, and outputs runtime heartbeats. Read-only.
---

# Skill: workflow-runtime (AI Workflow Runtime Controller)

---

## 🔒 GLOBAL POLICY REFERENCES

This Skill MUST strictly adhere to the global policies defined in [AI_RULES.md](../../AI_RULES.md):
- **Approval Gate Policy** (Section 1) - Required only when creating/updating the `.agents/.session.json` file during step/checkpoint transitions.
- **Git Workflow Policy** (Section 2) - For validating runtime branch consistency.
- **Memory First Policy** (Section 3) - Prioritize session data checks.
- **Artifact Policy** (Section 5) - Save active states pointing to standard directories.

---

## Multi-Agent Contract

This Skill runs under the Multi-Agent Workflow.
It must respect agent ownership and handoff rules defined in:
- [agents/](../../agents/)
- [runtime/](../../runtime/)

## Purpose

The **workflow-runtime** Skill manages the state, health, check-pointing, and resume capabilities of the AI Engineering Workflow. It keeps track of execution state via `.agents/.session.json` to prevent context loss, configuration drift, or incorrect branch transitions.

---

## Runtime Controller Flow

```
Start (Skill Invoked / Triggered)
         ↓
Read .agents/.session.json
         ↓
If Missing: Stop & Recommend /init
         ↓
Validate Context Health & Drift Detection
         ↓
If Inconsistent: Mark BROKEN, Stop & Recommend Recovery
         ↓
Perform Heartbeat / Checkpoint Update / Resume (based on command)
         ↓
Print Runtime Report & Next Step
```

---

## Session State Schema (`.agents/.session.json`)

**CRITICAL RULE**: The `"workspace"` (or `"workspace.path"`) field inside `.agents/.session.json` MUST be written as exactly `"."` (a relative path representation). Under no circumstances should an absolute path be saved or written to this file.

The runtime tracks the current workflow status in this layout:

```json
{
  "workspace": {
    "path": ".",
    "valid": true
  },
  "git": {
    "is_git_repository": true,
    "branch": "string",
    "working_tree": "clean | dirty",
    "default_branch": "string",
    "latest_tag": "string"
  },
  "work_item": {
    "type": "FEAT | FIX | QUICK",
    "id": "string",
    "title": "string"
  },
  "version": {
    "version": "string",
    "source": "string"
  },
  "memory": {
    "status": "FRESH | STALE | MISSING",
    "last_updated": "string (ISO timestamp)"
  },
  "rag": {
    "connected": true,
    "provider": "string"
  },
  "context_usage": {
    "total_tokens": 120534,
    "limit_tokens": 2000000,
    "percentage": 6.0
  },
  "conversation_id": "string (GUID)",
  "checkpoint": 1,
  "status": "in_progress | completed | failed",
  "current_skill": "string",
  "current_step": "string",
  "context_health": "healthy | broken"
}
```

---

## Session File Updates and Context Estimation

Whenever any Skill or Agent updates the `.agents/.session.json` file (including initialization, checkpoint changes, or memory syncs):
1. **Conversation ID Preservation**:
   - The agent MUST retrieve the root `Conversation ID` from the environment metadata (`user_information`).
   - If `"conversation_id"` is not yet set in `.session.json`, save the root ID to the `"conversation_id"` field.
   - If `"conversation_id"` is already defined in `.session.json`, preserve its value (do NOT overwrite it with a subagent's temporary ID).
2. **Context Token Estimation**:
   - The agent MUST calculate the current conversation's token count using the preserved `"conversation_id"` at `<appDataDir>/brain/<conversation_id>/.system_generated/logs/transcript.jsonl` (using `fileSize / 3` as an estimation).
   - Write this estimation into the `"context_usage"` object inside `.agents/.session.json` (specifying `total_tokens`, `limit_tokens: 2000000`, and `percentage`).
3. **Continuous Tracking Policy**:
   - Every time the agent responds or modifies files (even outside standard workflows), it must update `.session.json` as defined in **[AI_RULES.md](../../AI_RULES.md) (Section 12: Session State Tracking Policy)**.
4. **Status Field Updates**:
   - Set to `"in_progress"` at the very beginning of the skill execution (along with the target checkpoint value).
   - Set to `"completed"` upon successful completion of the skill execution.
   - Set to `"failed"` if any step fails or exits with validation errors.
5. This ensures the Visualizer UI Extension displays accurate, real-time context token usage and checkpoint status directly from the session file.

---

## Checkpoint Levels

The execution flow is structured around these standard checkpoint numbers:

*   **Checkpoint 1**: Initialization Complete (runs `/init`)
*   **Checkpoint 2**: Memory Loaded (runs `/memory-sync` / `/memory-init`)
*   **Checkpoint 3**: Requirement Brainstorming Complete (runs `/brainstorm`)
*   **Checkpoint 4**: Implementation Plan Approved (runs `/plan`)
*   **Checkpoint 5**: Technical Blueprint Approved (runs `/blueprint`)
*   **Checkpoint 6**: Implementation Complete (runs `/implement`)
*   **Checkpoint 7**: Debug Complete (runs `/debug`)
*   **Checkpoint 8**: Verification Complete (runs `/verify`)
*   **Checkpoint 9**: Release Complete (runs `/release`)

---

## Wrong Behavior & Context Drift Detection

Before every Skill step:
1. Compare the runtime Git branch against the `.session.json` branch field.
2. Compare the active version and work item files against the `.session.json` definitions.
3. If the branch, work item, or version changes unexpectedly:
   - Mark `context_health: "broken"`.
   - **STOP** execution immediately.
   - Display a Context Drift Warning and recommend recovery.

---

## Heartbeat Output Format

At major steps, the executing agent must print this plain text heartbeat block:

```text
Workflow Runtime Heartbeat
- Current Skill: [skill-name]
- Current Step:  [step-name]
- Checkpoint:    [N]
- Context Health:[healthy | broken]
- Memory Status: [loaded | missing | stale]
- RAG Status:    [connected | unavailable]
- Git Branch:    [branch-name]
- Status:        [Running | Paused]
```

---

## Resume Workflow (`/resume`)

When the user runs `/resume`:
1. Read `.agents/.session.json`.
2. Extract the last recorded `checkpoint`, `status`, `current_skill`, and `current_step`.
3. Verify that the current workspace branch and files match the session config.
4. Recommend the correct next action:
   - If `"status"` is `"in_progress"` or `"failed"`: Identify that `current_skill` was interrupted, and recommend retrying/running that exact skill (using its primary command) to resume.
   - If `"status"` is `"completed"` (or empty): Recommend running the next skill in the workflow corresponding to the next checkpoint.

---

## Runtime Report Format

At the end of every Skill execution, print this plain text report:

```text
Current Phase:
Workflow Runtime Status

Status:
Completed

Workflow Runtime:
- Session ID:     [session_id]
- Context Health: [healthy | broken]
- Checkpoint:     [N]
- Current Skill:  [skill-name]
- Current Step:   [step-name]
- Work Item:      [FEAT-XXX | FIX-XXX | QUICK-XXX]
- Memory Status:  [loaded | missing]
- RAG Status:     [connected | unavailable]
- Git Branch:     [branch-name]
- Project Version:[version]

Recommended Next Skill:
[skill-name]

Workflow Paused.
```
