"""Ports (abstract interfaces) the application depends on — dependency inversion.

Infrastructure adapters implement these; the application never imports concretes.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from .models import FileMeta, Message, UploadSession


class MessageStore(ABC):
    @abstractmethod
    def append(self, message: Message) -> None: ...

    @abstractmethod
    def read_since(self, since: int) -> list[Message]: ...

    @abstractmethod
    def max_seq(self) -> int: ...


class FileStore(ABC):
    @abstractmethod
    def commit_file(self, name: str, src: Path) -> FileMeta:
        """Atomically move a completed upload's partial file into the store."""

    @abstractmethod
    def resolve(self, name: str) -> Path | None:
        """Return the on-disk path of a stored file (for Range streaming), or None."""

    @abstractmethod
    def list(self) -> list[FileMeta]: ...


class UploadSessionStore(ABC):
    @abstractmethod
    def create(self, name: str, sender: str, to: str | None, length: int) -> UploadSession: ...

    @abstractmethod
    def get(self, upload_id: str) -> UploadSession | None: ...

    @abstractmethod
    def write_chunk(self, upload_id: str, offset: int, data: bytes) -> int:
        """Append a chunk at `offset`; return the new offset. Raise ValueError on offset mismatch."""

    @abstractmethod
    def partial_path(self, upload_id: str) -> Path: ...

    @abstractmethod
    def discard(self, upload_id: str) -> None:
        """Drop session metadata (and any leftover partial) after finalize/abort."""


class ClientChannel(ABC):
    """A connected realtime subscriber (one WebSocket client)."""

    name: str
    last_seq: int

    @abstractmethod
    def deliver(self, message: Message) -> None: ...

    @abstractmethod
    def is_alive(self) -> bool: ...


class ClientRegistry(ABC):
    @abstractmethod
    def add(self, channel: ClientChannel) -> None: ...

    @abstractmethod
    def remove(self, channel: ClientChannel) -> None: ...

    @abstractmethod
    def snapshot(self) -> list[ClientChannel]: ...


class Clock(ABC):
    @abstractmethod
    def now_iso(self) -> str: ...


class MessageCipher(ABC):
    """End-to-end content codec used on the client side only (server stays oblivious)."""

    @abstractmethod
    def encrypt(self, plaintext: str) -> str: ...

    @abstractmethod
    def decrypt(self, text: str) -> str: ...
