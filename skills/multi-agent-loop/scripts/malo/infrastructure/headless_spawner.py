"""Headless agent spawner (subprocess) — concrete AgentSpawner."""

from __future__ import annotations

import subprocess
import time
from pathlib import Path

from malo.application.dto import SpawnOutcome


class SubprocessSpawner:
    """Run a headless agent command in the shared workspace and capture output."""

    def run(self, command: list[str], cwd: Path, timeout_s: int) -> SpawnOutcome:
        start = time.monotonic()
        try:
            completed = subprocess.run(
                command,
                cwd=str(cwd),
                capture_output=True,
                text=True,
                timeout=timeout_s,
                check=False,
            )
        except FileNotFoundError:
            duration = time.monotonic() - start
            return SpawnOutcome(
                exit_code=127,
                stdout="",
                stderr=f"agent executable not found: {command[0]!r}",
                duration_s=duration,
            )
        except subprocess.TimeoutExpired as exc:
            duration = time.monotonic() - start
            stdout = exc.stdout if isinstance(exc.stdout, str) else ""
            stderr = exc.stderr if isinstance(exc.stderr, str) else ""
            return SpawnOutcome(
                exit_code=124,
                stdout=stdout,
                stderr=stderr or f"timed out after {timeout_s}s",
                duration_s=duration,
                timed_out=True,
            )
        duration = time.monotonic() - start
        return SpawnOutcome(
            exit_code=completed.returncode,
            stdout=completed.stdout or "",
            stderr=completed.stderr or "",
            duration_s=duration,
        )
