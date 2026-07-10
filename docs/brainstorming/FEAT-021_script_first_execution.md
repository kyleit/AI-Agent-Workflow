---
feature_id: FEAT-021
feature_name: Script-First Execution Refactoring
status: draft
stage: brainstorming
created_at: 2026-07-08
updated_at: 2026-07-08
previous_artifact: None
next_artifact: ../plans/FEAT-021_script_first_execution_plan.md
---

# Master Requirement Document – Script-First Execution Refactoring

## 1. Feature ID & Name
- **Feature ID**: FEAT-021
- **Feature Name**: Script-First Execution Refactoring

## 2. Original Idea
Refactor deterministic, repeatable, file-based, validation-based, and state-management work to be executed by Python CLI scripts instead of LLM prompt instructions, keeping LLM logic only for reasoning and content generation.

## 3. Business Problem
- **Problem**: Deterministic actions (validation, checking files, running compilation/tests, parsing Git, scanning technologies) are currently executed by the LLM manually in natural language or prompt instructions. This wastes significant token counts, introduces errors/hallucinations, cannot be easily automated/tested, and runs slowly.
- **Why it matters**: Automating these checks via Python CLI scripts reduces token overhead, guarantees 100% deterministic success, and improves reliability.
- **Who is affected**: AI engineering agents and developers using the AI Workflow Framework.
- **Expected outcome**: Fully scripted subcommands under the `workflow_runtime.py` engine covering initialization, resumption, stack discovery, memory bootstrap/sync/search, environmental validation, debug/verify runners, and release planning.

## 4. Requirement Discovery
- **Functional Requirements**:
  * **FR-01**: Implement `discover` command to auto-detect language, compiler, packages, framework, and generate `.agents/project-profile.json`.
  * **FR-02**: Port project memory scripts (bootstrap, update, search) from `runtime/scripts/project_memory` to `skills/workflow-runtime/scripts/memory/`.
  * **FR-03**: Create `env health` script to detect local tools, PATH issues, and config parameters.
  * **FR-04**: Implement validation runner (`debug run` & `verify run`) to check build, lint, typecheck, tests, and compliance gates.
  * **FR-05**: Implement release manager (`release plan` & `release execute`) to check version preflights, changelogs, and tag/push approvals.
  * **FR-06**: Ensure all CLI commands return formatted JSON output.
- **Non-functional Requirements**:
  * **NFR-01**: Commands must be cross-platform compatible (running on Windows and Unix).
  * **NFR-02**: Fast execution with JSON outputs to keep token usage down.
- **Technical Constraints**:
  * Python 3.10+ standard libraries should be used to minimize external dependencies.

## 5. Clarification Questions & Answers
| Question | Answer |
|---|---|
| Should we keep the existing `project_memory` code under `runtime/`? | Yes, but we copy/move it to `skills/workflow-runtime/scripts/memory/` and make sure CLI commands call it from the new location. |
| Is permission mode configuration sandbox by default? | Yes, defaults to sandbox. |

## 6. Requirement Readiness Score
- **Score**: 100/100
- **Status**: Ready >= 85

## 7. Existing Project Context
- **Memory Source**: [project-summary.md](file:///e:/AgentsProject/.agents/memory/project-summary.md)
- **Existing Architecture Summary**: The `workflow_runtime.py` script serves as the state controller, managing `.session.json` and interacting with SQLite.

## 8. Existing Modules & Services
| Module/Service | Location | Relevance |
|---|---|---|
| CLI Runtime Engine | `skills/workflow-runtime/scripts/workflow_runtime.py` | Central entrypoint parser to extend |
| Project Memory Engine | `runtime/scripts/project_memory/` | Source of logic to integrate |

## 9. Solution Options Evaluated

### Option A: Centralized Subcommands Router in workflow_runtime.py (Selected)
- **Overview**: Add commands directly in `workflow_runtime.py` using subparsers, delegating actual work to new Python files under `scripts/`.
- **Architecture**: Single CLI executable, clean routing.
- **Advantages**: State and session management utilities are reused.
- **Disadvantages**: Minor increase in entrypoint code size.
- **Complexity**: Low
- **Risk**: Low

### Option B: Standalone Python scripts
- **Overview**: Each command has its own file.
- **Advantages**: Highly modular.
- **Disadvantages**: Duplicate session load/save logic.
- **Complexity**: Medium

## 10. Solution Comparison Table
| Criteria | Option A | Option B |
|---|---|---|
| Complexity | Low | Medium |
| Risk | Low | Low |
| Performance | High | High |
| Maintainability | High | Medium |
| Compatibility | High | Low |
| Future Scalability | High | Medium |
| Development Cost | Low | Medium |

## 11. Selected Solution
- **Choice**: Option A — Centralized Subcommands Router in workflow_runtime.py
- **Why Selected**: Avoids code duplication for napping/writing the session state.

## 12. Risks & Assumptions
- **Risks**: Windows path issues and encoding conflicts when executing shell commands.
- **Assumptions**: Python path is correctly configured.

## 13. Acceptance Criteria
- [ ] Subcommands (`init`, `resume`, `discover`, `classify`, `memory`, `env`, `validate`, `debug`, `verify`, `release`) verified with unit tests.
- [ ] All commands return standard structured JSON.
- [ ] Workspace copies in `.agents/` kept in sync.

---

## 14. Final Planning Prompt

### Purpose
Trigger planning phase for FEAT-021.

### Objectives & Selected Solution
Implement Python scripts under `skills/workflow-runtime/scripts/` and extend CLI subparsers in `workflow_runtime.py` to route all commands.

### Verification Checklist
- [ ] docs/plans/FEAT-021_script_first_execution_plan.md generated and approved
- [ ] test_script_first.py unit tests pass 100%
