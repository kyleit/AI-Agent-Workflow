---
feature_id: FEAT-087
feature_name: Task Graph Engine
status: draft
stage: brainstorming
created_at: 2026-07-12
updated_at: 2026-07-12
previous_artifact: None
next_artifact: ../plans/FEAT-087_task_graph_engine_plan.md
---

# Master Brainstorming Document – Task Graph Engine (FEAT-087)

## 1. Executive Summary
This document designs the **Task Graph Engine (DAG)** for scheduling and orchestrating execution units within the AIWF. It manages task dependencies, priorities, and enforces execution topologies (both safe sequential execution and future isolated parallel branches), with retry, recovery, and dynamic re-planning on failures.

## 2. Background
Currently, AIWF workflows are completely linear. A failure in any step aborts the entire run. To solve complex development targets, an agent system must model sub-tasks as a dependency graph. If one branch fails, the engine should re-plan or retry only the affected nodes, leaving independent branches untouched.

## 3. Current Architecture Analysis
The current codebase has no task graphing system. The `breakdown_engine.py` generates basic sequential steps, but does not track dependencies or schedule executions dynamically.

## 4. Current Limitations
- **Linear execution**: Cannot execute non-dependent tasks out of order or concurrently.
- **Fragile recovery**: Any step failure breaks the process; there is no sub-tree re-evaluation or isolated retry logic.

## 5. Objectives
- Implement a **DAG Engine** that compiles task definitions into a topological schedule.
- Provide a **Scheduler** with priority queues.
- Support **Dynamic Re-planning** by pruning and appending nodes to the active graph.

## 6. Functional Requirements
- **FR-01: Graph Compilation**: Build a DAG from task specifications containing `id`, `depends_on`, and `priority`.
- **FR-02: Scheduler**: Topologically sort and schedule ready tasks (in-degree = 0).
- **FR-03: Execution Modes**: Support strict sequential execution and sandbox-isolated parallel execution.
- **FR-04: Resilient Recovery**: Define error policies (`retry_limit`, `fail_fast`, `ignore_and_continue`).
- **FR-05: Runtime Re-planning**: Mutate the active graph based on agent feedback during execution.

## 7. Non-Functional Requirements
- **NFR-01: Graph Cycle Detection**: Throws a cycle error in `< 10ms` using Kahn's algorithm.
- **NFR-02: Safety**: Parallel execution branches must run in isolated local directories (worktrees).

## 8. Scope
- Directed Graph module (`dag.py`).
- Task Scheduler and Priority Queue.
- Error handler and retry controller.
- CLI actions to inspect and debug the active graph.

## 9. Out of Scope
- Sandboxed environment setups (handled by Project Isolation).
- Agent execution locks (handled by Multi-Agent Runtime).

## 10. Runtime Responsibilities
The Task Graph Engine maintains the active graph schema, queues executable tasks, manages child processes, and updates the task state on execution feedback.

## 11. Components
- `DAGCompiler`: Validates structure, checks for cycles.
- `TaskQueueScheduler`: Dispatches ready tasks based on priority.
- `ReplanningController`: Intercepts failures, deletes or adds recovery nodes.

## 12. Data Model
```json
{
  "graph_id": "graph-123",
  "nodes": {
    "T1": {"id": "T1", "status": "completed", "depends_on": [], "priority": 3},
    "T2": {"id": "T2", "status": "ready", "depends_on": ["T1"], "priority": 1}
  }
}
```

## 13. Runtime State
Nodes transition through:
`[Blocked]` ──(dependencies cleared)──> `[Ready]` ──> `[Running]` ──> `[Completed] / [Failed]`

## 14. Event Flow
1. Executive Runtime reads plan and compiles graph.
2. Scheduler flags nodes T1, T2 as ready.
3. Workers pick nodes, start execution, and return exit codes.
4. On success, dependent nodes are unlocked.
5. On failure, error handler checks retry limits and triggers re-planning.

## 15. Sequence Flow
- Compile -> topological sort -> step-by-step queueing -> check status -> handle failures -> continue until graph is empty.

## 16. Dependencies
- Executive Orchestrator Runtime (FEAT-086) for lifecycle triggers.

## 17. Integration Points
- CLI: `python workflow_runtime.py task graph show`
- State: `.agents/state/breakdown.json`

## 18. Interaction with Executive Runtime
- The Executive Loop queries the Task Graph Engine to get the next executable task, and notifies it on completion or failure.

## 19. Interaction with other features
- Obtains lock boundaries from **Multi-Agent Runtime (FEAT-088)**.
- Logs task scheduling states to **Event Journal (FEAT-089)**.

## 20. Security Considerations
- Prevent infinite retries by capping the maximum retry count to 3.
- Do not execute tasks if dependency validation has failed.

## 21. Performance Considerations
- Keep graph models in memory; write graph states to disk only during node transitions to minimize I/O overhead.

## 22. Scalability Considerations
- Design scales to hundreds of tasks.

## 23. Failure Scenarios
- **Cycle Detected**: Stop compilation, return validation error.
- **Node Crashes**: Stop executing downstream dependent tasks, transition graph to `suspended` state.

## 24. Recovery Strategy
When resuming, inspect the saved graph, skip completed nodes, reset running nodes to `ready`, and resume schedule.

## 25. Migration Strategy
Translate linear steps in existing `breakdown.json` files into a single-path sequential DAG to maintain backward compatibility.

## 26. Backward Compatibility
Fall back to standard sequential execution if the graph contains no explicit branching structure.

## 27. Risks
- Deadlocks from circular dynamic dependencies added during execution. Mitigated by re-running cycle checks after any graph mutation.

## 28. Alternative Designs
- **Option A**: Use external libraries (like `networkx`). (Rejected: adds external dependencies).
- **Option B**: Pure sequential engine. (Rejected: cannot handle parallel agent workflows).

## 29. Trade-offs
- Graph mutation during execution adds complexity, but is necessary for autonomous re-planning.

## 30. Acceptance Criteria
- [ ] AC-01: Correctly detect cyclic dependencies and raise compile error.
- [ ] AC-02: Successfully execute T2 only after T1 completes successfully.

## 31. Estimated Complexity
- Medium to High.

## 32. Blueprint Estimation
- 1 design blueprint (`docs/designs/FEAT-087_task_graph_engine.md`).

## 33. Recommended Implementation Order
Implement after FEAT-086, as scheduling depends on the core execution loop.
