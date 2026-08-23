from abc import ABC, abstractmethod
from typing import Any

from workflow_runtime.domain.knowledge.entities import MemoryEntry, RAGResult


class IMemoryStorePort(ABC):
    @abstractmethod
    def load_memory_state(self) -> list[MemoryEntry]:
        pass

    @abstractmethod
    def save_memory_state(self, entries: list[MemoryEntry]) -> None:
        pass

    @abstractmethod
    def search_markdown_files(self, keyword: str, search_dir: Any = None) -> list[Any]:
        pass

class IRAGStorePort(ABC):
    @abstractmethod
    def index_document(self, relative_path: str, content: str, doc_metadata: dict[str, Any] | None = None) -> None:
        pass

    @abstractmethod
    def query_fts(self, query: str, limit: int = 5) -> list[RAGResult]:
        pass

    @abstractmethod
    def query_vector(self, query_text: str, limit: int = 5) -> list[dict[str, Any]]:
        pass

    @abstractmethod
    def close(self) -> None:
        pass
