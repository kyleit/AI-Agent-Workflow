"""Approval infrastructure: config loader + command-based auto-approver.

Auto-approval runs a configured, canonical CLI command per gate (e.g.
`aiwf blueprint --approve --work-item <id>`), so the approval is a REAL,
audited record — never a silent bypass. If a gate has no configured command,
the executor returns False and the loop falls back to manual approval.
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from malo.application.ports import AgentSpawner
from malo.domain.approval import ApprovalPolicy
from malo.domain.jsonutil import as_json_object

_CONFIG_REL = (".agents", "config", "loop-approval.json")

# Canonical default commands (only for gates auto mode is allowed to cover).
_DEFAULT_GATE_COMMANDS: dict[str, tuple[str, ...]] = {
    "blueprint": ("aiwf", "blueprint", "--approve", "--work-item", "${workflow}"),
    "implementation": ("aiwf", "blueprint", "--approve", "--work-item", "${workflow}"),
}


class FileApprovalPolicyRepo:
    """Load the approval policy; a missing file yields the safe auto default."""

    def load(self, root: Path) -> ApprovalPolicy:
        path = root.joinpath(*_CONFIG_REL)
        if path.is_file():
            data = as_json_object(path.read_text(encoding="utf-8"))
            if data is not None:
                policy = ApprovalPolicy.from_dict(data)
                if policy.gate_commands:
                    return policy
                # No commands configured -> attach canonical defaults.
                return ApprovalPolicy(
                    mode=policy.mode,
                    auto_gates=policy.auto_gates,
                    never_auto_gates=policy.never_auto_gates,
                    clarification_strategy=policy.clarification_strategy,
                    gate_commands=dict(_DEFAULT_GATE_COMMANDS),
                )
        return ApprovalPolicy(gate_commands=dict(_DEFAULT_GATE_COMMANDS))


def _subst(element: str, substitutions: Mapping[str, str]) -> str:
    rendered = element
    for key, value in substitutions.items():
        rendered = rendered.replace("${" + key + "}", value)
    return rendered


class CommandApprovalExecutor:
    """Record a gate approval by running its canonical CLI command."""

    def __init__(
        self, policy: ApprovalPolicy, spawner: AgentSpawner, timeout_s: int = 120
    ) -> None:
        self._policy = policy
        self._spawner = spawner
        self._timeout_s = timeout_s

    def approve(self, gate: str, workflow_id: str, root: Path) -> bool:
        command = self._policy.command_for(gate)
        if not command:
            return False
        subs = {"workflow": workflow_id, "gate": gate}
        rendered = [_subst(part, subs) for part in command]
        outcome = self._spawner.run(rendered, root, self._timeout_s)
        return outcome.exit_code == 0
