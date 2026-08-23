"""BusService — the core use-cases, orchestrating injected ports only."""
from __future__ import annotations

import threading
from pathlib import Path

from ..domain.models import FileMeta, Message
from ..domain.ports import ClientChannel, ClientRegistry, Clock, FileStore, MessageStore
from ..domain.routing import targets


class BusService:
    def __init__(
        self,
        messages: MessageStore,
        files: FileStore,
        registry: ClientRegistry,
        clock: Clock,
    ) -> None:
        self._messages = messages
        self._files = files
        self._registry = registry
        self._clock = clock
        self._lock = threading.RLock()
        self._seq = messages.max_seq()

    @property
    def message_count(self) -> int:
        with self._lock:
            return self._seq

    def add_message(self, sender: str, text: str, to: str | None = None) -> Message:
        with self._lock:
            self._seq += 1
            message = Message(
                seq=self._seq,
                ts=self._clock.now_iso(),
                sender=sender,
                to=(to or None),
                text=text,
            )
            self._messages.append(message)
        self._dispatch(message)
        return message

    def read_since(self, since: int, name: str | None = None) -> list[Message]:
        history = self._messages.read_since(since)
        if name is None:
            return history
        return [m for m in history if targets(m, name)]

    def register(self, channel: ClientChannel) -> list[Message]:
        """Snapshot the targeted replay AND register the channel under one lock.

        Registering under the same lock as the snapshot guarantees no message is
        lost; the channel's own seq-dedup prevents any duplicate that a concurrent
        broadcast could introduce.
        """
        with self._lock:
            replay = [m for m in self._messages.read_since(channel.last_seq) if targets(m, channel.name)]
            self._registry.add(channel)
        return replay

    def unregister(self, channel: ClientChannel) -> None:
        self._registry.remove(channel)

    def commit_upload(self, name: str, src: Path, sender: str, to: str | None = None) -> FileMeta:
        meta = self._files.commit_file(name, src)
        self.add_message(sender, f"[file] {meta.name} ({meta.size} bytes) uploaded by {sender}", to)
        return meta

    def list_files(self) -> list[FileMeta]:
        return self._files.list()

    def resolve_file(self, name: str) -> Path | None:
        return self._files.resolve(name)

    def ws_client_count(self) -> int:
        return sum(1 for channel in self._registry.snapshot() if channel.is_alive())

    def _dispatch(self, message: Message) -> None:
        for channel in self._registry.snapshot():
            channel.deliver(message)
        for channel in self._registry.snapshot():
            if not channel.is_alive():
                self._registry.remove(channel)
