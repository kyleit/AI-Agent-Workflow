<!-- File path: docs/designs/FEAT-053_aiwf_runtime_integration_stress_testing_blueprint.md -->

---
feature_id: FEAT-053
feature_name: AIWF Runtime Integration and Stress Testing Suite
status: reviewed
stage: blueprint
created_at: 2026-07-10
updated_at: 2026-07-10
previous_artifact: ../plans/FEAT-053_aiwf_runtime_integration_stress_testing_plan.md
next_artifact: ../../skills/workflow-runtime/tests/
---

# Technical Design Blueprint & Implementation Contract – AIWF Runtime Integration and Stress Testing Suite

## 0. Baseline Context & References

- **Memory Baseline**: High confidence. Existing test files in `skills/workflow-runtime/tests/`: `test_registry.py`, `test_optimizer.py`, `test_budget_controller.py`, `test_transcript_parsers.py`, `test_reconciliation_engine.py`, etc. Framework uses Python `unittest` + `pytest`. No existing fixture infrastructure.
- **Inspected Source Files**:
  - `skills/workflow-runtime/tests/test_registry.py` — Pattern reference for test structure.
  - `skills/workflow-runtime/tests/test_transcript_first_pipeline.py` — Integration test pattern.

---

## 1. File-by-File Analysis & Proposed Mutations

| File Path | Operation | Responsibility | Dependency | Impact & Risk |
| :--- | :--- | :--- | :--- | :--- |
| `skills/workflow-runtime/tests/fixtures/` | NEW (dir) | Root for all test fixtures | None | Low |
| `skills/workflow-runtime/tests/fixtures/state/legacy_session/.agents/.session.json` | NEW | Legacy session fixture | None | Low |
| `skills/workflow-runtime/tests/fixtures/state/flat_split/.agents/state/*.json` | NEW | Flat split state fixtures | None | Low |
| `skills/workflow-runtime/tests/fixtures/state/nested_split/.agents/state/` | NEW | Nested canonical state fixtures | None | Low |
| `skills/workflow-runtime/tests/fixtures/blueprints/FEAT-999_multi_phase_blueprint.json` | NEW | 5-phase 15+ task blueprint fixture | None | Low |
| `skills/workflow-runtime/tests/fixtures/blueprints/FEAT-998_single_phase_legacy_blueprint.md` | NEW | Legacy single-phase blueprint fixture | None | Low |
| `skills/workflow-runtime/tests/fixtures/blueprints/FEAT-997_broken_blueprint.json` | NEW | Broken blueprint with cycle + invalid paths | None | Low |
| `skills/workflow-runtime/tests/test_state_migration.py` | NEW | Migration tests | FEAT-050 modules | Low – test only |
| `skills/workflow-runtime/tests/test_state_aggregator.py` | NEW | Aggregator tests | FEAT-050 modules | Low – test only |
| `skills/workflow-runtime/tests/test_event_reducer.py` | NEW | Reducer / event replay tests | FEAT-050 modules | Low – test only |
| `skills/workflow-runtime/tests/test_phase_release_gates.py` | NEW | Gate condition tests | FEAT-051 modules | Low – test only |
| `skills/workflow-runtime/tests/test_file_locks.py` | NEW | Lock safety tests | FEAT-052 modules | Low – test only |
| `skills/workflow-runtime/tests/test_worker_registry.py` | NEW | Worker lifecycle tests | FEAT-052 modules | Low – test only |
| `skills/workflow-runtime/tests/test_task_dag_execution.py` | NEW | DAG execution tests | FEAT-052 modules | Low – test only |
| `skills/workflow-runtime/tests/test_resume_recovery.py` | NEW | Resume and abort tests | FEAT-052 modules | Low – test only |
| `skills/workflow-runtime/tests/test_visualizer_dashboard_state.py` | NEW | Dashboard state tests | FEAT-050 modules | Low – test only |
| `skills/workflow-runtime/tests/test_runtime_stress.py` | NEW | Stress + failure injection tests | All FEAT-050/051/052 | Low – isolated tempdir |
| `docs/guides/runtime-integration-testing.md` | NEW | Test running guide | None | Low |
| `docs/guides/runtime-recovery-playbook.md` | NEW | Recovery playbook | None | Low |

---

## 2. Target Folder Structure

```text
skills/workflow-runtime/tests/
├── fixtures/
│   ├── blueprints/
│   │   ├── FEAT-997_broken_blueprint.json
│   │   ├── FEAT-998_single_phase_legacy_blueprint.md
│   │   └── FEAT-999_multi_phase_blueprint.json
│   └── state/
│       ├── flat_split/
│       │   └── .agents/state/
│       │       ├── agents.json
│       │       ├── approvals.json
│       │       ├── breakdown.json
│       │       ├── context.json
│       │       ├── recovery.json
│       │       ├── runtime.json
│       │       ├── usage.json
│       │       └── workflow.json
│       ├── legacy_session/
│       │   └── .agents/.session.json
│       └── nested_split/
│           └── .agents/state/
│               ├── context/context.json
│               ├── dashboard.json
│               ├── events/events.jsonl
│               ├── project/profile.json
│               ├── recovery/recovery.json
│               ├── runtime/runtime.json
│               └── workflow/workflow.json
├── test_event_reducer.py
├── test_file_locks.py
├── test_phase_release_gates.py
├── test_resume_recovery.py
├── test_runtime_stress.py
├── test_state_aggregator.py
├── test_state_migration.py
├── test_task_dag_execution.py
├── test_visualizer_dashboard_state.py
└── test_worker_registry.py

docs/guides/
├── runtime-integration-testing.md
└── runtime-recovery-playbook.md
```

---

## 3. Complete Class & Module Design

### Test Base Pattern — `RuntimeTestBase`

All test files must inherit from a shared base class defined in `fixtures/conftest.py`:

```python
class RuntimeTestBase(unittest.TestCase):
    def setUp(self):
        self.workspace = tempfile.mkdtemp(prefix="aiwf_test_")
        # Patch StatePath to use self.workspace
        
    def tearDown(self):
        shutil.rmtree(self.workspace, ignore_errors=True)
        
    def load_fixture(self, fixture_path: str) -> dict:
        # Load JSON fixture from fixtures/ dir
        
    def copy_fixture_workspace(self, fixture_name: str) -> str:
        # Copy fixture state into self.workspace; return path
```

### `test_state_migration.py` — StateMigrationTests

- **Test Cases** (10):
  1. `test_migrate_legacy_session_to_nested` — From legacy `.session.json` → nested canonical.
  2. `test_migrate_flat_split_to_nested` — From flat `state/*.json` → nested.
  3. `test_migrate_idempotent` — Run migration twice → identical output.
  4. `test_migrate_preserves_all_fields` — No field lost during migration.
  5. `test_migrate_creates_dashboard_json` — `dashboard.json` generated post-migration.
  6. `test_migrate_creates_deprecated_session_snapshot` — `.session.json` has `_deprecated: true`.
  7. `test_migrate_creates_recovery_report` — `recovery/state-migration-report.json` written.
  8. `test_migrate_invalid_json_handled` — Broken JSON file reported, source not destroyed.
  9. `test_migrate_backup_created_before_modification` — Backup exists in `backups/`.
  10. `test_migrate_dry_run_no_changes` — `--dry-run` produces report but no file changes.

### `test_state_aggregator.py` — StateAggregatorTests

- **Test Cases** (12):
  1. Aggregator derives `suggested_next_skill = wait` when runtime status `in_progress`.
  2. Aggregator blocks release when any implementation phase incomplete.
  3. Aggregator recommends next implementation phase after Phase 1 completes.
  4. Aggregator recommends `/debug` only after all phases complete.
  5. Aggregator recommends `/verify` only after debug PASS.
  6. Aggregator recommends `/release` only after verify PASS.
  7. Aggregator recommends recovery when stale lock exists.
  8. Aggregator recommends recovery when orphan worker exists.
  9. Aggregator emits clear `release_block_reason`.
  10. Aggregator writes valid `dashboard.json`.
  11. Aggregator output is deterministic for same input (run 3x, compare).
  12. Aggregator ignores stale `workflow.json.suggested_next_skill` if implementation disagrees.

### `test_event_reducer.py` — EventReducerTests

- **Test Sequences** (13):
  1. `WorkflowInitialized → SkillStarted → SkillCompleted` → correct workflow state.
  2. `PhaseStarted → TaskStarted → TaskCompleted → PhaseCompleted` → correct runtime state.
  3. `TaskFailed` blocks downstream tasks.
  4. `WorkerSpawned → WorkerCompleted` → active_workers count decremented.
  5. `WorkerSpawned` without `WorkerCompleted` → orphan detection triggered.
  6. `FileLockAcquired → FileLockReleased` → lock count zero.
  7. `DebugPassed` → verify_allowed becomes True.
  8. `VerifyPassed` → release_allowed becomes True.
  9. `ReleaseRequested` before verify → `ReleaseBlocked` event emitted.
  10. `UsageUpdated` → context/usage state updated.
  11. Replaying all events from scratch → equivalent state to incremental.
  12. Duplicate `event_id` → ignored (no double-apply).
  13. Out-of-order event (monotone timestamp violation) → reported as warning, handled.

### `test_phase_release_gates.py` — PhaseReleaseGateTests

- **Test Cases** (8):
  1. Phase 1 complete with remaining phases → `release_allowed=False`, `verify_allowed=False`, next=implement.
  2. All phases complete → `debug_allowed=True`, `release_allowed=False`, next=debug.
  3. Debug failed → `verify_allowed=False`, next remains debug.
  4. Debug passed → `verify_allowed=True`, next=verify.
  5. Verify failed → `release_allowed=False`, next=verify/debug.
  6. Verify passed → `release_allowed=True`, next=release.
  7. Partial release requires explicit approval text match.
  8. Release blocked under 7 conditions (listed individually).

### `test_runtime_stress.py` — StressTests + FailureInjectionTests

- **Stress Test Generator**:
  ```python
  def generate_random_blueprint(n_phases: int, n_tasks_per_phase: int, seed: int) -> dict:
      # Generate valid random blueprint (no cycles) using seed for reproducibility
      # Include: some overlapping write_sets, some stale locks, some orphan workers
  ```
- **Stress Assertions** (per blueprint run):
  - No JSON files corrupted.
  - No release allowed before verify PASS.
  - No phase complete while tasks remain.
  - No active locks after successful completion.
  - Aggregator deterministic.

- **Failure Injection Cases** (10):
  1. JSON write interrupted via mocked `IOError` mid-write.
  2. `os.replace()` fails → original intact.
  3. Invalid JSON state file → doctor reports exact file.
  4. Missing state file → degraded mode, not crash.
  5. Duplicate `event_id` → second emit rejected.
  6. Event with missing `task_id` → handled gracefully.
  7. Worker PID unavailable (process already dead at register time).
  8. Permission denied on lock file → `FileLockConflict`.
  9. Patch conflict → `PatchConflictError`, workspace unchanged.
  10. Verification command failure → task marked failed, not completed.

---

## 4. Detailed Interface Contracts

### `test_runtime_stress.py::StressTest.run_blueprint_lifecycle(blueprint: dict) -> dict`
- **Parameters**: `blueprint` — Generated or fixture blueprint dict.
- **Return**: `{success: bool, phases_completed: int, json_corruptions: int, early_releases: int, orphan_workers_remaining: int}`.
- **Side Effects**: All in isolated `tempfile.mkdtemp()`. Auto-cleaned in `tearDown`.

### Fixture JSON Schemas

- **`FEAT-999_multi_phase_blueprint.json`** must include:
  - 5 phases with IDs `Phase 1` through `Phase 5`.
  - ≥15 tasks total across phases.
  - At least 2 parallel candidate tasks (non-overlapping write_sets).
  - At least 2 tasks with overlapping write_sets (must be detected as sequential-only).
  - `dependencies` field linking tasks across phases.
  - `expected_outputs` for each task.
  - `verification` commands for 3+ tasks.

- **`FEAT-997_broken_blueprint.json`** must include:
  - A dependency cycle: `Task A → Task B → Task A`.
  - A reference to non-existent task `Task Z`.
  - A task with write_set containing absolute path `/etc/hosts`.
  - A task with no `task_id` field.

---

## 5. Configuration Schema

```json
{
  "test_suite": {
    "fast_timeout_seconds": 30,
    "stress_blueprint_count": 50,
    "stress_tasks_per_phase_range": [10, 30],
    "failure_injection_enabled": true,
    "cleanup_temp_dirs": true
  }
}
```

---

## 6. Database & Storage Design

- Tests use `tempfile.mkdtemp()` exclusively. No persistent storage.
- `NEVER` write to real `.agents/` directory during tests.
- Test fixtures stored in `tests/fixtures/` (read-only during tests).

---

## 7. Cache Architecture

- No cache. Test isolation requires fresh state per test case.

---

## 8. Error Model

| Assertion | Failure Message | Recovery |
| :--- | :--- | :--- |
| JSON corruption detected | `f"JSON corrupted in {path}: {error}"` | Test fails; temp dir preserved for inspection |
| Early release allowed | `"release_allowed=True but verify not PASS"` | Test fails |
| Orphan worker remaining | `f"Worker {worker_id} (PID {pid}) still alive after completion"` | Test fails |
| Active lock remaining | `f"Lock on {file} held by Task {task_id} not released"` | Test fails |
| Stress test timeout | `f"Blueprint {seed} exceeded {timeout}s"` | Skip remaining stress iterations |

---

## 9. Skill Integration Contracts

- No skill integration. Tests run in complete isolation.
- `conftest.py` patches all `StatePath` calls to use temp directories.

---

## 10. CLI & Runtime Contracts

```bash
# Fast tests (< 30s, mandatory in CI)
python -m pytest skills/workflow-runtime/tests/ -k "not stress" -v

# Stress tests (opt-in)
python -m pytest skills/workflow-runtime/tests/test_runtime_stress.py -v --timeout=300

# Specific test category
python -m pytest skills/workflow-runtime/tests/test_phase_release_gates.py -v

# Regression (existing tests)
python -m pytest skills/workflow-runtime/tests/ -v
```

---

## 11. Sequence Flows

### Stress Test Blueprint Lifecycle
1. `generate_random_blueprint(n_phases=5, n_tasks_per_phase=15, seed=42)` called.
2. Isolated workspace created: `workspace = tempfile.mkdtemp()`.
3. `state migrate` simulation: init canonical state.
4. `ledger.init_from_blueprint(blueprint)`.
5. For each phase: `orchestrator.run_phase()` → tasks executed with fake I/O.
6. After all phases: attempt premature release → assert blocked.
7. Simulate debug PASS → emit `DebugPassed` event.
8. Simulate verify PASS → emit `VerifyPassed` event.
9. Attempt release → assert allowed.
10. Validate: no JSON corruption, no active locks, no orphan workers.
11. `tearDown()`: `shutil.rmtree(workspace)`.

---

## 12. Security & Safety

- **Isolation Absolute**: Tests MUST NOT write to real `.agents/`, `docs/`, or `skills/` directories.
- **Fixture Read-Only**: `tests/fixtures/` directory must not be modified during test runs. Copy to tempdir before use.
- **No Network**: Tests must not make network calls.
- **No Real Git**: Patch tests use mock git operations, not real `git apply`.

---

## 13. Complete Test Matrix

| Req ID | Test Type | Test File | Assertions |
| :--- | :--- | :--- | :--- |
| FR-01 | Unit | `test_state_migration.py` | 10 test cases covering legacy, flat, nested, idempotency |
| FR-02 | Unit | `test_state_aggregator.py` + `test_event_reducer.py` | 12 + 13 = 25 test cases |
| FR-03 | Unit | `test_phase_release_gates.py` | 8 gate conditions |
| FR-04 | Unit | `test_file_locks.py` + `test_worker_registry.py` | 10 + 10 test cases each |
| FR-04 | Integration | `test_task_dag_execution.py` | 14 DAG execution cases |
| FR-04 | Integration | `test_resume_recovery.py` | 10 resume/recovery cases |
| FR-04 | Integration | `test_visualizer_dashboard_state.py` | 6 dashboard state cases |
| FR-05 | Stress | `test_runtime_stress.py` | 50+ blueprints; zero corruption assertion |
| FR-06 | Failure | `test_runtime_stress.py` (injection section) | 10 failure scenarios |

---

## 14. Requirement Traceability Matrix

- `FR-01` → Task 1.2 → `StateMigrationTests` → `test_state_migration.py`
- `FR-02` → Task 1.3 → `StateAggregatorTests + EventReducerTests` → `test_state_aggregator.py + test_event_reducer.py`
- `FR-03` → Task 2.1 → `PhaseReleaseGateTests` → `test_phase_release_gates.py`
- `FR-04` → Task 2.2 + 2.3 → Lock/Worker/DAG/Resume tests → multiple test files
- `FR-05` → Task 3.1 → `StressTests` → `test_runtime_stress.py`
- `FR-06` → Task 3.2 → `FailureInjectionTests` → `test_runtime_stress.py`

---

## 15. File-Level Implementation Contracts

- **File**: `skills/workflow-runtime/tests/fixtures/conftest.py`
  - **Purpose**: Shared `RuntimeTestBase` class; `StatePath` patching; fixture loading utilities.
  - **Owner**: Coder
  - **Notes**: Must be importable by all test files without circular imports.

- **File**: `skills/workflow-runtime/tests/test_runtime_stress.py`
  - **Purpose**: Stress generator + failure injection. Opt-in via `--stress` flag or separate pytest marker.
  - **Owner**: Coder
  - **Notes**: Reproducible via seed. 50 blueprints as minimum. Timeout per blueprint = 10s.

- **File**: `docs/guides/runtime-integration-testing.md`
  - **Purpose**: Document all test commands, categories, interpretation of failures.
  - **Owner**: Coder
  - **Notes**: Include table of test files vs. components tested.

- **File**: `docs/guides/runtime-recovery-playbook.md`
  - **Purpose**: Step-by-step guides for: recovering stale locks, clearing orphan workers, fixing corrupt state files.
  - **Owner**: Coder
  - **Notes**: Each playbook entry must have: Symptom → Diagnosis Command → Fix Command → Verification.
