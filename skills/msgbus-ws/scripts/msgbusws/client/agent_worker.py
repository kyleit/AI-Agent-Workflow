"""Durable application service for an autonomous MsgBus Agent worker."""
from __future__ import annotations

import json
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock

from .config import ClientConfig, build_cipher
from .rest_client import RestClient
from .ws_client import WsClient

STATE_SCHEMA = "aiwf.msgbus-agent-state/1"
ASSIGNMENT_SCHEMA = "aiwf.msgbus-agent-assignment/1"
FINAL_STATUSES = {"completed", "failed", "cancelled"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_name(value: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9_.-]+", "-", value.strip()).strip("-.")
    return normalized[:80] or "agent"


class WorkerStateStore:
    """Atomic identity-scoped cursor, inbox, and task lifecycle store."""

    def __init__(self, root: Path, worker_name: str) -> None:
        self.root = root / _safe_name(worker_name)
        self.state_path = self.root / "state.json"
        self.inbox_path = self.root / "assignments.jsonl"
        self._lock = RLock()
        self.root.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _empty() -> dict:
        return {
            "schema": STATE_SCHEMA,
            "cursor": 0,
            "status": "idle",
            "current_task": None,
            "seen_task_ids": [],
            "pending": [],
            "updated_at": _now(),
        }

    def load(self) -> dict:
        with self._lock:
            try:
                payload = json.loads(self.state_path.read_text(encoding="utf-8"))
            except (OSError, ValueError, TypeError):
                return self._empty()
            if not isinstance(payload, dict) or payload.get("schema") != STATE_SCHEMA:
                return self._empty()
            baseline = self._empty()
            baseline.update(payload)
            return baseline

    def _write(self, state: dict) -> None:
        state["schema"] = STATE_SCHEMA
        state["updated_at"] = _now()
        temporary = self.state_path.with_suffix(".tmp")
        temporary.write_text(
            json.dumps(state, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        os.replace(temporary, self.state_path)

    def record_cursor(self, sequence: int) -> None:
        with self._lock:
            state = self.load()
            state["cursor"] = max(int(state.get("cursor", 0)), int(sequence))
            self._write(state)

    def enqueue(self, assignment: dict, record: dict) -> bool:
        task = assignment.get("task")
        if not isinstance(task, dict):
            return False
        task_id = str(task.get("id") or task.get("task_id") or "").strip()
        if not task_id:
            return False
        with self._lock:
            state = self.load()
            seen = [str(item) for item in state.get("seen_task_ids", [])]
            state["cursor"] = max(
                int(state.get("cursor", 0)),
                int(record.get("seq", 0) or 0),
            )
            if task_id in seen:
                self._write(state)
                return False
            row = {
                "schema": ASSIGNMENT_SCHEMA,
                "task_id": task_id,
                "sequence": int(record.get("seq", 0) or 0),
                "workflow_id": str(assignment.get("workflow_id", "")),
                "workflow_title": str(assignment.get("workflow_title", "")),
                "objective": str(assignment.get("objective", "")),
                "task": task,
                "collaboration": assignment.get("collaboration", {}),
                "received_at": _now(),
                "claim_status": "queued",
                "result_status": "assigned",
                "output": "",
            }
            with self.inbox_path.open("a", encoding="utf-8", newline="\n") as stream:
                stream.write(json.dumps(row, ensure_ascii=False) + "\n")
                stream.flush()
                os.fsync(stream.fileno())
            pending = list(state.get("pending", []))
            pending.append(row)
            state["pending"] = pending
            state["seen_task_ids"] = (seen + [task_id])[-512:]
            state["status"] = "ready"
            self._write(state)
            return True

    def claim_next(self) -> dict | None:
        with self._lock:
            state = self.load()
            pending = list(state.get("pending", []))
            for item in pending:
                if item.get("claim_status") != "queued":
                    continue
                item["claim_status"] = "claimed"
                item["claimed_at"] = _now()
                task_id = str(item.get("task_id", ""))
                state["current_task"] = task_id
                state["status"] = "working"
                state["pending"] = pending
                self._write(state)
                return item
            return None

    def update_task(self, task_id: str, status: str, output: str = "") -> dict:
        with self._lock:
            state = self.load()
            pending = list(state.get("pending", []))
            for item in pending:
                if str(item.get("task_id")) == task_id:
                    item["result_status"] = status
                    item["output"] = output
                    item["updated_at"] = _now()
            if status in FINAL_STATUSES:
                state["current_task"] = None
                state["status"] = "idle"
            else:
                state["current_task"] = task_id
                state["status"] = "working"
            state["pending"] = pending
            self._write(state)
            return state

    def snapshot(self) -> dict:
        return self.load()


class AgentWorker:
    """Validate, persist, acknowledge, and expose targeted assignments."""

    def __init__(
        self,
        config: ClientConfig,
        store: WorkerStateStore,
        rest_client: RestClient | None = None,
    ) -> None:
        self.config = config
        self.store = store
        self.rest = rest_client or RestClient(config)
        self.cipher = build_cipher(config)
        self._send_event = None

    def heartbeat_payload(self) -> dict:
        state = self.store.snapshot()
        return {
            "type": "heartbeat",
            "status": state.get("status", "idle"),
            "current_task": state.get("current_task"),
        }

    def on_connected(self, send_event) -> None:
        self._send_event = send_event
        send_event(self.heartbeat_payload())
        ready = {
            "type": "agent_ready",
            "agent": self.config.sender,
            "status": self.store.snapshot().get("status", "idle"),
        }
        send_event({"to": "coordinator", "text": json.dumps(ready)})

    def handle_record(self, record: dict) -> bool:
        sequence = int(record.get("seq", 0) or 0)
        self.store.record_cursor(sequence)
        target = str(record.get("to", "") or "")
        if target != self.config.sender:
            return False
        try:
            decoded = self.cipher.decrypt(str(record.get("text", "")))
            assignment = json.loads(decoded)
        except (ValueError, TypeError):
            return False
        if not isinstance(assignment, dict) or assignment.get("type") != "task_assignment":
            return False
        task = assignment.get("task")
        if not isinstance(task, dict) or str(task.get("agent", "")) != self.config.sender:
            return False
        if not self.store.enqueue(assignment, record):
            return False
        task_id = str(task.get("id") or task.get("task_id") or "")
        if not task_id:
            return False
        try:
            self.rest.task_update(task_id, "running", "accepted by autonomous agent worker")
        except OSError as exc:
            print(json.dumps({
                "event": "task_status_error",
                "task_id": task_id,
                "error": type(exc).__name__,
            }), flush=True)
            return False
        self.store.update_task(task_id, "running")
        if self._send_event is not None:
            ack = {
                "type": "task_ack",
                "task_id": task_id,
                "agent": self.config.sender,
                "sequence": sequence,
            }
            self._send_event({"to": "coordinator", "text": json.dumps(ack)})
            self._send_event(self.heartbeat_payload())
        print(json.dumps({"event": "task_assignment", "task_id": task_id}, ensure_ascii=False), flush=True)
        return False

    def run(self, since: int = 0, heartbeat_interval: float = 15.0) -> None:
        cursor = max(since, int(self.store.snapshot().get("cursor", 0)))
        WsClient(self.config).listen(
            self.handle_record,
            since=cursor,
            on_connected=self.on_connected,
            heartbeat_factory=self.heartbeat_payload,
            heartbeat_interval=heartbeat_interval,
        )


def worker_store(config: ClientConfig, state_dir: str | None = None) -> WorkerStateStore:
    configured = state_dir or os.environ.get("MSGBUS_WORKER_STATE")
    root = Path(configured) if configured else Path.home() / ".aiwf" / "msgbus" / "workers"
    return WorkerStateStore(root, config.sender)


def cmd_agent_run(config: ClientConfig, args) -> None:
    worker = AgentWorker(config, worker_store(config, getattr(args, "state_dir", None)))
    worker.run(args.since, args.heartbeat)


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
    store = worker_store(config, getattr(args, "state_dir", None))
    print(json.dumps(store.snapshot(), ensure_ascii=False))


def cmd_task_update(config: ClientConfig, args) -> None:
    remote = RestClient(config).task_update(args.task_id, args.status, args.output)
    store = worker_store(config, getattr(args, "state_dir", None))
    store.update_task(args.task_id, args.status, args.output)
    print(json.dumps(remote, ensure_ascii=False))
