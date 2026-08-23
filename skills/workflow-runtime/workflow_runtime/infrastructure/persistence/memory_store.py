"""In-memory persistence store and memory state persistence adapter."""

from pathlib import Path
from typing import Any

from workflow_runtime.domain.knowledge.entities import MemoryEntry
from workflow_runtime.domain.workflow.entities import Checkpoint, WorkflowState
from workflow_runtime.domain.workflow.repositories import IWorkflowRepository
from workflow_runtime.infrastructure.knowledge.memory_store_adapter import \
    MemoryStoreAdapter
from workflow_runtime.shared.errors import EntityNotFoundError


class MemoryStore(IWorkflowRepository):
    """In-memory dictionary repository for session states and memory state file adapter."""

    def __init__(self, base_dir: str | Path | None = None) -> None:
        self._states: dict[str, WorkflowState] = {}
        self._checkpoints: dict[str, list[Checkpoint]] = {}
        self._kv_store: dict[str, Any] = {}
        self._file_adapter = MemoryStoreAdapter(base_dir)

    def get_state(self, session_id: str) -> WorkflowState:
        """Retrieves WorkflowState entity for session_id.

        Raises:
            EntityNotFoundError: If session state is not stored.
        """
        if session_id not in self._states:
            raise EntityNotFoundError(f"Session '{session_id}' not found in memory store.")
        return self._states[session_id]

    def save_state(self, state: WorkflowState) -> None:
        """Saves WorkflowState entity to memory."""
        self._states[state.session_id] = state

    def record_checkpoint(self, checkpoint: Checkpoint) -> None:
        """Records a Checkpoint entity."""
        session_id = "default"
        if session_id not in self._checkpoints:
            self._checkpoints[session_id] = []
        self._checkpoints[session_id].append(checkpoint)

    def list_checkpoints(self, session_id: str) -> list[Checkpoint]:
        """Lists all Checkpoints for session_id."""
        return list(self._checkpoints.get(session_id, []))

    def read_state(self, key: str | None = None) -> Any:
        """Reads key-value store entry or full dict."""
        if key is not None:
            return self._kv_store.get(key)
        return dict(self._kv_store)

    def write_state(self, key: str, value: Any) -> None:
        """Writes key-value pair to transient memory store."""
        self._kv_store[key] = value

    def clear(self) -> None:
        """Clears all stored data."""
        self._states.clear()
        self._checkpoints.clear()
        self._kv_store.clear()

    # Memory State & Document Persistence Methods
    def load_memory_state(self) -> list[MemoryEntry]:
        return self._file_adapter.load_memory_state()

    def save_memory_state(self, entries: list[MemoryEntry]) -> None:
        self._file_adapter.save_memory_state(entries)

    def search_markdown_files(
        self, keyword: str, root_dir: str | Path | None = None
    ) -> list[dict[str, Any]]:
        return self._file_adapter.search_markdown_files(keyword, root_dir)
