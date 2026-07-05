---
name: quick-feature
command: feature
aliases:
  - scaffold
category: utility
tags:
  - utility
  - feature
  - scaffolding
version: 2.5.0
author:
  name: Kyle Dang
  email: kyleit@klexpress.net
  website: https://www.klexpress.net
license: MIT
repository: https://gitlab.com/hngan.it/ai-workflow-skills
created_at: 2026-07-03
updated_at: 2026-07-03
description: Skill definition.
---

# Skill: quick-feature (Two-Phase Workflow with Approval Gates)

---

## 🔒 WORKFLOW RUNTIME & INITIALIZATION CHECK

This Skill MUST interface with the centralized Python CLI Runtime Engine:
- **Validate Checkpoint**: Run `python skills/workflow-runtime/scripts/workflow_runtime.py validate --checkpoint "exactly 2"` before taking any action. If validation fails, halt execution immediately.
- **Progress Tracking**:
  - *Start*: Run `python skills/workflow-runtime/scripts/workflow_runtime.py start --skill "quick-feature" --command "feature" --checkpoint 5 --step "Starting execution..."`
  - *Step Updates*: Run `python skills/workflow-runtime/scripts/workflow_runtime.py step --step "<step_desc>" --log "<progress_message>"` progressively during major steps.
  - *Completion*: Run `python skills/workflow-runtime/scripts/workflow_runtime.py complete --checkpoint 5 --step "Step Complete" --next-skill "implementation-to-release" --next-command "release"` when execution finishes successfully.
  - *Failure*: Run `python skills/workflow-runtime/scripts/workflow_runtime.py fail --step "<error_step>" --log "<error_details>"` if any phase fails.

## ⚠ MANDATORY FIRST ACTION — DO THIS BEFORE ANYTHING ELSE

**When this Skill is invoked, you must immediately output this table to establish the behavioral anchor:**

| 🔒 QUICK-FEATURE MODE ACTIVE |
| :--- |
| This Skill runs in a **two-phase model** with an approval gate. |
| **Phase 1**: Analyze and write the MINI FEATURE SPEC. |
| **Phase 2**: Implement only after explicit Y/N confirmation. |
| NO SOURCE CODE will be modified during Phase 1. |
| The only file written in Phase 1 is: `docs/quick/QUICK-XXX_feature_name.md` |

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

## 🔒 QUICK-FEATURE WORKFLOW GUARDRAILS

**This Skill operates under strict execution rules to keep features lightweight and safe:**

- **Mandatory Phase 1 Spec File**: You MUST generate `docs/quick/QUICK-XXX_feature_name.md` during Phase 1. No implementation can start, and no source code can be modified, until after Y/N user approval is received.
- **No Workflow Overhead**: Do NOT create or edit files in `docs/plans/`, `docs/designs/`, or `docs/adr/`.
- **Minimal Code Scope**: Implement ONLY the minimum required code changes to resolve the feature request. Do NOT refactor code, redesign interfaces, or clean up unrelated technical debt.
- **No Downstream Execution**: Do NOT run Git commands (commit, push, branch) and do NOT automatically execute the next skill (`implementation-to-release`).

---

## Quick Feature Eligibility Rules

Every feature request must first be evaluated against the following criteria:

| Category | Quick-Feature Eligible (All Must Pass) | Standard Workflow Required (Any Trigger) |
|---|---|---|
| **Scope** | Single module or UI component (e.g. adding one API endpoint, one button, one dialog, one filter, one validation, one search field, one export function, one config option). | Multiple independent modules, cross-cutting concerns, database redesign. |
| **Architecture Impact** | Low (additive or purely local change, fits current design). | Medium/High (changes shared interfaces, authentication, storage/caching strategy, or infrastructure). |
| **ADR Requirement** | No ADR required. | ADR required (decisions with long-term architectural trade-offs). |
| **Estimated Work** | Less than one working day (Low complexity). | More than one working day (High complexity, uncertain paths). |
| **Risk** | Low | Medium / High |

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
Step 5:  Generate Mini Feature Specification (docs/quick/QUICK-XXX_feature_name.md)
         ↓
Step 6:  User Approval Gate (Phase 1)
         - [STOP] Ask "Continue? [Y/N]" → Wait for user confirmation.
         - If N: halt.
         - If Y: proceed to Step 7.
         ↓
Step 7:  Pre-Implementation Git Gate (Phase 2)
         - Run git branch & git status.
         - Ask choice (Continue on branch / Create new branch / Stop) and wait.
         ↓
Step 8:  Global Approval Gate (Phase 2)
         - Explain modifications, list affected files and branch.
         - Ask "Proceed with implementation? [Y/N]" and STOP.
         ↓
Step 9:  Code Implementation (Direct minimal code changes)
         ↓
Step 10: Verification & Testing
         - Run compiler, check builds, run existing unit tests.
         - [STOP] If tests fail → Report failures and halt.
         ↓
Step 11: Generate Quick Feature Summary Report & Self-Validation Checklist
```

---

## Detailed Step Instructions

---

### Step 2: Feature Classification & Eligibility Check

Evaluate the user's request and output the Decision Matrix table:

```markdown
### 🔍 Quick-Feature Eligibility Check

| Category | Evaluation Result |
| :--- | :--- |
| **Scope** | [Small / Medium / Large] |
| **Architecture Impact** | [Low / Medium / High] |
| **ADR Required** | [Yes / No] |
| **Recommended Workflow**| **[Quick Feature / Standard Workflow]** |
```

#### Rejection Rule (Standard Workflow Trigger)

If the **Recommended Workflow** is **Standard Workflow**, you must **STOP** immediately. Print the following message:

```text
❌ This feature exceeds Quick Feature eligibility criteria.
Recommended workflow sequence:
  1. /brainstorm (Requirement Discovery)
  2. /plan (Technical Planning)
  3. /blueprint (Technical Design)
```

---

### Step 3: Consult Project Memory & RAG

- Read `.agents/memory.config.json` to find `<memory_root>`.
- Consult `<memory_root>/project-summary.md` and RAG search to locate the module structure.
- Do NOT perform wild source searches.

---

### Step 4: Targeted Source Inspection

Inspect ONLY the files containing the target code area.

---

### Step 5: Generate Mini Feature Specification

Only after performing the analysis, calculate the Feature ID and write the document at:
```text
docs/quick/QUICK-XXX_feature_name.md
```
*(Replace `XXX` with the calculated Feature ID, and `feature_name` with a lowercase, underscore-separated slug)*

The generated file must follow this template exactly:

```markdown
<!-- File path: docs/quick/QUICK-XXX_feature_name.md -->

---
artifact_type: quick-feature
feature_id: QUICK-XXX
workflow: quick-feature
architecture_impact: low
adr_required: false
status: draft
---

# Mini Feature Specification – [Feature Name]

## 1. Feature Goal
[Detailed description of the requested feature goal]

## 2. Business Value
[What business value this feature brings and what success looks like]

## 3. Existing Context
[What existing components/APIs/modules relate to this request]

## 4. Scope
- **In Scope**: [Minimal feature details]
- **Out of Scope**: [What will NOT be built or changed]

## 5. Expected Files
| Action | File Path | Responsibility |
| :--- | :--- | :--- |
| [Modify | Create] | [relative_path] | [Expected role of the change] |

## 6. Proposed Changes
[Detailed textual description of the code changes]

## 7. Risks
- **Risk**: [Risk] → **Mitigation**: [Mitigation]

## 8. Acceptance Criteria
- [ ] [Verifiable criterion 1]
- [ ] [Verifiable criterion 2]

## 9. Test Plan
- **Verification**: Run compile/build commands.
- **Manual Check**: [How to verify manually]
- **Unit Tests**: [Run specific test command if available]
```

---

### Step 6: User Approval Gate

After writing the file, display this exact prompt and **STOP**:

```text
Quick Feature Analysis Complete

Generated:
docs/quick/QUICK-XXX_feature_name.md

Continue?

[Y/N]
```

> [!CAUTION]
> **Do NOT modify any source files until the user explicitly responds Y (or "yes").**
> If the user responds N or requests changes, stop. You may revise the proposed changes based on feedback.

---

### Step 7: Pre-Implementation Git Gate

Before modifying code:
1. Run `git branch --show-current` and `git status --short`.
2. Ask:
   ```text
   How would you like to proceed with the Git branch?
     1. Continue on current branch
     2. Create new branch (Suggested: quick/QUICK-XXX-slug)
     3. Stop
   ```
3. **STOP** and wait for explicit choice.

---

### Step 8: Global Approval Gate

Prior to coding, show the exact modification summary:
1. Explain modifications.
2. List affected files.
3. List branch name.
4. Prompt:
   ```text
   Proceed with implementation? [Y/N]
   ```
5. **STOP** and wait for approval.

---

### Step 9: Implementation Phase

Only after receiving explicit Y confirmation:
1. Read the generated Mini Feature Spec at `docs/quick/QUICK-XXX_feature_name.md`.
2. Apply the code edits described in the **Proposed Changes** section.
3. Keep changes minimal and focused.

---

### Step 10: Automatic Validation Pipeline

Immediately after applying code edits, the agent must run the automatic validation pipeline and self-fix loop:
1. Detect and execute the validation commands as defined in **[AI_RULES.md](../../AI_RULES.md) (Section 11: Shared Validation Engine Policy)**.
2. In case of command failures:
   - Print the execution command, status, and the error logs.
   - **Scope Protection Check**: Identify issues within the files modified by this Quick-Feature. Do NOT edit unrelated modules.
   - Apply fixes to the code and re-run validation (up to **3 retries** maximum).
3. If validation still fails after 3 retries, or if the fix is unsafe:
   - STOP immediately, set session status to `"failed"`, and recommend running `/debug`.

---

### Step 11: Frontend Visual Debug (If UI)

If the feature affects frontend components, UI layout, styles (HTML/CSS/JS, React, Vue, Svelte, Tailwind, Electron, Wails), or responsive behavior:
1. Run the `frontend-visual-debug` Skill (command `/visual-debug`) to inspect the changes in a browser environment (or fallback to static inspection if browser tools are unavailable).
2. Generate the visual debug report under `docs/verification/FEAT-XXX_visual_debug.md` (or save as section inside verification folder).
3. If visual debugging fails, the overall Quick-Feature status must be set to `FAILED`.

---

### Step 12: Generate Quick Task Result

Upon completion, print the final summary to the console and update `.session.json`:

```markdown
## Quick Task Result

Status: [PASS / PARTIAL / FAILED]
*Note: Set to PARTIAL if browser tools were unavailable for visual debugging of UI features.*

Files Modified:
- [Relative path to file 1](file_link)

Validation:

Build: [PASS | FAILED | Not Configured] (Command: [command])
Lint: [PASS | FAILED | Not Configured] (Command: [command])
Typecheck: [PASS | FAILED | Not Configured] (Command: [command])
Tests: [PASS | FAILED | Not Configured] (Command: [command])
Visual Debug: [PASS | PARTIAL | FAILED | Skipped (Backend Only)] (URL: [local url])

Issues Fixed Automatically:
- [List of fixes or "None"]

Remaining Issues:
- [List of remaining issues or "None"]

Recommended Next Step:
- If PASS or PARTIAL: /release
- If FAILED: /debug

Workflow Paused.
```
