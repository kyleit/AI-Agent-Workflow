"""
workflow_runtime/application/use_cases/process_registry.py

Registry adapter for active system processes and execution state.
"""
from __future__ import annotations

import json
import os
import tempfile
from typing import Any, Dict, cast

REGISTRY_PATH = os.path.abspath(os.path.join(
    os.path.dirname(__file__), "../../../.agents/state/executions.json"
))
LOGS_DIR = os.path.abspath(os.path.join(
    os.path.dirname(__file__), "../../../.agents/runtime/logs"
))


class ProcessRegistry:
    @staticmethod
    def read() -> Dict[str, Any]:
        if not os.path.exists(REGISTRY_PATH):
            return {}
        try:
            with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                return cast(Dict[str, Any], data) if isinstance(data, dict) else {}
        except Exception:
            return {}

    @staticmethod
    def write(data: Dict[str, Any]) -> None:
        dir_name = os.path.dirname(REGISTRY_PATH)
        os.makedirs(dir_name, exist_ok=True)
        fd, temp_path = tempfile.mkstemp(dir=dir_name, suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            os.replace(temp_path, REGISTRY_PATH)
        except Exception as e:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise e

    @staticmethod
    def update(execution_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        data = ProcessRegistry.read()
        if execution_id not in data:
            data[execution_id] = {}
        data[execution_id].update(updates)
        ProcessRegistry.write(data)
        return data[execution_id]


__all__ = ["ProcessRegistry", "REGISTRY_PATH"]
