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

## Step 2.5 — Orchestrator Routing & Dispatch Behavior (Single Entry Point)

The Orchestrator is the single entry point for all natural language user requests. No skill may self-activate from a raw user request. All raw requests must pass through the orchestrator.

### 2.5.1 — Active Workflow Continuation Check
Before classifying any user request, check the session file (`.agents/.session.json`) for an existing `active_workflow`.
1. If `active_workflow` has `waiting_for` set, and the user's prompt is a continue phrase (e.g., "continue", "tiếp", "tiếp đi", "proceed", "go"):
   * Immediately bypass reclassification.
   * Run the CLI to resume the active workflow:
     ```bash
     python skills/workflow-runtime/scripts/workflow_runtime.py active-workflow resume
     ```
   * Immediately transfer control and execute the instructions of the resumed skill.
   * Stop processing.

### 2.5.2 — Intent Classification Rules
If there is no active workflow or the user's request is not a continue command, analyze the user's intent:
* **quick-fix**:
  * local, low-risk bug, error, exception, failed command, broken behavior, config mismatch, regression, typo causing failure.
* **quick-feature**:
  * small new feature, simple API, UI button, filter, config addition, field, simple validation.
* **brainstorming**:
  * broad/unclear bug, large new feature, new workflow/module, architecture change, database design, multi-service change, high uncertainty.
* **project-rag-search**:
  * asking about existing code, architecture, file locations, dependency, or "how does this project handle X?".
* **project-memory-bootstrap**:
  * asking to initialize or bootstrap memory when no memory configuration exists.
* **project-memory-update**:
  * asking to refresh, rebuild, or sync memory (usually after file changes or implementations).
* **blueprint-to-implementation**:
  * asking to implement changes from an approved blueprint.
* **implementation-to-debug**:
  * asking to debug build, compilation, test, or runtime failures.
* **debug-to-verify**:
  * asking to verify/test a completed implementation.
* **implementation-to-release**:
  * asking explicitly to release, bump versions, write changelogs, tag, or git push. (Route ONLY if explicitly requested).

### 2.5.3 — State Management
Save the routing decision into `.agents/.session.json` under both `"orchestrator"` and `"suggestion_gate"` keys. Call the CLI:
* To recommend a single skill:
  ```bash
  python skills/workflow-runtime/scripts/workflow_runtime.py suggest --request "<request>" --recommend "<skill-name>"
  ```
* To suggest multiple ambiguous options:
  ```bash
  python skills/workflow-runtime/scripts/workflow_runtime.py suggest --request "<request>" --options "quick-fix,quick-feature,brainstorming"
  ```

Ensure the session block has:
```json
"orchestrator": {
  "active": true,
  "raw_request": "...",
  "classification": "...",
  "recommended_skill": "...",
  "recommended_command": "...",
  "options": [],
  "selected_skill": "...",
  "selected_command": "...",
  "routing_status": "waiting_for_user | dispatched | completed | stopped",
  "reason": "..."
}
```

### 2.5.4 — Output Formats & Confirmation Gates
If confidence is high (recommending one skill), output exactly:

```text
Detected request type:
[bug | quick-feature | large-feature | knowledge-search | memory-update | release | ambiguous]

Recommended workflow:
[skill-name] / [command]

Reason:
[...]

This will start:
[short workflow summary]

Confirm?
Y / N
```

Create a choice approval gate:
```bash
python skills/workflow-runtime/scripts/workflow_runtime.py choice create --id "workflow_suggestion" --title "Workflow Suggestion Confirmation" --desc "Confirm starting the suggested workflow:" --options '[{"id":"confirm","label":"Confirm and Proceed"},{"id":"cancel","label":"Cancel/Revise"}]' --type choice
python skills/workflow-runtime/scripts/workflow_runtime.py choice wait --id "workflow_suggestion"
```
Read the choice using `choice read`. If confirmed, dispatch the execution:
```bash
python skills/workflow-runtime/scripts/workflow_runtime.py start --skill <recommended_skill> --command <recommended_command> --checkpoint <checkpoint> --step <step>
```
And immediately execute the target skill's instructions.

If intent is ambiguous, output:
```text
I found multiple possible workflows:

1. quick-fix — for localized bug/issue
2. quick-feature — for small feature/change
3. brainstorming — for larger or unclear feature

Please choose 1, 2, or 3.
```

Create an options selection gate:
```bash
python skills/workflow-runtime/scripts/workflow_runtime.py choice create --id "workflow_suggestion" --title "Choose Workflow Option" --desc "Please choose one of the options:" --options '[{"id":"1","label":"quick-fix"},{"id":"2","label":"quick-feature"},{"id":"3","label":"brainstorming"}]' --type choice
python skills/workflow-runtime/scripts/workflow_runtime.py choice wait --id "workflow_suggestion"
```
Read the selected option. Call `suggest --choose <option_index>`. Then dispatch the chosen skill by calling `start --skill <skill> --command <command> ...` and immediately execute that skill's instructions.

---

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
* **Recommend next action**: Emit a blueprint approval choice:
  ```bash
  python skills/workflow-runtime/scripts/workflow_runtime.py choice create --id "blueprint_approval" --title "Blueprint Design Approval" --desc "Do you approve the Design Blueprint docs/designs/FEAT-XXX_<feature_name>_blueprint.md?" --type approval
  python skills/workflow-runtime/scripts/workflow_runtime.py choice wait --id "blueprint_approval"
  ```
  Wait for response. If approved, run:
  `python skills/workflow-runtime/scripts/workflow_runtime.py blueprint --path docs/designs/FEAT-XXX_<feature_name>_blueprint.md --approve`
* Stop.

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
