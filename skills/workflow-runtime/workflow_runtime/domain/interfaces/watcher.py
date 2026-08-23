from abc import ABC, abstractmethod
from typing import Callable


class IFileWatcher(ABC):
    @abstractmethod
    def watch(self, path: str, callback: Callable[[str], None]) -> None:
        pass

    @abstractmethod
    def stop(self) -> None:
        pass
