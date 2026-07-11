<!-- File path: docs/designs/FEAT-070_vir_target_lifecycle_and_sandbox_orchestrator_blueprint.md -->

---
feature_id: FEAT-070
feature_name: Visual Intelligence Runtime — Target Lifecycle & Sandbox Orchestrator
status: reviewed
stage: blueprint
created_at: 2026-07-12
updated_at: 2026-07-12
previous_artifact: ../plans/FEAT-070_vir_target_lifecycle_and_sandbox_orchestrator_plan.md
next_artifact: [Implementation (Source Code)](../../)
---

# Technical Design Blueprint & Implementation Contract – Target Lifecycle & Sandbox Orchestrator

## 0. Baseline Context & References
- **Memory Baseline**: Memory of process structures on Windows OS environments.
- **RAG Query Summaries**: Port binding requirements and process group sweeps patterns for subprocess cleanups.
- **Inspected Source Files**:
  - [FEAT-070 Plan](file:///e:/AgentsProject/docs/plans/FEAT-070_vir_target_lifecycle_and_sandbox_orchestrator_plan.md)

---

## 1. File-by-File Analysis & Proposed Mutations

| File Path | Operation | Responsibility | Dependency | Impact & Risk |
| :--- | :--- | :--- | :--- | :--- |
| `vir_runtime/sandbox/orchestrator.py` | Create | Manage the lifetime states of the application under test | None | High. Orchestrates target runs. |
| `vir_runtime/sandbox/ports.py` | Create | Detect available localhost port numbers dynamically | None | Low. Allocates port numbers. |
| `vir_runtime/sandbox/process.py` | Create | Clean up subprocesses and process groups safely (Windows compatible) | None | High. Prevents process leaks. |

---

## 2. Target Folder Structure
```text
vir_runtime/
└── sandbox/
    ├── orchestrator.py
    ├── ports.py
    └── process.py
```

---

## 3. Complete Class & Module Design

### 3.1 SandboxOrchestrator
- **Class / Module Name**: `vir_runtime.sandbox.orchestrator.SandboxOrchestrator`
  - **Responsibilities**: Prepare environments, run build scripts, launch target ports, seed mock database data, and cleanup target processes.
  - **Constructor Parameters**:
    - `workspace_dir: str`
    - `start_cmd: str`
  - **Public Methods**:
    - `async def launch_target() -> int` - Returns allocated port number.
    - `async def shutdown_target() -> None` - Cleans up target execution tree.
  - **Internal Methods**:
    - `async def _run_build() -> None`
    - `async def _seed_data() -> None`
  - **Dependencies**: `vir_runtime.sandbox.ports`, `vir_runtime.sandbox.process`

### 3.2 PortManager
- **Class / Module Name**: `vir_runtime.sandbox.ports.PortManager`
  - **Responsibilities**: Find open ports in the range `[3000-9000]` using local socket binds.
  - **Public Methods**:
    - `def find_available_port() -> int`
    - `def is_port_in_use(port: int) -> bool`

### 3.3 WindowsProcessManager
- **Class / Module Name**: `vir_runtime.sandbox.process.WindowsProcessManager`
  - **Responsibilities**: Traverses subprocess trees using parent IDs and forces termination using Windows system call commands.
  - **Public Methods**:
    - `def terminate_process_tree(pid: int) -> None`

---

## 4. Detailed Interface Contracts

- **API Signature**: `async def launch_target() -> int`
  - **Parameters**: None.
  - **Return Types**: `int` (The dynamic port number the target is listening on).
  - **Exceptions**:
    - `BuildFailedError` - If the build script fails.
    - `PortAllocationError` - If no open port is found in range.
    - `TargetStartupTimeoutError` - If the application fails to bind within 30 seconds.

---

## 5. Configuration Schema

- **Target Schema**:
```yaml
sandbox:
  build_command: "npm run build"
  start_command: "npm run dev"
  port_range: [5000, 6000]
  startup_timeout_seconds: 30
```

---

## 6. Database & Storage Design
- The sandbox stores no session records in SQLite. State structures reside in orchestrator memory properties.

---

## 7. Cache Architecture
- No cache allocated.

---

## 8. Error Model

- **Exception Class**: `TargetStartupTimeoutError`
  - **Trigger Condition**: Application started, but HTTP request probes return errors after 30 seconds.
  - **Recovery Strategy**: Force kill the allocated process trees, release ports, and raise a startup fault.
  - **Logging Requirements**: ERROR log referencing the exit code of the failed startup process.

---

## 9. Skill Integration Contracts
- None.

---

## 10. CLI & Runtime Contracts
- None.

---

## 11. Sequence Flows

- **Startup and Isolation Flow**:
  1. `SandboxOrchestrator` triggers `PortManager.find_available_port()`.
  2. Subprocess triggers `npm run build`.
  3. Orchestrator fires `npm run dev` binding to target port.
  4. Probe loop queries url.
  5. Session ends, triggers `WindowsProcessManager.terminate_process_tree(pid)`.

---

## 12. Security & Safety
- **Process Isolation**: Launched subprocesses inherit a clean, minimal environment dict containing only authorized path environment variables to prevent local secrets leak.

---

## 13. Complete Test Matrix

| Requirement ID | Test Type | Test File Target | Mapped Component | Verification Assertion |
| :--- | :--- | :--- | :--- | :--- |
| `FR-01` | Unit Test | `tests/unit/test_port_allocation.py` | `ports.py` | `self.assertFalse(is_port_in_use(port))` |
| `FR-04` | Integration Test | `tests/integration/test_process_cleanups.py` | `process.py` | `self.assertFalse(psutil.pid_exists(child_pid))` |

---

## 14. Requirement Traceability Matrix
- `FR-01` -> Task 1.1 -> Class `PortManager` -> `ports.py` -> `test_port_allocation.py` -> Verified.
- `FR-04` -> Task 1.4 -> Class `WindowsProcessManager` -> `process.py` -> `test_process_cleanups.py` -> Verified.

---

## 15. File-Level Implementation Contracts
- **File**: `vir_runtime/sandbox/process.py`
  - **Purpose**: Process-group cleanups helper routines.
  - **Owner**: Coder
  - **Inputs / Outputs / Dependencies**: Depends on `psutil` libraries.
