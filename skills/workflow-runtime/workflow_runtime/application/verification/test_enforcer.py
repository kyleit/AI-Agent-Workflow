# test_enforcer.py
import inspect
import json
import os
import subprocess
import sys
from typing import Any, List, Tuple, cast

# Backup original subprocess functions
_orig_run = subprocess.run
_orig_Popen = subprocess.Popen

def is_test_command(cmd: Any) -> bool:
    if not cmd:
        return False
    cmd_list = []
    if isinstance(cmd, str):
        cmd_list = cmd.split()
    elif isinstance(cmd, (list, tuple)):
        cmd_list = [str(c) for c in cast(Any, cmd)]
    else:
        return False

    if cmd_list and os.path.basename(cmd_list[0]).lower() == "agy":
        cmd_list = _strip_agy_prompt_payload(cmd_list)

    cmd_str = " ".join(cmd_list).lower()

    test_executables = [
        "pytest", "unittest", "vitest", "jest", "playwright", "cypress",
        "go test", "cargo test", "npm test", "npm run test", "pnpm test", "yarn test"
    ]
    for te in test_executables:
        if te in cmd_str:
            return True

    test_scripts = [
        "test_", "run_tests", "test.sh", "test.ps1", "test.py"
    ]
    for ts in test_scripts:
        if ts in cmd_str:
            return True

    if "make" in cmd_str or "task" in cmd_str or "just" in cmd_str:
        if "test" in cmd_str:
            return True

    return False

def _strip_agy_prompt_payload(cmd_list: List[str]) -> List[str]:
    """Keep AGY command flags inspectable without treating prompt text as a test command."""
    sanitized: List[str] = []
    skip_next = False
    value_options = {
        "--add-dir",
        "--agent",
        "--conversation",
        "--effort",
        "--mode",
        "--model",
        "--print-timeout",
    }
    for token in cmd_list:
        if skip_next:
            skip_next = False
            continue
        if token == "--print":
            break
        sanitized.append(token)
        if token in value_options:
            skip_next = True
    return sanitized

def verify_tester_ownership(cmd: Any) -> Tuple[bool, str]:
    base_dir = os.environ.get("AIWF_BASE_DIR") or os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
    state_dir = os.path.join(base_dir, ".agents", "state")
    if not os.path.exists(state_dir):
        if not os.environ.get("AIWF_BASE_DIR"):
            state_dir = ".agents/state"

    tasks_path = os.path.join(state_dir, "tasks.json")
    agents_path = os.path.join(state_dir, "agents.json")

    if not os.path.exists(tasks_path):
        return False, "tasks.json ledger not found"

    try:
        with open(tasks_path, "r", encoding="utf-8") as f:
            tdata = json.load(f)
        tasks: dict[str, Any] = cast(dict[str, Any], tdata.get("tasks", {})) if isinstance(tdata.get("tasks"), dict) else {}
    except Exception as e:
        return False, f"Failed to parse tasks.json: {e}"

    agents: dict[str, Any] = {}
    if os.path.exists(agents_path):
        try:
            with open(agents_path, "r", encoding="utf-8") as f:
                agents = json.load(f)
        except Exception:
            pass

    running_test_tasks: list[tuple[str, dict[str, Any]]] = []
    for tid, t in tasks.items():
        if t.get("status") == "running":
            role = t.get("role", "").lower()
            name = t.get("name", "").lower()
            if role in ["testing", "verification"] or "test" in name or "verify" in name or "qa" in name:
                running_test_tasks.append((tid, t))

    if not running_test_tasks:
        return False, "No active running test task found in tasks.json"

    for tid, t in running_test_tasks:
        assigned = t.get("assigned_agent")
        if not assigned:
            continue
        agent_meta: dict[str, Any] = cast(dict[str, Any], agents.get(cast(str, assigned), {}))
        agent_type = str(agent_meta.get("type", ""))
        if agent_type in ["qa", "tester"] or assigned == "AGENT-TESTER-001" or "tester" in str(assigned).lower() or "qa" in str(assigned).lower():
            return True, f"Valid owner found: {assigned} for task {tid}"

    return False, "Running test task exists but is not owned by a QA or TESTER agent"

def is_cli_test_gateway_caller() -> bool:
    for frame_info in inspect.stack():
        filename = os.path.basename(frame_info.filename)
        if filename == "test_runner.py" and "presentation" in frame_info.filename and "cli" in frame_info.filename:
            return True
    return False

def is_caller_authorized() -> bool:
    stack = inspect.stack()
    for frame_info in stack:
        filename = os.path.basename(frame_info.filename)
        if filename == "test_enforcer.py":
            continue
        if filename == "execution_manager.py":
            return True
        if filename in [
            "workflow_runtime.py",
            "fingerprint.py",
            "init_wizard.py",
            "provider_data.py",
            "provider_config.py",
            "session_meta.py",
            "session_lifecycle.py",
            "shared_helpers.py",
            "runtime_bus.py",
            "execution_commands.py",
            "context_manager.py",
            "system_health.py",
            "environment_health.py",
            "workspace_doctor.py",
            "test_runner.py",
            "validator.py",
            "workflow_runtime_shared.py",
            # Memory & git infra — used by aiwf memory/runtime CLI commands
            "bootstrap.py",
            "update.py",
            "git_diff.py",
            "scanner.py",
            "analyzer.py",
            "sqlite_writer.py",
            "json_writer.py",
            "vector_manifest.py",
            "memory_manager.py",
            "memory_commands.py",
            "knowledge_search.py",
            "knowledge_commands.py",
            # Registry dispatch itself
            "registry.py",
            # System & infrastructure modules
            "benchmark_init_flow.py",
            "benchmark_exporter.py",
            "update_source.py",
            "update_framework.py",
            "update_source_core.py",
            "update_source_git.py",
            "patch_integration_queue.py",
            "safe_writes_controllers.py",
            "safe_writes_io.py",
            "safe_multi_agent_writes.py",
            "dependency_resolver.py",
            "dependency_scanner.py",
            "dispatch_agent.py",
            "test_coordinator.py",
            "test_session_coordinator.py",
            "handlers.py",
            "session_command_handlers.py",
            "workflow_command_handlers.py",
            "knowledge_command_handlers.py",
            "runtime_command_handlers.py",
        ]:
            return True
    return False

def patched_run(*args: Any, **kwargs: Any) -> Any:
    cmd = args[0] if args else kwargs.get("args")

    if is_caller_authorized():
        # Double check test ownership inside Execution Manager
        if is_test_command(cmd) and not is_cli_test_gateway_caller():
            allowed, msg = verify_tester_ownership(cmd)
            if not allowed:
                err_msg = f"Policy Violation: Test execution blocked. Reason: {msg} (Command: {cmd})"
                print(f"❌ {err_msg}", file=sys.stderr)
                raise PermissionError(err_msg)
        return cast(Any, _orig_run)(*args, **kwargs)

    # 0. Workflow Context Check (FEAT-308)
    import json
    session_path = os.path.abspath(os.path.join(".", ".agents", ".session.json"))
    session_data: dict[str, Any] = {}
    if os.path.exists(session_path):
        try:
            with open(session_path, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                if isinstance(loaded, dict):
                    session_data = cast(dict[str, Any], loaded)
        except Exception:
            pass

    execution_mode = os.environ.get("AIWF_EXECUTION_MODE") or session_data.get("execution_mode")
    workflow_id = os.environ.get("AIWF_WORKFLOW_ID") or session_data.get("workflow_id")

    force_enforce = os.environ.get("AIWF_FORCE_ENFORCE") == "true"
    bypass_enforcer = os.environ.get("AIWF_TESTING_BYPASS_ENFORCER") == "true"
    is_testing = bypass_enforcer or (not force_enforce and (
        os.environ.get("AIWF_TESTING") == "true"
        or "PYTEST_CURRENT_TEST" in os.environ
        or "pytest" in os.path.basename(sys.argv[0])
        or "unittest" in os.path.basename(sys.argv[0])
    ))
    if is_testing:
        return cast(Any, _orig_run)(*args, **kwargs)
    if not is_testing and (execution_mode != "workflow" or not workflow_id):
        err_msg = f"EXECUTION_BLOCKED: Engineering action outside Workflow Gateway. (Command: {cmd})"
        print(f"❌ {err_msg}", file=sys.stderr)
        raise PermissionError(err_msg)

    # If not authorized, check strict enforcement or redirect
    strict = os.environ.get("AIWF_STRICT_PROCESS_ENFORCEMENT") == "true"
    if strict:
        err_msg = f"Policy Violation: Direct OS Process creation blocked. All execution must go through Execution Manager. (Command: {cmd})"
        print(f"❌ {err_msg}", file=sys.stderr)
        raise PermissionError(err_msg)

    force_enforce = os.environ.get("AIWF_FORCE_ENFORCE") == "true"
    bypass_enforcer = os.environ.get("AIWF_TESTING_BYPASS_ENFORCER") == "true"
    is_testing = bypass_enforcer or (not force_enforce and (
        os.environ.get("AIWF_TESTING") == "true"
        or "PYTEST_CURRENT_TEST" in os.environ
        or "pytest" in os.path.basename(sys.argv[0])
        or "unittest" in os.path.basename(sys.argv[0])
    ))
    if is_testing:
        return cast(Any, _orig_Popen)(*args, **kwargs)

    # Transparent redirect through Execution Manager
    from workflow_runtime.application.use_cases.execution_manager import \
        ExecutionManager
    cmd_list = []
    if isinstance(cmd, str):
        cmd_list = cmd.split()
    elif isinstance(cmd, (list, tuple)):
        cmd_list = [str(c) for c in cast(Any, cmd)]

    cwd = kwargs.get("cwd", ".")
    timeout = kwargs.get("timeout", 300)

    owner_agent = os.environ.get("AIWF_ACTIVE_AGENT") or "AGENT-SYSTEM"
    task_id = os.environ.get("AIWF_ACTIVE_WORK_ITEM") or os.environ.get("AIWF_WORK_ITEM_ID") or "TASK-SYSTEM"

    print(f"🔄 [Redirect] Direct subprocess.run of {cmd} redirected through Execution Manager.", file=sys.stderr)
    return ExecutionManager.run_command_managed(cmd_list, cwd=cwd, owner_agent_id=owner_agent, task_id=task_id, timeout=timeout)

def patched_Popen(*args: Any, **kwargs: Any) -> Any:
    cmd = args[0] if args else kwargs.get("args")

    if is_caller_authorized():
        # Double check test ownership inside Execution Manager
        if is_test_command(cmd) and not is_cli_test_gateway_caller():
            allowed, msg = verify_tester_ownership(cmd)
            if not allowed:
                err_msg = f"Policy Violation: Test execution blocked. Reason: {msg} (Command: {cmd})"
                print(f"❌ {err_msg}", file=sys.stderr)
                raise PermissionError(err_msg)
        # Double check test ownership inside Execution Manager
        if is_test_command(cmd) and not is_cli_test_gateway_caller():
            allowed, msg = verify_tester_ownership(cmd)
            if not allowed:
                err_msg = f"Policy Violation: Test execution blocked. Reason: {msg} (Command: {cmd})"
                print(f"❌ {err_msg}", file=sys.stderr)
                raise PermissionError(err_msg)
        return cast(Any, _orig_Popen)(*args, **kwargs)

    # If not authorized, check strict enforcement or redirect
    strict = os.environ.get("AIWF_STRICT_PROCESS_ENFORCEMENT") == "true"
    if strict:
        err_msg = f"Policy Violation: Direct OS Process creation blocked. All execution must go through Execution Manager. (Command: {cmd})"
        print(f"❌ {err_msg}", file=sys.stderr)
        raise PermissionError(err_msg)

    force_enforce = os.environ.get("AIWF_FORCE_ENFORCE") == "true"
    bypass_enforcer = os.environ.get("AIWF_TESTING_BYPASS_ENFORCER") == "true"
    is_testing = bypass_enforcer or (not force_enforce and (
        os.environ.get("AIWF_TESTING") == "true"
        or "PYTEST_CURRENT_TEST" in os.environ
        or "pytest" in os.path.basename(sys.argv[0])
        or "unittest" in os.path.basename(sys.argv[0])
    ))
    if is_testing:
        return cast(Any, _orig_Popen)(*args, **kwargs)

    # Transparent redirect through Execution Manager
    from workflow_runtime.application.use_cases.execution_manager import \
        ExecutionManager
    cmd_list: list[str] = []
    if isinstance(cmd, str):
        cmd_list = cmd.split()
    elif isinstance(cmd, (list, tuple)):
        cmd_list = [str(c) for c in cast(Any, cmd)]

    cwd = cast(str, kwargs.get("cwd", "."))
    timeout = cast(int, kwargs.get("timeout", 300))
    stdout: Any = kwargs.get("stdout")
    stderr: Any = kwargs.get("stderr")
    preexec_fn: Any = kwargs.get("preexec_fn")
    creationflags = cast(int, kwargs.get("creationflags", 0))
    text = cast(bool, kwargs.get("text", True))
    bufsize = cast(int, kwargs.get("bufsize", -1))

    owner_agent = os.environ.get("AIWF_ACTIVE_AGENT") or "AGENT-SYSTEM"
    task_id = os.environ.get("AIWF_ACTIVE_WORK_ITEM") or os.environ.get("AIWF_WORK_ITEM_ID") or "TASK-SYSTEM"

    print(f"🔄 [Redirect] Direct subprocess.Popen of {cmd} redirected through Execution Manager.", file=sys.stderr)
    return cast(Any, ExecutionManager).popen_command_managed(
        cmd_list, cwd=cwd, owner_agent_id=owner_agent, task_id=task_id, timeout=timeout,
        stdout=stdout, stderr=stderr, preexec_fn=preexec_fn, creationflags=creationflags,
        text=text, bufsize=bufsize
    )

def patch_subprocess():
    subprocess.run = patched_run
    subprocess.Popen = patched_Popen
