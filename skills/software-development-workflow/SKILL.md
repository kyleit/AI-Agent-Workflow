---
name: software-development-workflow
command: workflow
aliases:
  - flow
  - status
category: workflow
tags:
  - workflow
  - status
  - orchestrator
version: 2.5.0
author:
  name: Kyle Dang
  email: kyleit@klexpress.net
  website: https://www.klexpress.net
license: MIT
repository: https://gitlab.com/hngan.it/ai-workflow-skills
created_at: 2026-07-03
updated_at: 2026-07-03
description: Pure Workflow Orchestrator for the AI Coding Platform. Inspects environment health, project memory state, and SDLC artifact state to determine the current phase, trace Feature IDs in FEAT-001 format, check ADR dependencies, and recommend the single correct next Skill. Read-only.
---

# Skill: Software Development Workflow Orchestrator (FEAT-XXX format & ADR support)

## Purpose

This Skill is the **central coordinator** of the entire AI Coding Platform. It acts as a **Project Manager**, not a Software Engineer.

Its main responsibilities are:
1. Inspect the state of the environment, project memory, and SDLC directories.
2. Scan `docs/brainstorm/` to determine the latest **Feature ID** using the `FEAT-XXX` format (e.g., `FEAT-001`, `FEAT-002`).
3. Trace the status of the current active feature by checking downstream artifacts (`docs/plans/`, `docs/designs/`, `docs/adr/`) that share the same Feature ID.
4. Recommend the single correct next Skill to run.
5. Stop immediately.

It does NOT perform any engineering work, code modification, or file writing.

---

## AI Coding Platform SDLC Layers (FEAT-XXX format)

This Skill coordinates all phases of a feature's lifecycle:

```
Platform Infrastructure & Knowledge
  Layer 1 — Environment (environment-bootstrap, environment-health)
  Layer 2 — Knowledge (project-memory-bootstrap, project-memory-update, project-rag-search)

Feature-Centric SDLC (Reusing Feature ID 'FEAT-XXX')

  Option 1: Standard Workflow (Medium & Large Features)
    1. Brainstorming     ──> docs/brainstorm/FEAT-XXX_<feature_name>.md
                             Skill: brainstorming
    2. Planning          ──> docs/plans/FEAT-XXX_<feature_name>_plan.md
                             Skill: brainstorming-to-plan
    3. Design            ──> docs/designs/FEAT-XXX_<feature_name>_blueprint.md
                             Skill: plan-to-blueprint
    [Optional] ADR       ──> docs/adr/ADR-XXX_<short_title>.md
                             Skill: create-adr
    4. Implementation    ──> source code implementation
                             Skill: blueprint-to-implementation
    [Optional] Visual    ──> docs/verification/FEAT-XXX_visual_debug.md
       Debugging             Skill: frontend-visual-debug
                             (Required for Frontend features, skipped for Backend-only)
    5. Release           ──> updates CHANGELOG.md & bumps version
                             Skill: implementation-to-release

    Workflow Paths:
    - Frontend Features:     implementation ──> debug ──> visual-debug ──> verify ──> release
    - Backend-Only Features:  implementation ──> debug ──> verify ──> release

  Option 2: Quick-Fix Workflow (Small & Low-Risk Bug Fixes)
    1. Quick-Fix Check   ──> classify issue and estimate scope
                             Skill: quick-fix
    2. Implementation    ──> apply minimal hotfix & verify builds
                             Skill: quick-fix
    3. Release           ──> updates CHANGELOG.md & bumps version
                             Skill: implementation-to-release

  Option 3: Quick-Feature Workflow (Small & Low-Risk Feature Requests)
    1. Quick Feature Check ──> classify request and estimate scope
                             Skill: quick-feature
    2. Implementation    ──> apply minimal feature code & verify
                             Skill: quick-feature
    3. Release           ──> updates CHANGELOG.md & bumps version
                             Skill: implementation-to-release
```

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

## Decision Tree

Execute checks in this strict order. **Stop at the first check that returns a recommendation.**

```
Step 0 — Workflow Initialization Check
        ↓
Step 1 — Environment Health Check
        ↓
Step 2 — Project Memory Check
        ↓
Step 3 — Feature & Workflow Detection (Trace Feature ID)
        ↓
Step 4 — Generate Recommendation
        ↓
STOP
```

---

## Step 0 — Workflow Runtime & Initialization Check

This Skill assumes `initialize-workflow` and `workflow-runtime` have completed.
Before executing, inspect `.agents/.session.json` and perform the **Runtime Health Check**, **Drift Detection**, and **Checkpoint Verification** (Section 1 & 2 of `workflow-runtime`).
Verify that the current checkpoint in `.session.json` is at least `1` (Initialization Complete).
1. If the session file is missing, if context health is `broken` (e.g. active branch or work item has drifted), or if the current checkpoint is less than `1`:
   * **Recommend next Skill**: `initialize-workflow` or `workflow-runtime` (to resume)
   * Stop.
2. At the start of execution, write `.session.json` atomically (via `.session.json.tmp` rename) with:
   - `status`: `"in_progress"`
   - `current_skill`: `"software-development-workflow"`
   - `current_command`: `"workflow"`
   - `current_step`: `"Starting workflow orchestration checks..."`
   - `current_logs`: `["> Starting software-development-workflow..."]`
   - `updated_at`: (current ISO-8601 timestamp)
3. During major steps of execution (checking environment health, checking memory staleness, classifying features, tracing documents, checking quality gates), update `.session.json` progressively by updating `current_step` and appending detailed step descriptions to `current_logs`.
4. Upon generating a final recommendation, write `.session.json` atomically (via `.session.json.tmp` rename):
   - Set `status` to `"completed"`.
   - Set `current_step` to `"Workflow Orchestrated"`.
   - Update `suggested_next_skill` and `suggested_next_command` with the recommended skill/command.
   - Append `"> Recommendation generated: [skill-name]."` and `"> Workflow orchestration complete."` to `current_logs`.
5. If execution fails, write `.session.json` atomically with `status`: `"failed"` and append the failure details to `current_logs`.


---

## Step 1 — Environment Health Check

Perform lightweight checks on required tools (Git, Python, Node, SQLite, Tree-sitter).
If required tools are missing (Environment Status: `CRITICAL`):
* **Recommend next Skill**: `environment-bootstrap`

---

## Step 2 — Project Memory Check

Check for `.agents/memory.config.json` and `<memory_root>/project-summary.md`.
If missing:
* **Recommend next Skill**: `project-memory-bootstrap`

Check memory staleness in `memory-state.json`. If memory is older than 7 days (`STALE` or `VERY STALE`):
* **Recommend next Skill**: `project-memory-update`

---

## Step 3 — Feature & Workflow Detection (FEAT-XXX format)

To support feature traceability, the orchestrator tracks progress by scanning the project's documentation.

### 3.1 — Detect Active Feature ID, Quick-Fix, or Quick-Feature Eligibility

Before commencing a new feature cycle, classify the requested `task_description` (if provided) to determine if it is eligible for the parallel **Quick-Fix** or **Quick-Feature** tracks.

1. **Quick-Fix Classification**: If the user has provided a `task_description`, check if it qualifies as a Quick-Fix (low risk, small bug fix, e.g. 404 Route, Cannot POST, Null Pointer, Wrong SQL, Typo, Validation Bug, Configuration Error, Wrong Permission, Small UI Bug):
   - If it qualifies:
     * **Recommend next Skill**: `quick-fix`
     * **Required Input**: `issue: <task_description>`
     * Stop.
2. **Quick-Feature Classification**: If it does not qualify for Quick-Fix, check if it qualifies for a Quick-Feature (low risk, small feature request, e.g. Add one API endpoint, Add one button, Add one dialog, Add one filter, Add one validation, Add one search field, Add one export function, Add one configuration option):
   - If it qualifies:
     * **Recommend next Skill**: `quick-feature`
     * **Required Input**: `feature: <task_description>`
     * Stop.
3. **Scan documentation**: If it does not qualify for either (or if `task_description` is empty/new standard feature), scan the `docs/brainstorm/` directory. Ignore `docs/plans/`, `docs/designs/`, `docs/adr/`, Project Memory, Git History, and `CHANGELOG.md` for ID allocation.
4. Find all markdown files matching the pattern `docs/brainstorm/FEAT-XXX_*.md` (where `XXX` is a 3-digit numeric prefix).
5. If no matching files exist or the directory contains only placeholder files (like `.gitkeep`):
   - Set **Next Feature ID** to `FEAT-001`.
   - **Recommend next Skill**: `brainstorming` (to start Feature `FEAT-001` standard workflow).
   - Stop.
6. Otherwise, identify the file with the highest numerical suffix in `FEAT-XXX` as the **Active Feature**. Let this ID be `FEAT-XXX` and the feature slug be `<feature_name>`.

### 3.2 — Trace Feature Lifecycle Status
Once the Active Feature `FEAT-XXX` and name `<feature_name>` are identified, trace its lifecycle artifacts:

#### Case 0: Project Profile Missing
If the project configuration profile `.agents/project-profile.json` does NOT exist:
* **Recommend next Skill**: `project-discovery` (command: `/discover`)
* **Note**: Run project-discovery first to scan the tech stack and generate the dynamic checkpoints configuration.
* Stop.

#### Case A: Brainstorming File Incomplete / Discovery Phase
If `docs/brainstorm/FEAT-XXX_<feature_name>.md` exists but the Requirement Readiness Score is below 85, or the document indicates active discovery questions are pending:
* **Recommend next Skill**: `brainstorming` (to continue interactive discovery).
* Stop.

#### Case B: Plan Missing
If `docs/brainstorm/FEAT-XXX_<feature_name>.md` is complete (Readiness Score >= 85) but the corresponding implementation plan `docs/plans/FEAT-XXX_<feature_name>_plan.md` does NOT exist:
* **Recommend next Skill**: `brainstorming-to-plan`
* **Required Input**: `prompt_file: docs/brainstorm/FEAT-XXX_<feature_name>.md`
* Stop.

#### Case C: Design Blueprint Missing
If the implementation plan `docs/plans/FEAT-XXX_<feature_name>_plan.md` exists but the corresponding technical blueprint `docs/designs/FEAT-XXX_<feature_name>_blueprint.md` does NOT exist:
* **Recommend next Skill**: `plan-to-blueprint`
* **Required Input**: `source_plan: docs/plans/FEAT-XXX_<feature_name>_plan.md`
* Stop.

#### Case D: ADR Assessment and Creation
If the technical blueprint `docs/designs/FEAT-XXX_<feature_name>_blueprint.md` exists, inspect its `Architecture Decision Assessment` section.
* If the blueprint specifies `ADR Required: Yes` and no corresponding ADR file exists in `docs/adr/` referencing this Feature ID:
  * **Recommend next Skill**: `create-adr`
  * **Required Input**: `title: <suggested title>, related_feature: docs/brainstorm/FEAT-XXX_<feature_name>.md, design_file: docs/designs/FEAT-XXX_<feature_name>_blueprint.md`
  * Stop.

#### Case E: Implementation Incomplete
If the technical blueprint exists (and any required ADR exists in `docs/adr/`), inspect git status to determine if source code implementation is complete.
If git shows modified files or implementation commits are still in progress:
* **Recommend next Skill**: `blueprint-to-implementation`
* **Required Input**: `design_file: docs/designs/FEAT-XXX_<feature_name>_blueprint.md`
* **Note**: Remind the agent that the **Pre-Implementation Git Gate** must be run before modifications begin.
* Stop.

#### Case F: Debug Phase
If implementation is complete, check if the debug report `docs/debug/FEAT-XXX_debug.md` exists and is marked as `PASS`.
If it does not exist or has `status: FAIL`:
* **Recommend next Skill**: `implementation-to-debug`
* **Required Input**: `design_file: docs/designs/FEAT-XXX_<feature_name>_blueprint.md`
* Stop.

#### Case G: Dynamic Quality Gates (Visual Debug, E2E, DB Migrations)
If the debug report exists and is marked as `PASS`, read `.agents/project-profile.json` to identify applicable quality gates:
1.  **Visual Debugging Gate** (Frontend, Desktop, or Mobile):
    - If the project profile indicates `"visual_debug": { "required": true }`:
      - Check if the visual debug report `docs/verification/FEAT-XXX_visual_debug.md` exists and has `status: PASS` or `status: PARTIAL`.
      - If it does not exist, or has `status: FAIL`:
        - **Recommend next Skill**: `frontend-visual-debug` (or stack-specific UI debug skill).
        - **Required Input**: `design_file: docs/designs/FEAT-XXX_<feature_name>_blueprint.md`, `debug_report: docs/debug/FEAT-XXX_debug.md`
        - Stop.
2.  **Browser E2E Gate**:
    - If `playwright` or `cypress` is in `"quality_gates"`:
      - Check if E2E test report `docs/verification/FEAT-XXX_e2e.md` exists and has `status: PASS`.
      - If not, **Recommend next Skill**: `browser-e2e` (or equivalent QA command).
      - Stop.
3.  **Database Migration Gate**:
    - If `db_migration_check` is in `"quality_gates"`:
      - Check if database migration report `docs/verification/FEAT-XXX_db_verify.md` exists and has `status: PASS`.
      - If not, **Recommend next Skill**: `db-migration-check`.
      - Stop.

#### Case H: Verification Phase
If the debug report exists and is marked as `PASS` (and all applicable dynamic quality gates in Case G have passed), check if the verification report `docs/verification/FEAT-XXX_verify.md` exists and is marked as `PASS`.
If it does not exist or has `status: FAIL`:
* **Recommend next Skill**: `debug-to-verify`
* **Required Input**: `design_file: docs/designs/FEAT-XXX_<feature_name>_blueprint.md`, `debug_report: docs/debug/FEAT-XXX_debug.md`
* Stop.

#### Case I: Release Pending
If the verification report exists and is marked as `PASS`, check if the changes are committed, changelogs are updated, and version files bumped according to `.agents/release.config.json`.
If there are uncommitted/unpushed changes or `CHANGELOG.md` files do not list the new version/feature:
* **Recommend next Skill**: `implementation-to-release`
* **Note**: Remind the agent that `.agents/release.config.json` governs the modules, versions, and tag formats, and that release checks must be executed.
* Stop.

#### Case J: Post-Release Memory Update
If release is complete (changes pushed, tags created), check if project memory has been updated since the release commits.
If commits are newer than `last_updated_at` in `memory-state.json`:
* **Recommend next Skill**: `project-memory-update`
* Stop.

---

#### Case K: Feature Cycle Complete
If the release and memory sync are complete, and git is clean:
* Evaluate `task_description` (if provided):
  - If it qualifies for Quick-Fix:
    * **Recommend next Skill**: `quick-fix`
    * **Required Input**: `issue: <task_description>`
    * Stop.
  - If it qualifies for Quick-Feature:
    * **Recommend next Skill**: `quick-feature`
    * **Required Input**: `feature: <task_description>`
    * Stop.
  - Otherwise:
    * Increment the highest prefix to determine the next Feature ID (e.g., `FEAT-XXX` + 1).
    * **Recommend next Skill**: `brainstorming` (to start the new feature cycle standard workflow).
    * Stop.

---

## Step 4 — Output Format

Print the orchestration report using this layout:

```text
Current Phase:
Workflow Orchestration

Status:
Completed

Environment Status:
- Status:      [HEALTHY | WARNING | CRITICAL]
- Git:         [vX.X | MISSING]
- Python:      [3.X | MISSING]
- Node.js:     [vXX | MISSING]
- SQLite:      [3.X | MISSING]
- Tree-sitter: [vX.X | MISSING]

Memory Status:
- Status:       [FRESH | STALE | NOT GENERATED]
- Config:       [valid | missing]
- Last Updated: [ISO8601 | N/A]

Workflow State:
- Active Feature ID: [FEAT-XXX] - [Feature Name] (or [None - Quick-Fix / Quick-Feature Track Active])
- Brainstorming:  [exists: docs/brainstorm/FEAT-XXX_... | missing]
- Plan:           [exists: docs/plans/FEAT-XXX_... | missing]
- Blueprint:      [exists: docs/designs/FEAT-XXX_... | missing]
- ADR:            [exists: docs/adr/ADR-... | required but missing | not required]
- Implementation: [detected | in progress | pending]
- Memory Sync:    [up to date | outdated]
- Release:        [released | pending | not started]

Completed Phases:
- [x] Requirement Discovery (docs/brainstorm/FEAT-XXX_*.md)
- [x] Technical Planning (docs/plans/FEAT-XXX_*_plan.md)
- [/] Technical Design (docs/designs/FEAT-XXX_*_blueprint.md)
- [ ] ADR Creation (docs/adr/ADR-*.md)
- [ ] Implementation (source code)
- [ ] Release (CHANGELOG.md)

Recommended Next Skill:
[skill-name]

Reason:
[Specific reason citing missing artifact or state for Feature FEAT-XXX]

Required Input:
[yaml mapping of parameters needed by the skill]

Expected Output:
[Expected output file path and format]

Next Checkpoint:
[What files/states to inspect next]

Workflow Paused.
Waiting for user to invoke: [skill-name]
```

---

## Skill Parameters

```yaml
workspace: auto
# Current project directory

check_environment: true
# Include environment health check

check_memory: true
# Include memory state check

check_workflow: true
# Include SDLC/Fast-Fix workflow state detection

task_description: auto
# Optional description of the issue or feature request to evaluate for Fast-Fix eligibility.
```

---

## Completion Contract

```text
### Software Development Workflow Orchestrator

Phase:   Workflow Orchestration
Status:  Completed

[Full status report as per Output Format above]

Recommended Next Skill: [skill-name]

Workflow Paused.
```
