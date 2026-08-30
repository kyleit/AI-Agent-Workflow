# json_writer.py
from __future__ import annotations

import os
from datetime import datetime
from typing import Any, cast

from .common import read_json_safe, to_posix_path, write_json_safe


def generate_file_map(project_files: list[str]) -> dict[str, str]:
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
    file_map = generate_file_map(project_files)
    write_json_safe(dest_path, file_map)


def update_memory_state(dest_path: str, state_info: dict[str, Any]) -> None:
    existing: dict[str, Any] = read_json_safe(dest_path, default={})
    merged: dict[str, Any] = {**existing, **state_info}
    merged["last_updated_at"] = datetime.now().astimezone().isoformat()
    write_json_safe(dest_path, merged)


__all__ = ["generate_file_map", "write_file_map", "update_memory_state"]
