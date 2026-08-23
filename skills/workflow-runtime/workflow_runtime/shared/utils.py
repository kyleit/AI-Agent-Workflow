from __future__ import annotations

import hashlib
import json
import os
import pathlib
import re
from typing import Any

from workflow_runtime.shared.errors import PathPolicyViolation

PROMPT_UNAVAILABLE = "PROMPT_UNAVAILABLE"


def is_absolute_path(path_str: str) -> bool:
    if not path_str:
        return False
    cleaned = path_str.strip()
    if cleaned.startswith("/") or cleaned.startswith("\\"):
        return True
    return bool(re.match(r"^[a-zA-Z]:", cleaned))


def validate_relative_path(path_str: str) -> str:
    if is_absolute_path(path_str):
        raise PathPolicyViolation(f"Absolute paths are forbidden: '{path_str}'")
    return pathlib.PurePath(path_str).as_posix()


def atomic_write_json(file_path: str, data: Any) -> None:
    rel_path = validate_relative_path(file_path)
    target = pathlib.Path(rel_path)
    target.parent.mkdir(parents=True, exist_ok=True)

    temp_path = target.with_suffix(f"{target.suffix}.tmp_{os.getpid()}")
    with temp_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    temp_path.replace(target)


def sanitize_string(input_str: str) -> str:
    if not input_str:
        return ""
    return input_str.strip()


def compute_sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def get_memory_info() -> dict[str, Any]:
    info = {"status": "UNKNOWN", "last_updated": "N/A"}
    if os.path.exists(".agents/memory.config.json"):
        try:
            with open(".agents/memory.config.json", "r", encoding="utf-8") as f:
                data = json.load(f)
                info["status"] = "FRESH"
                info["last_updated"] = data.get("last_updated", "N/A")
        except (json.JSONDecodeError, IOError):
            pass
    return info

def get_rag_info() -> dict[str, Any]:
    info = {"connected": False, "provider": "unknown"}
    # Standard check of memory.config.json for RAG provider
    if os.path.exists(".agents/memory.config.json"):
        try:
            with open(".agents/memory.config.json", "r", encoding="utf-8") as f:
                data = json.load(f)
                info["connected"] = True
                info["provider"] = data.get("rag", {}).get("provider", "qdrant")
        except (json.JSONDecodeError, IOError):
            pass
    else:
        # Default fallback
        info["connected"] = True
        info["provider"] = "qdrant"
    return info

def is_stdin_ready() -> bool:
    import sys
    if type(sys.stdin).__name__ in ['Mock', 'MagicMock', 'StringIO', 'BytesIO']:
        return True
    ret = False
    if sys.platform == 'win32':
        import ctypes
        import msvcrt
        from ctypes import wintypes
        try:
            handle = msvcrt.get_osfhandle(sys.stdin.fileno())
            if ctypes.windll.kernel32.GetFileType(handle) == 3:  # FILE_TYPE_PIPE
                avail = wintypes.DWORD()
                res = ctypes.windll.kernel32.PeekNamedPipe(
                    handle, None, 0, None, ctypes.byref(avail), None
                )
                ret = bool(res and avail.value > 0)
            else:
                ret = msvcrt.kbhit()
        except Exception:
            ret = False
    else:
        import array
        import fcntl
        import select
        import termios
        try:
            buf = array.array('i', [0])
            fcntl.ioctl(sys.stdin.fileno(), termios.FIONREAD, buf)
            ret = buf[0] > 0
        except Exception:
            if not sys.stdin.isatty():
                ret = False
            else:
                try:
                    ready, _, _ = select.select([sys.stdin], [], [], 0)
                    ret = len(ready) > 0
                except Exception:
                    ret = False
    return ret

def log_gate_resolution_event(gate_name: str, resolution: str, decision: str) -> None:
    import json
    import os
    from datetime import datetime

    event = {
        "timestamp": datetime.now().astimezone().isoformat(),
        "gate_name": gate_name,
        "permission_mode": "full_access",
        "resolution": resolution,
        "decision": decision
    }

    paths = [
        os.path.join("artifacts", "full-access-autonomous-delivery", "gate_resolution_events.jsonl"),
        os.path.join("docs", "debug", "gate_resolution_events.jsonl")
    ]

    for path in paths:
        dir_name = os.path.dirname(path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
        try:
            with open(path, "a", encoding="utf-8") as f:
                f.write(json.dumps(event, ensure_ascii=False) + "\n")
        except Exception:
            pass

def log_phase_transition_event(from_phase: str, to_phase: str, status: str = "success") -> None:
    import json
    import os
    from datetime import datetime

    event = {
        "timestamp": datetime.now().astimezone().isoformat(),
        "from_phase": from_phase,
        "to_phase": to_phase,
        "status": status
    }

    path = os.path.join("artifacts", "full-access-autonomous-delivery", "phase_transition_events.jsonl")
    dir_name = os.path.dirname(path)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)
    try:
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")
    except Exception:
        pass

def _get_permission_mode() -> str:
    try:
        from workflow_runtime.infrastructure.session.session import (
            load_project_permissions,
            load_session,
        )

        session = load_session()
        if isinstance(session, dict) and session.get("permission_mode"):
            return str(session["permission_mode"])

        permissions = load_project_permissions()
        if permissions and permissions.get("mode"):
            return str(permissions["mode"])
    except Exception:
        pass
    return "sandbox"

def _emit_interactive_prompt(prompt_type: str, payload: dict[str, Any]) -> None:
    import sys

    xml_str = f"\n<interactive_prompt type=\"{prompt_type}\">\n{json.dumps(payload, indent=2, ensure_ascii=False)}\n</interactive_prompt>\n"
    try:
        sys.stdout.write(xml_str)
        sys.stdout.flush()
    except UnicodeEncodeError:
        sys.stdout.buffer.write(xml_str.encode("utf-8"))
        sys.stdout.buffer.flush()

def prompt_select(question: str, options: list[str], default: str | None = None) -> str:
    """
    In ra cấu trúc XML/JSON đặc biệt để Agent bắt sự kiện hiển thị UI ask_question.
    Chờ nhận kết quả từ stdin (do Agent gửi send_input).
    Với approval gate chiến lược, nếu prompt bridge không có câu trả lời thật,
    trả về PROMPT_UNAVAILABLE thay vì default để không nhầm với lựa chọn của user.
    """
    import sys

    question_lower = (question or "").lower()
    approval_terms = ("approve", "approval")
    protected_gate_terms = (
        "technical design blueprint",
        "blueprint",
        "release",
        "git",
        "deployment",
        "implementation",
    )
    strategic_approval_gate = (
        any(term in question_lower for term in approval_terms)
        and any(term in question_lower for term in protected_gate_terms)
    )

    mode = _get_permission_mode()

    if mode == "full_access" and os.environ.get("TEST_PROMPT") != "1" and not strategic_approval_gate:
        # Check positive options
        positive_choices = ["yes", "y", "continue", "continue on current branch", "proceed", "agree"]
        chosen = None
        for opt in options:
            if opt.lower().strip() in positive_choices:
                chosen = opt
                break
        if not chosen:
            chosen = default if default is not None else options[0]

        log_gate_resolution_event(question, "AUTHORIZED_BY_FULL_ACCESS", chosen)
        return chosen

    # Bỏ qua tương tác nếu đang chạy test tự động
    if (os.environ.get("TESTING") == "1" or any(m in sys.modules for m in ["unittest", "pytest"])) and os.environ.get("TEST_PROMPT") != "1":
        if is_stdin_ready():
            try:
                line = sys.stdin.readline().strip()
                if line:
                    return line
            except Exception:
                pass
        return default if default is not None else options[0]

    payload = {
        "question": question,
        "options": options,
        "default": default
    }
    # In ra XML tag đặc biệt để Agent phát hiện
    ask_question_payload = {
        **payload,
        "preferred_tool": "ask_question",
        "fallback_tool": "prompt_select",
        "bridge_order": ["ask_question", "prompt_select", "stdin"],
    }
    _emit_interactive_prompt("ask_question", ask_question_payload)
    _emit_interactive_prompt("select", payload)

    # Fallback cho terminal/human nếu IDE không tự động bắt thẻ XML
    if sys.stdin.isatty():
        prompt_str = f"\n[Prompt] {question}\n"
        for idx, opt in enumerate(options):
            prompt_str += f"  {idx + 1}. {opt}\n"
        prompt_str += f"Select option (1-{len(options)}) [Default: {default}]: "
        try:
            sys.stdout.write(prompt_str)
            sys.stdout.flush()
        except UnicodeEncodeError:
            sys.stdout.buffer.write(prompt_str.encode('utf-8'))
            sys.stdout.buffer.flush()

    try:
        # Prevent blocking indefinitely in non-interactive environments
        if not sys.stdin.isatty() and not is_stdin_ready():
            if strategic_approval_gate:
                return PROMPT_UNAVAILABLE
            return default if default is not None else options[0]

        # Block chờ phản hồi qua stdin
        line = sys.stdin.readline().strip()
        if not line:
            if strategic_approval_gate:
                return PROMPT_UNAVAILABLE
            return default if default is not None else options[0]

        # Hỗ trợ nhận diện cả index (1-based) hoặc chuỗi text khớp trực tiếp
        if line.isdigit():
            idx = int(line) - 1
            if 0 <= idx < len(options):
                return options[idx]

        # Nếu nhập chuỗi, kiểm tra khớp trong danh sách hoặc trả về chuỗi gốc
        for opt in options:
            if opt.lower() == line.lower():
                return opt
        return line
    except (IOError, KeyboardInterrupt):
        if strategic_approval_gate:
            return PROMPT_UNAVAILABLE
        return default if default is not None else options[0]

def get_current_branch() -> str:
    import subprocess
    try:
        res = subprocess.run(["git", "branch", "--show-current"], capture_output=True, text=True)
        if res.returncode == 0:
            return res.stdout.strip()
    except Exception:
        pass
    return ""

def suggest_branch_name(artifact_id: str, slug: str) -> str:
    import re
    slug_clean = re.sub(r'[^a-zA-Z0-9]+', '-', slug.strip().lower()).strip('-')
    art_upper = artifact_id.upper()
    if art_upper.startswith("FIX-"):
        return f"fix/{art_upper.lower()}-{slug_clean}"
    elif art_upper.startswith("QUICK-"):
        return f"quick/{art_upper.lower()}-{slug_clean}"
    else:
        return f"feature/{art_upper.lower()}-{slug_clean}"

def build_branch_selection_options(artifact_id: str, slug: str) -> dict[str, Any]:
    current = get_current_branch()
    suggested = suggest_branch_name(artifact_id, slug)

    if not current:
        opt1 = "Continue on current branch (detached HEAD - not recommended)"
    else:
        opt1 = f"Continue on current branch ({current})"

    opt2 = f"Create new branch ({suggested})"

    warn = False
    if current in ["main", "master"]:
        warn = True

    return {
        "current_branch": current or "detached HEAD",
        "suggested_branch": suggested,
        "options": [opt1, opt2, "Stop"],
        "warn_main": warn
    }
