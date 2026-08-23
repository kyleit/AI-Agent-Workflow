"""Memory store adapter for .agents/memory/ memory-state.json and markdown file search."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, cast

from workflow_runtime.application.ports.knowledge_ports import IMemoryStorePort
from workflow_runtime.domain.knowledge.entities import MemoryEntry
from workflow_runtime.domain.knowledge.value_objects import MemoryScope
from workflow_runtime.shared.logging import LoggerFactory
from workflow_runtime.shared.utils import atomic_write_json

logger = LoggerFactory.get_logger(__name__)


class MemoryStoreAdapter(IMemoryStorePort):
    """Adapter reading/writing .agents/memory/memory-state.json and scanning Markdown files."""

    def __init__(self, base_dir: str | Path | None = None) -> None:
        if base_dir is None:
            self.base_dir = Path(".agents/memory")
        else:
            self.base_dir = Path(base_dir)

    def get_state_file_path(self) -> Path:
        if self.base_dir.name == "memory":
            return self.base_dir / "memory-state.json"
        return self.base_dir / ".agents" / "memory" / "memory-state.json"

    def load_memory_state(self) -> list[MemoryEntry]:
        """Loads memory entries from memory-state.json.

        Returns empty list if file does not exist (Memory-First policy).
        """
        path = self.get_state_file_path()
        if not path.is_file():
            logger.info(f"Memory state file not found at {path}. Returning empty list.")
            return []

        try:
            with path.open(encoding="utf-8") as f:
                data = json.load(f)
        except Exception as exc:
            logger.warning(f"Failed to read memory state file {path}: {exc}")
            return []

        entries: list[MemoryEntry] = []

        if isinstance(data, dict):
            data_dict = cast(dict[str, Any], data)
            raw_entries = data_dict.get("entries")
            if isinstance(raw_entries, list):
                for raw in cast(list[Any], raw_entries):
                    raw_dict = cast(dict[str, Any], raw) if isinstance(raw, dict) else {}
                    created_at = raw_dict.get("created_at")
                    if isinstance(created_at, str) and created_at:
                        try:
                            dt = datetime.fromisoformat(created_at)
                        except ValueError:
                            dt = datetime.now(timezone.utc)
                    else:
                        dt = datetime.now(timezone.utc)

                    raw_tags = raw_dict.get("tags")
                    tags_list: list[Any] = cast(list[Any], raw_tags) if isinstance(raw_tags, list) else []

                    entries.append(
                        MemoryEntry(
                            entry_id=str(raw_dict.get("entry_id", "unknown")),
                            title=str(raw_dict.get("title", "")),
                            content=str(raw_dict.get("content", "")),
                            tags=tags_list,
                            decay_score=float(raw_dict.get("decay_score", 1.0)),
                            created_at=dt,
                            scope=MemoryScope.PROJECT,
                        )
                    )
                return entries

            notes = str(data_dict.get("notes", ""))
            version = str(data_dict.get("memory_version", "1.0.0"))
            raw_layers = data_dict.get("layers_generated")
            layers: list[Any] = cast(list[Any], raw_layers) if isinstance(raw_layers, list) else ["memory", "state"]
            last_hash = str(data_dict.get("last_git_hash", ""))
            updated_at = str(data_dict.get("last_updated_at", ""))

            content_lines = [
                f"Memory Version: {version}",
                f"Last Git Hash: {last_hash}",
                f"Last Updated: {updated_at}",
                f"Notes: {notes}",
            ]
            nl = "\n"
            entries.append(
                MemoryEntry(
                    entry_id="state_meta",
                    title="Project Memory State Summary",
                    content=nl.join(content_lines),
                    tags=layers,
                    decay_score=1.0,
                    created_at=datetime.now(timezone.utc),
                    scope=MemoryScope.PROJECT,
                )
            )

        return entries

    def save_memory_state(self, entries: list[MemoryEntry]) -> None:
        """Saves memory entries atomically to memory-state.json."""
        path = self.get_state_file_path()
        path.parent.mkdir(parents=True, exist_ok=True)

        serializable_entries: list[dict[str, Any]] = []
        for entry in entries:
            dt_str = entry.created_at.isoformat()
            serializable_entries.append(
                {
                    "entry_id": entry.entry_id,
                    "title": entry.title,
                    "content": entry.content,
                    "tags": entry.tags,
                    "decay_score": entry.decay_score,
                    "created_at": dt_str,
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                }
            )

        payload: dict[str, Any] = {
            "version": "1.0.0",
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "entries": serializable_entries,
        }
        atomic_write_json(str(path), payload)

    def search_markdown_files(
        self, keyword: str, search_dir: Any = None
    ) -> list[dict[str, Any]]:
        """Scans Markdown files for exact keyword occurrences."""
        target_dir = Path(search_dir) if search_dir else self.base_dir.parent.parent
        results: list[dict[str, Any]] = []
        if not target_dir.is_dir():
            return results

        kw_lower = keyword.lower()
        for md_file in target_dir.glob("**/*.md"):
            try:
                with md_file.open(encoding="utf-8", errors="ignore") as f:
                    for idx, line in enumerate(f, start=1):
                        if kw_lower in line.lower():
                            results.append(
                                {
                                    "path": str(md_file),
                                    "line_number": idx,
                                    "snippet": line.strip(),
                                }
                            )
            except Exception as exc:
                logger.warning(f"Error reading markdown file {md_file}: {exc}")
        return results


__all__ = ["MemoryStoreAdapter"]
