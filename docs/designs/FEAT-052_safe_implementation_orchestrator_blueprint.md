<!-- File path: docs/designs/FEAT-052_safe_implementation_orchestrator_blueprint.md -->

---
feature_id: FEAT-052
feature_name: Safe Implementation Orchestrator (DAG, Locks, Workers, Patches)
status: reviewed
stage: blueprint
created_at: 2026-07-10
updated_at: 2026-07-10
previous_artifact: ../plans/FEAT-052_safe_implementation_orchestrator_plan.md
next_artifact: ../../skills/workflow-runtime/scripts/
---

# Technical Design Blueprint & Implementation Contract – Safe Implementation Orchestrator (DAG, Locks, Workers, Patches)

## 0. Baseline Context & References

- **Memory Baseline**: High confidence. Existing `event_bus.py` provides pub/sub foundation. `process_wrapper.py` wraps subprocess execution. `workflow_runtime.py` uses `subprocess` for worker spawning.
- **Inspected Source Files**:
  - `skills/workflow-runtime/scripts/event_bus.py` — Existing event bus; can be leveraged for worker events.
  - `.agents/runtime/handoffs.json` — Process handoff schema reference.

---

## 1. File-by-File Analysis & Proposed Mutations

| File Path | Operation | Responsibility | Dependency | Impact & Risk |
| :--- | :--- | :--- | :--- | :--- |
| `skills/workflow-runtime/scripts/dag_planner.py` | NEW | Parse blueprint JSON → DAG, topological sort, cycle detection | None | Low – pure algorithm |
| `skills/workflow-runtime/scripts/lock_manager.py` | NEW | Manage `file-locks.json`; acquire/release/stale detection | `atomic_writer.py` (FEAT-050) | Medium – shared state |
| `skills/workflow-runtime/scripts/worker_manager.py` | NEW | Manage `workers.json`; PID tracking, orphan detection | `atomic_writer.py` (FEAT-050) | Medium – OS interaction |
| `skills/workflow-runtime/scripts/orchestrator.py` | NEW | DAG execution controller; locks + workers + orphan check | `dag_planner.py`, `lock_manager.py`, `worker_manager.py` | High – coordinates all |
| `skills/workflow-runtime/scripts/patch_applier.py` | NEW | Validate + apply `.patch` files to workspace | `lock_manager.py` | High – modifies workspace |
| `.agents/runtime/file-locks.json` | NEW (schema) | Active file locks registry | None | Low |
| `.agents/runtime/workers.json` | NEW (schema) | Worker PID registry | None | Low |
| `.agents/runtime/patches/` | NEW (dir) | Storage for task patch files | None | Low |
| `skills/blueprint-to-implementation/SKILL.md` | MODIFY | Add Safe Execution Policy section | None | Low – docs |
| `skills/workflow-runtime/scripts/workflow_runtime.py` | MODIFY | Add `implement abort`, `implement resume`, completion gate | All new modules | High |

---

## 2. Target Folder Structure

```text
skills/workflow-runtime/
├── scripts/
│   ├── dag_planner.py         [NEW] – DAG builder & topological sorter
│   ├── lock_manager.py        [NEW] – File lock registry manager
│   ├── worker_manager.py      [NEW] – Worker PID tracker
│   ├── orchestrator.py        [NEW] – Execution controller
│   └── patch_applier.py       [NEW] – Patch validator & applier

.agents/runtime/
├── file-locks.json            [NEW SCHEMA]
├── workers.json               [NEW SCHEMA]
└── patches/
    ├── Task_1_1.patch         [RUNTIME-GENERATED]
    └── Task_1_2.patch         [RUNTIME-GENERATED]
```

---

## 3. Complete Class & Module Design

### `dag_planner.py` — DAGPlanner

- **Responsibilities**: Parse blueprint JSON tasks+dependencies into a DAG, validate, sort topologically, assign execution groups.
- **Public Methods**:
  - `build(blueprint: dict) -> dict` — Parse tasks, dependencies. Returns `{nodes, edges, groups}`.
  - `topological_sort(graph: dict) -> list[str]` — Kahn's algorithm. Raise `CyclicDependencyError` if cycle found.
  - `get_execution_groups(graph: dict) -> list[list[str]]` — Return ordered groups of tasks that can potentially run together.
  - `validate(blueprint: dict) -> list[str]` — Return list of validation errors (missing task refs, invalid paths, absolute paths in write_set, etc.).
  - `check_parallel_safety(tasks: list[str], blueprint: dict) -> bool` — True only if write_sets don't overlap AND no global file touched.

- **Global File Blocklist** (always sequential):
  ```python
  GLOBAL_FILES = [
    "package.json", "package-lock.json", "pnpm-lock.yaml", "yarn.lock",
    "go.mod", "go.sum", "pyproject.toml", "requirements.txt",
    ".agents/.session.json", ".agents/runtime/workers.json",
    ".agents/runtime/file-locks.json"
  ]
  ```

### `lock_manager.py` — LockManager

- **Responsibilities**: All-or-nothing file lock acquisition; stale lock detection via PID liveness check; path security validation.
- **Public Methods**:
  - `acquire(task_id: str, write_set: list[str], pid: int, expires_seconds: int = 300) -> bool` — Acquire all locks atomically. Returns False if any file locked. Writes to `file-locks.json`.
  - `release(task_id: str) -> None` — Remove all locks owned by `task_id`.
  - `is_stale(lock_entry: dict) -> bool` — True if owning PID is dead (`os.kill(pid, 0)` raises `OSError`).
  - `clear_stale_locks() -> list[str]` — Find and remove stale locks; return list of cleared files.
  - `get_active_locks() -> list[dict]` — Return all non-stale active locks.
  - `has_conflict(write_set: list[str]) -> bool` — True if any file in write_set is currently locked.
- **Security**: Reject any path starting with `/`, containing `..`, or not within workspace. Raise `SecurityError`.
- **Atomicity**: All lock acquisitions use read-modify-write with `AtomicWriter`. If any file in set is locked, NONE are acquired.

### `worker_manager.py` — WorkerManager

- **Responsibilities**: Register/deregister worker PIDs; detect orphaned processes; maintain per-worker logs.
- **Public Methods**:
  - `register(task_id: str, pid: int, command: str) -> str` — Creates worker entry in `workers.json`. Returns `worker_id` (UUID).
  - `mark_completed(worker_id: str) -> None` — Set status to `completed`, set `ended_at`.
  - `mark_failed(worker_id: str, error: str) -> None` — Set status to `failed`.
  - `detect_orphans() -> list[str]` — Return worker_ids where status is `running` but PID is dead.
  - `terminate_orphan(worker_id: str, force: bool = False) -> bool` — Kill orphaned process (SIGTERM then SIGKILL after 5s).
  - `get_active_workers() -> list[dict]` — Return all workers with status `running` or `starting`.
  - `has_active_workers() -> bool` — True if any worker is `running` or `starting`.

### `orchestrator.py` — SafeOrchestrator

- **Responsibilities**: Execute task groups according to DAG; coordinate locks, workers, completion gate; support abort and resume.
- **Public Methods**:
  - `run_phase(phase_id: str, blueprint: dict, mode: str = "safe_sequential") -> dict` — Execute all tasks in phase. Returns `{status, tasks_completed, tasks_failed}`.
  - `run_task(task: dict, blueprint: dict) -> dict` — Execute single task: acquire locks → spawn/run → verify outputs → release locks.
  - `check_completion_gate() -> tuple[bool, list[str]]` — Returns `(passed, failing_reasons)`. Checks all 9 conditions.
  - `abort(ask_before_kill: bool = True) -> None` — Detect active workers, optionally ask user, terminate, release locks.
  - `resume() -> str | None` — Find first queued task with all dependencies completed; return task_id.
- **Completion Gate Conditions** (all must pass):
  1. All tasks `completed` in ledger.
  2. No task `running`, `queued`, `blocked`, or `failed`.
  3. `workers.json` has no active workers.
  4. `file-locks.json` has no active locks.
  5. Expected output files exist.
  6. Modified files within blueprint write_sets.
  7. Build/test/lint checks passed (or `Not Configured`).
  8. Workspace diff summary generated.
  9. `.session.json`/`dashboard.json` updated atomically.

### `patch_applier.py` — PatchApplier

- **Responsibilities**: Validate and apply task patch files to workspace sequentially.
- **Public Methods**:
  - `apply(task_id: str, patch_path: str, write_set: list[str]) -> dict` — Validate patch only touches declared write_set; apply with `git apply --check` first; apply if clean. Returns `{success, files_changed, conflicts}`.
  - `validate_patch_scope(patch_path: str, write_set: list[str]) -> list[str]` — Return list of files in patch NOT in write_set (violations).
  - `rollback_patch(patch_path: str) -> bool` — Reverse-apply patch via `git apply -R`.

---

## 4. Detailed Interface Contracts

### `acquire(task_id, write_set, pid, expires_seconds=300) -> bool`
- **Parameters**: `write_set` must be relative paths. Empty list is valid (no files locked).
- **Return**: `True` if all locks acquired; `False` if any conflict.
- **Atomicity**: Uses file-level mutex (`threading.Lock`) + `AtomicWriter` for `file-locks.json`.
- **Exceptions**: `SecurityError` if absolute path in write_set.

### `run_task(task: dict, blueprint: dict) -> dict`
- **Return**: `{status: "completed"|"failed", files_created: [], files_modified: [], error: str | None, elapsed_seconds: float}`.
- **Sequence**: Validate write_set → acquire locks → execute → verify outputs → release locks → update ledger.
- **Failure behavior**: On any error: release locks, mark task `failed`, stop downstream tasks, recommend `/debug`.

### `check_completion_gate() -> tuple[bool, list[str]]`
- **Return**: `(True, [])` if all 9 conditions pass; `(False, ["reason1", "reason2", ...])` with all failing reasons.

---

## 5. Configuration Schema

```json
{
  "orchestrator": {
    "default_mode": "safe_sequential",
    "allow_controlled_parallel": false,
    "lock_expiry_seconds": 300,
    "orphan_check_on_complete": true,
    "patch_mode": false
  }
}
```

---

## 6. Database & Storage Design

- **`file-locks.json`**:
  ```json
  {
    "version": "1.0.0",
    "locks": {
      "relative/path/to/file.py": {
        "task_id": "Task 1.1",
        "worker_id": "uuid",
        "pid": 12345,
        "locked_at": "ISO8601",
        "expires_at": "ISO8601",
        "status": "active"
      }
    }
  }
  ```
- **`workers.json`**:
  ```json
  {
    "version": "1.0.0",
    "workers": {
      "worker-uuid": {
        "task_id": "Task 1.1",
        "pid": 12345,
        "status": "running",
        "started_at": "ISO8601",
        "ended_at": null,
        "command": "...",
        "log_file": ".agents/runtime/logs/worker-uuid.log"
      }
    }
  }
  ```

---

## 7. Cache Architecture

- No cache. Lock/worker state must be read fresh from disk on every operation to prevent race conditions.

---

## 8. Error Model

| Exception | Trigger | Recovery Strategy | Log Level |
| :--- | :--- | :--- | :--- |
| `CyclicDependencyError(ValueError)` | Cycle detected in task DAG | Stop implementation; print cycle path | CRITICAL |
| `FileLockConflict(RuntimeError)` | Lock acquisition fails | Return False; task queued to retry | WARNING |
| `OrphanWorkerError(RuntimeError)` | Worker alive after task claimed complete | Block phase completion; prompt abort | ERROR |
| `PatchConflictError(RuntimeError)` | Patch touches files outside write_set | Stop task; do not apply patch | ERROR |
| `CompletionGateError(RuntimeError)` | Completion gate fails | Block checkpoint advance; print failing reasons | ERROR |

---

## 9. Skill Integration Contracts

### `blueprint-to-implementation/SKILL.md`
- **Safe Execution Policy** (MUST add):
  ```
  - Parallel definitions in blueprints are CANDIDATES ONLY.
  - Default mode: safe_sequential.
  - Controlled parallel requires: runtime managed ledger + file locks + worker tracking + final no-orphan check.
  - AI agents MUST NOT spawn unmanaged background workers.
  - AI agents MUST NOT claim completion while any worker is still running.
  - AI agents MUST NOT modify files outside task write_set.
  ```

---

## 10. CLI & Runtime Contracts

| Command | Parameters | Output | Exit Code |
| :--- | :--- | :--- | :--- |
| `implement abort` | `--force` (optional skip confirm) | JSON `{workers_killed, locks_released}` | 0 |
| `implement resume` | none | JSON `{task_id, phase_id, ready_to_run}` | 0 resumed, 1 nothing |
| `implement status` | none | JSON `{tasks[], locks[], workers[], gate_status}` | 0 |

---

## 11. Sequence Flows

### Safe Sequential Task Execution
1. `orchestrator.run_task(task, blueprint)` called.
2. `dag_planner.validate()` confirms write_set paths are relative and within workspace.
3. `lock_manager.acquire(task_id, write_set, current_pid)` → all-or-nothing.
4. If any lock held: task queued, retry after dependent task completes.
5. Task executed (direct code edit or via subprocess with PID registered in `worker_manager`).
6. `patch_applier.apply()` if patch mode enabled.
7. Verify expected output files exist.
8. `lock_manager.release(task_id)`.
9. `worker_manager.mark_completed(worker_id)`.
10. `ledger.mark_task_completed(task_id)`.
11. Continue to next task.

### Orphan Detection on Phase Complete
1. `orchestrator.check_completion_gate()` called.
2. `worker_manager.detect_orphans()` checks all `running` workers.
3. If orphan found → `(False, ["Orphan worker {worker_id} (PID {pid}) still running"])`.
4. Phase NOT marked complete.
5. User prompted: `implement abort --force` to clean up.

---

## 12. Security & Safety

- **Write Set Enforcement**: Tasks can ONLY modify files declared in their `write_set`. `PatchApplier.validate_patch_scope()` enforces this.
- **No Global File Parallel Writes**: `DAGPlanner.check_parallel_safety()` blocks parallel execution if any task touches global files.
- **PID Validation**: `os.kill(pid, 0)` used to check process liveness. Returns `True` if alive (no signal sent).
- **Lock Expiry**: Locks auto-expire after `lock_expiry_seconds`. `clear_stale_locks()` called at each task start.

---

## 13. Complete Test Matrix

| Req ID | Test Type | Test File | Component | Assertion |
| :--- | :--- | :--- | :--- | :--- |
| FR-01 | Unit | `test_dag_planner.py` | `DAGPlanner` | Cycle detected raises `CyclicDependencyError` |
| FR-01 | Unit | `test_dag_planner.py` | `DAGPlanner` | Topological sort produces correct order |
| FR-02 | Unit | `test_file_locks.py` | `LockManager` | Acquire all-or-nothing: partial locks not left on failure |
| FR-02 | Unit | `test_file_locks.py` | `LockManager` | Absolute path raises `SecurityError` |
| FR-03 | Unit | `test_worker_registry.py` | `WorkerManager` | register() creates entry; detect_orphans() returns dead PIDs |
| FR-04 | Integration | `test_task_dag_execution.py` | `SafeOrchestrator` | Phase fails if orphan worker alive |
| FR-05 | Unit | `test_patch_applier.py` | `PatchApplier` | Patch touching undeclared file returns violation list |

---

## 14. Requirement Traceability Matrix

- `FR-01` → Task 1.1 → `DAGPlanner.build()` → `dag_planner.py` → `test_dag_planner.py`
- `FR-02` → Task 1.2 → `LockManager.acquire()` → `lock_manager.py` → `test_file_locks.py`
- `FR-03` → Task 1.3 → `WorkerManager.register()` → `worker_manager.py` → `test_worker_registry.py`
- `FR-04` → Task 2.1 → `SafeOrchestrator.check_completion_gate()` → `orchestrator.py` → `test_task_dag_execution.py`
- `FR-05` → Task 2.2 → `PatchApplier.apply()` → `patch_applier.py` → `test_patch_applier.py`

---

## 15. File-Level Implementation Contracts

- **File**: `skills/workflow-runtime/scripts/dag_planner.py`
  - **Purpose**: Pure algorithm — no file I/O except reading blueprint.
  - **Owner**: Coder
  - **Notes**: Use Kahn's algorithm for topological sort. `GLOBAL_FILES` list hard-coded.

- **File**: `skills/workflow-runtime/scripts/lock_manager.py`
  - **Purpose**: All-or-nothing file locking. Cross-platform PID check.
  - **Owner**: Coder
  - **Notes**: `os.kill(pid, 0)` raises `ProcessLookupError` if PID dead. Catch both `OSError` and `ProcessLookupError`.

- **File**: `skills/workflow-runtime/scripts/worker_manager.py`
  - **Purpose**: Worker lifecycle tracking. Log file per worker.
  - **Owner**: Coder
  - **Notes**: Log directory: `.agents/runtime/logs/`. Create on first use.

- **File**: `skills/workflow-runtime/scripts/orchestrator.py`
  - **Purpose**: Coordinates all components. Completion gate is non-negotiable.
  - **Owner**: Coder
  - **Notes**: Default mode MUST be `safe_sequential`. Print explicit warning if parallel attempted without conditions.

- **File**: `skills/workflow-runtime/scripts/patch_applier.py`
  - **Purpose**: Patch validation and application. Uses `git apply --check` for dry-run.
  - **Owner**: Coder
  - **Notes**: If `git` not available, fall back to manual patch parsing. Never apply without scope validation first.
