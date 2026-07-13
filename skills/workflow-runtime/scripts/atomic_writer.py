# atomic_writer.py
"""
Atomic JSON file writer and JSONL appender for AIWF state management.
Uses tmp+rename pattern to guarantee no half-written files.
Cross-platform safe (macOS, Linux, Windows).
"""
import os
import json
import tempfile
import threading
from typing import Any

# Import state_path for security validation
try:
    from state_path import validate_relative_path, SecurityError  # type: ignore
except ImportError:
    # Fallback if imported standalone
    class SecurityError(ValueError):  # type: ignore
        pass

    def validate_relative_path(path: str) -> str:
        if os.path.isabs(path):
            raise SecurityError(f"Absolute path rejected: '{path}'")
        return os.path.normpath(path)


# Thread-level lock for JSONL appends to prevent interleaved writes
_jsonl_locks: dict[str, threading.Lock] = {}
_jsonl_locks_meta = threading.Lock()


def _get_jsonl_lock(path: str) -> threading.Lock:
    """Get or create a per-file threading.Lock for JSONL appends."""
    abs_path = os.path.abspath(path)
    with _jsonl_locks_meta:
        if abs_path not in _jsonl_locks:
            _jsonl_locks[abs_path] = threading.Lock()
        return _jsonl_locks[abs_path]


def write_json_atomic(
    path: str,
    data: dict[str, Any],
    require_relative: bool = False,
    indent: int = 2,
    ensure_parent: bool = True,
) -> None:
    """
    Write a JSON file atomically using tmp+rename pattern.
    
    Args:
        path: Target file path. If require_relative=True, must be a relative path.
        data: Dict to serialize as JSON.
        require_relative: If True, reject absolute paths (security mode).
        indent: JSON indentation level.
        ensure_parent: Create parent directory if it doesn't exist.
    
    Raises:
        SecurityError: If require_relative=True and path is absolute or has traversal.
        TypeError: If data is not JSON-serializable.
        IOError: If write fails (original file is not modified).
    """
    if require_relative:
        path = validate_relative_path(path)

    abs_path = os.path.abspath(path)
    parent_dir = os.path.dirname(abs_path)

    if ensure_parent and not os.path.exists(parent_dir):
        os.makedirs(parent_dir, exist_ok=True)

    # Validate JSON-serializability before opening tmp file
    json_str = json.dumps(data, indent=indent, ensure_ascii=False)

    # Write to tmp file in SAME directory as target (ensures same filesystem/partition)
    tmp_fd, tmp_path = tempfile.mkstemp(
        dir=parent_dir,
        prefix=f".{os.path.basename(abs_path)}.tmp_",
        suffix=".tmp",
    )
    try:
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
            f.write(json_str)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())

        # Atomic replace (POSIX: rename is atomic; Windows: os.replace is best-effort)
        _safe_rename(tmp_path, abs_path)

    except Exception:
        # Clean up tmp file on failure
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def _safe_rename(src: str, dst: str) -> None:
    """
    Cross-platform atomic rename.
    On POSIX: os.rename is atomic.
    On Windows: os.replace is best-effort (not fully atomic but better than copy).
    """
    try:
        os.rename(src, dst)
    except OSError:
        # Windows cross-device rename fallback
        os.replace(src, dst)


def append_jsonl(path: str, record: dict[str, Any], ensure_parent: bool = True) -> None:
    """
    Safely append a single JSON record as a new line to a JSONL file.
    Uses per-file threading.Lock to prevent interleaved concurrent writes.
    
    Args:
        path: Target JSONL file path.
        record: Dict to serialize as a single JSON line.
        ensure_parent: Create parent directory if it doesn't exist.
    
    Raises:
        TypeError: If record is not JSON-serializable.
        IOError: If append fails.
    """
    abs_path = os.path.abspath(path)
    parent_dir = os.path.dirname(abs_path)

    if ensure_parent and not os.path.exists(parent_dir):
        os.makedirs(parent_dir, exist_ok=True)

    # Validate JSON-serializability before acquiring lock
    line = json.dumps(record, ensure_ascii=False)

    lock = _get_jsonl_lock(abs_path)
    with lock:
        with open(abs_path, "a", encoding="utf-8") as f:
            f.write(line + "\n")
            f.flush()


def read_json_safe(path: str, default: Any = None) -> Any:
    """
    Safely read a JSON file. Returns default if file missing or JSON invalid.
    Never raises on missing file or parse error.
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return default


def read_jsonl_safe(path: str) -> list[dict]:
    """
    Safely read a JSONL file, skipping lines that are invalid JSON.
    Returns list of parsed dicts.
    """
    records = []
    if not os.path.exists(path):
        return records
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    # Skip invalid lines silently (logged by caller if needed)
                    pass
    except OSError:
        pass
    return records
