# compatibility_adapter.py
import warnings
from typing import Any, Dict
from runtime_sdk import RuntimeSDKv3

class CompatibilityAdapterV1toV3:
    def __init__(self, sdk_v3: RuntimeSDKv3) -> None:
        self.sdk = sdk_v3

    async def load_session_v1(self, session_id: str) -> Dict[str, Any]:
        # Issue migration warning
        warnings.warn(
            "API v1 'load_session_v1' is deprecated and will be removed in v3.5. Please migrate to SDK v3 'load_session'.",
            DeprecationWarning,
            stacklevel=2
        )
        # Map to SDK v3 load_session
        return await self.sdk.load_session(session_id)

    async def submit_task_v1(self, task_id: str, session_id: str, agent_id: str) -> Dict[str, Any]:
        # Issue migration warning
        warnings.warn(
            "API v1 'submit_task_v1' is deprecated and will be removed in v3.5. Please migrate to SDK v3 'submit_task'.",
            DeprecationWarning,
            stacklevel=2
        )
        # Map to SDK v3 submit_task
        return await self.sdk.submit_task(task_id=task_id, session_id=session_id, agent_id=agent_id)
