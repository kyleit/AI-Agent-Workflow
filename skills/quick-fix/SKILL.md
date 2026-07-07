---
name: quick-fix
command: fix
aliases:
  - bugfix
category: utility
tags:
  - fix
  - hotfix
  - quick
version: 3.1.0
author:
  name: Kyle Dang
  email: kyleit@klexpress.net
  website: https://www.klexpress.net
license: MIT
repository: https://gitlab.com/hngan.it/ai-workflow-skills
created_at: 2026-07-03
updated_at: 2026-07-06
description: Enforces a three-stage workflow (Specification, Blueprint, and Implementation) for quick fixes.
---

# Skill: quick-fix (Three-Phase Workflow with Blueprint-Driven Execution)

---

## 🔒 WORKFLOW RUNTIME & INITIALIZATION CHECK

This Skill MUST interface with the centralized Python CLI Runtime Engine:
- **Validate Checkpoint**: Run `python skills/workflow-runtime/scripts/workflow_runtime.py validate --checkpoint "exactly 2 or 1"` before taking any action. If validation fails, halt execution immediately.
- **Progress Tracking**:
  - *Start*: Run `python skills/workflow-runtime/scripts/workflow_runtime.py start --skill "quick-fix" --command "fix" --checkpoint 5 --step "Starting execution..."`
  - *Step Updates*: Run `python skills/workflow-runtime/scripts/workflow_runtime.py step --step "<step_desc>" --log "<progress_message>"` progressively during major steps.
  - *Completion*: Run `python skills/workflow-runtime/scripts/workflow_runtime.py complete --checkpoint 5 --step "Step Complete" --next-skill "project-memory-update" --next-command "memory-sync"` when execution finishes successfully.
  - *Failure*: Run `python skills/workflow-runtime/scripts/workflow_runtime.py fail --step "<error_step>" --log "<error_details>"` if any phase fails.

## ⚠ MANDATORY FIRST ACTION — DO THIS BEFORE ANYTHING ELSE

**When this Skill is invoked, you must immediately output this table to establish the behavioral anchor:**

| 🔒 QUICK-FIX MODE ACTIVE |
| :--- |
| This Skill runs in a **three-phase model** with strict Blueprint enforcement. |
| **Phase 1 (Specification)**: Analyze and write the FIX specification. |
| **Phase 2 (Blueprint)**: Design the technical solution and write the Design Blueprint. |
| **Phase 3 (Implementation)**: Implement code only after explicit Blueprint approval. |
| NO SOURCE CODE will be modified during Phase 1 or Phase 2. |
| Specification path: `docs/issues/FIX-XXX_issue_name.md` |
| Design Blueprint path: `docs/designs/FIX-XXX_issue_name_blueprint.md` |

---

## 🔒 GLOBAL POLICY REFERENCES

This Skill MUST strictly adhere to the global policies defined in [AI_RULES.md](../../AI_RULES.md):
- **Approval Gate Policy** (Section 1) - Seek explicit confirmation before modifying code or creating files.
- **Git Workflow Policy** (Section 2) - Perform branch checks and commits/tags/pushes only with approval.
- **Memory First Policy** (Section 3) - Consult project summary/memory before source files or user questions.
- **RAG Policy** (Section 4) - Follow retrieval sequence levels.
- **Artifact Policy** (Section 5) - Strictly follow path boundaries and naming formats.
- **Testing Policy** (Section 8) - Run compilation, build, and tests, halting on failures.
- **Blueprint Mandatory Execution Policy** (Section 13) - Never implement without approved Blueprint.
- **Skill Suggestion Gate Policy** (Section 14) - Raw requests require suggestion first; selected Skill requires confirmation.
- **Workspace Permission Mode Policy** (Section 15) - Sandbox mode is default; ask user to choose sandbox or full_access at init.

---

## Capability Boundary & Guardrails

- **No Premature Implementation**: No source code may be created, deleted, or modified before a Technical Design Blueprint is generated under `docs/designs/` and explicitly approved by the user.
- **Validation of Blueprint**: Before code generation, verify that the Blueprint exists, has status `approved` in the session or was explicitly approved by the user in the prompt logs.
- **No Refactoring**: Implement ONLY the minimal changes described in the approved Blueprint. Do NOT introduce unrelated cleanups, structural refactoring, or database redesigns.
- **No Downstream Auto-Execution**: Do NOT execute Git commands (commit, push) automatically. Release must only occur if explicitly requested by the user.

---

## Quick-Fix Eligibility Rules

Every issue must first be evaluated against the following criteria:

| Category | Quick-Fix Eligible (All Must Pass) | Standard Workflow Required (Any Trigger) |
|---|---|---|
| **Scope** | Single module, service, API, SQL query, UI component, or configuration file. | Multiple modules, cross-cutting concerns, database restructuring. |
| **Architecture Impact** | Low (additive or purely local change, fits current design). | Medium/High (changes shared interfaces, protocols, or infrastructure). |
| **ADR Requirement** | No ADR required. | ADR required (decisions with long-term architectural trade-offs). |
| **Estimated Work** | Less than one working day (Low complexity). | More than one working day (High complexity, uncertain paths). |

---

## FIX-XXX ID Naming Rule

FIX IDs are independent of Feature IDs but share the same directory:
1. Scan `docs/issues/` for files matching `FIX-XXX_*.md` (where `XXX` is a 3-digit number).
2. Ignore plans, designs, and other files.
3. If no matching files exist (excluding placeholders like `.gitkeep`), the ID starts at `FIX-001`.
4. If files exist, the next ID is the highest existing ID + 1 (e.g. `FIX-002`, `FIX-003`).

---

## Workflow Sequence

Execute these steps strictly. Stop at every gate.

```
Step 1:  Receive User Issue / Bug Report
         ↓
Step 2:  Issue Classification & Eligibility Check
         - Produce the Decision Matrix.
         - [STOP] If classified as Standard → Reject and recommend standard workflow.
         ↓
Step 3:  Consult Project Memory & RAG (No whole-workspace scanning)
         ↓
Step 4:  Targeted Source Inspection
         ↓
Step 5:  Generate Fix Specification (docs/issues/FIX-XXX_issue_name.md)
         ↓
          - Call the `ask_question` tool directly:
            - **Question**: "Approve FIX specification?"
            - **Options**: `["Yes", "No"]`
          - [STOP] Wait for user confirmation.
         ↓
Step 7:  Generate Technical Design Blueprint (docs/designs/FIX-XXX_issue_name_blueprint.md)
          ↓
Step 8:  User Approval Gate (Phase 2: Blueprint Approval)
          - Run python CLI to register blueprint.
          - Call the `ask_question` tool directly:
            - **Question**: "Approve Blueprint?"
            - **Options**: `["Yes", "No"]`
          - [STOP] Wait for user confirmation.
          - Run python CLI to mark blueprint approved.
         ↓
Step 9:  Pre-Implementation Git Gate (Phase 3)
          - Run git branch & git status.
          - Check if a Git branch action has already been selected by reading `git.branch_action` in `.session.json`.
            - If `git.branch_action` is already set (e.g., "continue", "create", or "stop"), skip the prompt and proceed.
            - If not set, call the `ask_question` tool directly:
              - **Question**: "Choose Git branch action:"
              - **Options**: `["Continue on current branch", "Create new branch", "Stop"]`
            - Once selected, save the choice in `.session.json` under `git.branch_action` ("continue", "create", or "stop").
          - [STOP] Wait for user confirmation (only if prompting occurred).
         ↓
Step 10: Global Approval Gate (Phase 3)
          - Explain modifications, list affected files and branch.
          - Call the `ask_question` tool directly:
            - **Question**: "Proceed with implementation?"
            - **Options**: `["Yes", "No"]`
          - [STOP] Wait for user confirmation.
         ↓
Step 11: Code Implementation (Direct minimal code fix)
         ↓
Step 12: Automatic Validation Pipeline
         - Run compiler, check builds, run existing unit tests.
         - [STOP] If tests fail → Report failures and halt.
         ↓
Step 13: Generate Quick-Fix Summary Report & Self-Validation Checklist
```

---

## Detailed Step Instructions

### Step 5: Generate Fix Specification

Calculate the FIX ID and write the document at:
`docs/issues/FIX-XXX_issue_name.md`

Use this template:

```markdown
<!-- File path: docs/issues/FIX-XXX_issue_name.md -->
---
artifact_type: fix-spec
issue_id: FIX-XXX
workflow: quick-fix
status: pending
---
# Fix Specification – [Issue Name]
## 1. Issue Description
[Detailed description of the issue]
## 2. Scope
- **In Scope**: [Minimal change description]
- **Out of Scope**: [What will NOT be changed]
```

---

### Step 6: User Approval Gate

Ask `Approve FIX specification? [Y/N]`. Do NOT create a Blueprint or modify source code until the user responds Y (or "yes").

---

### Step 7: Generate Technical Design Blueprint

Create the Design Blueprint under `docs/designs/FIX-XXX_issue_name_blueprint.md`.

Use this template:

```markdown
<!-- File path: docs/designs/FIX-XXX_issue_name_blueprint.md -->
---
artifact_type: blueprint
issue_id: FIX-XXX
workflow: quick-fix
status: draft
---
# Technical Design Blueprint – [Issue Name]
## 1. Proposed Code Changes
[Specify file changes with exact classes, methods, or blocks]
## 2. Test Plan
- Run compilation and tests
```

---

### Step 8: User Approval Gate (Blueprint)

1. Register the blueprint via CLI:
   `python skills/workflow-runtime/scripts/workflow_runtime.py blueprint --path docs/designs/FIX-XXX_issue_name_blueprint.md`
2. Ask: `Approve Blueprint? [Y/N]` and STOP.
3. If approved, run:
   `python skills/workflow-runtime/scripts/workflow_runtime.py blueprint --path docs/designs/FIX-XXX_issue_name_blueprint.md --approve`

---

### Step 11: Code Implementation

Only after receiving blueprint approval:
1. Verify the blueprint is approved in the session.
2. Implement code changes exactly as described in the blueprint.

---

### Step 13: Generate Quick Task Result

Upon completion, print the final summary:

```markdown
## Quick Task Result
Status: [PASS / FAILED]
Files Modified:
- [Relative path to file](link)

Validation:
Build: [PASS | FAILED]
Tests: [PASS | FAILED]

Recommended Next Step:
- Post-implementation verification complete. STOP. Recommend running Release if desired.
```
