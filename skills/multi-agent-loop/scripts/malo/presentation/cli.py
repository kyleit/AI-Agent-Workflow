"""CLI + composition root for the MALO orchestrator.

Contract:
    malo select  --workflow <id> --phase <phase>
    malo run     --workflow <id> --phases plan,blueprint,implement,verify [--start <phase>]
                 [--approval-gates blueprint,implementation] [--backtrack spike=brainstorming]
                 [--timeout 900] [--max-cycles 24] [--dry-run]

`select` is read-only. `run` drives the loop, spawning the selected agent per
phase, until HALT or a human approval gate. The loop-controller remains the
transition authority (shelled via LoopEngineCli).

Typing: basedpyright strict-full. argparse attributes are `Any`, so every access
is narrowed once through the typed `_ArgReader` boundary (cast → object → narrow).
"""

from __future__ import annotations

import argparse
import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import cast

from malo.application.dto import GateEvidence
from malo.application.use_cases import (
    DEFAULT_APPROVAL_GATES,
    DEFAULT_CODE_GATE_PHASES,
    DEFAULT_MAX_CYCLES,
    DEFAULT_TIMEOUT_S,
    DriveLoopUseCase,
    OrchestrationPlan,
    RunPhaseUseCase,
    TickUseCase,
)
from malo.domain.jsonutil import as_json_object
from malo.domain.results import Verdict
from malo.domain.approval import ApprovalMode
from malo.domain.errors import MaloError
from malo.domain.jsonutil import as_object_list
from malo.domain.selection import select_agent, selection_reason
from malo.infrastructure.approval import (
    CommandApprovalExecutor,
    FileApprovalPolicyRepo,
)
from malo.infrastructure.headless_spawner import SubprocessSpawner
from malo.infrastructure.repositories import FileRegistryRepo, FileResultRepo
from malo.infrastructure.services import FileMailbox, LoopEngineCli, SystemClock


class _ArgReader:
    """Typed boundary over argparse.Namespace (isolates reportAny to one place)."""

    def __init__(self, namespace: argparse.Namespace) -> None:
        self._ns = namespace

    def _raw(self, name: str) -> object:
        return cast(object, getattr(self._ns, name, None))

    def get_str(self, name: str) -> str:
        value = self._raw(name)
        return value if isinstance(value, str) else ""

    def get_opt_str(self, name: str) -> str | None:
        value = self._raw(name)
        return value if isinstance(value, str) else None

    def get_int(self, name: str, default: int) -> int:
        value = self._raw(name)
        return value if isinstance(value, int) and not isinstance(value, bool) else default

    def get_bool(self, name: str) -> bool:
        return self._raw(name) is True

    def get_str_list(self, name: str) -> list[str]:
        return [item for item in as_object_list(self._raw(name)) if isinstance(item, str)]


def _resolve_repo_root(override: str | None) -> Path:
    if override:
        return Path(override).resolve()
    current = Path.cwd().resolve()
    for candidate in (current, *current.parents):
        if (candidate / ".agents").is_dir() or (candidate / ".git").exists():
            return candidate
    return current


def _resolve_loop_scripts() -> Path:
    skills_dir = Path(__file__).resolve().parents[4]
    candidate = skills_dir / "loop-controller" / "scripts"
    if (candidate / "loop_engine" / "__init__.py").is_file():
        return candidate
    raise MaloError(
        "loop-controller engine not found next to multi-agent-loop; "
        "expected skills/loop-controller/scripts."
    )


def _emit(payload: Mapping[str, object]) -> None:
    print(json.dumps(dict(payload), ensure_ascii=False, indent=2, sort_keys=True))


def _parse_backtrack(pairs: Sequence[str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for pair in pairs:
        if "=" not in pair:
            raise MaloError(f"--backtrack expects phase=target, got '{pair}'.")
        phase, target = pair.split("=", 1)
        out[phase.strip()] = target.strip()
    return out


def _cmd_select(reader: _ArgReader, root: Path) -> int:
    registry = FileRegistryRepo().load(root)
    phase = reader.get_str("phase")
    workflow = reader.get_str("workflow")
    candidates = registry.capable_for(phase)
    agent = select_agent(phase, registry)
    if agent is None:
        _emit({
            "workflow_id": workflow, "phase": phase, "selected_agent_id": None,
            "reason": "no enabled agent capable of this phase; run in-session",
            "candidates": [a.id for a in candidates],
        })
        return 0
    _emit({
        "schema": "aiwf.agent-assignment/1",
        "workflow_id": workflow, "phase": phase,
        "selected_agent_id": agent.id, "agent_type": agent.type,
        "reason": selection_reason(agent, phase, len(candidates)),
        "candidates": [a.id for a in candidates],
    })
    return 0


def _cmd_run(reader: _ArgReader, root: Path) -> int:
    workflow = reader.get_str("workflow")
    phases = tuple(p.strip() for p in reader.get_str("phases").split(",") if p.strip())
    if not phases:
        raise MaloError("--phases must list at least one phase.")
    start = reader.get_opt_str("start") or phases[0]
    gates_raw = reader.get_opt_str("approval_gates")
    gates = (
        frozenset(g.strip() for g in gates_raw.split(",") if g.strip())
        if gates_raw else DEFAULT_APPROVAL_GATES
    )
    plan = OrchestrationPlan(
        phase_sequence=phases,
        approval_gate_phases=gates,
        backtrack_targets=_parse_backtrack(reader.get_str_list("backtrack")),
        timeout_s=reader.get_int("timeout", DEFAULT_TIMEOUT_S),
        max_cycles=reader.get_int("max_cycles", DEFAULT_MAX_CYCLES),
    )
    registry = FileRegistryRepo().load(root)

    if reader.get_bool("dry_run"):
        preview: list[dict[str, object]] = []
        for phase in phases:
            agent = select_agent(phase, registry)
            preview.append({
                "phase": phase,
                "agent": agent.id if agent else None,
                "approval_gate": phase in gates,
            })
        _emit({"workflow_id": workflow, "start": start, "dry_run": True, "plan": preview})
        return 0

    policy = FileApprovalPolicyRepo().load(root)
    approval_arg = reader.get_opt_str("approval")
    if approval_arg:
        policy = policy.with_mode(ApprovalMode.parse(approval_arg))
    spawner = SubprocessSpawner()
    driver = DriveLoopUseCase(
        registry=registry,
        run_phase=RunPhaseUseCase(spawner),
        loop=LoopEngineCli(root, _resolve_loop_scripts()),
        result_repo=FileResultRepo(),
        clock=SystemClock(),
        mailbox=FileMailbox(),
        policy=policy,
        approval_executor=CommandApprovalExecutor(policy, spawner),
    )
    outcome = driver.run(workflow, start, plan, root)
    _emit({
        "workflow_id": workflow, "status": outcome.status, "phase": outcome.phase,
        "cycles": outcome.cycles, "detail": outcome.detail,
        "escalation_options": list(outcome.escalation_options),
    })
    return 0 if outcome.status in ("COMPLETED", "AWAITING_APPROVAL") else 3


def _plan_from(reader: _ArgReader) -> tuple[OrchestrationPlan, frozenset[str]]:
    phases = tuple(p.strip() for p in reader.get_str("phases").split(",") if p.strip())
    if not phases:
        raise MaloError("--phases must list at least one phase.")
    gates_raw = reader.get_opt_str("approval_gates")
    gates = (
        frozenset(g.strip() for g in gates_raw.split(",") if g.strip())
        if gates_raw else DEFAULT_APPROVAL_GATES
    )
    plan = OrchestrationPlan(
        phase_sequence=phases,
        approval_gate_phases=gates,
        backtrack_targets=_parse_backtrack(reader.get_str_list("backtrack")),
        timeout_s=reader.get_int("timeout", DEFAULT_TIMEOUT_S),
        max_cycles=reader.get_int("max_cycles", DEFAULT_MAX_CYCLES),
    )
    return plan, gates


def _read_gate_evidence(path_str: str | None, root: Path) -> GateEvidence:
    """Parse a strict-code-block-gate code-block-gate.json into GateEvidence."""
    if not path_str:
        return GateEvidence(present=False)
    path = Path(path_str)
    if not path.is_absolute():
        path = root / path
    if not path.is_file():
        return GateEvidence(present=False)
    data = as_json_object(path.read_text(encoding="utf-8"))
    if data is None:
        return GateEvidence(present=True, decision="", code_block_count=0)
    decision = data.get("decision")
    count = data.get("code_block_count")
    return GateEvidence(
        present=True,
        decision=decision if isinstance(decision, str) else "",
        code_block_count=count if isinstance(count, int) and not isinstance(count, bool) else 0,
    )


def _cmd_tick(reader: _ArgReader, root: Path) -> int:
    """One agent-driven step: decide + persist, then advise the IDE agent."""
    workflow = reader.get_str("workflow")
    from_phase = reader.get_str("phase")
    verdict = Verdict.parse(reader.get_str("verdict"))
    plan, _gates = _plan_from(reader)
    cg_raw = reader.get_opt_str("code_gate_phases")
    code_gate_phases = (
        frozenset(p.strip() for p in cg_raw.split(",") if p.strip())
        if cg_raw is not None else DEFAULT_CODE_GATE_PHASES
    )
    gate_evidence = _read_gate_evidence(reader.get_opt_str("gate_evidence"), root)
    findings = tuple(reader.get_str_list("finding"))
    registry = FileRegistryRepo().load(root)
    policy = FileApprovalPolicyRepo().load(root)
    approval_arg = reader.get_opt_str("approval")
    if approval_arg:
        policy = policy.with_mode(ApprovalMode.parse(approval_arg))
    loop = LoopEngineCli(root, _resolve_loop_scripts())
    result = TickUseCase(registry, loop, policy).tick(
        workflow, from_phase, verdict, plan,
        code_gate_phases=code_gate_phases, gate_evidence=gate_evidence,
        findings=findings,
    )
    _emit({
        "schema": "aiwf.loop-tick/1",
        "workflow_id": workflow,
        "next_action": result.next_action,
        "phase": result.phase,
        "transition": result.transition,
        "resulting_phase": result.resulting_phase,
        "assigned_agent": result.assigned_agent,
        "approval_gate": result.approval_gate,
        "approval_mode": result.approval_mode,
        "approval_command": list(result.approval_command),
        "stop_conditions_met": list(result.stop_conditions_met),
        "escalation_options": list(result.escalation_options),
        "detail": result.detail,
    })
    return 0 if result.next_action not in ("HALTED", "HALT_ESCALATE") else 3


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="malo", description="AIWF multi-agent loop orchestrator.")
    common = argparse.ArgumentParser(add_help=False)
    _ = common.add_argument("--repo-root", default=None)
    sub = parser.add_subparsers(dest="command", required=True)

    sel = sub.add_parser("select", parents=[common], help="Select the agent for a phase.")
    _ = sel.add_argument("--workflow", required=True)
    _ = sel.add_argument("--phase", required=True)

    run = sub.add_parser("run", parents=[common], help="Drive the loop across agents.")
    _ = run.add_argument("--workflow", required=True)
    _ = run.add_argument("--phases", required=True)
    _ = run.add_argument("--start", default=None)
    _ = run.add_argument("--approval-gates", default=None)
    _ = run.add_argument("--backtrack", action="append", default=[])
    _ = run.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT_S)
    _ = run.add_argument("--max-cycles", type=int, default=DEFAULT_MAX_CYCLES)
    _ = run.add_argument("--approval", choices=["auto", "manual"], default=None,
                         help="Override approval mode (default: config, else auto).")
    _ = run.add_argument("--dry-run", action="store_true")

    tick = sub.add_parser(
        "tick", parents=[common],
        help="One agent-driven step: decide + persist, advise next action.",
    )
    _ = tick.add_argument("--workflow", required=True)
    _ = tick.add_argument("--phase", required=True, help="Phase just executed.")
    _ = tick.add_argument("--verdict", required=True,
                          help="Verdict of that phase: PASS | BLOCK | FAIL | ERROR.")
    _ = tick.add_argument("--phases", required=True)
    _ = tick.add_argument("--approval-gates", default=None)
    _ = tick.add_argument("--backtrack", action="append", default=[])
    _ = tick.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT_S)
    _ = tick.add_argument("--max-cycles", type=int, default=DEFAULT_MAX_CYCLES)
    _ = tick.add_argument("--approval", choices=["auto", "manual"], default=None,
                          help="Override approval mode (default: config, else auto).")
    _ = tick.add_argument("--code-gate-phases", default=None,
                          help="CSV of phases that REQUIRE a passing CODE_BLOCK_GATE "
                               "before approval (default: blueprint,implementation,"
                               "implementation-entry).")
    _ = tick.add_argument("--gate-evidence", default=None,
                          help="Path to code-block-gate.json from strict-code-block-gate. "
                               "A code-gate phase without a passing, non-empty gate "
                               "returns RUN_CODE_BLOCK_GATE (fail-closed).")
    _ = tick.add_argument("--finding", action="append", default=[],
                          help="A verdict finding (repeatable). Identical findings across "
                               "cycles drive NO_PROGRESS detection -> HALT+escalate (the "
                               "repair-loop cap). Pass the phase's failure reason on BLOCK/FAIL.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    reader = _ArgReader(args)
    root = _resolve_repo_root(reader.get_opt_str("repo_root"))
    command = reader.get_str("command")
    try:
        if command == "select":
            return _cmd_select(reader, root)
        if command == "run":
            return _cmd_run(reader, root)
        if command == "tick":
            return _cmd_tick(reader, root)
    except MaloError as exc:
        _emit({"error": type(exc).__name__, "message": str(exc)})
        return 2
    parser.error(f"unknown command: {command}")
    return 2
