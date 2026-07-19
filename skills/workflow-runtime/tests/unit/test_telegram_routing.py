# skills/workflow-runtime/tests/unit/test_telegram_routing.py
import os
import sys
import json
import shutil
import unittest
from pathlib import Path

# Add script directory to sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "scripts"))
import telegram_daemon
import aiwf_registry

class TestTelegramRouting(unittest.TestCase):
    def setUp(self):
        # Create temp folder for registry and test inboxes
        self.temp_dir = Path("scratch") / "test_telegram_tmp"
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
        # Mock global dir and registry path functions in daemon and registry
        self.original_global_dir = telegram_daemon.get_global_aiwf_dir
        self.original_registry_dir = telegram_daemon.get_registry_dir
        self.original_registry_dir_reg = aiwf_registry.get_registry_dir
        
        telegram_daemon.get_global_aiwf_dir = lambda: self.temp_dir
        telegram_daemon.get_registry_dir = lambda: self.temp_dir
        aiwf_registry.get_registry_dir = lambda: self.temp_dir
        
        # Initialize empty projects registry
        self.registry_data = {
            "schema_version": 1,
            "projects": [
                {
                    "id": "test_proj_id",
                    "path": str(Path("e:/test_proj").resolve()),
                    "name": "test-project",
                    "telegram_chat_id": "-999111",
                    "status": "active"
                }
            ]
        }
        with open(self.temp_dir / "projects.json", "w", encoding="utf-8") as f:
            json.dump(self.registry_data, f)
            
    def tearDown(self):
        # Restore functions
        telegram_daemon.get_global_aiwf_dir = self.original_global_dir
        telegram_daemon.get_registry_dir = self.original_registry_dir
        aiwf_registry.get_registry_dir = self.original_registry_dir_reg
        
        # Cleanup temp directory
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
            
    def test_routing_by_chat_id(self):
        # Mock Telegram Update for direct chat match
        update = {
            "update_id": 100,
            "message": {
                "chat": {
                    "id": -999111,
                    "type": "group",
                    "title": "Test Group"
                },
                "text": "Hello Agent!"
            }
        }
        
        # Perform routing
        telegram_daemon.route_update("mock_token", update)
        
        # Verify inbox file creation and contents
        inbox_file = self.temp_dir / "test_project" / "inbox.json"
        self.assertTrue(inbox_file.exists())
        with open(inbox_file, "r", encoding="utf-8") as f:
            content = f.read().strip()
        self.assertEqual(content, "MESSAGE_RECEIVED: Hello Agent!")
        
        # Verify group discovery
        disc_file = self.temp_dir / "discovered_groups.json"
        self.assertTrue(disc_file.exists())
        with open(disc_file, "r", encoding="utf-8") as f:
            groups = json.load(f)
        self.assertIn("-999111", groups)
        self.assertEqual(groups["-999111"], "Test Group")

    def test_routing_by_prefix_fallback(self):
        # Mock Telegram Update with prefix /test_project from non-linked chat
        update = {
            "update_id": 101,
            "message": {
                "chat": {
                    "id": -888222,
                    "type": "group",
                    "title": "Unlinked Group"
                },
                "text": "/test_project Hello by prefix"
            }
        }
        
        telegram_daemon.route_update("mock_token", update)
        
        # Inbox should be created under test_project
        inbox_file = self.temp_dir / "test_project" / "inbox.json"
        self.assertTrue(inbox_file.exists())
        with open(inbox_file, "r", encoding="utf-8") as f:
            content = f.read().strip()
        self.assertEqual(content, "MESSAGE_RECEIVED: Hello by prefix")
        
        # Group -888222 should be discovered
        disc_file = self.temp_dir / "discovered_groups.json"
        with open(disc_file, "r", encoding="utf-8") as f:
            groups = json.load(f)
        self.assertIn("-888222", groups)
        self.assertEqual(groups["-888222"], "Unlinked Group")

if __name__ == "__main__":
    unittest.main()
