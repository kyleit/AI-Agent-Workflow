from __future__ import annotations

import json
import os
import socket
import sys
import tempfile
from datetime import datetime, timedelta
from typing import Any, cast

from workflow_runtime.infrastructure.persistence.lease import (
    get_process_creation_time, is_process_alive)


class RuntimeDaemonState:
    """Owns the runtime singleton and exposes a machine-readable health contract."""

    STATES = {"STOPPED", "STARTING", "READY", "DEGRADED", "STALE", "CRASHED", "CONFLICT"}

    def __init__(
        self,
        root: str | None = None,
        *,
        workspace_root: str | None = None,
        runtime_revision: str | None = None,
        heartbeat_timeout_seconds: int = 90,
        max_backoff_seconds: int = 60,
    ) -> None:
        self.root = os.path.abspath(os.path.expanduser(root or "~/.aiwf"))
        self.pid_file = os.path.join(self.root, "runtime.pid")
        self.state_file = os.path.join(self.root, "runtime-state.json")
        self.workspace_root = os.path.abspath(
            workspace_root
            or os.environ.get("AIWF_PROJECT_ROOT")
            or os.getcwd()
        )
        self.runtime_revision = str(
            runtime_revision or os.environ.get("AIWF_RUNTIME_REVISION") or "unknown"
        )
        self.heartbeat_timeout_seconds = max(1, heartbeat_timeout_seconds)
        self.max_backoff_seconds = max(1, max_backoff_seconds)

    def _read_pid(self) -> int | None:
        try:
            with open(self.pid_file, "r", encoding="utf-8") as f:
                return int(f.read().strip())
        except Exception:
            return None

    def _read_state(self) -> dict[str, Any]:
        try:
            with open(self.state_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            return cast(dict[str, Any], data) if isinstance(data, dict) else {}
        except Exception:
            return {}

    def _write_state(self, data: dict[str, Any]) -> None:
        os.makedirs(self.root, exist_ok=True)
        fd, tmp_path = tempfile.mkstemp(dir=self.root, suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            os.replace(tmp_path, self.state_file)
        except Exception:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            raise

    def inspect(self) -> dict[str, Any]:
        state = self._read_state()
        pid = int(cast(int, state.get("pid") or self._read_pid() or 0))
        base: dict[str, Any] = {
            "active": False,
            "status": "STOPPED",
            "state": "STOPPED",
            "pid": pid,
            "process_started_at": state.get("process_started_at"),
            "heartbeat_at": state.get("heartbeat_at"),
            "workspace_root": state.get("workspace_root") or self.workspace_root,
            "runtime_revision": state.get("runtime_revision") or self.runtime_revision,
            "restart_count": int(cast(int, state.get("restart_count") or 0)),
            "last_error": state.get("last_error"),
        }
        if not pid:
            base["reason"] = "missing_pid"
            return base

        if not is_process_alive(pid):
            base.update({"status": "CRASHED", "state": "CRASHED", "reason": "pid_not_alive", "payload": state})
            return base

        expected_start = str(state.get("process_started_at") or "")
        actual_start = get_process_creation_time(pid)
        if expected_start and actual_start and expected_start != actual_start:
            base.update({
                "status": "CONFLICT",
                "state": "CONFLICT",
                "reason": "pid_reused",
                "payload": state,
                "conflict": {
                    "conflict_type": "pid_reused",
                    "owners": [f"pid:{pid}"],
                    "resolution": "clear stale state and allow the canonical supervisor to reacquire",
                    "severity": "high",
                },
            })
            return base

        heartbeat_at = str(state.get("heartbeat_at") or "")
        if heartbeat_at:
            try:
                heartbeat_dt = datetime.fromisoformat(heartbeat_at)
                age = (datetime.now().astimezone() - heartbeat_dt).total_seconds()
                base["heartbeat_age_seconds"] = age
                if age > self.heartbeat_timeout_seconds:
                    base.update({
                        "status": "STALE",
                        "state": "STALE",
                        "reason": "heartbeat_expired",
                        "active": False,
                        "payload": state,
                    })
                    return base
            except Exception:
                base["reason"] = "invalid_heartbeat"

        health_state = str(state.get("state") or ("DEGRADED" if state.get("last_error") else "READY"))
        if health_state not in self.STATES:
            health_state = "DEGRADED"
        base.update({"active": True, "status": health_state, "state": health_state, "payload": state})
        return base

    def acquire_or_report(self) -> tuple[bool, dict[str, Any]]:
        status = self.inspect()
        if status.get("active") and int(cast(int, status.get("pid") or 0)) != os.getpid():
            return False, status
        if not status.get("active"):
            self.clear_stale()
        self.write_started(os.getpid())
        return True, self.inspect()

    def write_started(self, pid: int) -> None:
        os.makedirs(self.root, exist_ok=True)
        now = datetime.now().astimezone().isoformat()
        state = self._read_state()
        restart_count = int(cast(int, state.get("restart_count") or 0))
        data = {
            "pid": pid,
            "hostname": socket.gethostname(),
            "command": "python -m workflow_runtime runtime daemon",
            "process_started_at": get_process_creation_time(pid),
            "started_at": now,
            "heartbeat_at": now,
            "last_error": None,
            "restart_count": restart_count + 1,
            "python": sys.executable,
            "state": "STARTING",
            "workspace_root": self.workspace_root,
            "runtime_revision": self.runtime_revision,
            "heartbeat_timeout_seconds": self.heartbeat_timeout_seconds,
        }
        self._write_state(data)
        with open(self.pid_file, "w", encoding="utf-8") as f:
            f.write(str(pid))

    def heartbeat(self, last_error: str | None = None) -> None:
        state = self._read_state()
        pid = int(cast(int, state.get("pid") or self._read_pid() or os.getpid()))
        if pid != os.getpid():
            return
        state["pid"] = pid
        state["heartbeat_at"] = datetime.now().astimezone().isoformat()
        state["state"] = "DEGRADED" if last_error else "READY"
        if last_error is not None:
            state["last_error"] = last_error
        elif state.get("last_error"):
            state["last_error"] = None
        self._write_state(state)

    def restart_delay_seconds(self, restart_count: int) -> int:
        """Return bounded exponential backoff for supervisor retries."""
        if restart_count <= 0:
            return 0
        return min(self.max_backoff_seconds, 2 ** min(restart_count, 16))

    def policy(self, *, enabled: bool = True) -> dict[str, Any]:
        return {
            "enabled": enabled,
            "restart_on_failure": True,
            "max_backoff_seconds": self.max_backoff_seconds,
            "heartbeat_timeout_seconds": self.heartbeat_timeout_seconds,
            "canonical_launcher": "workflow_runtime runtime daemon",
            "allow_battery": True,
        }

    def clear_stale(self) -> None:
        state = self._read_state()
        if state:
            state.update({"pid": 0, "state": "STOPPED", "heartbeat_at": None})
            self._write_state(state)
        try:
            if os.path.exists(self.pid_file):
                os.remove(self.pid_file)
        except OSError:
            pass

    def clear_if_owner(self, pid: int) -> None:
        current = self._read_pid()
        if current == pid:
            self.clear_stale()
