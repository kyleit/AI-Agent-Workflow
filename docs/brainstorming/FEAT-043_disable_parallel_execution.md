<!-- docs/brainstorming/FEAT-043_disable_parallel_execution.md -->

---
feature_id: FEAT-043
feature_name: Disable Parallel Execution and Emergency Lockdown
status: draft
stage: brainstorming
created_at: 2026-07-09
updated_at: 2026-07-09
previous_artifact: None
next_artifact: ../plans/FEAT-043_disable_parallel_execution_plan.md
---

# Master Requirement Document – Disable Parallel Execution and Emergency Lockdown

## 1. Feature ID & Name
- **Feature ID**: FEAT-043
- **Feature Name**: Disable Parallel Execution and Emergency Lockdown

## 2. Original Idea
```text
# Agent Execution Prompt: Emergency Lockdown - Disable Parallel Execution

## Role

You are the Runtime Architect responsible for stabilizing the AI
Workflow Framework.

Before any further debugging or implementation, permanently disable all
parallel execution paths and force the framework into Sequential
Execution Mode.

This is a safety operation.

------------------------------------------------------------------------

## Objectives

1.  Disable every form of parallel execution.
2.  Prevent background agents from starting concurrently.
3.  Ensure only one workflow task may execute at any time.
4.  Do **not** change feature logic; only change execution
    orchestration.

------------------------------------------------------------------------

## Requirements

### 1. Global Execution Mode

Introduce a global configuration:

execution_mode = "sequential"

Make this the default everywhere.

Parallel mode must never be enabled automatically.

------------------------------------------------------------------------

### 2. Disable Parallel Scheduler

Audit the orchestrator and remove or disable:

-   Promise.all
-   Task.WhenAll
-   async fan-out
-   worker pools
-   background agent spawning
-   parallel queues
-   multi-thread execution
-   parallel_groups
-   concurrent checkpoints

Replace with:

Queue
 ↓
Task #1
 ↓
Completed
 ↓
Task #2
 ↓
Completed

------------------------------------------------------------------------

### 3. Runtime Lock

Implement a global execution lock.

Requirements:

-   Only one active workflow.
-   Only one active skill.
-   Only one state writer.
-   Only one database writer.

If another task starts while locked:

-   enqueue it
-   or reject it with a clear message

Never execute simultaneously.

------------------------------------------------------------------------

### 4. State Protection

Ensure only one component can update:

-   .agents/state/*
-   project_runtime.db
-   global_runtime.db
-   pending-choice files
-   runtime metadata

All writes must be atomic.

------------------------------------------------------------------------

### 5. Queue Manager

Implement FIFO scheduling.

No task may bypass the queue.

The next task starts only after:

-   state committed
-   DB committed
-   verification completed
-   lock released

------------------------------------------------------------------------

### 6. Disable Background Agents

Background agents must not execute independently.

Every spawned agent must become a queued sequential task.

------------------------------------------------------------------------

### 7. Diagnostics

Add runtime diagnostics showing:

-   execution_mode
-   active_task
-   queue_length
-   lock_owner
-   waiting_tasks

Warn if more than one active task exists.

------------------------------------------------------------------------

### 8. Verification

Simulate:

-   multiple implementation requests
-   multiple quick-feature requests
-   multiple quick-fix requests
-   repeated approvals
-   resume workflow
-   initialize workspace

Verify:

-   only one task runs
-   no overlapping writes
-   no race conditions
-   no duplicated DB updates
-   no state corruption

------------------------------------------------------------------------

### 9. Deliverables

Produce:

-   Brainstorming
-   Plan
-   Blueprint
-   Implementation
-   Verification report

Include a migration note describing how parallel execution can be safely
reintroduced in the future using locks, transactions, and queues.

Do not stop until all execution paths are confirmed sequential and
stable.
```

## 3. Business Problem
- **Problem**: The AI Workflow Framework currently supports parallel execution paths, background agents, and concurrent checkpoint/state writers. Without synchronization, concurrent execution causes race conditions, corrupted state files under `.agents/state/*`, and duplicated/corrupted sqlite databases.
- **Why it matters**: Ensuring 100% data integrity and predictability of the workflow execution is critical. State corruption makes it impossible to recover from checkpoint failures.
- **Who is affected**: Developer (Ba) and all AI agents executing workflows inside the workspace.
- **Expected outcome**: Only a single workflow, single skill, and single writer run at any point. Parallel tasks are rejected or queued in a FIFO manner, and diagnostics warn if concurrency is detected.

## 4. Requirement Discovery
- **Functional Requirements**:
  - FR-01: Set default configuration `execution_mode = "sequential"`.
  - FR-02: Disable Promise.all, task fanning, worker pools, and concurrent background agent processes.
  - FR-03: Implement a global runtime lock that restricts execution to exactly one active skill/workflow.
  - FR-04: Implement atomic writes with locked file operations for `.agents/state/*` and database records.
  - FR-05: Maintain a queue for incoming execution requests when locked.
  - FR-06: Provide runtime diagnostics (active tasks, lock owner, queue details) and print warning if multiple tasks are found.
- **Non-functional Requirements**:
  - NFR-01: Auto-release lock after a timeout (e.g., 60 seconds) to prevent deadlock if an agent process terminates unexpectedly.
  - NFR-02: Fast failure response for blocked execution requests, passing exit code != 0 back to the agent.
- **Technical Constraints**:
  - TC-01: Must maintain complete compatibility with the split state architecture (`context.json`, `workflow.json`, etc.).
  - TC-02: Strictly read-only initialization unless confirmed by permission mode.

## 5. Clarification Questions & Answers
| Question | Answer |
|---|---|
| Q1: Should a blocked task be queued or immediately rejected? | Option A recommends immediately rejecting the task (fail-fast) with a clear explanation, which is simpler and prevents infinite loops in agent execution. |
| Q2: What is the timeout for the global execution lock? | A timeout of 60 seconds is recommended to automatically recover from stale locks (e.g., if the agent crashes). |

## 6. Requirement Readiness Score
- **Score**: 100/100
- **Status**: Ready

## 7. Existing Project Context
- **Memory Source**: [project-profile.json](file:///e:/AgentsProject/.agents/project-profile.json) and [AI_RULES.md](file:///e:/AgentsProject/.agents/AI_RULES.md).
- **Existing Architecture Summary**: The project currently uses `save_session_atomic` to serialize states and write them as split files under `.agents/state/`. A lock file `.agents/.session.json.lock` is used for synchronizing writes.

## 8. Existing Modules & Services
| Module/Service | Location | Relevance |
|---|---|---|
| workflow_runtime.py | [.agents/skills/workflow-runtime/scripts/workflow_runtime.py](file:///e:/AgentsProject/.agents/skills/workflow-runtime/scripts/workflow_runtime.py) | Main orchestration command handler |
| session.py | [.agents/skills/workflow-runtime/scripts/session.py](file:///e:/AgentsProject/.agents/skills/workflow-runtime/scripts/session.py) | Active lock creation and session writing |

## 9. Solution Options Evaluated

### Option A: Hardcoded Sequential + File-based Exclusive Lock (Recommended)
- **Overview**: Force the framework to run sequentially by setting `execution_mode = "sequential"` as the default configuration and adapting `SessionLock` to guard the startup of skills.
- **Architecture**:
  - If a skill starts, a file-lock `.agents/runtime.lock` is created. If the lock exists, any subsequent start command fails.
  - Vole-out any async spawning or parallel queue tasks in the runtime scripts.
- **Advantages**: Easy to implement, low code churn, high reliability.
- **Disadvantages**: Lack of advanced SQL-based queue queuing.
- **Complexity**: Low
- **Risk**: Low
- **Performance**: High (low overhead)
- **Maintainability**: High
- **Compatibility**: High
- **Future Scalability**: Low (exclusively sequential)

### Option B: SQLite-based Queue Manager
- **Overview**: Implement a queue table inside the SQLite runtime DB where tasks are scheduled.
- **Architecture**: SQLite transaction-based queue table `execution_queue`.
- **Advantages**: Supports complex scheduling.
- **Disadvantages**: High risk of SQLite locking issues, complex code.
- **Complexity**: High
- **Risk**: Medium

## 10. Solution Comparison Table
| Criteria | Option A (Lock File) | Option B (SQLite Queue) |
|---|---|---|
| Complexity | Low | High |
| Risk | Low | Medium |
| Performance | High | Medium |
| Maintainability | High | Medium |
| Compatibility | High | High |
| Future Scalability | Low | High |
| Development Cost | Low | High |

## 11. Selected Solution
- **Choice**: Option A — File-based Exclusive Lock
- **Why Selected**: Simpler, extremely robust for emergency lockdown, fail-fast prevents agent process leaks.
- **Trade-offs Accepted**: Blocked tasks fail immediately rather than waiting in queue indefinitely.
- **Technical Debt**: Future parallel execution would require rebuilding the scheduler.
- **Risk Mitigation**: A 60-second lock file expiration checks if the lock is stale.

## 12. Risks & Assumptions
- **Risks**:
  - R-01: Stale lock file left behind on crash. → Mitigation: Validate lock file age; if older than 60 seconds, auto-expire it.
- **Assumptions**:
  - A-01: All agent scripts use the central `workflow_runtime.py` to start and step tasks.

## 13. Acceptance Criteria
- [ ] Mặc định `execution_mode` trong cấu hình và các tệp trạng thái là `"sequential"`.
- [ ] Không có tệp tin hay command nào chạy song song.
- [ ] Mọi tác vụ `start` mới khi hệ thống đang bị khóa sẽ trả về lỗi ngay lập tức.
- [ ] `workflow_runtime.py` chẩn đoán hiển thị chế độ tuần tự và cảnh báo nếu phát hiện nhiều luồng.

## 14. Final Planning Prompt

### Purpose
Hoàn tất các bước chuẩn bị thiết kế để chuyển giao cho skill `brainstorming-to-plan`.

### Problem Statement
Loại bỏ hoàn toàn khả năng chạy song song và bất đồng bộ đồng thời của hệ thống để ngăn ngừa xung đột dữ liệu trạng thái.

### Objectives & Selected Solution
Thiết lập chế độ Sequential toàn cục và khóa tệp độc quyền (`.agents/runtime.lock`) khi bắt đầu thực thi skill.

### Verification Checklist
- [ ] docs/plans/FEAT-043_disable_parallel_execution_plan.md generated and approved
- [ ] docs/designs/FEAT-043_disable_parallel_execution_blueprint.md generated and approved
