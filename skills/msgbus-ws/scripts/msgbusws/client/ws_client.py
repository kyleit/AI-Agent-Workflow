"""WebSocket transport with one owned connection and callback-safe replay."""
from __future__ import annotations

import base64
import json
import os
import socket
import ssl
import threading
import time
from urllib.parse import urlencode

from ..infrastructure import ws_protocol

RECONNECT_BACKOFF = 1.5


class WsClient:
    def __init__(self, config) -> None:
        self._config = config

    def _connect(self, name: str, since: int) -> socket.socket:
        sock = socket.create_connection((self._config.host, self._config.port), timeout=10)
        try:
            if self._config.secure:
                sock = ssl.create_default_context().wrap_socket(sock, server_hostname=self._config.host)
            key = base64.b64encode(os.urandom(16)).decode("ascii")
            query = {**self._config.metadata(), "token": self._config.token,
                     "name": name, "since": since, "kind": "agent"}
            path = "/ws?" + urlencode(query)
            request = (
                f"GET {path} HTTP/1.1\r\nHost: {self._config.host}:{self._config.port}\r\n"
                "User-Agent: msgbus-ws-client/1.0\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n"
                f"Sec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n"
            )
            sock.sendall(request.encode("ascii"))
            buf = b""
            while b"\r\n\r\n" not in buf:
                chunk = sock.recv(1)
                if not chunk:
                    raise ConnectionError("WebSocket handshake closed")
                buf += chunk
                if len(buf) > 65536:
                    raise ConnectionError("WebSocket response headers are too large")
            lines = buf.decode("iso-8859-1").split("\r\n")
            if lines[0].split()[1] != "101":
                raise ConnectionError("WebSocket handshake rejected")
            headers = {key.lower().strip(): value.strip() for key, sep, value in
                       (line.partition(":") for line in lines[1:]) if sep}
            if headers.get("sec-websocket-accept") != ws_protocol.accept_key(key):
                raise ConnectionError("Invalid WebSocket accept key")
            sock.settimeout(None)
            return sock
        except BaseException:
            sock.close()
            raise

    def listen(self, on_message, since: int = 0, name: str | None = None,
               on_connected=None, heartbeat_factory=None,
               heartbeat_interval: float = 15.0) -> None:
        state = {"seq": since, "stop": False}
        while not state["stop"]:
            try:
                sock = self._connect(name or self._config.sender, state["seq"])
            except OSError:
                time.sleep(RECONNECT_BACKOFF)
                continue
            try:
                self._connection(sock, on_message, state, on_connected,
                                 heartbeat_factory, heartbeat_interval)
            except OSError:
                pass
            if not state["stop"]:
                time.sleep(RECONNECT_BACKOFF)

    def _connection(self, sock, on_message, state, on_connected, heartbeat_factory, interval):
        write_lock = threading.Lock()
        stopped = threading.Event()
        heartbeat = None

        def send_control(payload: bytes, opcode: int) -> None:
            with write_lock:
                if stopped.is_set():
                    raise ConnectionError("Connection is stopping")
                sock.sendall(ws_protocol.encode(payload, opcode, mask=True))

        def send_event(payload: dict) -> None:
            send_control(json.dumps(payload, ensure_ascii=False).encode("utf-8"), ws_protocol.OP_TEXT)

        def beat() -> None:
            while not stopped.wait(interval):
                try:
                    send_event(heartbeat_factory())
                except (OSError, ValueError, RuntimeError):
                    try:
                        sock.shutdown(socket.SHUT_RDWR)
                    except OSError:
                        pass
                    return

        try:
            if on_connected is not None:
                on_connected(send_event)
            if heartbeat_factory is not None and interval > 0:
                heartbeat = threading.Thread(target=beat, daemon=True)
                heartbeat.start()
            with sock.makefile("rb") as stream:
                self._pump(sock, stream, on_message, state, send_control)
        finally:
            stopped.set()
            try:
                sock.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            sock.close()
            if heartbeat is not None:
                heartbeat.join(timeout=2)

    def _pump(self, sock, rf, on_message, state, send_control=None) -> None:
        while True:
            frame = ws_protocol.read_frame(rf)
            if frame is None:
                return
            _, opcode, data = frame
            if opcode == ws_protocol.OP_CLOSE:
                return
            if opcode == ws_protocol.OP_PING:
                if send_control is None:
                    sock.sendall(ws_protocol.encode(data, ws_protocol.OP_PONG, mask=True))
                else:
                    send_control(data, ws_protocol.OP_PONG)
                continue
            if opcode not in (ws_protocol.OP_TEXT, ws_protocol.OP_BINARY):
                continue
            try:
                record = json.loads(data.decode("utf-8"))
                if not isinstance(record, dict) or type(record.get("seq")) is not int:
                    continue
                seq = record["seq"]
                if seq <= state["seq"]:
                    continue
            except (ValueError, UnicodeError):
                continue
            stop = on_message(record)
            state["seq"] = seq
            if stop:
                state["stop"] = True
                return

    def send_text(self, text: str, to: str | None = None, name: str | None = None) -> None:
        sock = self._connect(name or self._config.sender, 0)
        try:
            payload = json.dumps({"to": to, "text": text}, ensure_ascii=False) if to else text
            sock.sendall(ws_protocol.encode(payload.encode("utf-8"), ws_protocol.OP_TEXT, mask=True))
            time.sleep(0.3)
        finally:
            try:
                sock.sendall(ws_protocol.encode(b"", ws_protocol.OP_CLOSE, mask=True))
            except OSError:
                pass
            sock.close()
