<!-- docs/brainstorming/FEAT-010_workflow_runtime_engine.md -->

---
feature_id: FEAT-010
feature_name: AI Workflow Runtime Engine Refactor
status: draft
stage: brainstorming
created_at: 2026-07-06
updated_at: 2026-07-06
previous_artifact: None
next_artifact: ../plans/FEAT-010_workflow_runtime_engine_plan.md
---

# Master Requirement Document – AI Workflow Runtime Engine Refactor

## 1. Feature ID & Name
- **Feature ID**: FEAT-010
- **Feature Name**: AI Workflow Runtime Engine Refactor

## 2. Original Idea
Refactor the AI Workflow Runtime from a Prompt-Driven Runtime into an executable Runtime Engine in Python, exposing modular commands, verifying session states, updating logs/checkpoints, estimating token usage, checking context drift, and validating Git states while remaining 100% backward compatible.

## 3. Business Problem
- **Problem**: Logic describing `.session.json` schema updates, progressive logging, context usage calculations, and check-point transitions is currently duplicated across the prompts of 26 skills. This results in heavy token overhead, maintenance complexity, and potential logic divergence between different skills.
- **Why it matters**: Higher token overhead slows down model execution and is expensive. Decentralized runtime logic makes updating the state machine or integrating it into MCP/IDE plugins difficult and risky.
- **Expected outcome**: All runtime logic is extracted into a modular Python engine under `skills/workflow-runtime/scripts/`. Every skill calls this CLI wrapper (`runtime init`, `runtime start`, `runtime step`, `runtime complete`, `runtime fail`) instead of describing the json edits. Prompt token payload decreases significantly. Extension compatibility remains 100% untouched.

## 4. Requirement Discovery
- **Functional Requirements**:
  - FR-01: Modular architecture: Python-based Runtime Engine structured into clean files with a maximum of 200 lines per file.
  - FR-02: Command API exposure: Must support `init`, `validate`, `heartbeat`, `start`, `checkpoint`, `step`, `complete`, `fail`, `resume`, `context`, and `report` commands with parameters.
  - FR-03: Backward compatibility: The JSON structure inside `.agents/.session.json` must remain exactly as defined (preserving conversation_id, checkpoint, status, etc.).
  - FR-04: Atomic writing: Write updates to `.session.json.tmp` first, then rename.
  - FR-05: Context usage: Automatically estimate current conversation token usage using the log file size.
  - FR-06: Context drift: Automatically validate Git branch, project version, active work item, and directory health.
- **Non-functional Requirements**:
  - NFR-01: Zero changes to orchestrator checkpoint transitions or user SDLC workflow.
  - NFR-02: Modular CLI architecture that is future-ready to be wrapped as Go binary, Node.js command, MCP Tool, or VSCode Command.
- **Technical Constraints**:
  - TC-01: CLI must run on Windows/macOS/Linux.
  - TC-02: Complete unit tests must validate concurrent writes, corrupted sessions, and resume features.

## 5. Clarification Questions & Answers
| Question | Answer |
|---|---|
| What is the maximum line limit per script file? | Max 200 lines. |
| Where do runtime scripts live? | Under `skills/workflow-runtime/scripts/`. |
| Do we update all 26 skills? | Yes, every skill must be updated to call the new CLI. |

## 6. Requirement Readiness Score
- **Score**: 100/100
- **Status**: Ready (>= 85)

## 7. Existing Project Context
- **Memory Source**: [project-summary.md](file:///e:/Cloud/_protected/agents/.agents/memory/project-summary.md)
- **Existing Architecture Summary**: Prompt-driven session state updates defined in skills. Visualizer extension watches `.agents/.session.json`.

## 8. Existing Modules & Services
| Module/Service | Location | Relevance |
|---|---|---|
| Workflow Runtime | [skills/workflow-runtime/](file:///e:/Cloud/_protected/agents/skills/workflow-runtime/) | Destination for runtime scripts. |
| Skills Directory | [skills/](file:///e:/Cloud/_protected/agents/skills/) | All 26 skills calling the CLI. |

## 9. Solution Options Evaluated

### Option A: Python-based Modular CLI Engine
- **Overview**: Create `workflow_runtime.py`, `session.py`, `context.py`, `checkpoint.py`, `validator.py`, `heartbeat.py`, `drift.py`, and `utils.py` under `skills/workflow-runtime/scripts/`. Expose a clean command boundary. Update every skill to call this CLI.
- **Advantages**: Highly maintainable, modular, fits constraints, future-ready for MCP.
- **Complexity**: High
- **Risk**: Low (behavior-preserving)
- **Performance**: High (major token savings)

### Option B: Monolithic Python Script
- **Overview**: A single large script doing everything.
- **Disadvantages**: Violates the 200-line constraint, hard to maintain.

## 10. Selected Solution
- **Choice**: Option A — Python-based Modular CLI Engine.
- **Why Selected**: Fulfills all architecture, line-count, and modularity requirements.

## 11. Risks & Assumptions
- **Assumptions**: Python 3.9+ is available in the environment.

## 12. Acceptance Criteria
- [ ] Implement `skills/workflow-runtime/scripts/` files with `< 200` lines each.
- [ ] Implement unit tests validating all commands and recovery cases.
- [ ] Refactor all 26 skills to run `runtime` commands instead of editing json.
- [ ] Run `update.ps1 -Force` and `doctor.ps1` with zero failures.
- [ ] Produce `docs/runtime_refactor_report.md` detailing the migration.
