"""Process-safe durable local events with lease and explicit acknowledgment."""
from __future__ import annotations

import json
import os
import tempfile
import threading
import time
import uuid
from pathlib import Path


class ProcessLock:
    """Reentrant within one thread; OS ownership spans independent processes."""

    def __init__(self, path: Path, timeout: float = 5.0) -> None:
        self.path = path
        self.timeout = timeout
        self._thread = threading.RLock()
        self._depth = 0
        self._file = None

    def __enter__(self):
        self._thread.acquire()
        if self._depth:
            self._depth += 1
            return self
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            stream = self.path.open("a+b")
            self._file = stream
            os.chmod(self.path, 0o600)
            if self.path.stat().st_size == 0:
                stream.write(b"0")
                stream.flush()
            deadline = time.monotonic() + self.timeout
            while True:
                try:
                    stream.seek(0)
                    if os.name == "nt":
                        import msvcrt
                        msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
                    else:
                        import fcntl
                        fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    break
                except OSError:
                    if time.monotonic() >= deadline:
                        raise RuntimeError("MsgBus state is owned by another process") from None
                    time.sleep(0.05)
            self._depth = 1
            return self
        except BaseException:
            if self._file is not None:
                self._file.close()
                self._file = None
            self._thread.release()
            raise

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        try:
            self._depth -= 1
            if not self._depth and self._file is not None:
                stream = self._file
                self._file = None
                try:
                    stream.seek(0)
                    if os.name == "nt":
                        import msvcrt
                        msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
                    else:
                        import fcntl
                        fcntl.flock(stream.fileno(), fcntl.LOCK_UN)
                finally:
                    stream.close()
        finally:
            self._thread.release()


def read_json(path: Path, default: dict) -> dict:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return dict(default)
    if not isinstance(payload, dict):
        raise ValueError("Invalid MsgBus state object")
    return payload


def atomic_json(path: Path, value: dict) -> None:
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, delete=False) as stream:
            temporary = Path(stream.name)
            os.chmod(temporary, 0o600)
            json.dump(value, stream, ensure_ascii=False)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


class EventStream:
    def __init__(self, root: Path) -> None:
        self.root = root
        root.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.path = root / "ws_events.jsonl"
        self.cursor = root / "ws_event_cursor"
        self.lock = ProcessLock(root / ".events.lock")
        self.state_lock = ProcessLock(root / ".state.lock")

    def _position(self) -> dict:
        value = read_json(self.cursor, {"offset": 0})
        if type(value.get("offset")) is not int or value["offset"] < 0:
            raise ValueError("Invalid event cursor")
        return value

    def resume_sequence(self) -> int:
        with self.lock:
            maximum = 0
            if not self.path.exists():
                return maximum
            with self.path.open("rb") as stream:
                for line in stream:
                    if not line.endswith(b"\n"):
                        raise ValueError("Incomplete event tail; preserve file and repair before restarting daemon")
                    row = json.loads(line)
                    maximum = max(maximum, int(row["seq"]))
            return maximum

    def append(self, record: dict, metadata: dict) -> None:
        row = {**record, "event_id": str(record["seq"]), "receiver": metadata}
        data = (json.dumps(row, ensure_ascii=False) + "\n").encode("utf-8")
        with self.lock:
            with self.path.open("ab") as stream:
                os.chmod(self.path, 0o600)
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())

    def claim(self, lease: float = 60.0) -> dict:
        if not 1 <= lease <= 3600:
            raise ValueError("Event lease must be between 1 and 3600 seconds")
        with self.lock:
            cursor = self._position()
            if cursor.get("pending") and cursor.get("expires", 0) > time.time():
                return {"status": "busy"}
            if not self.path.exists():
                if cursor["offset"]:
                    raise ValueError("Event stream is missing for nonzero cursor")
                return {"status": "empty"}
            if cursor["offset"] > self.path.stat().st_size:
                raise ValueError("Event stream was truncated below cursor")
            with self.path.open("rb") as stream:
                stream.seek(cursor["offset"])
                line = stream.readline()
                end = stream.tell()
            if not line or not line.endswith(b"\n"):
                return {"status": "empty"}
            record = json.loads(line)
            token = uuid.uuid4().hex
            cursor.update(pending=token, end=end, expires=time.time() + lease)
            atomic_json(self.cursor, cursor)
            return {"status": "event", "receipt": token, "event": record}

    def acknowledge(self, token: str, release: bool = False) -> dict:
        with self.lock:
            cursor = self._position()
            if not token or cursor.get("pending") != token:
                raise ValueError("Event receipt does not match the pending delivery")
            offset = cursor["offset"] if release else cursor["end"]
            atomic_json(self.cursor, {"offset": offset})
            return {"status": "released" if release else "acknowledged"}

    def bind(self, identity: dict) -> None:
        with self.state_lock:
            path = self.root / "state.json"
            state = read_json(path, {})
            previous = state.get("receiver_identity")
            if previous is not None and previous != identity:
                raise ValueError("Conversation state belongs to a different agent identity")
            state["receiver_identity"] = identity
            atomic_json(path, state)
