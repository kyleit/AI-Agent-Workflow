<!-- File path: docs/designs/QUICK-017_force_sequential_orchestrator_blueprint.md -->
---
artifact_type: blueprint
feature_id: QUICK-017
workflow: quick-feature
status: approved
---

# Technical Design Blueprint – Force Sequential Orchestrator

## 1. Proposed Code Changes

### `.agents/skills/workflow-runtime/scripts/workflow_runtime.py`
- **Operation**: MODIFY
- **Responsibility**: Implement orchestrator lock check, lock heartbeat refresh, and lock release. Update diagnostics output.
- **Changes**:
  - Update `do_start` to check for exclusive `.agents/runtime/orchestrator.lock` file. If locked and locked for < 60 seconds, reject execution with error code `1` and exit with message: `"Sequential mode active. Another workflow task is already running. Resume or wait for it to finish."`
  - Write lock metadata containing `lock_owner`, `work_item_id`, `skill`, `pid`, `started_at`, and `heartbeat_at`.
  - Update `do_step` to update the `heartbeat_at` timestamp in the lock file.
  - Update `do_complete` and `do_fail` to release (delete) `.agents/runtime/orchestrator.lock`.
  - Update `do_state_action` (diagnose) to inspect `.agents/runtime/orchestrator.lock` and output correct diagnostics properties.

### `.agents/skills/workflow-runtime/scripts/state_sync.py`
- **Operation**: MODIFY
- **Responsibility**: Normalize legacy `parallel` settings to `sequential` and clear `parallel_groups`.
- **Changes**:
  - In `aggregate_state`, check if `execution_mode` or `recommended_mode` are `"parallel"`. If so, force them to `"sequential"`.
  - Clear `parallel_groups` list to empty `[]`.

## 2. Target Folder Structure
```text
.
├── .agents
│   ├── skills
│   │   └── workflow-runtime
│   │       └── scripts
│   │           ├── workflow_runtime.py
│   │           ├── state_sync.py
│   │           ├── session.py
│   │           └── validator.py
│   └── workflow.config.json
└── docs
    ├── quick
    │   └── QUICK-017_force_sequential_orchestrator.md
    └── designs
        └── QUICK-017_force_sequential_orchestrator_blueprint.md
```

## 3. Interface & Data Contracts
- **API/CLI Contracts**:
  - Lock File Schema (`.agents/runtime/orchestrator.lock`):
    ```json
    {
      "lock_owner": "orchestrator|skill-name",
      "work_item_id": "QUICK-017",
      "skill": "quick-feature",
      "pid": 12345,
      "started_at": "2026-07-09T07:24:00+07:00",
      "heartbeat_at": "2026-07-09T07:24:05+07:00"
    }
    ```
  - State Diagnose CLI JSON response format:
    ```json
    {
      "execution_mode": "sequential",
      "active_task": "quick-feature (feature)",
      "queue_length": 0,
      "lock_owner": "quick-feature",
      "locked_at": "2026-07-09T07:24:00+07:00",
      "waiting_tasks": []
    }
    ```

## 4. Algorithms & Key Logic
- **Exclusive Lock Validation**:
  - Read `.agents/runtime/orchestrator.lock`.
  - Compare current timezone-aware time with the lock's `heartbeat_at` time.
  - If difference < 60 seconds, lock is active -> reject start command.
  - Else, log stale override and recreate the lock.

## 5. Validation Rules
- `running_agents` list must contain at most one active task ID.
- Reject concurrent starts on `do_start` if lock is valid.

## 6. Implementation Checklist
- [ ] Update `aggregate_state` in `state_sync.py` to normalize legacy `parallel` execution modes and clear `parallel_groups`.
- [ ] Update lock logic in `do_start` of `workflow_runtime.py` to use `.agents/runtime/orchestrator.lock` with requested schema fields.
- [ ] Update lock update logic in `do_step` to update `heartbeat_at`.
- [ ] Update lock release in `do_complete`/`do_fail` to delete `.agents/runtime/orchestrator.lock`.
- [ ] Update diagnostics in `do_state_action` for the `diagnose` subcommand.
- [ ] Run tests to verify logic.

## 7. Verification & Test Plan
- **Acceptance Assertions**:
  - *REQ-001*: Verify `.agents/runtime/orchestrator.lock` is created on skill start with all required fields.
  - *REQ-002*: Verify concurrent start is rejected with exit code 1 and error message: `"Sequential mode active. Another workflow task is already running. Resume or wait for it to finish."`
  - *REQ-003*: Verify stale lock is overridden after 60 seconds.
  - *REQ-004*: Verify step updates `heartbeat_at`.
  - *REQ-005*: Verify complete/fail releases lock.
  - *REQ-006*: Verify legacy states containing `"parallel"` are normalized on loading to `"sequential"`.
