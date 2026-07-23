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
license: MIT
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
  usage: cached---

# Skill: Software Development Workflow Orchestrator (Blueprint-Driven & Explicit Release)

## Purpose

This Skill is the **central coordinator** of the entire AI Coding Platform. It acts as a **Project Manager** to determine the current phase, verify Quality Gates, check Blueprint approvals, perform raw request classification, and recommend the single correct next Skill to run.

It does NOT perform any engineering work, code modification, or file writing.

---

## 🔒 WORKFLOW RUNTIME & INITIALIZATION CHECK

This Skill interfaces with the aiwf Go Native CLI Engine (`aiwf`):
- **Validate Checkpoint**: Run `aiwf validate --checkpoint "optional"` before taking any action.
- **Progress Tracking**: Update status and log progress using `workflow_runtime.py` when integrated in a workflow session.

---

## AI Coding Platform SDLC Layers (FEAT-XXX / FIX-XXX / QUICK-XXX)

This Skill coordinates all phases of a feature's lifecycle:

```
Platform Infrastructure & Knowledge
  Layer 1 — Environment (environment-bootstrap, environment-health)
  Layer 2 — Knowledge (project-memory-bootstrap, project-memory-update, project-rag-search)

Feature-Centric SDLC (Enforcing Blueprint-Driven Development)

  Option 1: Standard Workflow (Medium & Large Features)
    1. Brainstorming     ──> docs/features/<feature-family>/brainstorming/FEAT-XXX_<feature_name>.md
                             Skill: brainstorming
    2. Planning          ──> docs/features/<feature-family>/plans/FEAT-XXX_<feature_name>_plan.md
                             Skill: brainstorming-to-plan
    3. Design            ──> docs/features/<feature-family>/blueprints/FEAT-XXX_<feature_name>_blueprint.md
                             Skill: plan-to-blueprint
    [Optional] ADR       ──> docs/adr/ADR-XXX_<short_title>.md
                             Skill: create-adr
    4. Design Approval   ──> Runtime `prompt select` for Blueprint Approval
    5. Implementation    ──> source code implementation
                             Skill: blueprint-to-implementation
    6. Debug             ──> docs/features/<feature-family>/debug/FEAT-XXX_<feature_name>_debug.md
                             Skill: implementation-to-debug
    7. VIR Visual QA     ──> Run visual check loops (if frontend changes are present)
                             Skills: frontend-visual-debug ──> vir-investigate ──> vir-runtime ──> vir-verify
    8. Verification      ──> docs/features/<feature-family>/verification/FEAT-XXX_<feature_name>_verify.md
                             Skill: debug-to-verify (requires vir-verify report PASS if mandatory)
    9. STOP              ──> Pause and recommend Release.
    10. Manual Release   ──> updates CHANGELOG.md & bumps version
                             Skill: implementation-to-release (only if explicitly requested)

  Option 2: Quick-Fix Workflow (Small Bug Fixes - 3-stage)
    1. Fix Specification ──> docs/features/<feature-family>/issues/FIX-XXX_<issue_name>.md
                             Skill: quick-fix
    2. Spec Review       ──> Internal review loop; no user approval stop
    3. Technical Design  ──> docs/features/<feature-family>/blueprints/FIX-XXX_<issue_name>_blueprint.md
                             Skill: quick-fix
    4. Design Approval   ──> Runtime `prompt select` for Blueprint Approval
    5. Implementation    ──> apply minimal hotfix & verify builds
                             Skill: quick-fix
    6. VIR Visual QA     ──> Targeted visual check (if UI affected)
                             Skills: frontend-visual-debug ──> vir-verify
    7. Verification      ──> docs/features/<feature-family>/verification/FIX-XXX_<issue_name>_verify.md
    8. STOP              ──> Pause and recommend Release.
    9. Manual Release    ──> updates CHANGELOG.md & bumps version (only if explicitly requested)

  Option 3: Quick-Feature Workflow (Small Feature Requests - 3-stage)
    1. Feature Spec      ──> docs/features/<feature-family>/quick/QUICK-XXX_<feature_name>.md
                             Skill: quick-feature
    2. Spec Review       ──> Internal review loop; no user approval stop
    3. Technical Design  ──> docs/features/<feature-family>/blueprints/QUICK-XXX_<feature_name>_blueprint.md
                             Skill: quick-feature
    4. Design Approval   ──> Runtime `prompt select` for Blueprint Approval
    5. Implementation    ──> apply minimal feature code & verify
                             Skill: quick-feature
    6. VIR Visual QA     ──> Targeted visual check (if UI affected)
                             Skills: frontend-visual-debug ──> vir-verify
    7. Verification      ──> docs/features/<feature-family>/verification/QUICK-XXX_<feature_name>_verify.md
    8. STOP              ──> Pause and recommend Release.
    9. Manual Release    ──> updates CHANGELOG.md & bumps version (only if explicitly requested)
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
     aiwf active-workflow resume
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
  aiwf suggest --request "<request>" --recommend "<skill-name>"
  ```
* To suggest multiple ambiguous options:
  ```bash
  aiwf suggest --request "<request>" --options "quick-fix,quick-feature,brainstorming"
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

### 2.5.4 — Auto-Dispatch & Ambiguity Gates
If confidence is high (one workflow is clearly correct), do not ask the user to confirm the recommended Skill and do not ask the user to type `/quick-feature`, `/quick-fix`, or `/brainstorming` manually.

Persist the routing decision:
```bash
aiwf suggest --request "<request>" --recommend "<skill-name>"
```

Then dispatch immediately:
```bash
aiwf start --skill <recommended_skill> --command <recommended_command> --checkpoint <checkpoint> --step <step>
```
Immediately execute the target Skill's instructions. Continue through the pre-approval artifact and internal review loops until the Technical Design Blueprint passes review, then stop for final user approval before implementation.

If intent is ambiguous, output:
```text
I found multiple possible workflows:

1. quick-fix — for localized bug/issue
2. quick-feature — for small feature/change
3. brainstorming — for larger or unclear feature

Please choose 1, 2, or 3.
```

Create a runtime prompt selection gate:
```bash
aiwf prompt select --question "Choose workflow option:" --options "quick-fix|quick-feature|brainstorming" --default "quick-feature"
```
Read the selected option from the runtime prompt result. Persist it with `suggest --request "<request>" --recommend "<selected_skill>"`. Then dispatch the chosen skill by calling `start --skill <skill> --command <command> ...` and immediately execute that skill's instructions.

---

---

## Step 3 — Feature & Workflow Detection

### 3.1 — Detect Active Feature ID & Track Eligibility

1. **Scan documentation**: Scan `docs/features/<feature-family>/brainstorming/FEAT-XXX_*.md`, former work-item folders, and legacy flat files only as backward-compatible input.
2. Find the file with the highest numerical suffix in `FEAT-XXX` as the **Active Feature**. Let this ID be `FEAT-XXX`.

### 3.2 — Trace Feature Lifecycle Status

#### Case C: Design Blueprint Missing
If the plan `docs/features/<feature-family>/plans/FEAT-XXX_<feature_name>_plan.md` exists but the technical blueprint `docs/features/<feature-family>/blueprints/FEAT-XXX_<feature_name>_blueprint.md` does NOT:
* **Recommend next Skill**: `plan-to-blueprint`
* Stop.

#### Case C.5: Design Blueprint Approval Pending
If the technical blueprint exists but `blueprint.approved` is NOT marked as `true` in the session data:
* **STOP**. Explain that the Blueprint is pending approval.
* **Recommend next action**: Emit a runtime prompt selection for Blueprint Approval:
  ```bash
  aiwf prompt select --question "Approve the Design Blueprint docs/features/<feature-family>/blueprints/FEAT-XXX_<feature_name>_blueprint.md for implementation?" --options "Continue|Cancel" --default "Cancel"
  ```
  Wait for the runtime prompt result. If the result is `Continue`, run:
  `aiwf blueprint --path docs/features/<feature-family>/blueprints/FEAT-XXX_<feature_name>_blueprint.md --approve`
  If the result is `Cancel`, leave the blueprint pending and stop.
* Stop.

#### Case E: Implementation Incomplete
If the technical blueprint exists and is approved, check if git status shows implementation in progress:
* **Recommend next Skill**: `blueprint-to-implementation`
* Stop.

#### Case H: Verification Phase
If debug and all quality gates pass, check if `docs/features/<feature-family>/verification/FEAT-XXX_<feature_name>_verify.md` is marked as `PASS`.
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
