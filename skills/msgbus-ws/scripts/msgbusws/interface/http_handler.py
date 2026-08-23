"""HTTP + WebSocket request handler mapping the wire protocol onto BusService.

Handles: REST (/health, /send, /recv, /list), tus resumable upload (/files),
Range download (/download), and the WebSocket relay (/ws). The handler treats
message `text` as opaque, so E2EE content passes through untouched.
"""
from __future__ import annotations

import base64
import json
import os
import sys
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, unquote, urlparse

from ..application.bus_service import BusService
from ..domain.ports import UploadSessionStore
from ..infrastructure import ws_protocol
from ..infrastructure.memory_registry import WsClientChannel

TUS_VERSION = "1.0.0"
TUS_MAX_SIZE = 1024 * 1024 * 1024  # 1 GiB


def _decode_metadata(raw: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for pair in (raw or "").split(","):
        pair = pair.strip()
        if not pair:
            continue
        parts = pair.split(" ", 1)
        key = parts[0]
        value = base64.b64decode(parts[1]).decode("utf-8") if len(parts) > 1 and parts[1] else ""
        out[key] = value
    return out


def make_handler(service: BusService, uploads: UploadSessionStore, token: str):
    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"
        server_version = "msgbus-ws/1.0"

        def log_message(self, fmt, *args):
            sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))

        # ---- helpers ---------------------------------------------------- #
        def _json(self, obj, code=200, extra=None):
            body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            for key, value in (extra or {}).items():
                self.send_header(key, value)
            self.end_headers()
            self.wfile.write(body)

        def _empty(self, code, headers=None):
            self.send_response(code)
            for key, value in (headers or {}).items():
                self.send_header(key, value)
            self.send_header("Content-Length", "0")
            self.end_headers()

        def _auth(self) -> bool:
            return self.headers.get("X-Token", "") == token

        def _hdr(self, name: str, default: str | None = None) -> str | None:
            """Read a header value, percent-decoding (Vietnamese names arrive quoted)."""
            raw = self.headers.get(name)
            return unquote(raw) if raw is not None else default

        def _read_body(self) -> bytes:
            n = int(self.headers.get("Content-Length", 0) or 0)
            return self.rfile.read(n) if n else b""

        # ---- OPTIONS (tus capabilities) --------------------------------- #
        def do_OPTIONS(self):
            if urlparse(self.path).path.rstrip("/") == "/files":
                self._empty(204, {
                    "Tus-Resumable": TUS_VERSION,
                    "Tus-Version": TUS_VERSION,
                    "Tus-Extension": "creation",
                    "Tus-Max-Size": str(TUS_MAX_SIZE),
                })
                return
            self._empty(404)

        # ---- GET -------------------------------------------------------- #
        def do_GET(self):
            parsed = urlparse(self.path)
            path, qs = parsed.path, parse_qs(parsed.query)
            if path == "/ws":
                self._handle_ws(qs)
                return
            if path == "/health":
                self._json({
                    "ok": True,
                    "messages": service.message_count,
                    "files": len(service.list_files()),
                    "ws_clients": service.ws_client_count(),
                })
                return
            if not self._auth():
                self._json({"error": "unauthorized"}, 401)
                return
            if path == "/recv":
                since = int((qs.get("since", ["0"])[0]) or 0)
                name = self._hdr("X-From") or None
                self._json([m.to_dict() for m in service.read_since(since, name)])
                return
            if path == "/list":
                self._json([f.to_dict() for f in service.list_files()])
                return
            if path == "/download":
                self._download(qs)
                return
            self._json({"error": "not_found"}, 404)

        def _download(self, qs):
            name = os.path.basename(qs.get("name", [""])[0])
            path = service.resolve_file(name) if name else None
            if path is None:
                self._json({"error": "not_found", "name": name}, 404)
                return
            size = path.stat().st_size
            start, end, code = 0, size - 1, 200
            rng = self.headers.get("Range", "")
            if rng.startswith("bytes="):
                lo, _, hi = rng[len("bytes="):].split(",")[0].partition("-")
                if lo.strip():
                    start, code = int(lo), 206
                    end = int(hi) if hi.strip() else size - 1
                elif hi.strip():
                    start, code = max(0, size - int(hi)), 206
            if start >= size:
                self._empty(416, {"Content-Range": f"bytes */{size}"})
                return
            length = end - start + 1
            headers = {"Content-Type": "application/octet-stream", "Accept-Ranges": "bytes"}
            if code == 206:
                headers["Content-Range"] = f"bytes {start}-{end}/{size}"
            self.send_response(code)
            for key, value in headers.items():
                self.send_header(key, value)
            self.send_header("Content-Length", str(length))
            self.end_headers()
            with path.open("rb") as f:
                f.seek(start)
                remaining = length
                while remaining > 0:
                    chunk = f.read(min(65536, remaining))
                    if not chunk:
                        break
                    self.wfile.write(chunk)
                    remaining -= len(chunk)

        # ---- POST (send + tus create) ----------------------------------- #
        def do_POST(self):
            parsed = urlparse(self.path)
            path = parsed.path
            if not self._auth():
                self._read_body()
                self._json({"error": "unauthorized"}, 401)
                return
            if path == "/send":
                text = self._read_body().decode("utf-8", errors="replace")
                frm = self._hdr("X-From", "unknown")
                to = self._hdr("X-To") or None
                message = service.add_message(frm, text, to)
                self._json({"seq": message.seq})
                return
            if path.rstrip("/") == "/files":
                self._tus_create()
                return
            self._read_body()
            self._json({"error": "not_found"}, 404)

        def _tus_create(self):
            length = int(self.headers.get("Upload-Length", "0") or 0)
            meta = _decode_metadata(self.headers.get("Upload-Metadata", ""))
            name = os.path.basename(meta.get("filename") or meta.get("name") or "upload.bin")
            sender = meta.get("from") or self._hdr("X-From", "unknown")
            to = meta.get("to") or None
            self._read_body()  # creation-with-upload not supported; drain any body
            session = uploads.create(name, sender, to, length)
            self._empty(201, {
                "Location": f"/files/{session.upload_id}",
                "Tus-Resumable": TUS_VERSION,
                "Upload-Offset": "0",
            })

        # ---- HEAD (tus offset) ------------------------------------------ #
        def do_HEAD(self):
            path = urlparse(self.path).path
            if path.startswith("/files/") and self._auth():
                session = uploads.get(path[len("/files/"):])
                if session is None:
                    self._empty(404)
                    return
                self._empty(200, {
                    "Upload-Offset": str(session.offset),
                    "Upload-Length": str(session.length),
                    "Tus-Resumable": TUS_VERSION,
                    "Cache-Control": "no-store",
                })
                return
            self._empty(404)

        # ---- PATCH (tus chunk) ------------------------------------------ #
        def do_PATCH(self):
            path = urlparse(self.path).path
            if not path.startswith("/files/"):
                self._read_body()
                self._empty(404)
                return
            if not self._auth():
                self._read_body()
                self._json({"error": "unauthorized"}, 401)
                return
            upload_id = path[len("/files/"):]
            session = uploads.get(upload_id)
            if session is None:
                self._read_body()
                self._empty(404)
                return
            offset = int(self.headers.get("Upload-Offset", "0") or 0)
            data = self._read_body()
            try:
                new_offset = uploads.write_chunk(upload_id, offset, data)
            except ValueError:
                self._empty(409, {"Upload-Offset": str(session.offset), "Tus-Resumable": TUS_VERSION})
                return
            session = uploads.get(upload_id)
            if session is not None and session.complete:
                service.commit_upload(session.name, uploads.partial_path(upload_id), session.sender, session.to)
                uploads.discard(upload_id)
            self._empty(204, {"Upload-Offset": str(new_offset), "Tus-Resumable": TUS_VERSION})

        # ---- WebSocket relay -------------------------------------------- #
        def _handle_ws(self, qs):
            if qs.get("token", [""])[0] != token:
                self._json({"error": "unauthorized"}, 401)
                return
            key = self.headers.get("Sec-WebSocket-Key")
            if not key:
                self._json({"error": "bad_ws_handshake"}, 400)
                return
            self.send_response(101)
            self.send_header("Upgrade", "websocket")
            self.send_header("Connection", "Upgrade")
            self.send_header("Sec-WebSocket-Accept", ws_protocol.accept_key(key))
            self.end_headers()
            self.close_connection = True

            name = qs.get("name", ["anon"])[0]
            since = int((qs.get("since", ["0"])[0]) or 0)
            channel = WsClientChannel(self.request, name, since)
            for message in service.register(channel):
                channel.deliver(message)
            try:
                self._ws_loop(channel)
            except OSError:
                pass
            finally:
                channel.kill()
                service.unregister(channel)

        def _ws_loop(self, channel):
            while True:
                frame = ws_protocol.read_frame(self.rfile)
                if frame is None:
                    break
                _, opcode, data = frame
                if opcode == ws_protocol.OP_CLOSE:
                    break
                if opcode == ws_protocol.OP_PING:
                    channel.send_control(data, ws_protocol.OP_PONG)
                    continue
                if opcode == ws_protocol.OP_PONG:
                    continue
                if opcode in (ws_protocol.OP_TEXT, ws_protocol.OP_BINARY):
                    text = data.decode("utf-8", errors="replace")
                    if not text.strip():
                        continue
                    to = None
                    try:
                        obj = json.loads(text)
                        if isinstance(obj, dict) and "text" in obj:
                            to = obj.get("to") or None
                            text = str(obj["text"])
                    except ValueError:
                        pass
                    service.add_message(channel.name, text, to)

    return Handler
