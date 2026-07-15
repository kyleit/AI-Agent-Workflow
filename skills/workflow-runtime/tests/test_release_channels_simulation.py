import os
import re
import json
import pytest
from release_gate import ReleaseGate
from state_store import get_state_store
from ledger import ImplementationLedger

def setup_release_environment(isolated_workspace, version):
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
    for phase in raw.get("phases", []):
        phase["status"] = "completed"
    for tid, tdata in raw.get("tasks", {}).items():
        tdata["status"] = "completed"
    ledger.save(raw)
    
    # Set mock debug and verify files
    os.makedirs(os.path.join(isolated_workspace, "docs", "debug"), exist_ok=True)
    with open(os.path.join(isolated_workspace, "docs", "debug", "FEAT-999_debug.md"), "w") as f:
        f.write("PASS")
    os.makedirs(os.path.join(isolated_workspace, "docs", "reviews"), exist_ok=True)
    with open(os.path.join(isolated_workspace, "docs", "reviews", "FEAT-999_verify.md"), "w") as f:
        f.write("PASS")
        
    # Write version to .agents/MANIFEST.json
    agents_dir = os.path.join(isolated_workspace, ".agents")
    os.makedirs(agents_dir, exist_ok=True)
    manifest_path = os.path.join(agents_dir, "MANIFEST.json")
    manifest_data = {
        "name": "ai-skill-framework",
        "version": version
    }
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f)

def test_alpha_release_gate(isolated_workspace):
    setup_release_environment(isolated_workspace, "1.0.0-alpha.1")
    
    store = get_state_store()
    approvals = store.get("approvals") or {}
    approvals["release"] = {"approved": False}
    store.set("approvals", approvals)
    
    gate = ReleaseGate(isolated_workspace)
    allowed, reason = gate.validate()
    assert allowed is False
    assert "Alpha release requires Maintainer Approval" in reason
    
    approvals["release"] = {"approved": True}
    store.set("approvals", approvals)
    allowed, reason = gate.validate()
    assert "Alpha release requires Maintainer Approval" not in reason

def test_beta_release_gate_score_compliance(isolated_workspace):
    setup_release_environment(isolated_workspace, "1.0.0-beta.2")
    
    store = get_state_store()
    approvals = store.get("approvals") or {}
    approvals["release"] = {"approved": True}
    store.set("approvals", approvals)
    
    # Create architecture compliance report with low score
    verify_dir = os.path.join(isolated_workspace, "docs", "verification")
    os.makedirs(verify_dir, exist_ok=True)
    arch_path = os.path.join(verify_dir, "FEAT-999_architecture_verify.md")
    with open(arch_path, "w", encoding="utf-8") as f:
        f.write("Architecture Compliance Score: 92/100")
        
    gate = ReleaseGate(isolated_workspace)
    allowed, reason = gate.validate()
    assert allowed is False
    assert "Architecture Compliance Score is 92/100" in reason
    
    # Update score to pass
    with open(arch_path, "w", encoding="utf-8") as f:
        f.write("Architecture Compliance Score: 96/100")
    allowed, reason = gate.validate()
    assert allowed is True

def test_stable_release_gate(isolated_workspace):
    setup_release_environment(isolated_workspace, "1.0.0")
    
    store = get_state_store()
    approvals = store.get("approvals") or {}
    approvals["release"] = {"approved": False}
    store.set("approvals", approvals)
    
    gate = ReleaseGate(isolated_workspace)
    allowed, reason = gate.validate()
    assert allowed is False
    assert "Stable release requires Final Release Approval Gate" in reason
    
    approvals["release"] = {"approved": True}
    store.set("approvals", approvals)
    allowed, reason = gate.validate()
    assert allowed is True

def test_invalid_tag_format(isolated_workspace):
    setup_release_environment(isolated_workspace, "1.0.0-invalid.tag")
    
    store = get_state_store()
    approvals = store.get("approvals") or {}
    approvals["release"] = {"approved": True}
    store.set("approvals", approvals)
    
    gate = ReleaseGate(isolated_workspace)
    allowed, reason = gate.validate()
    assert allowed is False
    assert "does not comply with SemVer 2.0.0 format rules" in reason
