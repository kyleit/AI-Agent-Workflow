"""File-backed repositories for loop state and the append-only ledger.

State authority: `.agents/state/loop/` under the repository root (never
`.agents/.session.json`, which is DEPRECATED). All writes are atomic
(temp file + os.replace) and UTF-8 without BOM. Paths returned to callers are
repository-relative POSIX strings, satisfying the Absolute Path Prohibition.
"""

from __future__ import annotations

import json
import os
import re
import tempfile
from pathlib import Path

from loop_engine.domain.errors import InvalidLoopStateError
from loop_engine.domain.jsonutil import as_json_object
from loop_engine.domain.ledger import LedgerEntry
from loop_engine.domain.models import LoopState
from loop_engine.domain.serialization import to_canonical_json

_LOOP_SUBDIR = (".agents", "state", "loop")
_SAFE_ID = re.compile(r"^[A-Za-z0-9._-]{1,128}$")


def _validate_workflow_id(workflow_id: str) -> str:
    if not _SAFE_ID.match(workflow_id):
        raise InvalidLoopStateError(
            "workflow_id must match ^[A-Za-z0-9._-]{1,128}$ "
            "(no path separators)."
        )
    return workflow_id


class _PathResolver:
    """Resolves loop artifact paths relative to the repository root."""

    def __init__(self, repo_root: Path) -> None:
        self._repo_root = repo_root.resolve()
        self._loop_dir = self._repo_root.joinpath(*_LOOP_SUBDIR)

    def state_file(self, workflow_id: str) -> Path:
        return self._loop_dir / f"{workflow_id}.json"

    def ledger_file(self, workflow_id: str) -> Path:
        return self._loop_dir / f"{workflow_id}.ledger.jsonl"

    def relative(self, path: Path) -> str:
        return path.resolve().relative_to(self._repo_root).as_posix()

    def ensure_dir(self) -> None:
        self._loop_dir.mkdir(parents=True, exist_ok=True)


def _atomic_write_text(target: Path, content: str) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(
        dir=str(target.parent), prefix=target.name, suffix=".tmp"
    )
    tmp_path = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            _ = handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_path, target)
    except BaseException:
        tmp_path.unlink(missing_ok=True)
        raise


class FileLoopStateRepository:
    """Concrete LoopStateRepository backed by a single JSON file per workflow."""

    def __init__(self, repo_root: Path) -> None:
        self._paths = _PathResolver(repo_root)

    def load(self, workflow_id: str) -> LoopState | None:
        _ = _validate_workflow_id(workflow_id)
        path = self._paths.state_file(workflow_id)
        if not path.is_file():
            return None
        data = as_json_object(path.read_text(encoding="utf-8"))
        if data is None:
            raise InvalidLoopStateError("loop_state file must contain an object.")
        return LoopState.from_dict(data)

    def save(self, state: LoopState) -> str:
        _ = _validate_workflow_id(state.workflow_id)
        self._paths.ensure_dir()
        path = self._paths.state_file(state.workflow_id)
        _atomic_write_text(path, to_canonical_json(state.to_dict()) + "\n")
        return self._paths.relative(path)


class FileLoopLedgerRepository:
    """Concrete LoopLedgerRepository appending one JSONL row per cycle."""

    def __init__(self, repo_root: Path) -> None:
        self._paths = _PathResolver(repo_root)

    def append(self, workflow_id: str, entry: LedgerEntry) -> str:
        _ = _validate_workflow_id(workflow_id)
        self._paths.ensure_dir()
        path = self._paths.ledger_file(workflow_id)
        line = json.dumps(entry.to_dict(), ensure_ascii=False, sort_keys=True)
        with open(path, "a", encoding="utf-8", newline="\n") as handle:
            _ = handle.write(line + "\n")
        return self._paths.relative(path)
