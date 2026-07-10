import abc

class BaseProvider(abc.ABC):
    @abc.abstractmethod
    def search(self, query: str, limit: int = 5) -> list[dict]:
        """Search knowledge using this provider."""
        pass

    @abc.abstractmethod
    def read(self, path: str) -> str:
        """Read a knowledge document."""
        pass

    @abc.abstractmethod
    def save(self, path: str, content: str) -> bool:
        """Save/create a knowledge document."""
        pass

    @abc.abstractmethod
    def is_available(self) -> bool:
        """Check if provider is available and properly configured."""
        pass
