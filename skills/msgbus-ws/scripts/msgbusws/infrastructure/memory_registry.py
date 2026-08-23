"""In-memory WebSocket client registry + the WS client channel adapter."""
from __future__ import annotations

import json
import socket
import threading

from ..domain.models import Message
from ..domain.ports import ClientChannel, ClientRegistry
from ..domain.routing import targets
from . import ws_protocol


class WsClientChannel(ClientChannel):
    """One connected WebSocket subscriber. Seq-dedup + routing happen here."""

    def __init__(self, sock: socket.socket, name: str, since: int) -> None:
        self._sock = sock
        self.name = name
        self.last_seq = since
        self._lock = threading.Lock()
        self._alive = True

    def deliver(self, message: Message) -> None:
        with self._lock:
            if not self._alive or message.seq <= self.last_seq:
                return
            self.last_seq = message.seq  # advance for every seq, even if not for us
            if not targets(message, self.name):
                return
            payload = json.dumps(message.to_dict(), ensure_ascii=False).encode("utf-8")
            try:
                self._sock.sendall(ws_protocol.encode(payload, ws_protocol.OP_TEXT))
            except OSError:
                self._alive = False

    def send_control(self, payload: bytes, opcode: int) -> None:
        with self._lock:
            if not self._alive:
                return
            try:
                self._sock.sendall(ws_protocol.encode(payload, opcode))
            except OSError:
                self._alive = False

    def is_alive(self) -> bool:
        return self._alive

    def kill(self) -> None:
        self._alive = False


class MemoryRegistry(ClientRegistry):
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._channels: list[ClientChannel] = []

    def add(self, channel: ClientChannel) -> None:
        with self._lock:
            self._channels.append(channel)

    def remove(self, channel: ClientChannel) -> None:
        with self._lock:
            self._channels = [c for c in self._channels if c is not channel]

    def snapshot(self) -> list[ClientChannel]:
        with self._lock:
            return list(self._channels)
