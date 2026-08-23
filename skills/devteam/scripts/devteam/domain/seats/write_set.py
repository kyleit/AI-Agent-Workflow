"""WriteSet value object — the directories a seat owns, with overlap logic."""

from __future__ import annotations

import posixpath
from dataclasses import dataclass


@dataclass(frozen=True)
class WriteSet:
    dirs: tuple[str, ...]

    def normalized(self) -> list[str]:
        out = []
        for d in self.dirs:
            n = posixpath.normpath(d.replace("\\", "/")).strip("/")
            out.append(n or ".")
        return out

    def overlaps(self, other: "WriteSet") -> bool:
        for a in self.normalized():
            for b in other.normalized():
                if a == b:
                    return True
                if a == "." or b == ".":
                    return True
                if a.startswith(b + "/") or b.startswith(a + "/"):
                    return True
        return False
