# test_blueprint_enforcement.py
import os
import sys
import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "skills", "workflow-coordinator", "scripts")))
from coordinator import WorkflowCoordinator

class TestBlueprintEnforcement(unittest.TestCase):
    @patch("coordinator.get_state_store")
    def test_verify_blueprint_gate(self, mock_get_store):
        with tempfile.TemporaryDirectory() as tmp:
            bp_path = Path(tmp) / "docs/features/desktop-app/blueprints/FEAT-408_aiwf_desktop_app_blueprint.md"
            bp_path.parent.mkdir(parents=True)
            bp_path.write_text("---\nfeature_id: FEAT-408\n---\n# Blueprint\n", encoding="utf-8")

            mock_store = MagicMock()
            mock_store.get.return_value = {
                "blueprint": {
                    "path": "docs/features/desktop-app/blueprints/FEAT-408_aiwf_desktop_app_blueprint.md",
                    "exists": True,
                    "approved": True,
                    "work_item_id": "FEAT-408"
                }
            }
            mock_get_store.return_value = mock_store

            coord = WorkflowCoordinator(workspace_root=tmp)
            self.assertTrue(coord._verify_blueprint_gate("FEAT-408"))
        
    @patch("coordinator.get_state_store")
    def test_verify_blueprint_gate_false(self, mock_get_store):
        mock_store = MagicMock()
        mock_store.get.return_value = {
            "blueprint": {
                "approved": False
            }
        }
        mock_get_store.return_value = mock_store
        
        coord = WorkflowCoordinator()
        self.assertFalse(coord._verify_blueprint_gate("FEAT-404"))

    @patch("coordinator.get_state_store")
    def test_verify_blueprint_gate_rejects_cross_work_item_approval(self, mock_get_store):
        with tempfile.TemporaryDirectory() as tmp:
            bp_path = Path(tmp) / "docs/features/desktop-app/blueprints/FEAT-408_aiwf_desktop_app_blueprint.md"
            bp_path.parent.mkdir(parents=True)
            bp_path.write_text("---\nfeature_id: FEAT-408\n---\n# Blueprint\n", encoding="utf-8")

            mock_store = MagicMock()
            mock_store.get.return_value = {
                "blueprint": {
                    "path": "docs/features/desktop-app/blueprints/FEAT-408_aiwf_desktop_app_blueprint.md",
                    "exists": True,
                    "approved": True,
                    "work_item_id": "FIX-419"
                }
            }
            mock_get_store.return_value = mock_store

            coord = WorkflowCoordinator(workspace_root=tmp)
            self.assertFalse(coord._verify_blueprint_gate("FIX-419"))

if __name__ == "__main__":
    unittest.main()
