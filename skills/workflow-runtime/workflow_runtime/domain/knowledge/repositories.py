from typing import Protocol

from workflow_runtime.domain.knowledge.entities import MemoryEntry, RAGResult


class IKnowledgeRepository(Protocol):
    def store_memory(self, entry: MemoryEntry) -> None:
        ...

    def query_memory(self, tags: list[str]) -> list[MemoryEntry]:
        ...

    def search_rag(self, query: str, top_k: int) -> list[RAGResult]:
        ...
