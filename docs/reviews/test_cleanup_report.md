# Test Suite Cleanup Strategy Report

This report outlines the rationalization plan for the framework test suite to phase out historical test files and keep coverage clean.

---

## 1. Test Classification

### A. Keep (v3 Production Engine Verification)
- **Files**:
  - `test_session_core.py`
  - `test_event_store.py`
  - `test_logical_agent.py`
  - `test_context_engine.py`
  - `test_logical_scheduler.py`
  - `test_external_executor.py`
  - `test_permissions.py`
  - `test_websocket_server.py`
  - `test_skill_migration.py`
  - `test_cli_runner.py`
  - `test_post_release_lifecycle.py`
- **Criteria**: Validates zero-trust permission boundaries, async workers backpressure, context OCC transitions, and event-store checkpoints.

---

### B. Archive (v1/v2 Legacy Mock Checks)
- **Files**:
  - `test_daemon_process.py`
  - `test_process_agent.py`
  - `test_legacy_orchestrator.py`
- **Criteria**: Relies on old daemon processes. Scheduled to be moved to an `archive/` folder.

---

### C. Remove (Obsolete and Duplicate Mocks)
- **Files**:
  - `test_duplicate_scheduler_mock.py`
  - `test_old_context_lock.py`
- **Criteria**: Contain duplicate assertions covered by `test_context_integration.py` or invalid single-thread execution assumptions.
