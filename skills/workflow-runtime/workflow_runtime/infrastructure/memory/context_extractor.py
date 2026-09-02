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
        target_files = [f for f in files if f.endswith((".py", ".go", ".ts", ".tsx", ".js", ".jsx", ".rs", ".cs", ".java"))]

        for rel in target_files:
            full = os.path.join(self.root_dir, rel)
            content = read_text_safe(full, max_chars=1_000_000)
            if not content:
                continue
            patterns = [
                (r"^\s*(?:async\s+)?def\s+([A-Za-z_][\w]*)", "function"),
                (r"^\s*class\s+([A-Za-z_][\w]*)", "class"),
                (r"^\s*func\s+(?:\([^)]*\)\s*)?([A-Za-z_][\w]*)", "function"),
                (r"^\s*type\s+([A-Za-z_][\w]*)\s+(struct|interface)", "type"),
                (r"^\s*(?:export\s+)?(?:abstract\s+)?class\s+([A-Za-z_][\w]*)", "class"),
                (r"^\s*(?:export\s+)?interface\s+([A-Za-z_][\w]*)", "interface"),
                (r"^\s*(?:export\s+)?type\s+([A-Za-z_][\w]*)", "type"),
                (r"^\s*(?:export\s+)?(?:async\s+)?function\s+([A-Za-z_][\w]*)", "function"),
                (r"^\s*(?:pub\s+)?fn\s+([A-Za-z_][\w]*)", "function"),
                (r"^\s*public\s+(?:static\s+)?(?:[\w<>\[\]]+\s+)+([A-Za-z_][\w]*)\s*\(", "method"),
            ]
            for line_no, line in enumerate(content.splitlines(), 1):
                for expression, kind in patterns:
                    match = re.search(expression, line)
                    if match:
                        symbols.append({
                            "file": to_posix_path(rel),
                            "name": match.group(1),
                            "kind": kind,
                            "source_anchor": f"{to_posix_path(rel)}:{line_no}",
                        })
                        break
        return symbols

    def extract_entrypoint_records(self) -> list[dict[str, str]]:
        records: list[dict[str, str]] = []
        known_names = {"main.py", "main.go", "main.rs", "main.ts", "main.js", "app.py", "server.py", "server.ts", "program.cs", "index.js", "index.ts"}
        for rel in get_project_files(self.root_dir):
            basename = os.path.basename(rel).lower()
            if basename not in known_names and not rel.startswith(("cmd/", "scripts/", "bin/")):
                continue
            content = read_text_safe(os.path.join(self.root_dir, rel), max_chars=200000)
            if not content:
                continue
            protocol = "CLI"
            if re.search(r"(?:fastapi|flask|gin|echo|express|router|http\.server|listen\s*\()", content, re.I):
                protocol = "HTTP"
            elif re.search(r"grpc|rpc", content, re.I):
                protocol = "RPC"
            symbol = "main"
            match = re.search(r"(?:def|func|function|fn)\s+(\w+)", content)
            if match:
                symbol = match.group(1)
            records.append({
                "path": to_posix_path(rel),
                "symbol": symbol,
                "protocol": protocol,
                "command": f"{basename} entrypoint",
                "start_condition": "process start",
                "source_anchor": f"{to_posix_path(rel)}:{next((i for i, line in enumerate(content.splitlines(), 1) if re.search(r'(def|func|function|fn)\s+\w+', line)), 1)}",
            })
        return records

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
            "entrypoint_records": self.extract_entrypoint_records(),
            "symbols": self.extract_code_symbols(),
            "recent_commits": self.extract_recent_commits(),
        }


__all__ = ["ProjectContextExtractor"]
