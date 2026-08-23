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
    """Owns runtime daemon singleton pid/state files."""

    def __init__(self, root: str | None = None) -> None:
        self.root = os.path.abspath(os.path.expanduser(root or "~/.aiwf"))
        self.pid_file = os.path.join(self.root, "runtime.pid")
        self.state_file = os.path.join(self.root, "runtime-state.json")

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
        if not pid:
            return {"active": False, "status": "INACTIVE", "reason": "missing_pid"}

        if not is_process_alive(pid):
            return {"active": False, "status": "STALE", "pid": pid, "reason": "pid_not_alive", "state": state}

        expected_start = str(state.get("process_started_at") or "")
        actual_start = get_process_creation_time(pid)
        if expected_start and actual_start and expected_start != actual_start:
            return {
                "active": False,
                "status": "STALE",
                "pid": pid,
                "reason": "pid_reused",
                "state": state,
            }

        heartbeat_at = str(state.get("heartbeat_at") or "")
        if heartbeat_at:
            try:
                heartbeat_dt = datetime.fromisoformat(heartbeat_at)
                age = (datetime.now().astimezone() - heartbeat_dt).total_seconds()
                if age > 90:
                    return {
                        "active": False,
                        "status": "STALE",
                        "pid": pid,
                        "reason": "heartbeat_expired",
                        "heartbeat_age_seconds": age,
                        "state": state,
                    }
                return {"active": True, "status": "ACTIVE", "pid": pid, "heartbeat_age_seconds": age, "state": state}
            except Exception:
                pass

        return {"active": True, "status": "ACTIVE", "pid": pid, "state": state}

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
        if last_error is not None:
            state["last_error"] = last_error
        self._write_state(state)

    def clear_stale(self) -> None:
        for path in (self.pid_file, self.state_file):
            try:
                if os.path.exists(path):
                    os.remove(path)
            except Exception:
                pass

    def clear_if_owner(self, pid: int) -> None:
        current = self._read_pid()
        if current == pid:
            self.clear_stale()
