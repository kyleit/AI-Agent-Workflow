"""Raw-socket WebSocket adapter: realtime listen (with reconnect) + one-shot send."""
from __future__ import annotations

import base64
import json
import os
import socket
import ssl
import time
from urllib.parse import quote

from ..infrastructure import ws_protocol

RECONNECT_BACKOFF = 1.5


class WsClient:
    def __init__(self, config) -> None:
        self._config = config

    def _connect(self, name: str, since: int) -> socket.socket:
        sock = socket.create_connection((self._config.host, self._config.port), timeout=10)
        if getattr(self._config, "secure", False):
            sock = ssl.create_default_context().wrap_socket(sock, server_hostname=self._config.host)
        key = base64.b64encode(os.urandom(16)).decode("ascii")
        path = f"/ws?token={quote(self._config.token, safe='')}&name={quote(name, safe='')}&since={since}"
        request = (
            f"GET {path} HTTP/1.1\r\n"
            f"Host: {self._config.host}:{self._config.port}\r\n"
            "User-Agent: msgbus-ws-client/1.0\r\n"
            "Upgrade: websocket\r\nConnection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n"
        )
        sock.sendall(request.encode("ascii"))
        buf = b""
        while b"\r\n\r\n" not in buf:
            chunk = sock.recv(1)
            if not chunk:
                raise ConnectionError("ws handshake failed (connection closed)")
            buf += chunk
        status_line = buf.split(b"\r\n", 1)[0]
        if b"101" not in status_line:
            raise ConnectionError(f"ws handshake rejected: {status_line!r}")
        sock.settimeout(None)
        return sock

    def listen(self, on_message, since: int = 0, name: str | None = None) -> None:
        """Stream messages, reconnecting from the highest seq seen (no dup/loss).

        `on_message(record)` returning a truthy value stops the loop. The resume
        cursor lives in `state` so it survives a mid-read disconnect (which may
        surface as an OSError, not a clean EOF) — otherwise a reconnect would
        replay from the wrong offset and duplicate messages.
        """
        name = name or self._config.sender
        state = {"seq": since, "stop": False}
        while not state["stop"]:
            try:
                sock = self._connect(name, state["seq"])
                try:
                    self._pump(sock, sock.makefile("rb"), on_message, state)
                finally:
                    sock.close()
            except OSError:
                pass
            if state["stop"]:
                return
            time.sleep(RECONNECT_BACKOFF)

    def _pump(self, sock, rf, on_message, state) -> None:
        while True:
            frame = ws_protocol.read_frame(rf)
            if frame is None:
                return
            _, opcode, data = frame
            if opcode == ws_protocol.OP_CLOSE:
                return
            if opcode == ws_protocol.OP_PING:
                sock.sendall(ws_protocol.encode(data, ws_protocol.OP_PONG, mask=True))
                continue
            if opcode == ws_protocol.OP_PONG:
                continue
            if opcode in (ws_protocol.OP_TEXT, ws_protocol.OP_BINARY):
                try:
                    record = json.loads(data.decode("utf-8", errors="replace"))
                except ValueError:
                    continue
                seq = int(record.get("seq", 0))
                if seq > state["seq"]:
                    state["seq"] = seq
                if on_message(record):
                    state["stop"] = True
                    return

    def send_text(self, text: str, to: str | None = None, name: str | None = None) -> None:
        name = name or self._config.sender
        sock = self._connect(name, 0)
        try:
            payload = json.dumps({"to": to, "text": text}, ensure_ascii=False) if to else text
            sock.sendall(ws_protocol.encode(payload.encode("utf-8"), ws_protocol.OP_TEXT, mask=True))
            time.sleep(0.3)  # let the server store + broadcast before we close
        finally:
            try:
                sock.sendall(ws_protocol.encode(b"", ws_protocol.OP_CLOSE, mask=True))
            except OSError:
                pass
            sock.close()
