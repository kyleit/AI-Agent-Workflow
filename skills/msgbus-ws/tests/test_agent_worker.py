"""Tests for durable autonomous MsgBus Agent worker behavior."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT_ROOT = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_ROOT))

from msgbusws.client.agent_worker import AgentWorker, WorkerStateStore
from msgbusws.client.config import ClientConfig


class FakeRestClient:
    def __init__(self) -> None:
        self.updates: list[tuple[str, str, str]] = []

    def task_update(self, task_id: str, status: str, output: str = "") -> dict:
        self.updates.append((task_id, status, output))
        return {"task_id": task_id, "status": status}


def assignment_record(sequence: int = 7, target: str = "Agent A") -> dict:
    payload = {
        "type": "task_assignment",
        "workflow_id": "flow-1",
        "workflow_title": "Build feature",
        "objective": "Collaborate with another Agent",
        "task": {
            "id": "task-1",
            "agent": target,
            "title": "Implement client",
            "instructions": "Change only the assigned files and report evidence.",
        },
        "collaboration": {
            "agents": ["Agent A", "Agent B"],
            "handoff_to": "Agent B",
        },
    }
    return {
        "seq": sequence,
        "from": "coordinator",
        "to": target,
        "text": json.dumps(payload),
    }


class AgentWorkerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.config = ClientConfig(
            host="127.0.0.1",
            port=8787,
            token="test-token",
            sender="Agent A",
            e2ee_key=None,
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_duplicate_assignment_is_not_enqueued_twice(self) -> None:
        store = WorkerStateStore(self.root, self.config.sender)
        rest = FakeRestClient()
        worker = AgentWorker(self.config, store, rest)
        worker.handle_record(assignment_record())
        worker.handle_record(assignment_record())
        state = store.snapshot()
        self.assertEqual(1, len(state["pending"]))
        self.assertEqual(1, len(rest.updates))

    def test_wrong_target_is_not_actionable(self) -> None:
        store = WorkerStateStore(self.root, self.config.sender)
        rest = FakeRestClient()
        worker = AgentWorker(self.config, store, rest)
        worker.handle_record(assignment_record(target="Agent B"))
        self.assertEqual([], store.snapshot()["pending"])
        self.assertEqual([], rest.updates)

    def test_cursor_survives_store_restart(self) -> None:
        first = WorkerStateStore(self.root, self.config.sender)
        first.record_cursor(41)
        second = WorkerStateStore(self.root, self.config.sender)
        self.assertEqual(41, second.snapshot()["cursor"])

    def test_claim_marks_current_task(self) -> None:
        store = WorkerStateStore(self.root, self.config.sender)
        payload = json.loads(assignment_record()["text"])
        self.assertTrue(store.enqueue(payload, assignment_record()))
        claimed = store.claim_next()
        self.assertIsNotNone(claimed)
        self.assertEqual("task-1", store.snapshot()["current_task"])

    def test_final_update_returns_worker_to_idle(self) -> None:
        store = WorkerStateStore(self.root, self.config.sender)
        payload = json.loads(assignment_record()["text"])
        store.enqueue(payload, assignment_record())
        store.claim_next()
        state = store.update_task("task-1", "completed", "verified")
        self.assertEqual("idle", state["status"])
        self.assertIsNone(state["current_task"])

    def test_assignment_sends_ack_and_running_status(self) -> None:
        store = WorkerStateStore(self.root, self.config.sender)
        rest = FakeRestClient()
        worker = AgentWorker(self.config, store, rest)
        events: list[dict] = []
        worker.on_connected(events.append)
        worker.handle_record(assignment_record())
        self.assertEqual("running", rest.updates[0][1])
        decoded = [json.loads(event["text"]) for event in events if "text" in event]
        self.assertTrue(any(event.get("type") == "task_ack" for event in decoded))


if __name__ == "__main__":
    unittest.main()
