"""The pure transition decision function.

This is the deterministic heart of the loop controller. Given a
`DecisionInput` it returns a `DecisionResult` with exactly one transition
from `{ADVANCE, REPEAT, BACKTRACK, HALT}`. It performs no IO and reads no
clock. PROTOCOL.md reproduces this table verbatim for hand-execution.

Iteration semantics:
  - REPEAT   -> iteration + 1 (rework the same phase; bounded by max_iterations)
  - ADVANCE  -> iteration reset to 0 (fresh budget for the next phase)
  - BACKTRACK-> iteration reset to 0 (fresh budget for the targeted phase)
  - HALT     -> iteration recorded at candidate value (current + 1)

No-progress semantics:
  - Same non-empty failure_signature on a non-PASS verdict increments the
    counter; anything else (PASS, or a changed/empty signature) resets it.
"""

from __future__ import annotations

from loop_engine.domain.models import (
    DecisionInput,
    DecisionResult,
    LoopState,
    StopCondition,
    Transition,
    Verdict,
)
from loop_engine.domain.stop_conditions import (
    evaluate_stop_conditions,
    requires_escalation,
)


def _escalation_options(backtrack_target: str | None) -> tuple[str, ...]:
    target = backtrack_target or "brainstorming"
    return (
        f"BACKTRACK to upstream phase '{target}' and re-derive the approach",
        "REVISE inputs / narrow scope, then REPEAT the current phase",
        "CANCEL the workflow (user HALT)",
    )


def _project_no_progress(inp: DecisionInput) -> int:
    """Compute the no-progress counter value resulting from this cycle."""
    if inp.verdict is Verdict.PASS:
        return 0
    prev = inp.current_state.failure_signature
    current = inp.new_failure_signature
    same_signature = bool(current) and current == prev
    if same_signature:
        return inp.current_state.no_progress_count + 1
    return 0


def decide(inp: DecisionInput) -> DecisionResult:
    """Return the deterministic transition decision for one controller cycle."""
    state = inp.current_state
    candidate_iteration = state.iteration + 1
    projected_no_progress = _project_no_progress(inp)

    stops = evaluate_stop_conditions(
        inp,
        candidate_iteration=candidate_iteration,
        projected_no_progress=projected_no_progress,
    )

    if stops:
        return DecisionResult(
            transition=Transition.HALT,
            resulting_phase=state.current_phase,
            next_iteration=candidate_iteration,
            no_progress_count=projected_no_progress,
            stop_conditions_met=tuple(stops),
            backtrack_target=None,
            escalate=requires_escalation(stops),
            escalation_options=(
                _escalation_options(inp.backtrack_target)
                if requires_escalation(stops)
                else ()
            ),
        )

    approval_ok = (not inp.requires_approval) or inp.approval_present

    if inp.verdict is Verdict.PASS:
        if not approval_ok:
            # Quality passed but the phase's approval is still pending: hold in
            # the same phase (REPEAT) until an approval record exists.
            return _repeat(state, candidate_iteration, projected_no_progress)
        next_phase = inp.next_phase or state.current_phase
        return DecisionResult(
            transition=Transition.ADVANCE,
            resulting_phase=next_phase,
            next_iteration=0,
            no_progress_count=0,
            stop_conditions_met=(),
            backtrack_target=None,
            escalate=False,
        )

    if inp.verdict is Verdict.FAIL and inp.backtrack_target:
        return DecisionResult(
            transition=Transition.BACKTRACK,
            resulting_phase=inp.backtrack_target,
            next_iteration=0,
            no_progress_count=projected_no_progress,
            stop_conditions_met=(),
            backtrack_target=inp.backtrack_target,
            escalate=False,
        )

    # BLOCK, or FAIL without a named backtrack target: refine the same phase.
    return _repeat(state, candidate_iteration, projected_no_progress)


def _repeat(
    state: LoopState, candidate_iteration: int, projected_no_progress: int
) -> DecisionResult:
    return DecisionResult(
        transition=Transition.REPEAT,
        resulting_phase=state.current_phase,
        next_iteration=candidate_iteration,
        no_progress_count=projected_no_progress,
        stop_conditions_met=(),
        backtrack_target=None,
        escalate=False,
    )


# Kept for callers that only need the enum set without importing StopCondition.
ALL_STOP_CONDITIONS: tuple[StopCondition, ...] = tuple(StopCondition)
