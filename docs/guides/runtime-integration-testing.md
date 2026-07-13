# Runtime Integration Testing Guide

This document explains how to run the AIWF runtime integration test suite for FEAT-050/051/052/053.

## Test File Overview

| File | Type | FR | Components Covered |
|------|------|----|--------------------|
| [test_state_migration.py](../../skills/workflow-runtime/tests/test_state_migration.py) | Unit | FR-01 | `state_path`, `atomic_writer`, `event_logger`, `state_aggregator` |
| [test_state_aggregator.py](../../skills/workflow-runtime/tests/test_state_aggregator.py) | Unit | FR-02 | `state_aggregator` — dashboard, gates, health |
| [test_event_reducer.py](../../skills/workflow-runtime/tests/test_event_reducer.py) | Unit | FR-02 | `event_reducer` — 14 event dispatch handlers |
| [test_phase_release_gates.py](../../skills/workflow-runtime/tests/test_phase_release_gates.py) | Unit | FR-03 | `ledger`, `phase_controller`, `release_gate` |
| [test_file_locks.py](../../skills/workflow-runtime/tests/test_file_locks.py) | Unit | FR-04 | `lock_manager` — all-or-nothing, stale, security |
| [test_worker_registry.py](../../skills/workflow-runtime/tests/test_worker_registry.py) | Unit | FR-04 | `worker_manager` — PID lifecycle, orphan |
| [test_dag_planner.py](../../skills/workflow-runtime/tests/test_dag_planner.py) | Unit | FR-04 | `dag_planner` — Kahn sort, cycle, parallel safety |
| [test_task_dag_execution.py](../../skills/workflow-runtime/tests/test_task_dag_execution.py) | Integration | FR-04 | DAG + Lock + Worker end-to-end |
| [test_resume_recovery.py](../../skills/workflow-runtime/tests/test_resume_recovery.py) | Integration | FR-04 | Checkpoint restore, crash recovery, stale cleanup |
| [test_visualizer_dashboard_state.py](../../skills/workflow-runtime/tests/test_visualizer_dashboard_state.py) | Integration | FR-04 | Dashboard JSON structure for Visualizer |
| [test_runtime_stress.py](../../skills/workflow-runtime/tests/test_runtime_stress.py) | Stress | FR-05/06 | 50 random blueprints + 4 failure injection types |

## Running Tests

### Fast Tests Only (< 30 seconds)

Exclude stress tests for quick CI:

```bash
python -m pytest skills/workflow-runtime/tests/ -k 'not stress' -v
```

### All Unit Tests (Specific Modules)

```bash
# FR-01: State migration
python -m pytest skills/workflow-runtime/tests/test_state_migration.py -v

# FR-02: Aggregator + Reducer
python -m pytest skills/workflow-runtime/tests/test_state_aggregator.py skills/workflow-runtime/tests/test_event_reducer.py -v

# FR-03: Phase + Release Gate
python -m pytest skills/workflow-runtime/tests/test_phase_release_gates.py -v

# FR-04: DAG + Lock + Worker
python -m pytest skills/workflow-runtime/tests/test_file_locks.py skills/workflow-runtime/tests/test_worker_registry.py skills/workflow-runtime/tests/test_dag_planner.py -v
```

### Integration Tests (FR-04)

```bash
python -m pytest skills/workflow-runtime/tests/test_task_dag_execution.py skills/workflow-runtime/tests/test_resume_recovery.py skills/workflow-runtime/tests/test_visualizer_dashboard_state.py -v
```

### Stress Tests (FR-05/06, opt-in, ~5 min)

```bash
python -m pytest skills/workflow-runtime/tests/test_runtime_stress.py -v --timeout=300
```

### Full Regression Suite

```bash
python -m pytest skills/workflow-runtime/tests/ -v
```

## Test Fixtures

All fixtures are in `skills/workflow-runtime/tests/fixtures/`:

```
fixtures/
├── conftest.py                      # RuntimeTestBase (shared test infrastructure)
├── blueprints/
│   ├── FEAT-999_multi_phase_blueprint.json   # 15-task, 5-phase valid blueprint
│   ├── FEAT-998_single_phase_legacy_blueprint.md  # Legacy single-phase format
│   └── FEAT-997_broken_blueprint.json        # Cycle + abs path + traversal (invalid)
└── state/
    ├── legacy_session/              # Pre-migration .session.json format
    ├── flat_split/                  # Flat state files (pre-nested)
    └── nested_split/               # Canonical nested state with stale worker
```

## RuntimeTestBase

All tests extend `RuntimeTestBase` from `fixtures/conftest.py`:

```python
from fixtures.conftest import RuntimeTestBase

class MyTests(RuntimeTestBase):
    def test_something(self):
        from state_aggregator import StateAggregator
        from state_path import ensure_dirs
        ensure_dirs(self.workspace)           # Create canonical dirs
        self.write_state("workflow", {...})   # Write sub-state
        agg = StateAggregator(self.workspace)
        dashboard = agg.aggregate()
        self.assertFalse(dashboard["release_allowed"])
```

Key utilities:
- `self.workspace` — isolated tempdir, auto-cleaned in `tearDown()`
- `self.state_root` — `.agents/state/` inside workspace
- `self.write_state(category, data)` — write sub-state JSON
- `self.read_dashboard()` — read current `dashboard.json`
- `self.load_fixture(path)` — load JSON from `fixtures/`
- `self.make_ledger_blueprint(feature_id, n_phases, tasks_per_phase)` — generate test blueprint

## Environment Variables

| Variable | Purpose | Set By |
|----------|---------|--------|
| `AIWF_STATE_ROOT` | Override canonical state root path | `RuntimeTestBase.setUp()` |

## Interpreting Results

| Status | Meaning |
|--------|---------|
| `PASS` | Test case passed, no state corruption |
| `FAIL` | Test assertion failed — check `AssertionError` message |
| `SKIP` | Platform-specific or opt-in test skipped |
| `ERROR` | Unexpected exception — likely module import or fixture issue |

## Adding New Tests

1. Extend `RuntimeTestBase` from `fixtures/conftest.py`
2. Place test file in `skills/workflow-runtime/tests/`
3. Name file `test_<module>.py`
4. Each test case must clean up in `tearDown()` (auto-handled by `RuntimeTestBase`)
5. Reference FR traceability in docstring

```python
class MyNewTests(RuntimeTestBase):
    # TC1: Description (FR-XX)
    def test_my_case(self):
        """FR-XX: Brief description."""
        ...
```
