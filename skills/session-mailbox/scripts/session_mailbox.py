from __future__ import annotations

import argparse
import json
import os
import sys
import time
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator


DEFAULT_BUS_ROOT = Path.home() / ".aiwf" / "session-bus"


def _bus_root(raw: str | None) -> Path:
    return Path(raw).expanduser().resolve() if raw else DEFAULT_BUS_ROOT


@contextmanager
def file_lock(lock_path: Path, timeout: float = 10.0) -> Iterator[None]:
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    deadline = time.time() + timeout
    fd: int | None = None
    while True:
        try:
            fd = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(fd, str(os.getpid()).encode("ascii"))
            break
        except FileExistsError:
            if time.time() >= deadline:
                raise TimeoutError(f"Timed out waiting for mailbox lock: {lock_path}")
            time.sleep(0.05)
    try:
        yield
    finally:
        if fd is not None:
            os.close(fd)
        try:
            lock_path.unlink()
        except FileNotFoundError:
            pass


def append_jsonl(path: Path, record: dict, bus_root: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lock_name = path.name.replace(os.sep, "_") + ".lock"
    lock_path = bus_root / ".locks" / lock_name
    line = json.dumps(record, ensure_ascii=False, separators=(",", ":"))
    with file_lock(lock_path):
        with path.open("a", encoding="utf-8", newline="\n") as f:
            f.write(line)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())


def read_jsonl(path: Path, strict: bool = False) -> tuple[list[dict], list[tuple[int, str, str]]]:
    records: list[dict] = []
    bad: list[tuple[int, str, str]] = []
    if not path.exists():
        return records, bad
    with path.open("r", encoding="utf-8") as f:
        for idx, raw_line in enumerate(f, start=1):
            line = raw_line.rstrip("\n")
            if not line:
                continue
            try:
                parsed = json.loads(line)
                if isinstance(parsed, dict):
                    records.append(parsed)
                else:
                    bad.append((idx, line, "json_line_not_object"))
            except json.JSONDecodeError as exc:
                if strict:
                    raise
                bad.append((idx, line, str(exc)))
    return records, bad


def repair_jsonl(path: Path, bus_root: Path) -> dict:
    records, bad = read_jsonl(path, strict=False)
    if not bad:
        return {"status": "ok", "valid": len(records), "bad": 0}
    bad_path = path.with_suffix(path.suffix + ".bad")
    lock_path = bus_root / ".locks" / (path.name + ".repair.lock")
    with file_lock(lock_path):
        with path.open("w", encoding="utf-8", newline="\n") as good_file:
            for record in records:
                good_file.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")))
                good_file.write("\n")
            good_file.flush()
            os.fsync(good_file.fileno())
        with bad_path.open("a", encoding="utf-8", newline="\n") as bad_file:
            for line_no, line, error in bad:
                bad_file.write(json.dumps({"line": line_no, "error": error, "raw": line}, ensure_ascii=False))
                bad_file.write("\n")
            bad_file.flush()
            os.fsync(bad_file.fileno())
    return {"status": "repaired", "valid": len(records), "bad": len(bad), "bad_path": str(bad_path)}


def message_record(args: argparse.Namespace) -> dict:
    now = datetime.now(timezone.utc).isoformat()
    return {
        "from": args.sender,
        "from_project": args.from_project or os.getcwd(),
        "from_project_name": args.from_project_name or Path(os.getcwd()).name,
        "to": args.to,
        "to_project": args.to_project or "",
        "ts": now,
        "type": args.type,
        "content": args.message,
        "bus_version": "1.0",
        "msg_id": args.msg_id or str(uuid.uuid4()),
    }


def inbox_path(bus_root: Path, session_id: str) -> Path:
    return bus_root / "sessions" / f"{session_id}.inbox.jsonl"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Safe session-mailbox JSONL utility")
    parser.add_argument("--bus-root", default=None)
    sub = parser.add_subparsers(dest="command", required=True)

    send = sub.add_parser("send")
    send.add_argument("--from", dest="sender", required=True)
    send.add_argument("--to", required=True)
    send.add_argument("--message", required=True)
    send.add_argument("--type", default="msg", choices=["msg", "broadcast", "group_msg", "system", "ack", "request", "response"])
    send.add_argument("--from-project", default="")
    send.add_argument("--from-project-name", default="")
    send.add_argument("--to-project", default="")
    send.add_argument("--msg-id", default="")

    validate = sub.add_parser("validate")
    validate.add_argument("--file", required=True)
    validate.add_argument("--strict", action="store_true")

    repair = sub.add_parser("repair")
    repair.add_argument("--file", required=True)

    append = sub.add_parser("append")
    append.add_argument("--file", required=True)
    append.add_argument("--record-json", required=True)

    args = parser.parse_args(argv)
    root = _bus_root(args.bus_root)

    if args.command == "send":
        append_jsonl(inbox_path(root, args.to), message_record(args), root)
        print(json.dumps({"status": "sent", "to": args.to}, ensure_ascii=False))
        return 0
    if args.command == "validate":
        records, bad = read_jsonl(Path(args.file).expanduser(), strict=args.strict)
        status = "ok" if not bad else "invalid"
        print(json.dumps({"status": status, "valid": len(records), "bad": len(bad)}, ensure_ascii=False))
        return 0 if not bad else 1
    if args.command == "repair":
        print(json.dumps(repair_jsonl(Path(args.file).expanduser(), root), ensure_ascii=False))
        return 0
    if args.command == "append":
        try:
            record = json.loads(args.record_json)
        except json.JSONDecodeError as exc:
            print(json.dumps({"status": "invalid_json", "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
            return 1
        if not isinstance(record, dict):
            print(json.dumps({"status": "invalid_json", "error": "record_json_must_be_object"}, ensure_ascii=False), file=sys.stderr)
            return 1
        append_jsonl(Path(args.file).expanduser(), record, root)
        print(json.dumps({"status": "appended", "file": args.file}, ensure_ascii=False))
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
