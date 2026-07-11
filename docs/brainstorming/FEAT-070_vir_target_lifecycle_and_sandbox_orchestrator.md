<!-- docs/brainstorming/FEAT-070_vir_target_lifecycle_and_sandbox_orchestrator.md -->

---
feature_id: FEAT-070
feature_name: Visual Intelligence Runtime — Target Lifecycle & Sandbox Orchestrator
status: draft
stage: brainstorming
created_at: 2026-07-12
updated_at: 2026-07-12
previous_artifact: FEAT-069_vir_sdlc_integration_and_future_ai_capabilities.md
next_artifact: ../plans/FEAT-070_vir_sandbox_orchestrator_plan.md
---

# Master Requirement Document – VIR Target Lifecycle & Sandbox Orchestrator

## 1. Feature ID & Name
- **Feature ID**: FEAT-070
- **Feature Name**: Visual Intelligence Runtime — Target Lifecycle & Sandbox Orchestrator

## 2. Original Idea
Design the target application execution control service (Sandbox Orchestrator) for VIR. It manages preparing, starting, observing, resetting, seeding, isolating, and shutting down the application under test (and its dependency backend mocks, databases) in a sandbox environment, ensuring stable execution and preventing resource leaks.

## 3. Business Problem
- **Problem**: When multiple AI agents make code changes or run tests in parallel, the target environment frequently degrades. Unmanaged processes lead to port collisions, dirty database states, build compile failures, and zombie processes.
- **Why it matters**: A robust execution framework requires a reliable sandbox. Without explicit lifecycle orchestration, verification tasks will fail due to stale ports, dirty databases, or unhandled build errors.
- **Who is affected**: All VIR sensory engines, Coder Agent, CI/CD runners, and developers running the Visualizer extension.
- **Expected outcome**: An automated Sandbox Orchestrator that provisions, runs, health-checks, isolates, and terminates the application under test with zero resource leaks.

## 4. Requirement Discovery

### Functional Requirements
- **FR-01: Target Application Discovery & Detection:** Auto-detect the project target platform (Node.js, Python, Go, Docker Compose, or custom commands) using project metadata.
- **FR-02: Command Detection & Environment Preparation:** Locate start, build, test, and database seed scripts from package definitions. Prepare runtime environment variables dynamically (e.g. `PORT`, `NODE_ENV=test`, `DATABASE_URL`, security hashes).
- **FR-03: Dynamic Port Allocation:** Scan and allocate unused ports for both the target application and any mock APIs. Avoid collisions with existing services running on the machine.
- **FR-04: Process Ownership & Tree Tracking:** Maintain process ownership. Trace child processes, spawned subprocesses, and database instances to prevent orphan/zombie processes.
- **FR-05: Health Checks & Readiness Probes:** Query configured HTTP health endpoints or check TCP sockets using exponential backoff until the target is ready to receive requests.
- **FR-06: Graceful & Forced Termination:** Shutdown processes gracefully (SIGTERM, SIGINT). If they fail to shut down within a timeout (default 3s), apply a forced termination fallback (SIGKILL).
- **FR-07: Sandbox Isolation & Directory Management:** Create isolated, temporary workspaces for compilation artifacts, log capture, and temporary SQLite databases.
- **FR-08: Test-User and Test-Data Seeding:** Run database migrations and seed script files before observation. Reset database state to pristine baselines between runs.
- **FR-09: Browser-Session Lifecycle Integration:** Link browser startup and teardown to target application readiness. Pause browser actions if the backend crashes.
- **FR-10: Crash Detection & Auto-Recovery:** Monitor the target's exit status in real-time. If it crashes mid-observation, capture output, publish `sandbox.crashed`, and attempt a configurable restart-recovery loop.
- **FR-11: Platform-Agnostic Adapters:** Define interface abstractions so that the sandbox manager can control: web applications, desktop applications, mobile applications, CLI tools, containers, remote host environments, and Kubernetes workloads.
- **FR-12: Destructive-Action Protection:** Enforce policies preventing execution of destructive commands (like `rm -rf /` or unapproved database wipes on staging).
- **FR-13: Execution Differences (CLI / IDE / CI / Daemon):**
  - **CI:** Non-interactive, fails fast on build errors, redirects logs to standard files.
  - **IDE/Visualizer:** Sends live process health stream, permits manual reset trigger.
  - **CLI:** Human-readable colorized process log summary.
  - **Daemon:** Spawns persistent detached server instances, handles periodic health checks.

### Non-functional Requirements
- **NFR-01: Graceful Termination Speed:** Terminate 100% of child processes in under 3 seconds.
- **NFR-02: Port Scanning Latency:** Detect free ports in under 100ms.
- **NFR-03: Startup Timeout:** Allow configurable timeouts, defaulting to 30 seconds for local builds.
- **NFR-04: Isolation Safety:** No sandbox process may access or modify paths outside the designated workspace directories without approved security boundaries.

### Technical Constraints
- **TC-01:** Core process tracking implemented using Python's `asyncio.subprocess` and cross-platform process managers (e.g. `psutil` integration).
- **TC-02:** Database reset uses SQLite file copying where possible for near-instant rollback.
- **TC-03:** Configuration resides in `.agents/visual-runtime/config/sandbox.yaml` with project overrides in local workspace.

## 5. Requirement Traceability Matrix

| Req ID | Priority | Description | Related Blueprint | Expected Tests | Acceptance Criteria |
| :--- | :--- | :--- | :--- | :--- | :--- |
| FR-01 | Must | Target discovery | BP-VIR-018 | Verify command parsing | Parses Node/Python run commands correctly |
| FR-03 | Must | Port allocation | BP-VIR-018 | Bind port 8000; query port | Returns free port, avoiding 8000 |
| FR-04 | Must | Process tree tracking | BP-VIR-018 | Spawn server with nested children | Kills all nested PIDs on shutdown |
| FR-05 | Must | Health check poller | BP-VIR-018 | Poll delayed-start server | Resolves `ready` when server returns 200 |
| FR-06 | Must | Forced termination | BP-VIR-018 | Attempt shutdown of uncooperative subprocess | Process killed via SIGKILL fallback |
| FR-08 | Must | Database seeding | BP-VIR-018 | Trigger seed script | DB state refreshed to baseline |
| FR-11 | Must | Platform-agnostic adapters | BP-VIR-018 | Swap Web target with CLI stub | CLI sandbox lifecycle executes |
| FR-12 | Must | Destructive protection | BP-VIR-018 | Pass `rm -rf` inside start script | Parser blocks execution; logs safety error |

## 6. Stakeholder Analysis

| Stakeholder | Category | Impact | Priority | Expected Benefits |
| :--- | :--- | :--- | :--- | :--- |
| Sensory Agents | Internal | High | Critical | Access to a reliable, clean application server |
| Coder Agent | Primary | High | High | Auto-heals builds when sandbox reports compilation errors |
| CI Runner | External | High | High | Clean pipelines with no lingering background tasks |
| Release Manager Agent | Secondary | Medium | Medium | Confirms test application environment is healthy before gating |

## 7. Scope Boundary

### In Scope
- Subprocess monitoring, environment variable preparation, port manager.
- Process group termination, health checking, database seeding, temporary workspace isolation.
- Platform-agnostic interface definitions.

### Out of Scope
- Code compiler engine implementation.
- Production hosting deployment (e.g. Docker Hub push).

### Deferred Scope
- Kubernetes pod lifecycle manager (Phase 11+).

## 8. Dependency Graph Preview
- FEAT-070: Sandbox Orchestrator
  - FEAT-056: Event Bus (prerequisite — events like `sandbox.ready`)
  - FEAT-057: Adapter contracts (prerequisite)
  - FEAT-060: Digital Twin (consumes performance/lifecycle indicators)
  - FEAT-062: Thinking Pipeline (uses sandbox status to verify fixes)

## 9. Data Flow Preview
- Orchestrator requests target start
  └── Sandbox Orchestrator parses environment setup
      └── Allocates next free port (e.g. 5173)
          └── Spawns subprocess tree for application
              └── Poller checks `/health` endpoint
                  └── Connection successful -> publishes `sandbox.ready` event
                      └── Sensory observations commence on port 5173

## 10. Existing Asset Analysis
- Reuses base process wrapping checks from `workflow_runtime.py`.
- Integrates stack detection using `project-profile.json` configuration structures.

## 11-13. Implementation Details
- **Affected Skills**: `implementation-to-debug`, `implementation-to-release`.
- **API Interfaces**: `SandboxAdapter(Protocol)` exposing async methods.
- **Security Boundaries**: Paths strictly normalized; validation rejects dangerous command patterns.

## 14-16. Metrics & Business Value
- **Token reduction**: Reduces repetitive codebase searches for ports or start triggers.
- **Accuracy**: Eliminates transient E2E run failures.

## 17. Risk Matrix
- *Risk:* Zombie subprocesses lock ports. *Mitigation:* Explicit process tree traversal with `psutil` on shutdown.
- *Risk:* Build times take too long. *Mitigation:* Support configurable caching and separate compilation timeouts.

## 34. Acceptance Criteria
- [ ] AC-01: Auto-detects project stack and starts target on allocated port.
- [ ] AC-02: Terminates process tree inside sandbox within 3s on shutdown request.
- [ ] AC-03: Resolves ready state using exponential health-checking probe.
- [ ] AC-04: Rejects dangerous start commands violating safety rules.

## 35. Final Planning Prompt
Provide design blueprints for the `SandboxController` class, process tracker, port manager, and dynamic environment variable injector.
