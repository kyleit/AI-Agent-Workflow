<!-- File path: docs/plans/FEAT-050_lightweight_runtime_initialization_plan.md -->

---
feature_id: FEAT-050
feature_name: Lightweight Runtime Initialization & Runtime Dependency Resolver
status: reviewed
stage: planning
created_at: 2026-07-10
updated_at: 2026-07-10
previous_artifact: ../brainstorming/FEAT-050_lightweight_runtime_initialization.md
next_artifact: ../designs/FEAT-050_lightweight_runtime_initialization_blueprint.md
---

# FEAT-050: Lightweight Runtime Initialization & Runtime Dependency Resolver

## 1. Requirement Coverage Matrix
| Req ID | Phase | Task ID | Deliverable | Covered? |
| :--- | :--- | :--- | :--- | :---: |
| FR-01 | Phase 1 | Task 1.1 | Lightweight initialization instructions manifest | [x] |
| FR-02 | Phase 1 | Task 1.2 | Script-first runtime bootstrap functions | [x] |
| FR-03 | Phase 1 | Task 1.3 | Cached state loaders for metadata | [x] |
| FR-07 | Phase 2 | Task 2.1 | Shared Dependency Resolver module | [x] |
| FR-05 | Phase 2 | Task 2.2 | Requirements schema validator | [x] |
| FR-09 | Phase 2 | Task 2.3 | Command sub-group `deps` (inspect, resolve, validate, doctor) | [x] |
| FR-08 | Phase 2 | Task 2.4 | Pre-execution dependency resolution check | [x] |
| FR-08 | Phase 2 | Task 2.5 | Resolution history output file | [x] |
| FR-05 | Phase 3 | Task 3.1 | Environment snapshot caching reader | [x] |
| FR-06 | Phase 3 | Task 3.2 | Lazy loading targeted memory index | [x] |
| FR-06 | Phase 3 | Task 3.3 | Lazy loading targeted RAG search loader | [x] |
| FR-02 | Phase 3 | Task 3.4 | Cached project version & work-item resolver | [x] |
| FR-04 | Phase 3 | Task 3.5 | Workspace scan execution constraint gate | [x] |
| FR-05 | Phase 4 | Task 4.1 | Core skills manifests migration | [x] |
| FR-05 | Phase 4 | Task 4.2 | Skills preload sequence description cleanup | [x] |
| FR-05 | Phase 4 | Task 4.3 | Legacy session state assumptions cleanup | [x] |
| FR-06 | Phase 5 | Task 5.1 | Dependency resolver test suites | [x] |
| FR-01 | Phase 5 | Task 5.2 | Lightweight initialization performance tests | [x] |
| FR-06 | Phase 5 | Task 5.3 | Compatibility tests for legacy skills | [x] |
| FR-07 | Phase 5 | Task 5.4 | Guides and architectural documentation | [x] |

## 2. Task Ownership & Roles
- **Task 1.1**: [Architect] - Rewrite initialization manifest to outline lightweight guardrail-only boundaries. (Design only, no code modification).
- **Task 1.2**: [Coder] - Refactor runtime entrypoint to move initialization logic into script-first functions.
- **Task 1.3**: [Coder] - Create state readers for workflow, approvals, dashboard, and git.
- **Task 2.1**: [Coder] - Create core dependency resolver library.
- **Task 2.2**: [Coder] - Implement `runtime_requirements` parsing schema.
- **Task 2.3**: [Coder] - Implement `deps` CLI subcommand group handlers.
- **Task 2.4**: [Coder] - Hook dependency resolution checks before executing any skill.
- **Task 2.5**: [Coder] - Record dependency states to `.agents/state/runtime/dependencies.json`.
- **Task 3.1**: [Coder] - Implement environment snapshot cached reader and stale warning reminders.
- **Task 3.2**: [Coder] - Implement dynamic targeted memory index loader.
- **Task 3.3**: [Coder] - Implement lazy RAG metadata and query loader.
- **Task 3.4**: [Coder] - Implement cached project version and active work-item resolvers.
- **Task 3.5**: [Coder] - Ensure workspace scan is blocked unless permitted by requirements.
- **Task 4.1**: [Coder] - Inject manifests declarations to core skills.
- **Task 4.2**: [Coder] - Remove legacy initialization preloading documentation.
- **Task 4.3**: [Coder] - Refactor quick-fix/quick-feature/resume/debug/release skills to use new resolver states.
- **Task 5.1**: [Reviewer] - Write dependency resolver tests.
- **Task 5.2**: [Reviewer] - Verify lightweight initialization performance latency.
- **Task 5.3**: [Reviewer] - Add compatibility tests for legacy skills fallback paths.
- **Task 5.4**: [Reviewer] - Produce guides and ADR documentation.

## 3. Parallel Execution Plan
- **Sequential Tasks**: Task 1.1 -> Task 1.2 -> Task 1.3 -> Task 2.1 -> Task 2.4 -> Task 2.5 -> Task 4.1 -> Task 5.1
- **Parallel Tasks**: [Task 2.2, Task 2.3], [Task 3.1, Task 3.2, Task 3.3, Task 3.4, Task 3.5]
- **Blocking Tasks**: Task 2.1 (blocks Task 2.4 and Task 2.6)
- **Independent Tasks**: Task 3.1, Task 5.4
- **Recommended Execution Groups**:
  - Group 1: Task 1.1
  - Group 2: Task 1.2, Task 1.3
  - Group 3: Task 2.1, Task 2.2, Task 2.3 (Parallel)
  - Group 4: Task 2.4, Task 2.5
  - Group 5: Task 3.1, Task 3.2, Task 3.3, Task 3.4, Task 3.5 (Parallel)
  - Group 6: Task 4.1, Task 4.2, Task 4.3
  - Group 7: Task 5.1, Task 5.2, Task 5.3, Task 5.4

## 4. File Change Plan (Implementation Boundary)
| Task ID | File Path | Operation | Rationale |
| :--- | :--- | :--- | :--- |
| Task 1.1 | `skills/initialize-workflow/SKILL.md` | Modify | Define lightweight guardrail-only initialization |
| Task 1.2 | `skills/workflow-runtime/scripts/workflow_runtime.py` | Modify | Support deps subcommands, refactor initialization to script functions |
| Task 2.1 | `skills/workflow-runtime/scripts/dependency_resolver.py` | Create | Central resolver library |
| Task 2.2 | `skills/workflow-runtime/scripts/context.py` | Modify | Add lazy loader wrappers |
| Task 2.1 | `skills/workflow-runtime/scripts/validator.py` | Modify | Implement environment snapshot reader |
| Task 1.3 | `skills/workflow-runtime/scripts/session.py` | Modify | Read/write split state JSONs instead of direct .session.json |
| Task 1.2 | `skills/workflow-runtime/scripts/state_sync.py` | Modify | Support split state synchronization |
| Task 4.1 | `skills/project-memory-bootstrap/SKILL.md` | Modify | Add runtime_requirements |
| Task 4.1 | `skills/project-memory-update/SKILL.md` | Modify | Add runtime_requirements |
| Task 4.1 | `skills/project-rag-search/SKILL.md` | Modify | Add runtime_requirements |
| Task 4.1 | `skills/environment-health/SKILL.md` | Modify | Add runtime_requirements |
| Task 4.1 | `skills/brainstorming/SKILL.md` | Modify | Add runtime_requirements |
| Task 4.1 | `skills/brainstorming-to-plan/SKILL.md` | Modify | Add runtime_requirements |
| Task 4.1 | `skills/plan-to-blueprint/SKILL.md` | Modify | Add runtime_requirements |
| Task 4.1 | `skills/blueprint-to-implementation/SKILL.md` | Modify | Add runtime_requirements |
| Task 4.1 | `skills/implementation-to-debug/SKILL.md` | Modify | Add runtime_requirements |
| Task 4.1 | `skills/debug-to-verify/SKILL.md` | Modify | Add runtime_requirements |
| Task 4.1 | `skills/implementation-to-release/SKILL.md` | Modify | Add runtime_requirements |
| Task 5.1 | `skills/workflow-runtime/tests/test_dependency_resolver.py` | Create | Unit tests for resolver library |
| Task 5.1 | `skills/workflow-runtime/tests/test_runtime_requirements_schema.py` | Create | Unit tests for manifest schema validation |
| Task 5.1 | `skills/workflow-runtime/tests/test_dependency_resolver_cli.py` | Create | CLI tests for deps subcommand |
| Task 5.2 | `skills/workflow-runtime/tests/test_lightweight_initialize.py` | Create | Verify initialization performance |
| Task 5.4 | `docs/guides/runtime-dependency-resolver.md` | Create | Dependency guide |
| Task 5.4 | `docs/adr/ADR-008_runtime_dependency_resolver.md` | Create | Architectural Decision Record |

## 5. Script-First Optimization
To optimize context footprint and latency, all complex startup operations are moved out of skill instructions and implemented inside dedicated Python script functions:
- `load_guardrails_summary()`
- `load_dashboard_state()`
- `load_approval_state()`
- `detect_git_branch_status()`
- `read_environment_snapshot()`
- `resolve_runtime_requirements()`
- `detect_active_work_item_cached()`
- `detect_project_version_cached()`
- `write_initialization_summary()`
- `validate_no_heavy_init_operations()`

## 6. Verification Strategy & Test Mapping
- **Unit Tests**:
  - `test_dependency_resolver.py`: verify resolver resolves rules, approvals, and cache levels.
  - `test_runtime_requirements_schema.py`: verify incorrect keys/modes fail validation.
  - `test_dependency_resolver_cli.py`: verify CLI deps resolve/doctor commands.
  - `test_lightweight_initialize.py`: verify initialize-workflow does not connect to RAG, load Project Memory, or run toolchain checks.
- **Integration Tests**: verify backward compatibility fallbacks for legacy skills.

## 7. Exit Criteria
- **Phase 1 Exit Criteria**:
  - [ ] Initialize-workflow runs without workspace scans, versions scanning, or environment toolchain queries.
  - [ ] Rules, gates, and session states are verified to load successfully.
- **Phase 2 Exit Criteria**:
  - [ ] `deps resolve` command validates requirements and writes resolution data to `dependencies.json`.
- **Phase 3 Exit Criteria**:
  - [ ] RAG and Memory are loaded dynamically only when requested.
- **Phase 4 Exit Criteria**:
  - [ ] All core skills manifests contain correct `runtime_requirements`.
- **Phase 5 Exit Criteria**:
  - [ ] 100% tests pass and startup latency is verified to be under 0.8s.

## 8. Rollback Strategy
- **Phase 1 Rollback**:
  - Trigger: System initialization failure or schema parsing exception.
  - Steps: Revert git commits, restore original initialize-workflow sequence.
  - Recovery: Restore normal main branch runtime state.
