import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "scripts"))
from sandbox_container_execution_provider import SandboxContainerProvider

def test_sandbox_provider():
    provider = SandboxContainerProvider()
    res = provider.run_container("box_1", "python -c 'print(1)'")
    assert res == "Command executed inside sandbox"
    provider.stop_container("box_1")
    assert provider.containers["box_1"] == "STOPPED"
