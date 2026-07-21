# skills/workflow-runtime/tests/unit/test_telegram_routing.py
import os
import sys
import json
import shutil
import unittest
from pathlib import Path
from datetime import datetime

# Add script directory to sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "scripts"))
import telegram_daemon
import aiwf_registry

class TestTelegramRouting(unittest.TestCase):
    def setUp(self):
        # Create temp folder for registry and test inboxes
        self.temp_dir = Path("scratch") / "test_telegram_tmp"
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self.project_dir = self.temp_dir / "test_project_workspace"
        self.project_dir.mkdir(parents=True, exist_ok=True)
        
        # Mock global dir and registry path functions in daemon and registry
        self.original_global_dir = telegram_daemon.get_global_aiwf_dir
        self.original_registry_dir = telegram_daemon.get_registry_dir
        self.original_registry_dir_reg = aiwf_registry.get_registry_dir
        self.original_send_reaction = telegram_daemon.send_telegram_reaction
        self.original_send_ack = telegram_daemon.send_telegram_ack
        self.original_download_file = telegram_daemon.download_telegram_file
        
        telegram_daemon.get_global_aiwf_dir = lambda: self.temp_dir
        telegram_daemon.get_registry_dir = lambda: self.temp_dir
        aiwf_registry.get_registry_dir = lambda: self.temp_dir
        telegram_daemon.send_telegram_reaction = lambda *args, **kwargs: None
        telegram_daemon.send_telegram_ack = lambda *args, **kwargs: True
        telegram_daemon.download_telegram_file = lambda *args, **kwargs: False
        
        # Initialize empty projects registry
        self.registry_data = {
            "schema_version": 1,
            "projects": [
                {
                    "id": "test_proj_id",
                    "path": str(self.project_dir.resolve()),
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
        telegram_daemon.send_telegram_reaction = self.original_send_reaction
        telegram_daemon.send_telegram_ack = self.original_send_ack
        telegram_daemon.download_telegram_file = self.original_download_file
        
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
        inbox_file = self.project_dir / ".agents" / "inbox" / "inbox.json"
        self.assertTrue(inbox_file.exists())
        with open(inbox_file, "r", encoding="utf-8") as f:
            content = json.load(f)
        self.assertEqual(content["type"], "MESSAGE_RECEIVED")
        self.assertEqual(content["content"], "Hello Agent!")
        self.assertEqual(content["update_id"], 100)
        self.assertEqual(content["chat_id"], "-999111")
        self.assert_valid_utc_timestamp(content["timestamp"])
        self.assertFalse(inbox_file.with_name("inbox.json.tmp").exists())
        
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
        inbox_file = self.project_dir / ".agents" / "inbox" / "inbox.json"
        self.assertTrue(inbox_file.exists())
        with open(inbox_file, "r", encoding="utf-8") as f:
            content = json.load(f)
        self.assertEqual(content["type"], "MESSAGE_RECEIVED")
        self.assertEqual(content["content"], "Hello by prefix")
        self.assertEqual(content["update_id"], 101)
        self.assertEqual(content["chat_id"], "-888222")
        self.assert_valid_utc_timestamp(content["timestamp"])
        
        # Group -888222 should be discovered
        disc_file = self.temp_dir / "discovered_groups.json"
        with open(disc_file, "r", encoding="utf-8") as f:
            groups = json.load(f)
        self.assertIn("-888222", groups)
        self.assertEqual(groups["-888222"], "Unlinked Group")

    def test_atomic_writer_replaces_tmp_with_valid_json_object(self):
        inbox_file = self.project_dir / ".agents" / "inbox" / "inbox.json"
        payload = telegram_daemon.build_inbox_payload(
            "FILE_RECEIVED",
            ".agents/inbox/files/123_report.md",
            123,
            "-999111",
        )

        telegram_daemon.write_inbox_payload_atomic(inbox_file, payload)

        self.assertTrue(inbox_file.exists())
        self.assertFalse(inbox_file.with_name("inbox.json.tmp").exists())
        with open(inbox_file, "r", encoding="utf-8") as f:
            content = json.load(f)
        self.assertEqual(content, payload)
        self.assert_valid_utc_timestamp(content["timestamp"])

    def test_photo_download_failure_writes_json_event(self):
        update = {
            "update_id": 102,
            "message": {
                "chat": {
                    "id": -999111,
                    "type": "group",
                    "title": "Test Group"
                },
                "photo": [
                    {"file_id": "small_photo"},
                    {"file_id": "large_photo"}
                ]
            }
        }

        telegram_daemon.route_update("mock_token", update)

        inbox_file = self.project_dir / ".agents" / "inbox" / "inbox.json"
        with open(inbox_file, "r", encoding="utf-8") as f:
            content = json.load(f)
        self.assertEqual(content["type"], "PHOTO_DOWNLOAD_FAILED")
        self.assertEqual(content["content"], "large_photo")
        self.assertEqual(content["update_id"], 102)
        self.assertEqual(content["chat_id"], "-999111")
        self.assert_valid_utc_timestamp(content["timestamp"])

    def test_document_download_failure_writes_json_event(self):
        update = {
            "update_id": 103,
            "message": {
                "chat": {
                    "id": -999111,
                    "type": "group",
                    "title": "Test Group"
                },
                "document": {
                    "file_id": "document_file",
                    "file_name": "report.md"
                }
            }
        }

        telegram_daemon.route_update("mock_token", update)

        inbox_file = self.project_dir / ".agents" / "inbox" / "inbox.json"
        with open(inbox_file, "r", encoding="utf-8") as f:
            content = json.load(f)
        self.assertEqual(content["type"], "FILE_DOWNLOAD_FAILED")
        self.assertEqual(content["content"], "document_file")
        self.assertEqual(content["update_id"], 103)
        self.assertEqual(content["chat_id"], "-999111")
        self.assert_valid_utc_timestamp(content["timestamp"])

    def test_project_outbox_is_sent_and_archived_by_daemon(self):
        sent = []

        def fake_send(token, chat_id, text, proxy=None):
            sent.append((token, chat_id, text, proxy))
            return True

        telegram_daemon.send_telegram_ack = fake_send
        outbox_file = self.project_dir / ".agents" / "inbox" / "outbox.json"
        payload = telegram_daemon.build_outbox_payload(
            "Con đã nhận được tin nhắn từ Telegram.",
            "-888222",
            reply_to_update_id=104,
        )
        telegram_daemon.write_outbox_payload_atomic(outbox_file, payload)

        telegram_daemon.process_project_outboxes("mock_token", "http://proxy.local")

        self.assertEqual(sent, [
            ("mock_token", "-888222", "Con đã nhận được tin nhắn từ Telegram.", "http://proxy.local")
        ])
        self.assertFalse(outbox_file.exists())
        self.assertFalse(outbox_file.with_name("outbox.json.tmp").exists())
        sent_file = outbox_file.with_name("outbox.sent.json")
        self.assertTrue(sent_file.exists())
        with open(sent_file, "r", encoding="utf-8") as f:
            archived = json.load(f)
        self.assertEqual(archived["type"], "TELEGRAM_REPLY")
        self.assertEqual(archived["chat_id"], "-888222")
        self.assertEqual(archived["reply_to_update_id"], 104)
        self.assert_valid_utc_timestamp(archived["sent_at"])

    def test_project_outbox_stays_queued_when_send_fails(self):
        telegram_daemon.send_telegram_ack = lambda *args, **kwargs: False
        outbox_file = self.project_dir / ".agents" / "inbox" / "outbox.json"
        payload = telegram_daemon.build_outbox_payload("Retry later", "-999111")
        telegram_daemon.write_outbox_payload_atomic(outbox_file, payload)

        telegram_daemon.process_project_outboxes("mock_token")

        self.assertTrue(outbox_file.exists())
        self.assertFalse(outbox_file.with_name("outbox.sent.json").exists())

    def assert_valid_utc_timestamp(self, value):
        self.assertTrue(value.endswith("Z"))
        datetime.fromisoformat(value.replace("Z", "+00:00"))

if __name__ == "__main__":
    unittest.main()
