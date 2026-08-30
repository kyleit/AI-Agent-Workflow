from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class Capability(StrEnum):
    READ = "read"
    LOCAL_WRITE = "local_write"
    COMPILE = "compile"
    LINT = "lint"
    LOCAL_TEST = "local_test"
    NETWORK = "network"
    DESTRUCTIVE = "destructive"
    RELEASE = "release"
    PRODUCTION = "production"


@dataclass(frozen=True)
class CapabilityDecision:
    allowed: bool
    requires_approval: bool
    reason: str


SAFE_AUTONOMOUS = {
    Capability.READ,
    Capability.COMPILE,
    Capability.LINT,
    Capability.LOCAL_TEST,
}
RISKY = {
    Capability.NETWORK,
    Capability.DESTRUCTIVE,
    Capability.RELEASE,
    Capability.PRODUCTION,
}


def decide_capability(
    mode: str,
    capability: Capability,
    blueprint_approved: bool,
) -> CapabilityDecision:
    normalized_mode = mode.strip().lower()
    if capability in RISKY:
        return CapabilityDecision(False, True, "explicit_risky_capability_approval")
    if capability in SAFE_AUTONOMOUS:
        return CapabilityDecision(True, False, "autonomous_local_safe")
    if capability is Capability.LOCAL_WRITE:
        if not blueprint_approved:
            return CapabilityDecision(False, True, "approved_blueprint_required")
        if normalized_mode == "autonomous":
            return CapabilityDecision(True, False, "approved_blueprint_local_write")
        return CapabilityDecision(False, True, "legacy_state_change_prompt")
    return CapabilityDecision(False, True, "unknown_capability_requires_approval")


__all__ = ["Capability", "CapabilityDecision", "decide_capability"]
