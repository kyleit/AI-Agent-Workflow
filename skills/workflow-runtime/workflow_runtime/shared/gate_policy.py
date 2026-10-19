"""AIWF workflow enforcement is opt-in; disabled does not mean approved."""
from __future__ import annotations

import os


def gates_enforced() -> bool:
    """Keep historical enforcement available only when explicitly requested."""
    return os.environ.get("AIWF_GATE_MODE", "off").strip().lower() == "enforce"
