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
version: 2.11.0
license: MIT
created_at: 2026-07-03
updated_at: 2026-07-06
description: Runtime controller for the AI Engineering Workflow. Manages execution session state (.session.json), validates context health, detects context drift, updates checkpoints, supports recovery via resume-workflow, and outputs runtime heartbeats. Read-only.
runtime_requirements:
  rules: required
  state: required
  approvals: optional
  git: cached
  memory: none
  rag: none
  workspace_scan: none
  environment: cached
  version: cached
  provider: optional
  usage: cached---

# Skill: workflow-runtime (AI Workflow Runtime Controller)

---

## 🔒 GLOBAL POLICY REFERENCES

This Skill MUST strictly adhere to the global policies defined in [AI_RULES.md](../../AI_RULES.md):
- **Approval Gate Policy** (Section 1) - Seek explicit confirmation before modifying code or creating files.
- **Git Workflow Policy** (Section 2) - Perform branch checks and commits/tags/pushes only with approval.
- **Memory First Policy** (Section 3) - Consult project summary/memory before source files or user questions.
- **RAG Policy** (Section 4) - Follow retrieval sequence levels.
- **Artifact Policy** (Section 5) - Strictly follow path boundaries and naming formats.
- **Testing Policy** (Section 8) - Run compilation, build, and tests, halting on failures.

## Multi-Agent Contract

Runs under the Multi-Agent Workflow. Respect agent ownership and handoff rules defined in [agents/](../../agents/) and [runtime/](../../runtime/).

---

## Purpose
The **workflow-runtime** Skill acts as the centralized execution state controller for all AI skills. It encapsulates atomic session updates, Git check-pointing, token usage estimations, context drift checks, and workspace validations.

---

## Runtime CLI Commands
The runtime CLI engine is written in Python and resides in:
`skills/workflow-runtime/scripts/workflow_runtime.py`

### 1. Initialize Session
```bash
python skills/workflow-runtime/scripts/workflow_runtime.py init
```
- Creates a clean `.session.json` state, generating a unique `conversation_id` if missing.

### 2. Validate Session Checkpoint
```bash
python skills/workflow-runtime/scripts/workflow_runtime.py validate --checkpoint "exactly X"
```
- Confirms workspace integrity and checks that the current checkpoint is at level `X`.

### 3. Start a Skill
```bash
python skills/workflow-runtime/scripts/workflow_runtime.py start --skill <skill_name> --command <command> --checkpoint <level> --step <step_desc>
```
- Transitions session status to `"in_progress"`.

### 4. Record Execution Step
```bash
python skills/workflow-runtime/scripts/workflow_runtime.py step --step <step_desc> --log <log_message>
```
- Appends progress messages and logs atomically.

### 5. Complete a Skill
```bash
python skills/workflow-runtime/scripts/workflow_runtime.py complete --checkpoint <level> --step <step_desc> --next-skill <skill> --next-command <cmd>
```
- Transitions status to `"completed"` and proposes the next step.

### 6. Fail a Skill
```bash
python skills/workflow-runtime/scripts/workflow_runtime.py fail --step <error_desc> --log <error_log>
```
- Marks status as `"failed"`.

### 7. View Heartbeat
```bash
python skills/workflow-runtime/scripts/workflow_runtime.py heartbeat
```
- Prints the formatted workflow state box.

---

## Examples & Usage Cases
- **Starting Initialization**:
  `python skills/workflow-runtime/scripts/workflow_runtime.py start --skill initialize-workflow --command init --checkpoint 1 --step "Starting initialization..."`
- **Recording Sub-tasks**:
  `python skills/workflow-runtime/scripts/workflow_runtime.py step --step "Resolving workspace path" --log "> Resolved relative path to '.'"`
- **Completion Transition**:
  `python skills/workflow-runtime/scripts/workflow_runtime.py complete --checkpoint 1 --step "Initialization Complete" --next-skill project-discovery --next-command discover`

---

## Troubleshooting & Failure Recovery
- **Corrupted Session File**: If `.session.json` becomes corrupted, the model will output an empty state check error. Run `init` to automatically regenerate a healthy schema without changing the conversation ID.
- **Git Branch Mismatch**: If you switch git branches during execution, `validate` or `heartbeat` will warn or return code 1 due to `context_health` drift detection. Ensure you are on the approved feature branch before running any modifications.
