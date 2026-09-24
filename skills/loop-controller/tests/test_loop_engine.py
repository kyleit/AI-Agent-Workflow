"""BAT + unit acceptance tests for the AIWF loop-controller engine.

Covers the five behavioral acceptance scenarios from the upgrade contract plus
supporting unit checks. Deterministic and pure where possible; load/persist use
in-memory fakes so no filesystem is touched.

Each test is stated as: input -> expected (transition / stop-condition / gate).
"""

from __future__ import annotations

import pytest

from loop_engine.application.dto import PersistInput
from loop_engine.application.use_cases import (
    DecideUseCase,
    LoadLoopStateUseCase,
    PersistLoopUseCase,
)
from loop_engine.domain.ledger import LedgerEntry
from loop_engine.domain.models import (
    DecisionInput,
    LoopState,
    StopCondition,
    Transition,
    Verdict,
)
from loop_engine.domain.signature import compute_failure_signature
from loop_engine.domain.transitions import decide

pytestmark = pytest.mark.unit


# --------------------------------------------------------------------------- #
# In-memory fakes for the application ports (DI).
# --------------------------------------------------------------------------- #
class FakeStateRepo:
    def __init__(self, initial: LoopState | None = None) -> None:
        self.saved: LoopState | None = initial

    def load(self, workflow_id: str) -> LoopState | None:
        return self.saved

    def save(self, state: LoopState) -> str:
        self.saved = state
        return f".agents/state/loop/{state.workflow_id}.json"


class FakeLedgerRepo:
    def __init__(self) -> None:
        self.entries: list[LedgerEntry] = []

    def append(self, workflow_id: str, entry: LedgerEntry) -> str:
        self.entries.append(entry)
        return f".agents/state/loop/{workflow_id}.ledger.jsonl"


class FixedClock:
    def now_iso(self) -> str:
        return "2026-09-18T00:00:00Z"


class FakeHasher:
    def sha256_hex(self, payload: str) -> str:
        return "deadbeef"


def _state(**kw: object) -> LoopState:
    base: dict[str, object] = {"workflow_id": "WF", "current_phase": "blueprint"}
    base.update(kw)
    return LoopState.from_dict(base)


# --------------------------------------------------------------------------- #
# BAT #1 — max iterations -> HALT + escalate
# --------------------------------------------------------------------------- #
def test_bat1_max_iterations_halts_and_escalates() -> None:
    st = _state(iteration=7, max_iterations=8)
    result = decide(
        DecisionInput(current_state=st, verdict=Verdict.BLOCK, new_failure_signature="a")
    )
    assert result.transition is Transition.HALT
    assert StopCondition.MAX_ITERATIONS in result.stop_conditions_met
    assert result.escalate is True
    assert len(result.escalation_options) >= 2


# --------------------------------------------------------------------------- #
# BAT #2 — same failure signature x threshold -> HALT NO_PROGRESS
# --------------------------------------------------------------------------- #
def test_bat2_no_progress_halts_after_threshold() -> None:
    st = _state(no_progress_count=2, no_progress_threshold=3, failure_signature="sig")
    result = decide(
        DecisionInput(
            current_state=st, verdict=Verdict.BLOCK, new_failure_signature="sig"
        )
    )
    assert result.transition is Transition.HALT
    assert StopCondition.NO_PROGRESS in result.stop_conditions_met
    assert result.escalate is True


def test_bat2_changed_signature_resets_no_progress() -> None:
    st = _state(no_progress_count=2, no_progress_threshold=3, failure_signature="old")
    result = decide(
        DecisionInput(
            current_state=st, verdict=Verdict.BLOCK, new_failure_signature="new"
        )
    )
    assert result.transition is Transition.REPEAT
    assert result.no_progress_count == 0


# --------------------------------------------------------------------------- #
# BAT #3 — Blueprint with an unspiked risk=high -> Freeze BLOCKED (loop REPEAT)
#          The Spike Gate emits BLOCK on the (non-terminal) blueprint phase, so
#          the loop cannot ADVANCE to Freeze.
# --------------------------------------------------------------------------- #
def test_bat3_unverified_spike_blocks_freeze() -> None:
    st = _state(current_phase="blueprint")
    result = decide(
        DecisionInput(
            current_state=st,
            verdict=Verdict.BLOCK,  # SPIKE_UNVERIFIED blocking condition
            new_failure_signature="spike_unverified",
            is_terminal_phase=False,
        )
    )
    assert result.transition is Transition.REPEAT
    assert result.resulting_phase == "blueprint"  # Freeze not reached


# --------------------------------------------------------------------------- #
# BAT #4 — Spike fail -> BACKTRACK to brainstorming
# --------------------------------------------------------------------------- #
def test_bat4_spike_fail_backtracks_to_brainstorming() -> None:
    st = _state(current_phase="blueprint")
    result = decide(
        DecisionInput(
            current_state=st,
            verdict=Verdict.FAIL,
            new_failure_signature="spike-001-fail",
            backtrack_target="brainstorming",
        )
    )
    assert result.transition is Transition.BACKTRACK
    assert result.resulting_phase == "brainstorming"
    assert result.next_iteration == 0


# --------------------------------------------------------------------------- #
# BAT #5 — Spike user-waived -> gate PASS -> Freeze reachable (ADVANCE)
# --------------------------------------------------------------------------- #
def test_bat5_spike_waived_allows_advance_to_freeze() -> None:
    st = _state(current_phase="blueprint")
    result = decide(
        DecisionInput(
            current_state=st,
            verdict=Verdict.PASS,  # spike_verified via user waiver
            next_phase="freeze",
        )
    )
    assert result.transition is Transition.ADVANCE
    assert result.resulting_phase == "freeze"


# --------------------------------------------------------------------------- #
# Supporting transitions.
# --------------------------------------------------------------------------- #
def test_advance_on_pass_nonterminal() -> None:
    st = _state(current_phase="requirements")
    result = decide(
        DecisionInput(current_state=st, verdict=Verdict.PASS, next_phase="brainstorming")
    )
    assert result.transition is Transition.ADVANCE
    assert result.resulting_phase == "brainstorming"


def test_repeat_when_pass_but_approval_missing() -> None:
    st = _state(current_phase="blueprint")
    result = decide(
        DecisionInput(
            current_state=st,
            verdict=Verdict.PASS,
            requires_approval=True,
            approval_present=False,
            next_phase="implementation",
        )
    )
    assert result.transition is Transition.REPEAT
    assert result.resulting_phase == "blueprint"


def test_halt_gate_pass_final_on_terminal() -> None:
    st = _state(current_phase="verify")
    result = decide(
        DecisionInput(current_state=st, verdict=Verdict.PASS, is_terminal_phase=True)
    )
    assert result.transition is Transition.HALT
    assert StopCondition.GATE_PASS_FINAL in result.stop_conditions_met
    assert result.escalate is False


def test_error_verdict_halts_unrecoverable() -> None:
    result = decide(DecisionInput(current_state=_state(), verdict=Verdict.ERROR))
    assert result.transition is Transition.HALT
    assert StopCondition.UNRECOVERABLE_ERROR in result.stop_conditions_met


def test_user_halt() -> None:
    result = decide(
        DecisionInput(current_state=_state(), verdict=Verdict.BLOCK, user_halt=True)
    )
    assert result.transition is Transition.HALT
    assert StopCondition.USER_HALT in result.stop_conditions_met


# --------------------------------------------------------------------------- #
# Signature policy.
# --------------------------------------------------------------------------- #
def test_signature_order_independent_and_empty() -> None:
    assert compute_failure_signature(["B", "a "]) == compute_failure_signature(["a", "b"])
    assert compute_failure_signature([]) == ""
    assert compute_failure_signature(["x"]) != compute_failure_signature(["y"])


# --------------------------------------------------------------------------- #
# Backward compatibility + persistence (load/decide/persist round trip).
# --------------------------------------------------------------------------- #
def test_backward_compat_missing_state_starts_iteration_zero() -> None:
    load = LoadLoopStateUseCase(FakeStateRepo(initial=None))
    st = load.execute("WF-NEW", "intake")
    assert st.iteration == 0
    assert st.schema == "aiwf.loop/1"
    assert st.no_progress_threshold == 3


def test_persist_writes_state_and_ledger_with_timestamp() -> None:
    state_repo = FakeStateRepo()
    ledger_repo = FakeLedgerRepo()
    decided = DecideUseCase().execute(
        DecisionInput(
            current_state=_state(current_phase="blueprint"),
            verdict=Verdict.FAIL,
            new_failure_signature="s",
            backtrack_target="brainstorming",
        ),
        gate="SPIKE_GATE",
        evidence_refs=(".agents/spikes/spike-001/log.txt",),
    )
    out = PersistLoopUseCase(
        state_repo, ledger_repo, FixedClock(), FakeHasher()
    ).execute(PersistInput(decided.next_state, decided.ledger_entry))

    assert state_repo.saved is not None
    assert state_repo.saved.updated_at == "2026-09-18T00:00:00Z"
    assert state_repo.saved.transition == "BACKTRACK"
    assert len(ledger_repo.entries) == 1
    assert ledger_repo.entries[0].ts == "2026-09-18T00:00:00Z"
    assert ledger_repo.entries[0].gate == "SPIKE_GATE"
    assert out.state_sha256 == "deadbeef"
