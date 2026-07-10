<!-- File path: docs/plans/FEAT-043_disable_parallel_execution_plan.md -->

---
feature_id: FEAT-043
feature_name: Disable Parallel Execution and Emergency Lockdown
status: reviewed
stage: planning
created_at: 2026-07-09
updated_at: 2026-07-09
previous_artifact: ../brainstorming/FEAT-043_disable_parallel_execution.md
next_artifact: ../designs/FEAT-043_disable_parallel_execution_blueprint.md
---

# FEAT-043: Disable Parallel Execution and Emergency Lockdown

## Objective
- **Business Objective**: Stabilize the AI Workflow Framework by disabling all parallel and background execution paths, forcing a strictly sequential processing pipeline to eliminate race conditions, double state writes, and SQLite database corruption.
- **Expected Outcome**: Enforce sequential execution across the framework, reject concurrent execution requests gracefully, implement atomic lock protection for state file updates, and expose diagnostics details.

## Scope

### Included
- Introduce a global sequential configuration setting (`execution_mode = "sequential"`) as the hard default.
- Audit the orchestrator/runtime scripts to disable all fanning out, background queues, and concurrent checkpoints.
- Implement an exclusive lock file (`.agents/runtime.lock`) that restricts system execution to one workflow/skill/writer at a time.
- Implement a lock timeout mechanism (e.g., 60 seconds) to prevent permanent deadlocks if the runtime process crashes.
- Fail-fast execution rejection with clean exit codes and error logs when a lock conflict occurs.
- Add CLI diagnostics showing `execution_mode`, active tasks, and lock status.

### Excluded
- Modifying core agent prompt templates or prompt content logic.
- Adding complex SQL queueing or distributed lock brokers.

## Project Impact
- **Impacted Areas**:
  - **Orchestration**: `workflow_runtime.py` start/step execution steps.
  - **State Management**: `session.py` and `state_sync.py` file writer transactions.
  - **Configuration**: Default execution settings in `.agents/workflow.config.json`.
  - **Diagnostics**: `workflow_runtime.py` CLI interface and diagnostics summaries.

## Dependencies
- Pre-requisite: Splitted state system is healthy and workspace is properly initialized at Checkpoint 1.

## Risks
- **Risk**: Interrupted/crashed processes might leave a stale lock file, blocking future executions.
  - **Mitigation**: Lock validator will check modification time of `.agents/runtime.lock` and automatically override it if it is older than 60 seconds.

## Acceptance Criteria
- [ ] Configuration and states default `execution_mode` to `"sequential"`.
- [ ] Concurrent skill executions are rejected immediately with clean exit codes and error diagnostics.
- [ ] Concurrent state writes are prevented using exclusive file-based lock.
- [ ] CLI diagnostics successfully expose lock details and warn if concurrent tasks are attempted.

## Deliverables
- Scoping & Planning: `docs/plans/FEAT-043_disable_parallel_execution_plan.md`
- Design Specification: `docs/designs/FEAT-043_disable_parallel_execution_blueprint.md`
- Lock implementation and sequential mode validation logic.
- Automated tests and verification report.

## Estimated Complexity
- **Low**: Adapting existing `SessionLock` wrapper and configuration defaults is straightforward and does not require complex infrastructure or third-party packages.

## Recommended Blueprint Focus
- Focus on implementing exclusive locks in `workflow_runtime.py` commands (`do_start`, `do_step`, etc.) and session state save transactions. Ensure the lock check logic is safe against stale locks.

## Recommended Next Skill
/blueprint
