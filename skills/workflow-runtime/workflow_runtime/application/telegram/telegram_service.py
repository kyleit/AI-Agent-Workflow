"""
application/telegram/telegram_service.py

Application Service for Telegram daemon management.
Handles start/stop/restart/status/config/link subcommands
by delegating to the infrastructure layer.
"""
from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast


@dataclass
class TelegramStatus:
    daemon_running: bool
    daemon_pid: int | None
    autostart_enabled: bool
    projects: list[dict[str, Any]]
    error: str | None = None


class TelegramService:
    """Application service for managing the shared Telegram daemon.

    Delegates subcommands to the canonical entry point:
    python -m workflow_runtime telegram <subcommand> [extra_args...]
    """

    def run(self, subcommand: str, extra_args: list[str] | None = None) -> int:
        """Dispatch a telegram subcommand.

        Args:
            subcommand: One of start, stop, restart, status, config, link, enable, disable
            extra_args: Additional args passed verbatim (e.g. ['--chat-id', '123'])

        Returns:
            Exit code (0 = success)
        """
        cmd = [sys.executable, "-m", "workflow_runtime", "telegram", subcommand]
        if extra_args:
            cmd.extend(extra_args)
        result = subprocess.run(cmd, check=False)
        return result.returncode

    def status(self) -> TelegramStatus:
        """Return structured status (daemon running, PID, autostart, projects)."""
        try:
            from workflow_runtime.infrastructure.telegram.daemon import (
                TelegramDaemonManager)
            mgr = TelegramDaemonManager()
            registry = mgr.load_projects_registry()
            raw_projects = registry.get("projects", [])
            projects = cast(list[dict[str, Any]], raw_projects) if isinstance(raw_projects, list) else []

            pid_file = Path.home() / ".aiwf" / "telegram_daemon.pid"
            pid = None
            running = False
            if pid_file.exists():
                try:
                    pid = int(pid_file.read_text().strip())
                    os.kill(pid, 0)
                    running = True
                except (ValueError, ProcessLookupError, PermissionError):
                    pass

            autostart_file = Path.home() / ".aiwf" / "telegram_autostart"
            autostart = autostart_file.exists()
            return TelegramStatus(
                daemon_running=running,
                daemon_pid=pid if running else None,
                autostart_enabled=autostart,
                projects=projects,
            )
        except Exception as e:
            return TelegramStatus(
                daemon_running=False,
                daemon_pid=None,
                autostart_enabled=False,
                projects=[],
                error=str(e),
            )


__all__ = [
    "TelegramStatus",
    "TelegramService",
]
