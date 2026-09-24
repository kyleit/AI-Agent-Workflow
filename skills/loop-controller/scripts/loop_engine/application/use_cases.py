"""Loop engine use cases (load | decide | persist).

Each use case receives its collaborators through the constructor (DI). The
domain decision function stays pure; only persist touches the clock and the
repositories.
"""

from __future__ import annotations

from dataclasses import replace

from loop_engine.application.dto import (
    DecideOutput,
    PersistInput,
    PersistOutput,
)
from loop_engine.application.ports import (
    Clock,
    HashService,
    LoopLedgerRepository,
    LoopStateRepository,
)
from loop_engine.domain.ledger import LedgerEntry
from loop_engine.domain.models import (
    DEFAULT_MAX_ITERATIONS,
    DEFAULT_NO_PROGRESS_THRESHOLD,
    DecisionInput,
    LoopState,
)
from loop_engine.domain.serialization import to_canonical_json
from loop_engine.domain.transitions import decide


class LoadLoopStateUseCase:
    """LOAD: read the loop state, initializing iteration 0 when absent."""

    def __init__(self, state_repo: LoopStateRepository) -> None:
        self._state_repo = state_repo

    def execute(
        self,
        workflow_id: str,
        default_phase: str,
        *,
        max_iterations: int = DEFAULT_MAX_ITERATIONS,
        no_progress_threshold: int = DEFAULT_NO_PROGRESS_THRESHOLD,
    ) -> LoopState:
        existing = self._state_repo.load(workflow_id)
        if existing is not None:
            return existing
        return LoopState.initial(
            workflow_id,
            default_phase,
            max_iterations=max_iterations,
            no_progress_threshold=no_progress_threshold,
        )


class DecideUseCase:
    """DECIDE: compute the transition and build the (unstamped) next state.

    Pure and deterministic; no clock, no IO. The produced next_state and
    ledger_entry carry no timestamp — persist stamps them.
    """

    def execute(
        self,
        inp: DecisionInput,
        *,
        gate: str | None = None,
        evidence_refs: tuple[str, ...] = (),
    ) -> DecideOutput:
        result = decide(inp)
        prev = inp.current_state
        next_state = replace(
            prev,
            current_phase=result.resulting_phase,
            iteration=result.next_iteration,
            no_progress_count=result.no_progress_count,
            last_verdict=inp.verdict.value,
            failure_signature=inp.new_failure_signature,
            transition=result.transition.value,
            backtrack_target=result.backtrack_target,
            stop_conditions_met=tuple(result.stop_values()),
            updated_at=None,
        )
        ledger_entry = LedgerEntry(
            iteration=result.next_iteration,
            phase=prev.current_phase,
            action=result.transition.value,
            verdict=inp.verdict.value,
            next_phase=result.resulting_phase,
            gate=gate,
            evidence_refs=evidence_refs,
        )
        return DecideOutput(
            decision=result,
            next_state=next_state,
            ledger_entry=ledger_entry,
        )


class PersistLoopUseCase:
    """PERSIST: atomically write the state and append one ledger row."""

    def __init__(
        self,
        state_repo: LoopStateRepository,
        ledger_repo: LoopLedgerRepository,
        clock: Clock,
        hasher: HashService,
    ) -> None:
        self._state_repo = state_repo
        self._ledger_repo = ledger_repo
        self._clock = clock
        self._hasher = hasher

    def execute(self, payload: PersistInput) -> PersistOutput:
        ts = self._clock.now_iso()
        stamped_state = replace(payload.next_state, updated_at=ts)
        content = to_canonical_json(stamped_state.to_dict())
        state_sha256 = self._hasher.sha256_hex(content)

        state_path = self._state_repo.save(stamped_state)
        ledger_path = self._ledger_repo.append(
            stamped_state.workflow_id,
            payload.ledger_entry.with_timestamp(ts),
        )
        return PersistOutput(
            state_path=state_path,
            ledger_path=ledger_path,
            state_sha256=state_sha256,
            updated_at=ts,
        )
