from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_runtime.application.ports.knowledge_ports import IMemoryStorePort
from workflow_runtime.domain.knowledge.entities import MemoryEntry
from workflow_runtime.domain.knowledge.value_objects import MemoryScope
from workflow_runtime.shared.logging import LoggerFactory

logger = LoggerFactory.get_logger(__name__)


class MemoryService:
    """Application service orchestrating Project Memory lifecycle and Memory First policy."""

    def __init__(self, memory_store: IMemoryStorePort) -> None:
        self._store = memory_store
        self._cache: list[MemoryEntry] | None = None

    def _get_entries(self) -> list[MemoryEntry]:
        if self._cache is None:
            self._cache = self._store.load_memory_state()
        return self._cache

    def query(self, query: str, category: str | None = None) -> list[MemoryEntry]:
        """Queries memory entries matching keyword and optional category/tag.

        Returns empty list if no memory file exists (Memory-First policy).
        """
        entries = self._get_entries()
        if not entries:
            return []

        q_lower = query.lower()
        results: list[MemoryEntry] = []
        for entry in entries:
            match_query = (
                q_lower in entry.title.lower()
                or q_lower in entry.content.lower()
                or any(q_lower in t.lower() for t in entry.tags)
            )
            match_category = (
                category is None
                or category.lower() in [t.lower() for t in entry.tags]
                or category.upper() == entry.scope.name
            )

            if match_query and match_category:
                results.append(entry)

        results.sort(key=lambda e: e.decay_score, reverse=True)
        return results

    def query_by_tags(self, tags: list[str]) -> list[MemoryEntry]:
        """Queries memory entries matching any of the specified tag keywords."""
        entries = self._get_entries()
        if not entries:
            return []

        target_tags = {t.lower() for t in tags}
        results: list[MemoryEntry] = []

        for entry in entries:
            entry_tags = {t.lower() for t in entry.tags}
            if target_tags.intersection(entry_tags):
                results.append(entry)

        results.sort(key=lambda e: e.decay_score, reverse=True)
        return results

    def store(self, entry: MemoryEntry) -> None:
        """Persists a new memory entry or updates an existing one."""
        entries = self._get_entries()
        updated = False
        for idx, existing in enumerate(entries):
            if existing.entry_id == entry.entry_id:
                entries[idx] = entry
                updated = True
                break

        if not updated:
            entries.append(entry)

        self._store.save_memory_state(entries)
        self._cache = entries

    def update(self, entry_id: str, content: str) -> bool:
        """Updates the content of an existing memory entry."""
        entries = self._get_entries()
        for entry in entries:
            if entry.entry_id == entry_id:
                entry.content = content
                self._store.save_memory_state(entries)
                return True
        return False

    def apply_decay(self, decay_rate: float = 0.05) -> int:
        """Applies decay factor to all stored memory entries."""
        entries = self._get_entries()
        count = 0
        for entry in entries:
            entry.apply_decay(decay_rate)
            count += 1

        if count > 0:
            self._store.save_memory_state(entries)
        return count

    def decay_old(self, decay_rate: float = 0.05) -> int:
        """Alias for apply_decay."""
        return self.apply_decay(decay_rate)

    def load_from_file(self, file_path: str | Path | None = None) -> list[MemoryEntry]:
        """Loads memory entries directly from file path or default store state file."""
        if file_path:
            try:
                from workflow_runtime.infrastructure.knowledge.memory_store_adapter import (
                    MemoryStoreAdapter)
                adapter = MemoryStoreAdapter(base_dir=Path(file_path).parent)
                return adapter.load_memory_state()
            except Exception:
                return []
        return self._store.load_memory_state()

    def initialize_memory(self, workspace_path: str) -> dict[str, Any]:
        """Bootstraps initial project memory directory and state structure."""
        ws_dir = Path(workspace_path)
        mem_dir = ws_dir / ".agents" / "memory"
        mem_dir.mkdir(parents=True, exist_ok=True)

        summary_file = mem_dir / "project-summary.md"
        if not summary_file.exists():
            summary_file.write_text("# Project Summary\n\nInitialized memory base.", encoding="utf-8")

        initial_entry = MemoryEntry(
            entry_id="init_001",
            title="Initial Workspace Bootstrap",
            content=f"Memory structure initialized for {ws_dir.name}",
            tags=["bootstrap", "init"],
            scope=MemoryScope.PROJECT,
        )
        self.store(initial_entry)

        return {
            "workspace": str(ws_dir),
            "memory_dir": str(mem_dir),
            "entry_count": len(self._get_entries()),
        }

    def update_from_diff(self, diff_text: str) -> int:
        """Incrementally updates memory state from Git diff text."""
        if not diff_text.strip():
            return 0

        changed_files: list[str] = []
        for line in diff_text.splitlines():
            if line.startswith("+++ b/"):
                changed_files.append(line.replace("+++ b/", "").strip())

        if not changed_files:
            return 0

        new_entry = MemoryEntry(
            entry_id=f"diff_{len(self._get_entries()) + 1}",
            title="Git Diff Incremental Update",
            content="Changed files:\n" + "\n".join(changed_files),
            tags=["git-diff", "incremental"],
            scope=MemoryScope.PROJECT,
        )
        self.store(new_entry)
        return 1

    def get_memory_summary(self) -> str:
        """Retrieves project summary Markdown content (Memory First Level 1)."""
        base_dir_val: Any = getattr(self._store, "base_dir", Path(".agents/memory"))
        summary_path = Path(base_dir_val) / "project-summary.md"
        if summary_path.is_file():
            try:
                return summary_path.read_text(encoding="utf-8")
            except Exception as exc:
                logger.warning(f"Error reading project-summary.md: {exc}")

        entries = self._get_entries()
        if entries:
            return f"# Project Summary\n\nActive memory entries: {len(entries)}"

        return "# Project Summary\n\nNo memory entries stored."


__all__ = ["MemoryService"]
