import os
import json
import pytest
import sys
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "scripts"))

from workflow_runtime import do_orchestrator

class ArgsMock:
    def __init__(self, action, level=None, agent=None, workflow=None, work_item=None, orchestrator=False, runtime=False):
        self.subaction = action
        self.level = level
        self.agent = agent
        self.workflow = workflow
        self.work_item = work_item
        self.orchestrator = orchestrator
        self.runtime = runtime
        self.work_item_id = "FEAT-111"
        self.work_item_opt = None
        self.work_item = None

def test_start_orchestrator(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    args = ArgsMock("start")
    with pytest.raises(SystemExit) as excinfo:
        do_orchestrator(args)
    assert excinfo.value.code == 1
    captured = capsys.readouterr()
    assert "deprecated" in captured.err

def test_stop_orchestrator(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    args = ArgsMock("stop")
    with pytest.raises(SystemExit) as excinfo:
        do_orchestrator(args)
    assert excinfo.value.code == 1
    captured = capsys.readouterr()
    assert "deprecated" in captured.err

def test_status_orchestrator(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    args = ArgsMock("status")
    do_orchestrator(args)
    captured = capsys.readouterr()
    assert "Resident Orchestrator: DISABLED" in captured.out
    assert "Runtime Manager: DISABLED" in captured.out

def test_health_orchestrator(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    args = ArgsMock("health")
    do_orchestrator(args)
    captured = capsys.readouterr()
    assert "DISABLED" in captured.out

def test_attach_detach(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    args = ArgsMock("attach")
    with pytest.raises(SystemExit) as excinfo:
        do_orchestrator(args)
    assert excinfo.value.code == 1
    captured = capsys.readouterr()
    assert "deprecated" in captured.err
    
    args_det = ArgsMock("detach")
    with pytest.raises(SystemExit) as excinfo_det:
        do_orchestrator(args_det)
    assert excinfo_det.value.code == 1

def test_agents_workflows_queue_graph_locks(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    state_dir = tmp_path / ".agents" / "state"
    orch_dir = state_dir / "work-items" / "FEAT-111" / "orchestrator"
    os.makedirs(orch_dir, exist_ok=True)
    
    with open(state_dir / "agents.json", "w") as f:
        json.dump({"AGENT-PM-001": {"role": "orchestrator", "status": "idle"}}, f)
        
    with open(orch_dir / "agents.json", "w") as f:
        json.dump({"AGENT-PM-001": {"role": "orchestrator", "status": "idle"}}, f)
        
    with open(orch_dir / "task_graph.json", "w") as f:
        json.dump({
            "tasks": {
                "TASK-1": {
                    "id": "TASK-1",
                    "name": "mock task",
                    "dependencies": [],
                    "status": "running",
                    "assigned_agent": "AGENT-PM-001"
                }
            }
        }, f)
        
    with open(orch_dir / "locks.json", "w") as f:
        json.dump({"active": {"res1": {"owner_agent_id": "AGENT-PM-001", "task_id": "TASK-1"}}}, f)
        
    args = ArgsMock("agents")
    do_orchestrator(args)
    captured = capsys.readouterr()
    assert "AGENT-PM-001" in captured.out
    
    args = ArgsMock("queue")
    do_orchestrator(args)
    captured = capsys.readouterr()
    assert "TASK-1" in captured.out
    
    args = ArgsMock("graph")
    do_orchestrator(args)
    captured = capsys.readouterr()
    assert "TASK-1" in captured.out
    
    args = ArgsMock("locks")
    do_orchestrator(args)
    captured = capsys.readouterr()
    assert "res1" in captured.out

def test_timeline_metrics_logs(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    state_dir = tmp_path / ".agents" / "state"
    os.makedirs(state_dir, exist_ok=True)
    
    timeline_file = state_dir / "timeline.jsonl"
    with open(timeline_file, "w") as f:
        f.write(json.dumps({"timestamp": "2026-07-12T12:00:00+07:00", "event_type": "daemon_started", "message": "Started."}) + "\n")
        f.write(json.dumps({"timestamp": "2026-07-12T12:01:00+07:00", "event_type": "task_started", "task_id": "TASK-1", "message": "Task started."}) + "\n")
        
    args = ArgsMock("timeline")
    do_orchestrator(args)
    captured = capsys.readouterr()
    assert "daemon_started" in captured.out
    
    args = ArgsMock("metrics")
    do_orchestrator(args)
    captured = capsys.readouterr()
    assert "Total Workflows" in captured.out
    
    args = ArgsMock("logs")
    do_orchestrator(args)
    captured = capsys.readouterr()
    assert "Task started." in captured.out
