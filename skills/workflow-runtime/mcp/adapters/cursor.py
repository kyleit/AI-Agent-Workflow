# skills/workflow-runtime/mcp/adapters/cursor.py
import os
import sys

# Ensure adapters folder is in path
sys.path.insert(0, os.path.dirname(__file__))

from base_adapter import BaseIDEAdapter

class CursorAdapter(BaseIDEAdapter):
    def __init__(self, workspace_root: str = "."):
        super().__init__(workspace_root)
        self.ide_name = "cursor"

    def get_config_path(self) -> str:
        import platform
        home = os.path.expanduser("~")
        sys_platform = platform.system()
        
        if sys_platform == "Windows":
            appdata = os.environ.get("APPDATA") or os.path.join(home, "AppData", "Roaming")
            return os.path.abspath(os.path.join(
                appdata, "Cursor", "User", 
                "globalStorage", "saoudrizwan.claude-dev", "settings", "cline_mcp_settings.json"
            ))
        elif sys_platform == "Darwin":
            return os.path.abspath(os.path.join(
                home, "Library", "Application Support", "Cursor", "User", 
                "globalStorage", "saoudrizwan.claude-dev", "settings", "cline_mcp_settings.json"
            ))
        else:
            return os.path.abspath(os.path.join(
                home, ".config", "Cursor", "User", 
                "globalStorage", "saoudrizwan.claude-dev", "settings", "cline_mcp_settings.json"
            ))
