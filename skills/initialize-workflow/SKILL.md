---
name: initialize-workflow
command: init
aliases:
  - initialize
category: runtime
tags:
  - initialization
  - runtime
  - lightweight
version: 3.0.0
license: MIT
created_at: 2026-07-03
updated_at: 2026-07-11
description: Lightweight runtime initializer for the AI Engineering Workflow. Loads mandatory guardrails, reads cached git/state/approval/dashboard context only. Does NOT load full memory, RAG, workspace scan, environment CLI checks, or transcript sync.
runtime_requirements:
  rules: required
  state: required
  approvals: required
  git: cached
  memory: cached
  rag: cached
  workspace_scan: none
  environment: cached
  version: cached
  provider: optional
  usage: cached---

# Skill: initialize-workflow (Lightweight Runtime Initialization)

---

## 🔒 GLOBAL POLICY REFERENCES

This Skill MUST strictly adhere to the global policies defined in [AI_RULES.md](../../AI_RULES.md):
- **Approval Gate Policy** (Section 1) - Seek explicit confirmation before modifying code or creating files.
- **Git Workflow Policy** (Section 2) - Read branch/status only (cached). No push, fetch, tag, or remote operations.
- **Memory First Policy** (Section 3) - Memory is CACHED mode only — reads metadata JSON, never full project-summary.md.
- **Artifact Policy** (Section 5) - Strictly follow path boundaries and naming formats.
- **Workspace Permission Mode Policy** (Section 15) - Sandbox mode is default.

---

## 🔒 LIGHTWEIGHT INITIALIZATION CONTRACT

This skill is the **mandatory entry point** of the AI Engineering Workflow. Its purpose is to compile a minimal runtime context from cached state files only — fast, safe, and repeatable.

### Hard Rules (NEVER VIOLATE)

| Forbidden Operation | Reason |
|---|---|
| Load full `project-summary.md` or memory chunks | Use `memory: cached` (metadata JSONs only) |
| Connect to RAG / query vector DB | Use `rag: cached` (metadata only) |
| Scan `docs/`, workspace files, or manifests | `workspace_scan: none` |
| Run direct Git commands during normal init | Use `.agents/state/git.json` or runtime command bus `git.status` |
| Run `python --version`, `node --version`, `docker version`, etc. | Forbidden — consume `workspace_doctor` JSON report instead |
| Parse transcript files or sync request history | `usage: cached` — read from `dashboard.json` or `context/usage.json` only |
| Call `sync_request_history()`, `parse_transcript()`, `refresh_context_usage_for_active_conversation()` | All forbidden during init |
| Write absolute paths to `.session.json` | Workspace `path` must always be `"."` |

### Git Data Contract

During normal Agent-driven initialization, do not run direct Git commands. Read Git data from
`.agents/state/git.json` first. If the cache is missing or stale and the runtime daemon is active,
request `git.status` through `.agents/runtime/commands/runtime.request.json`.

The only direct Git commands that may be used by the runtime daemon, `aiwf config`, or an explicitly
approved fallback are:
- `git rev-parse --is-inside-work-tree`
- `git branch --show-current`
- `git status --short`

Agents MUST NOT chain these commands with runtime start commands during initialization.

---

## Purpose

The `initialize-workflow` Skill compiles a lightweight, unified runtime context so subsequent Skills do not duplicate checks. All expensive operations (memory load, RAG connect, workspace scan, env CLI checks) are deferred to the skills that actually need them via the Runtime Dependency Resolver.

**Latency Goal**: < 0.8 seconds

---

## Workflow Sequence

```
Step 1:  Run deps resolve (Runtime Dependency Resolver)
         ↓
Step 2:  Load Guardrails Summary (hash-based)
         ↓
Step 3:  Read Git State (3 allowed commands only)
         ↓
Step 4:  Read Cached State + Approvals
         ↓
Step 5:  Read Cached Version + Provider + Usage (from state files only)
         ↓
Step 6:  Write Initialization Summary
         ↓
Step 7:  Auto-Resume & Git Auto-Stash Recovery (Optional)
         ↓
Step 8:  Arm Telegram project inbox monitor only when the shared daemon is active
         ↓
STOP — No memory load, no RAG, no env CLI, no workspace scan, no transcript sync
```

---

## Detailed Step Instructions

### Step 0 — Start Initialization & Progressive Tracking

- Immediately update `.agents/state/runtime.json` atomically with:
  - `status`: `"in_progress"`
  - `current_skill`: `"initialize-workflow"`
  - `current_command`: `"init"`
  - `current_step`: `"Starting lightweight workflow initialization..."`
  - `updated_at`: (current ISO-8601 timestamp)
- Do not call `python skills/workflow-runtime/scripts/workflow_runtime.py start ...` during normal
  initialization. Some IDEs ask for approval for every Python command. This Skill must use cached
  state files and runtime command-bus requests instead.

### Step 1 — Resolve Runtime Dependencies Without Approval Noise

Do not require agents to run a Python runtime command on every initialization. Some IDEs and agents
require approval for every Python command. Use this order:

1. Read `.agents/state/runtime/dependencies.json`.
2. If the file exists, is valid JSON, and `skill == "initialize-workflow"`, use it as the cached
   dependency result.
3. If the cache is missing or invalid, write a command-bus request to
   `.agents/runtime/commands/runtime.request.json`:

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

4. Wait for `.agents/runtime/commands/runtime.response.json`. If it reports `status == "OK"`,
   re-read `.agents/state/runtime/dependencies.json`.
5. If no runtime daemon is running and direct commands are blocked, continue with the existing
   cache if available; otherwise stop with a clear message telling the user to run `aiwf config` once.
6. Only if the user or IDE has explicitly allowed the project CLI, the fallback command is
   `aiwf deps resolve --skill initialize-workflow`. Do not call the Python script directly from this
   Skill.

- If resolution fails for a `required` dependency → **STOP**, print error, exit.
- If resolver warns about missing `runtime_requirements` in other skills → log warning, continue (safe_minimal fallback applies).
- The canonical resolution output is `.agents/state/runtime/dependencies.json`.

### Step 2 — Load Guardrails Summary (Hash-Based)

- Compute SHA-256 hash of `AI_RULES.md`, `.agents/AGENTS.md`, and active `SKILL.md`.
- Build `policy_flags` dict: `approval_gate`, `git_gate`, `blueprint_gate`, `release_gate`, `testing_gate`, `workspace_permission_gate`.
- **DO NOT** re-read or re-enforce full rule text — hash confirms integrity only.
- Source function: `load_guardrails_summary()` in `session.py`.

### Step 3 — Read Git State (Cached Only)

- Read `.agents/state/git.json` first and store the cached result in session `git` field.
- If the cache is missing/stale and the runtime daemon is active, write a `git.status` request to
  `.agents/runtime/commands/runtime.request.json`, wait for `.agents/runtime/commands/runtime.response.json`,
  then re-read `.agents/state/git.json`.
- If the daemon is inactive and the cache is missing, warn only and continue with
  `is_repository: unknown`; tell the user to run `aiwf config` once to refresh the cache.
- Do not run direct Git commands during normal Agent initialization.
- **FORBIDDEN**: `git describe --tags`, `git remote -v`, `git fetch`, `git tag`, `git --version`, `python --version`, `node --version`, `go version`, `docker --version`.

### Step 4 — Read Cached State + Approvals

- Read `.agents/state/context.json` → work_item, checkpoint, project metadata.
- Read `.agents/state/approvals.json` → approval state.
- Read `.agents/state/workflow.json` → workflow progress.
- **Handover Walkthrough**: If `.agents/state/walkthrough.md` exists, the AI MUST read this file to recover the handover context (accomplished tasks, testing status, and configurations) from the previous conversation thread.
- Source functions: `load_approval_state()`, `load_dashboard_state()` in `session.py`.
- **DO NOT** scan `docs/` directories. Work item is read from `context.json` only.

### Step 5 — Read Cached Version + Provider + Usage

- **Version**: Read from `.agents/state/context.json` → `project_version` field. **NEVER** scan `package.json`, `go.mod`, `pyproject.toml`, `Cargo.toml`, or `MANIFEST.json`.
- **Provider**: Read from `.agents/state/context.json` or `dashboard.json` if available. Skip silently if not found (`optional`).
- **Usage**: Read from `.agents/state/context/usage.json` or `.agents/state/dashboard.json`. **NEVER** parse transcript files.
- **Environment**: Read from `.agents/state/environment.json`. If stale (>24h) → warn only, do not block. If missing → warn only.

### Step 6 — Write Initialization Summary

- Call `write_initialization_summary()` from `state_sync.py`.
- Write lightweight summary to `.agents/state/context.json`:
  - `guardrail_hashes`: SHA-256 hashes
  - `git`: branch, working_tree, is_repository
  - `checkpoint`: current checkpoint number
  - `resolved_dependencies`: summary from deps resolve
  - `init_completed_at`: ISO-8601 timestamp
  - `init_latency_ms`: measured latency
- Call `validate_no_heavy_init_operations()` — if any heavy op was triggered → log critical warning.
- Update `runtime.json`: `status: "completed"`, `checkpoint: 1`, `current_step: "Initialization Complete"`.

### Step 7 — Auto-Resume & Git Auto-Stash Recovery (Optional)

- Check for `.agents/runtime/context_snapshot.json`.
- If exists: restore checkpoint, skill, command, step from snapshot. If `git_stash_ref` present → prompt approval to run `git stash pop`. Delete snapshot after restore.
- Print: `✨ [SYSTEM]: Recovered SDLC context from thread rollover. Checkpoint restored to X.`

### Step 8 — Telegram Project Inbox Monitor

- Initialization may start the project-specific Telegram monitor process
  (`skills/notify-telegram/monitor_listener.py`) only when the shared Telegram daemon is already
  active. If the daemon is inactive, do not start a listener and do not schedule idle polling.
- The monitor watches the project-local `.agents/inbox/inbox.json` file so agents do not need to
  read Telegram inbox messages from outside the registered workspace.
- If a background timer/check is used, it must be silent on idle. When `.agents/inbox/inbox.json`
  is absent, unchanged, empty, or invalid JSON, the agent must not write a chat response and must
  not send a Telegram message.
- When the timer/check detects a new valid inbox JSON object, load the `notify-telegram` skill and
  process the event according to its Project Inbox Mode rules. If the event originated from
  Telegram, the final answer or completion status must be sent back to the event `chat_id` on
  Telegram before the turn is considered complete.

---


## ⛔ Removed Operations (FEAT-050)

The following operations were removed from this skill in v3.0.0 and must NEVER be re-added:

| Removed Step | Reason | Alternative |
|---|---|---|
| Full Project Memory load | Too slow (~2-5s), not needed at init | Use `memory: cached` or `memory: lazy` in specific skills |
| RAG connect + validate | Too slow, network I/O | Use `rag: cached` or `rag: lazy` in specific skills |
| Workspace scan (`docs/` scan for work item) | Filesystem I/O on every init | Read `work_item` from `context.json` only |
| `get_version_info()` (scans manifests) | Not needed at init | Read `project_version` from `context.json` |
| Validate documentation folders | Not needed at init | Handled by `environment-health` skill |
| Env CLI checks (`python --version`, `node --version`, etc.) | Slow subprocess calls — now automated by `workspace_doctor.py` | Consume `workspace_doctor` JSON report |
| `git describe --tags` | Forbidden at init | Version from `context.json` only |
| `sync_request_history()` | Expensive, async | Never during init; guarded by `usage: cached` |
| `parse_transcript()` | File I/O + parsing | Never during init |
| `refresh_context_usage_for_active_conversation()` | API call | Never during init |
| Write absolute workspace path | Path leakage | Always write `path: "."` |

---

## Output Format

```text
Workspace:
READY

Runtime:
SESSION_MODE

Workflow Supervisor:
READY
```

---

## 🔒 WORKFLOW RUNTIME INTERFACE

- Runtime tracking for this Skill is file-based. Update `.agents/state/runtime.json` atomically for
  start, step, completion, and failure states.
- Runtime cache refreshes must use `.agents/runtime/commands/runtime.request.json` when possible.
- If a direct CLI fallback is explicitly allowed, use `aiwf ...` commands. Do not instruct the Agent
  to call `python skills/workflow-runtime/scripts/workflow_runtime.py ...` directly during
  initialization.
