import sys
import os
import pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "scripts"))
from remote_execution_federation_platform import FederationPlatform

def test_federation_platform():
    platform = FederationPlatform()
    platform.register_node("10.0.0.1")
    res = platform.execute_remote("10.0.0.1", "run_test")
    assert "routed to node" in res
    with pytest.raises(ConnectionError):
        platform.execute_remote("10.0.0.2", "run_test")
