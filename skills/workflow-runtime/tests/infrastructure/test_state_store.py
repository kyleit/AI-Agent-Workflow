import pytest
import json
import os
from workflow_runtime.infrastructure.persistence.state_store import StateStoreAdapter

def test_state_store_atomic_write(tmp_path):
    adapter = StateStoreAdapter(state_root=str(tmp_path))
    
    # Write initial state
    adapter.write_state("test_key", {"value": 123})
    
    # Read state
    content = adapter.read_state("test_key")
    assert content == {"value": 123}
    
    # Verify file exists
    assert (tmp_path / "workflow.json").exists()
