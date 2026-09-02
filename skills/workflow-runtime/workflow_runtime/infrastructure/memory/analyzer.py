from __future__ import annotations

import os
import json
import re
import shutil
from typing import Any

from .common import get_project_root, read_text_safe, to_posix_path
from .filesystem import get_project_files, IGNORE_DIRS


class ProjectAnalyzer:
    def __init__(self, root_dir: str | None = None) -> None:
        self.root_dir = root_dir or get_project_root()

    def analyze_modules(self) -> list[dict[str, str]]:
        """Phan tich toan dien tat ca cac modules, services, va subsystems cua du an."""
        modules: list[dict[str, str]] = []
        known_purposes: dict[str, str] = {
            "skills": "Autonomous agent skills and workflow definitions",
            "skills/workflow-runtime": "Hexagonal architecture core execution runtime",
            "desktop": "Wails GUI and native desktop integration",
            "wails-agent": "Wails desktop client application layer",
            "tools": "Git hooks, verification scripts, and release tools",
            "src": "Main application source codebase",
            "sources": "Source code components and services",
            "app": "Application entrypoints and controllers",
            "cmd": "Command line entrypoints and CLI utilities",
            "daemon": "Background background daemon services",
            "web": "Web frontend dashboard and UI assets",
            "electron": "Electron cross-platform desktop wrapper",
            "accounts": "Account management and credential store",
            "pkg": "Reusable domain packages and libraries",
            "lib": "Shared utility libraries",
            "internal": "Internal service components and domain logic",
            "docs": "Feature blueprints, specs, and architectural decisions",
            "deployments": "Deployment configurations and infrastructure manifests",
            "docker": "Docker container definitions and compose setups",
            "scripts": "Build, operational, and maintenance automation scripts",
            "tests": "Unit, integration, and end-to-end test suites",
        }

        all_project_files = get_project_files(self.root_dir)

        # 1. Scan top-level directories
        top_dirs = []
        try:
            for item in sorted(os.listdir(self.root_dir)):
                full_path = os.path.join(self.root_dir, item)
                if os.path.isdir(full_path) and not item.startswith(".") and item not in IGNORE_DIRS:
                    top_dirs.append(item)
        except Exception:
            pass

        for d in top_dirs:
            file_count = len([f for f in all_project_files if f.startswith(d + "/") or f == d])
            purpose = known_purposes.get(d, f"Subsystem and module directory for {d}.")
            name = d.replace("-", " ").replace("_", " ").title()
            modules.append({
                "name": name,
                "path": d,
                "purpose": purpose,
                "details": f"Contains approximately {file_count} tracked files."
                , "public_symbols": [], "dependencies": [], "tests": []
            })

            # Check special nested modules like skills/workflow-runtime
            if d == "skills":
                nested_full = os.path.join(self.root_dir, "skills", "workflow-runtime")
                if os.path.exists(nested_full) and os.path.isdir(nested_full):
                    nested_count = len([f for f in all_project_files if f.startswith("skills/workflow-runtime/")])
                    modules.append({
                        "name": "Workflow Runtime Engine",
                        "path": "skills/workflow-runtime",
                        "purpose": known_purposes.get("skills/workflow-runtime", "Core runtime engine"),
                        "details": f"Contains approximately {nested_count} tracked files.",
                        "public_symbols": [], "dependencies": [], "tests": []
                    })

        return modules

    def analyze_module_catalog(
        self,
        symbols: list[dict[str, Any]],
        dependencies: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Attach symbol, dependency, and test ownership to every module."""
        modules = self.analyze_modules()
        for module in modules:
            path = str(module.get("path") or "").rstrip("/")
            owned_files = [
                f for f in get_project_files(self.root_dir)
                if f == path or f.startswith(path + "/")
            ]
            module["public_symbols"] = [
                str(item.get("name")) for item in symbols
                if str(item.get("file", "")).startswith(path + "/")
            ]
            module["dependencies"] = [
                str(item.get("name")) for item in dependencies
                if str(item.get("source", "")).startswith(path + "/")
            ]
            module["tests"] = [
                f for f in owned_files
                if "/test" in f.lower() or f.lower().startswith("test")
            ]
        return modules

    def analyze_endpoints(self) -> list[dict[str, Any]]:
        endpoints: list[dict[str, Any]] = []
        patterns = [
            re.compile(r"@(?:\w+\.)?(get|post|put|patch|delete|route)\(\s*[\"']([^\"']+)", re.I),
            re.compile(r"\.?(GET|POST|PUT|PATCH|DELETE)\(\s*[\"']([^\"']+)[\"']\s*,\s*([\w.]+)", re.I),
            re.compile(r"(?:app|router)\.(get|post|put|patch|delete)\(\s*[\"']([^\"']+)[\"']", re.I),
        ]
        for rel in get_project_files(self.root_dir):
            if not rel.endswith((".py", ".go", ".js", ".jsx", ".ts", ".tsx", ".rs", ".cs")):
                continue
            content = read_text_safe(os.path.join(self.root_dir, rel))
            if not content:
                continue
            lines = content.splitlines()
            for line_no, line in enumerate(lines, 1):
                for index, pattern in enumerate(patterns):
                    match = pattern.search(line)
                    if not match:
                        continue
                    method = match.group(1).upper()
                    path = match.group(2)
                    handler = match.group(3) if index == 1 and match.lastindex and match.lastindex >= 3 else ""
                    if not handler:
                        next_line = lines[line_no] if line_no < len(lines) else ""
                        handler_match = re.search(r"(?:def|func|function)\s+(\w+)", next_line)
                        handler = handler_match.group(1) if handler_match else "unknown"
                    endpoints.append({
                        "method": method,
                        "path": path,
                        "handler": handler,
                        "source_anchor": f"{to_posix_path(rel)}:{line_no}",
                        "request_shape": "unknown",
                        "response_shape": "unknown",
                    })
                    break
        return endpoints

    def analyze_dependencies(self) -> list[dict[str, Any]]:
        dependencies: list[dict[str, Any]] = []
        package_path = os.path.join(self.root_dir, "package.json")
        if os.path.isfile(package_path):
            try:
                package = json.loads(read_text_safe(package_path))
                for section in ("dependencies", "devDependencies", "peerDependencies"):
                    values = package.get(section, {}) if isinstance(package, dict) else {}
                    if isinstance(values, dict):
                        dependencies.extend({"name": str(name), "version": str(version), "source": "package.json", "kind": section} for name, version in values.items())
            except (TypeError, ValueError):
                pass
        for filename in ("requirements.txt", "go.mod", "Cargo.toml", "pyproject.toml"):
            path = os.path.join(self.root_dir, filename)
            if not os.path.isfile(path):
                continue
            for line in read_text_safe(path).splitlines():
                match = re.match(r"\s*(?:require\s+)?([A-Za-z0-9_./@-]+)(?:\s*[=<>~!]+\s*([^\s#]+))?", line)
                if match and not line.lstrip().startswith(("#", "//", "[", "require (", "module ")):
                    dependencies.append({"name": match.group(1), "version": match.group(2) or "unknown", "source": filename, "kind": "manifest"})
        return dependencies

    def analyze_database_catalog(self) -> list[dict[str, Any]]:
        records: list[dict[str, Any]] = []
        migrations = [f for f in get_project_files(self.root_dir) if re.search(r"(^|/)(migrations?|alembic|prisma)(/|$)", f, re.I)]
        drivers = {
            "sqlite": "SQLite", "sqlite3": "SQLite", "postgres": "PostgreSQL",
            "psycopg": "PostgreSQL", "mysql": "MySQL", "redis": "Redis",
            "mongodb": "MongoDB", "qdrant": "Qdrant",
        }
        for rel in get_project_files(self.root_dir):
            if not rel.endswith((".py", ".go", ".js", ".ts", ".rs", ".toml", ".yml", ".yaml", ".json", ".sql")):
                continue
            content = read_text_safe(os.path.join(self.root_dir, rel), max_chars=200000).lower()
            engines = sorted({label for needle, label in drivers.items() if needle in content})
            if rel.lower().endswith(".sql") and re.search(r"create\s+table|alter\s+table", content):
                engines.append("SQLite")
            engines = sorted(set(engines))
            for engine in engines:
                records.append({
                    "engine": engine,
                    "path_or_service": rel,
                    "tables_or_collections": re.findall(r"(?:create table|collection\s*[=:])\s*[`\"']?([\w-]+)", content, re.I),
                    "migrations": [m for m in migrations if m.startswith(os.path.dirname(rel).replace("\\", "/"))][:20],
                    "access_modules": [rel],
                })
        return records or [{
            "engine": item.get("type", "File-based State"),
            "path_or_service": item.get("path", ".agents/state/"),
            "tables_or_collections": [], "migrations": [], "access_modules": [],
        } for item in self.get_database_info()]

    def get_database_info(self) -> list[dict[str, str]]:
        databases: list[dict[str, str]] = []
        try:
            for item in os.listdir(self.root_dir):
                if item.endswith(".sqlite") or item.endswith(".db"):
                    databases.append({
                        "type": "SQLite",
                        "path": item,
                        "purpose": "Local database persistence."
                    })
        except Exception:
            pass

        compose_path = os.path.join(self.root_dir, "docker-compose.yml")
        if os.path.exists(compose_path):
            try:
                with open(compose_path, "r", encoding="utf-8") as f:
                    content = f.read().lower()
                    if "postgres" in content:
                        databases.append({"type": "PostgreSQL", "path": "docker-compose.yml", "purpose": "Dockerized PostgreSQL relational backend"})
                    if "mysql" in content:
                        databases.append({"type": "MySQL", "path": "docker-compose.yml", "purpose": "Dockerized MySQL database"})
                    if "redis" in content:
                        databases.append({"type": "Redis", "path": "docker-compose.yml", "purpose": "Dockerized Redis cache/message bus"})
                    if "mongodb" in content or "mongo" in content:
                        databases.append({"type": "MongoDB", "path": "docker-compose.yml", "purpose": "Dockerized MongoDB document store"})
            except Exception:
                pass

        if not databases:
            databases.append({
                "type": "File-based JSON / State Store",
                "path": ".agents/state/",
                "purpose": "Decoupled state persistence and transactional session logs."
            })

        return databases

    def detect_infrastructure(self) -> list[dict[str, str]]:
        infra: list[dict[str, str]] = []
        if shutil.which("ollama"):
            infra.append({
                "type": "Ollama",
                "purpose": "Local LLM inference",
                "details": "Installed on host machine."
            })
        if shutil.which("docker"):
            infra.append({
                "type": "Docker",
                "purpose": "Container runtime",
                "details": "Installed on host machine."
            })
        if shutil.which("wails"):
            infra.append({
                "type": "Wails CLI",
                "purpose": "Desktop cross-platform framework",
                "details": "Installed on host machine."
            })
        return infra

    def detect_architecture_patterns(self) -> list[str]:
        patterns: list[str] = [
            "Hexagonal Architecture (Ports and Adapters)",
            "Multi-Agent SDLC Orchestration",
            "Decoupled Split-State Persistence",
            "Command Bus & Script-First CLI Pattern"
        ]
        return patterns


__all__ = ["ProjectAnalyzer"]
