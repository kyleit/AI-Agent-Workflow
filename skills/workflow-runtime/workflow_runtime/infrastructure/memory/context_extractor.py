from __future__ import annotations

import os
import re
import subprocess
from typing import Any

from .common import get_project_root, read_text_safe, to_posix_path
from .filesystem import IGNORE_DIRS, get_project_files


class ProjectContextExtractor:
    """Extracts high-signal codebase context, symbols, and documentation for AI cognitive synthesis."""

    def __init__(self, root_dir: str | None = None) -> None:
        self.root_dir = root_dir or get_project_root()

    def extract_readme_and_docs(self) -> dict[str, str]:
        docs: dict[str, str] = {}
        candidate_files = [
            "README.md", "readme.md", "SPEC.md", "ARCHITECTURE.md",
            "docs/README.md", "docs/architecture.md", "docs/overview.md"
        ]
        for rel in candidate_files:
            full = os.path.join(self.root_dir, rel)
            if os.path.exists(full) and os.path.isfile(full):
                text = read_text_safe(full, max_chars=5000)
                if text:
                    docs[to_posix_path(rel)] = text
        return docs

    def extract_manifests(self) -> dict[str, str]:
        manifests: dict[str, str] = {}
        manifest_files = [
            "package.json", "go.mod", "pyproject.toml", "requirements.txt",
            "Cargo.toml", "pom.xml", "docker-compose.yml", "Makefile",
            "wails.json", "tsconfig.json"
        ]
        for rel in manifest_files:
            full = os.path.join(self.root_dir, rel)
            if os.path.exists(full) and os.path.isfile(full):
                text = read_text_safe(full, max_chars=3000)
                if text:
                    manifests[to_posix_path(rel)] = text
        return manifests

    def extract_entrypoint_snippets(self) -> dict[str, str]:
        snippets: dict[str, str] = {}
        files = get_project_files(self.root_dir)
        entry_patterns = [
            "main.go", "server.go", "app.go", "app.py", "main.py",
            "index.ts", "index.js", "main.rs", "app.ts", "server.ts",
            "main.cpp", "Program.cs"
        ]
        found = 0
        for f in files:
            basename = os.path.basename(f)
            if basename in entry_patterns and found < 8:
                full = os.path.join(self.root_dir, f)
                text = read_text_safe(full, max_chars=2500)
                if text:
                    snippets[f] = text
                    found += 1
        return snippets

    def extract_code_symbols(self) -> list[dict[str, str]]:
        symbols: list[dict[str, str]] = []
        files = get_project_files(self.root_dir)
        target_files = [f for f in files if f.endswith((".py", ".go", ".ts", ".js", ".rs", ".cs"))][:40]

        for rel in target_files:
            full = os.path.join(self.root_dir, rel)
            content = read_text_safe(full, max_chars=4000)
            if not content:
                continue
            for match in re.finditer(r"type\s+([A-Za-z0-9_]+)\s+(struct|interface)", content):
                symbols.append({"file": rel, "name": match.group(1), "kind": match.group(2)})
            for match in re.finditer(r"class\s+([A-Za-z0-9_]+)(?:\([^)]*\))?:", content):
                symbols.append({"file": rel, "name": match.group(1), "kind": "class"})
            for match in re.finditer(r"(class|interface|type)\s+([A-Za-z0-9_]+)", content):
                symbols.append({"file": rel, "name": match.group(2), "kind": match.group(1)})
        return symbols[:30]

    def extract_recent_commits(self, limit: int = 5) -> list[str]:
        try:
            res = subprocess.run(
                ["git", "log", f"-n{limit}", "--oneline"],
                cwd=self.root_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                encoding="utf-8", errors="replace"
            )
            if res.returncode == 0:
                return [line.strip() for line in res.stdout.splitlines() if line.strip()]
        except Exception:
            pass
        return []

    def get_full_context_payload(self) -> dict[str, Any]:
        return {
            "project_id": os.path.basename(os.path.abspath(self.root_dir)),
            "readme_docs": self.extract_readme_and_docs(),
            "manifests": self.extract_manifests(),
            "entrypoints": self.extract_entrypoint_snippets(),
            "symbols": self.extract_code_symbols(),
            "recent_commits": self.extract_recent_commits(),
        }


__all__ = ["ProjectContextExtractor"]
