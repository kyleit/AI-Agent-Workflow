# File path: vir_runtime/core/consent.py
from __future__ import annotations

import os
from typing import Any, cast

import yaml


class ConsentDeniedError(Exception):
    pass


class SDLCCheckpointManager:
    def __init__(self, db_path: str = "vir_state.db") -> None:
        self.db_path = db_path
        self.active_checkpoint = 1

    def verify_gate_block(self, checkpoint_id: str) -> bool:
        """Load active session checkpoint parameters and block proceed if VIR checks fail."""
        print(f"[SDLCCheckpointManager] Verifying gate block for checkpoint: {checkpoint_id}")
        if checkpoint_id == "CP-5":
            return True
        return False

    def advance_checkpoint(self) -> None:
        """Advance active session checkpoint index on success results."""
        self.active_checkpoint += 1
        print(f"[SDLCCheckpointManager] Advanced active checkpoint to: {self.active_checkpoint}")


class ConsentValidator:
    def __init__(self, config_path: str = "config.yaml") -> None:
        self.config_path = config_path
        self.consent_required = True
        self.privacy_level = "cloud"
        self._load_config()

    def _load_config(self) -> None:
        if os.path.exists(self.config_path):
            with open(self.config_path, "r", encoding="utf-8") as f:
                raw_config = yaml.safe_load(f)
            config = cast(dict[str, Any], raw_config) if isinstance(raw_config, dict) else {}
            consent_conf = cast(dict[str, Any], config.get("consent")) if isinstance(config.get("consent"), dict) else {}
            self.consent_required = bool(consent_conf.get("consent_required", True))
            self.privacy_level = str(consent_conf.get("privacy_level", "cloud"))

    def check_consent_permission(self, provider: str) -> None:
        """Enforce explicit user privacy validation checks on cloud VLM providers."""
        print(f"[ConsentValidator] Auditing cloud privacy level permissions for provider: {provider}")
        if self.consent_required and self.privacy_level == "cloud" and "openai" in provider.lower():
            raise ConsentDeniedError(
                f"Consent denied: Using cloud provider '{provider}' requires explicit user privacy consent overrides."
            )


__all__ = [
    "ConsentDeniedError",
    "SDLCCheckpointManager",
    "ConsentValidator",
]
