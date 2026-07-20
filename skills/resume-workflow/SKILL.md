---
name: resume-workflow
command: resume
aliases:
  - continue
category: runtime
tags:
  - resume
  - recovery
  - runtime
version: 2.5.0
license: MIT
created_at: 2026-07-03
updated_at: 2026-07-03
description: Resume the AI Engineering Workflow from the last recorded checkpoint by reading .agents/.session.json and validating the workspace environment.
runtime_requirements:
  rules: required
  state: required
  approvals: optional
  git: cached
  memory: cached
  rag: none
  workspace_scan: none
  environment: cached
  version: cached
  provider: optional
  usage: cached---

# Skill: resume-workflow (Workflow Recovery Engine)

## Purpose

The **resume-workflow** Skill allows the user or orchestrator to recover and continue execution from the last valid checkpoint stored in `.agents/.session.json`. It prevents configuration loss, context drift, and branch misalignment.

---

## Role

You are acting as a **Workflow Coordinator** and **Context Recovery Specialist**.

Your responsibility is to safely restore the session state, verify environment integrity, and recommend the exact next step.

---

## Input

This Skill requires no parameters. It automatically reads state from the workspace.

```yaml
workspace: auto
# Current project directory
```

---

## 🔒 WORKFLOW RUNTIME & INITIALIZATION CHECK

This Skill MUST interface with the centralized Python CLI Runtime Engine:
- **Validate Checkpoint**: Run `python skills/workflow-runtime/scripts/workflow_runtime.py validate --checkpoint "any"` before taking any action. If validation fails, halt execution immediately.
- **Progress Tracking**:
  - *Start*: Run `python skills/workflow-runtime/scripts/workflow_runtime.py start --skill "resume-workflow" --command "resume" --checkpoint 2 --step "Starting execution..."`
  - *Step Updates*: Run `python skills/workflow-runtime/scripts/workflow_runtime.py step --step "<step_desc>" --log "<progress_message>"` progressively during major steps.
  - *Completion*: Run `python skills/workflow-runtime/scripts/workflow_runtime.py complete --checkpoint 2 --step "Step Complete" --next-skill "software-development-workflow" --next-command "workflow"` when execution finishes successfully.
  - *Failure*: Run `python skills/workflow-runtime/scripts/workflow_runtime.py fail --step "<error_step>" --log "<error_details>"` if any phase fails.

## 🔒 GLOBAL POLICY REFERENCES

This Skill MUST strictly adhere to the global policies defined in [AI_RULES.md](../../AI_RULES.md):
- **Approval Gate Policy** (Section 1) - Seek explicit confirmation before modifying code or creating files.
- **Git Workflow Policy** (Section 2) - Perform branch checks and commits/tags/pushes only with approval.
- **Memory First Policy** (Section 3) - Consult project summary/memory before source files or user questions.
- **RAG Policy** (Section 4) - Follow retrieval sequence levels.
- **Artifact Policy** (Section 5) - Strictly follow path boundaries and naming formats.
- **Testing Policy** (Section 8) - Run compilation, build, and tests, halting on failures.
- **Skill Suggestion Gate Policy** (Section 14) - Raw requests require suggestion first; selected Skill requires confirmation.

## Multi-Agent Contract

Runs under the Multi-Agent Workflow. Respect agent ownership and handoff rules defined in [agents/](../../agents/) and [runtime/](../../runtime/).

---

# Workflow

## Step 1 — Read Session State
Read the session file at:
```
.agents/.session.json
```
If the file is not found, stop and recommend running `/init`.

## Step 2 — Drift Detection
1. Run `git branch --show-current` and compare the active branch with the `"git.branch"` recorded in `.session.json`.
2. Check if the work item or project version files have changed since the last recorded step.
3. If drift is detected (e.g. active branch differs from session branch):
   - Output a warning indicating the mismatch.
   - Set `"context_health": "broken"` in `.session.json`.
   - STOP and ask the user to align the workspace (e.g. switch back to the correct branch) before proceeding.

## Step 3 — Resume Recommendation
First, check the `"status"` field in the session file:
1. If `"status"` is `"in_progress"` or `"failed"`:
   - Identify the interrupted skill from the `"current_skill"` field.
   - Recommend retrying/running that exact skill (using its primary command) to resume from the interrupted state.
2. If `"status"` is `"completed"` (or empty/missing), check the last recorded `checkpoint` in the session file:
   - Load the list of checkpoints from `.agents/project-profile.json` (specifically `recommended_workflow`).
   - Map the current `checkpoint` (integer) to the index in the `recommended_workflow` list.
   - Recommend running the skill and primary command associated with the NEXT step in the dynamic workflow array.
   - For example:
     - If active checkpoint is `6` (Code Generation / Implementation Complete): recommend the Debug skill listed in the profile.
     - If active checkpoint is `7` (Debug Complete): check the next step in the profile. If it is `Frontend Visual Debug` (or other UI debug skill), recommend `/visual-debug`. If the next step is `Feature Verification`, recommend `/verify`.
     - If the dynamic workflow is complete: inform the user that the active feature has been successfully released and recommend starting a new workflow.

## Step 5 — Restore Execution Plan (Orchestrator Bypass)
When resuming, check if `.agents/runtime/execution-plan.json` exists and if `"approved"` is `true`. If both are true:
- Restore the execution mode from `implementation_execution_mode`, and restore running, queued, and blocked tasks.
- Do not display the execution mode selection prompt to the user again.

## Step 6 — Heartbeat Output
Print the plain text heartbeat block:
```text
Workflow Runtime Heartbeat
- Current Skill: resume-workflow
- Current Step:  Recovery Analysis
- Checkpoint:    [recorded checkpoint value]
- Context Health:[healthy | broken]
- Memory Status: [loaded | missing | stale]
- RAG Status:    [connected | unavailable]
- Git Branch:    [current branch name]
- Status:        Running
```

---

# Output Rules

Every update to `.agents/.session.json` during the recovery phase must be done atomically (via `.session.json.tmp` rename):
1. **At start of execution**: Update session with `status`: `"in_progress"`, `current_skill`: `"resume-workflow"`, `current_command`: `"resume"`, `current_step`: `"Restoring workflow session..."`, `current_logs`: `["> Starting resume-workflow..."]`, `updated_at`.
2. **During recovery checks**: Update `current_step` and append progress details (e.g., verifying active git branch, checking project files) to `current_logs`.
3. **Upon completion**: Write session state atomically, restoring `"status"` to `"completed"`, `"current_step"` to `"Workflow Restored"`, updating `suggested_next_skill` and `suggested_next_command` with the recommended next step, and appending `"> Workflow session loaded successfully."` to `current_logs`. Do not modify the checkpoint level or other active work item fields during recovery.

---

# Constraints

- Do NOT modify any source code or project configuration.
- Only update `.agents/.session.json` with recovery status and token estimations progressively and atomically.


---

## Completion Contract

```text
Current Phase:
Workflow Recovery

Status:
Completed

Workflow Runtime:
- Session ID:     [session_id]
- Context Health: [healthy | broken]
- Checkpoint:     [recorded checkpoint]
- Current Skill:  resume-workflow
- Current Step:   Recovery Complete
- Work Item:      [FEAT-XXX | FIX-XXX | QUICK-XXX]
- Memory Status:  [loaded | missing]
- RAG Status:     [connected | unavailable]
- Git Branch:     [branch-name]
- Project Version:[version]

Recommended Next Skill:
[Recommended skill name from Step 3]

Workflow Paused.
```
