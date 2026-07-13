# skills/workflow-runtime/mcp/adapters/antigravity.py
import os
import sys

# Ensure adapters folder is in path
sys.path.insert(0, os.path.dirname(__file__))

from base_adapter import BaseIDEAdapter

class AntigravityAdapter(BaseIDEAdapter):
    def __init__(self, workspace_root: str = "."):
        super().__init__(workspace_root)
        self.ide_name = "antigravity"

    def get_config_path(self) -> str:
        home = os.path.expanduser("~")
        return os.path.abspath(os.path.join(home, ".gemini", "antigravity-ide", "mcp.json"))
