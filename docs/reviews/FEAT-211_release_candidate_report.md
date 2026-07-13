# Release Candidate Report (FEAT-211)

## 1. Release Summary
This release implements **FEAT-211: Session Runtime Redesign**, replacing the legacy multi-process daemon architecture with a modern, high-performance in-process execution model. 
Key highlights include the SQLite-backed Event Store, Copy-on-Write Shared Context Engine, Bounded Worker Pool Scheduler, strictly isolated Tool Executor with global process boundary validators, and a multi-layer hierarchical Permission Boundary.

---

## 2. Version Recommendation
- **Component Versioning**:
  - **Runtime Core & API**: `v3.0.0`
  - **Runtime SDK**: `v3.0.0`
  - **CLI Tools**: `v3.0.0`
- **Release Strategy**: Semantic Versioning Major Bump (`v2.x.x` -> `v3.0.0`) due to architectural transformation, though backward compatibility wraps are provided for v1 contracts.

---

## 3. Changed & New Components

### Core scripts:
- `session_core.py` (Session lifecycle manager)
- `event_store.py` (SQLite WAL Event Bus)
- `logical_agent.py` (Logical Agent thread/coroutine abstraction)
- `context_engine.py` (Shared Context / OCC merging)
- `logical_scheduler.py` (Bounded Worker dispatcher)
- `external_executor.py` (Subprocess Tool Executor with global patch)
- `permission_boundary.py` (Access validation boundary)
- `websocket_server.py` (JSON-RPC Local WebSocket host)
- `runtime_sdk.py` (Client SDK API v3 wrapper)
- `compatibility_adapter.py` (Legacy mapping bridges)
- `skill_migration.py` (Skill Manifest v3 validation and legacy adapters)
- `cli_runner.py` (Modern CLI subcommands)

### Test suites:
- 10 unit test modules.
- 6 integration test modules.
- 1 certification harness.

---

## 4. Migration & Compatibility Status
- **Backward Compatibility**: Fully supported. Adaptor layer converts older task submissions and warns developers in developer console mode.
- **Rollback Strategy**: Fast rollback is achieved by toggling the framework parameter flag back to Mode 1 (Legacy Client).

---

## 5. Known Risks
- **POSIX process group cleanup constraints**: PGID signaling works natively on Linux/macOS. Under Windows, force task termination falls back to normal execution kill tree calls.

---

## 6. Release Checklist Status
- [x] No compilation / syntax errors (All 56 tests passed).
- [x] Process leaks checked (All active workers shutdown successfully).
- [x] Sandboxed directories validated.
- [x] Upgrade documentation completed.

**Release Status**: `READY_FOR_RELEASE`
