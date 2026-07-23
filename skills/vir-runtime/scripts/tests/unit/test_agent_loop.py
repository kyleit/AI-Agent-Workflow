import pytest
from vir_runtime.varbc.domain.observation import VisualObservation
from vir_runtime.varbc.domain.action import ActionPlan, AgentAction, ActionType
from vir_runtime.varbc.domain.report import VARReport, VARStatus
from vir_runtime.varbc.application.ports import (
    CDPClientPort,
    LLMProviderPort,
    ReportRepositoryPort,
)
from vir_runtime.varbc.application.agent import VARAgentLoop, LoopState
from vir_runtime.varbc.application.investigator import VARInvestigator
from vir_runtime.varbc.application.verifier import VARVerifier


class DummyCDPClient(CDPClientPort):
    def __init__(self):
        self.navigated = False
        self.executed_actions = []

    async def navigate(self, url: str) -> None:
        self.navigated = True

    async def capture_screenshot(self, selector: str = "body") -> bytes:
        return b"fake_png"

    async def get_dom_snapshot(self) -> str:
        return "<html><body><div id='app'>Test App</div></body></html>"

    async def get_console_errors(self) -> list[str]:
        return []

    async def execute_action(self, action: AgentAction) -> None:
        self.executed_actions.append(action)

    async def close(self) -> None:
        pass


class DummyLLMProvider(LLMProviderPort):
    def __init__(self, actions=None, confidence=0.9):
        self.actions = actions or [AgentAction(type=ActionType.CLICK, target="#btn")]
        self.confidence = confidence
        self.call_count = 0

    async def plan_action(self, observation: VisualObservation, goal: str) -> ActionPlan:
        self.call_count += 1
        if self.call_count > 1:
            return ActionPlan(actions=[], rationale="Goal completed", confidence=0.9)
        return ActionPlan(actions=self.actions, rationale="Click next", confidence=self.confidence)


class DummyReportRepo(ReportRepositoryPort):
    def __init__(self):
        self.saved_reports = []

    async def save_report(self, report: VARReport) -> None:
        self.saved_reports.append(report)

    async def get_report(self, report_id: str) -> VARReport | None:
        for r in self.saved_reports:
            if r.id == report_id:
                return r
        return None


@pytest.mark.asyncio
async def test_agent_loop_execution_flow():
    cdp = DummyCDPClient()
    llm = DummyLLMProvider()
    repo = DummyReportRepo()
    investigator = VARInvestigator()
    verifier = VARVerifier()

    loop = VARAgentLoop(
        cdp_client=cdp,
        llm_provider=llm,
        report_repo=repo,
        investigator=investigator,
        verifier=verifier,
        max_steps=5,
    )

    assert loop.state == LoopState.IDLE

    report = await loop.run(start_url="http://localhost:8000", goal="Test navigation")

    assert cdp.navigated is True
    assert len(cdp.executed_actions) == 1
    assert cdp.executed_actions[0].target == "#btn"
    assert len(repo.saved_reports) == 1
    assert loop.state == LoopState.FINISHED
    assert isinstance(report, VARReport)
