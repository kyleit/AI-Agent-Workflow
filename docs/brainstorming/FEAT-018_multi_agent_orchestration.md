<!-- docs/brainstorming/FEAT-018_multi_agent_orchestration.md -->

---
feature_id: FEAT-018
feature_name: Multi-Agent Orchestration Framework
status: draft
stage: brainstorming
created_at: 2026-07-07
updated_at: 2026-07-07
previous_artifact: None
next_artifact: ../plans/FEAT-018_multi_agent_orchestration_plan.md
---

# Master Requirement Document – Multi-Agent Orchestration Framework

## 1. Feature ID & Name
- **Feature ID**: FEAT-018
- **Feature Name**: Multi-Agent Orchestration Framework

## 2. Original Idea
Create a new core Skill named skills/orchestrator/ which becomes the central brain of the entire framework. Users will invoke only `/orchestrate` and the Orchestrator will automatically understand the request, discover the project, inspect current workflow state, inspect Project Memory and RAG, determine workflow and required Skills/Agents, split work, schedule work, prevent conflicts, coordinate execution, merge outputs, validate, and report progress.

## 3. Business Problem
- **Problem**: Manual invocation of multiple Skills is complex, error-prone, and requires deep familiarity with the inner workings of the SDLC framework.
- **Why it matters**: Limits developer productivity, increases cognitive load, and slows down autonomous development loops.
- **Who is affected**: AI Coding Agents and developers interacting with this framework.
- **Expected outcome**: A single command entry point `/orchestrate` that autonomously handles the entire workspace lifecycle.

## 4. Requirement Discovery
- **Functional Requirements**:
  - FR-01: Auto-detect intent and map to appropriate workflow (Quick Fix, Quick Feature, Large Feature, Memory, Release, etc.).
  - FR-02: Parallel planner to split tasks with explicit read/write sets.
  - FR-03: Dependency Graph (DAG) construction and execution scheduling.
  - FR-04: File locking and conflict resolution mechanisms.
  - FR-05: Integrate orchestrator as the primary MANIFEST entry point.
- **Non-functional Requirements**:
  - NFR-01: Parallel execution efficiency and minimal overhead.
  - NFR-02: Backward compatibility for existing worker skills.
- **Technical Constraints**:
  - TC-01: Sandboxed file modification verification.
  - TC-02: Clean state updates via `workflow-runtime` CLI.

## 5. Clarification Questions & Answers
| Question | Answer |
|---|---|
| Cấu trúc khóa tệp có lưu trong db không? | Không, lưu ở tệp tin `.agents/runtime/file-locks.json` để đồng bộ nhanh. |

## 6. Requirement Readiness Score
- **Score**: 100/100
- **Status**: Ready

## 7. Existing Project Context
- **Memory Source**: [project-summary.md](file:///Volumes/Kyle/AgentsProject/.agents/memory/project-summary.md)
- **Existing Architecture Summary**: Python-based CLI runtime engine managing `.session.json` and SQLite database metrics.

## 8. Existing Modules & Services
| Module/Service | Location | Relevance |
|---|---|---|
| Workflow Runtime | `skills/workflow-runtime/` | Quản lý phiên chạy và lưu trạng thái checkpoint. |

## 9. Solution Options Evaluated

### Option A: CLI-integrated Script-First Orchestrator (Selected)
- **Overview**: Core orchestration engine built in Python as part of the `workflow-runtime` package, utilizing native lock management and subprocess coordination. Giao diện LLM được định nghĩa tại `skills/orchestrator/SKILL.md` để sinh kế hoạch `execution-plan.json` và kích hoạt CLI.
- **Advantages**: Robust process sandboxing, structured SQLite metrics logging, fast execution.
- **Disadvantages**: Requires updates to `workflow_runtime.py`.
- **Complexity**: Medium
- **Risk**: Low

### Option B: Pure Prompt-Based Agent Orchestrator
- **Overview**: Entirely prompt-driven coordination inside `skills/orchestrator/SKILL.md` using LLM loops.
- **Advantages**: Minimum runtime code changes.
- **Disadvantages**: Fragile concurrency handling, high latency, extremely high token costs.
- **Complexity**: High
- **Risk**: High

## 10. Solution Comparison Table
| Criteria | Option A | Option B |
|---|---|---|
| Complexity | Medium | High |
| Risk | Low | High |
| Performance | High | Low |
| Maintainability | High | Low |
| Compatibility | High | High |
| Future Scalability | High | Low |
| Development Cost | Medium | High |

## 11. Selected Solution
- **Choice**: Option A — CLI-integrated Script-First Orchestrator
- **Why Selected**: Provides native process scheduling, robust file-locking mechanisms, and clean integration with the framework's SQLite storage.

## 12. Risks & Assumptions
- **Risks**:
  - R-01: Overlapping write sets cause data corruption → Mitigated by strict file-lock checks prior to execution.
- **Assumptions**:
  - A-01: IDE/client platform supports running multiple tool executions in parallel.

## 13. Acceptance Criteria
- [ ] User runs `/orchestrate` successfully.
- [ ] DAG is generated and independent tasks run in parallel.
- [ ] File locks are verified and write conflicts are prevented.
- [ ] Existing skills remain fully functional when called directly.

---

## 14. Final Planning Prompt

### Purpose
Complete prompt for the `brainstorming-to-plan` Skill to implement the Orchestrator.

### Objectives & Selected Solution
Implement `skills/orchestrator/` under Option A. Extend `workflow_runtime.py` with orchestration commands (DAG, locking, execution). Update manifest, update worker skills.

### Functional Requirements
- Implement DAG construction and parallel processes runner.
- Manage `file-locks.json` during task runs.
- Integrate with `/orchestrate` slash command.

### Verification Checklist
- [ ] docs/plans/FEAT-018_multi_agent_orchestration_plan.md generated and approved
- [ ] docs/designs/FEAT-018_multi_agent_orchestration_blueprint.md generated and approved
