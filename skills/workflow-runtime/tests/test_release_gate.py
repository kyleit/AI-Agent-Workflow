import os
import pytest
from release_gate import ReleaseGate
from state_store import get_state_store
from ledger import ImplementationLedger

def test_release_gate_missing_gate3_approval(isolated_workspace):
    # Setup ledger
    ledger = ImplementationLedger(isolated_workspace)
    blueprint = {
        "feature_id": "FEAT-999",
        "feature_name": "Test feature",
        "implementation_packages": []
    }
    ledger.init_from_blueprint(blueprint)
    
    # Force implementation_status to completed
    raw = ledger.load()
    raw["implementation_status"] = "completed"
    ledger.save(raw)
    
    # Set other mock files so they don't block
    os.makedirs(os.path.join(isolated_workspace, "docs", "debug"), exist_ok=True)
    with open(os.path.join(isolated_workspace, "docs", "debug", "FEAT-999_debug.md"), "w") as f:
        f.write("PASS")
    os.makedirs(os.path.join(isolated_workspace, "docs", "reviews"), exist_ok=True)
    with open(os.path.join(isolated_workspace, "docs", "reviews", "FEAT-999_verify.md"), "w") as f:
        f.write("PASS")
        
    store = get_state_store()
    approvals = store.get("approvals") or {}
    approvals["release"] = {"approved": False}
    store.set("approvals", approvals)
    
    gate = ReleaseGate(isolated_workspace)
    allowed, reason = gate.validate()
    
    assert allowed is False
    assert "Missing manual Gate 3 Release Approval" in reason

def test_release_gate_approved_gate3(isolated_workspace):
    # Setup ledger
    ledger = ImplementationLedger(isolated_workspace)
    blueprint = {
        "feature_id": "FEAT-999",
        "feature_name": "Test feature",
        "implementation_packages": []
    }
    ledger.init_from_blueprint(blueprint)
    
    # Force implementation_status to completed
    raw = ledger.load()
    raw["implementation_status"] = "completed"
    ledger.save(raw)
    
    # Set other mock files so they don't block
    os.makedirs(os.path.join(isolated_workspace, "docs", "debug"), exist_ok=True)
    with open(os.path.join(isolated_workspace, "docs", "debug", "FEAT-999_debug.md"), "w") as f:
        f.write("PASS")
    os.makedirs(os.path.join(isolated_workspace, "docs", "reviews"), exist_ok=True)
    with open(os.path.join(isolated_workspace, "docs", "reviews", "FEAT-999_verify.md"), "w") as f:
        f.write("PASS")
        
    store = get_state_store()
    approvals = store.get("approvals") or {}
    approvals["release"] = {"approved": True}
    store.set("approvals", approvals)
    
    gate = ReleaseGate(isolated_workspace)
    allowed, reason = gate.validate()
    
    # Should not block on Gate 3 Release Approval
    assert "Missing manual Gate 3 Release Approval" not in reason
