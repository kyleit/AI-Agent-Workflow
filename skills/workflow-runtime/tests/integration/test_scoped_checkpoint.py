# test_scoped_checkpoint.py
import pytest
pytestmark = pytest.mark.integration

import unittest
import os
import sys
import shutil
import json
import uuid

# Add scripts directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "scripts"))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", ".agents", "skills", "workflow-runtime", "scripts")))

from state_store import get_state_store, reset_state_store, get_active_work_item_id, set_active_work_item_id, register_work_item
from session import load_session, save_session_atomic
from checkpoint import validate_checkpoint_level

class TestScopedCheckpoint(unittest.TestCase):
    def setUp(self):
        os.environ["TESTING"] = "1"
        self.test_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "temp_scoped_test"))
        os.makedirs(self.test_dir, exist_ok=True)
        
        # Override state root
        self.original_state_root = os.environ.get("AIWF_STATE_ROOT")
        os.environ["AIWF_STATE_ROOT"] = self.test_dir
        
        # Reset state store to initialize with the new state root
        reset_state_store(None)

        # Create a mock context.json to allow load_session to work
        context_data = {
            "project_id": "test",
            "workspace_path": ".",
            "git": {"is_git_repository": False}
        }
        with open(os.path.join(self.test_dir, "context.json"), "w", encoding="utf-8") as f:
            json.dump(context_data, f)

    def tearDown(self):
        # Restore environment and state store
        if self.original_state_root is not None:
            os.environ["AIWF_STATE_ROOT"] = self.original_state_root
        else:
            os.environ.pop("AIWF_STATE_ROOT", None)
            
        reset_state_store(None)
        
        # Clean up temp files
        if os.path.exists(self.test_dir):
            try:
                shutil.rmtree(self.test_dir)
            except Exception:
                pass

    def test_legacy_state_migration(self):
        # Create legacy state at root
        legacy_data = {
            "checkpoint": 10,
            "active_workflow": "standard-feature",
            "work_item": {"id": "QUICK-999", "type": "QUICK"}
        }
        legacy_path = os.path.join(self.test_dir, "workflow.json")
        with open(legacy_path, "w", encoding="utf-8") as f:
            json.dump(legacy_data, f)

        # Set active work item to QUICK-999
        set_active_work_item_id("QUICK-999")
        
        # Access through state store
        store = get_state_store()
        wf_data = store.get("workflow")
        
        # Verify it automatically migrated the file to scoped directory
        scoped_path = os.path.join(self.test_dir, "work-items", "QUICK-999", "workflow.json")
        self.assertTrue(os.path.exists(scoped_path))
        
        # Verify content is preserved
        self.assertEqual(wf_data.get("checkpoint"), 10)
        self.assertEqual(wf_data.get("active_workflow"), "standard-feature")

    def test_validation_parent_completed_child_active(self):
        # Setup parent state (FEAT-113) completed at checkpoint 10
        store = get_state_store()
        
        # Create parent state file
        parent_dir = os.path.join(self.test_dir, "work-items", "FEAT-113")
        os.makedirs(parent_dir, exist_ok=True)
        parent_data = {
            "checkpoint": 10,
            "active_workflow": "standard-feature",
            "work_item": {"id": "FEAT-113", "type": "FEAT"}
        }
        with open(os.path.join(parent_dir, "workflow.json"), "w", encoding="utf-8") as f:
            json.dump(parent_data, f)
            
        # Register parent
        register_work_item("FEAT-113", workflow_type="standard-feature", status="completed", checkpoint=10)

        # Setup child state (QUICK-009) starting at checkpoint 2
        set_active_work_item_id("QUICK-009")
        register_work_item("QUICK-009", workflow_type="quick-feature", status="active", checkpoint=2, parent_workflow_id="FEAT-113")
        save_session_atomic({"parent_workflow_id": "FEAT-113"})
        
        # Verify session loads correctly for child
        session = load_session()
        self.assertEqual(session.get("checkpoint"), 2)
        self.assertEqual(session.get("parent_workflow_id"), "FEAT-113")
        self.assertEqual(session.get("work_item", {}).get("id"), "QUICK-009")

        # Validate checkpoint level: child requires exactly 2 (as initialized)
        # Before this fix, this would fail because the legacy global state remained 10
        validate_checkpoint_level(2, "exactly 2") # Should PASS without exceptions

        # Re-check parent state directly to ensure it remains completed at checkpoint 10
        reset_state_store(None)
        set_active_work_item_id("FEAT-113")
        parent_session = load_session()
        self.assertEqual(parent_session.get("checkpoint"), 10)

    def test_concurrent_independent_workflows(self):
        # Initialize two concurrent workflows
        set_active_work_item_id("QUICK-001")
        register_work_item("QUICK-001", workflow_type="quick-feature", status="active", checkpoint=2)
        save_session_atomic(load_session())
        
        set_active_work_item_id("QUICK-002")
        register_work_item("QUICK-002", workflow_type="quick-feature", status="active", checkpoint=2)
        save_session_atomic(load_session())

        # Advance QUICK-001 to checkpoint 3
        set_active_work_item_id("QUICK-001")
        session1 = load_session()
        session1["checkpoint"] = 3
        save_session_atomic(session1)

        # Re-check QUICK-002 state, it should remain at checkpoint 2
        set_active_work_item_id("QUICK-002")
        session2 = load_session()
        self.assertEqual(session2.get("checkpoint"), 2)

        # Re-check QUICK-001 state, it should be at checkpoint 3
        set_active_work_item_id("QUICK-001")
        session1_reloaded = load_session()
        self.assertEqual(session1_reloaded.get("checkpoint"), 3)
