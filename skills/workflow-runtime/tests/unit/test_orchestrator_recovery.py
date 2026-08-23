import sys
import os
import json
import pytest
from unittest.mock import MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "scripts"))

from workflow_runtime import do_orchestrator

class ArgsMock:
    def __init__(self, action, task_id=None, lock_id=None):
        self.action = action
        self.task_id = task_id
        self.lock_id = lock_id

def test_do_orchestrator_resume(tmp_path, monkeypatch):
    state_dir = tmp_path / ".agents" / "state" / "orchestrator"
    os.makedirs(state_dir, exist_ok=True)
    
    # Mock objective.json
    obj_file = state_dir / "objective.json"
    with open(obj_file, "w") as f:
        json.dump({"objective_id": "OBJ-123", "status": "idle"}, f)
        
    monkeypatch.chdir(tmp_path)
    
    args = ArgsMock("resume")
    do_orchestrator(args)
    
    with open(obj_file, "r") as f:
        obj = json.load(f)
    assert obj["status"] == "in_progress"

def test_do_orchestrator_retry(tmp_path, monkeypatch):
    state_dir = tmp_path / ".agents" / "state" / "orchestrator"
    os.makedirs(state_dir, exist_ok=True)
    
    tg_file = state_dir / "task_graph.json"
    with open(tg_file, "w") as f:
        json.dump({
            "tasks": {
                "TASK-1": {"status": "failed"}
            }
        }, f)
        
    monkeypatch.chdir(tmp_path)
    
    args = ArgsMock("retry", task_id="TASK-1")
    do_orchestrator(args)
    
    with open(tg_file, "r") as f:
        tg = json.load(f)
    assert tg["tasks"]["TASK-1"]["status"] == "ready"

def test_do_orchestrator_cancel(tmp_path, monkeypatch):
    state_dir = tmp_path / ".agents" / "state" / "orchestrator"
    os.makedirs(state_dir, exist_ok=True)
    
    tg_file = state_dir / "task_graph.json"
    with open(tg_file, "w") as f:
        json.dump({
            "tasks": {
                "TASK-1": {"status": "running"}
            }
        }, f)
        
    monkeypatch.chdir(tmp_path)
    
    args = ArgsMock("cancel", task_id="TASK-1")
    do_orchestrator(args)
    
    with open(tg_file, "r") as f:
        tg = json.load(f)
    assert tg["tasks"]["TASK-1"]["status"] == "cancelled"

def test_do_orchestrator_release_lock(tmp_path, monkeypatch):
    state_dir = tmp_path / ".agents" / "state" / "orchestrator"
    os.makedirs(state_dir, exist_ok=True)
    
    locks_file = state_dir / "locks.json"
    with open(locks_file, "w") as f:
        json.dump({
            "active": {
                "resource_1": {"owner_agent_id": "agent-1"}
            }
        }, f)
        
    monkeypatch.chdir(tmp_path)
    
    args = ArgsMock("release_lock", lock_id="resource_1")
    do_orchestrator(args)
    
    with open(locks_file, "r") as f:
        locks = json.load(f)
    assert "resource_1" not in locks.get("active", {})

def test_do_orchestrator_restore_checkpoint(tmp_path, monkeypatch):
    state_dir = tmp_path / ".agents" / "state" / "orchestrator"
    cp_dir = state_dir / "checkpoints"
    os.makedirs(cp_dir, exist_ok=True)
    
    # Mock objective, queue, task_graph, agents, locks
    obj_file = state_dir / "objective.json"
    with open(obj_file, "w") as f:
        json.dump({"status": "failed"}, f)
        
    cp_file = cp_dir / "checkpoint_CP-001.json"
    with open(cp_file, "w") as f:
        json.dump({
            "checkpoint_id": "CP-001",
            "objective": {"status": "in_progress"},
            "queue": ["TASK-1"],
            "task_graph": {"tasks": {"TASK-1": {"status": "ready"}}},
            "agents": {},
            "locks": {}
        }, f)
        
    monkeypatch.chdir(tmp_path)
    
    args = ArgsMock("restore_checkpoint", task_id="CP-001")
    do_orchestrator(args)
    
    with open(obj_file, "r") as f:
        obj = json.load(f)
    assert obj["status"] == "in_progress"
