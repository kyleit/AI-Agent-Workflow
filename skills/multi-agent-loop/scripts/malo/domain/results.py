"""Phase-run result + verdict normalization (pure domain).

Maps a headless agent's exit code and stdout onto the loop-controller verdict
vocabulary (PASS|BLOCK|FAIL|ERROR), so the loop engine can DECIDE the next
transition. The mapping is deterministic and conservative:
  - exit != 0                      -> ERROR (unrecoverable run)
  - explicit token in stdout       -> that verdict (FAIL/BLOCK/PASS precedence)
  - otherwise                      -> BLOCK (recoverable; refine and repeat)
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from enum import Enum

PHASE_RUN_SCHEMA = "aiwf.phase-run/1"


class Verdict(str, Enum):
    PASS = "PASS"
    BLOCK = "BLOCK"
    FAIL = "FAIL"
    ERROR = "ERROR"

    @classmethod
    def parse(cls, raw: str) -> "Verdict":
        """Parse an agent-reported verdict token (default BLOCK: recoverable)."""
        token = raw.strip().upper()
        for member in cls:
            if member.value == token:
                return member
        return cls.BLOCK


def normalize_verdict(exit_code: int, stdout: str) -> Verdict:
    if exit_code != 0:
        return Verdict.ERROR
    upper = stdout.upper()
    # precedence: FAIL (named failure) > BLOCK (recoverable) > PASS
    if "FAIL" in upper:
        return Verdict.FAIL
    if "BLOCK" in upper:
        return Verdict.BLOCK
    if "PASS" in upper:
        return Verdict.PASS
    return Verdict.BLOCK


@dataclass(frozen=True)
class PhaseRunResult:
    """One agent run for one phase (aiwf.phase-run/1), append-only ledger row."""

    workflow_id: str
    phase: str
    agent_id: str
    agent_type: str
    verdict: Verdict
    exit_code: int
    duration_s: float
    command_redacted: str = ""
    findings: tuple[str, ...] = field(default_factory=tuple)
    evidence_refs: tuple[str, ...] = field(default_factory=tuple)
    ts: str | None = None
    schema: str = PHASE_RUN_SCHEMA

    def with_timestamp(self, ts: str) -> "PhaseRunResult":
        return PhaseRunResult(
            workflow_id=self.workflow_id,
            phase=self.phase,
            agent_id=self.agent_id,
            agent_type=self.agent_type,
            verdict=self.verdict,
            exit_code=self.exit_code,
            duration_s=self.duration_s,
            command_redacted=self.command_redacted,
            findings=self.findings,
            evidence_refs=self.evidence_refs,
            ts=ts,
            schema=self.schema,
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "workflow_id": self.workflow_id,
            "phase": self.phase,
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "verdict": self.verdict.value,
            "exit_code": self.exit_code,
            "duration_s": round(self.duration_s, 3),
            "command_redacted": self.command_redacted,
            "findings": list(self.findings),
            "evidence_refs": list(self.evidence_refs),
            "ts": self.ts,
        }


def redact_command(command: Sequence[str], substitutions: Mapping[str, str]) -> str:
    """Render a command for the ledger with the task payload elided."""
    task = substitutions.get("task", "")
    parts: list[str] = []
    for element in command:
        parts.append("<task>" if task and element == task else element)
    return " ".join(parts)
