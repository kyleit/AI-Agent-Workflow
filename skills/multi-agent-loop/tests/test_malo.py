"""BAT + unit tests for the MALO orchestrator (fakes; no real agents)."""

from __future__ import annotations

from pathlib import Path

import pytest

from malo.application.dto import (
    DecisionRequest,
    DecisionView,
    GateEvidence,
    SpawnOutcome,
)

_GATE_PASS = GateEvidence(present=True, decision="PASS", code_block_count=3)
from malo.application.ports import LoopEnginePort
from malo.domain.approval import (
    ApprovalDecision,
    ApprovalMode,
    ApprovalPolicy,
)
from malo.application.use_cases import (
    DriveLoopUseCase,
    OrchestrationPlan,
    RunPhaseUseCase,
    TickUseCase,
)
from malo.domain.errors import InvalidInvocationError
from malo.domain.invocation import build_headless_command
from malo.domain.models import AgentDescriptor, AgentRegistry
from malo.domain.results import PhaseRunResult, Verdict, normalize_verdict
from malo.domain.selection import select_agent

pytestmark = pytest.mark.unit


def _registry() -> AgentRegistry:
    return AgentRegistry(agents=(
        AgentDescriptor("claude-main", "claude", ("plan", "blueprint", "implement", "verify"),
                        ("claude", "-p", "${task}"), priority=5),
        AgentDescriptor("codex-impl", "codex", ("implement",),
                        ("codex", "exec", "${task}"), priority=10),
        AgentDescriptor("agy-verify", "antigravity", ("verify",),
                        ("agy", "--print", "${task}"), priority=10),
    ))


# ----------------------------- selection ---------------------------------- #
def test_selection_distributes_by_capability_and_priority() -> None:
    reg = _registry()
    assert select_agent("plan", reg) is not None
    assert select_agent("plan", reg).id == "claude-main"
    assert select_agent("implement", reg).id == "codex-impl"
    assert select_agent("verify", reg).id == "agy-verify"


def test_selection_none_when_no_capable_agent() -> None:
    assert select_agent("release", _registry()) is None


def test_selection_empty_registry_backward_compat() -> None:
    assert select_agent("plan", AgentRegistry()) is None


def test_selection_lru_tiebreak() -> None:
    reg = AgentRegistry(agents=(
        AgentDescriptor("a", "claude", ("x",), ("a", "${task}"), priority=5),
        AgentDescriptor("b", "codex", ("x",), ("b", "${task}"), priority=5),
    ))
    assert select_agent("x", reg, {"a": 3, "b": 1}).id == "b"  # b less used


# ----------------------------- invocation --------------------------------- #
def test_invocation_substitutes_and_is_injection_safe() -> None:
    agent = AgentDescriptor("a", "claude", ("p",), ("claude", "-p", "${task}"))
    cmd = build_headless_command(agent, {"task": "do X; rm -rf /", "phase": "p"})
    assert cmd == ["claude", "-p", "do X; rm -rf /"]  # single argv element, no shell


def test_invocation_unresolved_placeholder_raises() -> None:
    agent = AgentDescriptor("a", "claude", ("p",), ("claude", "${unknown}"))
    with pytest.raises(InvalidInvocationError):
        _ = build_headless_command(agent, {"task": "t"})


# ----------------------------- results ------------------------------------ #
def test_normalize_verdict() -> None:
    assert normalize_verdict(1, "PASS") is Verdict.ERROR       # non-zero exit
    assert normalize_verdict(0, "all good PASS") is Verdict.PASS
    assert normalize_verdict(0, "needs BLOCK more") is Verdict.BLOCK
    assert normalize_verdict(0, "FAIL upstream") is Verdict.FAIL
    assert normalize_verdict(0, "no token here") is Verdict.BLOCK  # conservative


# --------------------------- fakes for drive ------------------------------ #
class FakeSpawner:
    def __init__(self, verdict_word: str = "PASS") -> None:
        self.calls: list[list[str]] = []
        self._word = verdict_word

    def run(self, command: list[str], cwd: Path, timeout_s: int) -> SpawnOutcome:
        self.calls.append(command)
        return SpawnOutcome(exit_code=0, stdout=self._word, stderr="", duration_s=0.01)


class FakeLoopAdvance:
    """ADVANCE through phases; HALT GATE_PASS_FINAL on terminal."""

    def decide(self, request: DecisionRequest) -> DecisionView:
        if request.is_terminal_phase and request.verdict is Verdict.PASS:
            return DecisionView("HALT", request.phase, ("GATE_PASS_FINAL",), False, "{}")
        return DecisionView("ADVANCE", request.next_phase or request.phase, (), False, "{}")

    def persist(self, payload_json: str) -> str:
        return ".agents/state/loop/x.json"


class FakeLoopNoProgress:
    def decide(self, request: DecisionRequest) -> DecisionView:
        return DecisionView("HALT", request.phase, ("NO_PROGRESS",), True, "{}")

    def persist(self, payload_json: str) -> str:
        return ".agents/state/loop/x.json"


class FakeResultRepo:
    def __init__(self) -> None:
        self.rows: list[PhaseRunResult] = []

    def append(self, root: Path, result: PhaseRunResult) -> str:
        self.rows.append(result)
        return ".agents/state/loop/x.runs.jsonl"


class FixedClock:
    def now_iso(self) -> str:
        return "2026-09-18T00:00:00Z"


def _driver(
    loop: LoopEnginePort, spawner: FakeSpawner, results: FakeResultRepo
) -> DriveLoopUseCase:
    return DriveLoopUseCase(
        registry=_registry(),
        run_phase=RunPhaseUseCase(spawner),
        loop=loop,
        result_repo=results,
        clock=FixedClock(),
    )


# ----------------------------- drive loop --------------------------------- #
def test_drive_completes_across_agents() -> None:
    spawner = FakeSpawner("PASS")
    results = FakeResultRepo()
    driver = _driver(FakeLoopAdvance(), spawner, results)
    plan = OrchestrationPlan(
        phase_sequence=("plan", "implement", "verify"),
        approval_gate_phases=frozenset(),  # no gates for this test
    )
    outcome = driver.run("FEAT-1", "plan", plan, Path("."))
    assert outcome.status == "COMPLETED"
    assert len(results.rows) == 3
    assert {r.agent_id for r in results.rows} == {"claude-main", "codex-impl", "agy-verify"}


def test_drive_halts_at_approval_gate_without_spawning() -> None:
    spawner = FakeSpawner("PASS")
    results = FakeResultRepo()
    driver = _driver(FakeLoopAdvance(), spawner, results)
    plan = OrchestrationPlan(
        phase_sequence=("blueprint", "implement"),
        approval_gate_phases=frozenset({"blueprint"}),
    )
    outcome = driver.run("FEAT-2", "blueprint", plan, Path("."))
    assert outcome.status == "AWAITING_APPROVAL"
    assert outcome.phase == "blueprint"
    assert spawner.calls == []  # never spawned an agent to approve


def test_drive_needs_session_agent_when_incapable() -> None:
    driver = _driver(FakeLoopAdvance(), FakeSpawner(), FakeResultRepo())
    plan = OrchestrationPlan(phase_sequence=("release",), approval_gate_phases=frozenset())
    outcome = driver.run("FEAT-3", "release", plan, Path("."))
    assert outcome.status == "NEEDS_SESSION_AGENT"


def test_drive_halts_escalate_on_no_progress() -> None:
    driver = _driver(FakeLoopNoProgress(), FakeSpawner("BLOCK"), FakeResultRepo())
    plan = OrchestrationPlan(phase_sequence=("implement",), approval_gate_phases=frozenset())
    outcome = driver.run("FEAT-4", "implement", plan, Path("."))
    assert outcome.status == "HALTED_ESCALATE"
    assert len(outcome.escalation_options) >= 2


# --------------------------- approval policy ------------------------------ #
def test_policy_auto_covers_allowed_gate_but_never_git_release_deploy() -> None:
    p = ApprovalPolicy(mode=ApprovalMode.AUTO)
    assert p.decide("blueprint") is ApprovalDecision.AUTO
    assert p.decide("implementation") is ApprovalDecision.AUTO
    for forbidden in ("git", "release", "deploy"):
        assert p.decide(forbidden) is ApprovalDecision.MANUAL
    assert p.decide("something-else") is ApprovalDecision.MANUAL


def test_policy_manual_mode_never_auto() -> None:
    p = ApprovalPolicy(mode=ApprovalMode.MANUAL)
    assert p.decide("blueprint") is ApprovalDecision.MANUAL


def test_policy_from_dict_unions_forbidden_gates() -> None:
    p = ApprovalPolicy.from_dict({
        "mode": "auto",
        "auto_gates": ["blueprint"],
        "never_auto_gates": ["custom"],
    })
    assert p.decide("blueprint") is ApprovalDecision.AUTO
    assert p.decide("custom") is ApprovalDecision.MANUAL
    assert p.decide("release") is ApprovalDecision.MANUAL  # hard default preserved


class FakeApprovalExecutor:
    def __init__(self, ok: bool = True) -> None:
        self.calls: list[str] = []
        self._ok = ok

    def approve(self, gate: str, workflow_id: str, root: Path) -> bool:
        self.calls.append(gate)
        return self._ok


def _driver_with_approval(
    policy: ApprovalPolicy, approver: FakeApprovalExecutor
) -> DriveLoopUseCase:
    return DriveLoopUseCase(
        registry=_registry(),
        run_phase=RunPhaseUseCase(FakeSpawner("PASS")),
        loop=FakeLoopAdvance(),
        result_repo=FakeResultRepo(),
        clock=FixedClock(),
        policy=policy,
        approval_executor=approver,
    )


def test_drive_auto_approves_blueprint_and_completes() -> None:
    approver = FakeApprovalExecutor(ok=True)
    driver = _driver_with_approval(ApprovalPolicy(mode=ApprovalMode.AUTO), approver)
    plan = OrchestrationPlan(
        phase_sequence=("plan", "blueprint", "implement"),
        approval_gate_phases=frozenset({"blueprint"}),
    )
    outcome = driver.run("FEAT-A", "plan", plan, Path("."))
    assert outcome.status == "COMPLETED"
    assert approver.calls == ["blueprint"]  # auto-approved the gate


def test_drive_manual_mode_halts_at_gate_without_approving() -> None:
    approver = FakeApprovalExecutor(ok=True)
    driver = _driver_with_approval(ApprovalPolicy(mode=ApprovalMode.MANUAL), approver)
    plan = OrchestrationPlan(
        phase_sequence=("plan", "blueprint", "implement"),
        approval_gate_phases=frozenset({"blueprint"}),
    )
    outcome = driver.run("FEAT-B", "plan", plan, Path("."))
    assert outcome.status == "AWAITING_APPROVAL"
    assert outcome.phase == "blueprint"
    assert approver.calls == []


def test_drive_auto_but_release_gate_stays_manual() -> None:
    approver = FakeApprovalExecutor(ok=True)
    driver = _driver_with_approval(ApprovalPolicy(mode=ApprovalMode.AUTO), approver)
    plan = OrchestrationPlan(
        phase_sequence=("plan", "release"),
        approval_gate_phases=frozenset({"release"}),
    )
    outcome = driver.run("FEAT-C", "plan", plan, Path("."))
    assert outcome.status == "AWAITING_APPROVAL"
    assert outcome.phase == "release"
    assert approver.calls == []  # never auto-approved


# ------------------------------ tick (agent-driven) ----------------------- #
def _tick(loop: LoopEnginePort, policy: ApprovalPolicy) -> TickUseCase:
    return TickUseCase(registry=_registry(), loop=loop, policy=policy)


def test_tick_execute_phase_assigns_next_agent() -> None:
    tick = _tick(FakeLoopAdvance(), ApprovalPolicy(mode=ApprovalMode.AUTO))
    plan = OrchestrationPlan(
        phase_sequence=("plan", "implement", "verify"),
        approval_gate_phases=frozenset(),
    )
    result = tick.tick("FEAT-T1", "plan", Verdict.PASS, plan)
    assert result.next_action == "EXECUTE_PHASE"
    assert result.resulting_phase == "implement"
    assert result.assigned_agent == "codex-impl"


def test_tick_auto_approve_returns_command() -> None:
    policy = ApprovalPolicy(
        mode=ApprovalMode.AUTO,
        gate_commands={"blueprint": ("aiwf", "blueprint", "--workflow", "${workflow}",
                                     "--approve")},
    )
    tick = _tick(FakeLoopAdvance(), policy)
    plan = OrchestrationPlan(
        phase_sequence=("plan", "blueprint", "implement"),
        approval_gate_phases=frozenset({"blueprint"}),
    )
    result = tick.tick("FEAT-T2", "plan", Verdict.PASS, plan, gate_evidence=_GATE_PASS)
    assert result.next_action == "AUTO_APPROVE"
    assert result.approval_gate == "blueprint"
    assert result.approval_command == ("aiwf", "blueprint", "--workflow", "FEAT-T2",
                                       "--approve")


def test_tick_await_approval_when_manual() -> None:
    tick = _tick(FakeLoopAdvance(), ApprovalPolicy(mode=ApprovalMode.MANUAL))
    plan = OrchestrationPlan(
        phase_sequence=("plan", "blueprint", "implement"),
        approval_gate_phases=frozenset({"blueprint"}),
    )
    result = tick.tick("FEAT-T3", "plan", Verdict.PASS, plan, gate_evidence=_GATE_PASS)
    assert result.next_action == "AWAIT_APPROVAL"
    assert result.approval_gate == "blueprint"
    assert result.approval_mode == "manual"


def test_tick_await_approval_when_auto_but_no_command() -> None:
    # auto mode, gate allowed, but no gate_commands configured -> cannot self-run.
    tick = _tick(FakeLoopAdvance(), ApprovalPolicy(mode=ApprovalMode.AUTO))
    plan = OrchestrationPlan(
        phase_sequence=("plan", "blueprint", "implement"),
        approval_gate_phases=frozenset({"blueprint"}),
    )
    result = tick.tick("FEAT-T4", "plan", Verdict.PASS, plan, gate_evidence=_GATE_PASS)
    assert result.next_action == "AWAIT_APPROVAL"


def test_tick_code_gate_blocks_without_evidence() -> None:
    # blueprint is a code-gate phase; no evidence -> fail-closed RUN_CODE_BLOCK_GATE.
    tick = _tick(FakeLoopAdvance(), ApprovalPolicy(mode=ApprovalMode.AUTO))
    plan = OrchestrationPlan(
        phase_sequence=("plan", "blueprint", "implement"),
        approval_gate_phases=frozenset({"blueprint"}),
    )
    result = tick.tick("FEAT-T4b", "plan", Verdict.PASS, plan)
    assert result.next_action == "RUN_CODE_BLOCK_GATE"
    assert result.approval_gate == "blueprint"


def test_tick_code_gate_blocks_on_zero_blocks() -> None:
    tick = _tick(FakeLoopAdvance(), ApprovalPolicy(mode=ApprovalMode.AUTO))
    plan = OrchestrationPlan(
        phase_sequence=("plan", "blueprint", "implement"),
        approval_gate_phases=frozenset({"blueprint"}),
    )
    zero = GateEvidence(present=True, decision="PASS", code_block_count=0)
    result = tick.tick("FEAT-T4c", "plan", Verdict.PASS, plan, gate_evidence=zero)
    assert result.next_action == "RUN_CODE_BLOCK_GATE"


def test_tick_code_gate_blocks_when_not_pass() -> None:
    tick = _tick(FakeLoopAdvance(), ApprovalPolicy(mode=ApprovalMode.AUTO))
    plan = OrchestrationPlan(
        phase_sequence=("plan", "blueprint", "implement"),
        approval_gate_phases=frozenset({"blueprint"}),
    )
    blocked = GateEvidence(present=True, decision="BLOCKED", code_block_count=5)
    result = tick.tick("FEAT-T4d", "plan", Verdict.PASS, plan, gate_evidence=blocked)
    assert result.next_action == "RUN_CODE_BLOCK_GATE"


def test_tick_non_code_gate_phase_needs_no_evidence() -> None:
    # A gate NOT in code_gate_phases still approves without gate evidence.
    tick = _tick(FakeLoopAdvance(), ApprovalPolicy(mode=ApprovalMode.MANUAL))
    plan = OrchestrationPlan(
        phase_sequence=("plan", "signoff", "implement"),
        approval_gate_phases=frozenset({"signoff"}),
    )
    result = tick.tick("FEAT-T4e", "plan", Verdict.PASS, plan,
                       code_gate_phases=frozenset({"blueprint"}))
    assert result.next_action == "AWAIT_APPROVAL"
    assert result.approval_gate == "signoff"


class FakeLoopRecord:
    """Records the DecisionRequest so we can assert findings are forwarded."""

    def __init__(self) -> None:
        self.last: DecisionRequest | None = None

    def decide(self, request: DecisionRequest) -> DecisionView:
        self.last = request
        return DecisionView("ADVANCE", request.next_phase or request.phase, (), False, "{}")

    def persist(self, payload_json: str) -> str:
        return ".agents/state/loop/x.json"


def test_tick_forwards_findings_to_loop() -> None:
    loop = FakeLoopRecord()
    tick = TickUseCase(registry=_registry(), loop=loop,
                       policy=ApprovalPolicy(mode=ApprovalMode.AUTO))
    plan = OrchestrationPlan(phase_sequence=("plan", "implement"),
                             approval_gate_phases=frozenset())
    _ = tick.tick("FEAT-TF", "plan", Verdict.BLOCK, plan,
                  findings=("syntax error P01",))
    assert loop.last is not None
    assert loop.last.findings == ("syntax error P01",)


def test_tick_completed_on_final_gate_pass() -> None:
    tick = _tick(FakeLoopAdvance(), ApprovalPolicy(mode=ApprovalMode.AUTO))
    plan = OrchestrationPlan(phase_sequence=("verify",), approval_gate_phases=frozenset())
    result = tick.tick("FEAT-T5", "verify", Verdict.PASS, plan)
    assert result.next_action == "COMPLETED"
    assert "GATE_PASS_FINAL" in result.stop_conditions_met


def test_tick_halt_escalate_on_no_progress() -> None:
    tick = _tick(FakeLoopNoProgress(), ApprovalPolicy(mode=ApprovalMode.AUTO))
    plan = OrchestrationPlan(phase_sequence=("implement",), approval_gate_phases=frozenset())
    result = tick.tick("FEAT-T6", "implement", Verdict.BLOCK, plan)
    assert result.next_action == "HALT_ESCALATE"
    assert len(result.escalation_options) >= 2
