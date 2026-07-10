---
name: brainstorming-to-plan
command: plan
aliases:
  - planning
  - planning-phase
category: workflow
tags:
  - planning
  - workflow
  - scoping
version: 3.2.0
author:
  name: Kyle Dang
  email: kyleit@klexpress.net
  website: https://www.klexpress.net
license: MIT
repository: https://gitlab.com/hngan.it/ai-workflow-skills
created_at: 2026-07-03
updated_at: 2026-07-09
description: Convert a structured master brainstorming document into a formal Execution Plan (Markdown & JSON) using a Memory-First strategy and the FEAT-XXX Feature ID format.
---

# Skill: Planning Prompt → Implementation Plan (FEAT-XXX format)

## Purpose

Execute a planning prompt from a master brainstorming document and generate a complete, production-ready Implementation Plan under `docs/plans/`.

This Skill must NOT generate:
- Technical Blueprint (Design)
- Architecture Decision Records (ADRs)
- Source code
- Tests

Its only responsibility is creating the implementation planning document.

---

## Role

You are acting as a **Senior Software Architect**, **Technical Planner**, and **System Analyst**.

Your responsibility is to produce a production-ready Implementation Plan with the **lowest possible token usage** by reading memory before reading source code.

---

## Input

```yaml
prompt_file: docs/brainstorm/FEAT-XXX_feature_slug.md
# Path to the brainstorming/requirement discovery file containing the planning prompt

workspace: auto

language: auto

framework: auto

architecture: auto

output_path: docs/plans/auto
```

---

## 🔒 WORKFLOW RUNTIME & INITIALIZATION CHECK

This Skill MUST interface with the centralized Python CLI Runtime Engine:
- **Validate Checkpoint**: Run `python skills/workflow-runtime/scripts/workflow_runtime.py validate --checkpoint "exactly 3 or 2"` before taking any action. If validation fails, halt execution immediately.
- **Progress Tracking**:
  - *Start*: Run `python skills/workflow-runtime/scripts/workflow_runtime.py start --skill "brainstorming-to-plan" --command "plan" --checkpoint 3 --step "Starting execution..."`
  - *Step Updates*: Run `python skills/workflow-runtime/scripts/workflow_runtime.py step --step "<step_desc>" --log "<progress_message>"` progressively during major steps.
  - *Completion*: Run `python skills/workflow-runtime/scripts/workflow_runtime.py complete --checkpoint 3 --step "Step Complete" --next-skill "plan-to-blueprint" --next-command "blueprint"` when execution finishes successfully.
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

# Workflow

## Step 1 — Read Master Requirement Document
Read the brainstorming file at:
```
docs/brainstorming/FEAT-XXX_feature_slug.md
```
Extract the **Feature ID**, **Feature Name**, **MoSCoW Prioritization**, and the **Planning Prompt** section from it.

---

## Step 2 — Read Project Memory
Consult the memory summary and files to check the target codebase design and conventions.

---

## Step 3 — RAG Query
Query `project-rag-search` with the feature name and related keywords.

---

## Step 4 — Targeted Source Inspection (if needed)
Inspect only files explicitly referenced by memory or RAG.

---

## Step 5 — Generate Implementation Plan
Generate the plan document. It must contain the YAML metadata header and the plan sections. Planner MUST directly use the MoSCoW prioritization defined in the brainstorming document to group requirements into implementation phases (e.g., all 'Must' requirements must be placed in Phase 1, 'Should' in Phase 2, etc.) without re-analyzing architecture or scope:

```markdown
<!-- File path: docs/plans/FEAT-XXX_feature_slug_plan.md -->

---
feature_id: FEAT-XXX
feature_name: Human Readable Name
status: reviewed
stage: planning
created_at: [YYYY-MM-DD]
updated_at: [YYYY-MM-DD]
previous_artifact: ../brainstorming/FEAT-XXX_feature_slug.md
next_artifact: ../designs/FEAT-XXX_feature_slug_blueprint.md
---

# FEAT-XXX: [Human Readable Name]

## 1. Requirement Coverage Matrix
| Req ID | Phase | Task ID | Deliverable | Covered? |
| :--- | :--- | :--- | :--- | :---: |
| FR-01 | Phase 1 | Task 1.1 | [...] | [x] |
| FR-02 | Phase 1 | Task 1.2 | [...] | [x] |

## 2. Task Ownership & Roles
Phân bổ người chịu trách nhiệm thực thi các tác vụ (Architect, Coder, Reviewer, Verifier, Documentation, Runtime):
- **Task 1.1**: [Coder] - Triển khai...
- **Task 1.2**: [Architect] - Thiết kế...

## 3. Parallel Execution Plan
- **Sequential Tasks**: Task 1.1 -> Task 1.2
- **Parallel Tasks**: [Task 1.3, Task 1.4]
- **Blocking Tasks**: Task 2.1 (blocks Task 2.2)
- **Independent Tasks**: Task 3.1
- **Recommended Execution Groups**:
  - Group 1: Task 1.1
  - Group 2: Task 1.3, Task 1.4 (Parallel)

## 4. File Change Plan (Implementation Boundary)
| Task ID | File Path | Operation (Create/Modify/Delete/Do Not Modify) | Rationale |
| :--- | :--- | :--- | :--- |
| Task 1.1 | `skills/knowledge-runtime/scripts/...` | Create | Tạo cấu trúc gói |

## 5. Blueprint Preparation Inputs
Cung cấp định hướng cho pha Blueprint thiết kế chi tiết:
- **Interfaces / Classes / Modules**: [...]
- **Provider Pattern details**: [...]
- **Data Flow / Sequence Flow**: [...]
- **Migration Strategy & Testing Architecture**: [...]

## 6. Verification Strategy & Test Mapping
- **Unit Tests**: [...] (Mapped to Task 1.1)
- **Integration Tests**: [...] (Mapped to Task 2.1)
- **Compatibility / Regression Tests**: [...]

## 7. Exit Criteria
- **Phase 1 Exit Criteria**:
  - [ ] 100% Unit Tests vượt qua (Pass).
  - [ ] Giao diện API được cài đặt đầy đủ.
- **Phase 2 Exit Criteria**:
  - [ ] Đồ thị liên kết backlinks được cập nhật đúng.

## 8. Rollback Strategy
- **Phase 1 Rollback**:
  - Trigger: Gặp lỗi kiểm thử hệ thống nghiêm trọng không thể khắc phục nhanh.
  - Steps: Revert git commit, khôi phục cấu hình tri thức cũ.
  - Recovery: Trả về trạng thái hoạt động bình thường trên main.

## 9. Change Impact Matrix
| Task ID | Files | Modules | Runtime | Extension | Documentation | Memory | Database |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Task 1.1 | Yes | Yes | No | No | Yes | Yes | No |

## 10. Artifact Production Plan
- **Phase 1 Artifacts**: docs/designs/FEAT-XXX_blueprint.md
- **Phase 2 Artifacts**: docs/adr/ADR-XXX.md, docs/releases/Release_Notes.md

## 11. Token & Execution Optimization
- **Sequential execution cost**: [...]
- **Parallel execution opportunities**: [...]
- **Expected token savings**: [...]
- **Recommended execution strategy**: [...]

## Recommended Next Skill
/blueprint
```

---

# Output Rules

Create exactly two files:
1. `docs/plans/FEAT-XXX_feature_slug_plan.md`
2. `docs/plans/FEAT-XXX_feature_slug_plan.json`

First line of the Markdown file must be:
```html
<!-- File path: docs/plans/FEAT-XXX_feature_slug_plan.md -->
```

The JSON file must conform to this schema:
```json
{
  "phases": [
    {
      "phase_name": "Phase 1: ...",
      "tasks": ["Task 1.1", "Task 1.2"],
      "deliverables": ["..."],
      "milestones": ["..."]
    }
  ],
  "tasks": [
    {
      "id": "Task 1.1",
      "description": "...",
      "effort_hours": 4,
      "owner": "Coder",
      "operations": ["NEW", "MODIFY"],
      "files": ["relative/path/to/file"]
    }
  ],
  "dependencies": {
    "Task 1.2": ["Task 1.1"]
  },
  "parallel_groups": [
    ["Task 1.3", "Task 1.4"]
  ],
  "exit_criteria": ["..."],
  "rollback": {
    "trigger": "...",
    "steps": ["..."]
  },
  "tests": [
    {
      "test_target": "relative/path/to/test_file.py",
      "mapped_tasks": ["Task 1.1"]
    }
  ],
  "artifacts": ["docs/designs/FEAT-XXX_blueprint.md"]
}
```

---

# Constraints

- Do NOT describe technical implementation.
- Do NOT define classes, functions, or interfaces.
- Do NOT define APIs, database schemas, SQL, or folder structures.
- Do NOT generate pseudo-code.
- Planning must remain understandable by both technical and non-technical stakeholders.
- Keep the plan concise and focused entirely on project management.

---

# IDE Skill Hardening & Boundary Rules

## 1. Single Responsibility
Convert a master brainstorming planning prompt into a formal Implementation Plan. Once `docs/plans/FEAT-XXX_feature_slug_plan.md` is generated, STOP.

## 2. Never Execute Next Phase
Do NOT invoke `plan-to-blueprint` or any other Skill.

## 3. Workspace Modification Policy
Only create or update the target implementation plan file. No source code changes.

---

## Completion Contract

```text
Current Phase:
Phase 2 — Planning Prompt to Plan

Status:
Completed

Memory Status:
[Fresh | Medium | Low]

Memory Confidence:
[High | Medium | Low]

Memory Documents Read:
[list]

RAG Query:
[query text used]

Source Files Inspected:
[list or "None — answered from memory"]

Generated Output:
docs/plans/FEAT-XXX_feature_slug_plan.md

Recommended Next Skill:
plan-to-blueprint

Workflow Paused.
```
