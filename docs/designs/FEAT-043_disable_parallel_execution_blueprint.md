<!-- File path: docs/designs/FEAT-043_disable_parallel_execution_blueprint.md -->

---
feature_id: FEAT-043
feature_name: Disable Parallel Execution and Emergency Lockdown
status: reviewed
stage: blueprint
created_at: 2026-07-09
updated_at: 2026-07-09
previous_artifact: ../plans/FEAT-043_disable_parallel_execution_plan.md
next_artifact: [Implementation (Source Code)](../../)
---

# Technical Blueprint & Implementation Contract – Disable Parallel Execution and Emergency Lockdown

## 0. Baseline Context & References
- **Memory Baseline**: System uses the split state manager under `.agents/state/` to record session metadata. Writes are guarded momentarily during updates by `SessionLock` on `.agents/.session.json.lock`.
- **RAG Query Summaries**: The CLI starts skills via `do_start()`, transitions with `do_step()`, and finishes with `do_complete()` or `do_fail()` in `workflow_runtime.py`.
- **Inspected Source Files**:
  - `.agents/skills/workflow-runtime/scripts/workflow_runtime.py` (do_start, do_step, do_complete, do_fail)
  - `.agents/skills/workflow-runtime/scripts/session.py` (load_session, save_session_atomic)
  - `.agents/workflow.config.json` (root settings)

## 1. File-by-File Analysis & Proposed Mutations

| File Path | Operation | Responsibility | Dependency | Impact & Risk |
| :--- | :--- | :--- | :--- | :--- |
| `.agents/workflow.config.json` | `MODIFY` | Add default execution mode configuration setting | None | Low: adds new field `"execution_mode": "sequential"` |
| `.agents/skills/workflow-runtime/scripts/workflow_runtime.py` | `MODIFY` | Implement lock check on start, lock refresh on step, lock release on complete/fail. Implement `state diagnose` command. | `session.py` | Low: blocks concurrent command start execution safely. |
| `skills/workflow-runtime/tests/test_lock.py` | `NEW` | Add tests to verify sequential execution, lock file creation, collision blocks, stale lock expiration, and lock release. | `workflow_runtime.py` | None: isolated unit test file |

## 2. Target Folder Structure
```text
.
├── .agents
│   ├── skills
│   │   └── workflow-runtime
│   │       └── scripts
│   │           ├── workflow_runtime.py
│   │           ├── session.py
│   │           ├── context.py
│   │           └── validator.py
│   └── workflow.config.json
├── docs
│   ├── brainstorming
│   │   └── FEAT-043_disable_parallel_execution.md
│   ├── plans
│   │   └── FEAT-043_disable_parallel_execution_plan.md
│   └── designs
│       └── FEAT-043_disable_parallel_execution_blueprint.md
└── skills
    └── workflow-runtime
        └── tests
            ├── test_lock.py
            └── test_runtime.py
```

## 3. Interface Contracts (Public & Internal)
- **Public Interface Contracts**:
  - *CLI Command Syntax*:
    - `python .agents/skills/workflow-runtime/scripts/workflow_runtime.py start --skill <skill> --command <cmd> [--checkpoint <chk>] --step <step>`: Acquires the exclusive lock `.agents/runtime.lock`. Fails with code `1` if a valid lock is active.
    - `python .agents/skills/workflow-runtime/scripts/workflow_runtime.py step --step <step>`: Refreshes the lock expiration timestamp.
    - `python .agents/skills/workflow-runtime/scripts/workflow_runtime.py complete [--checkpoint <chk>] [--step <step>]`: Releases the lock.
    - `python .agents/skills/workflow-runtime/scripts/workflow_runtime.py fail --step <step> [--log <log>]`: Releases the lock.
    - `python .agents/skills/workflow-runtime/scripts/workflow_runtime.py state diagnose`: Exposes current diagnostics info as JSON:
      ```json
      {
        "execution_mode": "sequential",
        "active_task": "brainstorming (brainstorm)",
        "queue_length": 0,
        "lock_owner": "brainstorming",
        "locked_at": "2026-07-09T07:20:00+07:00",
        "waiting_tasks": []
      }
      ```
  - *Enum Constraint*: For `permission_mode`, only allow `sandbox` and `full_access`. If `unrestricted` is requested, automatically fallback to `sandbox`.

## 4. Algorithms & Logic Specifications

### Lock Acquisition Algorithm (do_start)
```python
lock_file = ".agents/runtime.lock"
if exists(lock_file):
    lock_data = read_json(lock_file)
    locked_at = parse_iso8601(lock_data["locked_at"])
    now = current_time_timezone_aware()
    if (now - locked_at).total_seconds() < 60:
        print_to_stderr("Error: Framework is locked by active skill '<skill>'")
        exit_code(1)
    else:
        print_to_stderr("Warning: Stale lock detected, overriding lock file.")

write_json(lock_file, {
    "active_skill": current_skill,
    "active_command": current_command,
    "locked_at": current_time_iso8601()
})
```

### Lock Refresh Algorithm (do_step)
```python
lock_file = ".agents/runtime.lock"
if exists(lock_file):
    lock_data = read_json(lock_file)
    lock_data["locked_at"] = current_time_iso8601()
    write_json(lock_file, lock_data)
```

### Lock Release Algorithm (do_complete / do_fail)
```python
lock_file = ".agents/runtime.lock"
if exists(lock_file):
    remove(lock_file)
```

## 5. State Machine & Transitions
- **States**:
  - `IDLE` (no lock file)
  - `LOCKED` (active valid `.agents/runtime.lock`)
- **Transitions**:
  - `IDLE` --(start)--> `LOCKED`
  - `LOCKED` --(step)--> `LOCKED` (expires timestamp refreshed)
  - `LOCKED` --(complete/fail)--> `IDLE`
  - `LOCKED` --(timeout > 60s + start)--> `LOCKED` (stale lock overridden)

## 6. Validation and Safety Constraints
- **Input Validation**: Check that `permission_mode` value from inputs matches only `sandbox` or `full_access`.
- **Lock Check**: Ensure that any state mutation checking uses timezone-aware comparisons.

## 7. Backward Compatibility & Migration Mapping
| Old Field | New File | New Field | Migration Rule | Recovery Rule |
| :--- | :--- | :--- | :--- | :--- |
| `permission_mode: "unrestricted"` | `.agents/state/context.json` | `permission_mode` | Change value to `"sandbox"` | Re-run initialization to prompt user again |
| (None) | `.agents/state/context.json` | `execution_mode` | Default new field to `"sequential"` | Fallback to `"sequential"` |

## 8. Implementation Checklist
- [ ] Add `"execution_mode": "sequential"` into `.agents/workflow.config.json`.
- [ ] Modify `do_start` in `.agents/skills/workflow-runtime/scripts/workflow_runtime.py` to check for active lock.
- [ ] Modify `do_step` in `.agents/skills/workflow-runtime/scripts/workflow_runtime.py` to refresh lock timestamp.
- [ ] Modify `do_complete` and `do_fail` in `.agents/skills/workflow-runtime/scripts/workflow_runtime.py` to delete lock.
- [ ] Update permission configuration choice in `do_init` to filter out `unrestricted`.
- [ ] Implement `state diagnose` CLI subcommand.
- [ ] Create test file `skills/workflow-runtime/tests/test_lock.py` to verify lock behavior.
- [ ] Run test suite to verify implementation.

## 9. Acceptance Criteria & Test Mapping

| Requirement ID | Requirement Description | Expected Result | Verification Method | Unit/Integration Test Target |
| :--- | :--- | :--- | :--- | :--- |
| `REQ-001` | Sequential default config | `execution_mode` defaults to `"sequential"` in configuration | View configuration file | `test_lock.py:test_config_sequential` |
| `REQ-002` | Lock file creation on start | Lock file is written with skill, command, and timestamp when skill starts | Inspect `.agents/runtime.lock` | `test_lock.py:test_lock_created_on_start` |
| `REQ-003` | Lock collision blocking | Start command fails with exit code 1 if valid lock exists | Run second start command | `test_lock.py:test_lock_collision_blocks` |
| `REQ-004` | Stale lock override | Stale lock (> 60s old) is overwritten and starts successfully | Set lock time to 70s ago and start | `test_lock.py:test_stale_lock_override` |
| `REQ-005` | Lock refresh on step | Step command updates locked_at timestamp | Run step command | `test_lock.py:test_lock_refreshed_on_step` |
| `REQ-006` | Lock release on complete/fail | Complete or fail command deletes lock file | Run complete/fail command | `test_lock.py:test_lock_released` |
| `REQ-007` | Unrestricted permission removed | System falls back to sandbox mode if unrestricted is requested | Run init with unrestricted mode | `test_lock.py:test_unrestricted_blocked` |

## 10. Disallowed Outputs Validation
- [x] No `file://` or absolute paths used.
- [x] No placeholders like `...` or `etc.` in code/structures.
- [x] No `TBD` or `To Be Determined` placeholders.
- [x] No unsafe permission values (e.g. `unrestricted`).
- [x] No unmapped legacy fields without migration rules.
