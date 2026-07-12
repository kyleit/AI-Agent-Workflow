import sys
import os
import json
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "scripts"))

from autonomous_orchestrator import create_authorization, run_autonomous_delivery

def test_create_authorization(tmp_path, monkeypatch):
    state_dir = tmp_path / ".agents" / "state" / "orchestrator"
    os.makedirs(state_dir, exist_ok=True)
    art_dir = tmp_path / "artifacts" / "autonomous-orchestrator"
    os.makedirs(art_dir, exist_ok=True)
    
    # Patch target directory paths inside autonomous_orchestrator
    monkeypatch.setattr("autonomous_orchestrator.AUTH_PATH", str(tmp_path / ".agents" / "state" / "authorization.json"))
    monkeypatch.setattr("autonomous_orchestrator.AUTH_ORCH_PATH", str(state_dir / "authorization.json"))
    monkeypatch.setattr("autonomous_orchestrator.ART_DIR", str(art_dir))
    
    auth = create_authorization("FEAT-111")
    assert auth["mode"] == "autonomous_delivery"
    assert auth["work_item_id"] == "FEAT-111"
    assert os.path.exists(tmp_path / ".agents" / "state" / "authorization.json")

def test_run_autonomous_delivery(tmp_path, monkeypatch):
    state_dir = tmp_path / ".agents" / "state" / "orchestrator"
    os.makedirs(state_dir, exist_ok=True)
    art_dir = tmp_path / "artifacts" / "autonomous-orchestrator"
    os.makedirs(art_dir, exist_ok=True)
    
    monkeypatch.setattr("autonomous_orchestrator.STATE_DIR", str(state_dir))
    monkeypatch.setattr("autonomous_orchestrator.CP_DIR", str(state_dir / "checkpoints"))
    monkeypatch.setattr("autonomous_orchestrator.ART_DIR", str(art_dir))
    monkeypatch.setattr("autonomous_orchestrator.AUTH_PATH", str(tmp_path / ".agents" / "state" / "authorization.json"))
    monkeypatch.setattr("autonomous_orchestrator.AUTH_ORCH_PATH", str(state_dir / "authorization.json"))
    
    # Run simulation
    run_autonomous_delivery("FEAT-111")
    
    # Assert generated files exist
    assert os.path.exists(state_dir / "objective.json")
    assert os.path.exists(state_dir / "agents.json")
    assert os.path.exists(state_dir / "task_graph.json")
    assert os.path.exists(art_dir / "validation_results.json")
    
    with open(art_dir / "validation_results.json", "r") as f:
        val = json.load(f)
    assert val["checks"]["autonomous_delivery_mode"] is True
