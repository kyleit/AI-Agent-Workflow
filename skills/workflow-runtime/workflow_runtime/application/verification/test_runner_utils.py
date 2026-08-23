from __future__ import annotations

import os
import subprocess
import sys
import time
from typing import Any, cast


def kill_process_tree(pid: int, timeout: float = 5.0) -> None:
    """
    Safely and recursively kill a process tree.
    Adheres to: terminate children -> wait -> kill surviving children -> terminate parent -> wait -> kill parent.
    Handles psutil errors and prevents PID reuse bugs by capturing process creation times.
    """
    import psutil

    try:
        parent = psutil.Process(pid)
        parent_create_time = float(parent.create_time())
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return

    def is_same_process(p: Any, expected_create_time: float) -> bool:
        try:
            return bool(getattr(p, "is_running")()) and abs(float(getattr(p, "create_time")()) - expected_create_time) <= 1.0
        except Exception:
            return False

    children_info: list[tuple[Any, float]] = []
    try:
        children = cast(list[Any], getattr(parent, "children")(recursive=True))
        for child in children:
            try:
                ctime = float(getattr(child, "create_time")())
                children_info.append((child, ctime))
            except Exception:
                pass
    except Exception:
        pass

    # 1. Terminate children
    for child, ctime in children_info:
        if is_same_process(child, ctime):
            try:
                getattr(child, "terminate")()
            except Exception:
                pass

    # Wait for children to exit
    child_wait_start = time.time()
    child_timeout = timeout / 2.0
    while time.time() - child_wait_start < child_timeout:
        alive_children = [c for c, ctime in children_info if is_same_process(c, ctime)]
        if not alive_children:
            break
        time.sleep(0.1)

    # 2. Kill surviving children
    for child, ctime in children_info:
        if is_same_process(child, ctime):
            try:
                getattr(child, "kill")()
            except Exception:
                pass

    # 3. Terminate parent
    if is_same_process(parent, parent_create_time):
        try:
            parent.terminate()
        except Exception:
            pass

    # Wait for parent to exit
    parent_wait_start = time.time()
    parent_timeout = timeout / 2.0
    while time.time() - parent_wait_start < parent_timeout:
        if not is_same_process(parent, parent_create_time):
            break
        time.sleep(0.1)

    # 4. Kill parent
    if is_same_process(parent, parent_create_time):
        try:
            parent.kill()
        except Exception:
            pass


def resolve_module_tests(changed_files: list[str]) -> list[str]:
    affected_skills: set[str] = set()
    for f in changed_files:
        norm_f = f.replace("\\", "/").lower()
        if "workflow-runtime" in norm_f:
            affected_skills.add("workflow-runtime")
        if "knowledge-runtime" in norm_f:
            affected_skills.add("knowledge-runtime")

    if not affected_skills:
        affected_skills.add("workflow-runtime")

    if "workflow-runtime" in affected_skills:
        affected_skills.add("knowledge-runtime")

    test_targets: list[str] = []
    for skill in affected_skills:
        test_dir = f"skills/{skill}/tests"
        if os.path.exists(test_dir):
            for root, _, files in os.walk(test_dir):
                for file in files:
                    if file.startswith("test_") and file.endswith(".py"):
                        rel_path = os.path.relpath(os.path.join(root, file), ".")
                        test_targets.append(rel_path.replace("\\", "/"))
    return sorted(list(set(test_targets)))


def resolve_integration_tests() -> list[str]:
    test_targets: list[str] = []
    for skill in ["workflow-runtime", "knowledge-runtime"]:
        integration_dir = f"skills/{skill}/tests/integration"
        if os.path.exists(integration_dir):
            for root, _, files in os.walk(integration_dir):
                for file in files:
                    if file.startswith("test_") and file.endswith(".py"):
                        rel_path = os.path.relpath(os.path.join(root, file), ".")
                        test_targets.append(rel_path.replace("\\", "/"))
    return sorted(list(set(test_targets)))


def run_stability_worker(test_targets: list[str], max_runs: int = 100) -> None:
    run_id = f"stability_{int(time.time())}"
    log_dir = os.path.abspath(os.path.join("artifacts", "test-runs", run_id))
    os.makedirs(log_dir, exist_ok=True)

    stdout_log_path = os.path.join(log_dir, "stdout.log")

    print(f"[BACKGROUND] Stability test worker started. Run ID: {run_id}. Logging to: {stdout_log_path}")

    passed_runs = 0
    failed_runs = 0

    for i in range(1, max_runs + 1):
        cmd = [sys.executable, "-m", "pytest"] + test_targets + ["-v"]

        msg = f"--- Iteration {i}/{max_runs} starting ---\n"
        with open(stdout_log_path, "a", encoding="utf-8") as log_file:
            log_file.write(msg)

        start_time = time.time()
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

        if p.stdout:
            for line in p.stdout:
                with open(stdout_log_path, "a", encoding="utf-8") as log_file:
                    log_file.write(line)

        p.wait()
        duration = round(time.time() - start_time, 2)

        if p.returncode == 0:
            passed_runs += 1
            status = "PASSED"
        else:
            failed_runs += 1
            status = "FAILED"

        summary_msg = f"--- Iteration {i}/{max_runs} {status} in {duration}s ---\n\n"
        with open(stdout_log_path, "a", encoding="utf-8") as log_file:
            log_file.write(summary_msg)

        time.sleep(1)

    final_msg = f"=== STABILITY COMPLETED: {passed_runs} PASSED, {failed_runs} FAILED ===\n"
    with open(stdout_log_path, "a", encoding="utf-8") as log_file:
        log_file.write(final_msg)

    print(f"[BACKGROUND] Stability test worker completed. Run ID: {run_id}. Passed: {passed_runs}, Failed: {failed_runs}.")


__all__ = [
    "kill_process_tree",
    "resolve_module_tests",
    "resolve_integration_tests",
    "run_stability_worker",
]
