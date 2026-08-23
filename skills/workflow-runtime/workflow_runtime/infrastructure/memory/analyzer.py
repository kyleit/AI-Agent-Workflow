from __future__ import annotations

import os
import shutil

from .common import get_project_root


class ProjectAnalyzer:
    def __init__(self, root_dir: str | None = None) -> None:
        self.root_dir = root_dir or get_project_root()

    def analyze_modules(self) -> list[dict[str, str]]:
        """Tự động phát hiện các module/cấu phần cốt lõi của dự án một cách tổng quát."""
        modules: list[dict[str, str]] = []

        common_src_dirs = ["src", "app", "cmd", "pkg", "lib", "core", "packages"]

        for d in common_src_dirs:
            d_path = os.path.join(self.root_dir, d)
            if os.path.exists(d_path) and os.path.isdir(d_path):
                for sub in os.listdir(d_path):
                    sub_path = os.path.join(d_path, sub)
                    if os.path.isdir(sub_path) and not sub.startswith((".", "__")):
                        modules.append({
                            "name": sub.title(),
                            "path": f"{d}/{sub}",
                            "purpose": f"Source module in {d}/{sub}.",
                            "details": "Auto-detected source directory."
                        })

                if not any(os.path.isdir(os.path.join(d_path, sub)) for sub in os.listdir(d_path) if not sub.startswith(".")):
                    modules.append({
                        "name": d.title(),
                        "path": d,
                        "purpose": "Main source directory.",
                        "details": "Auto-detected top-level source directory."
                    })

        if not modules:
            for item in os.listdir(self.root_dir):
                full_path = os.path.join(self.root_dir, item)
                if os.path.isdir(full_path) and not item.startswith(".") and item not in ["node_modules", "venv", "env", "__pycache__", "build", "dist"]:
                    modules.append({
                        "name": item.title(),
                        "path": item,
                        "purpose": f"Top-level directory {item}.",
                        "details": "Auto-detected directory."
                    })

        return modules

    def get_database_info(self) -> list[dict[str, str]]:
        databases: list[dict[str, str]] = []
        for item in os.listdir(self.root_dir):
            if item.endswith(".sqlite") or item.endswith(".db"):
                databases.append({
                    "type": "SQLite",
                    "path": item,
                    "purpose": "Local database file detected."
                })

        compose_path = os.path.join(self.root_dir, "docker-compose.yml")
        if os.path.exists(compose_path):
            try:
                with open(compose_path, "r", encoding="utf-8") as f:
                    content = f.read().lower()
                    if "postgres" in content:
                        databases.append({"type": "PostgreSQL", "path": "docker-compose", "purpose": "Dockerized PostgreSQL"})
                    if "mysql" in content:
                        databases.append({"type": "MySQL", "path": "docker-compose", "purpose": "Dockerized MySQL"})
                    if "redis" in content:
                        databases.append({"type": "Redis", "path": "docker-compose", "purpose": "Dockerized Redis"})
                    if "mongodb" in content or "mongo" in content:
                        databases.append({"type": "MongoDB", "path": "docker-compose", "purpose": "Dockerized MongoDB"})
            except Exception:
                pass

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
                "purpose": "Containerization",
                "details": "Installed on host machine."
            })
        return infra


__all__ = ["ProjectAnalyzer"]
