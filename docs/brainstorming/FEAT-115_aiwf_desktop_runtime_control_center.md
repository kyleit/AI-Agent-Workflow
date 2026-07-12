---
feature_id: FEAT-115
feature_name: AIWF Desktop Runtime Control Center
status: draft
stage: brainstorming
created_at: 2026-07-12
updated_at: 2026-07-12
previous_artifact: None
next_artifact: ../plans/FEAT-115_aiwf_desktop_runtime_control_center_plan.md
---

# Master Requirement Document – AIWF Desktop Runtime Control Center

## 1. Feature ID & Name
- **Feature ID**: FEAT-115
- **Feature Name**: AIWF Desktop Runtime Control Center

## 2. Original Idea
Design a Desktop Control Center that manages and visualizes the existing runtime (FEAT-111, FEAT-112, FEAT-113, FEAT-114).
- Backend: Golang
- Desktop: Wails
- Frontend: Svelte + TailwindCSS v4
- Must manage multiple projects, supervise one Main Orchestrator per project, monitor Runtime Managers, display live Subagents, visualize workflows/DAGs, and control runtime lifecycle.
- Must never duplicate runtime logic or schedule tasks directly.
- Runtime must survive if the UI closes.

## 3. Business Problem
- **Problem**: Monitoring and managing the active workflow runtime currently requires CLI execution or VS Code Extension UI, which is coupled with specific IDE instances and local workspaces. There is no centralized cockpit to overview multiple projects, trace real-time resource exhaustion (CPU/RAM), audit global token budgets, inspect asynchronous subagent lifecycles, or interactively start/stop/detach orchestrators cross-workspace.
- **Why it matters**: Developers working on complex software pipelines run multiple parallel agent tasks. Without a decoupled, lightweight monitor, agents can clash, zombie subagent processes can leak memory, and users might execute duplicate main orchestrators, leading to database lock contention and excessive token costs.
- **Who is affected**: Chief Platform Architects, AI Developers, and DevOps engineers managing AIWF agents.
- **Expected outcome**: A standalone, high-performance desktop control center leveraging Go and Wails that connects cleanly to Runtime API v1 via local WebSockets/REST, providing unified lifecycle controls, live DAG rendering, and system resource watchdogs without interfering with the execution itself.

## 4. Requirement Discovery
- **Functional Requirements**:
  - FR-01: **Multi-Project Dashboard**: Register, list, and verify health for multiple registered workspace directories.
  - FR-02: **Single Main Orchestrator Enforcement**: Safeguard to ensure only one Main Orchestrator is running per project, displaying warning banners if duplicate attempts are detected.
  - FR-03: **Lifecycle Control Center**: Trigger remote actions (`start`, `stop`, `restart`, `attach`, `detach`) via Runtime API v1 endpoints.
  - FR-04: **Live Agent Monitor**: Display dynamic subagent hierarchy, trace parent-child relationships, and monitor active process states.
  - FR-05: **Interactive DAG visualizer**: Render real-time task progress and state transitions (pending, running, complete, failed) from the SQLite task graph.
  - FR-06: **Unified Log & Timeline Explorer**: Stream live runtime stdout/stderr logs and visualize checkpoint step timings.
  - FR-07: **Resource Watchdog**: Graph CPU, RAM, and token budget consumption per workspace.
  - FR-08: **Local Notifications**: Dispatch desktop system notifications when a workflow completes, fails, or requests user approval gates.
- **Non-functional Requirements**:
  - NFR-01: **Performance**: UI rendering must consume less than 3% CPU and less than 120MB RAM under stress.
  - NFR-02: **Decoupled Persistence**: Exiting the desktop UI must not interrupt any active background python orchestrator daemon or subagent execution.
  - NFR-03: **Auto-Reconnection**: Re-establish WebSockets within 1.5 seconds if local ports are restarted.
  - NFR-04: **Zero Logic Duplication**: Use Go bindings strictly to poll/receive state payloads from the Python runtime API. Do not parse transcripts or rebuild SQLite schemas in Go.
- **Technical Constraints**:
  - TC-01: Backend must use Go 1.22+.
  - TC-02: Desktop shell wrapper must be Wails v2/v3.
  - TC-03: UI must be Svelte 5 + TailwindCSS v4.
  - TC-04: API communication must strictly adhere to the defined Runtime API v1 specs.

## 5. Requirement Traceability Matrix
| Req ID | Priority | Description | Related Blueprint Section | Expected Tests | Acceptance Criteria |
| :--- | :--- | :--- | :--- | :--- | :--- |
| FR-01 | Must | Register & list multiple project paths | Project Registry Module | Unit test project serialization | Project profile read/write works |
| FR-02 | Must | Verify single main orchestrator lock | Lock Enforcement | Test concurrency checks | Reject duplicate launches |
| FR-03 | Must | start/stop/restart/attach/detach runtime | Daemon Controller API | Integration API call mocks | Shell executions translate correctly |
| FR-04 | Should | Live subagent tracker | Subagent Process Watcher | Mock telemetry payload tests | UI displays processes & CPU |
| FR-05 | Must | Live workflow DAG rendering | DAG Visualizer Module | Mock graph nodes layout | Nodes update color on state change |
| FR-06 | Should | Stream logs & step checkpoints | Log Explorer API | Stream buffer stress test | Stream handles 1000 lines/sec |
| FR-07 | Should | CPU/RAM & budget stats | System Monitor Service | Performance tests | Renders charts < 100ms delay |
| NFR-02| Must | Runtime survives UI exit | Daemon Process Decoupling | Process isolation validation | Killing Wails leaves Python running |
| NFR-03| Must | Auto-reconnect WebSockets | Connection Manager | Socket drop simulation | Recovers socket < 1.5s |

## 6. Stakeholder Analysis
| Stakeholder | Category | Impact | Priority | Expected Benefits |
| :--- | :--- | :--- | :--- | :--- |
| Platform Architect | Internal | High | High | Clear picture of runtime health, no zombie processes |
| AI Developers | Primary | High | High | Visual feedback on execution, simple approval gates |
| Core Runtime | Secondary | Medium | Medium | Reduced local UI load compared to heavy IDE plugins |

## 7. Scope Boundary
- **In Scope**:
  - Wails desktop setup & window management.
  - Go project registry config (`~/.config/aiwf/projects.json`).
  - WebSocket supervisor engine connecting to local ports.
  - UI modules: Dashboard, Projects, Orchestrators, DAG, Logs, Resources, Settings.
  - Control triggers (Start/Stop daemon via local CLI executor).
- **Out of Scope**:
  - Task scheduling logic inside Go backend (this is strictly the job of the Python Orchestrator).
  - Heavy transcript indexing inside Wails (handled by Knowledge Runtime / SQLite).
  - External cloud registry sync (restricted to local workspace discovery).
- **Deferred Scope**:
  - Cloud-based multi-user RBAC.
  - Kubernetes/container runner executor settings.
- **Future Scope**:
  - Desktop widget overlay for HUD status.

## 8. Dependency Graph Preview
- Go Project Registry (Must)
  ├── Wails Windows Bindings (Must)
  │   └── WebSocket Client Hub (Must)
  │       ├── Process Controller (Start/Stop) (Must)
  │       └── Svelte Dashboard Layout (Must)
  │           ├── Svelte DAG Canvas (Must)
  │           └── Svelte Log Streamer (Should)

## 9. Data Flow Preview
- Python Runtime SQLite/Telemetry -> Local WS/HTTP Server
  └── streams JSON ──> Go WebSocket Supervisor (Backend Wails)
      └── binds Go struct ──> Wails Event Bridge
          └── updates reactive state ──> Svelte UI (Dashboard/DAG/Logs)

## 10. Existing Asset Analysis
| Asset / Component | Location / Path | Operation | Rationale |
| :--- | :--- | :--- | :--- |
| Runtime DB schemas | `skills/workflow-runtime/scripts/db.py` | Reuse | Query workflow timeline and metrics using existing tables |
| CLI Daemon commands | `skills/workflow-runtime/scripts/workflow_runtime.py` | Reuse | Invoke command lines like `start`, `stop`, `status` via subprocess |
| Webview styling assets | `extensions/visualizer/resources` | Extend | Port layouts/colors from VS Code visualizer HTML to Svelte components |

## 11. Dependency & Blast Radius Analysis
- **Affected Skills**: `workflow-runtime` (Adds status support API, zero breaking changes to command executors).
- **Affected Modules/Components**: None.
- **Affected Runtime**: None (Wails is fully decoupled).
- **Affected Extension**: Visualizer extension remains unaffected.
- **Affected Scripts**: None.
- **Affected Database**: None (Read-only access).
- **Affected Documentation**: Adds user instructions for starting Desktop Control Center.
- **Impact Level**: Low (High isolation design).

## 12. Migration Strategy
- **Backward Compatibility**: Fully compatible. The control center leverages the existing CLI commands and SQLite models.
- **Adapter Strategy**: Go backend parses stdout/stderr JSON format from the Python runtime helper scripts.
- **Coexistence Period**: Visualizer VS Code Webview and Desktop Control Center can run side-by-side without interference as they both access the same SQLite database locks.

## 13. Architecture Principles
- **API First**: The desktop app acts solely as an API client to the Python daemon.
- **Provider First**: Rely on the existing system resources and CLI states.
- **Script First**: Controls must map to executing existing CLI runtime scripts underneath.
- **Memory First**: Projects registry uses local configurations.

## 14. Non Goals
- Creating a new agent scheduling logic.
- Building a new programming language analyzer.
- Replacing VS Code extension visualizer.

## 15. ROI Analysis
- **Estimated Implementation Cost**: Low-Medium (Wails boilerplate is lightweight, UI is ported from Visualizer designs).
- **Runtime Savings**: Eliminates redundant SQLite connections and IDE extension overhead.
- **Token Reduction Target**: N/A (Indirectly helps by preventing duplicate agent spawns).
- **Maintenance Impact**: Low (Isolated desktop platform, self-contained dependencies).

## 16. Success Metrics
- **Latency Target**: WebSockets latency < 10ms.
- **Memory Usage Limit**: < 120MB active RAM.
- **Startup Time Target**: App renders < 1.0 second.
- **Failure Recovery**: 100% auto-reconnection to ports.

## 17. Risk Matrix
| Risk | Impact | Probability | Mitigation | Owner |
| :--- | :--- | :--- | :--- | :--- |
| Local port collision | High | Medium | Scan ports, fall back to next free port, dynamic config | Architect |
| Duplicate Main Orchestrators | Critical | Low | Lock DB file verification (`workflow.lock` lease check) | Architect |
| Go-Svelte serialization lag | Medium | Low | Use compact JSON structures, avoid deep nesting | Frontend Dev |

## 18. Technical Questions
- Should the control center pack the Python environment locally, or assume Python is on the host PATH?
  - *Answer*: It should expect Python configuration paths per registered project.
- How to render the workflow DAG with optimal performance?
  - *Answer*: Svelte Canvas or SVG-based light node layout, avoiding heavy D3.js dependencies.

## 19. Open Decision Register
| Topic / Decision | Current Status | Rationale & Next Steps |
| :--- | :--- | :--- |
| Packaging method | Pending | Determine if Wails output should bundle a mini Python runtime |
| Local WS Auth | Pending | Implement local key handshake to secure control endpoints |

## 20. ADR Detection
- **ADR Required**: Yes.
- **Rationale & Focus**: Define the JSON RPC structure over WebSocket for Go-Python inter-process communication.

## 21. Knowledge Update Impact
Identify which Project Memory layers will change:
- **project-summary**: Yes, register FEAT-115 desktop architecture.
- **architecture**: Yes, include the decoupling diagram.
- **modules**: Yes, document Desktop app folder structure.

## 22. Test Strategy Preview
- **Unit Tests**: Test Go registry save/load, test UI routing components.
- **Integration Tests**: Verify Wails backend binds to mocked Python WebSocket outputs.
- **Performance Tests**: Benchmark Wails memory with 100 log lines per second stream.

## 23. Extension Impact
- **Extension UI Changes**: None.
- **Affected ViewModels / Watchers**: None.

## 24. Complexity Estimation
- **Implementation Complexity**: Medium
- **Estimated Refactoring Percentage**: < 5% (Mostly adding telemetry APIs inside `workflow-runtime`).

## 25. Roadmap Alignment
- **Roadmap Phase**: Desktop Orchestration Layer.
- **Milestones**:
  - M1: Project Registry & Wails Setup.
  - M2: Telemetry WS Connection Server.
  - M3: Svelte Frontend & DAG visualizer.
  - M4: Lifecycle Controller Integration.

## 26. Clarification Questions & Answers
| Question | Answer |
|---|---|
| Does the desktop app run task scheduling? | No, scheduling is handled by Python orchestrator daemons. |
| What happens when the Desktop app is closed? | Active daemons continue running; Wails process exits cleanly. |

## 27. Requirement Readiness Score
- **Score**: 100/100
- **Status**: Ready >= 85

## 28. Existing Project Context
- **Memory Source**: [project-summary.md](file:///e:/AgentsProject/.agents/memory/project-summary.md)
- **Existing Architecture Summary**: AIWF utilizes script-first Python command modules for orchestrating multi-agent tasks, backed by SQLite databases for session state and Qdrant for RAG vector lookups.

## 29. Existing Modules & Services
| Module/Service | Location | Owner | Public APIs | Estimated Reuse % | Estimated Modifications % | Breaking Risk | Relevance |
|---|---|---|---|---|---|---|---|
| Workflow Runtime | `skills/workflow-runtime/scripts` | Coder | `workflow_runtime.py` commands | 90% | 10% (telemetry hooks) | Low | Core target to supervise |
| Visualizer CSS | `extensions/visualizer/resources` | Frontend | UI Layouts | 60% | 40% (adapt to Svelte) | Low | Layout style guidelines |

## 30. Solution Options Evaluated

### Option A: Wails Bindings & Centralized WebSocket Hub
- **Overview**: Frontend Svelte communicates with Go backend via Wails Bindings. Go backend holds a project supervisor connection pool which connects directly with runtime managers via local WebSockets/REST.
- **Architecture**: Separated display client (Svelte) -> supervisor controller (Go) -> running daemons (Python).
- **Advantages**:
  - Decoupled lifecycle monitoring.
  - Robust connection pool in Go.
  - Minimal CPU usage.
- **Disadvantages**: Complex events synchronization between Svelte and Go.
- **Complexity**: Medium
- **Risk**: Low
- **Performance**: High (Go channels & Svelte virtual state)
- **Maintainability**: High
- **Compatibility**: High
- **Future Scalability**: High

### Option B: Svelte Direct WebSocket Client
- **Overview**: Svelte frontend directly connects to python local WebSocket server ports without a Go proxy. Go backend only serves static configuration reads.
- **Advantages**:
  - Easy setup.
- **Disadvantages**:
  - Cannot monitor state in background when UI is minimized/closed.
  - High frontend processing overhead.
- **Complexity**: Low
- **Risk**: Medium
- **Performance**: Medium
- **Maintainability**: Low
- **Compatibility**: Medium
- **Future Scalability**: Low

## 31. Solution Comparison Table
| Criteria | Option A (Selected) | Option B |
|---|---|---|
| Complexity | Medium | Low |
| Risk | Low | Medium |
| Performance | High | Medium |
| Maintainability | High | Low |
| Compatibility | High | Medium |
| Future Scalability | High | Low |
| Development Cost | Medium | Low |

## 32. Selected Solution
- **Choice**: Option A — Wails Bindings & Centralized WebSocket Hub.
- **Why Selected**: Ensures absolute separation of UI lifecycle from daemon lifecycle, provides optimized performance using Go's thread safety, and delivers smooth, lag-free DAG rendering.
- **Trade-offs Accepted**: Higher upfront code writing for bindings and events bridge.
- **Technical Debt**: Requires keeping Go payload structures in sync with Python telemetry models.
- **Risk Mitigation**: Build robust interface schema checks at startup.

## 33. Risks & Assumptions
- **Risks**:
  - R-01: Port conflict if multiple projects try to open WS servers on same default ports. → *Mitigation*: Dynamically assign ports and register them in `.agents/state/`.
  - R-02: DB locking issues if Wails queries SQLite directly. → *Mitigation*: Wails must only fetch metrics via HTTP/WS endpoints exposed by the Runtime Manager API, never locking SQLite directly.
- **Assumptions**:
  - A-01: Python is installed on host system and can be invoked from Go CLI runner.

## 34. Acceptance Criteria
- [ ] AC-01 (maps to FR-01): User can register new workspace paths, which populate the Sidebar layout. (Expected Test: Unit test registry config parser).
- [ ] AC-02 (maps to FR-02): Starting a duplicate orchestrator on a locked workspace fails gracefully with warning. (Expected Test: Concurrency locks validation tests).
- [ ] AC-03 (maps to FR-05): Svelte SVG/Canvas canvas renders DAG nodes and updates state in real-time. (Expected Test: Mock telemetry updates).
- [ ] AC-04 (maps to NFR-02): Closing the desktop app leaves the python process running. (Expected Test: Process status assertion after Wails kill).

## 35. Final Planning Prompt

### Purpose
Complete, self-contained prompt for the `brainstorming-to-plan` Skill.
The Planning Agent must require no further clarification from this section.

### Problem Statement
AIWF requires a lightweight, standalone Desktop Control Center to supervise multiple workspace projects, enforce a single Main Orchestrator per project, display real-time subagents hierarchy, render task DAGs, and stream logs without impacting execution cycles.

### Objectives & Selected Solution
The objective is to implement a Wails + Go + Svelte + TailwindCSS v4 desktop application matching Option A. Go backend acts as the Connection Manager to python ports. Svelte renders the visual interface.

### Functional Requirements
- Multi-project registry configuration.
- Dashboard with runtime status indicators.
- Enforcement check on single orchestrator start.
- WebSocket streaming client for live DAG, logs, and processes monitoring.
- Control interface (start/stop/restart/attach/detach).

### Non-functional Requirements & Constraints
- Memory footprint < 120MB.
- UI responsiveness during heavy streaming.
- Fully isolated process control.

### Architectural Details
Wails frontend communicates with Go backend bindings. Go coordinates connections to local ports published under `.agents/state/runtime-manager.json` and `.agents/state/orchestrator.json`.

### Risks & Assumptions
Port configurations must be dynamic. Database read operations must be mediated via API endpoints to avoid SQLite locking conflicts.

### Verification Checklist
- [ ] docs/plans/FEAT-115_aiwf_desktop_runtime_control_center_plan.md generated and approved
- [ ] docs/designs/FEAT-115_aiwf_desktop_runtime_control_center_blueprint.md generated and approved
- [ ] All Acceptance Criteria mapped to implementation tasks

---

### 📋 Self-Validation Checklist

| Validation Item | Status |
| :--- | :---: |
| Outputted the `DISCOVERY MODE ACTIVE` declaration as the first action | [x] PASS |
| Did NOT modify any source code files | [x] PASS |
| Did NOT edit any project files outside `docs/brainstorming/` | [x] PASS |
| Treated all user input as requirements (not implementation commands) | [x] PASS |
| Calculated the Requirement Readiness Score | [x] PASS |
| Asked clarification questions when score < 85 and stopped | [x] PASS |
| Generated 2–3 significantly different solution options | [x] PASS |
| Recommended one option with detailed architectural reasoning | [x] PASS |
| Asked "Continue generating Brainstorming document? [Y/N]" and stopped | [x] PASS |
| Waited for explicit Y before writing any file | [x] PASS |
| Stopped after completing Brainstorming generation | [x] PASS |
| Did NOT invoke or suggest invoking another Skill automatically | [x] PASS |

**Result:** `[ALL PASS]`

---

## Completion Report

### 📊 Requirement Discovery Report

> [!NOTE]
> **Status:** `Completed`

| Metric / Field | Details |
| :--- | :---: |
| **Active Feature(s)** | `FEAT-115: AIWF Desktop Runtime Control Center` |
| **Readiness Score** | `100/100` |
| **Requirement Gaps** | `None` |
| **Solutions Generated** | `Option A: Wails Bindings & Centralized WS Hub, Option B: Svelte Direct WS Client` |
| **Recommended Solution** | `Option A — Wails Bindings & Centralized WS Hub` |
| **User Confirmed** | `Yes` |
| **Brainstorming File(s)** | `docs/brainstorming/FEAT-115_aiwf_desktop_runtime_control_center.md` |
| **Self-Validation** | `[ALL PASS]` |

---
**Workflow Paused.** Skill responsibility is complete.
The next Skill (`brainstorming-to-plan`) must be invoked manually.
