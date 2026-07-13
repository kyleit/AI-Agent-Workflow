# skills/workflow-runtime/mcp/adapters/base_adapter.py
import os
import json
import shutil
from datetime import datetime

class BaseIDEAdapter:
    def __init__(self, workspace_root: str = "."):
        self.workspace_root = os.path.abspath(workspace_root)
        self.ide_name = "base"

    def get_config_path(self) -> str:
        raise NotImplementedError

    def detect(self) -> bool:
        """
        Detects if the IDE environment is available.
        By default, check if the config parent folder exists.
        """
        path = self.get_config_path()
        return os.path.exists(os.path.dirname(path))

    def backup_config(self) -> str:
        """
        Backs up the existing configuration file.
        Returns the backup file path.
        """
        config_path = self.get_config_path()
        if not os.path.exists(config_path):
            return ""

        backup_dir = os.path.join(self.workspace_root, ".agents", "state", "mcp", "backup")
        os.makedirs(backup_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(backup_dir, f"{self.ide_name}_{timestamp}.json")
        
        shutil.copy2(config_path, backup_path)
        return backup_path

    def read_config(self) -> dict:
        config_path = self.get_config_path()
        if not os.path.exists(config_path):
            return {}
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def write_config(self, config: dict) -> None:
        config_path = self.get_config_path()
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        
        # Validate JSON before writing
        temp_str = json.dumps(config, indent=2, ensure_ascii=False)
        json.loads(temp_str) # test parser

        with open(config_path, "w", encoding="utf-8") as f:
            f.write(temp_str)

    def get_server_mcp_entry(self) -> dict:
        """
        Returns the standard aiwf mcp server block configuration.
        """
        # Absolute path to python3 executable
        python_exec = sys.executable or "python3"
        server_script = os.path.abspath(os.path.join(self.workspace_root, "skills", "workflow-runtime", "mcp", "server.py"))
        
        return {
            "command": python_exec,
            "args": [
                server_script
            ],
            "env": {
                "AIWF_EXECUTION_MODE": "workflow"
            }
        }

    def install(self) -> tuple[bool, str]:
        try:
            if not self.detect():
                return False, f"IDE '{self.ide_name}' installation not detected (parent config directory missing)."

            # 1. Backup first
            backup_path = self.backup_config()
            
            # 2. Read existing
            config = self.read_config()
            
            if "mcpServers" not in config:
                config["mcpServers"] = {}
                
            # 3. Safely merge configuration
            config["mcpServers"]["aiwf"] = self.get_server_mcp_entry()
            
            # 4. Save config
            self.write_config(config)
            
            msg = f"AIWF MCP installed successfully for {self.ide_name}."
            if backup_path:
                msg += f" (Backup created at {os.path.basename(backup_path)})"
            return True, msg
        except Exception as e:
            return False, str(e)

    def uninstall(self) -> tuple[bool, str]:
        try:
            config_path = self.get_config_path()
            if not os.path.exists(config_path):
                return True, f"AIWF MCP already uninstalled for {self.ide_name} (config file doesn't exist)."

            self.backup_config()
            config = self.read_config()
            
            if "mcpServers" in config and "aiwf" in config["mcpServers"]:
                del config["mcpServers"]["aiwf"]
                self.write_config(config)
                return True, f"AIWF MCP entry removed successfully for {self.ide_name}."
            
            return True, f"AIWF MCP entry not found in config for {self.ide_name} (nothing to remove)."
        except Exception as e:
            return False, str(e)

    def status(self) -> dict:
        config_path = self.get_config_path()
        installed = False
        server_available = False
        
        if os.path.exists(config_path):
            config = self.read_config()
            if "mcpServers" in config and "aiwf" in config["mcpServers"]:
                installed = True
                
                # Check if script file exists
                entry = config["mcpServers"]["aiwf"]
                args = entry.get("args", [])
                if args and os.path.exists(args[0]):
                    server_available = True

        return {
            "ide": self.ide_name,
            "installed": installed,
            "server_available": server_available,
            "config_path": config_path
        }
import sys
