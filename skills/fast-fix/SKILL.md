---
name: fast-fix
command: fast-fix
aliases:
  - quick-fix-legacy
category: utility
tags:
  - legacy
  - bugfix
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

# Skill: fast-fix (Two-Phase Workflow with Approval Gate)

---

## ⚠ MANDATORY FIRST ACTION — DO THIS BEFORE ANYTHING ELSE

**When this Skill is invoked, you must immediately output this block to establish the behavioral anchor:**

```
╔══════════════════════════════════════════════════════════════╗
║  🔒 FAST-FIX MODE ACTIVE                                     ║
║                                                              ║
║  This Skill runs in a two-phase model with an approval gate:  ║
║  - Phase 1: Analyze and write the FIX document.              ║
║  - Phase 2: Implement only after explicit Y/N confirmation.  ║
║                                                              ║
║  NO SOURCE CODE will be modified during Phase 1.             ║
║  The only file written in Phase 1 is:                        ║
║    docs/issues/FIX-XXX_issue_name.md                         ║
╚══════════════════════════════════════════════════════════════╝
```

---

## Capability Boundary & Guardrails

- **Mandatory Phase 1 Fix File**: You MUST generate `docs/issues/FIX-XXX_issue_name.md` during Phase 1. No implementation can start, and no source code can be modified, until after Y/N user approval is received.
- **Allowed Phase 1 Output**: The ONLY file this Skill may create or edit before explicit user confirmation is:
  ```text
  docs/issues/FIX-XXX_issue_name.md
  ```
- **Strict Read-Only Before Confirmation**: Do NOT modify any source code files (`.go`, `.svelte`, etc.), plans, blueprints, or other documents during Phase 1.
- **No Refactoring**: During Phase 2, implement ONLY the minimal changes described in the approved Fix document. Do NOT introduce unrelated cleanups, structural refactoring, or database redesigns.
- **No Downstream Auto-Execution**: Do NOT execute Git commands (commit, push) and do NOT automatically execute the next skill (`implementation-to-release`).

---

## Wrong Behavior Detection

**Verify before proceeding:**

```
IF you are about to:
  ✗ Modify source files before the user has typed Y or Yes.
  ✗ Create docs/plans/ or docs/designs/ files.
  ✗ Redesign database schemas or architecture layers.
  ✗ Auto-run git commands.

THEN: STOP immediately.
You are about to violate the Two-Phase Approval Gate.
Ask the user for confirmation or revision details.
```

---

## Fast-Fix Eligibility Rules

Every issue must first be evaluated against the following criteria:

| Category | Fast-Fix Eligible (All Must Pass) | Standard Workflow Required (Any Trigger) |
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
Step 5:  Generate Fix Document (docs/issues/FIX-XXX_issue_name.md)
         ↓
Step 6:  User Approval Gate
         - [STOP] Ask "Continue? [Y/N]" → Wait for user confirmation.
         - If N: halt.
         - If Y: proceed to Step 7.
         ↓
Step 7:  Implementation (Direct minimal code fix)
         ↓
Step 8:  Verification & Testing
         - Run compiler, check builds, run existing unit tests.
         - [STOP] If tests fail → Report failures and halt.
         ↓
Step 9:  Generate Fast-Fix Summary Report & Self-Validation Checklist
```

---

## Detailed Step Instructions

---

### Step 2: Issue Classification & Eligibility Check

Evaluate the user's issue and output the Decision Matrix table:

```markdown
### 🔍 Fast-Fix Eligibility Check

| Category | Evaluation Result |
| :--- | :--- |
| **Scope** | [Small / Medium / Large] |
| **Architecture Impact** | [Low / Medium / High] |
| **ADR Required** | [Yes / No] |
| **Recommended Workflow**| **[Fast Fix / Standard Workflow]** |
```

#### Rejection Rule (Standard Workflow Trigger)

If the **Recommended Workflow** is **Standard Workflow**, you must **STOP** immediately. Print the following message:

```text
❌ This issue exceeds Fast-Fix eligibility criteria.
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

Inspect ONLY the files containing the bug.

---

### Step 5: Generate Fix Document

Only after performing the analysis, calculate the FIX ID and write the document at:
```text
docs/issues/FIX-XXX_issue_name.md
```
*(Replace `XXX` with the calculated FIX ID, and `issue_name` with a lowercase, underscore-separated slug)*

The generated file must follow this template exactly:

```markdown
<!-- File path: docs/issues/FIX-XXX_issue_name.md -->

---
artifact_type: fix
issue_id: FIX-XXX
workflow: fast-fix
architecture_impact: low
adr_required: false
status: draft
---

# Fix Document – [Issue Name]

## 1. Issue
[Detailed description of the reported issue]

## 2. Symptoms
[What symptoms/errors occur, error logs, or UI misbehaviors]

## 3. Root Cause
[Why this bug happened under the hood]

## 4. Scope
- **In Scope**: [Minimal change description]
- **Out of Scope**: [What will NOT be refactored]

## 5. Expected Files
| Action | File Path | Responsibility |
| :--- | :--- | :--- |
| [Modify | Create] | [relative_path] | [Expected role of the change] |

## 6. Proposed Fix
[Detailed textual description of the proposed code edits]

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
Continue?

[Y/N]
```

> [!CAUTION]
> **Do NOT modify any source files until the user explicitly responds Y (or "yes").**
> If the user responds N or requests changes, stop. You may revise the proposed fix based on feedback.

---

### Step 7: Implementation Phase

Only after receiving explicit Y confirmation:
1. Read the generated Fix document at `docs/issues/FIX-XXX_issue_name.md`.
2. Apply the code edits described in the **Proposed Fix** section.
3. Keep changes minimal and focused.

---

### Step 8: Verification & Testing

Verify that your fix builds and compiles. Run test suites.
If compiling or testing fails:
- Print the compiler/test stdout/stderr.
- Do NOT proceed. Output the status: `Failed verification` and stop.

---

### Step 9: Generate Fast-Fix Summary Report

Once tests pass, output the report in Markdown format:

```markdown
### ⚡ Fast-Fix Implementation Summary

| Field | Details |
| :--- | :--- |
| **Issue** | [Brief summary of the issue] |
| **Root Cause** | [Why the bug occurred] |
| **Files Modified** | - [Relative path to file 1](file_link)<br>- [Relative path to file 2](file_link) |
| **Validation Details**| [What compile / manual test checks were performed] |
| **Test Result** | `✅ Build Success & Tests Pass` |
| **Remaining Risks** | [None / List potential edge cases] |

---
**Fast-Fix complete.**
Recommended Next Skill: `implementation-to-release` (must be executed manually).
```

Followed by the Self-Validation Checklist:

```markdown
### 📋 Fast-Fix Self-Validation Checklist

| Validation Item | Status |
| :--- | :---: |
| Issue classified correctly | [ ] PASS |
| Architecture impact assessed | [ ] PASS |
| No brainstorming, planning, blueprint, or ADR files created | [ ] PASS |
| Fix document generated under docs/issues/ | [ ] PASS |
| Only minimal implementation performed (no unrelated refactoring) | [ ] PASS |
| Build success and relevant tests executed | [ ] PASS |
| Implementation summary generated | [ ] PASS |
| Recommended `implementation-to-release` manually | [ ] PASS |

**Result:** `[ALL PASS | FAILED: list failed items]`
```
