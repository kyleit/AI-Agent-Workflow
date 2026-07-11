import os
import json
import sys
import pytest
pytestmark = pytest.mark.unit
from datetime import datetime

# Add scripts directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "scripts")))

from session import (
    get_project_permission_config_path,
    load_project_permissions,
    write_project_permissions_atomic,
    validate_permissions_data
)
from workflow_runtime import main
pytestmark = [pytest.mark.unit, pytest.mark.smoke]


@pytest.fixture(autouse=True)
def setup_permissions_testing(monkeypatch):
    monkeypatch.setenv("AIWF_TESTING_PERMISSIONS", "true")

def test_config_path_override(tmp_path, monkeypatch):
    # Without override
    monkeypatch.delenv("AIWF_PERMISSION_CONFIG_ROOT", raising=False)
    p = get_project_permission_config_path()
    assert p.endswith(os.path.join(".agents", "config", "permissions.json"))
    
    # With override
    monkeypatch.setenv("AIWF_PERMISSION_CONFIG_ROOT", str(tmp_path))
    p = get_project_permission_config_path()
    assert p == os.path.join(str(tmp_path), "permissions.json")

def test_load_and_write_atomic(tmp_path, monkeypatch):
    monkeypatch.setenv("AIWF_PERMISSION_CONFIG_ROOT", str(tmp_path))
    
    # Missing config returns None under normal mode (if PYTEST_CURRENT_TEST is temporarily removed or normal mode check)
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
    monkeypatch.setenv("AIWF_RUNTIME_MODE", "normal")
    assert load_project_permissions() is None
    
    # Restore pytest env for safety
    monkeypatch.setenv("PYTEST_CURRENT_TEST", "true")
    
    data = {
        "schema_version": "1.0.0",
        "initialized": True,
        "mode": "sandbox",
        "config_revision": 1,
        "initialized_at": datetime.now().astimezone().isoformat(),
        "updated_at": datetime.now().astimezone().isoformat(),
        "updated_by": "test",
        "source": "cli"
    }
    
    write_project_permissions_atomic(data)
    loaded = load_project_permissions()
    assert loaded["mode"] == "sandbox"
    assert loaded["schema_version"] == "1.0.0"

def test_validate_permissions_data():
    # Valid
    valid_data = {
        "schema_version": "1.0.0",
        "initialized": True,
        "mode": "sandbox"
    }
    ok, msg = validate_permissions_data(valid_data)
    assert ok is True
    
    # Invalid structure
    ok, msg = validate_permissions_data([])
    assert ok is False
    
    # Missing field
    invalid_data = {
        "schema_version": "1.0.0",
        "initialized": True
    }
    ok, msg = validate_permissions_data(invalid_data)
    assert ok is False
    assert "mode" in msg
    
    # Invalid mode value
    invalid_mode = {
        "schema_version": "1.0.0",
        "initialized": True,
        "mode": "invalid"
    }
    ok, msg = validate_permissions_data(invalid_mode)
    assert ok is False
    assert "Invalid permission mode" in msg

def test_cli_permissions_init_and_show(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("AIWF_PERMISSION_CONFIG_ROOT", str(tmp_path))
    
    # CLI init
    monkeypatch.setattr("sys.argv", ["workflow_runtime.py", "permissions", "init", "--mode", "full_access"])
    main()
    captured = capsys.readouterr()
    assert "Successfully initialized project permission mode to 'full_access'" in captured.out
    
    # Verify file content
    config_file = os.path.join(str(tmp_path), "permissions.json")
    assert os.path.exists(config_file)
    with open(config_file, "r") as f:
        data = json.load(f)
    assert data["mode"] == "full_access"
    
    # CLI show
    monkeypatch.setattr("sys.argv", ["workflow_runtime.py", "permissions", "show"])
    main()
    captured = capsys.readouterr()
    parsed = json.loads(captured.out)
    assert parsed["mode"] == "full_access"

def test_cli_permissions_change_and_validate(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("AIWF_PERMISSION_CONFIG_ROOT", str(tmp_path))
    
    # CLI init first
    monkeypatch.setattr("sys.argv", ["workflow_runtime.py", "permissions", "init", "--mode", "sandbox"])
    main()
    capsys.readouterr() # clear buffers
    
    # CLI change escalation with force
    monkeypatch.setattr("sys.argv", ["workflow_runtime.py", "permissions", "change", "--mode", "full_access", "--force"])
    main()
    captured = capsys.readouterr()
    assert "Successfully changed project permission mode from 'sandbox' to 'full_access'" in captured.out
    
    # CLI validate
    monkeypatch.setattr("sys.argv", ["workflow_runtime.py", "permissions", "validate"])
    main()
    captured = capsys.readouterr()
    assert "Validation succeeded: permissions.json is valid" in captured.out
