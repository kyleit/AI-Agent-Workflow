<!-- File path: docs/designs/FEAT-115_aiwf_desktop_runtime_control_center_blueprint.md -->

---
feature_id: FEAT-115
feature_name: AIWF Desktop Runtime Control Center
status: reviewed
stage: blueprint
created_at: 2026-07-12
updated_at: 2026-07-12
previous_artifact: ../plans/FEAT-115_aiwf_desktop_runtime_control_center_plan.md
next_artifact: [Implementation (Source Code)](../../)
---

# Technical Design Blueprint & Implementation Contract – AIWF Desktop Runtime Control Center

## 0. Baseline Context & References
- **Memory Baseline**: Based on [project-summary.md](file:///e:/AgentsProject/.agents/memory/project-summary.md) (ai-skill-framework, secondary languages include JS, HTML, CSS, SQLite as runtime storage). Confidence level is High.
- **RAG Query Summaries**: Queried "AIWF Desktop Control Center Wails Go Svelte" matching FEAT-112 (Resident Orchestrator Service) and FEAT-113 (Resident Runtime Manager) designs. Key finding: Wails desktop wraps Svelte webview using Go bindings.
- **Inspected Source Files**:
  - `skills/workflow-runtime/scripts/workflow_runtime.py` (L500-530): ensure_daemon_running, checking daemon status via state files.
  - `skills/workflow-runtime/scripts/context.py` (L235-260): sync_request_history writing telemetry metrics to SQLite.

## 1. File-by-File Analysis & Proposed Mutations
| File Path | Operation | Responsibility | Dependency | Impact & Risk |
| :--- | :--- | :--- | :--- | :--- |
| `desktop/main.go` | NEW | Set up Wails app window and configure Go bindings | Wails packages | Low. Initialization config only |
| `desktop/registry.go` | NEW | Parse and persist registered projects config | JSON config file | Medium. Config serialization lock |
| `desktop/supervisor.go` | NEW | Create a WebSocket connection pool to local daemon ports | Python WebSocket server | High. Network/socket drop logic |
| `desktop/lock_checker.go` | NEW | Perform file-lock validation using SQLite DB queries | `workflow.lock` file | High. Database lock contention |
| `desktop/executor.go` | NEW | Run subprocess CLI commands to spawn/stop python daemons | Host shell commands | Medium. Cross-platform path issues |
| `desktop/frontend/src/Dashboard.svelte` | NEW | Render list of projects and active resource monitors | Svelte components | Low. Pure UI visual layer |
| `desktop/frontend/src/components/DAGViewer.svelte` | NEW | Draw task graph states (nodes & edges) using responsive SVG | JSON graph payload | Medium. Rendering efficiency |
| `desktop/frontend/src/components/AgentMonitor.svelte` | NEW | Render active hierarchical subagents tree | Process states payload | Low. Component logic |
| `desktop/frontend/src/components/LogStreamer.svelte` | NEW | Buffer and filter live streamed log messages | Logs WS channel | Medium. Memory overflow risk |
| `desktop/frontend/src/components/ResourceGovernor.svelte` | NEW | Draw RAM and CPU consumption graphs over time | Telemetry payloads | Low. Charts rendering |
| `desktop/notifier.go` | NEW | Dispatch cross-platform notifications to target system OS | OS APIs | Low. OS integration |

## 2. Target Folder Structure
```text
.
├── desktop/
│   ├── main.go
│   ├── registry.go
│   ├── supervisor.go
│   ├── lock_checker.go
│   ├── executor.go
│   ├── notifier.go
│   ├── wails.json
│   └── frontend/
│       ├── package.json
│       ├── tailwind.config.js
│       └── src/
│           ├── main.js
│           ├── App.svelte
│           ├── Dashboard.svelte
│           └── components/
│               ├── DAGViewer.svelte
│               ├── AgentMonitor.svelte
│               ├── LogStreamer.svelte
│               └── ResourceGovernor.svelte
```

## 3. Complete Class & Module Design
- **Module Name**: `Registry`
  - **Responsibilities**: Manage project registration paths.
  - **Constructor Parameters**: None.
  - **Public Methods**:
    - `func (r *Registry) RegisterProject(path string) (Project, error)`
    - `func (r *Registry) GetProjects() ([]Project, error)`
    - `func (r *Registry) DeleteProject(id string) error`
  - **Internal Methods**:
    - `func (r *Registry) _loadConfig() (Config, error)`
    - `func (r *Registry) _saveConfig(c Config) error`
  - **Dependencies**: OS file system packages.
- **Module Name**: `Supervisor`
  - **Responsibilities**: Maintain live WebSocket connections to workspace servers.
  - **Constructor Parameters**: None.
  - **Public Methods**:
    - `func (s *Supervisor) ConnectProject(id string, port int) error`
    - `func (s *Supervisor) DisconnectProject(id string) error`
  - **Internal Methods**:
    - `func (s *Supervisor) _reconnectLoop(id string)`
  - **Dependencies**: `github.com/gorilla/websocket`.

## 4. Detailed Interface Contracts
- **API Signature**: `func (e *Executor) StartOrchestrator(projectPath string) (bool, error)`
  - **Parameters**: `projectPath` (Must be an absolute directory path on the local filesystem)
  - **Return Types**: `bool` (indicates launch success), `error` (returns failure reason if locks exist)
  - **Exceptions**: `ErrOrchestratorLocked` thrown when `workflow.lock` is active and lease is not expired.
  - **Validation Rules**: Validate directory contains `.agents/` folder and `workflow_runtime.py` is present.
  - **Compatibility Notes**: Maps directly to command line calls `python skills/workflow-runtime/scripts/workflow_runtime.py start`.

## 5. Configuration Schema
- **Current Schema**: None (New app initialization).
- **Target Schema** (`~/.config/aiwf/projects.json`):
  ```json
  {
    "projects": [
      {
        "id": "uuid-v4-string",
        "name": "Project K",
        "path": "E:/AgentsProject",
        "port": 8085
      }
    ]
  }
  ```
- **Migration Rules**: None required. Defaults to empty array if config is missing.

## 6. Database & Storage Design
- **Tables**: Reads existing tables from `.agents/project_runtime.db`:
  - `provider_requests`: Traces query metrics, duration, token usage.
  - `workflow_runs`: Logs session execution milestones.
- **Migration & Rollback Strategy**: The desktop app runs as read-only on the SQLite database, thus avoiding any SQL write schema migrations.

## 7. Cache Architecture
- **Cache Keys**: Registry project list cached in memory on Go backend.
- **Invalidation Rules**: Invalidated whenever `RegisterProject` or `DeleteProject` methods are triggered.
- **TTL**: Persistent cache matching desktop process life.

## 8. Error Model
- **Exception Class**: `ConnectionError`
  - **Trigger Condition**: WebSocket port disconnected unexpectedly.
  - **Recovery Strategy**: Start auto-reconnection attempts, rendering yellow warning status badge on UI.
  - **Retry Policy**: Re-try every 1.5 seconds, up to 10 attempts before failing back to disconnected status.
  - **Logging Requirements**: Logs details to Wails standard output stream.

## 9. Skill Integration Contracts
- **Skill Name**: `workflow-runtime`
  - **Before Hooks**: Invokes CLI validator status checks.
  - **After Hooks**: None.
  - **Runtime Calls**: Runs `python workflow_runtime.py` commands in dynamic sandbox modes.

## 10. CLI & Runtime Contracts
- **Command Syntax**: Wails executable runs shell command wrapper:
  ```powershell
  python skills/workflow-runtime/scripts/workflow_runtime.py start --skill <skill> --command <command>
  ```
  - **Exit Codes**: 0 (success), 1 (failed locks / execution error).

## 11. Sequence Flows
- **Normal Start Flow**:
  1. User clicks "Start Orchestrator" on Svelte UI.
  2. Svelte triggers Wails binding call `StartOrchestrator(path)`.
  3. Go backend checks DB lock via `lock_checker.go`.
  4. If unlocked, Go backend spawns `workflow_runtime.py` daemon subprocess.
  5. Go backend establishes WebSocket connection to the spawned telemetry port.
  6. Real-time updates flow back to Svelte UI event handler.

## 12. Security & Safety
- **Workspace Boundary**: Go backend registry validates target folders are within local partitions.
- **Path Validation**: Sanitize paths to prevent Directory Traversal attacks (escape strings containing `..` are rejected).
- **Write Restrictions**: The desktop client is forbidden from modifying any source code files under target workspaces.

## 13. Complete Test Matrix
| Requirement ID | Test Type | Test File Target | Mapped Component | Verification Assertion |
| :--- | :--- | :--- | :--- | :--- |
| `FR-01` | Unit Test | `desktop/registry_test.go` | `registry.go` | `assert.Equal(t, len(projects), 1)` |
| `FR-02` | Integration Test| `desktop/executor_test.go` | `executor.go` | `assert.ErrorIs(t, err, ErrOrchestratorLocked)` |
| `FR-05` | E2E UI Test | `desktop/frontend/src/tests/dag.test.js` | `DAGViewer.svelte` | Graph layout updates nodes colors on state changes |

## 14. Requirement Traceability Matrix
- `FR-01` -> Task 1.1 -> Class `Registry` -> `registry.go` -> `registry_test.go` -> Verified.
- `FR-02` -> Task 1.3 -> Class `LockChecker` -> `lock_checker.go` -> `executor_test.go` -> Verified.
- `FR-03` -> Task 1.4 -> Class `Executor` -> `executor.go` -> `executor_test.go` -> Verified.
- `FR-05` -> Task 1.5 -> Component `DAGViewer` -> `DAGViewer.svelte` -> E2E visual verified.

## 15. File-Level Implementation Contracts
- **File**: `desktop/registry.go`
  - **Purpose**: Persist user workspace directories configurations.
  - **Owner**: Coder.
  - **Inputs / Outputs / Dependencies**: Input path strings, outputs list of Project metadata structs.
- **File**: `desktop/supervisor.go`
  - **Purpose**: Handle socket telemetry connections to active workspace ports.
  - **Owner**: Architect.
  - **Implementation Notes**: Must run socket connection routines inside separate Goroutines to avoid freezing the Wails UI event loops.
- **File**: `desktop/lock_checker.go`
  - **Purpose**: Verify no active locks on the project before launching subprocesses.
  - **Owner**: Architect.
  - **Implementation Notes**: Check both the SQLite lease table state and the presence of physical file lock `workflow.lock`.
