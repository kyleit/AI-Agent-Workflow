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
repository: https://gitlab.com/hngan.it/ai-workflow-skills
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
  usage: cached
---

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
| Run `git describe --tags`, `git remote -v`, `git fetch` | Only 3 allowed git commands |
| Run `python --version`, `node --version`, `docker version`, etc. | Forbidden — consume `workspace_doctor` JSON report instead |
| Parse transcript files or sync request history | `usage: cached` — read from `dashboard.json` or `context/usage.json` only |
| Call `sync_request_history()`, `parse_transcript()`, `refresh_context_usage_for_active_conversation()` | All forbidden during init |
| Write absolute paths to `.session.json` | Workspace `path` must always be `"."` |

### Allowed Git Commands (Exactly 3)

```bash
git rev-parse --is-inside-work-tree
git branch --show-current
git status --short
```

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

### Step 1 — Run Runtime Dependency Resolver

```bash
python skills/workflow-runtime/scripts/workflow_runtime.py deps resolve --skill initialize-workflow
```

- If resolution fails for a `required` dependency → **STOP**, print error, exit.
- If resolver warns about missing `runtime_requirements` in other skills → log warning, continue (safe_minimal fallback applies).
- Write resolution result to `.agents/state/runtime/dependencies.json`.

### Step 2 — Load Guardrails Summary (Hash-Based)

- Compute SHA-256 hash of `AI_RULES.md`, `.agents/AGENTS.md`, and active `SKILL.md`.
- Build `policy_flags` dict: `approval_gate`, `git_gate`, `blueprint_gate`, `release_gate`, `testing_gate`, `workspace_permission_gate`.
- **DO NOT** re-read or re-enforce full rule text — hash confirms integrity only.
- Source function: `load_guardrails_summary()` in `session.py`.

### Step 3 — Read Git State (Cached Only)

Run **exactly these 3 commands**, nothing more:

```bash
git rev-parse --is-inside-work-tree
git branch --show-current
git status --short
```

- Store result in session `git` field.
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

Resident Orchestrator:
DISABLED

Workflow Supervisor:
READY
```

---

## 🔒 WORKFLOW RUNTIME INTERFACE

- **Start**: `python skills/workflow-runtime/scripts/workflow_runtime.py start --skill "initialize-workflow" --command "init" --checkpoint 1 --step "Starting lightweight initialization..."`
- **Step Updates**: `python skills/workflow-runtime/scripts/workflow_runtime.py step --step "<desc>" --log "<msg>"`
- **Completion**: `python skills/workflow-runtime/scripts/workflow_runtime.py complete --checkpoint 1 --step "Initialization Complete" --next-skill "software-development-workflow" --next-command "workflow"`
- **Failure**: `python skills/workflow-runtime/scripts/workflow_runtime.py fail --step "<error_step>" --log "<error_details>"`
