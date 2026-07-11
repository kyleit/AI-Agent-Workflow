import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "scripts"))
from workspace_context_isolation import ContextIsolationManager

def test_context_isolation(tmp_path):
    manager = ContextIsolationManager(base_session_dir=str(tmp_path))
    session_dir = manager.create_session_env("session_999")
    
    assert os.path.exists(session_dir)
    manager.cleanup_session_env("session_999")
    assert not os.path.exists(session_dir)
