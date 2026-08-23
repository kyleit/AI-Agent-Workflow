# test_full_access.py
import pytest
pytestmark = pytest.mark.integration

import unittest
import os
import sys
import shutil
import json

# Add scripts directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "scripts")))

from state_store import get_state_store, reset_state_store, set_active_work_item_id
from session import load_session, save_session_atomic
from utils import prompt_select
from workflow_runtime import requires_approval

class TestFullAccessAutonomousDelivery(unittest.TestCase):
    def setUp(self):
        os.environ["TESTING"] = "1"
        self.test_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "temp_full_access_test"))
        os.makedirs(self.test_dir, exist_ok=True)
        
        # Override state root and permission root
        self.original_state_root = os.environ.get("AIWF_STATE_ROOT")
        os.environ["AIWF_STATE_ROOT"] = self.test_dir
        self.original_perm_root = os.environ.get("AIWF_PERMISSION_CONFIG_ROOT")
        os.environ["AIWF_PERMISSION_CONFIG_ROOT"] = self.test_dir
        os.environ["AIWF_TESTING_PERMISSIONS"] = "true"
        
        # Reset state store to initialize with the new state root
        reset_state_store(None)

        # Create a mock context.json to allow load_session to work
        context_data = {
            "project_id": "test-project",
            "workspace_path": os.getcwd(),
            "git": {"is_git_repository": False}
        }
        with open(os.path.join(self.test_dir, "context.json"), "w", encoding="utf-8") as f:
            json.dump(context_data, f)
            
        # Clean any preexisting events
        self.cleanup_events()

    def tearDown(self):
        # Restore environment and state store
        if self.original_state_root is not None:
            os.environ["AIWF_STATE_ROOT"] = self.original_state_root
        else:
            os.environ.pop("AIWF_STATE_ROOT", None)
            
        if self.original_perm_root is not None:
            os.environ["AIWF_PERMISSION_CONFIG_ROOT"] = self.original_perm_root
        else:
            os.environ.pop("AIWF_PERMISSION_CONFIG_ROOT", None)
        os.environ.pop("AIWF_TESTING_PERMISSIONS", None)
            
        reset_state_store(None)
        
        # Clean up temp files
        if os.path.exists(self.test_dir):
            try:
                shutil.rmtree(self.test_dir)
            except Exception:
                pass
                
        self.cleanup_events()

    def cleanup_events(self):
        paths = [
            os.path.join("artifacts", "full-access-autonomous-delivery", "gate_resolution_events.jsonl"),
            os.path.join("docs", "debug", "gate_resolution_events.jsonl"),
            os.path.join("artifacts", "full-access-autonomous-delivery", "phase_transition_events.jsonl")
        ]
        for p in paths:
            if os.path.exists(p):
                try:
                    os.remove(p)
                except Exception:
                    pass

    def test_prompt_bypass_in_full_access(self):
        # 1. Setup full_access session
        save_session_atomic({
            "permission_mode": "full_access",
            "work_item": {"id": "FEAT-115"}
        })
        
        # Override active work item env
        os.environ["AIWF_ACTIVE_WORK_ITEM"] = "FEAT-115"
        
        # 2. Call prompt select which should automatically resolve to "Yes" positive choice
        res = prompt_select("Proceed to Planning? [Y/N]", ["Yes", "No"], default="No")
        self.assertEqual(res, "Yes")
        
        # 3. Verify gate resolution event is logged
        log_path = os.path.join("artifacts", "full-access-autonomous-delivery", "gate_resolution_events.jsonl")
        self.assertTrue(os.path.exists(log_path))
        with open(log_path, "r", encoding="utf-8") as f:
            line = f.readline().strip()
            event = json.loads(line)
            self.assertEqual(event["resolution"], "AUTHORIZED_BY_FULL_ACCESS")
            self.assertEqual(event["decision"], "Yes")

    def test_prompt_sandbox_compatibility(self):
        # 1. Setup sandbox session
        save_session_atomic({
            "permission_mode": "sandbox",
            "work_item": {"id": "FEAT-115"}
        })
        
        # 2. In testing environment, prompt_select falls back to default in sandbox mode
        res = prompt_select("Proceed to Planning? [Y/N]", ["Yes", "No"], default="No")
        self.assertEqual(res, "No")

    def test_release_protection(self):
        save_session_atomic({
            "permission_mode": "full_access",
            "work_item": {"id": "FEAT-115"}
        })
        os.environ["AIWF_ACTIVE_WORK_ITEM"] = "FEAT-115"
        
        # Protected git action must be blocked
        blocked = requires_approval("git_commit")
        self.assertTrue(blocked)
        
        # Verify blocked event is logged
        log_path = os.path.join("artifacts", "full-access-autonomous-delivery", "gate_resolution_events.jsonl")
        self.assertTrue(os.path.exists(log_path))
        with open(log_path, "r", encoding="utf-8") as f:
            line = f.readline().strip()
            event = json.loads(line)
            self.assertEqual(event["resolution"], "BLOCKED_BY_RELEASE_BOUNDARY")

    def test_scope_protection_work_item_isolation(self):
        # Setup session for FEAT-115 but env is active for FEAT-116 (mismatched scope)
        save_session_atomic({
            "permission_mode": "full_access",
            "work_item": {"id": "FEAT-115"}
        })
        os.environ["AIWF_ACTIVE_WORK_ITEM"] = "FEAT-116"
        
        blocked = requires_approval("normal_file_write")
        self.assertTrue(blocked)
        
        # Verify out of scope log
        log_path = os.path.join("artifacts", "full-access-autonomous-delivery", "gate_resolution_events.jsonl")
        self.assertTrue(os.path.exists(log_path))
        with open(log_path, "r", encoding="utf-8") as f:
            line = f.readline().strip()
            event = json.loads(line)
            self.assertEqual(event["resolution"], "OUT_OF_SCOPE")

    def test_out_of_scope_path(self):
        save_session_atomic({
            "permission_mode": "full_access",
            "work_item": {"id": "FEAT-115"}
        })
        os.environ["AIWF_ACTIVE_WORK_ITEM"] = "FEAT-115"
        
        # Trying to write to forbidden path outside workspace
        blocked = requires_approval("normal_file_write", path="/etc/hosts")
        self.assertTrue(blocked)

    def test_global_policy_protection(self):
        save_session_atomic({
            "permission_mode": "full_access",
            "work_item": {"id": "FEAT-115"}
        })
        os.environ["AIWF_ACTIVE_WORK_ITEM"] = "FEAT-115"
        
        # Trying to write to AI_RULES.md
        blocked = requires_approval("normal_file_write", path=os.path.abspath("AI_RULES.md"))
        self.assertTrue(blocked)
