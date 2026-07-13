---
artifact_type: implementation_plan
feature_id: FEAT-050-053
workflow: aiwf-hardening-campaign
status: approved
tracking_links:
  - https://gitlab.com/hngan.it/ai-workflow-skills
---

# Implementation Plan — Runtime Spawn Tree Profiler & OOM Root-Cause Audit

Audit and resolve resource exhaustion (CPU/RAM escalation and OOM) in the Resident Orchestrator daemon by building a spawn profiler, reproducing the failure on the latest code, identifying the root cause, and applying minimal safe fixes with defense-in-depth resource guards.

## Forensics & Root Cause Findings

> [!IMPORTANT]
> **1. OSFileLock Leak and Duplicate Daemons (Split-Brain)**
> - **Defect**: In `session.py`, `OSFileLock.acquire()` calls `self.release()` in its `except` block when it fails to lock. However, `release()` unconditionally closes the file handle and **deletes the lock file** on disk (`os.remove(self.lock_path)`).
> - **Impact**: Any CLI status check, init, or subagent checking daemon status will delete the running daemon's lock file. A subsequent CLI command will see no lock file, fail the PID process creation time drift check (if delta > 1.0s), bypass killing the active daemon, and spawn a duplicate daemon. This leads to multiple parallel daemons, conflicting file writes, watcher feedback loops, and rapid memory/CPU exhaustion.

> [!IMPORTANT]
> **2. Task Self-Blocking & Concurrency Deadlock**
> - **Defect**: When starting a task, the runtime marks it as `"running"`, then calls `can_spawn_subagent()`. In `can_spawn_subagent()`, it counts the active tasks including the current one. If CPU is reported as high (e.g. 100% on first call to `psutil.cpu_percent` without interval), adaptive concurrency reduces `max_concurrency` to 1.
> - **Impact**: The current task counts itself and exceeds the concurrency limit (1/1), resulting in self-blocking. It transitions to `"blocked"` and hangs the workflow loop forever because the daemon never re-reads the task graph from disk, and the mock runtime lacks an auto-recovery scheduler mechanism.

> [!IMPORTANT]
> **3. Pytest Timeout Cleanup Crash (Orphan Process Leak)**
> - **Defect**: In `test_coordinator.py`, on `subprocess.TimeoutExpired`, it attempts to import `kill_process_tree` from `conftest` which **does not exist** in any `conftest.py` in the workspace.
> - **Impact**: This throws an `ImportError` inside the timeout handling block, crashing the test coordinator thread, skipping the process termination (`p.kill()` / `p.wait()`), and leaving orphaned `pytest` / `pytest-xdist` worker processes running indefinitely.

---

## Proposed Changes & Refinements

### 1. Robust Resource Watermark & Throttle (No Hardcoded 200MB Limits)
We will dynamically calculate RAM limits in the daemon loop based on:
- Centralized policy config `max_runtime_rss_mb` (default 300MB if not specified).
- System RAM percentage throttle limit (`memory_throttle_percent`, default 80%).
- Process RSS baseline recorded at daemon startup + safe buffer (e.g., startup baseline + 150MB).
If memory usage exceeds any of these thresholds for 3 consecutive cycles, enter "Drain Mode" (suspend scheduling new tasks, yield CPU, and wait for memory/tasks to clear).

### 2. Lock Ownership & Metadata Safeguards
We will update `OSFileLock` in `session.py` to ensure it does not rely on deleting the file for unlocking. Lock ownership must be strictly validated:
- Maintain lock owner state: file handle holding the lock, PID, process creation time, and a unique `runtime_instance_id` (generated on start).
- Only the actual owner process is permitted to delete the lock file or clear the metadata lock.
- If a secondary process calls `acquire()` and fails, it must close its file handle but **never** delete the lock file or tamper with the active metadata.

### 3. Graceful Process Tree Termination with Timeout & Fallbacks
We will implement a robust `kill_process_tree(pid, timeout=5.0)` utility in `test_coordinator.py` adhering to this strict sequence:
- **Phase A (Children Terminate)**: Retrieve child processes of `pid` recursively. Send `SIGTERM` to all children.
- **Phase B (Children Wait & Kill)**: Wait for children to exit (up to `timeout/2` seconds). Send `SIGKILL` to any children still alive.
- **Phase C (Parent Terminate)**: Send `SIGTERM` to the parent process (`pid`).
- **Phase D (Parent Wait & Kill)**: Wait for parent to exit. Send `SIGKILL` to the parent if it remains active.
- Handle `psutil.NoSuchProcess`, `psutil.AccessDenied`, and prevent PID reuse bugs by validating process creation times.

---

## Proposed Code Modifications

### [Workflow Session Management & Locks]

#### [MODIFY] [session.py](../../skills/workflow-runtime/scripts/session.py)
- Refactor `OSFileLock` with ownership tracking (`self.locked`, `self.owner_pid`, `self.owner_create_time`, `self.runtime_instance_id`).
- Validate owner metadata before releasing/deleting files.

### [Workflow Runtime Core]

#### [MODIFY] [hierarchical_runtime.py](../../skills/workflow-runtime/scripts/hierarchical_runtime.py)
- **Baseline Capture**: Record initial RSS memory baseline at startup.
- **Dynamic Throttle**: Implement dynamic memory checks (RSS threshold, baseline buffer, system %).
- **Concurrency Correction**: Exclude the task currently being spawned from concurrency checks in `can_spawn_subagent()`.
- **Exception Safety**: Bounded `execute_subagent()` thread execution inside `try-finally`.

### [Test Coordination]

#### [MODIFY] [test_coordinator.py](../../skills/workflow-runtime/scripts/test_coordinator.py)
- Remove `from conftest import kill_process_tree`.
- Implement robust, multi-phase `kill_process_tree(pid)` with timeouts, fallback `SIGKILL`, and `psutil` error handling.

---

## Verification & Regression Plan

### 1. Regression Test Suite
We will add new automated unit tests in `skills/workflow-runtime/tests/` to verify:
- **Lock Protection**: Verify CLI `status` or parallel `init` calls do not delete or break the active daemon's lock.
- **Self-Blocking Prevention**: Validate that task execution does not self-block when concurrency limit is set to 1.
- **Timeout Leak Cleanup**: Mock a pytest timeout and assert that all subprocesses and child worker processes are successfully terminated (no orphan pytest or xdist workers left running).

### 2. Expanded Automated Test Verification
Run all three test suites to ensure zero regressions:
```bash
pytest -v -s skills/workflow-runtime/tests/unit 2>&1 | tee .agents/runtime/tests_unit.log
pytest -v -s skills/workflow-runtime/tests/concurrency 2>&1 | tee .agents/runtime/tests_concurrency.log
pytest -v -s skills/workflow-runtime/tests/integration 2>&1 | tee .agents/runtime/tests_integration.log
```

### 3. Long-Running Validation
Run the daemon idle and stress test loop for at least 15-20 minutes, monitoring the profiler to confirm:
- Exactly one Runtime Manager and one Resident Orchestrator are running.
- Heartbeats are written by a single active instance.
- Processes count remains stable and returns to baseline post-stress.
- Memory/RAM consumption reaches a stable plateau (no linear slope).
- No orphaned `pytest` or `xdist` processes exist after simulating test timeouts.
