"""E2EE envelope (de)serialization. The relay stores this opaque string as `text`."""
from __future__ import annotations

import json
from typing import Any

ALG = "scrypt-sha256ctr-hmac-v1"


def is_envelope(text: str) -> bool:
    if not text or not text.startswith("{"):
        return False
    try:
        obj = json.loads(text)
    except (ValueError, TypeError):
        return False
    return isinstance(obj, dict) and obj.get("e2ee") == 1 and obj.get("alg") == ALG


def pack(salt_b64: str, nonce_b64: str, ct_b64: str, tag_b64: str) -> str:
    return json.dumps(
        {"e2ee": 1, "alg": ALG, "salt": salt_b64, "nonce": nonce_b64, "ct": ct_b64, "tag": tag_b64},
        separators=(",", ":"),
    )


def unpack(text: str) -> dict[str, Any]:
    return json.loads(text)
