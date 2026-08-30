from __future__ import annotations

import os
import shutil
from typing import Any

from .common import get_project_root, to_posix_path
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
                        "details": f"Contains approximately {nested_count} tracked files."
                    })

        return modules

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
