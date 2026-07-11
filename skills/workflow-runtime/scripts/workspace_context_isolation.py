# workspace_context_isolation.py
import os
import shutil

class ContextIsolationManager:
    """
    FEAT-092: Multi-Tenant Workspace & Context Isolation
    Isolates dynamic parallel sessions under unique directory namespaces.
    """
    def __init__(self, base_session_dir: str = ".agents/state/sessions"):
        self.base_session_dir = base_session_dir

    def create_session_env(self, session_id: str) -> str:
        session_path = os.path.join(self.base_session_dir, session_id)
        os.makedirs(session_path, exist_ok=True)
        return os.path.abspath(session_path)

    def cleanup_session_env(self, session_id: str) -> None:
        session_path = os.path.join(self.base_session_dir, session_id)
        if os.path.exists(session_path):
            shutil.rmtree(session_path)
