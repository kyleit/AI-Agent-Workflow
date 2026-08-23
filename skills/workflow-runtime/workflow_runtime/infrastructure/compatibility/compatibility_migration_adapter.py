# compatibility_migration_adapter.py
from __future__ import annotations

from typing import Any


class CompatibilityMigrationAdapter:
    """
    FEAT-093: Migration & Backward Compatibility Adapter
    Adapts legacy structures to newer schemas.
    """
    def convert_legacy_checkpoint(self, legacy_data: dict[str, Any]) -> dict[str, Any]:
        cp_id = legacy_data.get("checkpoint_id", 0)
        done_flag = bool(legacy_data.get("done"))
        return {
            "checkpoint": cp_id,
            "status": "completed" if done_flag else "active"
        }


__all__ = ["CompatibilityMigrationAdapter"]
