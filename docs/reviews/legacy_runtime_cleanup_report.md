# Legacy Runtime Cleanup Report

This report outlines deprecated v1/v2 daemon execution components identified for phased deprecation and removal post-v3 deployment.

---

## 1. Deprecated Components Catalog

### A. Resident Daemon Logic (`runtime_daemon.py` / `daemon_controller.py`)
- **Purpose**: Managed resident background execution processes in v1/v2.
- **Current Usage**: None. Fully replaced by the in-process async `SessionCore`.
- **Action**: Deprecate immediately. Scheduled for deletion.
- **Removal Risk**: Low. No active client requests are mapped to daemon sockets.

### B. Process Agent Model (`process_agent.py`)
- **Purpose**: Spawns physical OS subprocesses for agent isolation.
- **Current Usage**: None. Replaced by `LogicalAgent` threads.
- **Action**: Deprecate.
- **Removal Risk**: Low.

### C. Old Orchestrator Flow (`legacy_orchestrator.py`)
- **Purpose**: Controlled workflow routing using polling loops.
- **Current Usage**: Backward compatibility adapter warning.
- **Action**: Keep adapter warning intact; scheduled for removal.

---

## 2. Transition Plan
1. Mark classes/modules with deprecation warnings.
2. Run regression tests verifying zero dependency on background processes.
3. Permanently remove code files in version `6.15.0`.
