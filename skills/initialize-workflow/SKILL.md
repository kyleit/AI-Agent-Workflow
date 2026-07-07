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
version: 2.6.0
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
- **Approval Gate Policy** (Section 1) - Seek explicit confirmation before modifying code or creating files.
- **Git Workflow Policy** (Section 2) - Perform branch checks and commits/tags/pushes only with approval.
- **Memory First Policy** (Section 3) - Consult project summary/memory before source files or user questions.
- **RAG Policy** (Section 4) - Follow retrieval sequence levels.
- **Artifact Policy** (Section 5) - Strictly follow path boundaries and naming formats.
- **Testing Policy** (Section 8) - Run compilation, build, and tests, halting on failures.
- **Workspace Permission Mode Policy** (Section 15) - Sandbox mode is default; ask user to choose sandbox or full_access at init.

## Multi-Agent Contract

Runs under the Multi-Agent Workflow. Respect agent ownership and handoff rules defined in [agents/](../../agents/) and [runtime/](../../runtime/).

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

### Step 0 — Start Initialization & Progressive Tracking
- Immediately write `.agents/.session.json` atomically (via `.session.json.tmp` rename) with:
  - `status`: `"in_progress"`
  - `checkpoint`: 1
  - `current_skill`: `"initialize-workflow"`
  - `current_command`: `"init"`
  - `current_step`: `"Starting workflow initialization..."`
  - `current_logs`: `["> Starting initialize-workflow..."]`
  - `updated_at`: (current ISO-8601 timestamp)

### Step 1 — Validate Workspace
- Confirm a project workspace is active and resolved as a relative path (e.g. `.`). If not, stop.
- Update session state: `current_step`: `"Validating workspace..."`, append `"> Validating workspace path..."` to `current_logs`.

### Step 2 — Load AGENTS.md & Centralized Policies
- Read `.agents/AGENTS.md` and load global rules.
- Locate and read the centralized policy definitions from `AI_RULES.md`.
- Update session state: `current_step`: `"Loading centralized policies..."`, append `"> Loading rules and policies..."` to `current_logs`.

### Step 3 — Load Project Memory Configuration
- Check for `.agents/memory.config.json` and load memory state. If unavailable, mark Memory Status as `Missing` and continue.
- Update session state: `current_step`: `"Loading memory config..."`, append `"> Reading memory.config.json..."` to `current_logs`.

### Step 4 — Connect and Validate RAG Store
- Verify RAG configuration and connect. Fallback to Markdown memory without failing if RAG is unavailable.
- Update session state: `current_step`: `"Connecting RAG store..."`, append `"> Connecting to vector search database..."` to `current_logs`.

### Step 5 — Validate Git State
- Check repository status. Detect active branch, working tree status (clean/dirty), remote URLs, default branch, and latest tag. Do NOT modify Git state.
- Update session state: `current_step`: `"Validating Git repository state..."`, append `"> Fetching current Git branch and status..."` to `current_logs`.

### Step 6 — Detect Active Work Item
- Scan `docs/` subdirectories (`brainstorming/`, `plans/`, `designs/`, `issues/`, `quick/`).
- Find the latest active feature/fix/quick prefix (`FEAT-XXX`, `FIX-XXX`, or `QUICK-XXX`) to identify the current work item.
- Update session state: `current_step`: `"Detecting active work item..."`, append `"> Scanning docs/ for active feature/fix IDs..."` to `current_logs`.

### Step 7 — Detect Current Project Version
- Detect version strings from config files: `package.json`, `pyproject.toml`, `go.mod`, `Cargo.toml`, or `MANIFEST.json`.
- Update session state: `current_step`: `"Detecting project version..."`, append `"> Reading version string from manifest..."` to `current_logs`.

### Step 8 — Validate Documentation Directory Structure
- Verify that standard folders exist: `docs/brainstorm/`, `docs/plans/`, `docs/designs/`, `docs/issues/`, `docs/quick/`, `docs/adr/`, `docs/releases/`, `docs/debug/`, `docs/verification/`, and `docs/archive/`. Report missing directories.
- Update session state: `current_step`: `"Validating documentation folders..."`, append `"> Verifying standard documentation layout..."` to `current_logs`.

### Step 9 — Validate Environment Tools
- Test execution of: `git`, `python`, `node`, `go`, `docker`, `tree-sitter`, `qdrant`, `qmd`, `ollama`. Do not auto-install; only report availability.
- Update session state: `current_step`: `"Checking environment tools..."`, append `"> Checking CLI tool versions (git, node, python...)..."` to `current_logs`.

### Step 10 — Create Session State File & Permission Selection (Finalize)
- Prompt the user to select the Workspace Permission Mode (Sandbox Mode vs Full Access Mode vs Unrestricted Mode) during initialization:
  ```bash
  python3 .agents/skills/workflow-runtime/scripts/workflow_runtime.py prompt select --question "Choose workspace permission mode:" --options "sandbox|full_access|unrestricted" --default "sandbox"
  ```
- Based on the user choice:
  - If choice is `1` (or sandbox): set `permission_mode = "sandbox"`.
  - If choice is `2` (or full_access): set `permission_mode = "full_access"`.
  - If choice is `3` (or unrestricted):
    - Display danger zone warning and ask for `CONFIRM_UNRESTRICTED`.
    - If user inputs correctly: set `permission_mode = "unrestricted"`.
    - Else: fallback to `sandbox`.
  - Otherwise, default/fallback to `sandbox`.
- Perform final atomic update of `.agents/.session.json` (via `.session.json.tmp` rename):
  - Set `checkpoint` to `1` (Initialization Complete).
  - Set `status` to `"completed"`.
  - Set `current_step` to `"Initialization Complete"`.
  - Set `permission_mode` to the selected mode.
  - Set `permission_mode_selected_at` to current ISO-8601 timestamp.
  - Set `permission_mode_selected_by` to `"user"`.
  - Append `"> System initialization finished successfully."` to `current_logs`.
  - Update `suggested_next_skill` to `"software-development-workflow"` and `suggested_next_command` to `"workflow"`.
  - Ensure all gathered git, version, work_item, memory, and rag fields are written in their nested slots.
  - **Conversation ID Recording**: Retrieve the active `Conversation ID` from `user_information` in the environment metadata and save it to the `"conversation_id"` string field inside `.session.json`, preserving it if already set.
  - **Context Usage Token Estimation**: Estimate the current conversation's token count from the active transcript file size (at `<appDataDir>/brain/<conversation_id>/.system_generated/logs/transcript.jsonl` using `fileSize / 3` as an approximation) and write it to the `"context_usage"` object.
  - **CRITICAL**: The `"path"` field of the `"workspace"` object in `.agents/.session.json` MUST be exactly `"."` (a relative path representation to prevent path leakage). Under no circumstances should an absolute path be written.

### Step 11 — Auto-Resume & Git Auto-Stash Recovery (Rollover Mechanism)
- Prior to finalizing initialization, the AI Agent **MUST** check for the existence of `.agents/runtime/context_snapshot.json`.
- If the snapshot file exists:
  1. Read the snapshot data (extract `checkpoint`, `current_skill`, `current_command`, `current_step`, `git_stash_ref`).
  2. Overwrite the corresponding fields in `.agents/.session.json` with the snapshot data to restore the state from the previous thread.
  3. If `git_stash_ref` is present and not empty, the Agent **MUST** run (or instruct/ask approval to run):
     ```bash
     git stash pop
     ```
     to restore any unstaged code changes.
  4. Delete the `.agents/runtime/context_snapshot.json` file immediately to prevent duplicate recovery loops.
  5. Print a clear recovery confirmation notice to the user:
     `✨ [SYSTEM]: Recovered SDLC context from thread rollover. Checkpoint restored to X, Git changes unstashed.`

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
