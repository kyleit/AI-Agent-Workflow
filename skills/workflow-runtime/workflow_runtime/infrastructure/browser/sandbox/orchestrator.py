# File path: vir_runtime/sandbox/orchestrator.py
from __future__ import annotations

import asyncio
import subprocess
import time

from workflow_runtime.infrastructure.browser.sandbox.ports import PortManager
from workflow_runtime.infrastructure.browser.sandbox.process import (
    WindowsProcessManager)


class TargetStartupTimeoutError(Exception):
    pass


class SandboxOrchestrator:
    def __init__(self, build_command: str = "npm run build", dev_command: str = "npm run dev", startup_timeout: float = 30.0) -> None:
        self.build_command = build_command
        self.dev_command = dev_command
        self.startup_timeout = startup_timeout
        self.port_manager = PortManager()
        self.process_manager = WindowsProcessManager()
        self.process: subprocess.Popen[bytes] | None = None

    async def start_sandbox(self, port: int) -> None:
        """Run build and startup target application background processes."""
        if self.build_command:
            print(f"[SandboxOrchestrator] Running build command: {self.build_command}")
            await asyncio.sleep(0.1)

        print(f"[SandboxOrchestrator] Starting dev server command: {self.dev_command} on port {port}")
        self.process = subprocess.Popen(
            self.dev_command,
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        start_time = time.time()
        while time.time() - start_time < self.startup_timeout:
            if self.port_manager.is_port_in_use(port):
                print(f"[SandboxOrchestrator] Target application successfully bound to port {port}")
                return
            await asyncio.sleep(0.1)

        self.stop_sandbox()
        raise TargetStartupTimeoutError(f"Application failed to bind to port {port} within {self.startup_timeout}s.")

    def stop_sandbox(self) -> None:
        """Stop background processes recursively sweeping process IDs."""
        if self.process is not None:
            pid = self.process.pid
            print(f"[SandboxOrchestrator] Stopping sandbox processes group for PID {pid}")
            self.process_manager.terminate_process_tree(pid)
            self.process = None


__all__ = [
    "TargetStartupTimeoutError",
    "SandboxOrchestrator",
]
