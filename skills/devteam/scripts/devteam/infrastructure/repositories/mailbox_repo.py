"""JsonlMailboxRepository — append-only JSONL inbox + line-count cursor."""

from __future__ import annotations

import json
import os

from ...domain.mailbox.envelope import Envelope
from ..fs.atomic import append_line, atomic_write
from ..paths import PathResolver


class JsonlMailboxRepository:
    def __init__(self, paths: PathResolver) -> None:
        self._p = paths

    def ensure_inbox(self, slug: str) -> None:
        for f in (self._p.inbox(slug), self._p.cursor(slug)):
            os.makedirs(os.path.dirname(f), exist_ok=True)
            if not os.path.exists(f):
                open(f, "a", encoding="utf-8").close()

    def append(self, slug: str, env: Envelope) -> None:
        line = json.dumps(env.to_dict(), ensure_ascii=False, sort_keys=True)
        append_line(self._p.inbox(slug), line)

    def read_from(self, slug: str, cursor: int) -> list[Envelope]:
        path = self._p.inbox(slug)
        if not os.path.exists(path):
            return []
        with open(path, encoding="utf-8") as f:
            lines = [ln for ln in f.read().splitlines() if ln.strip()]
        return [Envelope.from_dict(json.loads(ln)) for ln in lines[cursor:]]

    def cursor(self, slug: str) -> int:
        path = self._p.cursor(slug)
        if not os.path.exists(path):
            return 0
        raw = open(path, encoding="utf-8").read().strip()
        return int(raw) if raw else 0

    def set_cursor(self, slug: str, value: int) -> None:
        atomic_write(self._p.cursor(slug), str(value))
