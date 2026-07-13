<!-- File path: docs/designs/FEAT-311_workflow_runtime_entry_migration_blueprint.md -->

---
feature_id: FEAT-311
feature_name: Workflow Runtime Entry Command Migration
status: approved
stage: blueprint
created_at: 2026-07-13
updated_at: 2026-07-13
previous_artifact: ../plans/FEAT-311_workflow_runtime_entry_migration_plan.md
next_artifact: [Implementation (Source Code)](../../)
---

# Technical Design Blueprint & Implementation Contract - Workflow Runtime Entry Command Migration

## 0. Baseline Context & References
- **Memory Baseline**: The legacy Resident Orchestrator is deprecated.
- **Inspected Source Files**:
  - `skills/workflow-runtime/scripts/workflow_runtime.py`
  - `skills/workflow-runtime/scripts/event_logger.py`

## 1. File-by-File Analysis & Proposed Mutations
| File Path | Operation | Responsibility | Dependency | Impact & Risk |
| :--- | :--- | :--- | :--- | :--- |
| `skills/workflow-runtime/scripts/workflow_runtime.py` | MODIFY | Implement new subcommands and redirection logic | None | Low |
| `skills/workflow-runtime/scripts/event_logger.py` | MODIFY | Register `workflow.created` event | None | Low |
| `AI_RULES.md` | MODIFY | Update routing enforcement policy | None | Low |

## 2. Target Folder Structure
No folder structure changes required.

## 3. Complete Class & Module Design
No new classes are required. `do_workflow` is updated to handle new CLI subactions.

## 4. Detailed Interface Contracts
- `workflow submit`: returns `{ "workflow_id": "FEAT-XXX", "intent": "feature_request/bug_fix", "status": "CREATED", "next_phase": "brainstorming" }`
- `orchestrator run`: prints deprecation warning and redirects.

## 5. Sequence Flows
- **Submit Flow**:
  1. CLI parsed.
  2. Subcommand `submit` is run.
  3. Detect next feature ID.
  4. Write workflow state.
  5. Emit log events.
  6. Return JSON.

## 13. Complete Test Matrix
- `test_workflow_runtime_entry.py`: Verifies submit, bug_fix submit, and redirect logic.
