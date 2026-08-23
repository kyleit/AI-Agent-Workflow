import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "scripts"))
from compatibility_migration_adapter import CompatibilityMigrationAdapter

def test_migration_adapter():
    adapter = CompatibilityMigrationAdapter()
    res = adapter.convert_legacy_checkpoint({"checkpoint_id": 3, "done": True})
    assert res["checkpoint"] == 3
    assert res["status"] == "completed"
