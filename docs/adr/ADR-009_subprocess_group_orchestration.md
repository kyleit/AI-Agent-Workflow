<!-- File path: docs/adr/ADR-009_subprocess_group_orchestration.md -->

# ADR-009: Target Sandbox Orchestration using Asyncio Subprocess & Process Group Management

## Status
Accepted

## Related Feature
[FEAT-070: Visual Intelligence Runtime — Target Lifecycle & Sandbox Orchestrator](file:///e:/AgentsProject/docs/brainstorming/FEAT-070_vir_target_lifecycle_and_sandbox_orchestrator.md)

## Context
During verification runs, VIR must start compile commands and launch application servers (e.g. `npm run dev`), mock APIs, and databases. Because VIR is an automated AI runtime, if the target application compiles with errors or spawns background processes, standard node/process management commands can leave orphan or zombie processes bound to local ports. This prevents subsequent test runs, degrades resources on CI/CD runner machines, and triggers false verification results. We need a reliable cross-process manager that can run commands asynchronously and guarantee 100% cleanup of the entire subprocess tree.

## Decision
We will implement sandbox orchestration using Python's `asyncio.subprocess` API combined with process group OS routing:
- Spawned subprocesses will be initialized inside a dedicated **Process Group** (using `preexec_fn=os.setsid` on Unix or `creationflags=subprocess.CREATE_NEW_PROCESS_GROUP` on Windows).
- VIR will track process trees using PIDs and cross-platform tools (e.g. `psutil`).
- On termination, SIGTERM will be dispatched to the entire process group ID (PGID) rather than just the parent PID, ensuring all child processes (like node workers or database threads) are killed.
- Implement a 3-second timeout for graceful shutdown, followed by a forced `SIGKILL` cascade fallback for uncooperative processes.

## Alternatives Considered
- **Option A: Running shell commands directly without tracking:** Spawn shell wrappers (`sh` or `cmd.exe`) and let them exit. Rejected because killing the shell wrapper leaves child server processes running as orphans.
- **Option B: Docker containers for every run:** Wrap targets in Docker containers. Rejected because container build overhead (> 30s) violates the fast local execution mode target (< 1.5s startup). Local process execution is preferred for speed in local/IDE modes.

## Trade-offs
### Pros:
- **Fast Execution:** Spawning local processes has near-zero overhead, keeping startup under 1.5 seconds.
- **Orphan Prevention:** Process group mapping ensures child processes are cleaned up together.
- **Cross-platform:** Windows process group flags and Unix PGIDs are abstracted cleanly.

### Cons:
- **Platform Specifics:** Handling process flags differently on Windows vs Unix adds minor OS routing complexity.
- **Sandbox Limits:** Process-level isolation does not provide the same security guarantees as containers.

## Consequences
- The sandbox orchestrator must run with permissions sufficient to spawn and terminate local processes.
- Port allocation must be fully dynamic since we execute directly in host spaces.

## Risks
- **Subprocesses escaping group limits:** Double-forked daemon processes might escape the process group. *Mitigation:* System ports are checked after shutdown; alert if a port remains bound.

## References
- [VIR Index](file:///e:/AgentsProject/docs/brainstorming/VIR_ARCHITECTURE_BIBLE_INDEX.md)
- [FEAT-070](file:///e:/AgentsProject/docs/brainstorming/FEAT-070_vir_target_lifecycle_and_sandbox_orchestrator.md)
