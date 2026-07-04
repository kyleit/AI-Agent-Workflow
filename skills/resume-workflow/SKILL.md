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
author:
  name: Kyle Dang
  email: kyleit@klexpress.net
  website: https://www.klexpress.net
license: MIT
repository: https://gitlab.com/hngan.it/ai-workflow-skills
created_at: 2026-07-03
updated_at: 2026-07-03
description: Resume the AI Engineering Workflow from the last recorded checkpoint by reading .agents/.session.json and validating the workspace environment.
---

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

# Pre-flight & Global Policies

This Skill does NOT require any specific checkpoint level before running, but it **requires** that `.agents/.session.json` exists.

If `.agents/.session.json` is missing:
- Recommend running: `initialize-workflow`
- Stop execution.

This Skill MUST strictly follow the global policies defined in [AI_RULES.md](../../AI_RULES.md):
- **Memory First Policy** (Section 3) - When retrieving workspace state.
- **Git Workflow Policy** (Section 2) - When validating branch and repository dirty state.

---

## Multi-Agent Contract

This Skill runs under the Multi-Agent Workflow.
It must respect agent ownership and handoff rules defined in:
- [agents/](../../agents/)
- [runtime/](../../runtime/)

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
   *   **Checkpoint 1** (Initialization Complete):
       - Recommend running: `project-memory-bootstrap` (to load codebase memory).
   *   **Checkpoint 2** (Memory Loaded):
       - Recommend running: `brainstorming` (to start requirement discovery).
   *   **Checkpoint 3** (Architecture Analysis Complete):
       - Check if `docs/plans/FEAT-XXX_*.md` exists.
         - If missing: Recommend running `brainstorming-to-plan`.
         - If exists: Recommend running `plan-to-blueprint` (to create the technical design).
   *   **Checkpoint 4** (Blueprint/Fix Spec Generated):
       - Recommend running: `blueprint-to-implementation` (or `quick-fix`/`quick-feature` if utilizing fast-track).
   *   **Checkpoint 5** (Implementation Ready) or **Checkpoint 6** (Verification & Testing Complete):
       - Recommend running: `implementation-to-release` (to run tests, bump version, and release).
   *   **Checkpoint 7** (Release Complete):
       - Inform the user that the active feature has been successfully released and recommend starting a new workflow.

## Step 4 — Heartbeat Output
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

Update the `"current_skill"` and `"current_step"` in `.agents/.session.json` to reflect that `resume-workflow` was executed. Do not modify the checkpoint level during recovery.

---

# Constraints

- Do NOT modify any source code or project configuration.
- Only update `.agents/.session.json` with recovery status and token estimations.

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
