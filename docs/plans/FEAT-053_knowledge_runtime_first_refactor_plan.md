<!-- File path: docs/plans/FEAT-053_knowledge_runtime_first_refactor_plan.md -->

---
feature_id: FEAT-053
feature_name: Refactor AIWF Knowledge Retrieval to a Runtime-First Architecture
status: reviewed
stage: planning
created_at: 2026-07-11
updated_at: 2026-07-11
previous_artifact: ../brainstorming/FEAT-053_knowledge_runtime_first_refactor.md
next_artifact: ../designs/FEAT-053_knowledge_runtime_first_refactor_blueprint.md
---

# FEAT-053: Refactor AIWF Knowledge Retrieval to a Runtime-First Architecture

## 1. Requirement Coverage Matrix
| Req ID | Phase | Task ID | Deliverable | Covered? |
| :--- | :--- | :--- | :--- | :---: |
| FR-01 | Phase 1 | Task 1.1 | Unified Knowledge Runtime core package | [x] |
| FR-02 | Phase 1 | Task 1.2 | QMD metadata storage SQLite schemas and queries | [x] |
| FR-03 | Phase 1 | Task 1.3 | Qdrant semantic vector integration and routing | [x] |
| FR-04 | Phase 1 | Task 1.4 | Obsidian section-level document resolver | [x] |
| FR-05 | Phase 2 | Task 2.1 | Caching layer with TTL and invalidation protocol | [x] |
| FR-06 | Phase 2 | Task 2.2 | Command line interface diagnostics and subcommands | [x] |
| FR-07 | Phase 3 | Task 3.1 | Migration of existing skills (project-rag-search, memory-bootstrap, memory-update) | [x] |

## 2. Task Ownership & Roles
- **Task 1.1 (Runtime Core)**: [Architect] - Define core pipeline hooks.
- **Task 1.2 (QMD DB)**: [Database Developer] - Initialize SQLite indexing schemas.
- **Task 1.3 (Qdrant Vector)**: [Backend Developer] - Implement semantic query routing.
- **Task 1.4 (Obsidian Resolver)**: [Backend Developer] - Refactor physical file reader to target specific sections.
- **Task 2.1 (Cache layer)**: [Backend Developer] - Implement in-memory & file-based query caching.
- **Task 2.2 (Diagnostics CLI)**: [Coder] - Register diagnostic and status CLI entrypoints.
- **Task 3.1 (Skills Migration)**: [Coder] - Migrate file-first search operations to Knowledge Runtime client queries.

## 3. Parallel Execution Plan
- **Sequential Tasks**: Task 1.1 -> Task 1.2 -> Task 3.1
- **Parallel Tasks**: [Task 1.3, Task 1.4, Task 2.1]
- **Blocking Tasks**: Task 1.2 (blocks Task 1.3)
- **Independent Tasks**: Task 2.2
- **Recommended Execution Groups**:
  - Group 1: Task 1.1, Task 1.2
  - Group 2: Task 1.3, Task 1.4, Task 2.1 (Parallel)
  - Group 3: Task 2.2, Task 3.1

## 4. File Change Plan (Implementation Boundary)
| Task ID | File Path | Operation | Rationale |
| :--- | :--- | :--- | :--- |
| Task 1.1 | `skills/knowledge-runtime/scripts/knowledge_runtime.py` | Create | Introduce the unified runtime controller class |
| Task 1.2 | `skills/workflow-runtime/scripts/db.py` | Modify | Expand database logic to handle QMD metadata tables |
| Task 1.3 | `skills/knowledge-runtime/scripts/qdrant_client.py` | Create | Provide semantic client wrapper |
| Task 1.4 | `skills/knowledge-runtime/scripts/obsidian_resolver.py` | Create | Provide section-targeted parser |
| Task 2.2 | `skills/workflow-runtime/scripts/workflow_runtime.py` | Modify | Connect CLI subcommands `aiwf knowledge ...` |
| Task 3.1 | `skills/project-rag-search/scripts/project_rag_search.py` | Modify | Route search requests through local Runtime API |

## 5. Blueprint Preparation Inputs
- **Interfaces / Classes / Modules**: Centralized `KnowledgeRuntime` routing to `QmdRouter`, `QdrantSearcher`, and `ObsidianResolver`.
- **Provider Pattern details**: Client abstraction supporting local SQLite, Qdrant client, and fallback file-traversal.
- **Data Flow / Sequence Flow**: Client Query -> KnowledgeRuntime -> Qdrant -> QMD SQLite -> Obsidian Section -> Context payload.
- **Migration Strategy & Testing Architecture**: Deploy `LegacySearchAdapter` to preserve backward compatibility for bootstrap operations.

## 6. Verification Strategy & Test Mapping
- **Unit Tests**:
  - `skills/knowledge-runtime/tests/test_runtime_api.py` (Mapped to Task 1.1)
  - `skills/knowledge-runtime/tests/test_qmd.py` (Mapped to Task 1.2)
  - `skills/knowledge-runtime/tests/test_cache.py` (Mapped to Task 2.1)
- **Integration Tests**:
  - `skills/knowledge-runtime/tests/test_qdrant_integration.py` (Mapped to Task 1.3)
  - `skills/knowledge-runtime/tests/test_cli.py` (Mapped to Task 2.2)
- **Compatibility / Regression Tests**:
  - Verify existing memory bootstrap outputs matching output snapshots.

## 7. Exit Criteria
- **Phase 1 Exit Criteria**:
  - [ ] 100% of unit tests for API and QMD routing pass.
  - [ ] Local search handles document section retrieval without directory scans.
- **Phase 2 Exit Criteria**:
  - [ ] Cache retrieval returns hit rate matching performance criteria.
  - [ ] All `aiwf knowledge` CLI subcommands exit with code 0.
- **Phase 3 Exit Criteria**:
  - [ ] Complete migration of all core skills to Runtime API.
  - [ ] Physical workspace scan frequency is exactly 0 during search calls.

## 8. Rollback Strategy
- **Phase 1 Rollback**:
  - Trigger: Database locking errors or Qdrant connection drops blocking workflow initialization.
  - Steps: Revert git commits, fallback to static JSON index loaders.
  - Recovery: Re-initialize workspace permissions and memory states to clean snapshot.

## 9. Change Impact Matrix
| Task ID | Files | Modules | Runtime | Extension | Documentation | Memory | Database |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Task 1.1 | Yes | Yes | Yes | No | Yes | No | No |
| Task 1.2 | Yes | Yes | Yes | No | Yes | No | Yes |
| Task 1.3 | Yes | Yes | Yes | No | Yes | No | No |
| Task 1.4 | Yes | Yes | Yes | No | Yes | No | No |
| Task 2.1 | Yes | Yes | Yes | No | Yes | No | No |
| Task 2.2 | Yes | Yes | Yes | No | Yes | No | No |
| Task 3.1 | Yes | Yes | Yes | No | Yes | Yes | No |

## 10. Artifact Production Plan
- **Phase 1 Artifacts**: `docs/designs/FEAT-053_knowledge_runtime_first_refactor_blueprint.md`
- **Phase 2 Artifacts**: `docs/releases/Release_Notes_FEAT-053.md`

## 11. Token & Execution Optimization
- **Sequential execution cost**: Estimating ~45,000 tokens during development.
- **Parallel execution opportunities**: Tasks 1.3, 1.4, 2.1 can be designed in parallel.
- **Expected token savings**: Expecting ~35% token footprint reduction for search execution.
- **Recommended execution strategy**: Perform database schema and connection integration first, then implement parallel layers.

## Recommended Next Skill
/blueprint
