---
feature_id: FEAT-088
feature_name: Multi-Agent Runtime
status: draft
stage: brainstorming
created_at: 2026-07-12
updated_at: 2026-07-12
previous_artifact: None
next_artifact: ../plans/FEAT-088_multi_agent_runtime_plan.md
---

# Master Brainstorming Document – Multi-Agent Runtime (FEAT-088)

## 1. Executive Summary
This document designs the **Multi-Agent Runtime** layer. It coordinates a team of specialist agents (Planner, Architect, Coder, Reviewer, etc.) using an Agent Registry, capability matching, dynamic locks, safe handoffs, heartbeats, and structured model outputs.

## 2. Background
Currently, AIWF has conceptual definitions for multiple agents (e.g., in `AGENTS.md` and `agents/` directories), but executions are coordinated via manual user command sequences or single-agent scripts. To support complex, multi-agent collaborations, the runtime must manage agent identities, lock resources during active agent execution, and allow clean handoffs.

## 3. Current Architecture Analysis
The current codebase has `agent_routing.py` and `skill_classifier.py` under `skills/workflow-runtime/scripts`.
- It performs basic classification of prompts to suggest a skill.
- It has definitions for `architect`, `planner`, `coder`, `reviewer`, `release-manager`.

## 4. Current Limitations
- **Manual Handover**: The user must explicitly run the next command or direct the next step.
- **No Resource Locks**: Multiple scripts could try to modify the same context concurrently, causing race conditions.
- **Vague Outputs**: LLM agents often output unstructured markdown text, which is hard for subsequent scripts to parse.

## 5. Objectives
- Implement an **Agent Registry** with capability descriptors.
- Support **Agent Handoffs** via runtime context updates.
- Enforce **Resource & State Locks** per agent.
- Validate **Structured JSON Outputs** from agent calls.

## 6. Functional Requirements
- **FR-01: Agent Registry**: Maintain profile metadata for all available agents (capabilities, schemas).
- **FR-02: Capability Matching**: Route tasks to the best agent based on task descriptions.
- **FR-03: Execution Dispatcher**: Run agent scripts or prompt chains in isolated subprocesses.
- **FR-04: Agent Locks**: Lock the session and specific files when an agent is executing.
- **FR-05: Handover Protocol**: Transition execution focus to another agent when a sub-task is complete.
- **FR-06: Heartbeat Monitor**: Monitor execution; raise alerts if an agent hangs.

## 7. Non-Functional Requirements
- **NFR-01: Dispatch Overhead**: Processing agent registration and routing must take `< 20ms`.
- **NFR-02: Output Integrity**: All agent completions must match their registered JSON schema.

## 8. Scope
- Agent Registry schema and routing module (`registry.py`).
- Agent execution dispatcher (`dispatcher.py`).
- Handoff logic and transition coordinator.
- Structured output verification.

## 9. Out of Scope
- Task scheduling logic (delegated to Task Graph Engine).
- CLI state locks (handled by Lease module).

## 10. Runtime Responsibilities
The Multi-Agent Runtime handles agent selection, configures their environment, validates output contracts, and updates lease ownership during transitions.

## 11. Components
- `AgentRegistry`: The repository of agent specs.
- `TaskDispatcher`: Launches and monitors agent processes.
- `HandoffCoordinator`: Executes handover hooks.
- `SchemaValidator`: Parses and validates agent return payloads.

## 12. Data Model
```json
{
  "agent_id": "coder-agent",
  "capabilities": ["code_generation", "refactoring"],
  "schemas": {
    "output": "coder_output_schema.json"
  },
  "status": "idle"
}
```

## 13. Runtime State
```
[Unregistered] ──> [Idle] ──(acquire lock)──> [Busy] ──(release / handover)──> [Idle]
```

## 14. Event Flow
1. Scheduler triggers task T1.
2. Dispatcher queries Registry for matching capability.
3. Coder Agent is selected. Lock is acquired on `.agents/state/context.json` for Coder.
4. Coder Agent executes task and generates output.
5. SchemaValidator checks the output JSON format.
6. HandoffCoordinator releases Coder lock and hands execution over to Reviewer.

## 15. Sequence Flow
- Dispatch -> Lock -> Run -> Validate -> Handover -> Unlock.

## 16. Dependencies
- State synchronization layer (from FEAT-051).

## 17. Integration Points
- CLI: `python workflow_runtime.py routing suggest`
- File: `.agents/state/agents.json`

## 18. Interaction with Executive Runtime
- The Executive loop uses the dispatcher to run the target agent and listens for handoff triggers to advance the cycle.

## 19. Interaction with other features
- Relies on **Task Graph Engine (FEAT-087)** to determine the next task parameters.
- Uses **Validation Runtime (FEAT-090)** to inspect task outputs.

## 20. Security Considerations
- Restrict agent access to authorized files only.
- Validate and sanitize all LLM JSON output to prevent injection.

## 21. Performance Considerations
- Pre-compile JSON schemas for rapid validation.

## 22. Scalability Considerations
- Design supports dynamic loading of third-party agent plugins.

## 23. Failure Scenarios
- **Agent Execution Hangs**: Heartbeat threshold exceeded -> trigger SIGKILL -> log failure.
- **JSON Validation Fails**: Trigger retry loop or escalate to User.

## 24. Recovery Strategy
On agent timeout, restore the workspace state using the pre-execution git snapshot and transition the task node state to `failed`.

## 25. Migration Strategy
Map existing linear commands (e.g. `memory-sync`, `brainstorm`) to virtual agents (e.g. `MemoryAgent`, `PlannerAgent`) to ensure compatibility.

## 26. Backward Compatibility
Fall back to standard stdout execution if an agent does not support structured JSON output schemas.

## 27. Risks
- Infinite loop handoffs between agents (e.g., Coder and Reviewer ping-ponging). Mitigated by capping max handoffs per task.

## 28. Alternative Designs
- **Option A**: All-in-one generic agent. (Rejected: lacks specialization and control).
- **Option B**: Multi-process TCP agent server. (Rejected: increases environment complexity).

## 29. Trade-offs
- Enforcing structured JSON outputs adds parsing complexity but guarantees script-level readability.

## 30. Acceptance Criteria
- [ ] AC-01: Correctly parse, validate, and extract structured JSON from agent responses.
- [ ] AC-02: Successfully block other agents from writing to state files during active execution.

## 31. Estimated Complexity
- Medium.

## 32. Blueprint Estimation
- 1 design blueprint (`docs/designs/FEAT-088_multi_agent_runtime.md`).

## 33. Recommended Implementation Order
Implement third, following the Task Graph Engine.
