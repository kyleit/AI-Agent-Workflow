"""Focused tests for FEAT-616 identity, event durability and WS cursor order."""
from __future__ import annotations

import argparse
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

SCRIPT_ROOT = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_ROOT))

from msgbusws.client.agent_worker import (  # noqa: E402
    AgentWorker,
    WorkerStateStore,
    cmd_agent_run,
)
from msgbusws.client.config import ClientConfig, load_config, validate_conversation  # noqa: E402
from msgbusws.client.event_stream import EventStream  # noqa: E402
from msgbusws.client.ws_client import WsClient  # noqa: E402
from msgbusws.infrastructure import ws_protocol  # noqa: E402


def args(command="daemon", **values):
    defaults = dict(command=command, host=None, port=None, token=None, sender=None,
                    e2ee_key=None, capabilities=None, avatar=None, identity=None,
                    soul=None, machine=None, platform=None, project=None,
                    conversation_id=None, role=None, tls=None)
    defaults.update(values)
    return argparse.Namespace(**defaults)


class FakeSocket:
    def __init__(self, response: bytes) -> None:
        self.response = io.BytesIO(response)
        self.sent = b""
        self.closed = False

    def sendall(self, value: bytes) -> None:
        self.sent += value

    def recv(self, size: int) -> bytes:
        return self.response.read(size)

    def settimeout(self, value) -> None:
        pass

    def close(self) -> None:
        self.closed = True


class PersistentClientTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.config = ClientConfig(
            host="127.0.0.1", port=8787, token="test", sender="route-a",
            e2ee_key=None, capabilities=("test",), machine="machine-a",
            platform="Windows", project="Project-A",
            conversation_id="abcd-one", agent_name="Tester", root=self.root,
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_identity_label_room_and_full_conversation_path(self) -> None:
        self.assertEqual("[Project-A | Windows | #abcd] Tester", self.config.display_label)
        self.assertEqual("build", self.config.room)
        self.assertEqual(self.root / ".agents/state/msgbus/abcd-one", self.config.runtime_dir())

    def test_websocket_accept_key_matches_rfc_6455_vector(self) -> None:
        self.assertEqual(
            "s3pPLMBiTxaQ9kYGzzhZRbK+xOo=",
            ws_protocol.accept_key("dGhlIHNhbXBsZSBub25jZQ=="),
        )

    def test_conversation_rejects_traversal_and_reserved_name(self) -> None:
        for value in ("../escape", "CON", "name/child"):
            with self.assertRaises(ValueError):
                validate_conversation(value)

    def test_config_precedence_and_explicit_false_tls(self) -> None:
        profile = self.root / ".agents/msgbus.json"
        profile.parent.mkdir()
        profile.write_text(json.dumps({"host": "profile", "tls": True,
                                       "capabilities": ["infra"]}))
        env = {"MSGBUS_CONFIG": str(profile), "MSGBUS_HOST": "env",
               "MSGBUS_TLS": "false", "MSGBUS_CONVERSATION_ID": "session-a"}
        with patch.dict(os.environ, env, clear=True), patch("msgbusws.client.config.project_root", return_value=self.root):
            config = load_config(args(host="cli"))
        self.assertEqual("cli", config.host)
        self.assertFalse(config.secure)
        self.assertEqual(("infra",), config.capabilities)

    def test_event_requires_ack_and_release_retries_same_record(self) -> None:
        events = EventStream(self.config.runtime_dir())
        events.append({"seq": 1, "from": "peer", "text": "hello"}, self.config.metadata())
        first = events.claim(lease=10)
        self.assertEqual("busy", events.claim(lease=10)["status"])
        events.acknowledge(first["receipt"], release=True)
        retry = events.claim(lease=10)
        self.assertEqual(first["event"]["event_id"], retry["event"]["event_id"])
        events.acknowledge(retry["receipt"])
        self.assertEqual("empty", events.claim()["status"])

    def test_incomplete_tail_is_not_delivered(self) -> None:
        events = EventStream(self.config.runtime_dir())
        events.path.write_bytes(b'{"seq":1}')
        self.assertEqual("empty", events.claim()["status"])
        with self.assertRaises(ValueError):
            events.resume_sequence()

    def test_worker_filters_self_and_other_target_but_persists_peer(self) -> None:
        events = EventStream(self.config.runtime_dir())
        worker = AgentWorker(self.config, WorkerStateStore(self.config.runtime_dir()), events, silent=True)
        self.assertFalse(worker.handle_record({"seq": 1, "from": "route-a", "text": "self"}))
        self.assertFalse(worker.handle_record({
            "seq": 2, "from": self.config.display_label, "text": "self-label",
        }))
        self.assertFalse(worker.handle_record({"seq": 3, "from": "peer", "to": "other", "text": "other"}))
        self.assertFalse(worker.handle_record({
            "seq": 4, "from": "peer", "text": json.dumps({"type": "heartbeat"}),
        }))
        self.assertFalse(worker.handle_record({
            "seq": 5, "from": "peer", "to": self.config.display_label, "text": "hello",
        }))
        claimed = events.claim()
        self.assertEqual("hello", claimed["event"]["text"])

    def test_daemon_state_dir_owns_store_and_event_stream(self) -> None:
        custom = self.root / "custom-state"
        daemon_args = argparse.Namespace(
            state_dir=str(custom), silent=True, since=0, heartbeat=15.0,
        )
        with patch("msgbusws.client.agent_worker.AgentWorker") as worker_class:
            cmd_agent_run(self.config, daemon_args)

        _, store, events = worker_class.call_args.args
        self.assertEqual(custom, store.root)
        self.assertEqual(custom, events.root)

    def test_daemon_registers_with_canonical_4d_display_name(self) -> None:
        events = EventStream(self.config.runtime_dir())
        worker = AgentWorker(
            self.config, WorkerStateStore(self.config.runtime_dir()), events, silent=True,
        )
        with patch("msgbusws.client.agent_worker.WsClient") as client_class:
            worker.run(heartbeat_interval=15.0)

        self.assertEqual(
            self.config.display_label,
            client_class.return_value.listen.call_args.kwargs["name"],
        )

    def test_ws_cursor_advances_only_after_callback_success(self) -> None:
        payload = json.dumps({"seq": 9, "from": "peer", "text": "x"}).encode()
        stream = io.BytesIO(ws_protocol.encode(payload))
        state = {"seq": 8, "stop": False}
        with self.assertRaises(RuntimeError):
            WsClient(self.config)._pump(None, stream, lambda record: (_ for _ in ()).throw(RuntimeError("disk")), state)
        self.assertEqual(8, state["seq"])

    def test_ws_handshake_contains_4d_metadata_and_checks_accept(self) -> None:
        import base64
        with patch("msgbusws.client.ws_client.os.urandom", return_value=b"a" * 16):
            key = base64.b64encode(b"a" * 16).decode("ascii")
            response = ("HTTP/1.1 101 Switching Protocols\r\nSec-WebSocket-Accept: "
                        + ws_protocol.accept_key(key) + "\r\n\r\n").encode()
            fake = FakeSocket(response)
            with patch("msgbusws.client.ws_client.socket.create_connection", return_value=fake):
                WsClient(self.config)._connect(self.config.sender, 0)
        request_line = fake.sent.split(b"\r\n", 1)[0].decode("ascii")
        query = parse_qs(urlparse(request_line.split()[1]).query)
        self.assertEqual(["Project-A"], query["project"])
        self.assertEqual(["abcd-one"], query["conversation_id"])
        self.assertEqual(["build"], query["room"])


if __name__ == "__main__":
    unittest.main()
