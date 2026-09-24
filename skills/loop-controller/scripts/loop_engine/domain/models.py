"""Domain models for the AIWF loop engine.

Pure value objects and enums. No IO, no time access, no hashing side effects.
All time and persistence concerns are injected via application ports.

Typing: basedpyright strict-full. No `Any`; JSON is parsed as `object` and
narrowed through explicit, typed coercion helpers.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum

from loop_engine.domain.errors import (
    InvalidLoopStateError,
    InvalidTransitionError,
    InvalidVerdictError,
)

LOOP_STATE_SCHEMA = "aiwf.loop/1"
DEFAULT_MAX_ITERATIONS = 8
DEFAULT_NO_PROGRESS_THRESHOLD = 3


def _as_str(value: object, field_name: str) -> str:
    if isinstance(value, str):
        return value
    raise InvalidLoopStateError(f"Field '{field_name}' must be a string.")


def _as_opt_str(value: object, field_name: str) -> str | None:
    if value is None or isinstance(value, str):
        return value
    raise InvalidLoopStateError(f"Field '{field_name}' must be a string or null.")


def _as_int(value: object, default: int, field_name: str) -> int:
    if value is None:
        return default
    if isinstance(value, bool):
        raise InvalidLoopStateError(f"Field '{field_name}' must be an integer.")
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        text = value.strip()
        if text.lstrip("-").isdigit():
            return int(text)
    raise InvalidLoopStateError(f"Field '{field_name}' must be an integer.")


def _as_str_tuple(value: object, field_name: str) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, (list, tuple)):
        items: list[str] = []
        for item in value:  # pyright: ignore[reportUnknownVariableType]
            if isinstance(item, str):
                items.append(item)
            else:
                raise InvalidLoopStateError(
                    f"Field '{field_name}' must contain only strings."
                )
        return tuple(items)
    raise InvalidLoopStateError(f"Field '{field_name}' must be a list of strings.")


class Verdict(str, Enum):
    """Evaluation verdict fed into the controller from a gate/skill.

    Maps the existing AIWF gate decisions onto four loop-relevant classes:
      - PASS  : gate PASS (readiness >= 95 + no blockers, or spike pass).
      - BLOCK : BLOCKED / AWAITING_APPROVAL / INVALIDATED — recoverable, refine.
      - FAIL  : FAIL — a named-target failure (e.g. spike fail -> brainstorming).
      - ERROR : unrecoverable runtime error — halt immediately.
    """

    PASS = "PASS"
    BLOCK = "BLOCK"
    FAIL = "FAIL"
    ERROR = "ERROR"

    @classmethod
    def parse(cls, raw: str) -> "Verdict":
        try:
            return cls(str(raw).strip().upper())
        except ValueError as exc:
            raise InvalidVerdictError(
                f"Unknown verdict '{raw}'. Expected one of "
                f"{[v.value for v in cls]}."
            ) from exc


class Transition(str, Enum):
    """The four legal loop transitions. This enum is closed and additive-only."""

    ADVANCE = "ADVANCE"
    REPEAT = "REPEAT"
    BACKTRACK = "BACKTRACK"
    HALT = "HALT"

    @classmethod
    def parse(cls, raw: str) -> "Transition":
        try:
            return cls(str(raw).strip().upper())
        except ValueError as exc:
            raise InvalidTransitionError(
                f"Unknown transition '{raw}'. Expected one of "
                f"{[t.value for t in cls]}."
            ) from exc


class StopCondition(str, Enum):
    """Terminal stop-conditions that force a HALT transition."""

    MAX_ITERATIONS = "MAX_ITERATIONS"
    NO_PROGRESS = "NO_PROGRESS"
    GATE_PASS_FINAL = "GATE_PASS_FINAL"
    USER_HALT = "USER_HALT"
    UNRECOVERABLE_ERROR = "UNRECOVERABLE_ERROR"


@dataclass(frozen=True)
class LoopState:
    """The persisted loop state (schema aiwf.loop/1).

    `no_progress_threshold` is an additive config field (default 3). Absent in
    legacy files it is filled with the default, preserving backward
    compatibility.
    """

    workflow_id: str
    current_phase: str
    iteration: int = 0
    max_iterations: int = DEFAULT_MAX_ITERATIONS
    no_progress_count: int = 0
    no_progress_threshold: int = DEFAULT_NO_PROGRESS_THRESHOLD
    last_verdict: str | None = None
    failure_signature: str = ""
    transition: str | None = None
    backtrack_target: str | None = None
    stop_conditions_met: tuple[str, ...] = field(default_factory=tuple)
    updated_at: str | None = None
    schema: str = LOOP_STATE_SCHEMA

    def __post_init__(self) -> None:
        if not self.workflow_id:
            raise InvalidLoopStateError("workflow_id is required.")
        if not self.current_phase:
            raise InvalidLoopStateError("current_phase is required.")
        if self.max_iterations < 1:
            raise InvalidLoopStateError("max_iterations must be >= 1.")
        if self.no_progress_threshold < 1:
            raise InvalidLoopStateError("no_progress_threshold must be >= 1.")
        if self.iteration < 0 or self.no_progress_count < 0:
            raise InvalidLoopStateError("counters must be non-negative.")

    @classmethod
    def initial(
        cls,
        workflow_id: str,
        current_phase: str,
        *,
        max_iterations: int = DEFAULT_MAX_ITERATIONS,
        no_progress_threshold: int = DEFAULT_NO_PROGRESS_THRESHOLD,
    ) -> "LoopState":
        """Backward-compat init: a missing loop_state starts at iteration 0."""
        return cls(
            workflow_id=workflow_id,
            current_phase=current_phase,
            iteration=0,
            max_iterations=max_iterations,
            no_progress_threshold=no_progress_threshold,
        )

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> "LoopState":
        schema = _as_str(data.get("schema", LOOP_STATE_SCHEMA), "schema")
        if schema != LOOP_STATE_SCHEMA:
            raise InvalidLoopStateError(
                f"Unsupported loop_state schema '{schema}'. "
                f"Expected '{LOOP_STATE_SCHEMA}'."
            )
        return cls(
            workflow_id=_as_str(data.get("workflow_id", ""), "workflow_id"),
            current_phase=_as_str(data.get("current_phase", ""), "current_phase"),
            iteration=_as_int(data.get("iteration"), 0, "iteration"),
            max_iterations=_as_int(
                data.get("max_iterations"), DEFAULT_MAX_ITERATIONS, "max_iterations"
            ),
            no_progress_count=_as_int(
                data.get("no_progress_count"), 0, "no_progress_count"
            ),
            no_progress_threshold=_as_int(
                data.get("no_progress_threshold"),
                DEFAULT_NO_PROGRESS_THRESHOLD,
                "no_progress_threshold",
            ),
            last_verdict=_as_opt_str(data.get("last_verdict"), "last_verdict"),
            failure_signature=_as_str(
                data.get("failure_signature", ""), "failure_signature"
            ),
            transition=_as_opt_str(data.get("transition"), "transition"),
            backtrack_target=_as_opt_str(
                data.get("backtrack_target"), "backtrack_target"
            ),
            stop_conditions_met=_as_str_tuple(
                data.get("stop_conditions_met"), "stop_conditions_met"
            ),
            updated_at=_as_opt_str(data.get("updated_at"), "updated_at"),
            schema=schema,
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "workflow_id": self.workflow_id,
            "current_phase": self.current_phase,
            "iteration": self.iteration,
            "max_iterations": self.max_iterations,
            "no_progress_count": self.no_progress_count,
            "no_progress_threshold": self.no_progress_threshold,
            "last_verdict": self.last_verdict,
            "failure_signature": self.failure_signature,
            "transition": self.transition,
            "backtrack_target": self.backtrack_target,
            "stop_conditions_met": list(self.stop_conditions_met),
            "updated_at": self.updated_at,
        }


@dataclass(frozen=True)
class DecisionInput:
    """Everything the pure decision function needs for one controller cycle.

    The engine never runs a skill (EXECUTE) nor computes a gate (EVALUATE);
    those happen in the agent turn. The verdict, the freshly computed
    failure_signature, and the phase metadata are passed in here.
    """

    current_state: LoopState
    verdict: Verdict
    new_failure_signature: str = ""
    approval_present: bool = False
    requires_approval: bool = False
    is_terminal_phase: bool = False
    next_phase: str | None = None
    backtrack_target: str | None = None
    user_halt: bool = False


@dataclass(frozen=True)
class DecisionResult:
    """Outcome of a pure decision: the proposed next loop state fields."""

    transition: Transition
    resulting_phase: str
    next_iteration: int
    no_progress_count: int
    stop_conditions_met: tuple[StopCondition, ...]
    backtrack_target: str | None
    escalate: bool
    escalation_options: tuple[str, ...] = field(default_factory=tuple)

    def stop_values(self) -> list[str]:
        return [s.value for s in self.stop_conditions_met]
