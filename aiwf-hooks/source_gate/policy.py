"""Standalone hooks cannot depend on an installed workflow_runtime package."""
from __future__ import annotations

import os


def gates_enforced() -> bool:
    return os.environ.get("AIWF_GATE_MODE", "off").strip().lower() == "enforce"
