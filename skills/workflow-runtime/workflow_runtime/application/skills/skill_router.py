# skill_router.py
from __future__ import annotations

import json
import os
from typing import Any, cast


class SkillRouter:
    def __init__(self, registry_path: str | None = None) -> None:
        if not registry_path:
            registry_path = os.path.join(".", ".agents", "skills", "registry.json")
        self.registry_path = registry_path
        self.registry: dict[str, Any] = {}
        if os.path.exists(self.registry_path):
            try:
                with open(self.registry_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        self.registry = cast(dict[str, Any], data)
            except Exception:
                pass

    def route_phase_to_skill(self, phase_name: str) -> dict[str, Any] | None:
        clean_phase = phase_name.lower()
        for _skill_key, cfg in self.registry.items():
            if isinstance(cfg, dict):
                cfg_dict = cast(dict[str, Any], cfg)
                if cfg_dict.get("phase") == clean_phase:
                    return cfg_dict
        return None

    def validate_inputs(self, skill_name: str, inputs: dict[str, Any]) -> bool:
        skill_cfg = self.registry.get(skill_name)
        if not isinstance(skill_cfg, dict):
            return True

        cfg_dict = cast(dict[str, Any], skill_cfg)
        required: list[Any] = cast(list[Any], cfg_dict.get("inputs")) if isinstance(cfg_dict.get("inputs"), list) else []
        for req in required:
            req_str = str(req)
            if req_str not in inputs or not inputs[req_str]:
                return False
        return True


__all__ = ["SkillRouter"]
