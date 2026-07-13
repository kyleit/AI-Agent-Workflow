# skills/workflow-runtime/mcp/manager.py
import os
import sys
import json
import subprocess

# Ensure correct sys.path imports
current_dir = os.path.dirname(__file__)
adapters_dir = os.path.join(current_dir, "adapters")
if adapters_dir not in sys.path:
    sys.path.insert(0, adapters_dir)

from antigravity import AntigravityAdapter
from vscode import VSCodeAdapter
from cursor import CursorAdapter

class MCPManager:
    def __init__(self, workspace_root: str = "."):
        self.workspace_root = os.path.abspath(workspace_root)
        self.adapters = {
            "antigravity": AntigravityAdapter(self.workspace_root),
            "vscode": VSCodeAdapter(self.workspace_root),
            "cursor": CursorAdapter(self.workspace_root)
        }

    def _get_adapter(self, ide: str):
        if ide not in self.adapters:
            raise ValueError(f"Unsupported IDE: {ide}")
        return self.adapters[ide]

    def install(self, ide: str) -> dict:
        adapter = self._get_adapter(ide)
        success, msg = adapter.install()
        return {
            "status": "success" if success else "error",
            "summary": msg,
            "ide": ide
        }

    def uninstall(self, ide: str) -> dict:
        adapter = self._get_adapter(ide)
        success, msg = adapter.uninstall()
        return {
            "status": "success" if success else "error",
            "summary": msg,
            "ide": ide
        }

    def status(self, ide: str) -> dict:
        adapter = self._get_adapter(ide)
        res = adapter.status()
        
        # Check overall connectivity status
        workflow_runtime_connected = False
        workflow_script = os.path.join(self.workspace_root, "skills", "workflow-runtime", "scripts", "workflow_runtime.py")
        if os.path.exists(workflow_script):
            workflow_runtime_connected = True

        return {
            "ide": ide,
            "installed": "Installed" if res["installed"] else "Not Installed",
            "server_available": "Available" if res["server_available"] else "Unavailable",
            "workflow_runtime_connected": "Connected" if workflow_runtime_connected else "Disconnected",
            "config_path": res["config_path"]
        }

    def doctor(self, ide: str) -> dict:
        adapter = self._get_adapter(ide)
        config_path = adapter.get_config_path()
        
        diagnostics = []
        healthy = True

        # 1. IDE detection
        ide_detected = adapter.detect()
        diagnostics.append({
            "check": f"IDE '{ide}' Detected",
            "status": "PASS" if ide_detected else "FAIL",
            "detail": f"IDE profile directory check at: {os.path.dirname(config_path)}"
        })
        if not ide_detected:
            healthy = False

        # 2. Config existence & validity
        config_exists = os.path.exists(config_path)
        diagnostics.append({
            "check": "MCP configuration file exists",
            "status": "PASS" if config_exists else "WARNING",
            "detail": f"File path: {config_path}"
        })

        if config_exists:
            try:
                adapter.read_config()
                diagnostics.append({
                    "check": "MCP configuration is valid JSON",
                    "status": "PASS",
                    "detail": "Successfully loaded and validated JSON schema syntax."
                })
            except Exception as e:
                healthy = False
                diagnostics.append({
                    "check": "MCP configuration is valid JSON",
                    "status": "FAIL",
                    "detail": f"JSON syntax error: {str(e)}"
                })

        # 3. AIWF MCP server script executable
        server_script = os.path.join(self.workspace_root, "skills", "workflow-runtime", "mcp", "server.py")
        script_exists = os.path.exists(server_script)
        diagnostics.append({
            "check": "AIWF MCP server script exists",
            "status": "PASS" if script_exists else "FAIL",
            "detail": f"Script location: {server_script}"
        })
        if not script_exists:
            healthy = False

        # 4. workflow_runtime reachable
        workflow_script = os.path.join(self.workspace_root, "skills", "workflow-runtime", "scripts", "workflow_runtime.py")
        workflow_exists = os.path.exists(workflow_script)
        diagnostics.append({
            "check": "Workflow Runtime script reachable",
            "status": "PASS" if workflow_exists else "FAIL",
            "detail": f"Script location: {workflow_script}"
        })
        if not workflow_exists:
            healthy = False

        return {
            "status": "healthy" if healthy else "unhealthy",
            "ide": ide,
            "diagnostics": diagnostics
        }
