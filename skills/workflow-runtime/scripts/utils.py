# utils.py
import os
import json

def get_memory_info() -> dict:
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

def get_rag_info() -> dict:
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
        import msvcrt
        import ctypes
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
        import select
        import fcntl
        import termios
        import array
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

def prompt_select(question: str, options: list[str], default: str | None = None) -> str:
    """
    In ra cấu trúc XML/JSON đặc biệt để Agent bắt sự kiện hiển thị UI ask_question.
    Chờ nhận kết quả từ stdin (do Agent gửi send_input).
    Nếu không nhận được hoặc lỗi, trả về giá trị default.
    """
    import sys
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
    xml_str = f"\n<interactive_prompt type=\"select\">\n{json.dumps(payload, indent=2, ensure_ascii=False)}\n</interactive_prompt>\n"
    try:
        sys.stdout.write(xml_str)
        sys.stdout.flush()
    except UnicodeEncodeError:
        sys.stdout.buffer.write(xml_str.encode('utf-8'))
        sys.stdout.buffer.flush()
    
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
            return default if default is not None else options[0]
            
        # Block chờ phản hồi qua stdin
        line = sys.stdin.readline().strip()
        if not line:
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

def build_branch_selection_options(artifact_id: str, slug: str) -> dict:
    current = get_current_branch()
    suggested = suggest_branch_name(artifact_id, slug)
    
    if not current:
        opt1 = "Continue on current branch (detached HEAD — not recommended)"
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


