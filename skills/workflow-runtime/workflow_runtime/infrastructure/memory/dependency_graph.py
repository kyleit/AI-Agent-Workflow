# dependency_graph.py
from __future__ import annotations

import os
from typing import Any, cast

from .common import get_project_root
from .parser import CodeParser


class DependencyGraph:
    def __init__(self, root_dir: str | None = None) -> None:
        self.root_dir = root_dir or get_project_root()
        self.graph: dict[str, list[str]] = {}

    def build_graph(self, files: list[str]) -> dict[str, list[str]]:
        """Xây dựng quan hệ import chéo giữa các tệp tin trong dự án."""
        for file in files:
            full_path = os.path.join(self.root_dir, file)
            if not os.path.exists(full_path):
                continue

            parsed = CodeParser.parse_file(full_path)
            raw_imports = parsed.get("imports", [])
            imports = cast(list[Any], raw_imports) if isinstance(raw_imports, list) else []

            resolved_imports: list[str] = []
            for imp_raw in imports:
                imp = str(imp_raw)
                if imp.startswith("."):
                    dir_path = os.path.dirname(file)
                    resolved = os.path.normpath(os.path.join(dir_path, imp))
                    resolved_imports.append(resolved.replace("\\", "/"))
                else:
                    resolved_imports.append(imp)

            self.graph[file] = resolved_imports
        return self.graph


__all__ = ["DependencyGraph"]
