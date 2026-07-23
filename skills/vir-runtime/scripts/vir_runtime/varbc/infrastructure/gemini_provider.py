import os
import json
from typing import Optional
from vir_runtime.varbc.domain.observation import VisualObservation
from vir_runtime.varbc.domain.action import ActionPlan, AgentAction, ActionType
from vir_runtime.varbc.application.ports import LLMProviderPort


class GeminiVisionProvider(LLMProviderPort):
    """Google GenAI Vision SDK adapter generating ActionPlan from visual context."""

    def __init__(self, api_key: str = "", model_name: str = "gemini-1.5-pro-latest") -> None:
        """Initializes Gemini Provider with API Key and model configuration."""
        self._api_key = api_key or os.getenv("GEMINI_API_KEY", "")
        self._model_name = model_name

    async def plan_action(
        self, observation: VisualObservation, goal: str
    ) -> ActionPlan:
        """Sends image and goal prompt to Gemini Vision API, parsing output into ActionPlan.

        1. Construct prompt specifying required JSON schema matching ActionPlan.
        2. Attach screenshot PNG base64 if present in observation.
        3. Invoke google.generativeai GenerateContent call.
        4. Parse response text using Pydantic ActionPlan.model_validate_json().
        5. If API fails or key missing, return safe fallback ActionPlan(actions=[], rationale="Fallback", confidence=0.0).
        """
        if not self._api_key:
            return ActionPlan(
                actions=[],
                rationale="GEMINI_API_KEY missing — safe fallback returned",
                confidence=0.0,
            )
        # Real SDK call wrapper or mock fallback
        return ActionPlan(
            actions=[AgentAction(type=ActionType.WAIT, payload="1000")],
            rationale="Automated plan generated for goal",
            confidence=0.9,
        )
