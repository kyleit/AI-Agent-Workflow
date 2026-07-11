<!-- File path: docs/designs/FEAT-051_workflow_runtime_locking_and_isolation_blueprint.md -->

---
feature_id: FEAT-051
feature_name: Fix Workflow Runtime State Locking, Concurrency, and Test Isolation
status: reviewed
stage: blueprint
created_at: 2026-07-11
updated_at: 2026-07-11
previous_artifact: ../plans/FEAT-051_workflow_runtime_locking_and_isolation_plan.md
next_artifact: [Implementation (Source Code)](../../)
---

# Technical Design Blueprint & Implementation Contract – Fix Workflow Runtime State Locking, Concurrency, and Test Isolation

## 0. Baseline Context & References
- **Memory Baseline**: State store configurations, runtime session aggregates, and lock managers inside `.agents/state/` and `skills/workflow-runtime/`.
- **RAG Query Summaries**: Existing session locking mechanisms (`workflow.lock` file checking) and concurrent write utilities (`state_sync.py`).
- **Inspected Source Files**:
  - [workflow_runtime.py](file:///E:/AgentsProject/skills/workflow-runtime/scripts/workflow_runtime.py)
  - [session.py](file:///E:/AgentsProject/skills/workflow-runtime/scripts/session.py)
  - [state_sync.py](file:///E:/AgentsProject/skills/workflow-runtime/scripts/state_sync.py)
  - [context.py](file:///E:/AgentsProject/skills/workflow-runtime/scripts/context.py)

## 1. File-by-File Analysis & Proposed Mutations
| File Path | Operation | Responsibility | Dependency | Impact & Risk |
| :--- | :--- | :--- | :--- | :--- |
| `skills/workflow-runtime/scripts/lease.py` | NEW | Define `WorkflowLease` class and checking helper | None | Low. Handles cross-platform PID start-time validation. |
| `skills/workflow-runtime/scripts/state_store.py` | NEW | Define `StateStore`, `AtomicFileStateStore`, `InMemoryStateStore`, and `NullStateStore` | None | Low. Provides abstract state database. |
| `skills/workflow-runtime/scripts/session.py` | MODIFY | Refactor save/load to call the active `StateStore` instance | `state_store.py` | Medium. Standard session caching read/write routes modified. |
| `skills/workflow-runtime/scripts/state_sync.py` | MODIFY | Move serialization pipelines and CAS revision matching into `StateStore` | `state_store.py` | Medium. Concurrent write serialization adjustments. |
| `skills/workflow-runtime/scripts/context.py` | MODIFY | Enable path routing via `AIWF_STATE_ROOT` and test overrides | `state_store.py` | Medium. Ensures isolated environment operations. |
| `skills/workflow-runtime/scripts/workflow_runtime.py` | MODIFY | Replace traditional `workflow.lock` calls with `WorkflowLease` checkpoints | `lease.py` | High. Changes core script start/stop gate controls. |
| `tests/conftest.py` | MODIFY | Register temp directories for parallel workers | None | Medium. Pytest harness updates. |

## 2. Target Folder Structure
```text
.
├── skills/
│   └── workflow-runtime/
│       ├── scripts/
│       │   ├── lease.py
│       │   ├── state_store.py
│       │   ├── session.py
│       │   ├── state_sync.py
│       │   ├── context.py
│       │   └── workflow_runtime.py
│       └── tests/
│           ├── test_state_store.py
│           └── test_locking_recovery.py
└── tests/
    └── conftest.py
```

## 3. Complete Class & Module Design
- **Class / Module Name**: `WorkflowLease` (in `skills/workflow-runtime/scripts/lease.py`)
  - **Responsibilities**: Represents active workflow lock state. Performs cross-platform process checks.
  - **Constructor Parameters**: None.
  - **Public Methods**:
    - `acquire(workflow_id: str, conversation_id: str) -> bool`
    - `release() -> bool`
    - `is_active() -> bool`
    - `inspect() -> dict`
  - **Internal Methods**:
    - `_get_process_creation_time(pid: int) -> float`
    - `_is_process_alive(pid: int) -> bool`
- **Class / Module Name**: `StateStore` (in `skills/workflow-runtime/scripts/state_store.py`)
  - **Responsibilities**: Base abstraction for writing and reading state data.
  - **Public Methods**:
    - `get(key: str) -> dict`
    - `set(key: str, data: dict, expected_revision: int = None) -> int`
    - `delete(key: str) -> bool`

## 4. Detailed Interface Contracts
- **API Signature**: `_get_process_creation_time(pid: int) -> float` (in `lease.py`)
  - **Parameters**: `pid` (target process ID).
  - **Return Types**: POSIX timestamp indicating process start time. Returns `0.0` if query fails.
  - **Exceptions**: None. All internal command failures are caught and handled.
  - **Validation Rules**: Uses `wmic` or `Get-CimInstance` on Windows, `/proc/<pid>/stat` on Linux, and `ps` on macOS.

- **API Signature**: `set(key: str, data: dict, expected_revision: int = None) -> int` (in `state_store.py`)
  - **Parameters**: `key` (file state basename), `data` (payload dictionary), `expected_revision` (CAS revision check).
  - **Return Types**: New revision count.
  - **Exceptions**: `RevisionConflictError` when the actual state revision is newer than `expected_revision`.
  - **Validation Rules**: Atomic write replaces payload using thread-safe write locks.

## 5. Configuration Schema
- **Current Schema**: Configuration is parsed through default command options and manual `.agents/.session.json` paths.
- **Target Schema**: Support env configuration options:
  - `AIWF_RUNTIME_MODE`: `normal`, `test-isolated`, `test-stateful`, `test-memory`.
  - `AIWF_STATE_ROOT`: Custom path routing directory (defaults to `.agents/state`).
  - `AIWF_DISABLE_STATE_WRITES`: `true` to force using `NullStateStore`.

## 6. Database & Storage Design
- **Tables**: None.
- **Indexes**: None.
- **Migration & Rollback Strategy**: Old session locks (`workflow.lock`) are ignored or deleted on startup.

## 7. Cache Architecture
- **Cache Keys**: Registry mappings inside `StateStore` to bypass disk reads during stateful sessions.
- **Invalidation Rules**: Re-reads disk state whenever `revision` mismatch is detected or `get()` is invoked with `force_refresh=True`.
- **TTL**: N/A.

## 8. Error Model
- **Exception Class**: `RevisionConflictError`
  - **Trigger Condition**: Concurrent writer updates state with outdated revision context.
  - **Recovery Strategy**: Read fresh state, apply changes, retry set (up to 3 times).
- **Exception Class**: `StaleLeaseRecovered`
  - **Trigger Condition**: Attempting to acquire lease when stale lock is found and deleted.

## 9. Skill Integration Contracts
- **Skill Name**: `workflow-runtime`
  - **Before Hooks**: None.
  - **After Hooks**: None.
  - **Runtime Calls**: Validate active lease status prior to launching other task subprocesses.

## 10. CLI & Runtime Contracts
- **Command Syntax**: `python workflow_runtime.py lock inspect`
  - **Output**: JSON representation of current lease information.
- **Command Syntax**: `python workflow_runtime.py lock recover`
  - **Exit Codes**: 0 (recovered / active), 1 (failed).

## 11. Sequence Flows
- **Normal Lease Acquisition**:
  1. Client calls `WorkflowLease.acquire()`.
  2. Read `workflow-lease.json` (not found or stale).
  3. Write current PID, start time, and conversation details.
  4. Heartbeat thread starts writing updates every 15 seconds.
- **Stale Lease Recovery**:
  1. Client calls `WorkflowLease.acquire()`.
  2. Lease exists but heartbeat is older than 45 seconds, PID is inactive, or hostname does not match.
  3. Archive stale file to `docs/brainstorming/stale_leases/`.
  4. Write new lease metadata.

## 12. Security & Safety
- **Workspace Boundary**: State roots are validated using `os.path.abspath` to block directory traversal escapes.
- **Write Restrictions**: State files can only be created under directories configured by the active store path.

## 13. Complete Test Matrix
| Requirement ID | Test Type | Test File Target | Mapped Component | Verification Assertion |
| :--- | :--- | :--- | :--- | :--- |
| FR-01 | Unit Test | `skills/workflow-runtime/tests/test_locking_recovery.py` | `lease.py` | Verify lease JSON conforms to schema values |
| FR-02 | Integration Test | `skills/workflow-runtime/tests/test_locking_recovery.py` | `lease.py` | Mock expired timestamp and verify self-healing recovery |
| FR-04 | Unit Test | `skills/workflow-runtime/tests/test_state_store.py` | `state_store.py` | Verify `InMemoryStateStore` does not touch filesystem |
| NFR-01| Unit Test | `skills/workflow-runtime/tests/test_state_store.py` | `state_store.py` | Verify write collision triggers `RevisionConflictError` |
| NFR-02| Integration Test | `skills/workflow-runtime/tests/test_state_store.py` | `state_store.py` | Interrupt write loop and check JSON integrity |
| NFR-04| Integration Test | `tests/conftest.py` | `conftest.py` | Run parallel tests without polluting host repository |

## 14. Requirement Traceability Matrix
- `FR-01` -> Task 1.1 -> Class `WorkflowLease` -> `lease.py` -> `test_locking_recovery.py`
- `FR-02` -> Task 1.2 -> Class `WorkflowLease` -> `lease.py` -> `test_locking_recovery.py`
- `FR-04` -> Task 1.4 -> Class `StateStore` -> `state_store.py` -> `test_state_store.py`
- `NFR-01` -> Task 1.7 -> Class `StateStore` -> `state_store.py` -> `test_state_store.py`

## 15. File-Level Implementation Contracts
- **File**: `skills/workflow-runtime/scripts/lease.py`
  - **Purpose**: Defines `WorkflowLease` class.
  - **Owner**: Coder.
  - **Inputs / Outputs / Dependencies**: Standard Python libraries (`json`, `os`, `sys`, `time`, `subprocess`).
- **File**: `skills/workflow-runtime/scripts/state_store.py`
  - **Purpose**: Defines database `StateStore` hierarchy.
  - **Owner**: Coder.
  - **Inputs / Outputs / Dependencies**: Base python components.
- **File**: `tests/conftest.py`
  - **Purpose**: Pytest setup.
  - **Owner**: Reviewer.
