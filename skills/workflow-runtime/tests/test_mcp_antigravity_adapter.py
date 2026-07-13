# skills/workflow-runtime/tests/test_mcp_antigravity_adapter.py
import os
import sys
import json
import pytest
from unittest.mock import patch

# Include script and mcp path
mcp_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "mcp"))
if mcp_dir not in sys.path:
    sys.path.insert(0, mcp_dir)
scripts_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts"))
if scripts_dir not in sys.path:
    sys.path.insert(0, scripts_dir)

from manager import MCPManager

@pytest.fixture
def temp_workspace(tmp_path):
    ws = str(tmp_path)
    os.makedirs(os.path.join(ws, ".agents"), exist_ok=True)
    os.makedirs(os.path.join(ws, "skills", "workflow-runtime", "mcp"), exist_ok=True)
    
    with open(os.path.join(ws, "skills", "workflow-runtime", "mcp", "server.py"), "w") as f:
        f.write("# mock server script")
        
    return ws

def test_antigravity_adapter_lifecycle(temp_workspace):
    manager = MCPManager(temp_workspace)
    adapter = manager.adapters["antigravity"]
    
    mock_config_file = os.path.join(temp_workspace, "mock_antigravity_config.json")
    
    with patch.object(adapter, "get_config_path", return_value=mock_config_file):
        # 1. Initially config doesn't exist
        assert not os.path.exists(mock_config_file)
        
        # 2. Write initial custom config representing pre-existing user settings
        initial_config = {
            "mcpServers": {
                "custom_server": {
                    "command": "node",
                    "args": ["some_tool.js"]
                }
            }
        }
        os.makedirs(os.path.dirname(mock_config_file), exist_ok=True)
        with open(mock_config_file, "w") as f:
            json.dump(initial_config, f, indent=2)
            
        # 3. Install AIWF MCP
        install_res = manager.install("antigravity")
        assert install_res["status"] == "success"
        
        # 4. Verify merge strategy and backup creation
        assert os.path.exists(mock_config_file)
        with open(mock_config_file, "r") as f:
            config = json.load(f)
            
        # custom_server MUST be preserved
        assert "custom_server" in config["mcpServers"]
        assert config["mcpServers"]["custom_server"]["command"] == "node"
        
        # aiwf entry must exist
        assert "aiwf" in config["mcpServers"]
        assert "server.py" in config["mcpServers"]["aiwf"]["args"][0]
        
        # Backup folder must contain a backup copy
        backup_dir = os.path.join(temp_workspace, ".agents", "state", "mcp", "backup")
        assert os.path.exists(backup_dir)
        backups = os.listdir(backup_dir)
        assert len(backups) == 1
        assert backups[0].startswith("antigravity_")
        
        # 5. Test Status check
        status_res = manager.status("antigravity")
        assert status_res["installed"] == "Installed"
        assert status_res["server_available"] == "Available"
        
        # 6. Uninstall AIWF MCP
        uninstall_res = manager.uninstall("antigravity")
        assert uninstall_res["status"] == "success"
        
        # Verify aiwf entry is deleted but custom_server is preserved
        with open(mock_config_file, "r") as f:
            config_after = json.load(f)
            
        assert "aiwf" not in config_after["mcpServers"]
        assert "custom_server" in config_after["mcpServers"]
