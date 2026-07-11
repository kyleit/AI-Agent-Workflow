---
feature_id: FEAT-086
feature_name: Executive Orchestrator Runtime
status: draft
stage: brainstorming
created_at: 2026-07-12
updated_at: 2026-07-12
previous_artifact: None
next_artifact: ../plans/FEAT-086_executive_orchestrator_runtime_plan.md
---

# Master Brainstorming Document – Executive Orchestrator Runtime (FEAT-086)

## 1. Executive Summary
This document designs the **Executive Orchestrator Runtime**, the foundational core of the upgraded AIWF Operating System. It transitions AIWF from a phase-driven pipeline to a dynamic, goal-driven runtime engine. The Executive Runtime manages the top-level execution loop, parses and tracks the Objective Lifecycle, persists process state, and guarantees crash recovery across session rollovers.

## 2. Background
The current AIWF manages development workflows procedurally via checkpoints (e.g., Spec, Blueprint, Code, Verify). While effective for guided scripts, this structure prevents the runtime from executing autonomous tasks, branching dynamically, or recovering from middle-loop process interrupts. An advanced coding-agent architecture requires a persistent, goal-driven executive loop to orchestrate subagents and tools autonomously.

## 3. Current Architecture Analysis
The current `orchestrator` skill and `workflow_runtime.py` coordinate the state using files like `runtime.json`, `context.json`, and `workflow.json`. State transitions are triggered manually by executing sequential CLI commands.
- File-based checkpoint system tracking progress from 1 to 9.
- Telemetry saves basic usage and latency statistics to `workflow_usage.db`.

## 4. Current Limitations
- **Procedural Checkpoints**: Hardcoded phases cannot handle recursive sub-tasks or parallel branches.
- **No Goal Representation**: The runtime cannot model complex objectives as a dynamic tree.
- **Vulnerability to Interrupts**: If a process crashes mid-step, there is no automatic state reconstruction or recovery mechanism.
- **Manual Transition**: Agents cannot autonomously hand over execution context without CLI-level triggers.

## 5. Objectives
- Establish an **Executive Runtime Core** that drives the agentic loop.
- Implement a hierarchical **Goal Tree** data structure representing the objective lifecycle.
- Support **Crash Recovery** and state reconstruction via transaction-like snapshots.

## 6. Functional Requirements
- **FR-01: Objective Lifecycle Management**: Define states (`pending`, `active`, `completed`, `failed`, `suspended`).
- **FR-02: Execution Loop (Reconstruct-Plan-Execute-Verify)**: Execute loop cycles with evaluation metrics.
- **FR-03: Process Persistence**: Write atomic snapshots on every loop transition.
- **FR-04: Crash Recovery & Rollover Resume**: Detect unclean shutdowns, restore state from `.agents/runtime/context_snapshot.json`, and resume execution.

## 7. Non-Functional Requirements
- **NFR-01: Loop Cycle Latency**: The orchestrator's decision cycle overhead must be `< 50ms`.
- **NFR-02: Memory Footprint**: Minimal heap allocation in pure stdlib.
- **NFR-03: Crash Safety**: State commits must use atomic replace (`os.replace`) to guarantee zero corruption.

## 8. Scope
- Core loop engine (`runtime.py`).
- State machine for Objective Lifecycle.
- Persistence and restore interfaces.
- CLI subcommands for runtime controls (`start`, `loop`, `resume`, `halt`).

## 9. Out of Scope
- Specific agent execution logic (delegated to Multi-Agent Runtime).
- Visualizer UI implementation (delegated to Extension).

## 10. Runtime Responsibilities
The Executive Runtime owns the primary execution thread. It validates preconditions, starts and logs cycles, triggers subagents, verifies outcomes, and persists progress metrics.

## 11. Components
- `ExecutiveLoopController`: Governs the execution cycles.
- `GoalTreeManager`: Manipulates the goal nodes and computes resolution.
- `CrashRecoveryHandler`: Manages snapshots and stale locks.
- `RuntimeStateStore`: Persists session details atomicaly.

## 12. Data Model
```json
{
  "session_id": "uuid-string",
  "objective": {
    "id": "OBJ-001",
    "text": "Implement database locking",
    "status": "active",
    "children": []
  },
  "loop_iteration": 14,
  "last_active_agent": "planner",
  "snapshots": []
}
```

## 13. Runtime State
```
[Idle] ──(start)──> [Reconstructing] ──> [Evaluating] ──> [Executing] ──> [Verifying] ──> [Completed]
                                              ▲                                │
                                              └───────(next cycle / fail)──────┘
```

## 14. Event Flow
1. User invokes `/goal`.
2. Executive Runtime registers the goal, writes `runtime.json`, and starts the loop.
3. The loop evaluates the next sub-objective.
4. Dispatcher spawns the designated agent.
5. Agent returns results, triggering verification.
6. Loop checks for goal completion. If done, exits.

## 15. Sequence Flow
- **Start**: Reads `context.json` -> Resolves dependencies -> Initiates Loop.
- **Iterate**: Snapshot -> Execute Agent -> Validate -> Update Goal Tree.
- **Halt**: Write final state -> Release locks -> Exit.

## 16. Dependencies
- State manager and Lease engine (from FEAT-051).

## 17. Integration Points
- CLI interface (`workflow_runtime.py`).
- IPC channel with Visualizer webview (`webviewHtml.ts`).

## 18. Interaction with other features
- Triggers the **Task Graph Engine (FEAT-087)** to schedule sub-tasks.
- Dispatches executions to the **Multi-Agent Runtime (FEAT-088)**.
- Logs events to the **Event Journal (FEAT-089)**.

## 19. Security Considerations
- Execution timeouts to prevent infinite loops.
- Sandboxed execution scope constraints.

## 20. Performance Considerations
- Debounced state writes.
- Lazy-loading of non-critical state files.

## 21. Scalability Considerations
- Tree structure design allows scaling up to 1000 nodes without latency decay.

## 22. Failure Scenarios
- Process killed via SIGKILL: Stale lease will be detected by the next process, restoring state from `context_snapshot.json`.
- State file write crash: Solved via atomic swap writing to `context.json.tmp` first.

## 23. Recovery Strategy
On startup, look for `.agents/runtime/context_snapshot.json`. If found, verify process PID has exited, read the snapshot, pop the stash, and resume from the saved iteration.

## 24. Migration Strategy
Translate existing checkpoint numbers (`1-9`) into corresponding linear Goal Tree nodes to preserve compatibility with existing pipelines.

## 25. Backward Compatibility
Expose standard `runtime.json` fields expected by the Visualizer extension.

## 26. Risks
- Infinite loop execution due to incorrect goal resolution criteria. Mitigated by setting a max loop threshold.

## 27. Alternative Designs
- **Option A**: State machine in LLM prompts. (Rejected: non-deterministic).
- **Option B**: SQLite-only state storage. (Deferred: JSON files preferred for visualizer compatibility).

## 28. Trade-offs
- Writing snapshots on every cycle increases disk writes (~2-5ms) but guarantees crash safety.

## 29. Acceptance Criteria
- [ ] AC-01: Successfully reconstruct state tree from crashed session snapshot.
- [ ] AC-02: Complete execution loop without any manual checkpoint updates.

## 30. Estimated Complexity
- High.

## 31. Blueprint Estimation
- 1 design blueprint (`docs/designs/FEAT-086_executive_orchestrator_runtime.md`).

## 32. Recommended Implementation Order
This feature must be implemented first, as all other subsystems register with the Executive Loop.
