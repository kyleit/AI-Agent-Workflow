"""Concurrency proof (AC3): many threads append to one inbox via O_APPEND.

O_APPEND single-line writes are atomic at the OS level, so no line is lost,
truncated, or interleaved. We assert exact count and that every line parses.
"""

from __future__ import annotations

import json
import threading

from devteam.domain.mailbox.envelope import Envelope
from devteam.infrastructure.paths import PathResolver
from devteam.infrastructure.repositories.mailbox_repo import JsonlMailboxRepository

WRITERS = 8
PER_WRITER = 200


def test_concurrent_appends_no_loss_or_corruption(tmp_path):
    repo = JsonlMailboxRepository(PathResolver(str(tmp_path)))
    repo.ensure_inbox("x")
    barrier = threading.Barrier(WRITERS)

    def worker(wid: int) -> None:
        barrier.wait()  # maximize contention
        for i in range(PER_WRITER):
            env = Envelope(id=f"{wid}-{i}", frm=f"seat-{wid}", to="seat-x",
                           ts="t", type="msg", body=f"{wid}:{i}")
            repo.append("x", env)

    threads = [threading.Thread(target=worker, args=(w,)) for w in range(WRITERS)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    path = PathResolver(str(tmp_path)).inbox("x")
    lines = [ln for ln in open(path, encoding="utf-8").read().splitlines() if ln.strip()]
    assert len(lines) == WRITERS * PER_WRITER
    seen = set()
    for ln in lines:
        obj = json.loads(ln)             # every line is a complete, valid JSON object
        env = Envelope.from_dict(obj)    # and a valid envelope
        seen.add(env.id)
    assert len(seen) == WRITERS * PER_WRITER  # no duplicates/merges
