# skills/notify-telegram/monitor_listener.py
import os
import sys
import time
import json
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

if sys.platform == "win32":
    py_dir = os.path.dirname(sys.executable)
    if py_dir not in os.environ.get("PATH", ""):
        os.environ["PATH"] = py_dir + os.pathsep + os.environ.get("PATH", "")
    try:
        os.add_dll_directory(py_dir)
    except Exception:
        pass


local_inbox = Path(".agents") / "inbox" / "inbox.json"
VALID_INBOX_TYPES = {
    "MESSAGE_RECEIVED",
    "FILE_RECEIVED",
    "PHOTO_RECEIVED",
    "PHOTO_DOWNLOAD_FAILED",
    "FILE_DOWNLOAD_FAILED",
}


def read_inbox_event(path: Path) -> dict | None:
    """Read and validate one project-local Telegram inbox event."""
    with open(path, "r", encoding="utf-8") as f:
        payload = json.load(f)
    if not isinstance(payload, dict):
        raise ValueError("Telegram inbox payload must be a JSON object")
    if payload.get("type") not in VALID_INBOX_TYPES:
        raise ValueError(f"Unsupported Telegram inbox type: {payload.get('type')}")
    for key in ("content", "update_id", "chat_id", "timestamp"):
        if key not in payload:
            raise ValueError(f"Missing Telegram inbox field: {key}")
    return payload

print(f"Monitoring project inbox: {local_inbox}", flush=True)

# Give it a moment to initialize
time.sleep(1)

# Get initial state of the project inbox file
last_mtime = 0
last_size = 0


while True:
    if local_inbox.exists():
        try:
            stat = local_inbox.stat()
            mtime = stat.st_mtime
            size = stat.st_size

            # If the file is modified or newly created
            if mtime != last_mtime or size != last_size or last_mtime == 0:
                print("Change detected in project inbox.", flush=True)

                event = read_inbox_event(local_inbox)
                if event:
                    print(f"Telegram inbox event: {event['type']}", flush=True)
                    last_mtime = mtime
                    last_size = size
        except Exception as e:
            print(f"Error checking project inbox: {e}", file=sys.stderr)

    time.sleep(2)
