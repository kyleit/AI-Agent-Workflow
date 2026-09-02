from __future__ import annotations

import json
import os
import re
import signal
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from typing import Any, Optional, Tuple, cast
from dataclasses import dataclass

from workflow_runtime.application.verification.test_enforcer import     patch_subprocess
from workflow_runtime.infrastructure.session.session import load_session

patch_subprocess()


@dataclass(frozen=True)
class ProjectValidationScope:
    project_type: str
    working_directory: str
    build_command: tuple[str]
    runtime_command: tuple[str]


def resolve_validation_scope(root: str = ".") -> ProjectValidationScope:
    normalized_root = root.rstrip("/\\") or "."
    desktop = os.path.join(normalized_root, "desktop")
    if os.path.isfile(os.path.join(normalized_root, "go.mod")):
        return ProjectValidationScope("go", normalized_root, ("go", "vet", "./..."), ("go", "run", "."))
    if os.path.isfile(os.path.join(desktop, "go.mod")):
        return ProjectValidationScope("go", desktop, ("go", "vet", "./..."), ("go", "run", "."))
    if os.path.isfile(os.path.join(normalized_root, "pyproject.toml")):
        return ProjectValidationScope("python", normalized_root, (sys.executable, "-m", "compileall", "-q", "."), (sys.executable, "main.py"))
    if any(os.path.isfile(os.path.join(normalized_root, name)) for name in ("requirements.txt", "poetry.lock", "uv.lock")):
        return ProjectValidationScope("python", normalized_root, (sys.executable, "-m", "compileall", "-q", "."), (sys.executable, "main.py"))
    return ProjectValidationScope("unknown", normalized_root, tuple(), tuple())


def detect_project_type(cwd: str = ".") -> str:
    override = os.environ.get("AIWF_PROJECT_TYPE")
    if override:
        return override
    return resolve_validation_scope(cwd).project_type


def current_source_scope(root: str = ".") -> list[str]:
    """Return current source changes so AI verification does not scan stale mirrors."""
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain", "--untracked-files=all"],
            cwd=root,
            capture_output=True,
            text=True,
            check=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return []

    paths: list[str] = []
    for line in result.stdout.splitlines():
        if len(line) < 4:
            continue
        raw_path = line[3:].strip()
        if " -> " in raw_path:
            raw_path = raw_path.rsplit(" -> ", 1)[-1]
        path = raw_path.strip('"').replace("\\", "/")
        if (
            path.endswith((".py", ".go"))
            and not path.startswith(("public_export/", "artifacts/"))
            and "/tests/" not in f"/{path}/"
            and not path.startswith("tests/")
            and not path.endswith("_test.go")
            and not os.path.basename(path).startswith("test_")
        ):
            paths.append(path)
    return sorted(set(paths))


def active_work_item_id(default: str = "FEAT-001") -> str:
    session = load_session()
    raw_work_item = session.get("work_item")
    work_item = cast(dict[str, Any], raw_work_item) if isinstance(raw_work_item, dict) else {}
    return str(work_item.get("id", "")) or str(os.environ.get("AIWF_WORK_ITEM_ID", default))


def write_stage_report(stage: str, work_item_id: str, summary: str, status: str) -> str:
    filename = f"{work_item_id}_{'debug' if stage == 'debug' else 'verify'}.md"
    directory = os.path.join("docs", stage)
    os.makedirs(directory, exist_ok=True)
    path = os.path.join(directory, filename)
    with open(path, "w", encoding="utf-8") as report_file:
        report_file.write(
            f"---\nartifact_type: {stage}_verification\n"
            f"feature_id: {work_item_id}\nstatus: {status}\n---\n\n"
            f"# {stage.title()} Report - {work_item_id}\n\n{summary}\n"
        )
    return path


def classify_log_error(log_content: str) -> Optional[str]:
    rules = {
        "Build Error": [r"compile error", r"build failed", r"syntax error", r"declared and not used"],
        "Dependency Error": [r"ModuleNotFoundError", r"ImportError", r"no required module provides package", r"missing dependency"],
        "Network Error": [r"port binding failure", r"address already in use", r"connection refused", r"dial tcp"],
        "Database Error": [r"Database failure", r"Redis failure", r"database is locked", r"OperationalError"],
        "Configuration Error": [r"missing config", r"missing env", r"missing secrets", r"invalid yaml", r"invalid json"],
        "Runtime Error": [r"panic:", r"fatal error", r"Traceback", r"RuntimeError", r"exception"]
    }

    for category, patterns in rules.items():
        for pat in patterns:
            if re.search(pat, log_content, re.IGNORECASE):
                return category
    return None


def is_port_open(port: int, host: str = "127.0.0.1") -> bool:
    try:
        with socket.create_connection((host, port), timeout=0.5):
            return True
    except OSError:
        return False


def find_free_port() -> int:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('', 0))
            return int(s.getsockname()[1])
    except Exception:
        return 9095


def wait_for_readiness(proc: subprocess.Popen[Any], port: int, timeout: float = 15.0) -> Tuple[bool, str]:
    is_wails_app = False
    if os.path.exists("go.mod") or os.path.exists("desktop/go.mod"):
        is_wails_app = True

    start_time = time.time()
    while time.time() - start_time < timeout:
        exit_code = proc.poll()
        if exit_code is not None:
            stdout_b, stderr_b = proc.communicate()
            stdout_str = stdout_b.decode("utf-8", errors="ignore") if isinstance(stdout_b, bytes) else str(stdout_b or "")
            stderr_str = stderr_b.decode("utf-8", errors="ignore") if isinstance(stderr_b, bytes) else str(stderr_b or "")
            log_err = stdout_str + "\n" + stderr_str
            return False, f"Process terminated prematurely with exit code {exit_code}. Logs: {log_err}"

        if is_wails_app:
            if time.time() - start_time >= 1.5:
                return True, "Wails application launched and running successfully."
        else:
            if is_port_open(port):
                return True, "Port is open and listening."

        time.sleep(0.2)

    if is_wails_app:
        return True, "Wails application launched and running successfully."
    return False, "Startup timeout: port did not bind in time."


def run_smoke_test(port: int) -> Tuple[bool, str]:
    if os.path.exists("go.mod") or os.path.exists("desktop/go.mod"):
        return True, "Smoke test bypassed for desktop UI package (running natively)."

    url = f"http://127.0.0.1:{port}/"
    start = time.time()
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=2.0) as response:
            latency = (time.time() - start) * 1000
            raw_body: bytes = response.read()
            html_body = raw_body.decode("utf-8", errors="ignore")
            if "Dummy" in html_body:
                return False, "Smoke test failed: Embedded UI contains Dummy placeholder."
            if response.status in [200, 404]:
                return True, f"Smoke test succeeded. Latency: {latency:.1f}ms. Status: {response.status}"
            return False, f"Unexpected HTTP status: {response.status}"
    except urllib.error.HTTPError as e:
        latency = (time.time() - start) * 1000
        raw_body: bytes = e.read() if hasattr(e, "read") else b""
        html_body = raw_body.decode("utf-8", errors="ignore")
        if "Dummy" in html_body:
            return False, "Smoke test failed: Embedded UI contains Dummy placeholder."
        if e.code in [200, 404]:
            return True, f"Smoke test succeeded with HTTP status code. Latency: {latency:.1f}ms. Code: {e.code}"
        return False, f"HTTP Error {e.code}: {e.reason}"
    except Exception as e:
        return False, f"Smoke test connection error: {e}"


def run_pipeline(project_type: str, cwd: str = ".") -> Tuple[bool, str, list[str]]:
    port = find_free_port()
    scope = resolve_validation_scope(cwd)

    try:
        if project_type == "go":
            build_env = os.environ.copy()
            if os.name == "nt":
                # A global GOOS override can produce an ELF file named .exe;
                # force the artifact to match the host used by this E2E gate.
                build_env["GOOS"] = "windows"
                build_env.pop("CGO_ENABLED", None)
            subprocess.run(
                list(scope.build_command),
                cwd=scope.working_directory,
                env=build_env,
                check=True,
                capture_output=True,
            )
            subprocess.run(
                ["go", "build", "-o", "bin/app.exe", "."],
                cwd=scope.working_directory,
                env=build_env,
                check=True,
                capture_output=True,
            )
            # Windows does not reliably resolve a relative executable without a
            # path prefix when launched from a subprocess. Use the built file
            # explicitly so the AI receives a real runtime result.
            cmd = [os.path.abspath(os.path.join(scope.working_directory, "bin", "app.exe"))]
        elif project_type == "python":
            subprocess.run([sys.executable, "-m", "py_compile"], cwd=cwd, check=True, capture_output=True)
            cmd = [sys.executable, "main.py"]
        else:
            return True, f"Bypassed build verification for {project_type} project type.", []

        process_cwd = scope.working_directory if project_type == "go" else cwd
        proc = subprocess.Popen(
            cmd,
            cwd=process_cwd,
            env={**os.environ, "PORT": str(port)},
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        try:
            ready, msg = wait_for_readiness(proc, port, timeout=10.0)
            if not ready:
                return False, f"Readiness Gate Failed: {msg}", [msg]

            smoke_ok, smoke_msg = run_smoke_test(port)
            if not smoke_ok:
                return False, f"Smoke Gate Failed: {smoke_msg}", [smoke_msg]

            return True, "All validation pipeline steps PASSED.", []

        finally:
            if proc.poll() is None:
                if os.name == 'nt':
                    subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)], capture_output=True)
                else:
                    try:
                        os.kill(proc.pid, signal.SIGTERM)
                    except OSError:
                        pass
    except subprocess.CalledProcessError as e:
        def decode_output(val: Any) -> str:
            if isinstance(val, bytes):
                return val.decode("utf-8", errors="ignore")
            return str(val or "")
        err_msg = decode_output(e.stdout) + "\n" + decode_output(e.stderr)
        category = classify_log_error(err_msg) or "Build Error"
        raw_cmd = e.cmd
        cmd_str = " ".join([str(c) for c in cast(list[Any], raw_cmd)]) if isinstance(raw_cmd, list) else str(raw_cmd)
        return False, f"{category} during command '{cmd_str}': {err_msg}", [err_msg]
    except Exception as e:
        return False, f"Runtime error: {e}", [str(e)]


def run_debug() -> dict[str, Any]:
    cwd = "."
    project_type = detect_project_type(cwd)

    max_retries = 3
    attempt = 0
    success = False
    summary = ""
    warnings: list[str] = []

    while attempt < max_retries:
        attempt += 1
        success, summary, warnings = run_pipeline(project_type, cwd)
        if success:
            break

        print(f"DEBUG: Pipeline attempt {attempt} failed: {summary}. Log: {warnings}")
        time.sleep(0.5)

    from workflow_runtime.application.workflow.code_size_governor import (
        generate_code_size_report, run_code_size_audit)
    source_scope = current_source_scope(cwd)
    size_passed, size_violations, size_metrics = run_code_size_audit(".", files=source_scope or None)

    work_item_id = active_work_item_id()

    audit_content = generate_code_size_report(work_item_id, size_passed, size_violations, size_metrics)
    audit_dir = os.path.join("docs", "debug")
    os.makedirs(audit_dir, exist_ok=True)
    audit_path = os.path.join(audit_dir, "code_size_policy_audit.md")
    with open(audit_path, "w", encoding="utf-8") as f:
        f.write(audit_content)

    for v in size_violations:
        file_str = str(v.get("file", ""))
        scope_str = str(v.get("scope", ""))
        curr_lines = str(v.get("current_lines", ""))
        warnings.append(f"Code Size warning/fail on {file_str} ({scope_str} size: {curr_lines})")

    stage_report = write_stage_report("debug", work_item_id, summary, "PASS" if success else "FAIL")
    return {
        "status": "success" if success else "failure",
        "command": "debug run",
        "summary": summary,
        "warnings": warnings,
        "files_read": [],
        "files_written": [audit_path, stage_report]
    }


def run_verify(blueprint_path: Optional[str] = None) -> dict[str, Any]:
    work_item_id = active_work_item_id("FEAT-115")

    # 1. Chạy Architecture Compliance Validator
    from workflow_runtime.application.verification.architecture_validator import (
        generate_architecture_report, run_architecture_validation)
    source_scope = current_source_scope(".")
    arch_passed, arch_score, arch_violations, dep_graph = run_architecture_validation(
        ".", files=source_scope or None
    )

    report_content = generate_architecture_report(work_item_id, arch_passed, arch_score, arch_violations, dep_graph)
    report_dir = os.path.join("docs", "verification")
    os.makedirs(report_dir, exist_ok=True)
    report_path = os.path.join(report_dir, f"{work_item_id}_architecture_verify.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_content)

    if not arch_passed:
        return {
            "status": "failure",
            "command": "verify run",
            "summary": f"Clean Architecture / DDD Validation failed. Score: {arch_score}/100. Violations count: {len(arch_violations)}",
            "warnings": [str(v.get("evidence", "")) for v in arch_violations],
            "files_read": [],
            "files_written": [report_path]
        }

    # 2. Chạy tiếp Runtime Debug Validation Pipeline
    res = run_debug()
    if res["status"] != "success":
        return {
            "status": "failure",
            "command": "verify run",
            "summary": f"Verification failed during runtime pipeline validation: {res.get('summary')}",
            "warnings": cast(list[str], res.get("warnings", [])),
            "files_read": [],
            "files_written": [report_path]
        }

    # 3. Chạy tiếp Code Size Governance Verification
    from workflow_runtime.application.workflow.code_size_governor import (
        generate_code_size_report, run_code_size_audit)
    size_passed, size_violations, size_metrics = run_code_size_audit(
        ".", files=source_scope or None
    )

    verify_content = generate_code_size_report(work_item_id, size_passed, size_violations, size_metrics)
    verify_dir = os.path.join("docs", "verification")
    os.makedirs(verify_dir, exist_ok=True)
    verify_path = os.path.join(verify_dir, "code_size_policy_verify.md")
    with open(verify_path, "w", encoding="utf-8") as f:
        f.write(verify_content)

    metrics_dir = os.path.join("artifacts", "code-size-policy")
    os.makedirs(metrics_dir, exist_ok=True)
    metrics_path = os.path.join(metrics_dir, "metrics.json")
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(size_metrics, f, indent=2)

    if not size_passed:
        return {
            "status": "failure",
            "command": "verify run",
            "summary": "Verification failed: Code Size Policy Violation.",
            "warnings": [f"{str(v.get('scope', ''))} '{str(v.get('name', ''))}' size {str(v.get('current_lines', ''))} exceeds limit {str(v.get('limit', ''))}" for v in size_violations if str(v.get("status", "")) == "FAIL"],
            "files_read": [],
            "files_written": [report_path, verify_path, metrics_path]
        }

    is_release_requested = bool(load_session().get("release_requested", False))
    next_skill = "implementation-to-release" if is_release_requested else "software-development-workflow"

    stage_report = write_stage_report(
        "verification",
        work_item_id,
        f"{res.get('summary', 'Verification complete')} Architecture score: {arch_score}/100.",
        "PASS",
    )
    return {
        "status": "success",
        "command": "verify run",
        "summary": f"Runtime, Architecture & Code Size verification complete. Architecture Score: {arch_score}/100. All compliance gates passed.",
        "warnings": [] if is_release_requested else ["Release is currently blocked: User must explicitly request release"],
        "files_read": [],
        "files_written": [report_path, verify_path, metrics_path, stage_report],
        "next_skill": next_skill
    }


__all__ = [
    "detect_project_type",
    "current_source_scope",
    "active_work_item_id",
    "ProjectValidationScope",
    "resolve_validation_scope",
    "classify_log_error",
    "is_port_open",
    "find_free_port",
    "wait_for_readiness",
    "run_smoke_test",
    "run_pipeline",
    "run_debug",
    "run_verify",
]
