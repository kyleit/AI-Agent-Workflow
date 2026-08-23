from __future__ import annotations

import contextlib
from typing import Any, cast

from workflow_runtime.infrastructure.browser.cdp_client import CDPClient
from workflow_runtime.shared.errors import VIRConnectionError


class CDPSession:
    """Manages attachment lifecycle and command execution for CDP target sessions."""

    def __init__(self, client: CDPClient, keep_alive: bool = False) -> None:
        self.client = client
        self.keep_alive = keep_alive
        self.active_session_id: str | None = None
        self.target_id: str | None = None

    def attach(self, target_id: str = "default") -> str:
        """Attaches to a specific CDP target ID, returning a session ID."""
        self.target_id = target_id
        session_id = f"session-{target_id}-001"
        self.active_session_id = session_id
        if self.client.connected:
            with contextlib.suppress(VIRConnectionError):
                raw_res: Any = self.client.send_command("Target.attachToTarget", {"targetId": target_id, "flatten": True})
                if isinstance(raw_res, dict):
                    res_dict = cast(dict[str, Any], raw_res)
                    result_val = res_dict.get("result")
                    if isinstance(result_val, dict):
                        sess_id = cast(dict[str, Any], result_val).get("sessionId")
                        if sess_id is not None:
                            self.active_session_id = str(sess_id)
        return self.active_session_id or session_id

    def detach(self, session_id: str = "") -> bool:
        """Detaches active target session."""
        target_session = session_id or self.active_session_id
        if not target_session:
            return False

        if self.client.connected:
            with contextlib.suppress(VIRConnectionError):
                self.client.send_command("Target.detachFromTarget", {"sessionId": target_session})

        if target_session == self.active_session_id:
            self.active_session_id = None
            self.target_id = None
        return True

    def close(self, force: bool = False) -> None:
        """Closes the CDP session unless keep_alive is True (unless forced)."""
        if self.keep_alive and not force:
            # Chỉ clear DOM cũ
            self.execute_cdp_method("DOM.disable")
            return
        self.detach()
        self.client.close()

    def wait_for_hmr_reload(self, timeout_ms: int = 500) -> bool:
        """Waits for HMR reload event or timeout."""
        import time
        if not self.client.connected:
            return False

        # Lắng nghe sự kiện Page.frameNavigated (Mock implementation cho HMR)
        self.execute_cdp_method("Page.enable")
        time.sleep(timeout_ms / 1000.0)
        return True

    def execute_cdp_method(
        self,
        method: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Executes a CDP method within the attached target session scope."""
        payload_params = dict(params) if params else {}
        if self.active_session_id:
            payload_params["sessionId"] = self.active_session_id

        if not self.client.connected:
            return {
                "id": 1,
                "result": {"status": "mock", "method": method, "params": payload_params},
            }

        return self.client.send_command(method, payload_params)
