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

Agents SHOULD invoke the project CLI wrapper (`aiwf ...`) instead of calling the Python script
directly. Direct Python invocation is a maintainer/debug fallback only, because some IDEs require
approval for every Python command.

### 1. Initialize Session
```bash
aiwf init
```
- Creates a clean `.session.json` state, generating a unique `conversation_id` if missing.

### 2. Validate Session Checkpoint
```bash
aiwf validate --checkpoint "exactly X"
```
- Confirms workspace integrity and checks that the current checkpoint is at level `X`.

### 3. Start a Skill
```bash
aiwf start --skill <skill_name> --command <command> --checkpoint <level> --step <step_desc>
```
- Transitions session status to `"in_progress"`.

### 4. Record Execution Step
```bash
aiwf step --step <step_desc> --log <log_message>
```
- Appends progress messages and logs atomically.

### 5. Complete a Skill
```bash
aiwf complete --checkpoint <level> --step <step_desc> --next-skill <skill> --next-command <cmd>
```
- Transitions status to `"completed"` and proposes the next step.

### 6. Fail a Skill
```bash
aiwf fail --step <error_desc> --log <error_log>
```
- Marks status as `"failed"`.

### 7. View Heartbeat
```bash
aiwf heartbeat
```
- Prints the formatted workflow state box.

### 8. Agent-Safe Runtime Daemon

Use this when an IDE/Agent requires approval for every Python/runtime command. The agent writes a
project-local request file, and the already-running runtime daemon executes only allowlisted runtime
commands.

Daemon controls:

```bash
aiwf runtime start
aiwf runtime stop
aiwf runtime restart
aiwf runtime reload
aiwf runtime status
aiwf runtime enable
aiwf runtime disable
```

- `start` / `stop` only affect the current running daemon.
- `restart` restarts only the runtime daemon.
- `reload` restarts both the runtime daemon and the shared Telegram daemon; Telegram is skipped
  with an explicit message when global Telegram credentials are not configured.
- `enable` / `disable` manage OS login autostart, matching the Telegram daemon semantics.
- `status` MUST include the current project context so multi-project setups are not ambiguous.

Request file:

```json
{
  "type": "RUNTIME_COMMAND",
  "command": "deps.resolve",
  "args": {
    "skill": "initialize-workflow"
  },
  "idempotency_key": "deps-resolve-initialize-workflow",
  "requested_at": "2026-07-21T08:40:00Z"
}
```

Supported allowlisted commands:
- `deps.resolve`: refreshes `.agents/state/runtime/dependencies.json`.
- `git.status`: reads branch and short status only. It does not commit, tag, push, checkout, or
  mutate Git state.

Response file: `.agents/runtime/commands/runtime.response.json`.

### 9. One-Shot Configuration

```bash
aiwf config
```

This is the single setup command for normal users. It checks and bootstraps safe local runtime
services: dependency cache, Git read cache, project registry, runtime daemon, and Telegram
daemon when credentials are already configured. Use `--check-only` to report without starting
daemons and `--no-start` to create/cache files without launching background processes.

---

## Examples & Usage Cases
- **Starting Initialization**:
  `aiwf start --skill initialize-workflow --command init --checkpoint 1 --step "Starting initialization..."`
- **Recording Sub-tasks**:
  `aiwf step --step "Resolving workspace path" --log "> Resolved relative path to '.'"`
- **Completion Transition**:
  `aiwf complete --checkpoint 1 --step "Initialization Complete" --next-skill project-discovery --next-command discover`

---

## Troubleshooting & Failure Recovery
- **Corrupted Session File**: If `.session.json` becomes corrupted, the model will output an empty state check error. Run `init` to automatically regenerate a healthy schema without changing the conversation ID.
- **Git Branch Mismatch**: If you switch git branches during execution, `validate` or `heartbeat` will warn or return code 1 due to `context_health` drift detection. Ensure you are on the approved feature branch before running any modifications.
