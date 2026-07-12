# -*- coding: utf-8 -*-
import sys
import os
import json
import pytest
import shutil
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "scripts"))

from hierarchical_runtime import CapabilityEngine, LockManager, HierarchicalRuntime

def test_capability_engine():
    assert CapabilityEngine.validate_action("orchestrator", "can_receive_user_commands") is True
    assert CapabilityEngine.validate_action("subagent", "can_receive_user_commands") is False
    assert CapabilityEngine.validate_action("subagent", "can_commit") is False

def test_lock_manager_scope_overlap():
    lm = LockManager()
    
    # Simple direct locking
    assert lm.acquire("sources/backend", "AGENT-001") is True
    # Same resource lock by different agent must fail
    assert lm.acquire("sources/backend", "AGENT-002") is False
    
    # Lock overlap checks
    assert lm.acquire("sources/backend/src/main.py", "AGENT-002") is False
    
    lm.release("sources/backend", "AGENT-001")
    assert lm.acquire("sources/backend/src/main.py", "AGENT-002") is True

def test_hierarchical_runtime_lifecycle():
    with tempfile.TemporaryDirectory() as tmp_dir:
        rt = HierarchicalRuntime("FEAT-111-TEST", state_dir=tmp_dir, art_dir=tmp_dir)
        
        # Test command inbox
        rt.receive_command("set concurrency 6")
        assert "set concurrency 6" in rt.command_inbox
        
        rt.process_inbox()
        assert len(rt.command_inbox) == 0
        assert rt.task_graph["concurrency_limit"] == 6
        
        # Run workflow cycle
        rt.run_workflow_cycle()
        
        # Confirm atomic states
        assert os.path.exists(os.path.join(tmp_dir, "agents.json"))
        assert os.path.exists(os.path.join(tmp_dir, "tasks.json"))
