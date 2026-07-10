<!-- docs/brainstorming/FEAT-019_selectable_execution_mode.md -->

---
feature_id: FEAT-019
feature_name: User Selectable Execution Mode (Parallel vs Sequential)
status: draft
stage: brainstorming
created_at: 2026-07-07
updated_at: 2026-07-07
previous_artifact: None
next_artifact: ../plans/FEAT-019_selectable_execution_mode_plan.md
---

# Master Requirement Document – User Selectable Execution Mode

## 1. Feature ID & Name
- **Feature ID**: FEAT-019
- **Feature Name**: User Selectable Execution Mode (Parallel vs Sequential)

## 2. Original Idea
Refactor and improve the existing Orchestrator implementation to make the execution mode user-controlled instead of automatically choosing parallel execution. The Orchestrator will analyze whether parallel execution is safe and recommend a mode, but the final decision (Parallel, Sequential, Re-split, or Cancel) always belongs to the user.

## 3. Business Problem
- **Problem**: Automatic parallel execution might be risky or hard to debug under certain circumstances. Users need control over the execution mode to balance speed, debuggability, and safety.
- **Why it matters**: Improves framework safety, gives users control over resource/token spending, and makes debugging concurrent executions simpler.
- **Who is affected**: Developers and AI Agents utilizing the `/orchestrate` workflow.
- **Expected outcome**: User selects the mode via an interactive gate before execution begins.

## 4. Requirement Discovery
- **Functional Requirements**:
  - FR-01: Update `AI_RULES.md` to define the "User Execution Mode Policy".
  - FR-02: Orchestrator displays an Execution Plan Summary and prompts the user to select the mode (Parallel, Sequential, Re-split, Cancel).
  - FR-03: Option 1 (Parallel) runs tasks concurrently using lock checks. Option 2 (Sequential) runs tasks one by one in DAG order. Option 3 (Re-split) regenerates task splits. Option 4 (Cancel) halts immediately.
  - FR-04: Extend `execution-plan.json` with execution mode properties: `execution_mode`, `recommended_mode`, `recommended_reason`, and `approved`.
  - FR-05: Extend `parallel-tasks.json` with `execution_group` property.
  - FR-06: Extend `workflow-runtime` CLI with commands: `execution recommend`, `execution mode`, `execution summary`.
  - FR-07: Real-time Visualizer updates.
  - FR-08: Resume workflow restores execution mode and task states without re-prompting if already approved.
- **Non-functional Requirements**:
  - NFR-01: Complete backward compatibility with existing skills and runtime schemas.
  - NFR-02: Atomicity in runtime JSON file writes.

## 5. Clarification Questions & Answers
| Question | Answer |
|---|---|
| Nếu chạy tuần tự (Sequential), các nhóm thực thi song song (execution_group) có bị bỏ qua không? | Có, chạy tuần tự sẽ bỏ qua `execution_group` và chạy theo thứ tự tô-pô của DAG. |

## 6. Requirement Readiness Score
- **Score**: 100/100
- **Status**: Ready

## 7. Existing Project Context
- **Memory Source**: [project-summary.md](file:///Volumes/Kyle/AgentsProject/.agents/memory/project-summary.md)
- **Existing Architecture Summary**: CLI runtime engine in Python managing state and lock registry.

## 8. Existing Modules & Services
| Module/Service | Location | Relevance |
|---|---|---|
| Orchestrator | `skills/orchestrator/` | Nhận yêu cầu và lập kế hoạch DAG. |
| Workflow Runtime | `skills/workflow-runtime/` | Quản lý khóa tệp và lưu trạng thái checkpoint. |

## 9. Solution Options Evaluated

### Option A: CLI-extended Caching & Config Schema (Selected)
- **Overview**: Implement `execution` subcommands in `workflow_runtime.py`. Orchestrator writes the plan with `approved: false` and `recommended_mode` to `execution-plan.json`, then prompts the user and saves the selected mode using CLI.
- **Advantages**: Atomic updates, clean state restore on resume, works across IDE extensions.
- **Complexity**: Medium
- **Risk**: Low

### Option B: Pure Prompt-State Verification
- **Overview**: Orchestrator LLM manages the prompt selection entirely in the chat interface and writes the final approved state directly.
- **Advantages**: No CLI changes.
- **Disadvantages**: Breaks state synchronization on resume.
- **Complexity**: High
- **Risk**: High

## 10. Solution Comparison Table
| Criteria | Option A | Option B |
|---|---|---|
| Complexity | Medium | High |
| Risk | Low | High |
| Performance | High | Low |
| Scalability | High | Low |

## 11. Selected Solution
- **Choice**: Option A — CLI-extended Caching & Config Schema
- **Why Selected**: Ensures robust, atomic state serialization which is crucial for workflow recovery (resume) and real-time visualization.

## 12. Risks & Assumptions
- **Risks**:
  - R-01: Session drift if files change between plan approval and execution start → Mitigated by validation checks on resume.

## 13. Acceptance Criteria
- [ ] User is prompted to select execution mode before any tasks run.
- [ ] Selecting Parallel executes concurrent tasks safely.
- [ ] Selecting Sequential runs tasks one-by-one in DAG order.
- [ ] Resume restore works without re-prompting if already approved.
- [ ] Backward compatibility with existing projects is fully preserved.

---

## 14. Final Planning Prompt

### Purpose
Complete prompt for the `brainstorming-to-plan` Skill to implement user-controlled execution mode.

### Objectives & Selected Solution
Implement selectable execution modes under Option A. Extend `workflow_runtime.py` with `execution` commands, update Orchestrator SKILL.md, and update Visualizer state.

### Functional Requirements
- Support execution modes: parallel, sequential.
- Serialized state in `execution-plan.json` and `parallel-tasks.json`.
- Task grouping (`execution_group`) for parallel runs.
