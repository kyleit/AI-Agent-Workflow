from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from typing import Any, cast


def _ensure_test_import_paths(workspace_root: str) -> None:
    roots = [
        "skills/workflow-runtime",
        "skills/workflow-runtime/workflow_runtime/application/use_cases",
        "skills/workflow-runtime/workflow_runtime/application/dependency",
        "skills/workflow-runtime/workflow_runtime/application/analysis",
        "skills/workflow-runtime/workflow_runtime/infrastructure/persistence",
        "skills/workflow-runtime/workflow_runtime/domain/security",
        "skills/knowledge-runtime/scripts",
    ]
    existing: list[str] = []
    for rel in roots:
        path = os.path.abspath(os.path.join(workspace_root, rel))
        if os.path.exists(path):
            existing.append(path)
            if path not in sys.path:
                sys.path.insert(0, path)
    current = os.environ.get("PYTHONPATH", "")
    parts = [part for part in current.split(os.pathsep) if part]
    merged: list[str] = existing + [part for part in parts if part not in existing]
    os.environ["PYTHONPATH"] = os.pathsep.join(merged)


def _skill_has_testable_runtime(skill_name: str) -> bool:
    if skill_name == "knowledge-runtime":
        return os.path.exists(os.path.join("skills", skill_name, "scripts", "knowledge_runtime"))
    return True


def do_test_action(args: Any) -> None:
    from workflow_runtime.application.analysis.tia_engine import (
        TestImpactResolver, validate_test_architecture)
    from workflow_runtime.application.verification.test_coordinator import \
        TestCoordinator
    from workflow_runtime.infrastructure.session.session import load_session
    from workflow_runtime.infrastructure.session.session_lock import \
        load_runtime_policy

    subaction = getattr(args, 'action', None) or getattr(args, 'subaction', None)
    force = bool(getattr(args, "force", False))

    try:
        policy = load_runtime_policy(validate=True)
        te_cfg: dict[str, Any] = cast(dict[str, Any], policy.get("test_execution", {})) if isinstance(policy.get("test_execution"), dict) else {}
    except Exception as e:
        print(f"Error loading/validating runtime policy: {e}", file=sys.stderr)
        sys.exit(1)

    if not subaction:
        subaction = "smoke"

    coordinator = TestCoordinator(".")
    _ensure_test_import_paths(".")

    if subaction == "validate":
        res = validate_test_architecture(".")
        if res.get("status") == "success":
            print(json.dumps({
                "status": "success",
                "summary": "Validation succeeded: Test architecture conforms to all rules.",
                "errors": []
            }, indent=2))
            sys.exit(0)
        else:
            print(json.dumps({
                "status": "failed",
                "summary": "Validation failed: Static architecture checks failed.",
                "errors": res.get("errors", [])
            }, indent=2), file=sys.stderr)
            sys.exit(1)

    if subaction == "limits":
        metrics = coordinator.get_resource_metrics()
        rl: dict[str, Any] = cast(dict[str, Any], policy.get("resource_limits", {})) if isinstance(policy.get("resource_limits"), dict) else {}
        print(json.dumps({
            "status": "success",
            "current_usage": metrics,
            "limits": {
                "cpu_throttle_percent": rl.get("cpu_throttle_percent", 80),
                "memory_throttle_percent": rl.get("memory_throttle_percent", 80),
                "max_parallel_pytest_processes": te_cfg.get("max_parallel_pytest_processes", 1),
                "max_pytest_workers": te_cfg.get("max_pytest_workers", 2)
            }
        }, indent=2))
        return

    if subaction in ["status", "queue"]:
        load_fn: Any = getattr(coordinator, "_load_coordinator_state", None)
        state: dict[str, Any] = cast(dict[str, Any], load_fn()) if callable(load_fn) else {}
        print(json.dumps(state, indent=2))
        return

    if subaction == "cancel":
        run_id = getattr(args, "run_id", None)
        if not run_id:
            print("Error: Please specify run_id to cancel.", file=sys.stderr)
            sys.exit(1)

        from workflow_runtime.infrastructure.session.session import OSFileLock
        lock = OSFileLock(coordinator.lock_path)
        while not lock.acquire():
            time.sleep(0.1)
        try:
            load_fn: Any = getattr(coordinator, "_load_coordinator_state", None)
            save_fn: Any = getattr(coordinator, "_save_coordinator_state", None)
            state_raw: Any = load_fn() if callable(load_fn) else {}
            state: dict[str, Any] = cast(dict[str, Any], state_raw) if isinstance(state_raw, dict) else {}

            found = False
            raw_active = state.get("active_runs")
            active_runs: list[dict[str, Any]] = cast(list[dict[str, Any]], raw_active) if isinstance(raw_active, list) else []
            for run in active_runs:
                if run.get("run_id") == run_id:
                    try:
                        import psutil
                        pid = cast(int, run.get("pid", 0))
                        parent = psutil.Process(pid)
                        for child in parent.children(recursive=True):
                            child.kill()
                        parent.kill()
                    except Exception:
                        pass
                    found = True
                    break
            raw_queue = state.get("queue")
            queue_list: list[dict[str, Any]] = cast(list[dict[str, Any]], raw_queue) if isinstance(raw_queue, list) else []
            state["queue"] = [item for item in queue_list if item.get("run_id") != run_id]
            state["active_runs"] = [run for run in active_runs if run.get("run_id") != run_id]
            if callable(save_fn):
                save_fn(state)
            if found:
                print(f"Successfully cancelled run {run_id}.")
            else:
                print(f"Run {run_id} not found or already completed.")
        finally:
            lock.release()
        return

    if subaction == "logs":
        run_id = getattr(args, "run_id", None)
        if not run_id:
            print("Error: Please specify run_id to fetch logs.", file=sys.stderr)
            sys.exit(1)
        log_path = os.path.join("artifacts", "test-runs", str(run_id), "stdout.log")
        if os.path.exists(log_path):
            with open(log_path, "r", encoding="utf-8") as f:
                print(f.read())
        else:
            print(f"No logs found for run {run_id} at {log_path}.", file=sys.stderr)
        return

    allowed, err_msg = coordinator.check_rate_limit()
    if not allowed:
        print(json.dumps({
            "status": "failed",
            "summary": f"Test run blocked: {err_msg}",
            "errors": [err_msg]
        }, indent=2), file=sys.stderr)
        sys.exit(1)

    resolver = TestImpactResolver()
    changed_files = resolver.get_git_changed_files()

    test_targets: list[str] = []

    if subaction == "affected":
        test_targets = resolver.resolve_affected_tests(changed_files)
    elif subaction == "module":
        mod_fn: Any = getattr(coordinator, "resolve_module_tests", None)
        test_targets = cast(list[str], mod_fn(changed_files)) if callable(mod_fn) else []
    elif subaction == "integration":
        integ_fn: Any = getattr(coordinator, "resolve_integration_tests", None)
        test_targets = cast(list[str], integ_fn()) if callable(integ_fn) else []
    elif subaction in ["unit", "smoke", "browser", "e2e"]:
        skills_root = "skills"
        if os.path.exists(skills_root):
            for skill in os.listdir(skills_root):
                if not _skill_has_testable_runtime(skill):
                    continue
                t_dir = os.path.join(skills_root, skill, "tests", str(subaction))
                if os.path.exists(t_dir):
                    for root, _, files in os.walk(t_dir):
                        for file in files:
                            if file.startswith("test_") and file.endswith(".py"):
                                rel_path = os.path.relpath(os.path.join(root, file), ".")
                                test_targets.append(rel_path.replace("\\", "/"))
        test_targets = sorted(list(set(test_targets)))
    elif subaction == "changed":
        test_targets = sorted(list(set([f.replace("\\", "/") for f in changed_files if os.path.basename(f).startswith("test_") and f.endswith(".py")])))
    elif subaction in ["full", "all"]:
        if te_cfg.get("full_suite_only_at_final_verification", True) and not force:
            session = load_session()
            current_skill = str(session.get("current_skill")) if session else None
            if current_skill not in ["verification", "final-review", "final_review", "debug-to-verify", "vir-verify"]:
                print(json.dumps({
                    "status": "failed",
                    "summary": "Execution of full test suite is restricted to the final review/verification phase under the current Runtime Policy.",
                    "errors": ["Full test suite execution restricted by Runtime Policy."]
                }, indent=2), file=sys.stderr)
                sys.exit(1)
        skills_root = "skills"
        if os.path.exists(skills_root):
            for skill in os.listdir(skills_root):
                if not _skill_has_testable_runtime(skill):
                    continue
                t_dir = os.path.join(skills_root, skill, "tests")
                if os.path.exists(t_dir):
                    for root, _, files in os.walk(t_dir):
                        for file in files:
                            if file.startswith("test_") and file.endswith(".py"):
                                rel_path = os.path.relpath(os.path.join(root, file), ".")
                                test_targets.append(rel_path.replace("\\", "/"))
        test_targets = sorted(list(set(test_targets)))

    elif subaction == "stability":
        lock_files = [f for f in changed_files if "lock" in f.lower() or "concurrency" in f.lower() or "lease" in f.lower() or "state_store" in f.lower()]
        if lock_files:
            test_targets = ["skills/workflow-runtime/tests/concurrency/test_lock.py"]
        else:
            test_targets = resolver.resolve_affected_tests(changed_files)

        if not test_targets:
            test_targets = ["skills/workflow-runtime/tests/smoke/test_smoke.py"]

        if getattr(args, "run_stability_worker", False):
            stab_fn: Any = getattr(coordinator, "run_stability_worker", None)
            if callable(stab_fn):
                stab_fn(test_targets, max_runs=100)
            return
        else:
            cli_path = os.path.abspath(__file__)
            background_cmd = [sys.executable, cli_path, "test", "stability", "--run-stability-worker"]
            _p = subprocess.Popen(background_cmd, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0, close_fds=True)
            print("[INFO] Launched stability runs in background worker. Logging output to artifacts/test-runs/stability_*")
            return

    if not test_targets:
        print(json.dumps({
            "status": "success",
            "message": f"No tests resolved for mode '{subaction}'.",
            "changed_files": changed_files,
            "selected_tests": []
        }, indent=2))
        return

    cmd: list[str] = [sys.executable, "-m", "pytest"] + test_targets

    try:
        ret_code, _stdout, _stderr = coordinator.run_coordinated(cmd, test_mode=str(subaction), test_scope=",".join(test_targets), force=force)
        sys.exit(ret_code)
    except Exception as e:
        print(f"Error running tests: {e}", file=sys.stderr)
        sys.exit(1)


__all__ = [
    "do_test_action",
]
