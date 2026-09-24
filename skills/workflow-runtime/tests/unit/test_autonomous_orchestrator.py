import sys
import os
import json
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "scripts"))

from autonomous_orchestrator import create_authorization, run_autonomous_delivery
# autonomous_orchestrator is now a re-export facade; the path constants live in
# the modules that use them.
from workflow_runtime.application.use_cases import orchestrator_core, orchestrator_delivery

def test_create_authorization(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    state_dir = tmp_path / ".agents" / "state" / "orchestrator"
    os.makedirs(state_dir, exist_ok=True)
    art_dir = tmp_path / "artifacts" / "autonomous-orchestrator"
    os.makedirs(art_dir, exist_ok=True)
    
    # Patch target directory paths inside autonomous_orchestrator
    monkeypatch.setattr(orchestrator_core, "AUTH_PATH", str(tmp_path / ".agents" / "state" / "authorization.json"))
    monkeypatch.setattr(orchestrator_core, "AUTH_ORCH_PATH", str(state_dir / "authorization.json"))
    monkeypatch.setattr(orchestrator_core, "ART_DIR", str(art_dir))
    
    from autonomous_orchestrator import resolve_auth_path
    auth = create_authorization("FEAT-111")
    assert auth["mode"] == "autonomous_delivery"
    assert auth["work_item_id"] == "FEAT-111"
    assert os.path.exists(resolve_auth_path("FEAT-111"))

def test_run_autonomous_delivery(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    state_dir = tmp_path / ".agents" / "state" / "orchestrator"
    os.makedirs(state_dir, exist_ok=True)
    art_dir = tmp_path / "artifacts" / "autonomous-orchestrator"
    os.makedirs(art_dir, exist_ok=True)
    
    monkeypatch.setattr(orchestrator_delivery, "STATE_DIR", str(state_dir))
    monkeypatch.setattr(orchestrator_delivery, "CP_DIR", str(state_dir / "checkpoints"))
    monkeypatch.setattr(orchestrator_delivery, "ART_DIR", str(art_dir))
    monkeypatch.setattr(orchestrator_core, "ART_DIR", str(art_dir))
    monkeypatch.setattr(orchestrator_delivery, "AUTH_PATH", str(tmp_path / ".agents" / "state" / "authorization.json"))
    monkeypatch.setattr(orchestrator_delivery, "AUTH_ORCH_PATH", str(state_dir / "authorization.json"))
    
    # run_autonomous_delivery resolves CapacityController via the locator.
    from workflow_runtime.presentation.cli.bootstrap import bootstrap_di
    bootstrap_di()

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
