"""Stop-condition evaluation (pure domain policy).

Order of evaluation is deterministic and must match PROTOCOL.md exactly so a
hand-run agent reaches an identical HALT decision.
"""

from __future__ import annotations

from loop_engine.domain.models import (
    DecisionInput,
    StopCondition,
    Verdict,
)


def evaluate_stop_conditions(
    inp: DecisionInput,
    candidate_iteration: int,
    projected_no_progress: int,
) -> list[StopCondition]:
    """Return every stop-condition that holds for this cycle (may be empty).

    Args:
        inp: the decision input for this cycle.
        candidate_iteration: iteration value assuming another rework attempt
            (i.e. current iteration + 1).
        projected_no_progress: the no-progress counter after this cycle.
    """
    stops: list[StopCondition] = []

    # 1. Explicit user halt always wins.
    if inp.user_halt:
        stops.append(StopCondition.USER_HALT)

    # 2. Unrecoverable error.
    if inp.verdict is Verdict.ERROR:
        stops.append(StopCondition.UNRECOVERABLE_ERROR)

    # 3. Iteration ceiling (hard anti-infinite-loop guard for rework).
    if candidate_iteration >= inp.current_state.max_iterations:
        stops.append(StopCondition.MAX_ITERATIONS)

    # 4. No-progress detector: same failure_signature for K consecutive cycles.
    if projected_no_progress >= inp.current_state.no_progress_threshold:
        stops.append(StopCondition.NO_PROGRESS)

    # 5. Successful terminal completion (gate PASS + approval on final phase).
    approval_ok = (not inp.requires_approval) or inp.approval_present
    if inp.verdict is Verdict.PASS and approval_ok and inp.is_terminal_phase:
        stops.append(StopCondition.GATE_PASS_FINAL)

    return stops


def requires_escalation(stops: list[StopCondition]) -> bool:
    """Escalate to the user for stuck/exhausted loops, not for clean success."""
    return (
        StopCondition.NO_PROGRESS in stops
        or StopCondition.MAX_ITERATIONS in stops
    )
