"""PathResolver — resolves repo-relative locations and guards against §22 leaks."""

from __future__ import annotations

import os
import posixpath
import subprocess

from ..domain.errors import DevTeamError, ErrorCode


class PathResolver:
    def __init__(self, root: str) -> None:
        self.root = os.path.abspath(root)

    @staticmethod
    def discover_root(start: str | None = None) -> str:
        try:
            out = subprocess.run(
                ["git", "rev-parse", "--show-toplevel"],
                cwd=start or os.getcwd(),
                capture_output=True,
                text=True,
                check=True,
            )
            top = out.stdout.strip()
            if top:
                return top
        except Exception:
            pass
        return start or os.getcwd()

    # --- directories ---
    def devteam_dir(self) -> str:
        return os.path.join(self.root, ".agents", "devteam")

    def mail_dir(self) -> str:
        return os.path.join(self.root, ".agents", "session-mail")

    def charters_dir(self) -> str:
        return os.path.join(self.devteam_dir(), "charters")

    def state_dir(self) -> str:
        return os.path.join(self.devteam_dir(), "state")

    # --- files ---
    def seats_json(self) -> str:
        return os.path.join(self.devteam_dir(), "seats.json")

    def board(self) -> str:
        return os.path.join(self.devteam_dir(), "BOARD.md")

    def locks_json(self) -> str:
        return os.path.join(self.devteam_dir(), "locks.json")

    def charter(self, slug: str) -> str:
        return os.path.join(self.charters_dir(), f"seat-{slug}.md")

    def seat_state(self, slug: str) -> str:
        return os.path.join(self.state_dir(), f"seat-{slug}.md")

    def inbox(self, slug: str) -> str:
        return os.path.join(self.mail_dir(), f"seat-{slug}.inbox.jsonl")

    def cursor(self, slug: str) -> str:
        return os.path.join(self.mail_dir(), f"seat-{slug}.inbox.cursor")

    def project_id(self) -> str:
        return os.path.basename(self.root.rstrip(os.sep)) or "project"

    def rel(self, p: str) -> str:
        """Return a POSIX repo-relative path, rejecting anything that escapes root."""
        r = posixpath.normpath(os.path.relpath(p, self.root).replace("\\", "/"))
        if r.startswith("..") or posixpath.isabs(r):
            raise DevTeamError(ErrorCode.ABSOLUTE_PATH, f"path escapes repo: {p!r}")
        return r
