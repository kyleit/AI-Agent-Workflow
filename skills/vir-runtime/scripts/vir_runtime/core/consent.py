# File path: vir_runtime/core/consent.py
import yaml
import os
from typing import Dict, Any

class ConsentDeniedError(Exception):
    pass

class SDLCCheckpointManager:
    def __init__(self, db_path: str = "vir_state.db"):
        self.db_path = db_path
        self.active_checkpoint = 1

    def verify_gate_block(self, checkpoint_id: str) -> bool:
        """Load active session checkpoint parameters and block proceed if VIR checks fail."""
        print(f"[SDLCCheckpointManager] Verifying gate block for checkpoint: {checkpoint_id}")
        # Return True if blocked, False if clear
        # Simulating that we block checkpoint 5 if regression fails
        if checkpoint_id == "CP-5":
            return True
        return False

    def advance_checkpoint(self) -> None:
        """Advance active session checkpoint index on success results."""
        self.active_checkpoint += 1
        print(f"[SDLCCheckpointManager] Advanced active checkpoint to: {self.active_checkpoint}")

class ConsentValidator:
    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = config_path
        self.consent_required = True
        self.privacy_level = "cloud"
        self._load_config()

    def _load_config(self) -> None:
        if os.path.exists(self.config_path):
            with open(self.config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f) or {}
            consent_conf = config.get("consent", {})
            self.consent_required = consent_conf.get("consent_required", True)
            self.privacy_level = consent_conf.get("privacy_level", "cloud")

    def check_consent_permission(self, provider: str) -> None:
        """Enforce explicit user privacy validation checks on cloud VLM providers."""
        print(f"[ConsentValidator] Auditing cloud privacy level permissions for provider: {provider}")
        # If cloud provider is requested but consent is required and not granted
        if self.consent_required and self.privacy_level == "cloud" and "openai" in provider.lower():
            # Raise exception if cloud providers are called without user consent override flags
            raise ConsentDeniedError(
                f"Consent denied: Using cloud provider '{provider}' requires explicit user privacy consent overrides."
            )
