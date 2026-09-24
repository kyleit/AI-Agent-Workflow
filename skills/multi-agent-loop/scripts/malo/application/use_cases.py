"""MALO use cases: select agent -> run phase (spawn) -> drive loop.

The loop-controller remains the transition authority (via LoopEnginePort);
these use cases add selection, headless execution, result recording, and the
continuous drive that stops at HALT or a human approval gate.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path

from malo.application.dto import (
    DecisionRequest,
    DriveOutcome,
    GateEvidence,
    TickResult,
)
from malo.application.ports import (
    AgentSpawner,
    ApprovalExecutor,
    Clock,
    LoopEnginePort,
    MailboxPort,
    ResultRepo,
)
from malo.domain.approval import ApprovalDecision, ApprovalMode, ApprovalPolicy
from malo.domain.invocation import build_headless_command
from malo.domain.models import AgentDescriptor, AgentRegistry
from malo.domain.results import (
    PhaseRunResult,
    Verdict,
    normalize_verdict,
    redact_command,
)
from malo.domain.selection import select_agent

DEFAULT_APPROVAL_GATES = frozenset({"blueprint", "implementation", "implementation-entry"})
# Gates that MUST have a passing CODE_BLOCK_GATE artifact before approval can even
# be offered (no code blocks => no approval, even in auto mode). Fail-closed.
DEFAULT_CODE_GATE_PHASES = frozenset({"blueprint", "implementation", "implementation-entry"})
DEFAULT_TIMEOUT_S = 900
DEFAULT_MAX_CYCLES = 24


def _empty_str_map() -> dict[str, str]:
    return {}


@dataclass(frozen=True)
class OrchestrationPlan:
    """Phase ordering + gate/backtrack policy driving the loop."""

    phase_sequence: tuple[str, ...]
    approval_gate_phases: frozenset[str] = DEFAULT_APPROVAL_GATES
    backtrack_targets: Mapping[str, str] = field(default_factory=_empty_str_map)
    timeout_s: int = DEFAULT_TIMEOUT_S
    max_cycles: int = DEFAULT_MAX_CYCLES

    def next_of(self, phase: str) -> str | None:
        if phase in self.phase_sequence:
            idx = self.phase_sequence.index(phase)
            if idx + 1 < len(self.phase_sequence):
                return self.phase_sequence[idx + 1]
        return None

    def is_terminal(self, phase: str) -> bool:
        return bool(self.phase_sequence) and phase == self.phase_sequence[-1]

    def backtrack_of(self, phase: str) -> str | None:
        return self.backtrack_targets.get(phase)


def compose_phase_task(workflow_id: str, phase: str) -> str:
    return (
        f"Run the AIWF '{phase}' phase for workflow {workflow_id} in this shared "
        f"workspace via /aiwf. Do the phase work, then print exactly one verdict "
        f"token on the last line: PASS (phase done), BLOCK (needs another pass), "
        f"or FAIL (route back upstream)."
    )


def _extract_findings(stdout: str, stderr: str, verdict_pass: bool) -> tuple[str, ...]:
    if verdict_pass:
        return ()
    source = (stderr.strip() or stdout.strip())
    if not source:
        return ()
    last = source.splitlines()[-1].strip()
    return (last,) if last else ()


class RunPhaseUseCase:
    """Spawn the chosen agent headless for one phase and build its result."""

    def __init__(self, spawner: AgentSpawner) -> None:
        self._spawner = spawner

    def execute(
        self,
        workflow_id: str,
        phase: str,
        agent: AgentDescriptor,
        root: Path,
        timeout_s: int,
    ) -> PhaseRunResult:
        subs = {"task": compose_phase_task(workflow_id, phase),
                "workflow": workflow_id, "phase": phase}
        command = build_headless_command(agent, subs)
        outcome = self._spawner.run(command, root, timeout_s)
        verdict = normalize_verdict(outcome.exit_code, outcome.stdout)
        findings = _extract_findings(
            outcome.stdout, outcome.stderr, verdict.value == "PASS"
        )
        return PhaseRunResult(
            workflow_id=workflow_id,
            phase=phase,
            agent_id=agent.id,
            agent_type=agent.type,
            verdict=verdict,
            exit_code=outcome.exit_code,
            duration_s=outcome.duration_s,
            command_redacted=redact_command(command, subs),
            findings=findings,
        )


class DriveLoopUseCase:
    """Continuously drive the loop across agents until HALT or an approval gate."""

    def __init__(
        self,
        registry: AgentRegistry,
        run_phase: RunPhaseUseCase,
        loop: LoopEnginePort,
        result_repo: ResultRepo,
        clock: Clock,
        mailbox: MailboxPort | None = None,
        policy: ApprovalPolicy | None = None,
        approval_executor: ApprovalExecutor | None = None,
    ) -> None:
        self._registry = registry
        self._run_phase = run_phase
        self._loop = loop
        self._result_repo = result_repo
        self._clock = clock
        self._mailbox = mailbox
        self._policy = policy or ApprovalPolicy(mode=ApprovalMode.MANUAL)
        self._approval_executor = approval_executor

    def run(
        self,
        workflow_id: str,
        start_phase: str,
        plan: OrchestrationPlan,
        root: Path,
    ) -> DriveOutcome:
        history: dict[str, int] = {}
        current = start_phase
        for cycle in range(1, plan.max_cycles + 1):
            if current in plan.approval_gate_phases:
                if (
                    self._policy.decide(current) is ApprovalDecision.AUTO
                    and self._approval_executor is not None
                    and self._approval_executor.approve(current, workflow_id, root)
                ):
                    if self._mailbox is not None:
                        self._mailbox.post(
                            root, workflow_id, "auto-approval",
                            f"{current}: auto-approved",
                        )
                    nxt = plan.next_of(current)
                    if nxt is None:
                        return DriveOutcome(
                            "COMPLETED", current, cycle - 1,
                            f"auto-approved terminal gate '{current}'",
                        )
                    current = nxt
                    continue
                return DriveOutcome(
                    "AWAITING_APPROVAL", current, cycle - 1,
                    f"human approval required at '{current}'",
                )
            agent = select_agent(current, self._registry, history)
            if agent is None:
                return DriveOutcome(
                    "NEEDS_SESSION_AGENT", current, cycle - 1,
                    f"no enabled agent capable of phase '{current}'; run in-session",
                )
            result = self._run_phase.execute(
                workflow_id, current, agent, root, plan.timeout_s
            )
            self._result_repo.append(root, result.with_timestamp(self._clock.now_iso()))
            if self._mailbox is not None:
                self._mailbox.post(
                    root, workflow_id, agent.id,
                    f"{current} -> {result.verdict.value}",
                )
            decision = self._loop.decide(DecisionRequest(
                workflow_id=workflow_id,
                phase=current,
                verdict=result.verdict,
                findings=result.findings,
                next_phase=plan.next_of(current),
                backtrack_target=plan.backtrack_of(current),
                is_terminal_phase=plan.is_terminal(current),
            ))
            _ = self._loop.persist(decision.persist_payload_json)
            history[agent.id] = history.get(agent.id, 0) + 1

            if decision.transition == "HALT":
                stops = decision.stop_conditions_met
                if "GATE_PASS_FINAL" in stops:
                    return DriveOutcome("COMPLETED", current, cycle, "feature complete")
                if decision.escalate:
                    return DriveOutcome(
                        "HALTED_ESCALATE", current, cycle, "; ".join(stops),
                        escalation_options=(
                            "BACKTRACK to an upstream phase and re-derive",
                            "REVISE scope, then re-run",
                            "CANCEL the workflow",
                        ),
                    )
                return DriveOutcome("HALTED", current, cycle, "; ".join(stops))
            current = decision.resulting_phase
        return DriveOutcome("MAX_CYCLES", current, plan.max_cycles, "reached max cycles")


class TickUseCase:
    """One agent-driven step: decide + persist, then tell the IDE agent what to do.

    The agent is the worker AND the driver: it executes phases as itself and, at
    an auto gate, runs the returned approval command itself (no subprocess spawn).
    """

    def __init__(
        self,
        registry: AgentRegistry,
        loop: LoopEnginePort,
        policy: ApprovalPolicy,
    ) -> None:
        self._registry = registry
        self._loop = loop
        self._policy = policy

    def tick(
        self,
        workflow_id: str,
        from_phase: str,
        verdict: Verdict,
        plan: OrchestrationPlan,
        code_gate_phases: frozenset[str] = DEFAULT_CODE_GATE_PHASES,
        gate_evidence: GateEvidence | None = None,
        findings: tuple[str, ...] = (),
    ) -> TickResult:
        decision = self._loop.decide(DecisionRequest(
            workflow_id=workflow_id,
            phase=from_phase,
            verdict=verdict,
            findings=findings,
            next_phase=plan.next_of(from_phase),
            backtrack_target=plan.backtrack_of(from_phase),
            is_terminal_phase=plan.is_terminal(from_phase),
        ))
        _ = self._loop.persist(decision.persist_payload_json)

        if decision.transition == "HALT":
            stops = decision.stop_conditions_met
            if "GATE_PASS_FINAL" in stops:
                return TickResult("COMPLETED", from_phase, "HALT", from_phase,
                                  stop_conditions_met=stops, detail="feature complete")
            if decision.escalate:
                return TickResult(
                    "HALT_ESCALATE", from_phase, "HALT", from_phase,
                    stop_conditions_met=stops, detail="; ".join(stops),
                    escalation_options=(
                        "BACKTRACK to an upstream phase and re-derive",
                        "REVISE scope, then continue",
                        "CANCEL the workflow",
                    ),
                )
            return TickResult("HALTED", from_phase, "HALT", from_phase,
                              stop_conditions_met=stops, detail="; ".join(stops))

        resulting = decision.resulting_phase
        if resulting in plan.approval_gate_phases:
            # Fail-closed: a code-gate phase (blueprint/implementation) may NOT
            # reach approval without a passing, non-empty CODE_BLOCK_GATE artifact.
            # This stops a code-less/contract-only blueprint from being approved
            # (even under auto mode) in the agent-driven loop.
            if resulting in code_gate_phases and not (
                gate_evidence is not None and gate_evidence.passes()
            ):
                reason = "no CODE_BLOCK_GATE evidence provided"
                if gate_evidence is not None and gate_evidence.present:
                    reason = (
                        f"CODE_BLOCK_GATE decision={gate_evidence.decision or 'UNKNOWN'}, "
                        f"code_block_count={gate_evidence.code_block_count}"
                    )
                return TickResult(
                    "RUN_CODE_BLOCK_GATE", resulting, decision.transition, resulting,
                    approval_gate=resulting,
                    detail=(
                        f"blocked before approval of '{resulting}': {reason}. Run the "
                        f"strict code-block gate (real full-file blocks), then tick "
                        f"again with --gate-evidence pointing at code-block-gate.json"
                    ),
                )
            if self._policy.decide(resulting) is ApprovalDecision.AUTO:
                command = self._policy.rendered_command(resulting, workflow_id)
                if command:
                    return TickResult(
                        "AUTO_APPROVE", resulting, decision.transition, resulting,
                        approval_gate=resulting, approval_mode="auto",
                        approval_command=command,
                        detail=(f"run the approval command yourself, then tick again "
                                f"with --phase {resulting} --verdict PASS"),
                    )
            return TickResult(
                "AWAIT_APPROVAL", resulting, decision.transition, resulting,
                approval_gate=resulting, approval_mode="manual",
                detail=f"human approval required at '{resulting}'; stop and ask the user",
            )

        agent = select_agent(resulting, self._registry)
        return TickResult(
            "EXECUTE_PHASE", resulting, decision.transition, resulting,
            assigned_agent=agent.id if agent else None,
            detail=(f"execute phase '{resulting}'"
                    + ("" if agent else " (no capable agent; run it in this session)")),
        )
