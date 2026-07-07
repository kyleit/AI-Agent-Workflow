---
name: software-development-workflow
command: workflow
aliases:
  - flow
  - status
category: workflow
tags:
  - workflow
  - lifecycle
  - engineering
version: 4.1.0
author:
  name: Kyle Dang
  email: kyleit@klexpress.net
  website: https://www.klexpress.net
license: MIT
repository: https://gitlab.com/hngan.it/ai-workflow-skills
created_at: 2026-07-03
updated_at: 2026-07-06
description: Pure Workflow Orchestrator. Evaluates checkpoints and ensures Blueprint execution and manual Release gates.
---

# Skill: Software Development Workflow Orchestrator (Blueprint-Driven & Explicit Release)

## Purpose

This Skill is the **central coordinator** of the entire AI Coding Platform. It acts as a **Project Manager** to determine the current phase, verify Quality Gates, check Blueprint approvals, perform raw request classification, and recommend the single correct next Skill to run.

It does NOT perform any engineering work, code modification, or file writing.

---

## AI Coding Platform SDLC Layers (FEAT-XXX / FIX-XXX / QUICK-XXX)

This Skill coordinates all phases of a feature's lifecycle:

```
Platform Infrastructure & Knowledge
  Layer 1 — Environment (environment-bootstrap, environment-health)
  Layer 2 — Knowledge (project-memory-bootstrap, project-memory-update, project-rag-search)

Feature-Centric SDLC (Enforcing Blueprint-Driven Development)

  Option 1: Standard Workflow (Medium & Large Features)
    1. Brainstorming     ──> docs/brainstorm/FEAT-XXX_<feature_name>.md
                             Skill: brainstorming
    2. Planning          ──> docs/plans/FEAT-XXX_<feature_name>_plan.md
                             Skill: brainstorming-to-plan
    3. Design            ──> docs/designs/FEAT-XXX_<feature_name>_blueprint.md
                             Skill: plan-to-blueprint
    [Optional] ADR       ──> docs/adr/ADR-XXX_<short_title>.md
                             Skill: create-adr
    4. Design Approval   ──> Seek User Y/N Confirmation for Blueprint
    5. Implementation    ──> source code implementation
                             Skill: blueprint-to-implementation
    6. Debug             ──> docs/debug/FEAT-XXX_debug.md
                             Skill: implementation-to-debug
    7. Verification      ──> docs/verification/FEAT-XXX_verify.md
                             Skill: debug-to-verify
    8. STOP              ──> Pause and recommend Release.
    9. Manual Release    ──> updates CHANGELOG.md & bumps version
                             Skill: implementation-to-release (only if explicitly requested)

  Option 2: Quick-Fix Workflow (Small Bug Fixes - 3-stage)
    1. Fix Specification ──> docs/issues/FIX-XXX_<issue_name>.md
                             Skill: quick-fix
    2. Spec Approval     ──> Seek User Y/N Confirmation
    3. Technical Design  ──> docs/designs/FIX-XXX_<issue_name>_blueprint.md
                             Skill: quick-fix
    4. Design Approval   ──> Seek User Y/N Confirmation for Blueprint
    5. Implementation    ──> apply minimal hotfix & verify builds
                             Skill: quick-fix
    6. Verification      ──> docs/verification/FIX-XXX_verify.md
    7. STOP              ──> Pause and recommend Release.
    8. Manual Release    ──> updates CHANGELOG.md & bumps version (only if explicitly requested)

  Option 3: Quick-Feature Workflow (Small Feature Requests - 3-stage)
    1. Feature Spec      ──> docs/quick/QUICK-XXX_<feature_name>.md
                             Skill: quick-feature
    2. Spec Approval     ──> Seek User Y/N Confirmation
    3. Technical Design  ──> docs/designs/QUICK-XXX_<feature_name>_blueprint.md
                             Skill: quick-feature
    4. Design Approval   ──> Seek User Y/N Confirmation for Blueprint
    5. Implementation    ──> apply minimal feature code & verify
                             Skill: quick-feature
    6. Verification      ──> docs/verification/QUICK-XXX_verify.md
    7. STOP              ──> Pause and recommend Release.
    8. Manual Release    ──> updates CHANGELOG.md & bumps version (only if explicitly requested)
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
- **Explicit Release Policy** (Section 9) - Never release automatically.
- **Blueprint Mandatory Execution Policy** (Section 13) - Enforce Blueprint approval for implementation.
- **Skill Suggestion Gate Policy** (Section 14) - Enforce suggestion and confirmation for raw user requests.
- **Workspace Permission Mode Policy** (Section 15) - Sandbox mode is default; ask user to choose sandbox or full_access at init.

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
Step 2.5 — Skill Suggestion Gate (Classification Check)
        ↓
Step 3 — Feature & Workflow Detection (Trace Feature ID)
        ↓
Step 4 — Generate Recommendation
        ↓
STOP
```

---

## Step 2.5 — Skill Suggestion Gate (Classification Check)

If the user has provided a raw request without explicitly calling a Command (like `/workflow`, `/brainstorm`, `/quick-fix`, `/quick-feature`, `/blueprint`, `/implement`, or `/release`), the AI must not proceed immediately.

### 2.5.1 — Classification Matrix
Classify the request using this matrix:
* **quick-fix**: Keywords: bug, error, exception, broken UI, wrong behavior, failed command, small regression, typo causing failure, config mismatch, simple validation bug.
* **quick-feature**: Keywords: add small button, add small API endpoint, add filter/search/export, add config option, add field, add small UI block, small behavior improvement, low-risk single-module feature.
* **brainstorming**: Keywords: new system, new module, new workflow, architecture change, database design, multi-service change, unclear requirement, business logic redesign, high uncertainty.
* **project-rag-search**: Keywords: user asks about existing architecture, where something is implemented, dependency/ownership questions, "how does this project handle X?".
* **project-memory-update**: Keywords: refresh memory, sync memory, after implementation, after major file changes.
* **project-memory-bootstrap**: Keywords: initialize memory, bootstrap memory when no memory exists.
* **implementation-to-release**: Keywords: release, tag, version bump, changelog update, git push. (Suggest ONLY if explicitly requested).

### 2.5.2 — Suggestion Output
* If `suggestion_gate.status` is `waiting_for_user_confirmation` and user input is not confirmation, keep waiting.
* If user confirms (via `Y`, `Yes`, `Proceed`, `Continue` or option number), clear suggestion gate or update status to `confirmed` and proceed to step 3.
* Otherwise, output the correct suggestion layout (Single recommendation or Multiple options) and STOP.

---

## Step 3 — Feature & Workflow Detection

### 3.1 — Detect Active Feature ID & Track Eligibility

1. **Scan documentation**: Scan `docs/brainstorm/FEAT-XXX_*.md`.
2. Find the file with the highest numerical suffix in `FEAT-XXX` as the **Active Feature**. Let this ID be `FEAT-XXX`.

### 3.2 — Trace Feature Lifecycle Status

#### Case C: Design Blueprint Missing
If the plan `docs/plans/FEAT-XXX_<feature_name>_plan.md` exists but the technical blueprint `docs/designs/FEAT-XXX_<feature_name>_blueprint.md` does NOT:
* **Recommend next Skill**: `plan-to-blueprint`
* Stop.

#### Case C.5: Design Blueprint Approval Pending
If the technical blueprint exists but `blueprint.approved` is NOT marked as `true` in the session data:
* **STOP**. Explain that the Blueprint is pending approval.
* **Recommend next action**: Approve the Blueprint using:
  `python skills/workflow-runtime/scripts/workflow_runtime.py blueprint --path docs/designs/FEAT-XXX_<feature_name>_blueprint.md --approve`

#### Case E: Implementation Incomplete
If the technical blueprint exists and is approved, check if git status shows implementation in progress:
* **Recommend next Skill**: `blueprint-to-implementation`
* Stop.

#### Case H: Verification Phase
If debug and all quality gates pass, check if `docs/verification/FEAT-XXX_verify.md` is marked as `PASS`.
* If missing or not `PASS`:
  * **Recommend next Skill**: `debug-to-verify`
  * Stop.

#### Case I: Release Pending (STOP Gate)
If the verification report is marked as `PASS`, the workflow **MUST STOP**. Release cannot proceed automatically.
* Check if the user has explicitly requested Release.
* If NOT explicitly requested:
  * **STOP**.
  * **Action**: Recommend running `/release` or `implementation-to-release` to publish changes.
  * Stop.
* If explicitly requested:
  * **Recommend next Skill**: `implementation-to-release`
  * Stop.

---

## Output Format

Print the orchestration report using this layout:

```text
Current Phase:
Workflow Orchestration

Status:
Completed

Workflow State:
- Active Feature ID: [FEAT-XXX]
- Brainstorming:  [status]
- Plan:           [status]
- Blueprint:      [status - approved/pending/missing]
- Implementation: [status]
- Verification:   [status]
- Release:        [status - pending/released]

Recommended Next Skill:
[skill-name]

Reason:
[Specific reason citing missing artifact or unapproved state]
```
