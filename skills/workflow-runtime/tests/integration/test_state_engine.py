import os
import pytest
pytestmark = pytest.mark.integration
pytestmark = [pytest.mark.integration, pytest.mark.stateful]

import json
import pytest
pytestmark = pytest.mark.integration
import shutil
import sys
from datetime import datetime, timedelta

# Add scripts directory to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "scripts"))

from fingerprint import calculate_project_fingerprint
from state_sync import write_json_atomic, read_json_safe, aggregate_state, deconstruct_state
from session import load_session, save_session_atomic
from workflow_runtime import do_init

def test_write_json_atomic(tmp_path):
    file_path = os.path.join(tmp_path, "test.json")
    data = {"key": "value"}
    write_json_atomic(file_path, data)
    assert os.path.exists(file_path)
    with open(file_path, 'r', encoding='utf-8') as f:
        loaded = json.load(f)
    assert loaded == data

def test_calculate_project_fingerprint(tmp_path):
    fp = calculate_project_fingerprint(str(tmp_path))
    assert len(fp) == 64  # SHA-256 length hex

def test_state_splitting_and_aggregation(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    
    session = {
        "workspace": {"path": ".", "valid": True},
        "git": {
            "is_git_repository": True,
            "branch": "main",
            "working_tree": "clean",
            "default_branch": "main",
            "latest_tag": "none"
        },
        "work_item": {"type": "FEAT", "id": "FEAT-022", "title": "Split State"},
        "version": {"version": "1.0.0", "source": "none"},
        "memory": {"status": "HEALTHY", "last_updated": "N/A"},
        "rag": {"connected": False, "provider": "none"},
        "blueprint": {"path": "", "exists": False, "approved": False, "approved_at": "", "approved_by": ""},
        "checkpoint": 3,
        "status": "in_progress",
        "current_skill": "test",
        "current_command": "run",
        "current_step": "Running test...",
        "current_logs": ["log 1"],
        "project_fingerprint": "fake-fingerprint"
    }
    
    # Test Deconstruct
    deconstruct_state(".", session)
    state_dir = os.path.join(".", ".agents", "state")
    assert os.path.exists(state_dir)
    assert os.path.exists(os.path.join(state_dir, "context.json"))
    assert os.path.exists(os.path.join(state_dir, "workflow.json"))
    assert os.path.exists(os.path.join(state_dir, "runtime.json"))
    
    context = read_json_safe(os.path.join(state_dir, "context.json"))
    assert context.get("project_fingerprint") == "fake-fingerprint"
    
    # Test Aggregate
    aggregated = aggregate_state(".")
    assert aggregated["project_fingerprint"] == "fake-fingerprint"
    assert aggregated["work_item"]["id"] == "FEAT-022"

def test_bi_directional_sync_session_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    
    # Test save_session_atomic triggers deconstruct & aggregate
    data = {
        "workspace": {"path": ".", "valid": True},
        "git": {"is_git_repository": True, "branch": "test-branch"},
        "permission_mode": "sandbox",
        "conversation_id": "test-id"
    }
    save_session_atomic(data)
    
    # sub-state file context.json must exist and have test-branch
    state_dir = os.path.join(".", ".agents", "state")
    context = read_json_safe(os.path.join(state_dir, "context.json"))
    assert context["git"]["branch"] == "test-branch"
    assert context["conversation_id"] == "test-id"
    
    # load_session must aggregate successfully
    loaded = load_session()
    assert loaded["conversation_id"] == "test-id"
    assert loaded["git"]["branch"] == "test-branch"

def test_stale_data_drift_detection(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    
    # 1. Initialize states
    session = {
        "permission_mode": "sandbox",
        "conversation_id": "original-id"
    }
    os.makedirs(".agents", exist_ok=True)
    session_path = os.path.join(".agents", ".session.json")
    write_json_atomic(session_path, session)
    
    # 2. Simulate external modification to .session.json directly (newer timestamp)
    session_path = os.path.join(".agents", ".session.json")
    with open(session_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    data["conversation_id"] = "updated-externally-id"
    
    # Set session.json mtime to be in the future to simulate newer write
    write_json_atomic(session_path, data)
    future_time = datetime.now() + timedelta(seconds=10)
    os.utime(session_path, (future_time.timestamp(), future_time.timestamp()))
    
    # 3. Reading session will detect drift and auto-deconstruct/aggregate (synchronize)
    loaded = load_session()
    assert loaded["conversation_id"] == "updated-externally-id"
    
    # Verify sub-state is also updated
    context = read_json_safe(os.path.join(".agents", "state", "context.json"))
    assert context["conversation_id"] == "updated-externally-id"

def test_init_fingerprint_cache_hit_and_miss(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    
    # Setup args mock
    class Args:
        permission = "1" # Sandbox
    args = Args()
    
    # 1. First run: Cache Miss (No files exist)
    do_init(args)
    
    state_dir = os.path.join(".agents", "state")
    assert os.path.exists(os.path.join(state_dir, "context.json"))
    context1 = read_json_safe(os.path.join(state_dir, "context.json"))
    fp1 = context1["project_fingerprint"]
    assert len(fp1) == 64
    
    # 2. Second run: Cache Hit (Fingerprint matches)
    do_init(args)
    context2 = read_json_safe(os.path.join(state_dir, "context.json"))
    assert context2["project_fingerprint"] == fp1
    
    # Check that logs denote cache loaded
    session = load_session()
    assert "cache" in session["current_logs"][0]

def test_cli_commands_and_state_recovery(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    
    # Write initial states
    session = {
        "workspace": {"path": ".", "valid": True},
        "git": {"is_git_repository": True, "branch": "main"},
        "permission_mode": "sandbox",
        "conversation_id": "test-id"
    }
    save_session_atomic(session)
    
    # Import main & mock sys.argv
    from workflow_runtime import main
    
    # 1. Test 'context' command
    monkeypatch.setattr("sys.argv", ["workflow_runtime.py", "context"])
    main()
    captured = capsys.readouterr()
    res = json.loads(captured.out)
    assert res["conversation_id"] == "test-id"
    
    # 2. Test 'rules status' command
    monkeypatch.setattr("sys.argv", ["workflow_runtime.py", "rules", "status"])
    main()
    captured = capsys.readouterr()
    res = json.loads(captured.out)
    assert "active_rules" in res
    
    # 3. Test 'state status' command
    monkeypatch.setattr("sys.argv", ["workflow_runtime.py", "state", "status"])
    main()
    captured = capsys.readouterr()
    res = json.loads(captured.out)
    assert res["status"] == "healthy"
    assert res["session_synced"] is True
    
    # 4. Test 'state validate' command
    monkeypatch.setattr("sys.argv", ["workflow_runtime.py", "state", "validate"])
    main()
    captured = capsys.readouterr()
    res = json.loads(captured.out)
    assert res["status"] == "success"
    
    # 5. Test 'state recover' command (by deleting state directory)
    state_dir = os.path.join(".agents", "state")
    if os.path.exists(state_dir):
        shutil.rmtree(state_dir)
    # Write .session.json back to simulate backup availability for recovery
    write_json_atomic(os.path.join(".agents", ".session.json"), session)
    monkeypatch.setattr("sys.argv", ["workflow_runtime.py", "state", "recover"])
    main()
    captured = capsys.readouterr()
    res = json.loads(captured.out)
    assert res["status"] == "success"
    assert os.path.exists(os.path.join(".agents", "state", "context.json"))

def test_state_file_lock_and_granular_writes(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    from state_sync import StateFileLock, deconstruct_state
    
    # 1. Test Reentrant Lock
    with StateFileLock(".") as lock1:
        assert os.path.abspath(lock1.lock_file) == os.path.abspath(os.path.join(".agents", "state", "state.lock"))
        # Reentrant call should pass
        with StateFileLock(".") as lock2:
            pass
            
    # 2. Test Granular Write:
    session = {
        "workspace": {"path": ".", "valid": True},
        "git": {"is_git_repository": True},
        "permission_mode": "sandbox",
        "conversation_id": "original-id"
    }
    deconstruct_state(".", session)
    
    state_dir = os.path.join(".", ".agents", "state")
    context_path = os.path.join(state_dir, "context.json")
    workflow_path = os.path.join(state_dir, "workflow.json")
    
    # Ghi nhận mtime cũ
    old_context_mtime = os.path.getmtime(context_path)
    old_workflow_mtime = os.path.getmtime(workflow_path)
    
    import time
    time.sleep(0.1) # Wait a bit to ensure time difference
    
    # Chỉ thay đổi conversation_id (nằm trong context.json)
    session["conversation_id"] = "changed-id"
    deconstruct_state(".", session)
    
    new_context_mtime = os.path.getmtime(context_path)
    new_workflow_mtime = os.path.getmtime(workflow_path)
    
    # context.json phải được ghi đè (mtime mới)
    assert new_context_mtime > old_context_mtime
    # workflow.json KHÔNG được ghi đè (mtime giữ nguyên)
    assert new_workflow_mtime == old_workflow_mtime
