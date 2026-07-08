---
name: quick-feature
command: feature
aliases:
  - scaffold
category: utility
tags:
  - utility
  - feature
  - quick
  - minor
version: 3.1.0
author:
  name: Kyle Dang
  email: kyleit@klexpress.net
  website: https://www.klexpress.net
license: MIT
repository: https://gitlab.com/hngan.it/ai-workflow-skills
created_at: 2026-07-03
updated_at: 2026-07-06
description: Enforces a three-stage workflow (Specification, Blueprint, and Implementation) for quick features.
---

# Skill: quick-feature (Three-Phase Workflow with Blueprint-Driven Execution)

---

## 🔒 WORKFLOW RUNTIME & INITIALIZATION CHECK

This Skill MUST interface with the centralized Python CLI Runtime Engine:
- **Validate Checkpoint**: Run `python skills/workflow-runtime/scripts/workflow_runtime.py validate --checkpoint "exactly 2"` before taking any action. If validation fails, halt execution immediately.
- **Progress Tracking**:
  - *Start*: Run `python skills/workflow-runtime/scripts/workflow_runtime.py start --skill "quick-feature" --command "feature" --checkpoint 5 --step "Starting execution..."`
  - *Step Updates*: Run `python skills/workflow-runtime/scripts/workflow_runtime.py step --step "<step_desc>" --log "<progress_message>"` progressively during major steps.
  - *Completion*: Run `python skills/workflow-runtime/scripts/workflow_runtime.py complete --checkpoint 5 --step "Step Complete" --next-skill "project-memory-update" --next-command "memory-sync"` when execution finishes successfully.
  - *Failure*: Run `python skills/workflow-runtime/scripts/workflow_runtime.py fail --step "<error_step>" --log "<error_details>"` if any phase fails.

## ⚠ MANDATORY FIRST ACTION — DO THIS BEFORE ANYTHING ELSE

**When this Skill is invoked, you must immediately output this table to establish the behavioral anchor:**

| 🔒 QUICK-FEATURE MODE ACTIVE |
| :--- |
| This Skill runs in a **three-phase model** with strict Blueprint enforcement. |
| **Phase 1 (Specification)**: Analyze and write the QUICK feature specification. |
| **Phase 2 (Blueprint)**: Design the technical solution and write the Design Blueprint. |
| **Phase 3 (Implementation)**: Implement code only after explicit Blueprint approval. |
| NO SOURCE CODE will be modified during Phase 1 or Phase 2. |
| Specification path: `docs/quick/QUICK-XXX_feature_name.md` |
| Design Blueprint path: `docs/designs/QUICK-XXX_feature_name_blueprint.md` |

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

## Quick-Feature Eligibility Rules

Every feature request must first be evaluated against the following criteria:

| Category | Quick-Feature Eligible (All Must Pass) | Standard Workflow Required (Any Trigger) |
|---|---|---|
| **Scope** | Single module or UI component (e.g. adding one API endpoint, one button, one dialog, one filter, one validation, one search field, one export function). | Multiple independent modules, cross-cutting concerns, database redesign. |
| **Architecture Impact** | Low (additive or purely local change, fits current design). | Medium/High (changes shared interfaces, authentication, storage/caching strategy). |
| **ADR Requirement** | No ADR required. | ADR required (decisions with long-term architectural trade-offs). |
| **Estimated Work** | Less than one working day (Low complexity). | More than one working day (High complexity, uncertain paths). |

---

## Feature ID Allocation Rule

QUICK Feature IDs are determined **ONLY** by scanning `docs/quick/`:
1. Scan `docs/quick/` for files matching `QUICK-XXX_*.md` (where `XXX` is a 3-digit number).
2. Ignore plans, designs, and other files.
3. If directory is empty (or has only `.gitkeep`): start at `QUICK-001`.
4. If files exist: next ID = highest existing ID + 1.

---

## Workflow Sequence

Execute these steps strictly. Stop at every gate.

```
Step 1:  Receive User Feature Request
         ↓
Step 2:  Feature Classification & Eligibility Check
         - Produce the Decision Matrix.
         - [STOP] If classified as Standard → Reject and recommend standard workflow.
         ↓
Step 3:  Consult Project Memory & RAG (No whole-workspace scanning)
         ↓
Step 4:  Targeted Source Inspection
         ↓
Step 5:  Generate Feature Specification (docs/quick/QUICK-XXX_feature_name.md)
         ↓
Step 6:  User Approval Gate (Phase 1: Spec Approval)
          - Run:
            ```bash
            python3 .agents/skills/workflow-runtime/scripts/workflow_runtime.py prompt select --question "Approve QUICK specification?" --options "Yes|No" --default "No"
            ```
          - [STOP] Wait for user confirmation.
         ↓
Step 7:  Generate Technical Design Blueprint (docs/designs/QUICK-XXX_feature_name_blueprint.md)
         ↓
Step 8:  User Approval Gate (Phase 2: Blueprint Approval)
          - Run python CLI to register blueprint.
          - Run:
            ```bash
            python3 .agents/skills/workflow-runtime/scripts/workflow_runtime.py prompt select --question "Approve Blueprint?" --options "Yes|No" --default "No"
            ```
          - [STOP] Wait for user confirmation.
          - Run python CLI to mark blueprint approved.
         ↓
Step 9:  Pre-Implementation Git Gate (Phase 3)
          - Run git branch & git status.
          - Run:
            ```bash
            python3 .agents/skills/workflow-runtime/scripts/workflow_runtime.py prompt select --question "Choose Git branch action:" --options "Continue on current branch|Create new branch|Stop" --default "Stop"
            ```
          - [STOP] Wait for user confirmation.
         ↓
Step 10: Global Approval Gate (Phase 3)
          - Explain modifications, list affected files and branch.
          - Run:
            ```bash
            python3 .agents/skills/workflow-runtime/scripts/workflow_runtime.py prompt select --question "Proceed with implementation?" --options "Yes|No" --default "No"
            ```
          - [STOP] Wait for user confirmation.
         ↓
Step 11: Code Implementation (Direct minimal code changes)
         ↓
Step 12: Automatic Validation Pipeline
         - Run compiler, check builds, run existing unit tests.
         - [STOP] If tests fail → Report failures and halt.
         ↓
Step 13: Generate Quick Feature Summary Report & Self-Validation Checklist
```

---

## Detailed Step Instructions

### Step 5: Generate Feature Specification

Calculate the Feature ID and write the document at:
`docs/quick/QUICK-XXX_feature_name.md`

Use this template:

```markdown
<!-- File path: docs/quick/QUICK-XXX_feature_name.md -->
---
artifact_type: quick-feature-spec
feature_id: QUICK-XXX
workflow: quick-feature
status: pending
---
# Mini Feature Specification – [Feature Name]
## 1. Feature Goal
[Detailed description of the feature goal]
## 2. Scope
- **In Scope**: [Minimal feature details]
- **Out of Scope**: [What will NOT be built or changed]
```

---

### Step 6: User Approval Gate

Ask `Approve QUICK specification? [Y/N]`. Do NOT create a Blueprint or modify source code until the user responds Y (or "yes").

---

### Step 7: Generate Technical Design Blueprint

Create the Design Blueprint under `docs/designs/QUICK-XXX_feature_name_blueprint.md`.

Use this template:

```markdown
<!-- File path: docs/designs/QUICK-XXX_feature_name_blueprint.md -->
---
artifact_type: blueprint
feature_id: QUICK-XXX
workflow: quick-feature
status: draft
---
# Technical Design Blueprint – [Feature Name]

## 1. Proposed Code Changes
All files to create, modify, or delete must be listed here. No placeholders allowed.

### [File Path]
- **Operation**: [NEW | MODIFY | DELETE]
- **Responsibility**: [Explain the file change's specific role]
- **Changes**: [List classes, methods, or blocks affected]

## 2. Target Folder Structure
Complete directory layout after modifications:
```text
.
├── (folders and files structure)
```

## 3. Interface & Data Contracts
- **API/CLI Contracts**: [CLI flags, REST payloads, response schema, config properties]
- **Data Schema**: [JSON schemas, DB columns, or state models]

## 4. Algorithms & Key Logic
- [Pseudo-code or step-by-step logic description]

## 5. Validation Rules
- [Specify validation checks and input formatting constraints]

## 6. Implementation Checklist
- [ ] Task...

## 7. Verification & Test Plan
- **Acceptance Assertions**:
  - *REQ-001*: Test method and target file.
```

---

### Step 8: User Approval Gate (Blueprint)

1. Register the blueprint via CLI:
   `python skills/workflow-runtime/scripts/workflow_runtime.py blueprint --path docs/designs/QUICK-XXX_feature_name_blueprint.md`
2. Ask: `Approve Blueprint? [Y/N]` and STOP.
3. If approved, run:
   `python skills/workflow-runtime/scripts/workflow_runtime.py blueprint --path docs/designs/QUICK-XXX_feature_name_blueprint.md --approve`

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
