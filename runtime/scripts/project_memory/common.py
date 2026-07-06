# common.py
import os
import sys

def log_info(msg: str):
    print(f"\033[1;34m[INFO]\033[0m {msg}", flush=True)

def log_success(msg: str):
    print(f"\033[1;32m[SUCCESS]\033[0m {msg}", flush=True)

def log_warn(msg: str):
    print(f"\033[1;33m[WARN]\033[0m {msg}", flush=True)

def log_error(msg: str):
    print(f"\033[1;31m[ERROR]\033[0m {msg}", flush=True)

def get_project_root() -> str:
    # CLI luôn chạy từ thư mục gốc của dự án
    return os.getcwd()

def to_posix_path(path_str: str) -> str:
    """Chuẩn hóa đường dẫn về dạng POSIX với ký tự '/' (tránh lỗi Windows path trong metadata)."""
    return path_str.replace("\\", "/")

def integrate_runtime_api():
    """Chèn đường dẫn của workflow-runtime vào sys.path."""
    root = get_project_root()
    paths = [
        os.path.join(root, "skills", "workflow-runtime", "scripts"),
        os.path.join(root, ".agents", "skills", "workflow-runtime", "scripts")
    ]
    success = False
    for p in paths:
        if os.path.exists(p):
            if p not in sys.path:
                sys.path.append(p)
            success = True
    return success

# Gọi các hàm runtime
def session_start(skill: str, command: str, checkpoint: int, step: str):
    if integrate_runtime_api():
        try:
            workflow_runtime = __import__("workflow_runtime")
            session_module = __import__("session")
            load_session = session_module.load_session
            save_session_atomic = session_module.save_session_atomic
            
            session = load_session()
            if not session:
                session = {"workspace": {"path": ".", "valid": True}}
            session["status"] = "in_progress"  # type: ignore
            session["checkpoint"] = checkpoint  # type: ignore
            session["current_skill"] = skill  # type: ignore
            session["current_command"] = command  # type: ignore
            session["current_step"] = step  # type: ignore
            session["current_logs"] = [f"> Starting {skill}..."]  # type: ignore
            workflow_runtime.update_context_health(session)
            save_session_atomic(session)
            log_info(f"Session updated: {skill} start.")
        except Exception as e:
            log_warn(f"Failed to call runtime start API: {e}")

def session_step(step: str, log_msg: str):
    if integrate_runtime_api():
        try:
            workflow_runtime = __import__("workflow_runtime")
            session_module = __import__("session")
            load_session = session_module.load_session
            save_session_atomic = session_module.save_session_atomic
            
            session = load_session()
            if session:
                session["current_step"] = step  # type: ignore
                if "current_logs" not in session or not isinstance(session["current_logs"], list):
                    session["current_logs"] = []  # type: ignore
                if log_msg:
                    session["current_logs"].append(log_msg)  # type: ignore
                workflow_runtime.update_context_health(session)
                save_session_atomic(session)
        except Exception as e:
            log_warn(f"Failed to call runtime step API: {e}")

def session_complete(checkpoint: int, step: str, next_skill: str, next_cmd: str):
    if integrate_runtime_api():
        try:
            workflow_runtime = __import__("workflow_runtime")
            session_module = __import__("session")
            load_session = session_module.load_session
            save_session_atomic = session_module.save_session_atomic
            
            session = load_session()
            if session:
                session["status"] = "completed"  # type: ignore
                session["checkpoint"] = checkpoint  # type: ignore
                session["current_step"] = step  # type: ignore
                if "current_logs" not in session or not isinstance(session["current_logs"], list):
                    session["current_logs"] = []  # type: ignore
                session["current_logs"].append("> Completed successfully.")  # type: ignore
                session["suggested_next_skill"] = next_skill  # type: ignore
                session["suggested_next_command"] = next_cmd  # type: ignore
                workflow_runtime.update_context_health(session)
                save_session_atomic(session)
                log_success(f"Session completed: checkpoint {checkpoint} reached.")
        except Exception as e:
            log_warn(f"Failed to call runtime complete API: {e}")

def session_fail(step: str, log_msg: str):
    if integrate_runtime_api():
        try:
            workflow_runtime = __import__("workflow_runtime")
            session_module = __import__("session")
            load_session = session_module.load_session
            save_session_atomic = session_module.save_session_atomic
            
            session = load_session()
            if session:
                session["status"] = "failed"  # type: ignore
                session["current_step"] = step  # type: ignore
                if "current_logs" not in session or not isinstance(session["current_logs"], list):
                    session["current_logs"] = []  # type: ignore
                session["current_logs"].append(f"Error: {log_msg}")  # type: ignore
                workflow_runtime.update_context_health(session)
                save_session_atomic(session)
        except Exception as e:
            log_warn(f"Failed to call runtime fail API: {e}")


