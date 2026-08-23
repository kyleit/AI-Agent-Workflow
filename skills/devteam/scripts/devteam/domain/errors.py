"""Domain errors — typed, serializable, no I/O."""

from __future__ import annotations


class ErrorCode:
    UNKNOWN_SEAT = "UNKNOWN_SEAT"
    SCHEMA_INVALID = "SCHEMA_INVALID"
    ABSOLUTE_PATH = "ABSOLUTE_PATH"
    WRITESET_OVERLAP = "WRITESET_OVERLAP"
    NOT_INITIALIZED = "NOT_INITIALIZED"
    DUPLICATE_LEADER = "DUPLICATE_LEADER"
    ALREADY_INITIALIZED = "ALREADY_INITIALIZED"
    LOCK_CONFLICT = "LOCK_CONFLICT"
    LOCK_NOT_HELD = "LOCK_NOT_HELD"
    INTERNAL = "INTERNAL"


class DevTeamError(Exception):
    """Base error carrying a stable code + optional structured details."""

    def __init__(self, code: str, message: str, details: dict | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details or {}

    def to_json(self) -> dict:
        return {
            "ok": False,
            "error": {"code": self.code, "message": self.message, "details": self.details},
        }
