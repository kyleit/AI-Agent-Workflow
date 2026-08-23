"""
workflow_runtime/application/verification/test_session_coordinator.py

Test session coordinator and execution queue manager.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import threading
import time
from datetime import datetime
from typing import Any, cast

from workflow_runtime.application.ports.locator import InfrastructureLocator
from workflow_runtime.application.verification.test_runner_utils import (
    kill_process_tree)
from workflow_runtime.infrastructure.session.session_lock import (
    load_runtime_policy)


class TestSessionCoordinator:
    """Session coordinator mixin for pytest execution and resource leases."""
    lock_path: str
    workspace_root: str = "."

    def _load_coordinator_state(self) -> dict[str, Any]:
        return {}

    def _save_coordinator_state(self, state: dict[str, Any]) -> None:
        pass

    def check_resources_ok(self, policy: dict[str, Any] | None = None) -> tuple[bool, str]:
        return True, "OK"

    def _wait_for_outcome(self, target_run_id: str, outcome_path: str, active_pid: int) -> tuple[int, str, str]:
        while True:
            if os.path.exists(outcome_path):
                try:
                    with open(outcome_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    if data.get("run_id") == target_run_id or not data.get("run_id"):
                        return data["returncode"], data["stdout"], data["stderr"]
                except Exception:
                    pass

            if active_pid and not InfrastructureLocator.is_process_alive(active_pid) and not os.path.exists(outcome_path):
                return 1, "", f"Error: Active test run process {active_pid} died unexpectedly."

            time.sleep(0.5)

    def _wait_in_queue(self, run_id: str, dedup_key: str, outcome_path: str) -> tuple[int, str, str]:
        lock = InfrastructureLocator.OSFileLock(self.lock_path)

        while True:
            if os.path.exists(outcome_path):
                try:
                    with open(outcome_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    return data["returncode"], data["stdout"], data["stderr"]
                except Exception:
                    pass

            while not lock.acquire():
                time.sleep(0.1)

            try:
                state = self._load_coordinator_state()
                policy = load_runtime_policy(validate=True)
                te_cfg = cast(dict[str, Any], policy.get("test_execution", {}))
                max_parallel = te_cfg.get("max_parallel_pytest_processes", 1)

                active_runs: list[dict[str, Any]] = []
                for r in state.get("active_runs", []):
                    if InfrastructureLocator.is_process_alive(r["pid"]):
                        active_runs.append(r)
                state["active_runs"] = active_runs

                queue: list[Any] = cast(list[Any], state.get("queue", [])) if isinstance(state.get("queue"), list) else []
                my_idx = -1
                for idx, item in enumerate(queue):
                    if item.get("run_id") == run_id:
                        my_idx = idx
                        break

                if my_idx == -1:
                    lock.release()
                    return 1, "", "Error: Run removed from queue."

                resources_ok, _ = self.check_resources_ok(policy)

                if my_idx == 0 and len(active_runs) < max_parallel and resources_ok:
                    item = queue.pop(0)
                    new_run = {
                        "run_id": run_id,
                        "pid": os.getpid(),
                        "dedup_key": dedup_key,
                        "cmd": item["cmd"],
                        "test_mode": item["test_mode"],
                        "test_scope": item["test_scope"],
                        "subscribers": [os.getpid()],
                        "started_at": datetime.now().astimezone().isoformat()
                    }
                    state["active_runs"].append(new_run)
                    state["queue"] = queue
                    self._save_coordinator_state(state)
                    lock.release()

                    print(f"[INFO] Transitioned from queue to active: {run_id}")
                    return self._execute_pytest(run_id, item["cmd"], dedup_key, outcome_path, te_cfg)
            finally:
                if lock.is_held:
                    lock.release()

            time.sleep(1.0)

    def _execute_pytest(self, run_id: str, cmd: list[str], dedup_key: str, outcome_path: str, te_cfg: dict[str, Any], test_mode: str = "affected") -> tuple[int, str, str]:
        has_n = False
        for arg in cmd:
            if arg == "-n" or arg.startswith("-n"):
                has_n = True
                break
        if not has_n:
            workers = int(te_cfg.get("max_pytest_workers", 2) or 2)
            if workers > 1:
                cmd.extend(["-n", str(workers)])

        log_dir = os.path.join(self.workspace_root, "artifacts", "test-runs", run_id)
        os.makedirs(log_dir, exist_ok=True)

        stdout_log_path = os.path.join(log_dir, "stdout.log")
        stderr_log_path = os.path.join(log_dir, "stderr.log")
        summary_json_path = os.path.join(log_dir, "summary.json")
        metadata_json_path = os.path.join(log_dir, "metadata.json")
        junit_xml_path = os.path.join(log_dir, "junit.xml")

        cmd.extend(["--junitxml", junit_xml_path])

        print(f"Test Run: {run_id}")
        print(f"Mode: {test_mode}")
        print("Progress: START")

        stdout_buf: list[str] = []
        stderr_buf: list[str] = []

        start_time = time.time()
        timeout = int(te_cfg.get("timeout_seconds", 1800) or 1800)

        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)

        def read_stderr():
            if p.stderr is not None:
                for line in p.stderr:
                    stderr_buf.append(str(line))

        t_err = threading.Thread(target=read_stderr, daemon=True)
        t_err.start()

        pct_regex = re.compile(r"\[\s*(\d+)%\]")
        printed_milestones: set[int] = set()

        passed_count = 0
        failed_count = 0

        line: str = ""
        try:
            if p.stdout is not None:
                for line in p.stdout:
                    stdout_buf.append(str(line))

                match = pct_regex.search(line)
                if match:
                    percent = int(match.group(1))
                    interval = int(te_cfg.get("progress_log_interval_percent", 25) or 25)
                    milestone = (percent // interval) * interval
                    if milestone > 0 and milestone not in printed_milestones:
                        printed_milestones.add(milestone)
                        elapsed = int(time.time() - start_time)
                        print(f"Progress: {milestone}% | Elapsed: {elapsed}s")
                        sys.stdout.flush()

            p.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            print(f"Progress: FAIL (Timeout after {timeout}s)")
            if te_cfg.get("kill_process_tree_on_timeout", True):
                kill_process_tree(p.pid)
            else:
                p.kill()
                p.wait()

        duration = round(time.time() - start_time, 2)

        stdout_str = "".join(stdout_buf)
        stderr_str = "".join(stderr_buf)

        try:
            with open(stdout_log_path, "w", encoding="utf-8") as f:
                f.write(stdout_str)
            with open(stderr_log_path, "w", encoding="utf-8") as f:
                f.write(stderr_str)
        except Exception:
            pass

        final_passed = passed_count
        final_failed = failed_count
        final_skipped = 0

        summary_line = ""
        for line in reversed(stdout_buf):
            if "passed" in line or "failed" in line or "error" in line:
                summary_line = line
                break

        if summary_line:
            final_passed = 0
            final_failed = 0
            final_skipped = 0
            passed_match = re.search(r"(\d+)\s+passed", summary_line)
            failed_match = re.search(r"(\d+)\s+failed", summary_line)
            error_match = re.search(r"(\d+)\s+error", summary_line)
            skipped_match = re.search(r"(\d+)\s+skipped", summary_line)

            if passed_match: final_passed = int(passed_match.group(1))
            if failed_match: final_failed = int(failed_match.group(1))
            if error_match: final_failed += int(error_match.group(1))
            if skipped_match: final_skipped = int(skipped_match.group(1))

        total_tests = final_passed + final_failed + final_skipped

        outcome_status = "success" if p.returncode == 0 else "failed"
        print(f"Progress: 100% | Status: {outcome_status.upper()} | Passed: {final_passed} | Failed: {final_failed} | Elapsed: {duration}s")

        metadata = {
            "test_run_id": run_id,
            "dedup_key": dedup_key,
            "status": outcome_status,
            "git_revision": getattr(self, "git_rev", "unknown"),
            "started_at": datetime.now().astimezone().isoformat(),
            "completed_at": datetime.now().astimezone().isoformat(),
            "elapsed_seconds": duration,
            "summary": {
                "passed": final_passed,
                "failed": final_failed,
                "skipped": final_skipped,
                "total": total_tests
            }
        }

        try:
            with open(metadata_json_path, "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2)
            with open(summary_json_path, "w", encoding="utf-8") as f:
                json.dump(metadata["summary"], f, indent=2)
        except Exception:
            pass

        outcome_data = {
            "run_id": run_id,
            "returncode": p.returncode,
            "stdout": stdout_str,
            "stderr": stderr_str,
            "completed_at": datetime.now().astimezone().isoformat()
        }
        try:
            with open(outcome_path, "w", encoding="utf-8") as f:
                json.dump(outcome_data, f, indent=2)
        except Exception:
            pass

        lock = InfrastructureLocator.OSFileLock(self.lock_path)
        while not lock.acquire():
            time.sleep(0.1)
        try:
            state = self._load_coordinator_state()
            state["active_runs"] = [r for r in state.get("active_runs", []) if r.get("run_id") != run_id]
            self._save_coordinator_state(state)
        finally:
            lock.release()

        cooldown = int(te_cfg.get("cooldown_seconds", 5) or 5)
        if cooldown > 0:
            time.sleep(cooldown)

        return p.returncode, stdout_str, stderr_str


__all__ = ["TestSessionCoordinator"]
