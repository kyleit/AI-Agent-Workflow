"""ResourcePath normalization — repo-relative, §22-safe (no absolute, no escape)."""

from __future__ import annotations

import ntpath
import posixpath

from ..errors import DevTeamError, ErrorCode


def normalize_resource(path: str) -> str:
    if not path:
        raise DevTeamError(ErrorCode.SCHEMA_INVALID, "lock path required")
    norm = path.replace("\\", "/")
    if posixpath.isabs(norm) or ntpath.isabs(path) or ".." in norm.split("/"):
        raise DevTeamError(ErrorCode.ABSOLUTE_PATH, f"absolute/escaping path {path!r}")
    return posixpath.normpath(norm).strip("/")
