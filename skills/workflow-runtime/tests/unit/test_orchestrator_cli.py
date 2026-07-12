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

def test_start_orchestrator(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    state_dir = tmp_path / ".agents" / "state"
    os.makedirs(state_dir, exist_ok=True)
    
    with patch("subprocess.Popen") as mock_popen:
        args = ArgsMock("start")
        do_orchestrator(args)
        assert mock_popen.called

def test_stop_orchestrator(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    state_dir = tmp_path / ".agents" / "state"
    os.makedirs(state_dir, exist_ok=True)
    
    daemon_file = state_dir / "daemon.json"
    with open(daemon_file, "w") as f:
        json.dump({"pid": 99999, "status": "running"}, f)
        
    with patch("psutil.pid_exists", return_value=True), \
         patch("psutil.Process") as mock_process:
        mock_p_instance = MagicMock()
        mock_process.return_value = mock_p_instance
        
        args = ArgsMock("stop")
        do_orchestrator(args)
        
        assert mock_p_instance.terminate.called
        assert not os.path.exists(daemon_file)

def test_status_orchestrator(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    state_dir = tmp_path / ".agents" / "state"
    os.makedirs(state_dir, exist_ok=True)
    
    import datetime
    now_iso = datetime.datetime.now(datetime.timezone.utc).astimezone().isoformat()
    
    daemon_file = state_dir / "daemon.json"
    with open(daemon_file, "w") as f:
        json.dump({
            "pid": 99999,
            "status": "running",
            "started_at": now_iso,
            "heartbeat_at": now_iso
        }, f)
        
    orch_file = state_dir / "orchestrator.json"
    with open(orch_file, "w") as f:
        json.dump({
            "pid": 99999,
            "status": "running",
            "attach_mode": "started",
            "last_heartbeat": now_iso
        }, f)
        
    mgr_file = state_dir / "runtime-manager.json"
    with open(mgr_file, "w") as f:
        json.dump({
            "status": "running"
        }, f)
    
    with patch("psutil.pid_exists", return_value=True):
        args = ArgsMock("status")
        do_orchestrator(args)
        
        captured = capsys.readouterr()
        assert "Status: RUNNING" in captured.out or "Resident Orchestrator: RUNNING" in captured.out
        assert "PID: 99999" in captured.out

def test_health_orchestrator(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    state_dir = tmp_path / ".agents" / "state"
    os.makedirs(state_dir, exist_ok=True)
    
    import datetime
    now_iso = datetime.datetime.now(datetime.timezone.utc).astimezone().isoformat()
    
    daemon_file = state_dir / "daemon.json"
    with open(daemon_file, "w") as f:
        json.dump({"pid": 99999, "status": "running"}, f)
        
    orch_file = state_dir / "orchestrator.json"
    with open(orch_file, "w") as f:
        json.dump({
            "pid": 99999,
            "status": "running",
            "attach_mode": "started",
            "last_heartbeat": now_iso
        }, f)
        
    mgr_file = state_dir / "runtime-manager.json"
    with open(mgr_file, "w") as f:
        json.dump({
            "status": "running"
        }, f)
    
    with patch("psutil.pid_exists", return_value=True), \
         patch("psutil.Process") as mock_proc:
        mock_p = MagicMock()
        mock_p.cpu_percent.return_value = 1.5
        mock_p.memory_info.return_value.rss = 50 * 1024 * 1024
        mock_proc.return_value = mock_p
        
        args = ArgsMock("health")
        do_orchestrator(args)
        
        captured = capsys.readouterr()
        assert "Overall Health: HEALTHY" in captured.out
        assert "CPU Usage: 1.5%" in captured.out

def test_attach_detach(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    state_dir = tmp_path / ".agents" / "state"
    os.makedirs(state_dir, exist_ok=True)
    
    context_file = state_dir / "context.json"
    with open(context_file, "w") as f:
        json.dump({"attach_mode": False}, f)
        
    args = ArgsMock("attach")
    do_orchestrator(args)
    with open(context_file, "r") as f:
        ctx = json.load(f)
    assert ctx["attach_mode"] is True
    
    args_det = ArgsMock("detach")
    do_orchestrator(args_det)
    with open(context_file, "r") as f:
        ctx = json.load(f)
    assert ctx["attach_mode"] is False

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
