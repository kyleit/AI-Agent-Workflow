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

def prompt_select(question: str, options: list[str], default: str | None = None) -> str:
    """
    In ra cấu trúc XML/JSON đặc biệt để Agent bắt sự kiện hiển thị UI ask_question.
    Chờ nhận kết quả từ stdin (do Agent gửi send_input).
    Nếu không nhận được hoặc lỗi, trả về giá trị default.
    """
    import sys
    # Bỏ qua tương tác nếu đang chạy test tự động
    if (os.environ.get("TESTING") == "1" or any(m in sys.modules for m in ["unittest", "pytest"])) and os.environ.get("TEST_PROMPT") != "1":
        import select
        try:
            ready, _, _ = select.select([sys.stdin], [], [], 0.1)
            if not ready:
                return default if default is not None else options[0]
        except Exception:
            return default if default is not None else options[0]
        
    payload = {
        "question": question,
        "options": options,
        "default": default
    }
    # In ra XML tag đặc biệt để Agent phát hiện
    print(f"\n<interactive_prompt type=\"select\">\n{json.dumps(payload, indent=2)}\n</interactive_prompt>", flush=True)
    
    # Luôn in ra câu hỏi và danh sách lựa chọn để hiển thị trong nhật ký/terminal
    print(f"\n[Prompt] {question}")
    for idx, opt in enumerate(options):
        print(f"  {idx + 1}. {opt}")
    print(f"Select option (1-{len(options)}) [Default: {default}]: ", end="", flush=True)
    
    try:
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


