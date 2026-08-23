"""Structured JSON stdout envelope for every CLI command."""

from __future__ import annotations

import json
import sys

from ...domain.errors import DevTeamError


def ok(payload: dict) -> int:
    sys.stdout.write(json.dumps({"ok": True, **payload}, ensure_ascii=False) + "\n")
    return 0


def err(e: Exception) -> int:
    if isinstance(e, DevTeamError):
        sys.stdout.write(json.dumps(e.to_json(), ensure_ascii=False) + "\n")
        return 2
    body = {"ok": False, "error": {"code": "INTERNAL", "message": str(e), "details": {}}}
    sys.stdout.write(json.dumps(body, ensure_ascii=False) + "\n")
    return 1
