---
feature_id: FEAT-092
feature_name: Multi-Tenant Workspace & Context Isolation
status: draft
stage: brainstorming
created_at: 2026-07-12
updated_at: 2026-07-12
previous_artifact: None
next_artifact: ../plans/FEAT-092_workspace_context_isolation_plan.md
---

# Master Brainstorming Document – Multi-Tenant Workspace & Context Isolation (FEAT-092)

## 1. Executive Summary
This document designs the **Multi-Tenant Workspace & Context Isolation** engine. It establishes mechanisms to isolate conversations, workspaces, and runtime threads. It guarantees that memory databases, caches, and session contexts do not leak across project boundaries or active branch environments.

## 2. Background
Currently, the AIWF runtime is single-tenant. It assumes a single active developer conversation in a single local workspace. In environments where multiple developers run parallel tasks, or where an agent works on multiple branch workspaces simultaneously, context leakage can lead to corrupted state databases or incorrect task context.

## 3. Current Architecture Analysis
The current session stores global variables and writes directly to `.agents/state/*.json`.
- State paths are relative but lack multi-session namespace prefixes.
- SQLite files are shared globally within the `.agents` folder.

## 4. Current Limitations
- **No Session Separation**: Running two parallel CLI agent commands on different tasks can overwrite `runtime.json`.
- **Database Pollution**: Logs and token metrics from different tasks are mixed in a single SQLite file.
- **Cache Contamination**: Shared memory and RAG caches can mix context from different branches.

## 5. Objectives
- Implement **Context Isolation** using unique workspace and conversation IDs.
- Develop **Isolated State Stores** per execution thread.
- Provide **Memory and Cache Isolation** for parallel tasks.

## 6. Functional Requirements
- **FR-01: Session Identity**: Generate unique `session_id` and `conversation_id` markers for all active threads.
- **FR-02: Isolated State Namespaces**: Partition `.agents/state` into subfolders based on conversation and workspace IDs.
- **FR-03: RAG Cache Isolation**: Key vector search caches with workspace-specific hash prefixes.
- **FR-04: Memory Partitioning**: Prevent agents from accessing project memory chunks belonging to other workspaces.
- **FR-05: Concurrent Worktrees**: Run parallel task branches in isolated local git worktree subfolders.

## 7. Non-Functional Requirements
- **NFR-01: Leak Prevention**: Zero shared memory variables between distinct execution threads.
- **NFR-02: Directory Checks**: Sandbox isolation checks must execute in `< 5ms` during context validation.

## 8. Scope
- Session partitioning logic in `context.py`.
- Isolated directory managers.
- RAG search cache namespace keys.
- Command-line overrides to isolate threads.

## 9. Out of Scope
- Full container-level virtualization (restricted to workspace filesystem partitioning).
- Multi-user authentication frameworks.

## 10. Runtime Responsibilities
The Isolation Runtime constructs execution workspaces, assigns session folders, cleans up temporary context resources on exit, and verifies directory boundaries.

## 11. Components
- `SessionNamespaceCoordinator`: Assigns paths and creates session directories.
- `WorkspaceSandboxVerifier`: Evaluates paths to prevent traversal leaks.
- `CacheKeyspaceManager`: Partition caches and database records.

## 12. Data Model
```
.agents/
  ├── state/
  │   ├── default/
  │   └── sessions/
  │       ├── session_uuid_1/
  │       │   ├── context.json
  │       │   └── runtime.json
  │       └── session_uuid_2/
```

## 13. Runtime State
```
[GlobalContext] ──(initialize session)──> [Constructing Namespace] ──> [IsolatedRun]
                                                                            │
                                                                         (exit)
                                                                            ▼
                                                                     [Cleanup State]
```

## 14. Event Flow
1. Agent commands are dispatched with unique conversation IDs.
2. The orchestrator identifies the session namespace.
3. It maps state directories to `.agents/state/sessions/<session_id>/`.
4. State reads and writes are isolated to this subfolder.
5. SQLite trace records are tagged with the session ID.
6. Caches use namespace-prefixed keys.

## 15. Sequence Flow
- Resolve session ID -> create workspace folders -> configure state routes -> run isolated task -> archive state on completion.

## 16. Dependencies
- State Manager and Lease system (from FEAT-051).

## 17. Integration Points
- CLI arguments: `--session-id` and `--workspace-path`
- File System: `.agents/state/sessions/`

## 18. Interaction with Executive Runtime
- The Executive loop queries the Namespace Coordinator on startup to isolate state files before launching.

## 19. Interaction with other features
- Provides isolated environments and workspaces for the **Multi-Agent Runtime (FEAT-088)**.

## 20. Security Considerations
- Enforce strict path prefix validations to prevent file path traversal.
- Prevent symlink attacks that attempt to link files outside the workspace bounds.

## 21. Performance Considerations
- Clean up expired session files automatically to prevent disk bloat.

## 22. Scalability Considerations
- Design supports scaling up to 100 concurrent execution sessions.

## 23. Failure Scenarios
- **Session ID Collision**: Generate UUIDs to guarantee uniqueness.
- **Workspace locked by concurrent process**: Raise resource collision error and queue the task.

## 24. Recovery Strategy
On crash, inspect the workspace session database, locate orphaned session directories, check if their processes have terminated, and archive or delete stale directories.

## 25. Migration Strategy
Map the legacy flat `.agents/state/` files to the `default` session directory namespace.

## 26. Backward Compatibility
Support flat, non-isolated states if no session ID parameter is provided.

## 27. Risks
- Workspace directory bloat from orphaned session folders. Mitigated by automatic cleanup tasks.

## 28. Alternative Designs
- **Option A**: Use docker containers. (Rejected: too slow for rapid local development tasks).
- **Option B**: Completely separate repositories. (Rejected: does not support parallel branch tasks on a single project).

## 29. Trade-offs
- Path isolation adds path parsing logic but prevents context contamination.

## 30. Acceptance Criteria
- [ ] AC-01: Parallel agent commands run simultaneously without overwriting each other's state files.
- [ ] AC-02: Prevent vector search leakage across workspaces.

## 31. Estimated Complexity
- Medium.

## 32. Blueprint Estimation
- 1 design blueprint (`docs/designs/FEAT-092_workspace_context_isolation.md`).

## 33. Recommended Implementation Order
Implement seventh, following the Safety Runtime.
