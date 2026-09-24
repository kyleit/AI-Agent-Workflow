"""Approval policy (pure domain).

Decides, per gate, whether the loop AUTO-approves (records a real approval and
continues) or stops for MANUAL human approval. Governance-critical defaults:
git / release / deploy gates are NEVER auto-approved, even in auto mode.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum
from typing import cast

APPROVAL_POLICY_SCHEMA = "aiwf.loop-approval/1"

# Gates that must ALWAYS be manual — auto mode never covers them.
NEVER_AUTO_GATES: frozenset[str] = frozenset({"git", "release", "deploy"})
# Gates auto mode covers by default.
DEFAULT_AUTO_GATES: frozenset[str] = frozenset(
    {"clarification", "blueprint", "implementation"}
)


class ApprovalMode(str, Enum):
    AUTO = "auto"
    MANUAL = "manual"

    @classmethod
    def parse(cls, raw: str) -> "ApprovalMode":
        return cls.AUTO if raw.strip().lower() == "auto" else cls.MANUAL


class ApprovalDecision(str, Enum):
    AUTO = "auto"
    MANUAL = "manual"


def _as_str_frozenset(value: object, default: frozenset[str]) -> frozenset[str]:
    if isinstance(value, list):
        return frozenset(x for x in cast("list[object]", value) if isinstance(x, str))
    return default


def _empty_command_map() -> dict[str, tuple[str, ...]]:
    return {}


def _as_command_map(value: object) -> dict[str, tuple[str, ...]]:
    out: dict[str, tuple[str, ...]] = {}
    if isinstance(value, dict):
        for key, raw in cast("Mapping[str, object]", value).items():
            if isinstance(raw, list):
                out[key] = tuple(
                    x for x in cast("list[object]", raw) if isinstance(x, str)
                )
    return out


@dataclass(frozen=True)
class ApprovalPolicy:
    """How the loop treats approval gates (default: auto, safe gates only)."""

    mode: ApprovalMode = ApprovalMode.AUTO
    auto_gates: frozenset[str] = DEFAULT_AUTO_GATES
    never_auto_gates: frozenset[str] = NEVER_AUTO_GATES
    clarification_strategy: str = "first-option"
    gate_commands: Mapping[str, tuple[str, ...]] = field(default_factory=_empty_command_map)

    def decide(self, gate: str) -> ApprovalDecision:
        """Return AUTO only when auto mode covers this (non-forbidden) gate."""
        if self.mode is not ApprovalMode.AUTO:
            return ApprovalDecision.MANUAL
        # Hard safety rule: git/release/deploy are never auto-approved.
        if gate in self.never_auto_gates or gate in NEVER_AUTO_GATES:
            return ApprovalDecision.MANUAL
        if gate not in self.auto_gates:
            return ApprovalDecision.MANUAL
        return ApprovalDecision.AUTO

    def command_for(self, gate: str) -> tuple[str, ...] | None:
        return self.gate_commands.get(gate)

    def with_mode(self, mode: ApprovalMode) -> "ApprovalPolicy":
        return ApprovalPolicy(
            mode=mode,
            auto_gates=self.auto_gates,
            never_auto_gates=self.never_auto_gates,
            clarification_strategy=self.clarification_strategy,
            gate_commands=self.gate_commands,
        )

    def rendered_command(self, gate: str, workflow_id: str) -> tuple[str, ...]:
        """The gate's approval command with ${workflow}/${gate} substituted."""
        command = self.gate_commands.get(gate)
        if not command:
            return ()
        subs = {"workflow": workflow_id, "gate": gate}
        rendered: list[str] = []
        for part in command:
            value = part
            for key, sub in subs.items():
                value = value.replace("${" + key + "}", sub)
            rendered.append(value)
        return tuple(rendered)

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> "ApprovalPolicy":
        mode_raw = data.get("mode", "auto")
        mode = ApprovalMode.parse(mode_raw if isinstance(mode_raw, str) else "auto")
        strat = data.get("clarification_strategy", "first-option")
        # never_auto is the union of the configured set and the hard defaults.
        never = _as_str_frozenset(data.get("never_auto_gates"), NEVER_AUTO_GATES)
        return cls(
            mode=mode,
            auto_gates=_as_str_frozenset(data.get("auto_gates"), DEFAULT_AUTO_GATES),
            never_auto_gates=never | NEVER_AUTO_GATES,
            clarification_strategy=strat if isinstance(strat, str) else "first-option",
            gate_commands=_as_command_map(data.get("gate_commands")),
        )
