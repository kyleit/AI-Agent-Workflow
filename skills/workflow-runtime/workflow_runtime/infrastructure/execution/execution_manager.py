"""
infrastructure/execution/execution_manager.py

DDD Adapter wrapping the legacy ExecutionManager and ProcessRegistry.
Provides subprocess lifecycle management with scheduling, cancellation, and recovery.
"""
from __future__ import annotations

from typing import Any, cast


def _import_exec_manager() -> Any:
    from workflow_runtime.application.use_cases import (
        execution_manager as legacy_exec_manager)
    return legacy_exec_manager


class ExecutionGateway:
    """DDD adapter over legacy ExecutionManager + ProcessRegistry.

    Provides a clean interface for agent subprocess lifecycle management:
    - submit(req) → execution_id
    - cancel/kill/pause/resume by execution_id
    - recover() → list of recovered execution_ids
    - run_command_managed(cmd_list) → result
    """

    def __init__(self) -> None:
        self._mod: Any = None

    def _m(self) -> Any:
        if self._mod is None:
            self._mod = _import_exec_manager()
        return self._mod

    def start_scheduler(self) -> None:
        """Start the background scheduler thread."""
        self._m().ExecutionManager.start_scheduler()

    def stop_scheduler(self) -> None:
        self._m().ExecutionManager.stop_scheduler()

    def submit(self, req: dict[str, Any]) -> str:
        """Submit an execution request. Returns execution_id."""
        res = self._m().ExecutionManager.submit(req)
        return str(res)

    def cancel(self, execution_id: str, reason: str = "CANCELLED") -> None:
        self._m().ExecutionManager.cancel(execution_id, reason)

    def kill(self, execution_id: str, reason: str = "KILLED") -> None:
        self._m().ExecutionManager.kill(execution_id, reason)

    def pause(self, execution_id: str) -> None:
        self._m().ExecutionManager.pause(execution_id)

    def resume(self, execution_id: str) -> None:
        self._m().ExecutionManager.resume(execution_id)

    def recover(self) -> list[str]:
        """Recover stale/zombie executions. Returns list of recovered IDs."""
        res = self._m().ExecutionManager.recover()
        return cast(list[str], res) if isinstance(res, list) else []

    def tick(self) -> None:
        """Run one scheduler tick (process queued jobs)."""
        self._m().ExecutionManager.tick_scheduler()

    def list_executions(self) -> dict[str, Any]:
        """Return the full ProcessRegistry state dict."""
        res = self._m().ProcessRegistry.read()
        return cast(dict[str, Any], res) if isinstance(res, dict) else {}

    def get_execution(self, execution_id: str) -> dict[str, Any] | None:
        registry = self.list_executions()
        item = registry.get(execution_id)
        return cast(dict[str, Any], item) if isinstance(item, dict) else None

    def run_managed(
        self,
        cmd_list: list[str],
        cwd: str = ".",
        owner_agent_id: str = "AGENT-SYSTEM",
        task_id: str = "TASK-SYSTEM",
        timeout: int = 300,
    ) -> Any:
        """Run a command under execution management. Returns result with returncode, stdout, stderr."""
        return self._m().run_command_managed(
            cmd_list, cwd=cwd, owner_agent_id=owner_agent_id,
            task_id=task_id, timeout=timeout,
        )

    def get_system_capacity(self) -> tuple[int, int, int]:
        """Return (total_slots, used_slots, available_slots)."""
        res = self._m().ExecutionManager.get_system_capacity()
        return cast(tuple[int, int, int], res)

    def is_pid_alive(self, pid: int) -> bool:
        return bool(self._m().is_pid_alive(pid))


__all__ = ["ExecutionGateway"]
