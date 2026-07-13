import pytest
import os
import sys
import json
import subprocess
import shutil

# Thêm đường dẫn scripts vào sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "scripts")))

from workspace_doctor import check_permissions, check_skills, check_supervisor, get_runtime_mode

@pytest.fixture
def setup_mock_workspace(tmp_path):
    workspace = tmp_path / "mock_workspace"
    workspace.mkdir()
    
    # Tạo cấu hình config và skills registry
    config_dir = workspace / ".agents" / "config"
    config_dir.mkdir(parents=True)
    
    skills_dir = workspace / ".agents" / "skills"
    skills_dir.mkdir(parents=True)
    
    permissions_data = {
        "schema_version": "1.0.0",
        "initialized": True,
        "mode": "sandbox"
    }
    with open(config_dir / "permissions.json", "w", encoding="utf-8") as f:
        json.dump(permissions_data, f)
        
    registry_data = {
        "dummy_skill": {
            "name": "dummy",
            "phase": "discovery"
        }
    }
    with open(skills_dir / "registry.json", "w", encoding="utf-8") as f:
        json.dump(registry_data, f)
        
    yield str(workspace)

def test_workspace_doctor_checks(setup_mock_workspace):
    workspace = setup_mock_workspace
    
    # Kiểm tra permissions
    assert check_permissions(workspace) == "PASS"
    
    # Kiểm tra skills
    assert check_skills(workspace) == "PASS"
    
    # Kiểm tra supervisor (chạy thực tế trong workspace thật vì sys.path đã có scripts)
    assert check_supervisor(".") == "READY"
    
    # Kiểm tra runtime mode
    assert get_runtime_mode(workspace) == "session"

def test_init_does_not_spawn_daemon(setup_mock_workspace):
    workspace = setup_mock_workspace
    
    # Tạo project.config.json giả lập để do_init không chạy wizard
    project_config = {
        "schema_version": "1.0.0",
        "project": {"name": "test-project"}
    }
    with open(os.path.join(workspace, ".agents", "project.config.json"), "w", encoding="utf-8") as f:
        json.dump(project_config, f)
        
    # Tạo runtime-policy.json giả lập
    policy_data = {
        "schema_version": "1.0.0",
        "policy": {}
    }
    with open(os.path.join(workspace, ".agents", "config", "runtime-policy.json"), "w", encoding="utf-8") as f:
        json.dump(policy_data, f)
        
    # Tạo các thư mục con state
    os.makedirs(os.path.join(workspace, ".agents", "state"), exist_ok=True)
    
    # Chạy script workflow_runtime.py init trên mock workspace
    script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "scripts", "workflow_runtime.py"))
    
    # Thiết lập biến môi trường để trỏ state root và permission root vào mock workspace
    env = os.environ.copy()
    env["AIWF_STATE_ROOT"] = os.path.join(workspace, ".agents", "state")
    env["AIWF_PERMISSION_CONFIG_ROOT"] = os.path.join(workspace, ".agents", "config")
    
    # Copy file workspace_doctor.py sang cùng thư mục với script trong mock workspace hoặc gọi trực tiếp
    # Vì file workspace_doctor.py đang ở thư mục scripts thật, workflow_runtime.py cũng ở scripts thật,
    # chúng ta có thể gọi trực tiếp thông qua sys.executable
    
    # Chạy lệnh
    cmd = [sys.executable, script_path, "init"]
    output = subprocess.check_output(cmd, env=env, cwd=os.path.abspath(".")).decode()
    
    # Kiểm tra đầu ra chuẩn
    assert "Workspace:" in output
    assert "READY" in output
    assert "Runtime:" in output
    assert "SESSION_MODE" in output
    assert "Resident Orchestrator:" in output
    assert "DISABLED" in output
    assert "Workflow Supervisor:" in output
    assert "READY" in output
    
    # Đảm bảo daemon.json không được sinh ra trong mock workspace
    daemon_path = os.path.join(workspace, ".agents", "state", "daemon.json")
    assert not os.path.exists(daemon_path)
