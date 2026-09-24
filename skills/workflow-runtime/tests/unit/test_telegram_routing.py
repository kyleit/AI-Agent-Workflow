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
from unittest.mock import patch

from workflow_runtime.infrastructure.telegram import daemon_utils, outbox_sender

# The daemon was split into three modules in v6.20.8. Each module resolves these
# helpers from its own namespace, so a patch applied only to `daemon` left the
# others calling the real functions: the registry and discovered groups were read
# from and written to the real ~/.aiwf, and outbox dispatch made real HTTP calls.
_TELEGRAM_MODULES = (telegram_daemon, daemon_utils, outbox_sender)

class TestTelegramRouting(unittest.TestCase):
    def setUp(self):
        # Create temp folder for registry and test inboxes
        self.temp_dir = Path("scratch") / "test_telegram_tmp"
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self.project_dir = self.temp_dir / "test_project_workspace"
        self.project_dir.mkdir(parents=True, exist_ok=True)
        
        # Isolate every telegram module from the real home directory and network.
        self._patch("get_global_aiwf_dir", lambda: self.temp_dir)
        registry_patch = patch.object(aiwf_registry, "get_registry_dir", lambda: self.temp_dir)
        registry_patch.start()
        self.addCleanup(registry_patch.stop)
        self._patch("send_telegram_reaction", lambda *args, **kwargs: None)
        self._patch("send_telegram_ack", lambda *args, **kwargs: True)
        self._patch("download_telegram_file", lambda *args, **kwargs: False)
        
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
        # Cleanup temp directory
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
            
    def _patch(self, name, value):
        """Patch one helper in every telegram module that holds a reference to it."""
        for module in _TELEGRAM_MODULES:
            if hasattr(module, name):
                helper_patch = patch.object(module, name, value)
                helper_patch.start()
                self.addCleanup(helper_patch.stop)

    def _inbox_file(self):
        # Since v6.20.8 the inbox lives under state/telegram.
        return self.project_dir / ".agents" / "state" / "telegram" / "inbox.json"

    def _outbox_file(self):
        # Since v6.20.8 the outbox lives under state, not beside the inbox.
        return self.project_dir / ".agents" / "state" / "telegram" / "outbox.json"

    def _queue_outbox(self, payload):
        outbox_file = self._outbox_file()
        outbox_file.parent.mkdir(parents=True, exist_ok=True)
        outbox_file.write_text(json.dumps([payload], ensure_ascii=False), encoding="utf-8")
        return outbox_file

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
        inbox_file = self._inbox_file()
        self.assertTrue(inbox_file.exists())
        with open(inbox_file, "r", encoding="utf-8") as f:
            queue = json.load(f)
        self.assertIsInstance(queue, list)
        self.assertEqual(len(queue), 1)
        content = queue[0]
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
        self.assertEqual(groups["-999111"]["title"], "Test Group")

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
        inbox_file = self._inbox_file()
        self.assertTrue(inbox_file.exists())
        with open(inbox_file, "r", encoding="utf-8") as f:
            queue = json.load(f)
        self.assertIsInstance(queue, list)
        self.assertEqual(len(queue), 1)
        content = queue[0]
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
        # Discovered groups became records with a last-seen time in v6.20.8.
        self.assertEqual(groups["-888222"]["title"], "Unlinked Group")

    def test_atomic_writer_replaces_tmp_with_valid_json_object(self):
        inbox_file = self._inbox_file()
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
            queue = json.load(f)
        self.assertIsInstance(queue, list)
        self.assertEqual(len(queue), 1)
        content = queue[0]
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

        inbox_file = self._inbox_file()
        with open(inbox_file, "r", encoding="utf-8") as f:
            queue = json.load(f)
        self.assertIsInstance(queue, list)
        self.assertEqual(len(queue), 1)
        content = queue[0]
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

        inbox_file = self._inbox_file()
        with open(inbox_file, "r", encoding="utf-8") as f:
            queue = json.load(f)
        self.assertIsInstance(queue, list)
        self.assertEqual(len(queue), 1)
        content = queue[0]
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

        self._patch("send_telegram_ack", fake_send)
        payload = daemon_utils.build_outbox_payload(
            "Con đã nhận được tin nhắn từ Telegram.",
            "-888222",
            reply_to_update_id=104,
        )
        outbox_file = self._queue_outbox(payload)

        telegram_daemon.process_project_outboxes("mock_token", "http://proxy.local")

        self.assertEqual(sent, [
            ("mock_token", "-888222", "Con đã nhận được tin nhắn từ Telegram.", "http://proxy.local")
        ])
        # Since v6.20.8 a sent item leaves the queue and is appended to
        # sent_history.jsonl; the queue file is rewritten, not deleted.
        self.assertEqual(json.loads(outbox_file.read_text(encoding="utf-8")), [])
        self.assertFalse(outbox_file.with_name("outbox.json.tmp").exists())
        history = outbox_file.with_name("sent_history.jsonl").read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(history), 1)
        archived = json.loads(history[0])
        self.assertEqual(archived["type"], "TELEGRAM_REPLY")
        self.assertEqual(archived["chat_id"], "-888222")
        self.assertEqual(archived["reply_to_update_id"], 104)
        self.assert_valid_utc_timestamp(archived["sent_at"])

    def test_project_outbox_stays_queued_when_send_fails(self):
        self._patch("send_telegram_ack", lambda *args, **kwargs: False)
        payload = daemon_utils.build_outbox_payload("Retry later", "-999111")
        outbox_file = self._queue_outbox(payload)

        telegram_daemon.process_project_outboxes("mock_token")

        self.assertEqual(json.loads(outbox_file.read_text(encoding="utf-8")), [payload])
        self.assertFalse(outbox_file.with_name("sent_history.jsonl").exists())

    def assert_valid_utc_timestamp(self, value):
        self.assertTrue(value.endswith("Z"))
        datetime.fromisoformat(value.replace("Z", "+00:00"))

if __name__ == "__main__":
    unittest.main()
