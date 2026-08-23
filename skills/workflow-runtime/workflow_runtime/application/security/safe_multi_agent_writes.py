"""Backward-compatible re-exports."""
from __future__ import annotations

from workflow_runtime.domain.security.safe_writes_io import (
    calculate_file_hash, calculate_hash, ensure_state_dir, read_json_safe,
    write_json_atomic)

from .safe_writes_controllers import (AdaptiveTeamPlanner, AtomicWriter,
                                      ConcurrencyController, LeaseManager,
                                      PatchIntegrationQueue)

__all__ = [
    "ensure_state_dir",
    "read_json_safe",
    "write_json_atomic",
    "calculate_hash",
    "calculate_file_hash",
    "AdaptiveTeamPlanner",
    "LeaseManager",
    "ConcurrencyController",
    "AtomicWriter",
    "PatchIntegrationQueue",
]
