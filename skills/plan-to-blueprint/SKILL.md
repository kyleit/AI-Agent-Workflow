---
name: plan-to-blueprint
command: blueprint
aliases:
  - design
  - architecture
category: workflow
tags:
  - blueprint
  - design
  - architecture
version: 2.5.0
author:
  name: Kyle Dang
  email: kyleit@klexpress.net
  website: https://www.klexpress.net
license: MIT
repository: https://gitlab.com/hngan.it/ai-workflow-skills
created_at: 2026-07-03
updated_at: 2026-07-03
description: Generate a production-grade Technical Blueprint from an approved Implementation Plan using a Memory-First strategy and the FEAT-XXX Feature ID format.
---

# Skill: Plan to Blueprint (FEAT-XXX format)

## Role

You are acting as a **Chief Software Architect**, **Senior Solution Architect**, and **Technical Reviewer**.

Your responsibility is to transform an approved implementation plan into a **production-grade Technical Blueprint** suitable for direct implementation by another AI or Senior Engineer.

---

# Objective

Upgrade the implementation plan into a production-grade Technical Blueprint. Do NOT merely transform the plan — act as an architect and reviewer to reduce uncertainty, analyze alternatives, evaluate risks, and enforce high architectural standards.

---

## 🔒 WORKFLOW RUNTIME & INITIALIZATION CHECK

This Skill MUST interface with the centralized Python CLI Runtime Engine:
- **Validate Checkpoint**: Run `python skills/workflow-runtime/scripts/workflow_runtime.py validate --checkpoint "exactly 3"` before taking any action. If validation fails, halt execution immediately.
- **Progress Tracking**:
  - *Start*: Run `python skills/workflow-runtime/scripts/workflow_runtime.py start --skill "plan-to-blueprint" --command "blueprint" --checkpoint 4 --step "Starting execution..."`
  - *Step Updates*: Run `python skills/workflow-runtime/scripts/workflow_runtime.py step --step "<step_desc>" --log "<progress_message>"` progressively during major steps.
  - *Completion*: Run `python skills/workflow-runtime/scripts/workflow_runtime.py complete --checkpoint 4 --step "Step Complete" --next-skill "blueprint-to-implementation" --next-command "implement"` when execution finishes successfully.
  - *Failure*: Run `python skills/workflow-runtime/scripts/workflow_runtime.py fail --step "<error_step>" --log "<error_details>"` if any phase fails.

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

# Input

```yaml
source_brainstorming: docs/brainstorm/FEAT-XXX_feature_slug.md
source_plan: docs/plans/FEAT-XXX_feature_slug_plan.md

workspace: auto

language: auto

tech_stack: auto

architecture: auto

output_path: docs/designs/auto
```

---

# Workflow

## Step 1 — Read Inputs
Read `docs/brainstorm/FEAT-XXX_feature_slug.md` and `docs/plans/FEAT-XXX_feature_slug_plan.md`. Extract **Feature ID**, **Feature Name**, requirements, scope, constraints, and recommendations from both documents.

---

## Step 2 — Read Project Memory
Consult the memory summaries, interfaces, and architecture layers.

---

## Step 3 — RAG Query
Query `project-rag-search` for existing patterns and dependencies.

---

## Step 4 — Targeted Source Inspection (if needed)
Inspect source files directly only if memory gaps remain.

---

## Step 5 — Generate Technical Blueprint
Produce the blueprint. It must include the YAML metadata header and the design specifications:

```markdown
<!-- File path: docs/designs/FEAT-XXX_feature_slug_blueprint.md -->

---
feature_id: FEAT-XXX
feature_name: Human Readable Name
status: reviewed
stage: blueprint
created_at: [YYYY-MM-DD]
updated_at: [YYYY-MM-DD]
previous_artifact: ../plans/FEAT-XXX_feature_slug_plan.md
next_artifact: [Implementation (Source Code)](../../)
---

# Technical Blueprint & Implementation Contract – [Human Readable Name]

## 0. Baseline Context & References
- **Memory Baseline**: [State and confidence levels retrieved from project memory summary]
- **RAG Query Summaries**: [List of vector search query results, matched files, and key findings]
- **Inspected Source Files**: [Target files inspected directly, including line references]

## 1. File-by-File Analysis & Proposed Mutations
All file mutations must be listed explicitly. No generic statements like "modify related files" or placeholders are allowed.

**CRITICAL PATH RULES**:
- Never generate absolute paths or `file://` links. All file references must be relative workspace paths (e.g. `skills/workflow-runtime/scripts/session.py` instead of `/path/to/session.py` or `file:///path/to/session.py`).

| File Path | Operation | Responsibility | Dependency | Impact & Risk |
| :--- | :--- | :--- | :--- | :--- |
| `relative/path/to/file` | `[NEW | MODIFY | DELETE | RENAME]` | `Specific responsibility of the file's logic` | `Dependencies on other modules/files` | `Risk level, migration impacts, side effects` |

## 2. Target Folder Structure
Provide the complete directory tree structure of the workspace showing the exact location of all new/modified files. No folders may be omitted, and placeholders like `...` or `etc.` are strictly forbidden.
```text
.
├── (exact directory structure)
```

## 3. Interface Contracts (Public & Internal)
- **Public Interface Contracts**:
  - *CLI Command Syntax*: `command subcommand [args] [options]` (specify types, optional/required, default values).
  - *REST / GraphQL / RPC API Schema*: Complete request/response JSON schemas, header specs, error codes, HTTP statuses.
  - *Data Models & Database Schema*: Table definitions, columns (types, constraints, nullability), indices, migration script payloads.
  - *Backward Compatibility*: Every schema must preserve backward compatibility with the existing `.agents/.session.json`. If a legacy field exists, the blueprint must define exactly where it migrates.
  - *Enum Constraint*: Do not invent unsafe enum values. For `permission_mode`, only allow: `sandbox`, `full_access`. Never allow `unrestricted`.
- **Internal Component Contracts**:
  - *Module/Class Signatures*: Interfaces, classes, types, function signatures with exact input types, output types, and thrown exception/error types.
- **Extension Changes (if applicable)**:
  If the feature modifies the VSCode / Antigravity extension, the blueprint MUST define:
  - *ViewModel Schema*: The exact UI model structure.
  - *File Watch Strategy*: How and when the extension watches state files.
  - *Debounce Behavior*: Throttle/debounce settings for UI updates.
  - *Fallback Order*: The sequence of settings to resolve if files are missing.
  - *Missing/Corrupted State UI*: UI representation when state files are empty or corrupted.
  - *Partial Refresh Rules*: Which components are refreshed instead of full reload.

## 4. Algorithms & Logic Specifications
Describe all non-trivial logic (search, routing, state transition, retry, synchronization, data diffing).
- *Algorithm Flow / Pseudo-code*: Complete pseudo-code or step-by-step logic.
- *Pseudo-code Path Validation*: `.agents/.session.json` must never become `.agents/session.json`. Validate all paths used.
- *Error Handling & Recovery*: Fallback behavior, retry policies (exponential backoff, max retries), circuit breakers.

## 5. State Machine & Transitions
If the feature modifies workflow state, define the exact state machine:
- *States*: `State A`, `State B`, `etc.`
- *Transitions*: `State A` --(Event)--> `State B`
- *Abnormal Conditions*: Resume checkpoint rules, rollback mechanics, failure/timeout recovery paths.

## 6. Validation and Safety Constraints
- *Input Validation Rules*: Format validation, length, types, regex checks, range limits.
- *Permission / Security Checks*: Required authentication, token checks, directory restriction gates (sandbox verification).

## 7. Backward Compatibility & Migration Mapping
Every blueprint must include this section if state schemas or files are modified:
| Old Field | New File | New Field | Migration Rule | Recovery Rule |
| :--- | :--- | :--- | :--- | :--- |
| `legacy_field` | `relative/path/to/new_file` | `new_field` | `How old field translates to new field` | `Rollback strategy if migration fails` |

## 8. Implementation Checklist
Provide an objectively verifiable, step-by-step list of tasks.
- [ ] Task 1...
- [ ] Task 2...

## 9. Acceptance Criteria & Test Mapping
Every implementation requirement must map directly to validation test assertions.
**CRITICAL RULE**: Acceptance Criteria must cover every requirement. If the blueprint claims N tests, all N must be listed and mapped. Rushing or grouping tests like "Task 2..11" is strictly forbidden.

| Requirement ID | Requirement Description | Expected Result | Verification Method | Unit/Integration Test Target |
| :--- | :--- | :--- | :--- | :--- |
| `REQ-001` | `Description` | `Exact outcome` | `Automated/Manual Command` | `Target test file & assertion name` |

## 10. Disallowed Outputs Validation
Verify and ensure the following outputs are NOT present in this blueprint:
- [ ] No `file://` or absolute paths used.
- [ ] No placeholders like `...` or `etc.` in code/structures.
- [ ] No `TBD` or `To Be Determined` placeholders.
- [ ] No unsafe permission values (e.g. `unrestricted`).
- [ ] No unmapped legacy fields without migration rules.
```

---

# Output Rules

Create exactly one file:
```
docs/designs/FEAT-XXX_feature_slug_blueprint.md
```

First line must be:
```html
<!-- File path: docs/designs/FEAT-XXX_feature_slug_blueprint.md -->
```

---

# Constraints

- Do NOT implement business logic.
- Do NOT skip sections.
- Keep naming consistent with project (from memory).
- **Do NOT create ADR files**. Only assess and recommend if they are required.
- **Run a self-review of the generated blueprint against the "Disallowed Outputs Validation" checklist and fix all violations before saving.**

---

# IDE Skill Hardening & Boundary Rules

## 1. Single Responsibility
Convert an approved Implementation Plan into a detailed Technical Blueprint. Once `docs/designs/FEAT-XXX_feature_slug_blueprint.md` is generated, STOP.

## 2. Never Execute Next Phase
Do NOT invoke `blueprint-to-implementation` or `create-adr`. Only recommend.

## 3. Workspace Modification Policy
Only create or update the target Technical Blueprint file.

---

## Completion Contract

```text
Current Phase:
Phase 3 — Plan to Blueprint

Status:
Completed

Memory Confidence:
[High | Medium | Low]

Memory Documents Read:
[list]

RAG Queries:
[list of queries and key findings]

Source Files Inspected:
[list or "None — all context from memory"]

Generated Output:
docs/designs/FEAT-XXX_feature_slug_blueprint.md

Recommended Next Skill:
[create-adr (if ADR Required = Yes) | blueprint-to-implementation (if ADR Required = No)]

Workflow Paused.
```
