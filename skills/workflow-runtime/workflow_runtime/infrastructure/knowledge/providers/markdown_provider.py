from __future__ import annotations

import glob
import os
from typing import Any, cast

from workflow_runtime.domain.knowledge.interfaces import IKnowledgeProvider


def _sort_key(item: dict[str, Any]) -> float:
    return float(cast(float, item.get("score", 0.0)))


class MarkdownProvider(IKnowledgeProvider):
    def __init__(self, workspace_root: str = ".") -> None:
        self.workspace_root = os.path.abspath(workspace_root)

    def _resolve_path(self, path: str) -> str:
        full_path = os.path.abspath(os.path.join(self.workspace_root, path))
        if not full_path.startswith(self.workspace_root):
            raise PermissionError("Access denied: path is outside workspace sandbox.")
        return full_path

    def search(self, query: str, limit: int = 5) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        if not query:
            return results

        search_pattern = os.path.join(self.workspace_root, "docs", "**", "*.md")
        files = glob.glob(search_pattern, recursive=True)

        for f in files:
            try:
                with open(f, "r", encoding="utf-8") as file:
                    content = file.read()

                rel_path = os.path.relpath(f, self.workspace_root)
                if query.lower() in content.lower() or query.lower() in rel_path.lower():
                    snippet = ""
                    idx = content.lower().find(query.lower())
                    if idx != -1:
                        start = max(0, idx - 60)
                        end = min(len(content), idx + 60)
                        snippet = content[start:end].replace("\n", " ")
                    else:
                        snippet = content[:120].replace("\n", " ")

                    results.append({
                        "path": rel_path,
                        "snippet": snippet,
                        "score": 1.0 if query.lower() in rel_path.lower() else 0.5
                    })
            except Exception:
                continue

        results.sort(key=_sort_key, reverse=True)
        return results[:limit]

    def read(self, path: str) -> str:
        resolved = self._resolve_path(path)
        if not os.path.exists(resolved):
            raise FileNotFoundError(f"File not found: {path}")
        with open(resolved, "r", encoding="utf-8") as f:
            return f.read()

    def write(self, path: str, content: str) -> bool:
        resolved = self._resolve_path(path)
        os.makedirs(os.path.dirname(resolved), exist_ok=True)
        with open(resolved, "w", encoding="utf-8") as f:
            f.write(content)
        return True

    def save(self, path: str, content: str) -> bool:
        return self.write(path, content)

    def is_available(self) -> bool:
        return True


__all__ = ["MarkdownProvider"]
