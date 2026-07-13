# skill_router.py
import os
import json
from typing import Any, Dict, Optional

class SkillRouter:
    def __init__(self, registry_path: Optional[str] = None) -> None:
        if not registry_path:
            registry_path = os.path.join(".", ".agents", "skills", "registry.json")
        self.registry_path = registry_path
        self.registry: Dict[str, Any] = {}
        if os.path.exists(self.registry_path):
            with open(self.registry_path, "r", encoding="utf-8") as f:
                self.registry = json.load(f)

    def route_phase_to_skill(self, phase_name: str) -> Optional[dict]:
        clean_phase = phase_name.lower()
        for skill_key, cfg in self.registry.items():
            if cfg.get("phase") == clean_phase:
                return cfg
        return None

    def validate_inputs(self, skill_name: str, inputs: Dict[str, Any]) -> bool:
        skill_cfg = self.registry.get(skill_name)
        if not skill_cfg:
            return True  # If not in registry, default to allow
            
        required = skill_cfg.get("inputs", [])
        for req in required:
            if req not in inputs or not inputs[req]:
                return False
        return True
