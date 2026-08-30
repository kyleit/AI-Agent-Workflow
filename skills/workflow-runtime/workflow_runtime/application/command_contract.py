from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Mapping, Sequence, TextIO


EXIT_CODES = {
    "success": 0,
    "invalid_input": 2,
    "blocked": 3,
    "failure": 4,
}


@dataclass(frozen=True)
class NextAction:
    skill: str | None = None
    command: str | None = None
    required: bool = False
    automatic: bool = False
    requires_approval: bool = False
    arguments: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class CommandResult:
    command: str
    status: str
    summary: str
    data: Mapping[str, object] = field(default_factory=dict)
    artifacts: Sequence[str] = field(default_factory=tuple)
    blocking_findings: Sequence[str] = field(default_factory=tuple)
    warnings: Sequence[str] = field(default_factory=tuple)
    side_effects: Sequence[str] = field(default_factory=tuple)
    next_action: NextAction = field(default_factory=NextAction)
    evidence: Sequence[str] = field(default_factory=tuple)
    request_id: str | None = None
    schema_version: str = "aiwf.command.v1"

    def payload(self) -> dict[str, object]:
        body = asdict(self)
        body["artifacts"] = list(self.artifacts)
        body["blocking_findings"] = list(self.blocking_findings)
        body["warnings"] = list(self.warnings)
        body["side_effects"] = list(self.side_effects)
        body["evidence"] = list(self.evidence)
        body["next_action"] = asdict(self.next_action)
        body["next_action"]["arguments"] = dict(self.next_action.arguments)
        return body

    def exit_code(self) -> int:
        return EXIT_CODES.get(self.status, EXIT_CODES["failure"])


def emit_result(result: CommandResult, stream: TextIO) -> int:
    stream.write(json.dumps(result.payload(), ensure_ascii=False, separators=(",", ":")))
    stream.write("\n")
    stream.flush()
    return result.exit_code()
