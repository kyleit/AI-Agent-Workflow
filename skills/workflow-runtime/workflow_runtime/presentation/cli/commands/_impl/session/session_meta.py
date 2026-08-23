from __future__ import annotations

import argparse
import json
import os
import sys
import time
from typing import Any


def _provider_runtime() -> Any:
    from workflow_runtime.presentation.cli.commands._impl.provider import         provider_data
    return provider_data


def _runtime_bus_processor() -> Any:
    from workflow_runtime.presentation.cli.commands._impl.update import         update_source_git
    return update_source_git


def _runtime_bus_paths() -> Any:
    from workflow_runtime.presentation.cli.commands._impl.update import         update_source_core
    return update_source_core


def do_runtime_bus(args: argparse.Namespace) -> None:
    subaction = getattr(args, "subaction", None)
    if subaction == "start":
        started, pid, status = _provider_runtime().start_runtime_bus_daemon()
        if started:
            print(f"[SYSTEM]: Runtime daemon started with PID: {pid}.")
        else:
            print(f"[SYSTEM]: Runtime daemon is already running (PID: {pid}, status={status}).")
        return

    if subaction == "stop":
        pid_file = os.path.expanduser("~/.aiwf/runtime.pid")
        running, pid = is_telegram_daemon_running(pid_file)
        if running:
            _provider_runtime().stop_runtime_bus_daemon(pid_file)
            print(f"[SYSTEM]: Runtime daemon (PID: {pid}) stopped.")
        else:
            print("[SYSTEM]: No running runtime daemon found.")
        return

    if subaction == "restart":
        _provider_runtime().restart_runtime_bus_daemon()
        return

    if subaction == "reload":
        print("[SYSTEM]: Reloading AIWF daemons...")
        _provider_runtime().restart_runtime_bus_daemon()
        print("[SYSTEM]: AIWF daemon reload complete; Telegram worker is supervised by runtime.")
        return

    if subaction == "status":
        pid_file = os.path.expanduser("~/.aiwf/runtime.pid")
        running, pid = is_telegram_daemon_running(pid_file)
        enabled = _provider_runtime().is_runtime_bus_autostart_enabled()
        _provider_runtime().print_project_context()
        print(f"[SYSTEM]: Runtime daemon is {'ACTIVE' if running else 'INACTIVE'}" + (f" (PID: {pid})." if running else "."))
        print(f"[SYSTEM]: Autostart is {'ENABLED' if enabled else 'DISABLED'}.")
        return

    if subaction == "enable":
        try:
            target = _provider_runtime().enable_runtime_bus_autostart()
        except Exception as exc:
            print(f"[SYSTEM]: Runtime daemon autostart enable FAILED: {exc}")
            sys.exit(1)
        print(f"[SYSTEM]: Runtime daemon autostart enabled: {target}")
        return

    if subaction == "disable":
        target = _provider_runtime().disable_runtime_bus_autostart()
        print(f"[SYSTEM]: Runtime daemon autostart disabled: {target}")
        return

    if subaction == "process":
        processed = _runtime_bus_processor().process_runtime_bus_once()
        print("Processed runtime request." if processed else "No runtime request found.")
        return

    if subaction == "daemon":
        import glob
        import hashlib
        import threading
        from workflow_runtime.infrastructure.persistence.runtime_daemon_state import (
            RuntimeDaemonState)

        runtime_state = RuntimeDaemonState()
        acquired, owner = runtime_state.acquire_or_report()
        if not acquired:
            print(
                f"[SUPERVISOR] Runtime daemon already running (PID {owner.get('pid')}, status={owner.get('status')}).",
                flush=True,
            )
            return

        raw_interval = getattr(args, "interval", None)
        interval = max(1.0, float(raw_interval if raw_interval is not None else 2.0))
        print(f"[SUPERVISOR] System Supervisor (Runtime Daemon) started. Watching {_runtime_bus_paths().RUNTIME_REQUEST_PATH}", flush=True)

        telegram_thread: Any = None
        from workflow_runtime.infrastructure.telegram.daemon import             run_polling_loop

        _WATCH_DIR = os.path.dirname(os.path.abspath(__file__))

        def _compute_code_hash(directory: str) -> str:
            h = hashlib.md5()
            for path in sorted(glob.glob(os.path.join(directory, "**", "*.py"), recursive=True)):
                try:
                    with open(path, "rb") as f:
                        h.update(path.encode())
                        h.update(f.read())
                except OSError:
                    pass
            return h.hexdigest()

        _last_code_hash = _compute_code_hash(_WATCH_DIR)
        print(f"[SUPERVISOR] Code watchdog active — watching {_WATCH_DIR}", flush=True)

        _CODE_CHECK_INTERVAL = 10
        _tick = 0

        while True:
            last_error: str | None = None
            try:
                _runtime_bus_processor().process_runtime_bus_once()
            except Exception as e:
                last_error = str(e)
                print(f"[SUPERVISOR] Error processing runtime bus: {e}", file=sys.stderr)

            if run_polling_loop is not None:
                if telegram_thread is None or not getattr(telegram_thread, "is_alive", lambda: False)():
                    print("[SUPERVISOR] Starting/Restarting Telegram daemon worker thread...", flush=True)
                    telegram_thread = threading.Thread(
                        target=run_polling_loop,
                        kwargs={"supervised": True},
                        daemon=True
                    )
                    telegram_thread.start()

            _tick += 1
            if _tick >= _CODE_CHECK_INTERVAL:
                _tick = 0
                try:
                    current_hash = _compute_code_hash(_WATCH_DIR)
                    if current_hash != _last_code_hash:
                        print("[SUPERVISOR] Code change detected! Self-restarting...", flush=True)
                        os.execv(sys.executable, [sys.executable] + sys.argv)
                except Exception as e:
                    last_error = str(e)
                    print(f"[SUPERVISOR] Code watchdog error: {e}", file=sys.stderr)

            runtime_state.heartbeat(last_error)
            time.sleep(interval)
        return

    print(f"Unknown runtime subaction: {subaction}", file=sys.stderr)
    sys.exit(1)


def do_session_command(args: argparse.Namespace) -> None:
    session_id = str(getattr(args, "session_id", None) or os.environ.get("ANTIGRAVITY_TRAJECTORY_ID") or "default_session")
    workspace_root = os.getcwd()

    from workflow_runtime.infrastructure.session.session_bootstrap_guard import (
        SessionBootstrapGuard)
    guard = SessionBootstrapGuard(workspace_root=workspace_root, session_id=session_id)

    subaction = str(getattr(args, "subaction", ""))

    if subaction == "status":
        initialized = guard.is_initialized()
        output = {
            "session_id": session_id,
            "initialized": initialized,
            "workspace_ready": initialized
        }
        print(json.dumps(output, indent=2))

    elif subaction == "initialize":
        success, err = guard.initialize_workspace()
        if success:
            output = {
                "session_id": session_id,
                "initialized": True,
                "workspace_ready": True
            }
            print(json.dumps(output, indent=2))
        else:
            output = {
                "status": "SESSION_BOOTSTRAP_FAILED",
                "failed_step": "initialize-workspace",
                "error": err,
                "recovery_suggestion": "Please verify environment configs or check workspace doctor report."
            }
            print(json.dumps(output, indent=2))
            sys.exit(1)

    elif subaction == "reset":
        guard.reset_session()
        print(f"Session {session_id} reset successfully.")


def is_telegram_daemon_running(pid_file: str) -> tuple[bool, int | None]:
    pid: int | None = None
    if os.path.exists(pid_file):
        try:
            with open(pid_file, "r", encoding="utf-8") as f:
                pid = int(f.read().strip())
            if os.name == "nt":
                session_path = os.path.abspath(os.path.join(".", ".agents", ".session.json"))
                if os.path.exists(session_path):
                    try:
                        with open(session_path, "r", encoding="utf-8") as session_file:
                            json.load(session_file)
                    except Exception:
                        pass
                import subprocess
                res = subprocess.run(["tasklist", "/FI", f"PID eq {pid}"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                return (str(pid) in res.stdout), pid
            os.kill(pid, 0)
            return True, pid
        except Exception:
            return False, pid
    return False, None


__all__ = [
    "do_runtime_bus",
    "do_session_command",
    "is_telegram_daemon_running",
]
