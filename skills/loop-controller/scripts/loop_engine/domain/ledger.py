"""Append-only ledger entry (domain value object).

One entry per controller cycle. Serialized as a single JSON object per line
(JSONL) into `.agents/state/loop/<workflow-id>.ledger.jsonl`. Field names on
the wire follow the framework contract: `iter`, `phase`, `action`, `gate`,
`verdict`, `evidence_refs`, `next`, `ts`.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field


@dataclass(frozen=True)
class LedgerEntry:
    iteration: int
    phase: str
    action: str
    verdict: str
    next_phase: str
    gate: str | None = None
    evidence_refs: tuple[str, ...] = field(default_factory=tuple)
    ts: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "iter": self.iteration,
            "phase": self.phase,
            "action": self.action,
            "gate": self.gate,
            "verdict": self.verdict,
            "evidence_refs": list(self.evidence_refs),
            "next": self.next_phase,
            "ts": self.ts,
        }

    def with_timestamp(self, ts: str) -> "LedgerEntry":
        return LedgerEntry(
            iteration=self.iteration,
            phase=self.phase,
            action=self.action,
            verdict=self.verdict,
            next_phase=self.next_phase,
            gate=self.gate,
            evidence_refs=self.evidence_refs,
            ts=ts,
        )

    @staticmethod
    def _as_str_tuple(value: object) -> tuple[str, ...]:
        if value is None:
            return ()
        if isinstance(value, (list, tuple)):
            out: list[str] = []
            for item in value:  # pyright: ignore[reportUnknownVariableType]
                if isinstance(item, str):
                    out.append(item)
            return tuple(out)
        return ()

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> "LedgerEntry":
        iteration_raw = data.get("iter", 0)
        iteration = iteration_raw if isinstance(iteration_raw, int) else 0
        phase = data.get("phase")
        action = data.get("action")
        verdict = data.get("verdict")
        next_phase = data.get("next")
        gate = data.get("gate")
        ts = data.get("ts")
        evidence: Sequence[object] | object = data.get("evidence_refs")
        return cls(
            iteration=iteration,
            phase=phase if isinstance(phase, str) else "",
            action=action if isinstance(action, str) else "",
            verdict=verdict if isinstance(verdict, str) else "",
            next_phase=next_phase if isinstance(next_phase, str) else "",
            gate=gate if isinstance(gate, str) else None,
            evidence_refs=cls._as_str_tuple(evidence),
            ts=ts if isinstance(ts, str) else None,
        )
