"""Application DTOs for the MALO use cases."""

from __future__ import annotations

from dataclasses import dataclass, field

from malo.domain.results import Verdict


@dataclass(frozen=True)
class SpawnOutcome:
    """Raw result of running a headless agent process."""

    exit_code: int
    stdout: str
    stderr: str
    duration_s: float
    timed_out: bool = False


@dataclass(frozen=True)
class DecisionRequest:
    """Inputs the loop-controller needs to DECIDE the next transition."""

    workflow_id: str
    phase: str
    verdict: Verdict
    findings: tuple[str, ...] = field(default_factory=tuple)
    next_phase: str | None = None
    backtrack_target: str | None = None
    requires_approval: bool = False
    approval_present: bool = False
    is_terminal_phase: bool = False


@dataclass(frozen=True)
class DecisionView:
    """The loop-controller's decision, plus the payload to persist."""

    transition: str
    resulting_phase: str
    stop_conditions_met: tuple[str, ...]
    escalate: bool
    persist_payload_json: str


@dataclass(frozen=True)
class DriveOutcome:
    """Terminal outcome of driving the loop."""

    status: str  # COMPLETED | AWAITING_APPROVAL | HALTED_ESCALATE | HALTED | NEEDS_SESSION_AGENT | MAX_CYCLES
    phase: str
    cycles: int
    detail: str = ""
    escalation_options: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class GateEvidence:
    """Parsed CODE_BLOCK_GATE result bound to a blueprint (from code-block-gate.json).

    `present` is False when no evidence file was supplied — a code-gate phase then
    fails closed (RUN_CODE_BLOCK_GATE), never approve.
    """

    present: bool = False
    decision: str = ""
    code_block_count: int = 0

    def passes(self) -> bool:
        return self.present and self.decision == "PASS" and self.code_block_count > 0


@dataclass(frozen=True)
class TickResult:
    """One agent-driven step: what the IDE agent should do next.

    The agent (Claude/Codex/Antigravity) is the worker AND the driver — it calls
    `aiwf malo tick` each turn, does `next_action` itself (no subprocess spawn),
    then ticks again. `run` (headless spawn) remains the autonomous alternative.
    """

    next_action: str  # EXECUTE_PHASE | AUTO_APPROVE | AWAIT_APPROVAL | RUN_CODE_BLOCK_GATE | COMPLETED | HALTED | HALT_ESCALATE
    phase: str
    transition: str
    resulting_phase: str
    assigned_agent: str | None = None
    approval_gate: str | None = None
    approval_mode: str | None = None
    approval_command: tuple[str, ...] = field(default_factory=tuple)
    stop_conditions_met: tuple[str, ...] = field(default_factory=tuple)
    escalation_options: tuple[str, ...] = field(default_factory=tuple)
    detail: str = ""
