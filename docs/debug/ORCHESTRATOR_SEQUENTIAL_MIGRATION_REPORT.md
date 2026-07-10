# Orchestrator Sequential Migration Report

## 1. Root Cause of Parallel Execution Issues
The previous inclusion of parallel execution modes introduced significant risks to the stability of the workflow:
- **Race Conditions**: Parallel background workers spawned concurrently often updated the shared session file (`.agents/.session.json`) simultaneously, causing write collisions and lost updates.
- **SQLite Write Conflicts**: Concurrent SQL statements to `project_runtime.db` led to SQLite locking issues (`database is locked`), causing command failures.
- **Workflow Phase Drift**: Different parallel tasks updated checkpoints out-of-order, leading to state inconsistencies where the workspace was modified before blueprints were validated.
- **Telemetry Discrepancies**: Overlapping updates to provider requests and timeline logs corrupted character estimates and cost statistics.

## 2. Files Changed
- `skills/orchestrator/SKILL.md` (and `.agents/skills/orchestrator/SKILL.md` copy):
  - Removed `parallel` aliases and tags.
  - Rewrote execution flow description to reflect pure sequential dispatcher.
  - Removed prompt selection options for parallel mode execution.
- `skills/workflow-runtime/scripts/workflow_runtime.py` (and `.agents` copy):
  - Upgraded lock file target from `orchestrator.lock` to `workflow.lock` with strict exit policies.
  - Forced recommendation modes in `do_execution` to always resolve to `sequential`.
  - Disallowed `--mode parallel` flag validation, printing error outputs.
  - Simplified the `summary` subcommand to report sequential-only operations.
- `skills/workflow-runtime/tests/test_lock.py`:
  - Adjusted unit tests to expect `workflow.lock` and verify sequential collision error messages.
  - Removed stale override tests as stale locks are no longer bypassed automatically.
- `skills/workflow-runtime/tests/test_runtime.py`:
  - Refactored `test_execution_mode_switching_and_approval` and `test_parallel_scope_constraints` to verify that attempting parallel modes triggers exit failures.

## 3. Removed Parallel Features
- **Parallel Recommendations**: The CLI `execution recommend` subaction now forces the recommended mode to `sequential`.
- **Parallel Mode Switch**: The CLI `execution mode --mode parallel` now exits immediately with failure code 1.
- **Stale Lock Bypass**: The startup check no longer checks lock age or heartbeats to bypass lock presence; it blocks immediately if `workflow.lock` exists.
- **Multi-Worker Execution Options**: Removed choice prompts from orchestrator definitions.

## 4. Lock Implementation Detail
- **Global Lock**: A lock file is written to `.agents/runtime/workflow.lock` whenever a workflow starts via `do_start`.
- **Collision Policy**: Any subsequent startup command (e.g. `start`) instantly terminates if `workflow.lock` is present:
  ```text
  Another workflow is already running.
  Do not continue.
  ```
- **Release Hooks**: The lock is deleted automatically during the execution of cleanup hooks inside `do_complete` and `do_fail`.

## 5. Test Results
- Automated unit test suite updated and run successfully.
- Verified that trying to run concurrent tasks is blocked.

## 6. Remaining Risks
- **Manual Lock Release**: If an agent process is killed forcefully (e.g., Sigkill or system crash) before writing failures, the lock file `.agents/runtime/workflow.lock` will persist and must be manually deleted by the user.
