---
name: initialize-workflow
command: init
aliases:
  - initialize
category: runtime
tags:
  - initialization
  - bootstrap
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
description: Mandatory entry point for the AI Engineering Workflow. Performs system initialization, loads project rules/policies, loads project memory/RAG, validates Git state, detects current active work item and project version, verifies environment tools, and builds the unified execution context. Read-only.
---

# Skill: initialize-workflow (AI Workflow Initialization Layer)

---

## 🔒 GLOBAL POLICY REFERENCES

This Skill MUST strictly adhere to the global policies defined in [AI_RULES.md](../../AI_RULES.md):
- **Memory First Policy** (Section 3) - Build and load the execution context to support memory-first operations.
- **RAG Policy** (Section 4) - Initialize retrieval sequence connections.
- **Artifact Policy** (Section 5) - Validate directory layout structure.

**No Approval Gate is required because this Skill is completely read-only and makes no file or Git modifications.**

---

## Multi-Agent Contract

This Skill runs under the Multi-Agent Workflow.
It must respect agent ownership and handoff rules defined in:
- [agents/](../../agents/)
- [runtime/](../../runtime/)

---

## Purpose

The **initialize-workflow** Skill is the mandatory entry point of the entire AI Engineering Workflow. It executes first to compile a single, unified runtime context so that subsequent Skills do not duplicate environment-checking, rule-loading, and Git-verifying checks.

---

## Workflow Sequence

```
Step 1:  Validate Workspace
         ↓
Step 2:  Load AGENTS.md & Centralized Policies (AI_RULES.md)
         ↓
Step 3:  Load Project Memory Configuration
         ↓
Step 4:  Connect and Validate RAG Store
         ↓
Step 5:  Validate Git State & Current Branch
         ↓
Step 6:  Detect Active Work Item (FEAT, FIX, or QUICK)
         ↓
Step 7:  Detect Current Project Version
         ↓
Step 8:  Validate Documentation Directory Structure
         ↓
Step 9:  Validate Environment Tools
         ↓
Step 10: Build and Print Execution Summary
```

---

## Detailed Step Instructions

### Step 1 — Validate Workspace
- Confirm a project workspace is active and resolved as a relative path (e.g. `.`). If not, stop.

### Step 2 — Load AGENTS.md & Centralized Policies
- Read `.agents/AGENTS.md` and load global rules.
- Locate and read the centralized policy definitions from `AI_RULES.md`.

### Step 3 — Load Project Memory Configuration
- Check for `.agents/memory.config.json` and load memory state. If unavailable, mark Memory Status as `Missing` and continue.

### Step 4 — Connect and Validate RAG Store
- Verify RAG configuration and connect. Fallback to Markdown memory without failing if RAG is unavailable.

### Step 5 — Validate Git State
- Check repository status. Detect active branch, working tree status (clean/dirty), remote URLs, default branch, and latest tag. Do NOT modify Git state.

### Step 6 — Detect Active Work Item
- Scan `docs/` subdirectories (`brainstorming/`, `plans/`, `designs/`, `issues/`, `quick/`).
- Find the latest active feature/fix/quick prefix (`FEAT-XXX`, `FIX-XXX`, or `QUICK-XXX`) to identify the current work item.

### Step 7 — Detect Current Project Version
- Detect version strings from config files: `package.json`, `pyproject.toml`, `go.mod`, `Cargo.toml`, or `VERSION`.

### Step 8 — Validate Documentation Directory Structure
- Verify that standard folders exist: `docs/brainstorm/`, `docs/plans/`, `docs/designs/`, `docs/issues/`, `docs/quick/`, `docs/adr/`, `docs/releases/`, `docs/debug/`, `docs/verification/`, and `docs/archive/`. Report missing directories.

### Step 9 — Validate Environment Tools
- Test execution of: `git`, `python`, `node`, `go`, `docker`, `tree-sitter`, `qdrant`, `qmd`, `ollama`. Do not auto-install; only report availability.

### Step 10 — Create Session State File
- Generate or update `.agents/.session.json` containing the gathered workspace, branch, version, work item, memory, and RAG status, setting the checkpoint to `1` (Initialization Complete) and `"status"` to `"completed"`.
- **Conversation ID Recording**: Retrieve the active `Conversation ID` from `user_information` in the environment metadata and save it to the `"conversation_id"` string field inside `.session.json`.
- **Context Usage Token Estimation**: Estimate the current conversation's token count from the active transcript file size (at `<appDataDir>/brain/<conversation_id>/.system_generated/logs/transcript.jsonl` using `fileSize / 3` as an approximation). Write this to the `"context_usage"` field inside `.session.json` (`total_tokens`, `limit_tokens: 2000000`, `percentage`).
- **CRITICAL**: The `"path"` field of the `"workspace"` object in `.agents/.session.json` MUST be exactly `"."` (a relative path representation to prevent path leakage). Under no circumstances should an absolute path be written.

---

## Output Format

```text
Current Phase:
Workflow Initialization

Status:
Completed

Workspace:
- Path: [relative path (e.g. .)]
- Valid: Yes

Policies Loaded:
- Approval Gate Policy: Yes
- Git Workflow Policy: Yes
- Memory First Policy: Yes
- RAG Policy: Yes
- Artifact Policy: Yes
- Versioning Policy: Yes
- Documentation Policy: Yes
- Testing Policy: Yes
- Release Policy: Yes

Memory Status:
- Status: [FRESH | STALE | MISSING]
- Last Updated: [ISO8601 | N/A]

RAG Connection:
- Connected: [Yes | No (Fallback to Markdown Memory)]

Git Status:
- Branch: [branch-name]
- Working Tree: [clean | dirty]
- Default Branch: [main | master | etc.]
- Latest Tag: [vX.Y.Z | none]

Current Work Item:
- Type: [FEAT | FIX | QUICK | None]
- ID: [FEAT-XXX | FIX-XXX | QUICK-XXX | None]
- Title: [Title of the active item]

Current Version:
- Version: [x.y.z]
- Source: [go.mod | package.json | etc.]

Environment Status:
- Git: [available | missing]
- Python: [available | missing]
- Node: [available | missing]
- Go: [available | missing]
- Docker: [available | missing]

Documentation Status:
- Missing Folders: [None | list of missing folders]

Recommended Next Skill:
[software-development-workflow | user-requested-skill]

Workflow Paused.
```
