# Runtime Dependency Resolver — Developer Guide

> **FEAT-050** | Version 1.0 | Updated: 2026-07-11

---

## Overview

The **Runtime Dependency Resolver** (RDR) is the lazy-loading layer of the AIWF runtime. It allows every skill to explicitly declare what runtime context it needs, so the runtime loads only the required dependencies — never more.

This replaces the old model where `initialize-workflow` eagerly loaded everything (memory, RAG, environment, workspace scan) regardless of what the active skill actually needed.

---

## Quick Reference

```bash
# Inspect what a skill declares
python skills/workflow-runtime/scripts/workflow_runtime.py deps inspect --skill <name>

# Validate schema only (no actual loading)
python skills/workflow-runtime/scripts/workflow_runtime.py deps validate --skill <name>

# Resolve dependencies and write to .agents/state/runtime/dependencies.json
python skills/workflow-runtime/scripts/workflow_runtime.py deps resolve --skill <name>

# Scan all skills for missing/invalid declarations
python skills/workflow-runtime/scripts/workflow_runtime.py deps doctor

# Strict mode (missing = error)
python skills/workflow-runtime/scripts/workflow_runtime.py deps doctor-strict

# Auto-fix missing or deprecated declarations
python skills/workflow-runtime/scripts/workflow_runtime.py deps fix --skill <name>
python skills/workflow-runtime/scripts/workflow_runtime.py deps fix --all --yes
```

---

## Adding `runtime_requirements` to a SKILL.md

Every SKILL.md must declare a `runtime_requirements` block in its YAML frontmatter:

```yaml
---
name: my-skill
description: My skill description
runtime_requirements:
  rules: required
  state: required
  approvals: optional
  git: cached
  memory: cached
  rag: cached
  workspace_scan: none
  environment: cached
  version: cached
  provider: optional
  usage: cached
---
```

### Supported Keys

| Key | Description |
|---|---|
| `rules` | `AI_RULES.md` and `AGENTS.md` policy guardrails |
| `state` | Runtime state files (`context.json`, `workflow.json`, etc.) |
| `approvals` | Approval state (`approvals.json`) |
| `git` | Git branch and working tree status |
| `memory` | Project Memory (metadata or full load) |
| `rag` | RAG / vector database |
| `workspace_scan` | Filesystem scan of `docs/` or workspace |
| `environment` | Environment snapshot (`environment.json`) |
| `version` | Project version from `context.json` |
| `provider` | AI provider metadata |
| `usage` | Context usage summary |

### Supported Modes

| Mode | Behavior |
|---|---|
| `required` | Must be available — blocks execution if missing |
| `cached` | Read from cached JSON files only — no subprocess calls |
| `lazy` | Deferred — loaded only when first accessed with a query |
| `optional` | Loaded if available — warns only if missing |
| `none` | Not loaded at all — skip silently |

---

## Safety Rules

### Safety Keys
`rules` and `state` **must** be `required`. Setting them to `lazy`, `optional`, or `none` raises a `SafetyKeyViolationError`.

```yaml
# ✅ Correct
rules: required
state: required

# ❌ Blocked
rules: none
state: lazy
```

### workspace_scan Allowlist
Only these skills may set `workspace_scan: required`:
- `project-memory-bootstrap`
- `project-memory-update`
- `project-discovery`

All other skills must use `workspace_scan: none`.

### Deprecated Keys
These keys are deprecated and automatically migrated by `deps fix`:

| Deprecated | Replace With |
|---|---|
| `transcript_sync` | `usage` |
| `provider_usage` | `provider` |

---

## Safe Minimal Fallback

Skills **without** `runtime_requirements` receive the safe minimal fallback instead of full preload. This prevents lightweight initialization from being bypassed by legacy skills.

```yaml
# Applied automatically to legacy skills:
rules: required
state: required
approvals: optional
git: cached
memory: cached
rag: cached
workspace_scan: none
environment: cached
version: cached
provider: optional
usage: cached
```

> ⚠️ To prevent warnings, always add `runtime_requirements` explicitly. Run `deps fix --skill <name>` to add a safe template.

---

## Context Loader Functions

All loaders are in `dependency_resolver.py` and `validator.py`. They are **read-only** — no subprocess calls.

### Memory

```python
from dependency_resolver import load_memory_cached, load_memory_lazy

# Cached: reads memory-state.json + memory.config.json only (NO project-summary.md)
result = load_memory_cached()

# Lazy: defers loading until query is provided
result = load_memory_lazy(query="search term")
```

### RAG

```python
from dependency_resolver import load_rag_cached, load_rag_lazy

result = load_rag_cached()   # reads rag-state.json metadata only
result = load_rag_lazy(query="search term")  # deferred
```

### Version

```python
from dependency_resolver import load_version_cached

# Reads context.json only — NEVER scans package.json, go.mod, pyproject.toml, Cargo.toml
result = load_version_cached()
```

### Usage / Context

```python
from dependency_resolver import load_usage_cached

# Reads usage.json or dashboard.json — NEVER parses transcript files
result = load_usage_cached()
```

### Environment

```python
from validator import read_environment_snapshot

# Reads environment.json — NEVER runs python/node/docker --version
result = read_environment_snapshot()
# result["status"] = "cached" | "stale" | "missing"
# result["stale"] = True if >24h old
```

### Git (cached)

```python
from validator import get_git_info

# Runs EXACTLY 3 allowed commands:
#   git rev-parse --is-inside-work-tree
#   git branch --show-current
#   git status --short
# FORBIDDEN: git describe --tags, git remote -v, git fetch, git tag
info = get_git_info()
```

### Work Item (cached)

```python
from validator import detect_work_item_cached

# Reads context.json only — NEVER scans docs/ directories
item = detect_work_item_cached()
# {"type": "FEAT", "id": "FEAT-050", "title": "..."}
```

---

## Task Orchestration

The Runtime Dependency Resolver integrates with the Task Orchestrator to provide:

### Task Graph

```bash
# Build task graph from plan JSON
python skills/workflow-runtime/scripts/workflow_runtime.py task graph build --feature FEAT-XXX

# Show current status
python skills/workflow-runtime/scripts/workflow_runtime.py task graph status

# Get next recommended task
python skills/workflow-runtime/scripts/workflow_runtime.py task next
```

### Task State Machine

Valid states: `queued → waiting → ready → running → completed | failed | skipped | aborted`

```bash
# Apply a state transition
python skills/workflow-runtime/scripts/workflow_runtime.py task state transition <task_id> <new_state> --reason "..."
```

**Forbidden shortcuts** (always blocked):
- `queued → completed`
- `waiting → completed`
- `running → queued`
- `completed → running`

**Completion requires ALL of:**
1. `state == completed`
2. `verification_status ∈ {pass, not_configured}`
3. No active worker (`worker_id == null`)
4. No active locks (`lock_ids == []`)

### Phase Completion Gate

A phase is complete ONLY when **ALL** tasks in `phase.tasks` satisfy:
1. ✅ Exists in `tasks.json` ledger
2. ✅ `state == completed`
3. ✅ `verification_status ∈ {pass, not_configured}`
4. ✅ No unapproved skip (required tasks)
5. ✅ Not in any non-terminal state
6. ✅ No active workers or locks

> **Hard Rule**: "First blocker task complete" ≠ "Phase complete". 100% task coverage required.

---

## State Files

| File | Purpose |
|---|---|
| `.agents/state/runtime/dependencies.json` | Last resolved dependency result |
| `.agents/state/workflow/task_graph.json` | Task dependency graph with ready_queue |
| `.agents/state/workflow/tasks.json` | Task ledger — source of truth for completion |
| `.agents/state/context.json` | Cached version, work item, git state |
| `.agents/state/environment.json` | Environment snapshot (24h TTL) |
| `.agents/state/approvals.json` | Approval gate state |

---

## Initialize-Workflow Latency Contract

`initialize-workflow` must complete in **< 800ms**. This is enforced by:

1. No memory load (only metadata hashes)
2. No RAG connect (metadata only)
3. No workspace scan
4. Only 3 git commands (`rev-parse`, `branch --show-current`, `status --short`)
5. No manifest scanning for version
6. No transcript parsing for usage
7. No env CLI subprocess calls

```bash
# Verify init latency was within budget (shown in init output):
Init Latency: 245ms
```

---

## Troubleshooting

### "Missing required dependency: state"
`context.json` is missing. Run `initialize-workflow` first to create it.

### "SafetyKeyViolationError: rules cannot be 'none'"
You declared `rules: none` in `runtime_requirements`. Change to `rules: required`.

### "WorkspaceScanBlockedError"
Your skill tried to set `workspace_scan: required` but is not in the allowlist. Remove it or use `workspace_scan: none`.

### "Environment snapshot is stale (>24h)"
Run `environment-health` skill to refresh `environment.json`.

### "No runtime_requirements found for skill 'X'"
Run `deps fix --skill X` to add a safe template.

---

## See Also

- [initialize-workflow/SKILL.md](../../skills/initialize-workflow/SKILL.md) — Lightweight runtime initializer
- [ADR-005](../adr/ADR-005_runtime_dependency_resolver.md) — Architecture Decision Record
- [FEAT-050 Blueprint](../designs/FEAT-050_lightweight_runtime_initialization_blueprint.md) — Full design spec
