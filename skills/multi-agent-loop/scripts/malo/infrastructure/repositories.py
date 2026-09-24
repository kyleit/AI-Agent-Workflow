"""File-backed registry + result repositories (concrete ports).

Registry: `.agents/config/agent-registry.json` (aiwf.agent-registry/1); a missing
file yields an empty registry so behavior degrades to a single session agent.
Results: append-only `.agents/state/loop/<workflow-id>.runs.jsonl` (aiwf.phase-run/1),
repository-relative paths only.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from malo.domain.errors import InvalidRegistryError, InvalidResultError
from malo.domain.jsonutil import as_json_object
from malo.domain.models import AgentRegistry
from malo.domain.results import PhaseRunResult

_REGISTRY_REL = (".agents", "config", "agent-registry.json")
_LOOP_SUBDIR = (".agents", "state", "loop")
_SAFE_ID = re.compile(r"^[A-Za-z0-9._-]{1,128}$")


def _validate_workflow_id(workflow_id: str) -> str:
    if not _SAFE_ID.match(workflow_id):
        raise InvalidResultError(
            "workflow_id must match ^[A-Za-z0-9._-]{1,128}$ (no path separators)."
        )
    return workflow_id


class FileRegistryRepo:
    """Load the agent registry from JSON; missing file -> empty registry."""

    def load(self, root: Path) -> AgentRegistry:
        path = root.joinpath(*_REGISTRY_REL)
        if not path.is_file():
            return AgentRegistry()
        data = as_json_object(path.read_text(encoding="utf-8"))
        if data is None:
            raise InvalidRegistryError("agent-registry.json must contain an object.")
        return AgentRegistry.from_dict(data)


class FileResultRepo:
    """Append phase-run results to the per-workflow run ledger (JSONL)."""

    def append(self, root: Path, result: PhaseRunResult) -> str:
        workflow_id = _validate_workflow_id(result.workflow_id)
        loop_dir = root.joinpath(*_LOOP_SUBDIR)
        loop_dir.mkdir(parents=True, exist_ok=True)
        path = loop_dir / f"{workflow_id}.runs.jsonl"
        line = json.dumps(result.to_dict(), ensure_ascii=False, sort_keys=True)
        with open(path, "a", encoding="utf-8", newline="\n") as handle:
            _ = handle.write(line + "\n")
        return path.resolve().relative_to(root.resolve()).as_posix()
