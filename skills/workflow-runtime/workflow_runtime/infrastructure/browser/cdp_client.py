import contextlib
import json
import os
import urllib.error
import urllib.request
from typing import Any

from workflow_runtime.shared.errors import VIRConnectionError


class CDPClient:
    """Low-level CDP (Chrome DevTools Protocol) HTTP and JSON-RPC adapter using standard library."""

    def __init__(self, host: str = "localhost", port: int = 9222) -> None:
        env_port = os.environ.get("VIR_CDP_PORT")
        if env_port:
            with contextlib.suppress(ValueError):
                port = int(env_port)
        self.host = host
        self.port = port
        self.connected = False
        self._command_id = 0

    def connect(
        self,
        host: str | None = None,
        port: int | None = None,
        timeout_seconds: float = 10.0,
    ) -> bool:
        """Connects to CDP endpoint on host:port, checking HTTP /json/version endpoint."""
        if host is not None:
            self.host = host
        if port is not None:
            self.port = port

        env_port = os.environ.get("VIR_CDP_PORT")
        if env_port:
            with contextlib.suppress(ValueError):
                self.port = int(env_port)

        url = f"http://{self.host}:{self.port}/json/version"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "python-runtime-cdp"})
            with urllib.request.urlopen(req, timeout=timeout_seconds) as response:
                if response.status == 200:
                    self.connected = True
                    return True
        except (urllib.error.URLError, TimeoutError, OSError):
            self.connected = False
            return False

        self.connected = False
        return False

    def send_command(
        self,
        method: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Sends JSON-RPC command to CDP target or HTTP JSON endpoint."""
        if not self.connected:
            raise VIRConnectionError(
                f"CDP service unavailable on {self.host}:{self.port}. "
                "Ensure Chrome is running with --remote-debugging-port."
            )

        self._command_id += 1
        payload = {
            "id": self._command_id,
            "method": method,
            "params": params or {},
        }
        url = f"http://{self.host}:{self.port}/json/command"
        try:
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                url, data=data, headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=5.0) as response:
                res_data = json.loads(response.read().decode("utf-8"))
                return res_data
        except Exception as exc:
            raise VIRConnectionError(
                f"Failed CDP command '{method}' on {self.host}:{self.port}: {exc}"
            ) from exc

    def navigate_to(self, url: str) -> bool:
        """Navigates target to specified URL using Page.navigate command."""
        try:
            res = self.send_command("Page.navigate", {"url": url})
            return "error" not in res
        except VIRConnectionError:
            return False

    def close(self) -> None:
        """Closes CDP connection session."""
        self.connected = False
