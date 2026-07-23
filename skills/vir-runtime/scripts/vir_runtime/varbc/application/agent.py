from enum import Enum
import uuid
import logging
from typing import Optional, List
from vir_runtime.varbc.domain.observation import VisualObservation
from vir_runtime.varbc.domain.action import ActionPlan, AgentAction, ActionType
from vir_runtime.varbc.domain.report import VARReport, VARStatus
from vir_runtime.varbc.application.ports import (
    CDPClientPort,
    LLMProviderPort,
    ReportRepositoryPort,
)
from vir_runtime.varbc.application.investigator import VARInvestigator
from vir_runtime.varbc.application.verifier import VARVerifier

logger = logging.getLogger(__name__)


class LoopState(str, Enum):
    """Execution states for autonomous agent loop."""
    IDLE = "IDLE"
    OBSERVING = "OBSERVING"
    PLANNING = "PLANNING"
    ACTING = "ACTING"
    EVALUATING = "EVALUATING"
    REPORTING = "REPORTING"
    FINISHED = "FINISHED"
    FAILED = "FAILED"


class VARAgentLoop:
    """Autonomous state machine orchestrating 5-step Observe-Plan-Act-Evaluate-Report loop."""

    def __init__(
        self,
        cdp_client: CDPClientPort,
        llm_provider: LLMProviderPort,
        report_repo: ReportRepositoryPort,
        investigator: VARInvestigator,
        verifier: VARVerifier,
        max_steps: int = 10,
    ) -> None:
        """Initializes agent loop with required cognitive engines and infrastructure ports."""
        self._cdp_client = cdp_client
        self._llm_provider = llm_provider
        self._report_repo = report_repo
        self._investigator = investigator
        self._verifier = verifier
        self._max_steps = max_steps
        self._state = LoopState.IDLE
        self._current_step = 0
        self._observations: List[VisualObservation] = []

    @property
    def state(self) -> LoopState:
        """Returns current loop execution state."""
        return self._state

    async def run(self, start_url: str, goal: str) -> VARReport:
        """Executes autonomous loop until goal completion or max steps reached."""
        self._state = LoopState.OBSERVING
        self._current_step = 0
        self._observations = []

        try:
            await self._cdp_client.navigate(start_url)

            while self._current_step < self._max_steps and self._state not in (LoopState.FINISHED, LoopState.FAILED):
                # 3a. STEP 1 (Observe): capture screenshot and DOM snapshot -> observation
                self._state = LoopState.OBSERVING
                dom = await self._cdp_client.get_dom_snapshot()
                console_errs = await self._cdp_client.get_console_errors()

                obs = VisualObservation(
                    id=f"obs-{uuid.uuid4().hex[:8]}",
                    url=start_url,
                    screenshot_path="",
                    dom_snapshot=dom,
                    console_errors=console_errs,
                )
                self._observations.append(obs)

                # 3b. STEP 2 (Plan): set state PLANNING, call llm_provider.plan_action(observation, goal)
                self._state = LoopState.PLANNING
                action_plan = await self._llm_provider.plan_action(obs, goal)

                # 3c. Check if action_plan has no further actions or confidence < 0.2:
                if not action_plan.actions or action_plan.confidence < 0.2:
                    self._state = LoopState.EVALUATING
                    break

                # 3d. STEP 3 (Act): set state ACTING, execute actions in action_plan against cdp_client
                self._state = LoopState.ACTING
                for action in action_plan.actions:
                    await self._cdp_client.execute_action(action)

                # 3e. Increment self._current_step
                self._current_step += 1

            # 4. STEP 4 (Evaluate): set state EVALUATING
            self._state = LoopState.EVALUATING
            report = await self._verifier.verify(self._observations, diffs=[])
            await self._investigator.investigate(self._observations)

            # 5. STEP 5 (Report): set state REPORTING, save report via report_repo
            self._state = LoopState.REPORTING
            await self._report_repo.save_report(report)

            # 6. Set state FINISHED and return report.
            self._state = LoopState.FINISHED
            return report

        except Exception as e:
            logger.error(f"Error during agent loop execution: {e}")
            self._state = LoopState.FAILED
            raise e
