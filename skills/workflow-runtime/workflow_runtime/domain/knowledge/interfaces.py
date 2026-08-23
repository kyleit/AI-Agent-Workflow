import abc
from typing import Any


class IKnowledgeProvider(abc.ABC):
    """
    Interface for Knowledge Providers (Markdown, SQLite, Obsidian, Vector, etc.).
    """

    @abc.abstractmethod
    def search(self, query: str, limit: int = 5) -> list[dict[str, Any]]:
        """Search knowledge using this provider."""

    @abc.abstractmethod
    def read(self, path: str) -> str:
        """Read a knowledge document."""

    @abc.abstractmethod
    def save(self, path: str, content: str) -> bool:
        """Save/create a knowledge document."""

    @abc.abstractmethod
    def is_available(self) -> bool:
        """Check if provider is available and properly configured."""
