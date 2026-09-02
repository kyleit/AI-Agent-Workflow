from __future__ import annotations

import os
import hashlib
from collections import Counter
from typing import Any, Optional, cast

from .common import get_project_root
from .filesystem import get_project_files

LANG_EXT_MAP: dict[str, str] = {
    ".py": "Python",
    ".js": "JavaScript",
    ".ts": "TypeScript",
    ".go": "Go",
    ".rs": "Rust",
    ".java": "Java",
    ".cpp": "C++",
    ".c": "C",
    ".cs": "C#",
    ".sh": "Shell",
    ".ps1": "PowerShell",
    ".html": "HTML",
    ".css": "CSS"
}

SOURCE_KIND_MAP: dict[str, str] = {
    ".py": "source", ".go": "source", ".rs": "source", ".java": "source",
    ".cs": "source", ".js": "source", ".jsx": "source", ".ts": "source",
    ".tsx": "source", ".cpp": "source", ".c": "source", ".h": "source",
    ".sh": "script", ".ps1": "script", ".bat": "script", ".cmd": "script",
    ".sql": "schema", ".md": "documentation", ".json": "configuration",
    ".toml": "configuration", ".yaml": "configuration", ".yml": "configuration",
}


class ProjectScanner:
    def __init__(self, root_dir: Optional[str] = None) -> None:
        self.root_dir = root_dir or get_project_root()
        self._files: Optional[list[str]] = None

    @property
    def files(self) -> list[str]:
        if self._files is None:
            self._files = get_project_files(self.root_dir)
        return self._files

    def detect_languages(self) -> list[str]:
        exts: list[str] = []
        for file in self.files:
            _, ext = os.path.splitext(file)
            if ext in LANG_EXT_MAP:
                exts.append(LANG_EXT_MAP[ext])

        if not exts:
            return ["Unknown"]

        counter = Counter(exts)
        sorted_langs: list[str] = [str(item[0]) for item in counter.most_common()]
        return sorted_langs

    def detect_frameworks(self, languages: list[str]) -> list[str]:
        _ = languages
        frameworks: list[str] = []

        package_json_path = os.path.join(self.root_dir, "package.json")
        if os.path.exists(package_json_path):
            frameworks.append("Node.js")
            try:
                with open(package_json_path, "r", encoding="utf-8") as f:
                    import json
                    raw_pkg = json.load(f)
                    pkg: dict[str, Any] = cast(dict[str, Any], raw_pkg) if isinstance(raw_pkg, dict) else {}
                    raw_deps = pkg.get("dependencies", {})
                    raw_dev = pkg.get("devDependencies", {})
                    deps: dict[str, Any] = {
                        **(cast(dict[str, Any], raw_deps) if isinstance(raw_deps, dict) else {}),
                        **(cast(dict[str, Any], raw_dev) if isinstance(raw_dev, dict) else {})
                    }
                    if "vscode" in deps or "@types/vscode" in deps or "vscode-test" in deps:
                        frameworks.append("VS Code Extension API")
                    if "react" in deps:
                        frameworks.append("React")
                    if "vue" in deps:
                        frameworks.append("Vue")
                    if "electron" in deps:
                        frameworks.append("Electron")
            except Exception:
                pass

        go_mod_path = os.path.join(self.root_dir, "go.mod")
        if os.path.exists(go_mod_path):
            frameworks.append("Go Modules")
            try:
                with open(go_mod_path, "r", encoding="utf-8") as f:
                    mod_text = f.read()
                    if "wails" in mod_text:
                        frameworks.append("Wails v2")
                    if "gin-gonic" in mod_text:
                        frameworks.append("Gin Web Framework")
            except Exception:
                pass

        pyproject_toml = os.path.join(self.root_dir, "pyproject.toml")
        requirements_txt = os.path.join(self.root_dir, "requirements.txt")
        if os.path.exists(pyproject_toml) or os.path.exists(requirements_txt):
            frameworks.append("Python / PyPI")

        return frameworks

    def detect_build_commands(self) -> list[dict[str, Any]]:
        commands: list[dict[str, Any]] = []
        makefile_path = os.path.join(self.root_dir, "Makefile")
        if os.path.exists(makefile_path):
            commands.append({"name": "Makefile Build", "command": "make"})

        go_mod_path = os.path.join(self.root_dir, "go.mod")
        if os.path.exists(go_mod_path):
            commands.append({"name": "Go Build", "command": "go build ./..."})
            commands.append({"name": "Go Test", "command": "go test -v ./..."})

        if os.path.exists(os.path.join(self.root_dir, "pyproject.toml")) or os.path.exists(os.path.join(self.root_dir, "pytest.ini")):
            commands.append({"name": "Pytest Suite", "command": "pytest"})

        package_json_path = os.path.join(self.root_dir, "package.json")
        if os.path.exists(package_json_path):
            try:
                with open(package_json_path, "r", encoding="utf-8") as f:
                    import json
                    raw_pkg = json.load(f)
                    if isinstance(raw_pkg, dict):
                        scripts = raw_pkg.get("scripts", {})
                        if isinstance(scripts, dict):
                            if "build" in scripts:
                                commands.append({"name": "NPM Build", "command": "npm run build"})
                            if "test" in scripts:
                                commands.append({"name": "NPM Test", "command": "npm test"})
            except Exception:
                pass

        return commands

    def source_catalog(self, revision: str = "WORKTREE") -> list[dict[str, Any]]:
        """Create a complete, compact source inventory without reading source into memory."""
        catalog: list[dict[str, Any]] = []
        for rel in self.files:
            full = os.path.join(self.root_dir, rel)
            try:
                raw = open(full, "rb").read()
                line_count = raw.count(b"\n") + (1 if raw and not raw.endswith(b"\n") else 0)
                ext = os.path.splitext(rel)[1].lower()
                catalog.append({
                    "path": rel,
                    "language": LANG_EXT_MAP.get(ext, "Unknown"),
                    "kind": SOURCE_KIND_MAP.get(ext, "asset"),
                    "sha256": hashlib.sha256(raw).hexdigest(),
                    "line_count": line_count,
                    "revision": revision,
                })
            except OSError:
                continue
        return catalog
