# compatibility_migration_adapter.py
class CompatibilityMigrationAdapter:
    """
    FEAT-093: Migration & Backward Compatibility Adapter
    Adapts legacy structures to newer schemas.
    """
    def convert_legacy_checkpoint(self, legacy_data: dict) -> dict:
        return {
            "checkpoint": legacy_data.get("checkpoint_id", 0),
            "status": "completed" if legacy_data.get("done") else "active"
        }
