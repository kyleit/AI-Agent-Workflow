# interactive_terminal_process_monitor.py
from __future__ import annotations

import subprocess


class InteractiveTerminalMonitor:
    """
    FEAT-100: Interactive Terminal & Process Monitor
    Monitors long-running background processes and captures stdout/stderr.
    """
    def __init__(self) -> None:
        self.log_buffer: list[str] = []

    def run_interactive(self, args: list[str], input_str: str = "") -> str:
        proc = subprocess.Popen(
            args,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        stdout, stderr = proc.communicate(input=input_str)
        if stdout:
            self.log_buffer.extend(stdout.splitlines())
        if stderr:
            self.log_buffer.extend(stderr.splitlines())
        return stdout or ""


__all__ = ["InteractiveTerminalMonitor"]
