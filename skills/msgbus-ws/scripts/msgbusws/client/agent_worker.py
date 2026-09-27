"""Persistent MsgBus network daemon plus backward-compatible task lifecycle."""
from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import cast

from .config import ClientConfig, build_cipher
from .event_stream import EventStream, ProcessLock, atomic_json, read_json
from .rest_client import RestClient
from .ws_client import WsClient

STATE_SCHEMA = "aiwf.msgbus-agent-state/2"
ASSIGNMENT_SCHEMA = "aiwf.msgbus-agent-assignment/1"
FINAL_STATUSES = {"completed", "failed", "cancelled"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class WorkerStateStore:
    """Conversation-scoped assignment inbox sharing state.json with the daemon."""

    def __init__(self, root: Path, worker_name: str = "") -> None:
        self.root = root
        self.state_path = root / "state.json"
        self.inbox_path = root / "inbox.jsonl"
        self.lock = ProcessLock(root / ".state.lock")
        root.mkdir(parents=True, exist_ok=True, mode=0o700)

    @staticmethod
    def _empty() -> dict:
        return {
            "schema": STATE_SCHEMA, "assignment_cursor": 0, "cursor": 0,
            "status": "idle",
            "current_task": None, "seen_task_ids": [], "pending": [],
            "updated_at": _now(),
        }

    def load(self) -> dict:
        payload = read_json(self.state_path, self._empty())
        if payload.get("schema") not in (None, STATE_SCHEMA):
            raise ValueError("Unsupported MsgBus worker state schema")
        baseline = self._empty()
        baseline.update(payload)
        return baseline

    def _write(self, state: dict) -> None:
        state["schema"] = STATE_SCHEMA
        state["updated_at"] = _now()
        atomic_json(self.state_path, state)

    def record_cursor(self, sequence: int) -> None:
        with self.lock:
            state = self.load()
            state["assignment_cursor"] = max(int(state["assignment_cursor"]), sequence)
            state["cursor"] = state["assignment_cursor"]
            self._write(state)

    def enqueue(self, assignment: dict, record: dict) -> bool:
        task = assignment.get("task")
        if not isinstance(task, dict):
            return False
        task_id = str(task.get("id") or task.get("task_id") or "").strip()
        if not task_id:
            return False
        with self.lock:
            state = self.load()
            seen = [str(item) for item in state["seen_task_ids"]]
            state["assignment_cursor"] = max(int(state["assignment_cursor"]), int(record["seq"]))
            state["cursor"] = state["assignment_cursor"]
            if task_id in seen:
                self._write(state)
                return False
            row = {
                "schema": ASSIGNMENT_SCHEMA, "task_id": task_id,
                "sequence": int(record["seq"]),
                "workflow_id": str(assignment.get("workflow_id", "")),
                "workflow_title": str(assignment.get("workflow_title", "")),
                "objective": str(assignment.get("objective", "")),
                "task": task, "collaboration": assignment.get("collaboration", {}),
                "received_at": _now(), "claim_status": "queued",
                "result_status": "assigned", "output": "",
            }
            with self.inbox_path.open("a", encoding="utf-8", newline="\n") as stream:
                os.chmod(self.inbox_path, 0o600)
                stream.write(json.dumps(row, ensure_ascii=False) + "\n")
                stream.flush()
                os.fsync(stream.fileno())
            state["pending"].append(row)
            state["seen_task_ids"] = (seen + [task_id])[-512:]
            state["status"] = "ready"
            self._write(state)
            return True

    def claim_next(self) -> dict | None:
        with self.lock:
            state = self.load()
            for item in state["pending"]:
                if item.get("claim_status") == "queued":
                    item["claim_status"] = "claimed"
                    item["claimed_at"] = _now()
                    state["current_task"] = item["task_id"]
                    state["status"] = "working"
                    self._write(state)
                    return item
            return None

    def update_task(self, task_id: str, status: str, output: str = "") -> dict:
        with self.lock:
            state = self.load()
            found = False
            for item in state["pending"]:
                if str(item.get("task_id")) == task_id:
                    found = True
                    item.update(result_status=status, output=output, updated_at=_now())
            if not found:
                raise ValueError("Unknown local task ID")
            if status in FINAL_STATUSES:
                state.update(current_task=None, status="idle")
            else:
                state.update(current_task=task_id, status="working")
            self._write(state)
            return state

    def snapshot(self) -> dict:
        with self.lock:
            return self.load()


class AgentWorker:
    """Own one durable receive socket and expose local events to a dispatcher."""

    def __init__(self, config: ClientConfig, store: WorkerStateStore,
                 event_stream: EventStream | None = None,
                 rest_client: RestClient | None = None, silent: bool = False) -> None:
        if event_stream is not None and not isinstance(event_stream, EventStream):
            if not hasattr(event_stream, "task_update") or rest_client is not None:
                raise TypeError("Third argument must be EventStream or a legacy RestClient")
            rest_client = cast(RestClient, event_stream)
            event_stream = None
        self.config = config
        self.store = store
        events_root = config.runtime_dir() if config.conversation_id else store.root
        self.events = event_stream or EventStream(events_root)
        self.rest = rest_client or RestClient(config)
        self.cipher = build_cipher(config)
        self.silent = silent
        self._send_event = None

    def heartbeat_payload(self) -> dict:
        state = self.store.snapshot()
        return {"type": "heartbeat", "status": state["status"],
                "current_task": state["current_task"]}

    def on_connected(self, send_event) -> None:
        self._send_event = send_event
        send_event(self.heartbeat_payload())
        if not self.silent:
            ready = {"type": "agent_ready", "agent": self.config.sender,
                     "display_label": self.config.display_label,
                     "status": self.store.snapshot()["status"]}
            send_event({"to": "coordinator", "text": json.dumps(ready)})

    def _is_local_name(self, value: object) -> bool:
        return str(value) in {self.config.sender, self.config.display_label}

    def handle_record(self, record: dict) -> bool:
        try:
            if self._is_local_name(record.get("from", "")):
                return False
            target = str(record.get("to", "") or "")
            if target and not self._is_local_name(target):
                return False
            decoded = self.cipher.decrypt(str(record.get("text", "")))
            if decoded.startswith("[encrypted:"):
                print(json.dumps({"event": "message_decode_error", "seq": record["seq"]}), flush=True)
                return False
            try:
                control = json.loads(decoded)
            except (TypeError, ValueError):
                control = None
            if isinstance(control, dict) and control.get("type") == "heartbeat":
                return False
            durable = {**record, "text": decoded}
            self.events.append(durable, self.config.metadata())
        except OSError as exc:
            raise RuntimeError(f"Cannot persist MsgBus event: {type(exc).__name__}") from exc
        self._handle_assignment(durable)
        return False

    def _handle_assignment(self, record: dict) -> None:
        try:
            assignment = json.loads(record["text"])
        except (ValueError, TypeError):
            return
        if not isinstance(assignment, dict) or assignment.get("type") != "task_assignment":
            return
        task = assignment.get("task")
        if not isinstance(task, dict) or not self._is_local_name(task.get("agent", "")):
            return
        if not self.store.enqueue(assignment, record):
            return
        task_id = str(task.get("id") or task.get("task_id"))
        try:
            self.rest.task_update(task_id, "running", "accepted by autonomous agent worker")
            self.store.update_task(task_id, "running")
        except OSError as exc:
            print(json.dumps({"event": "task_status_error", "task_id": task_id,
                              "error": type(exc).__name__}), flush=True)
            return
        if self._send_event is not None:
            ack = {"type": "task_ack", "task_id": task_id,
                   "agent": self.config.sender, "sequence": record["seq"]}
            self._send_event({"to": "coordinator", "text": json.dumps(ack)})
            self._send_event(self.heartbeat_payload())
        print(json.dumps({"event": "task_assignment", "task_id": task_id}), flush=True)

    def run(self, since: int = 0, heartbeat_interval: float = 15.0) -> None:
        identity = {"project": self.config.project,
                    "conversation_id": self.config.conversation_id,
                    "agent_name": self.config.agent_name,
                    "machine": self.config.machine}
        self.events.bind(identity)
        with ProcessLock(self.events.root / ".daemon.lock", timeout=0.1):
            cursor = max(since, self.events.resume_sequence())
            WsClient(self.config).listen(
                self.handle_record, since=cursor, name=self.config.display_label,
                on_connected=self.on_connected,
                heartbeat_factory=self.heartbeat_payload,
                heartbeat_interval=heartbeat_interval,
            )


def worker_store(config: ClientConfig, state_dir: str | None = None) -> WorkerStateStore:
    return WorkerStateStore(Path(state_dir) if state_dir else config.runtime_dir())


def cmd_agent_run(config: ClientConfig, args) -> None:
    root = Path(args.state_dir) if getattr(args, "state_dir", None) else config.runtime_dir()
    worker = AgentWorker(
        config,
        WorkerStateStore(root),
        EventStream(root),
        silent=bool(getattr(args, "silent", False)),
    )
    worker.run(args.since, args.heartbeat)


def cmd_pop_event(config: ClientConfig, args) -> None:
    events = EventStream(Path(args.state_dir) if args.state_dir else config.runtime_dir())
    deadline = time.monotonic() + max(0.0, args.wait)
    while True:
        result = events.claim(args.lease)
        if result["status"] != "empty" or time.monotonic() >= deadline:
            print(json.dumps(result, ensure_ascii=False))
            return
        time.sleep(0.25)


def cmd_ack_event(config: ClientConfig, args) -> None:
    events = EventStream(Path(args.state_dir) if args.state_dir else config.runtime_dir())
    print(json.dumps(events.acknowledge(args.receipt)))


def cmd_release_event(config: ClientConfig, args) -> None:
    events = EventStream(Path(args.state_dir) if args.state_dir else config.runtime_dir())
    print(json.dumps(events.acknowledge(args.receipt, release=True)))


def cmd_agent_next(config: ClientConfig, args) -> None:
    store = worker_store(config, getattr(args, "state_dir", None))
    deadline = time.monotonic() + max(0.0, float(args.wait))
    while True:
        assignment = store.claim_next()
        if assignment is not None:
            print(json.dumps(assignment, ensure_ascii=False))
            return
        if time.monotonic() >= deadline:
            print(json.dumps({"status": "empty"}))
            return
        time.sleep(0.25)


def cmd_agent_status(config: ClientConfig, args) -> None:
    print(json.dumps(worker_store(config, getattr(args, "state_dir", None)).snapshot(), ensure_ascii=False))


def cmd_task_update(config: ClientConfig, args) -> None:
    remote = RestClient(config).task_update(args.task_id, args.status, args.output)
    worker_store(config, getattr(args, "state_dir", None)).update_task(args.task_id, args.status, args.output)
    print(json.dumps(remote, ensure_ascii=False))
