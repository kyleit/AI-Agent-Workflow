from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

from workflow_runtime.application.ports.agy_port import IAGYPort


class AGYAdapter(IAGYPort):
    """Infrastructure adapter executing the external 'agy' CLI subprocess."""

    def __init__(self, binary_name: str = "agy") -> None:
        self.binary_name = binary_name

    def check_binary_available(self) -> bool:
        """Checks if the agy executable is reachable on system PATH."""
        return shutil.which(self.binary_name) is not None

    def build_command(
        self,
        role_name: str,
        prompt: str,
        model: str = "gemini-3.6-flash-high",
        effort: str | None = None,
        timeout_seconds: int = 300,
        add_dir: Path | str | None = None,
    ) -> list[str]:
        """Formulates the exact agy CLI argument list.

        Returns:
            List of command-line token strings.
        """
        cmd = [self.binary_name]
        if role_name:
            cmd.extend(["--agent", role_name])
        if model:
            cmd.extend(["--model", model])
        if effort:
            cmd.extend(["--effort", effort])
        cmd.append("--dangerously-skip-permissions")
        if add_dir:
            cmd.extend(["--add-dir", str(add_dir)])
        cmd.append("--print")
        cmd.append(prompt)
        return cmd

    def execute_dispatch(
        self,
        command_args: list[str],
        dry_run: bool = False,
        timeout_seconds: int = 300,
    ) -> tuple[int, str, str]:
        """Executes agy CLI command line or formats dry-run output.

        Returns:
            Tuple of (exit_code, stdout_str, stderr_str).
        """
        if dry_run:
            cmd_str = " ".join(command_args)
            return (0, f"[DRY-RUN] Would execute: {cmd_str}", "")

        if not self.check_binary_available():
            return (1, "", f"Error: AGY binary '{self.binary_name}' not found on system PATH.")

        try:
            process = subprocess.Popen(
                command_args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
            )
            stdout_list: list[str] = []
            if process.stdout:
                for line in process.stdout:
                    sys.stdout.write(line)
                    sys.stdout.flush()
                    stdout_list.append(line)

            process.wait(timeout=timeout_seconds)

            stderr_str = process.stderr.read() if process.stderr else ""
            if stderr_str:
                sys.stderr.write(stderr_str)
                sys.stderr.flush()

            stdout_str = "".join(stdout_list)
            return (process.returncode, stdout_str, stderr_str)
        except subprocess.TimeoutExpired:
            return (124, "", f"Error: AGY execution timed out after {timeout_seconds} seconds.")
        except Exception as exc:
            return (1, "", f"Error executing AGY binary: {str(exc)}")
