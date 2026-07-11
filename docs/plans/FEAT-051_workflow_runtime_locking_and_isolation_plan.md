<!-- File path: docs/plans/FEAT-051_workflow_runtime_locking_and_isolation_plan.md -->

---
feature_id: FEAT-051
feature_name: Fix Workflow Runtime State Locking, Concurrency, and Test Isolation
status: reviewed
stage: planning
created_at: 2026-07-11
updated_at: 2026-07-11
previous_artifact: ../brainstorming/FEAT-051_workflow_runtime_locking_and_isolation.md
next_artifact: ../designs/FEAT-051_workflow_runtime_locking_and_isolation_blueprint.md
---

# FEAT-051: Fix Workflow Runtime State Locking, Concurrency, and Test Isolation

## 1. Requirement Coverage Matrix
| Req ID | Phase | Task ID | Deliverable | Covered? |
| :--- | :--- | :--- | :--- | :---: |
| FR-01 | Phase 1 | Task 1.1 | Implement workflow lease model and `workflow-lease.json` metadata file | [x] |
| FR-02 | Phase 1 | Task 1.2 | Implement self-healing stale lease detection (checks PID active state, hostname, start time, and heartbeat age) and auto-recovery | [x] |
| FR-03 | Phase 1 | Task 1.3 | Implement idempotent workflow `start` logic yielding exit code 0 | [x] |
| FR-04 | Phase 1 | Task 1.4 | Define `StateStore` abstraction with `AtomicFileStateStore` utilizing temp-file replacements | [x] |
| FR-05 | Phase 1 | Task 1.5 | Implement runtime modes (`normal`, `test-isolated`, `test-stateful`, `test-memory`) with overrides via environment variables | [x] |
| FR-06 | Phase 1 | Task 1.6 | Add exit hooks (`atexit`, `SIGINT`, `SIGTERM`) for lease release | [x] |
| NFR-01| Phase 1 | Task 1.7 | Implement Optimistic Concurrency Control (CAS) using `generation` and `revision` fields | [x] |
| NFR-02| Phase 1 | Task 1.8 | Implement atomic writes using unique temporary file names and `os.replace` swaps | [x] |
| NFR-03| Phase 2 | Task 2.1 | Implement debouncing and rate-limiting for heartbeats and progress events | [x] |
| NFR-04| Phase 2 | Task 2.2 | Configure Pytest fixtures to run stateful tests in isolated directories, allowing parallel test execution | [x] |
| FR-07 | Phase 3 | Task 3.1 | Implement telemetry subcommands (`status`, `lock inspect/recover/release`) | [x] |

## 2. Task Ownership & Roles
- **Task 1.1 - 1.4**: [Architect] - Design the lease schema and define the validation workflow for stale recovery.
- **Task 1.5 - 1.8**: [Coder] - Implement the StateStore registry, atomic replacement methods, CAS collision handlers, and exit hooks.
- **Task 2.1**: [Coder] - Implement telemetry write debouncer throttling logic.
- **Task 2.2**: [Reviewer] - Design the pytest fixture framework, verify parallel execution isolation, and prevent host state pollution.
- **Task 3.1**: [Coder] - Implement CLI controller routes for lease/status query commands.

## 3. Parallel Execution Plan
- **Sequential Tasks**: Task 1.1 -> Task 1.2 -> Task 1.3
- **Parallel Tasks**: [Task 1.4, Task 1.5, Task 1.6, Task 1.7, Task 1.8] (Can be developed concurrently once base StateStore interface is ready)
- **Blocking Tasks**: Task 1.4 (stale checks block Task 3.1 CLI tool integration)
- **Independent Tasks**: Task 2.1 (debouncing can run independently)
- **Recommended Execution Groups**:
  - Group 1: Task 1.1, Task 1.4, Task 1.8 (Lease & Atomic store foundation)
  - Group 2: Task 1.2, Task 1.7, Task 1.3 (CAS control & Idempotency)
  - Group 3: Task 1.5, Task 1.6, Task 2.2 (Runtime mode configurations & test isolation)
  - Group 4: Task 2.1, Task 3.1 (Optimization and subcommands)

## 4. File Change Plan (Implementation Boundary)
| Task ID | File Path | Operation | Rationale |
| :--- | :--- | :--- | :--- |
| Task 1.1 | `skills/workflow-runtime/scripts/session.py` | Modify | Move raw state reading and lock queries to StateStore wrapper |
| Task 1.2 | `skills/workflow-runtime/scripts/state_sync.py` | Modify | Extract serialization to store registry |
| Task 1.4 | `skills/workflow-runtime/scripts/workflow_runtime.py` | Modify | Integrate stale checking and command handler entry points |
| Task 1.5 | `skills/workflow-runtime/scripts/context.py` | Modify | Route context loading through runtime mode options |
| Task 2.2 | `tests/conftest.py` | Modify | Implement worker isolated workspace setup for pytest-xdist |

## 5. Blueprint Preparation Inputs
- **Interfaces / Classes / Modules**:
  - `StateStore` base class with operations: `read()`, `write()`, `update()`, `acquire_lease()`, `release_lease()`.
  - `AtomicFileStateStore` child class subclassing `StateStore`.
- **Provider Pattern details**: Use the existing registry patterns inside `workflow-runtime` to load store implementations dynamically based on active mode flags.
- **Data Flow / Sequence Flow**: Standard CAS checking loop: Read -> Compute -> Compare generation -> Write -> Increment revision.
- **Migration Strategy & Testing Architecture**: Provide dummy schemas to parse legacy checkpoint files missing revision metadata safely (fallback default to revision 1).

## 6. Verification Strategy & Test Mapping
- **Unit Tests**:
  - `tests/test_state_store.py` (Mapped to Task 1.1, Task 1.4, Task 1.7)
  - `tests/test_runtime_modes.py` (Mapped to Task 1.5)
- **Integration Tests**:
  - `tests/test_locking_recovery.py` (Mapped to Task 1.2, Task 1.6)
  - `tests/test_idempotent_start.py` (Mapped to Task 1.3)
- **Concurrency & Parallel Testing**:
  - Execute `pytest -n auto` to verify total test execution isolation.

## 7. Exit Criteria
- **Phase 1 Exit Criteria**:
  - [ ] 100% of CAS validation unit tests succeed.
  - [ ] Simulated process terminations trigger lease cleanup successfully.
- **Phase 2 Exit Criteria**:
  - [ ] Parallel pytest runs completed without a single filesystem state collision.
  - [ ] Event log file writes are reduced by at least 40% under simulation.
- **Phase 3 Exit Criteria**:
  - [ ] Status commands and stale manual release tools are verified correct.

## 8. Rollback Strategy
- **Phase 1 Rollback**:
  - Trigger: System deadlock or visualizer dashboard telemetry breakage.
  - Steps: Revert git commits; restore backup `workflow.lock` logic in `workflow_runtime.py`.
  - Recovery: Re-run validation tests under standard lock settings.

## 9. Change Impact Matrix
| Task ID | Files | Modules | Runtime | Extension | Documentation | Memory | Database |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Task 1.1 | Yes | Yes | Yes | No | No | No | No |
| Task 1.2 | Yes | Yes | Yes | No | No | No | No |
| Task 1.5 | Yes | Yes | Yes | No | Yes | No | No |
| Task 2.2 | Yes | No | Yes | No | No | No | No |
| Task 3.1 | Yes | Yes | Yes | No | Yes | No | No |

## 10. Artifact Production Plan
- **Phase 1 Artifacts**: `docs/designs/FEAT-051_workflow_runtime_locking_and_isolation_blueprint.md`
- **Phase 2 Artifacts**: `docs/adr/ADR-006_lease_locking_and_isolation.md`
- **Phase 3 Artifacts**: `docs/releases/Release_Notes_v6.7.0.md`

## 11. Token & Execution Optimization
- **Sequential execution cost**: Normal execution has no overhead since metadata lease is tiny.
- **Parallel execution opportunities**: Pytest runs can utilize 100% core capacity.
- **Expected token savings**: CAS prevents redundant double queries and loops.

## Recommended Next Skill
/blueprint
