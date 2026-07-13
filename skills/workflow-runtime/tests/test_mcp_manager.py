# skills/workflow-runtime/tests/test_mcp_manager.py
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
    # Create subfolders representing settings paths
    os.makedirs(os.path.join(ws, ".agents"), exist_ok=True)
    os.makedirs(os.path.join(ws, "skills", "workflow-runtime", "mcp"), exist_ok=True)
    os.makedirs(os.path.join(ws, "skills", "workflow-runtime", "scripts"), exist_ok=True)
    
    # Write mock files to allow doctor checklist to pass
    with open(os.path.join(ws, "skills", "workflow-runtime", "mcp", "server.py"), "w") as f:
        f.write("# mock")
    with open(os.path.join(ws, "skills", "workflow-runtime", "scripts", "workflow_runtime.py"), "w") as f:
        f.write("# mock")
        
    return ws

def test_mcp_manager_doctor(temp_workspace):
    manager = MCPManager(temp_workspace)
    
    # Mock config paths to point inside temp_workspace to protect user files
    mock_antigravity_config = os.path.join(temp_workspace, "antigravity_mcp.json")
    mock_vscode_config = os.path.join(temp_workspace, "vscode_mcp.json")
    mock_cursor_config = os.path.join(temp_workspace, "cursor_mcp.json")
    
    with patch.object(manager.adapters["antigravity"], "get_config_path", return_value=mock_antigravity_config), \
         patch.object(manager.adapters["vscode"], "get_config_path", return_value=mock_vscode_config), \
         patch.object(manager.adapters["cursor"], "get_config_path", return_value=mock_cursor_config):
         
        # By default check passes with warning because parent folder exists but config file is missing
        doc_res = manager.doctor("antigravity")
        assert doc_res["status"] == "healthy"
        
        # Test unhealthy status when IDE is not detected
        with patch.object(manager.adapters["antigravity"], "detect", return_value=False):
            unhealthy_res = manager.doctor("antigravity")
            assert unhealthy_res["status"] == "unhealthy"
        
        # Now create mock config
        with open(mock_antigravity_config, "w") as f:
            json.dump({"mcpServers": {}}, f)
            
        # Recheck doctor
        doc_res = manager.doctor("antigravity")
        assert doc_res["status"] == "healthy"
        assert len(doc_res["diagnostics"]) >= 4
        
        # Test status check
        status_res = manager.status("antigravity")
        assert status_res["installed"] == "Not Installed"
        assert status_res["server_available"] == "Unavailable"
