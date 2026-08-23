import pytest
import os
import sys
import json
import subprocess
import shutil

# Add scripts/ folder to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "scripts")))

@pytest.fixture
def setup_test_env(tmp_path):
    workspace = tmp_path / "doctor_test_ws"
    workspace.mkdir()
    
    # Setup .agents directories
    agents_dir = workspace / ".agents"
    agents_dir.mkdir()
    
    config_dir = agents_dir / "config"
    config_dir.mkdir()
    
    state_dir = agents_dir / "state"
    state_dir.mkdir()
    
    skills_dir = agents_dir / "skills"
    skills_dir.mkdir()
    
    # 1. Create permissions.json
    permissions_data = {
        "schema_version": "1.0.0",
        "initialized": True,
        "mode": "sandbox"
    }
    with open(config_dir / "permissions.json", "w", encoding="utf-8") as f:
        json.dump(permissions_data, f)
        
    # 2. Create registry.json
    registry_data = {
        "init": {
            "name": "initialize-workflow",
            "phase": "runtime"
        }
    }
    with open(skills_dir / "registry.json", "w", encoding="utf-8") as f:
        json.dump(registry_data, f)
        
    # 3. Create workflow.config.json
    workflow_config = {
        "project_name": "doctor-test",
        "git_flow": {
            "development_branch": "main",
            "release_branch": "main"
        }
    }
    with open(agents_dir / "workflow.config.json", "w", encoding="utf-8") as f:
        json.dump(workflow_config, f)
        
    yield str(workspace)

def test_doctor_success_flow(setup_test_env):
    workspace = setup_test_env
    script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "scripts", "workspace_doctor.py"))
    
    # Run workspace_doctor.py passing the mock workspace as target
    res = subprocess.run([sys.executable, script_path, workspace], capture_output=True, text=True)
    
    assert res.returncode == 0
    data = json.loads(res.stdout)
    
    assert data["status"] == "READY"
    assert data["workspace"]["project_type"] == "python" # default fallback
    assert data["permissions"]["permissions_json_exists"] is True
    assert data["permissions"]["initialized"] is True
    assert data["skills"]["registry_exists"] is True
    assert data["skills"]["skills_count"] == 1
    assert data["workflow"]["config_exists"] is True
    assert len(data["issues"]) == 0

def test_doctor_missing_permissions(setup_test_env):
    workspace = setup_test_env
    script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "scripts", "workspace_doctor.py"))
    
    # Remove permissions.json
    perm_file = os.path.join(workspace, ".agents", "config", "permissions.json")
    os.remove(perm_file)
    
    res = subprocess.run([sys.executable, script_path, workspace], capture_output=True, text=True)
    
    # Exit code should be 1 since status is FAIL
    assert res.returncode == 1
    data = json.loads(res.stdout)
    
    assert data["status"] == "FAIL"
    assert data["permissions"]["permissions_json_exists"] is False
    assert any("permissions.json config file is missing" in iss for iss in data["issues"])

def test_doctor_missing_skills_registry(setup_test_env):
    workspace = setup_test_env
    script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "scripts", "workspace_doctor.py"))
    
    # Remove registry.json
    reg_file = os.path.join(workspace, ".agents", "skills", "registry.json")
    os.remove(reg_file)
    
    res = subprocess.run([sys.executable, script_path, workspace], capture_output=True, text=True)
    
    assert res.returncode == 1
    data = json.loads(res.stdout)
    
    assert data["status"] == "FAIL"
    assert data["skills"]["registry_exists"] is False
    assert any("registry.json is missing" in iss for iss in data["issues"])

def test_doctor_project_stack_detection(setup_test_env):
    workspace = setup_test_env
    script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "scripts", "workspace_doctor.py"))
    
    # Create go.mod to simulate Golang project
    with open(os.path.join(workspace, "go.mod"), "w", encoding="utf-8") as f:
        f.write("module test\ngo 1.21\n")
        
    res = subprocess.run([sys.executable, script_path, workspace], capture_output=True, text=True)
    data = json.loads(res.stdout)
    
    assert "Go" in data["workspace"]["languages"]
    assert data["workspace"]["project_type"] == "golang"
    
    # Verify golang tool compat check
    assert data["toolchain"]["golang"]["compat"] == "1.21"

def test_doctor_json_schema_compliance(setup_test_env):
    workspace = setup_test_env
    script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "scripts", "workspace_doctor.py"))
    schema_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "workspace_doctor.schema.json"))
    
    res = subprocess.run([sys.executable, script_path, workspace], capture_output=True, text=True)
    data = json.loads(res.stdout)
    
    # Load schema
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = json.load(f)
        
    # Attempt schema validation if jsonschema is installed
    try:
        from jsonschema import validate
        validate(instance=data, schema=schema)
    except ImportError:
        # Fallback basic schema validation
        assert "status" in data
        assert "workspace" in data
        assert "environment" in data
        assert "toolchain" in data
        assert "runtime" in data
        assert "permissions" in data
        assert "skills" in data
        assert "workflow" in data
        assert "issues" in data
        assert "recommendations" in data
