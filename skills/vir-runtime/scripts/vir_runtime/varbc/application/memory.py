from typing import Dict, Optional
from vir_runtime.varbc.domain.baseline import UIBaseline
from vir_runtime.varbc.application.ports import MemoryManagerPort


class MemoryManager(MemoryManagerPort):
    """In-memory state cache adapter providing fast access to baseline visual context."""

    def __init__(self) -> None:
        """Initializes empty in-memory context dictionary."""
        self._cache: Dict[str, UIBaseline] = {}

    async def get_context(self, component_id: str) -> Optional[UIBaseline]:
        """Retrieves cached baseline for component_id."""
        return self._cache.get(component_id)

    async def update_memory(self, baseline: UIBaseline) -> None:
        """Updates or adds baseline into in-memory cache."""
        self._cache[baseline.component_id] = baseline

    def clear(self) -> None:
        """Clears all cached visual context."""
        self._cache.clear()
