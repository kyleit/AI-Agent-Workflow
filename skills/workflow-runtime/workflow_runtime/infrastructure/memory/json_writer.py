# json_writer.py
from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any, cast

from .common import to_posix_path


def generate_file_map(project_files: list[str]) -> dict[str, str]:
    """Tạo bản đồ ánh xạ từ tệp nguồn sang memory target."""
    file_map: dict[str, str] = {}
    for file in project_files:
        target = "project-summary.md"
        if file.startswith("skills/workflow-runtime/") or file.startswith("runtime/"):
            target = "modules/workflow-runtime.md"
        elif file.startswith("extensions/visualizer/"):
            target = "modules/visualizer-extension.md"
        elif file.startswith("skills/"):
            parts = file.split("/")
            if len(parts) > 1:
                target = f"modules/{parts[1]}.md"
        elif file.startswith("docs/adr/"):
            target = "lessons/architectural-decisions.md"
        elif file.startswith("docs/issues/") or file.startswith("docs/quick/") or file.startswith("docs/brainstorming/"):
            target = "lessons/known-problems.md"

        file_map[file] = to_posix_path(target)
    return file_map


def write_file_map(dest_path: str, project_files: list[str]) -> None:
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    file_map = generate_file_map(project_files)
    with open(dest_path, "w", encoding="utf-8") as f:
        json.dump(file_map, f, indent=2)


def update_memory_state(dest_path: str, state_info: dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)

    existing: dict[str, Any] = {}
    if os.path.exists(dest_path):
        try:
            with open(dest_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    existing = cast(dict[str, Any], data)
        except Exception:
            pass

    merged: dict[str, Any] = {**existing, **state_info}
    merged["last_updated_at"] = datetime.now().astimezone().isoformat()

    with open(dest_path, "w", encoding="utf-8") as f:
        json.dump(merged, f, indent=2)


__all__ = [
    "generate_file_map",
    "write_file_map",
    "update_memory_state",
]
