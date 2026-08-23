"""GitCliStatusProvider — short git status for seat entry context."""

from __future__ import annotations

import subprocess


class GitCliStatusProvider:
    def __init__(self, root: str) -> None:
        self._root = root

    def short_status(self) -> str:
        try:
            out = subprocess.run(
                ["git", "status", "--short"],
                cwd=self._root,
                capture_output=True,
                text=True,
                check=True,
            )
            return out.stdout.strip()
        except Exception:
            return ""
