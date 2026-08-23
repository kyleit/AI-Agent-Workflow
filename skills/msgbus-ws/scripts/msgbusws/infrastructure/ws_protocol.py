"""RFC 6455 WebSocket frame codec + handshake helper. Shared by server and client."""
from __future__ import annotations

import base64
import hashlib
import os
from typing import BinaryIO

OP_TEXT = 0x1
OP_BINARY = 0x2
OP_CLOSE = 0x8
OP_PING = 0x9
OP_PONG = 0xA

WS_GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B16"


def encode(payload: bytes, opcode: int = OP_TEXT, mask: bool = False) -> bytes:
    """Encode one frame. Server->client uses mask=False; client->server mask=True."""
    header = bytearray([0x80 | opcode])
    mask_bit = 0x80 if mask else 0x00
    n = len(payload)
    if n < 126:
        header.append(mask_bit | n)
    elif n < 65536:
        header.append(mask_bit | 126)
        header += n.to_bytes(2, "big")
    else:
        header.append(mask_bit | 127)
        header += n.to_bytes(8, "big")
    if mask:
        key = os.urandom(4)
        header += key
        payload = bytes(b ^ key[i % 4] for i, b in enumerate(payload))
    return bytes(header) + payload


def _read_exact(rf: BinaryIO, n: int) -> bytes:
    buf = bytearray()
    while len(buf) < n:
        chunk = rf.read(n - len(buf))
        if not chunk:
            break
        buf.extend(chunk)
    return bytes(buf)


def read_frame(rf: BinaryIO):
    """Read one frame from a binary file-like. Return (fin, opcode, data) or None at EOF."""
    head = _read_exact(rf, 2)
    if len(head) < 2:
        return None
    b0, b1 = head[0], head[1]
    fin = bool(b0 & 0x80)
    opcode = b0 & 0x0F
    masked = bool(b1 & 0x80)
    length = b1 & 0x7F
    if length == 126:
        length = int.from_bytes(_read_exact(rf, 2), "big")
    elif length == 127:
        length = int.from_bytes(_read_exact(rf, 8), "big")
    key = _read_exact(rf, 4) if masked else b""
    data = _read_exact(rf, length) if length else b""
    if masked and data:
        data = bytes(b ^ key[i % 4] for i, b in enumerate(data))
    return fin, opcode, data


def accept_key(sec_websocket_key: str) -> str:
    digest = hashlib.sha1((sec_websocket_key + WS_GUID).encode("ascii")).digest()
    return base64.b64encode(digest).decode("ascii")
