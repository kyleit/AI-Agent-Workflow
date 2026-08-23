"""
application/ports/agy_port.py

Port interface for AGY (AI Agent execution) adapter.
Defines the contract that any AGY implementation must fulfill.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path


class IAGYPort(ABC):
    """Port: executes AI agent commands via CLI or any other transport."""

    @abstractmethod
    def check_binary_available(self) -> bool:
        """Returns True if the AGY binary / CLI is available on this machine."""
        ...

    @abstractmethod
    def build_command(
        self,
        role_name: str,
        prompt: str,
        model: str,
        effort: str | None,
        timeout_seconds: int,
        add_dir: Path | str | None,
    ) -> list[str]:
        """Constructs the command-line arguments list for the agent invocation."""
        ...

    @abstractmethod
    def execute_dispatch(
        self,
        command_args: list[str],
        dry_run: bool,
        timeout_seconds: int,
    ) -> tuple[int, str, str]:
        """Executes the dispatch command and returns (exit_code, stdout, stderr)."""
        ...
