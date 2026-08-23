"""TopLevelRepoScanner — list visible top-level dirs to seed the roster."""

from __future__ import annotations

import os

from ..paths import PathResolver

IGNORE = {
    ".git", ".agents", "public_export", "node_modules", ".venv", "venv",
    "__pycache__", "dist", "build", ".idea", ".vscode", "scratch", "tmp",
    ".import_linter_cache", "screenshots", "test-results", "artifacts",
}


class TopLevelRepoScanner:
    def __init__(self, paths: PathResolver) -> None:
        self._p = paths

    def top_level_dirs(self) -> list[str]:
        root = self._p.root
        out = []
        for name in sorted(os.listdir(root)):
            if name in IGNORE or name.startswith("."):
                continue
            if os.path.isdir(os.path.join(root, name)):
                out.append(name)
        return out
