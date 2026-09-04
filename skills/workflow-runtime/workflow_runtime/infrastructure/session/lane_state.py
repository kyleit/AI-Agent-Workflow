from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any
from urllib.parse import quote

from workflow_runtime.domain.approval import LaneKey


class LaneStateStore:
    """Persist lane state below one project-local namespace without global mixing."""

    def __init__(self, workspace_root: str | Path = ".") -> None:
        self.root = Path(workspace_root).resolve() / ".agents" / "state" / "lanes"

    def lane_dir(self, lane: LaneKey) -> Path:
        return self.root / quote(lane.project_id, safe="") / quote(lane.workflow_id, safe="") / quote(lane.agent_id, safe="") / quote(lane.task_id, safe="")

    def save(self, lane: LaneKey, state: dict[str, Any]) -> Path:
        directory = self.lane_dir(lane)
        directory.mkdir(parents=True, exist_ok=True)
        destination = directory / "state.json"
        fd, temporary = tempfile.mkstemp(prefix="state-", suffix=".tmp", dir=directory)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump({"lane": lane.to_dict(), "state": state}, handle, indent=2, ensure_ascii=False)
            os.replace(temporary, destination)
        finally:
            if os.path.exists(temporary):
                os.remove(temporary)
        return destination

    def load(self, lane: LaneKey) -> dict[str, Any] | None:
        path = self.lane_dir(lane) / "state.json"
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None
        return value.get("state") if isinstance(value, dict) and isinstance(value.get("state"), dict) else None


__all__ = ["LaneStateStore"]

