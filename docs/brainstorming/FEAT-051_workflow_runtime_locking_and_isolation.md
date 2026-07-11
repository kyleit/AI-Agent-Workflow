---
feature_id: FEAT-051
feature_name: Fix Workflow Runtime State Locking, Concurrency, and Test Isolation
status: draft
stage: brainstorming
created_at: 2026-07-11
updated_at: 2026-07-11
previous_artifact: None
next_artifact: ../plans/FEAT-051_workflow_runtime_locking_and_isolation_plan.md
---

# Master Requirement Document – Fix Workflow Runtime State Locking, Concurrency, and Test Isolation

## 1. Feature ID & Name
- **Feature ID**: FEAT-051
- **Feature Name**: Fix Workflow Runtime State Locking, Concurrency, and Test Isolation

## 2. Original Idea
- Fix Workflow Runtime State Locking, Concurrency, and Test Isolation.

## 3. Business Problem
- **Problem**: The workflow runtime current state manager relies on an exclusive file lock (`workflow.lock`) that blocks subsequent runs on crash/kill, suffers from concurrent write race conditions, and pollutes the host repository state during parallel unit testing.
- **Why it matters**: Deadlocks force developers to manually delete lock files; state files can get corrupted; test runs cannot be executed in parallel reliably (`pytest -n auto` fails).
- **Who is affected**: Developer agents and testing workflows within the AI Skill Framework.
- **Expected outcome**: Seamless, crash-resilient lease-based workflow lock, atomic state writes, optimistic concurrency control (CAS), and 100% test isolation.

## 4. Requirement Discovery
- **Functional Requirements**:
  - FR-01: Introduce JSON-based workflow lease metadata (`workflow-lease.json`) to track ownership details (lock_id, PID, process start time, hostname, conversation ID, etc.).
  - FR-02: Self-healing stale lease detection (checks PID active state, start time, hostname, and heartbeat timeout) and recovery.
  - FR-03: Idempotent `start` returning `already_started`/`resumed` (exit 0) for matching active workloads.
  - FR-04: Implement `StateStore` abstraction with `AtomicFileStateStore`, `InMemoryStateStore`, and `NullStateStore`.
  - FR-05: Enable runtime modes (`normal`, `test-isolated`, `test-stateful`, `test-memory`) with overrides via CLI and environment variables.
  - FR-06: Automatically release the lease on process exit (`atexit`, `SIGINT`, `SIGTERM`).
  - FR-07: Telemetry management subcommands (`status`, `lock inspect/recover/release --stale-only`, `resume`).
- **Non-functional Requirements**:
  - NFR-01: Compare-and-swap (CAS) check using a revision counter in the state document metadata (`generation`, `revision`, `event_sequence`) to prevent concurrent overwrite.
  - NFR-02: Atomic file writes via unique temp file replacement (`os.replace`) on the same filesystem.
  - NFR-03: Rate-limited heartbeats and debounced minor progress state writes.
  - NFR-04: Pytest isolated temporary state directories per worker.
- **Technical Constraints**:
  - Must remain strictly cross-platform without adding new third-party packages (use stdlib only).
  - Must keep backward compatibility with the Visualizer extension.

## 5. Requirement Traceability Matrix
| Req ID | Priority | Description | Related Blueprint Section | Expected Tests | Acceptance Criteria |
| :--- | :--- | :--- | :--- | :--- | :--- |
| FR-01 | Must | Workflow lease metadata file | Section 3.2 | Lease serialization test | lease JSON conforms to schema |
| FR-02 | Must | Self-healing stale lease recovery | Section 4 | PID active / mismatched start time tests | stale lease auto-archived and recovered |
| FR-03 | Must | Idempotent start commands | Section 6 | Repeated start test | exit code 0 and resumes correctly |
| FR-04 | Must | StateStore abstraction | Section 10 | Store registration / swap tests | store selected matches runtime mode |
| FR-05 | Must | Mode selection overrides | Section 11, 12 | Environment/CLI configuration overrides | CLI override takes precedence |
| NFR-01| Must | CAS optimistic revision control | Section 7 | Race condition simulated writers | older revision rejected, newer CAS wins |
| NFR-02| Must | Atomic state file replaces | Section 8 | Partial write crash test | no partial JSON read ever observed |
| NFR-03| Should | Debouncing and rate-limiting writes| Section 9 | Telemetry update counting test | state writes reduced for logs |
| NFR-04| Must | Pytest parallel isolation | Section 13 | Pytest -n parallel run | no state pollution in host directory |

## 6. Stakeholder Analysis
| Stakeholder | Category | Impact | Priority | Expected Benefits |
| :--- | :--- | :--- | :--- | :--- |
| AI Developer Agent | Primary | High | Critical | Crash resiliency, no lock blocking |
| Test Runner Pipeline | Internal | High | High | Faster parallel runs, stable test results |
| IDE / Extension | Secondary | Medium | Medium | Correct telemetry state without lock blockage |

## 7. Scope Boundary
- **In Scope**:
  - Full rewrite of locking/state synchronization logic in `workflow-runtime` python scripts.
  - `StateStore` class hierarchy.
  - Cross-platform process checks (Windows, Linux, macOS) in pure stdlib.
  - Modes support, Pytest fixtures, debouncing, and subcommands.
- **Out of Scope**:
  - Changes to VCS provider interactions.
  - Rewriting Visualizer dashboard UI.

## 8. Dependency Graph Preview
- FR-04: StateStore Abstraction (Must)
  ├── FR-05: Runtime Modes & Configuration (Must)
  │   └── NFR-04: Pytest parallel isolation (Must)
  ├── NFR-02: Atomic File Writes (Must)
  │   └── NFR-01: CAS Optimistic Concurrency (Must)
  └── FR-01: Workflow Lease File (Must)
      ├── FR-02: Stale Lease Detection & Recovery (Must)
      └── FR-06: Process Cleanup hooks (Must)

## 9. Data Flow Preview
- Component A (CLI / Skill)
  └── passes data to ──> StateStore.update()
      └── validates Expected Revision (CAS) ──> writes to UNIQUE temp file ──> atomically replaces active JSON via os.replace()

## 10. Existing Asset Analysis
| Asset / Component | Location / Path | Operation | Rationale |
| :--- | :--- | :--- | :--- |
| main script | `skills/workflow-runtime/scripts/workflow_runtime.py` | Refactor | Integrate new CLI command actions, update do_start/step/complete |
| session utility | `skills/workflow-runtime/scripts/session.py` | Refactor | Relocate load/save to StateStore |
| state sync utility| `skills/workflow-runtime/scripts/state_sync.py` | Refactor | Relocate write methods |
| lock file checks | `skills/workflow-runtime/scripts/workflow_runtime.py` | Refactor | Replace workflow.lock logic |

## 11. Dependency & Blast Radius Analysis
- **Affected Skills**: `workflow-runtime`, `initialize-workflow`
- **Affected Modules/Components**: python scripts inside `workflow-runtime`
- **Affected Runtime**: State synchronization, checkpoint validation, CLI execution
- **Affected Scripts**: `workflow_runtime.py`
- **Impact Level**: High (core state layer)

## 12. Migration Strategy
- **Backward Compatibility**: Keep old `.agents/state/*.json` files so Visualizer extension is unimpacted.
- **Adapter Strategy**: Map old schema fields to new revision fields during load if missing (default version to 1).
- **Deprecation Plan**: Cleanly remove the old physical `workflow.lock` file checks.

## 13. Architecture Principles
- **API First**: No.
- **Provider First**: No.
- **Script First**: Yes.
- **Memory First**: Yes.
- **Incremental Updates**: Yes (optimistic revision merging).

## 14. Non Goals
- Migrating fully to SQLite for all states (Option B rejected due to compatibility).
- Creating complex daemon locking services.

## 15. ROI Analysis
- **Estimated Implementation Cost**: Medium (1-2 developer days).
- **Runtime Savings**: Zero stale lock deadlocks. Faster local execution.
- **Token Reduction Target**: N/A.

## 16. Success Metrics
- **Latency Target**: CAS and lease check under 50ms.
- **Memory Usage Limit**: Minimal footprint (no extra libraries).
- **Startup Time Target**: Lightweight init <100ms.
- **Failure Tolerance**: Zero state corruption observed during simulated write interrupts.

## 17. Risk Matrix
| Risk | Impact | Probability | Mitigation | Owner |
| :--- | :--- | :--- | :--- | :--- |
| Windows/Linux/macOS process start time mismatch | High | Medium | Implement robust OS-specific subprocess queries with safe fallbacks | Coder |
| Optimistic write retry collision starvation | Medium | Low | Cap retries to 3 attempts with random exponential backoff | Coder |
| Pytest worker pollution | High | Low | Pytest session initialization forces isolated state directories | Coder |

## 18. Technical Questions
- What command is most portable to get process creation time on macOS without dependencies? (`ps -o lstart= -p <pid>`).
- Does `os.replace` work across partitions on Windows? (It fails if cross-volume, but our state and temp files are guaranteed to be in the same workspace directory, so it is safe).

## 19. Open Decision Register
| Topic / Decision | Current Status | Rationale & Next Steps |
| :--- | :--- | :--- |
| How to query start time on Windows? | Resolved | Use ctypes or WMIC command query, whichever is safer and fast. |

## 20. ADR Detection
- **ADR Required**: Yes
- **Rationale & Focus**: Create `ADR-006` documenting transition from long-lived file locks to state-write locks and leases.

## 21. Knowledge Update Impact
- **project-summary**: Yes, document new locking mechanism.
- **architecture**: Yes, update lock architecture guide.
- **lessons**: Yes, record lessons on concurrency.

## 22. Test Strategy Preview
- **Unit Tests**: Test store implementations (`AtomicFileStateStore`), modes (`test-isolated`, `test-memory`).
- **Integration Tests**: Test stale lease detection, PID start-time validation, idempotent start.
- **Concurrency Tests**: Multiple processes writing to the same file concurrently, validating CAS correctness.

## 23. Extension Impact
- **Extension UI Changes**: None.
- **Affected ViewModels / Watchers**: Unimpacted since JSON files remain at the same paths.

## 24. Complexity Estimation
- **Implementation Complexity**: Medium.
- **Estimated Refactoring Percentage**: 35% of workflow-runtime scripts.

## 25. Roadmap Alignment
- **Milestones**:
  - Implement StateStore and modes (Phase 1).
  - Implement Lease and Stale checks (Phase 2).
  - Implement Concurrency CAS (Phase 3).
  - Implement Test fixtures and subcommands (Phase 4).

## 26. Clarification Questions & Answers
| Question | Answer |
|---|---|
| Should we keep the old session aggregate cache? | Yes, Visualizer relies on it. |

## 27. Requirement Readiness Score
- **Score**: 100/100
- **Status**: Ready

## 28. Existing Project Context
- **Memory Source**: [project-summary.md](file:///E:/AgentsProject/.agents/memory/project-summary.md)
- **Existing Architecture Summary**: Split state model under `.agents/state/`.

## 29. Existing Modules & Services
| Module/Service | Location | Owner | Public APIs | Estimated Reuse % | Estimated Modifications % | Breaking Risk | Relevance |
|---|---|---|---|---|---|---|---|
| session | `skills/workflow-runtime/scripts/session.py` | release-manager | load_session, save_session | 50% | 50% | Medium | Reads/writes states |
| sync | `skills/workflow-runtime/scripts/state_sync.py` | release-manager | deconstruct_state, aggregate_state | 60% | 40% | Medium | Deconstructs states |

## 30. Solution Options Evaluated

### Option A: File-System Lease + Registry State Stores (Recommended)
- **Overview**: Use a metadata lease file (`workflow-lease.json`) to track active workflow ownership. The lease includes `lock_id`, `pid`, `process_started_at`, `hostname`, and `heartbeat_at`. When starting, the process validates the lease's PID start time. Implement `StateStore` with `AtomicFileStateStore` (uses unique temp files `state.json.tmp.<pid>.<uuid>` and `os.replace`) and CAS `revision` checks. Use `InMemoryStateStore` / `NullStateStore` for test isolation.
- **Advantages**: No long-lived lock deadlocks, concurrent safety via CAS, full test isolation, backward compatibility.
- **Disadvantages**: Requires cross-platform process start-time check logic.
- **Complexity**: Medium.
- **Risk**: Low.

### Option B: SQLite-Backed Lease Registry & Transactions
- **Overview**: Move all workflow states and lease tracking into the SQLite database.
- **Advantages**: Transaction safety from SQLite.
- **Disadvantages**: Breaks Visualizer extension reading JSON files.
- **Complexity**: High.
- **Risk**: High.

## 31. Solution Comparison Table
| Criteria | Option A | Option B |
|---|---|---|
| Complexity | Medium | High |
| Risk | Low | High |
| Performance | High | Medium |
| Maintainability | High | Medium |
| Compatibility | Excellent | Poor |
| Future Scalability | High | High |
| Development Cost | Medium | High |

## 32. Selected Solution
- **Choice**: Option A — File-System Lease + Registry State Stores.
- **Why Selected**: Fits the repository constraints perfectly, avoids breaking Visualizer, provides robust atomic writes and test isolation, and requires no external packages.
- **Trade-offs Accepted**: Requires custom cross-platform start-time checks.
- **Technical Debt**: None.
- **Risk Mitigation**: Build robust fallback check mechanisms.

## 33. Risks & Assumptions
- **Risks**: OS-specific commands (ps, wmic) could return differently formatted outputs.
  - *Mitigation*: Regex parsing with fallback to simple PID check on command failure.
- **Assumptions**: Temp files are written to the same workspace directory.

## 34. Acceptance Criteria
- [ ] Workflow ownership no longer depends on a long-held file lock.
- [ ] State-write locks are short-lived.
- [ ] A valid active workflow blocks a conflicting workflow.
- [ ] A stale workflow lease is detected and safely recovered.
- [ ] PID reuse is handled through process start-time validation.
- [ ] Repeated `start` for the same workflow is idempotent.
- [ ] Atomic writes prevent partial JSON.
- [ ] Unique temporary files prevent writer collision.
- [ ] Revision checks prevent stale writers from overwriting newer state.
- [ ] Older workflow generations cannot overwrite newer generations.
- [ ] Minor updates are debounced.
- [ ] Heartbeats are rate-limited.
- [ ] Main state is not rewritten for every log line.
- [ ] Normal tests run with state writes disabled.
- [ ] Stateful tests use isolated temporary state.
- [ ] Parallel workers do not share state by default.
- [ ] Only explicitly marked concurrency tests share a sandbox state file.
- [ ] Tests never modify the real project `.agents/state/`.
- [ ] Management commands can inspect and safely recover stale leases.
- [ ] Active valid leases cannot be force-released accidentally.
- [ ] Existing Visualizer behavior remains compatible.
- [ ] Existing state is migrated or read compatibly.
- [ ] All runtime tests pass.

## 35. Final Planning Prompt

### Purpose
Provide requirements for the `brainstorming-to-plan` skill to generate the execution plan for FEAT-051.

### Problem Statement
Frequent `Another workflow is already running` errors due to crash/kill of prior runs leaving a stale lock file. Concurrent write conflicts and lack of atomic replaces. Host state pollution by parallel unit test execution.

### Objectives & Selected Solution
Implement Option A: File-System Lease + Registry State Stores. Build lease model, stale recovery checks, StateStore abstraction, runtime test modes, and debounced heartbeats.

### Functional Requirements
- Lease metadata validation (active PID + start time).
- StateStore abstraction (`AtomicFileStateStore`, `InMemoryStateStore`, `NullStateStore`).
- Runtime modes (`normal`, `test-isolated`, `test-stateful`, `test-memory`).
- Idempotent CLI command `start` and subcommands `status`, `lock inspect/recover/release`.

### Non-functional Requirements & Constraints
- Optimistic Concurrency Control (CAS) using `revision` and `generation`.
- Atomic writes with unique temp files and `os.replace`.
- Debouncing and rate-limiting.
- stdlib only. Cross-platform support.

### Risks & Assumptions
- Windows/Linux/macOS process start time checks. Fallback to PID checks on error.

### Verification Checklist
- [ ] docs/plans/FEAT-051_workflow_runtime_locking_and_isolation_plan.md generated and approved
- [ ] docs/designs/FEAT-051_workflow_runtime_locking_and_isolation_blueprint.md generated and approved
- [ ] All Acceptance Criteria mapped to implementation tasks
