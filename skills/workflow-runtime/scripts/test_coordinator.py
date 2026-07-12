# test_coordinator.py
import os
import sys
import json
import time
import uuid
import hashlib
import subprocess
from datetime import datetime

class TestCoordinator:
    def __init__(self, workspace_path: str = "."):
        self.workspace_root = os.path.abspath(workspace_path)
        self.state_dir = os.path.join(self.workspace_root, ".agents", "state")
        self.lock_path = os.path.join(self.state_dir, "pytest_coordinator.lock")
        self.exec_path = os.path.join(self.state_dir, "test-coordinator.json")
        os.makedirs(self.state_dir, exist_ok=True)
        
    def _load_coordinator_state(self) -> dict:
        if os.path.exists(self.exec_path):
            try:
                with open(self.exec_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        return data
            except Exception:
                pass
        return {"active_runs": [], "queue": []}

    def _save_coordinator_state(self, state: dict) -> None:
        try:
            with open(self.exec_path, "w", encoding="utf-8") as f:
                json.dump(state, f, indent=2)
        except Exception:
            pass

    def check_rate_limit(self) -> tuple[bool, str]:
        now = time.time()
        cb_path = os.path.join(self.state_dir, "circuit-breakers.json")
        cb_data = {
            "pytest_circuit": "closed",
            "updated_at": datetime.now().astimezone().isoformat()
        }
        if os.path.exists(cb_path):
            try:
                with open(cb_path, "r", encoding="utf-8") as f:
                    cb_data.update(json.load(f))
            except Exception:
                pass

        if cb_data.get("pytest_circuit") == "open":
            return False, "pytest circuit breaker is OPEN"

        history_path = os.path.join(self.state_dir, "pytest_history.json")
        history = []
        if os.path.exists(history_path):
            try:
                with open(history_path, "r", encoding="utf-8") as f:
                    history = json.load(f)
            except Exception:
                pass
        
        history = [t for t in history if now - t < 60]
        
        from session import load_config_section, DEFAULT_TEST_EXECUTION
        # Fallback to test_execution section
        from session import load_runtime_policy
        try:
            policy = load_runtime_policy(validate=True)
            te_cfg = policy.get("test_execution", {})
        except Exception:
            te_cfg = {}
            
        max_rate = te_cfg.get("max_requests_per_minute", 5)
        
        if len(history) >= max_rate:
            cb_data["pytest_circuit"] = "open"
            cb_data["updated_at"] = datetime.now().astimezone().isoformat()
            try:
                with open(cb_path, "w", encoding="utf-8") as f:
                    json.dump(cb_data, f, indent=2)
            except Exception:
                pass
            return False, "Rate limit exceeded (tripped circuit breaker)"
            
        history.append(now)
        try:
            with open(history_path, "w", encoding="utf-8") as f:
                json.dump(history, f)
        except Exception:
            pass
            
        return True, "OK"

    def get_resource_metrics(self) -> dict:
        import psutil
        try:
            cpu = psutil.cpu_percent(interval=None)
            ram = psutil.virtual_memory().percent
        except Exception:
            cpu = 0.0
            ram = 0.0
        return {"cpu": cpu, "ram": ram}

    def check_resources_ok(self, policy: dict) -> tuple[bool, str]:
        metrics = self.get_resource_metrics()
        te_cfg = policy.get("test_execution", {})
        
        cpu_limit = policy.get("resource_limits", {}).get("cpu_throttle_percent", 80)
        ram_limit = policy.get("resource_limits", {}).get("memory_throttle_percent", 80)
        
        if metrics["cpu"] > cpu_limit:
            return False, f"CPU usage is {metrics['cpu']}% (limit: {cpu_limit}%)"
        if metrics["ram"] > ram_limit:
            return False, f"RAM usage is {metrics['ram']}% (limit: {ram_limit}%)"
            
        return True, "OK"

    def run_coordinated(self, cmd: list[str], test_mode: str, test_scope: str, force: bool = False) -> tuple[int, str, str]:
        from session import load_runtime_policy, load_session, OSFileLock
        policy = load_runtime_policy(validate=True)
        te_cfg = policy.get("test_execution", {})
        
        # 1. Deduplication key
        session = load_session()
        project_id = session.get("project_id", "ai-skill-framework")
        work_item_id = session.get("work_item", {}).get("id") or os.environ.get("AIWF_WORK_ITEM_ID", "default_work_item")
        
        # Git revision
        git_rev = "unknown"
        try:
            git_rev = subprocess.check_output(["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL).decode().strip()
        except Exception:
            pass
            
        # Changed files hash
        from tia_engine import TestImpactResolver
        resolver = TestImpactResolver()
        changed = sorted(resolver.get_git_changed_files())
        changed_hash = hashlib.sha256(json.dumps(changed).encode()).hexdigest()[:16]
        
        dedup_raw = f"{project_id}:{work_item_id}:{test_mode}:{test_scope}:{git_rev}:{changed_hash}"
        dedup_key = hashlib.sha256(dedup_raw.encode("utf-8")).hexdigest()[:16]
        
        outcome_path = os.path.join(self.state_dir, f"test_outcome_{dedup_key}.json")
        
        # Check if identical successful run has already completed and outcome cache is valid
        if not force and os.path.exists(outcome_path):
            try:
                with open(outcome_path, "r", encoding="utf-8") as f:
                    cached = json.load(f)
                if cached.get("status") == "success":
                    print(f"[INFO] Reusing cached successful test result for dedup_key {dedup_key}.")
                    return cached.get("returncode", 0), cached.get("stdout", ""), cached.get("stderr", "")
            except Exception:
                pass
        
        run_id = f"run_{int(time.time())}_{uuid.uuid4().hex[:6]}"
        caller_pid = os.getpid()
        
        # 2. Acquire lock to modify state
        lock = OSFileLock(self.lock_path)
        while not lock.acquire():
            time.sleep(0.1)
            
        try:
            state = self._load_coordinator_state()
            
            # Check duplicate active run
            dedup_enabled = te_cfg.get("deduplicate_requests", True)
            if dedup_enabled:
                for run in state["active_runs"]:
                    if run.get("dedup_key") == dedup_key:
                        # Join as subscriber
                        run["subscribers"].append(caller_pid)
                        self._save_coordinator_state(state)
                        lock.release()
                        
                        print(f"[INFO] Subscribed to existing test run {run['run_id']}. Waiting for coalesced results...")
                        return self._wait_for_outcome(run["run_id"], outcome_path, run.get("pid"))
            
            # Not duplicate or dedup disabled: check process limit & resource limits
            max_parallel = te_cfg.get("max_parallel_pytest_processes", 1)
            
            # Clean up dead active runs first
            active_runs = []
            for run in state["active_runs"]:
                from lease import is_process_alive
                if is_process_alive(run["pid"]):
                    active_runs.append(run)
            state["active_runs"] = active_runs
            
            resources_ok, res_msg = self.check_resources_ok(policy)
            
            should_queue = len(active_runs) >= max_parallel or (not resources_ok and not force)
            
            if should_queue:
                queue_item = {
                    "run_id": run_id,
                    "pid": caller_pid,
                    "dedup_key": dedup_key,
                    "cmd": cmd,
                    "test_mode": test_mode,
                    "test_scope": test_scope,
                    "queued_at": datetime.now().astimezone().isoformat()
                }
                state["queue"].append(queue_item)
                self._save_coordinator_state(state)
                lock.release()
                
                print(f"[INFO] Test run {run_id} queued. Reason: " + ("Max process limit reached" if len(active_runs) >= max_parallel else res_msg))
                return self._wait_in_queue(run_id, dedup_key, outcome_path)
            
            # Start running immediately
            new_run = {
                "run_id": run_id,
                "pid": caller_pid,
                "dedup_key": dedup_key,
                "cmd": cmd,
                "test_mode": test_mode,
                "test_scope": test_scope,
                "subscribers": [caller_pid],
                "started_at": datetime.now().astimezone().isoformat()
            }
            state["active_runs"].append(new_run)
            self._save_coordinator_state(state)
        finally:
            if lock.is_held:
                lock.release()
                
        # 3. Execute test run
        return self._execute_pytest(run_id, cmd, dedup_key, outcome_path, te_cfg)

    def _wait_for_outcome(self, target_run_id: str, outcome_path: str, active_pid: int) -> tuple[int, str, str]:
        from lease import is_process_alive
        while True:
            if os.path.exists(outcome_path):
                try:
                    with open(outcome_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    if data.get("run_id") == target_run_id or not data.get("run_id"):
                        return data["returncode"], data["stdout"], data["stderr"]
                except Exception:
                    pass
            
            # If the active run process died, raise error
            if active_pid and not is_process_alive(active_pid) and not os.path.exists(outcome_path):
                return 1, "", f"Error: Active test run process {active_pid} died unexpectedly."
                
            time.sleep(0.5)

    def _wait_in_queue(self, run_id: str, dedup_key: str, outcome_path: str) -> tuple[int, str, str]:
        from session import OSFileLock, load_runtime_policy
        lock = OSFileLock(self.lock_path)
        
        while True:
            # Check if an identical run has already completed and written the outcome
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
                te_cfg = policy.get("test_execution", {})
                max_parallel = te_cfg.get("max_parallel_pytest_processes", 1)
                
                # Clean dead active runs
                active_runs = []
                from lease import is_process_alive
                for r in state["active_runs"]:
                    if is_process_alive(r["pid"]):
                        active_runs.append(r)
                state["active_runs"] = active_runs
                
                # Check if we are at the front of the queue
                queue = state.get("queue", [])
                my_idx = -1
                for idx, item in enumerate(queue):
                    if item["run_id"] == run_id:
                        my_idx = idx
                        break
                        
                if my_idx == -1:
                    # We were removed or processed?
                    lock.release()
                    return 1, "", "Error: Run removed from queue."
                    
                resources_ok, _ = self.check_resources_ok(policy)
                
                if my_idx == 0 and len(active_runs) < max_parallel and resources_ok:
                    # Transition to active
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

    def _execute_pytest(self, run_id: str, cmd: list[str], dedup_key: str, outcome_path: str, te_cfg: dict) -> tuple[int, str, str]:
        # Bounded worker configuration
        has_n = False
        for arg in cmd:
            if arg == "-n" or arg.startswith("-n"):
                has_n = True
                break
        if not has_n:
            workers = te_cfg.get("max_pytest_workers", 2)
            # Check if xdist is installed
            xdist_installed = False
            try:
                import xdist
                xdist_installed = True
            except ImportError:
                pass
            if xdist_installed and workers > 1:
                cmd.extend(["-n", str(workers)])
                
        # Persist full output path setup
        log_dir = os.path.join(self.workspace_root, "artifacts", "test-runs", run_id)
        os.makedirs(log_dir, exist_ok=True)
        
        stdout_log_path = os.path.join(log_dir, "stdout.log")
        stderr_log_path = os.path.join(log_dir, "stderr.log")
        summary_json_path = os.path.join(log_dir, "summary.json")
        metadata_json_path = os.path.join(log_dir, "metadata.json")
        junit_xml_path = os.path.join(log_dir, "junit.xml")
        
        cmd.extend(["--junitxml", junit_xml_path])
        
        print(f"Test Run: {run_id}")
        print(f"Mode: {te_cfg.get('default_mode', 'affected')}")
        print("Progress: START")
        
        stdout_buf = []
        stderr_buf = []
        
        start_time = time.time()
        timeout = te_cfg.get("timeout_seconds", 1800)
        
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)
        
        import threading
        # Thread to read stderr
        def read_stderr():
            for line in p.stderr:
                stderr_buf.append(line)
                
        t_err = threading.Thread(target=read_stderr, daemon=True)
        t_err.start()
        
        import re
        pct_regex = re.compile(r"\[\s*(\d+)%\]")
        printed_milestones = set()
        
        passed_count = 0
        failed_count = 0
        
        # Read stdout line by line for sparse progress logging
        try:
            for line in p.stdout:
                stdout_buf.append(line)
                
                # Count dots and Fs for live count estimation (simple parsing)
                if not line.startswith("=") and not line.startswith("skills") and "PASSED" not in line and "FAILED" not in line:
                    passed_count += line.count(".")
                    failed_count += line.count("F") + line.count("E")
                    
                match = pct_regex.search(line)
                if match:
                    percent = int(match.group(1))
                    interval = te_cfg.get("progress_log_interval_percent", 25)
                    milestone = (percent // interval) * interval
                    if milestone > 0 and milestone not in printed_milestones:
                        printed_milestones.add(milestone)
                        elapsed = int(time.time() - start_time)
                        print(f"Progress: {milestone}% | Passed: {passed_count} | Failed: {failed_count} | Elapsed: {elapsed}s")
                        sys.stdout.flush()
                        
            # Wait for completion or timeout
            p.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            print(f"Progress: FAIL (Timeout after {timeout}s)")
            if te_cfg.get("kill_process_tree_on_timeout", True):
                from conftest import kill_process_tree
                kill_process_tree(p.pid)
            p.kill()
            p.wait()
            
        duration = round(time.time() - start_time, 2)
        
        # Save raw outputs to disk
        stdout_str = "".join(stdout_buf)
        stderr_str = "".join(stderr_buf)
        
        try:
            with open(stdout_log_path, "w", encoding="utf-8") as f:
                f.write(stdout_str)
            with open(stderr_log_path, "w", encoding="utf-8") as f:
                f.write(stderr_str)
        except Exception:
            pass
            
        # Parse final summary counts from pytest summary line
        final_passed = passed_count
        final_failed = failed_count
        final_skipped = 0
        
        summary_line = ""
        for line in reversed(stdout_buf):
            if "passed" in line or "failed" in line or "error" in line:
                summary_line = line
                break
                
        if summary_line:
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
            "git_revision": git_rev,
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
            
        # Write outcome file for subscribers
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
            
        # 4. Remove active run from state
        from session import OSFileLock
        lock = OSFileLock(self.lock_path)
        while not lock.acquire():
            time.sleep(0.1)
        try:
            state = self._load_coordinator_state()
            state["active_runs"] = [r for r in state["active_runs"] if r["run_id"] != run_id]
            self._save_coordinator_state(state)
        finally:
            lock.release()
            
        # Cooldown sleep to protect resources
        cooldown = te_cfg.get("cooldown_seconds", 5)
        if cooldown > 0:
            time.sleep(cooldown)
            
        return p.returncode, stdout_str, stderr_str

def resolve_module_tests(changed_files: list[str]) -> list[str]:
    affected_skills = set()
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
        
    test_targets = []
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
    test_targets = []
    for skill in ["workflow-runtime", "knowledge-runtime"]:
        integration_dir = f"skills/{skill}/tests/integration"
        if os.path.exists(integration_dir):
            for root, _, files in os.walk(integration_dir):
                for file in files:
                    if file.startswith("test_") and file.endswith(".py"):
                        rel_path = os.path.relpath(os.path.join(root, file), ".")
                        test_targets.append(rel_path.replace("\\", "/"))
    return sorted(list(set(test_targets)))

def run_stability_worker(test_targets: list[str], max_runs: int = 100):
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
        
        # Read and log stdout to file
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
