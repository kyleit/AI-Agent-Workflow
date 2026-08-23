"""Append-only JSONL message store with flush + fsync durability."""
from __future__ import annotations

import json
import os
import threading
from pathlib import Path

from ..domain.models import Message
from ..domain.ports import MessageStore


class JsonlMessageStore(MessageStore):
    def __init__(self, path: Path) -> None:
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    def append(self, message: Message) -> None:
        line = json.dumps(message.to_dict(), ensure_ascii=False, separators=(",", ":"))
        with self._lock:
            with self._path.open("a", encoding="utf-8", newline="\n") as f:
                f.write(line)
                f.write("\n")
                f.flush()
                os.fsync(f.fileno())

    def read_since(self, since: int) -> list[Message]:
        out: list[Message] = []
        if not self._path.exists():
            return out
        with self._path.open("r", encoding="utf-8") as f:
            for raw in f:
                raw = raw.strip()
                if not raw:
                    continue
                try:
                    data = json.loads(raw)
                except ValueError:
                    continue
                if int(data.get("seq", 0)) > since:
                    out.append(Message.from_dict(data))
        return out

    def max_seq(self) -> int:
        seq = 0
        if not self._path.exists():
            return 0
        with self._path.open("r", encoding="utf-8") as f:
            for raw in f:
                raw = raw.strip()
                if not raw:
                    continue
                try:
                    seq = max(seq, int(json.loads(raw).get("seq", 0)))
                except (ValueError, TypeError):
                    continue
        return seq
