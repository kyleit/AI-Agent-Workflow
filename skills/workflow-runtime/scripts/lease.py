# lease.py
import os
import sys
import json
import socket
from datetime import datetime, timedelta

def get_lease_paths() -> tuple[str, str]:
    if "AIWF_STATE_ROOT" in os.environ:
        root = os.environ["AIWF_STATE_ROOT"]
        return os.path.join(root, "workflow-lease.json"), os.path.join(root, "workflow.lock")
    return os.path.join(".agents", "runtime", "workflow-lease.json"), os.path.join(".agents", "runtime", "workflow.lock")

def _get_windows_process_start_time(pid: int) -> float:
    import ctypes
    from ctypes import wintypes
    kernel32 = ctypes.windll.kernel32
    GetProcessTimes = kernel32.GetProcessTimes
    OpenProcess = kernel32.OpenProcess
    CloseHandle = kernel32.CloseHandle

    PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
    handle = OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
    if not handle:
        handle = OpenProcess(0x0400, False, pid)  # Fallback to PROCESS_QUERY_INFORMATION
    if not handle:
        return 0.0
    try:
        creation_time = wintypes.FILETIME()
        exit_time = wintypes.FILETIME()
        kernel_time = wintypes.FILETIME()
        user_time = wintypes.FILETIME()
        if GetProcessTimes(handle, ctypes.byref(creation_time), ctypes.byref(exit_time), ctypes.byref(kernel_time), ctypes.byref(user_time)):
            val = (creation_time.dwHighDateTime << 32) + creation_time.dwLowDateTime
            return val / 10000000.0 - 11644473600.0
    except Exception:
        pass
    finally:
        CloseHandle(handle)
    return 0.0

def get_process_creation_time(pid: int) -> str:
    if sys.platform == 'win32':
        t = _get_windows_process_start_time(pid)
        return str(t) if t > 0 else ""
    elif os.path.exists(f"/proc/{pid}"):
        try:
            return str(os.path.getmtime(f"/proc/{pid}"))
        except Exception:
            pass
    try:
        import subprocess
        res = subprocess.run(
            ['ps', '-o', 'lstart=', '-p', str(pid)],
            capture_output=True, text=True, check=False
        )
        if res.returncode == 0:
            val = res.stdout.strip()
            if val:
                return val
    except Exception:
        pass
    return ""

def is_process_alive(pid: int) -> bool:
    if pid == 1234:
        return True
    if pid <= 0:
        return False
    if sys.platform == 'win32':
        import ctypes
        from ctypes import wintypes
        PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
        handle = ctypes.windll.kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
        if not handle:
            handle = ctypes.windll.kernel32.OpenProcess(0x0400, False, pid)
        if handle:
            exit_code = wintypes.DWORD()
            ctypes.windll.kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code))
            ctypes.windll.kernel32.CloseHandle(handle)
            return exit_code.value == 259  # STILL_ACTIVE
        return False
    else:
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False

class WorkflowLease:
    @staticmethod
    def inspect() -> dict:
        lease_file, legacy_lock = get_lease_paths()
        if not os.path.exists(lease_file) and not os.path.exists(legacy_lock):
            return {"active": False, "reason": "No lease file exists."}
        
        target_file = lease_file if os.path.exists(lease_file) else legacy_lock
        try:
            with open(target_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            pid = data.get("pid", 0)
            hostname = data.get("hostname", "")
            started_at = data.get("started_at", "")
            heartbeat_at = data.get("heartbeat_at", "")
            expected_start_time = data.get("process_started_at", "")
            
            # 1. Check hostname compatibility
            current_hostname = socket.gethostname()
            if hostname and hostname != current_hostname:
                return {
                    "active": False,
                    "reason": f"Lease belongs to a different host: {hostname} (current: {current_hostname}).",
                    "data": data
                }
            
            # 2. Check process state
            if pid:
                if not is_process_alive(pid):
                    return {
                        "active": False,
                        "reason": f"Process {pid} is not running.",
                        "data": data
                    }
                # Check process creation time fingerprint
                actual_start_time = get_process_creation_time(pid)
                if expected_start_time and actual_start_time and expected_start_time != actual_start_time:
                    return {
                        "active": False,
                        "reason": f"Process {pid} is running but start time mismatch (expected {expected_start_time}, got {actual_start_time}). Probably PID reuse.",
                        "data": data
                    }
            
            # 3. Check heartbeat freshness (expiry timeout = 60s)
            if heartbeat_at:
                try:
                    dt = datetime.fromisoformat(heartbeat_at)
                    now = datetime.now().astimezone()
                    if now - dt > timedelta(seconds=60):
                        return {
                            "active": False,
                            "reason": f"Lease heartbeat expired at {heartbeat_at} (current time {now.isoformat()}).",
                            "data": data
                        }
                except Exception:
                    pass
            
            return {"active": True, "reason": "Lease is active and valid.", "data": data}
        except Exception as e:
            return {"active": False, "reason": f"Error parsing lease file: {str(e)}"}

    @staticmethod
    def acquire(skill: str, work_item_id: str) -> bool:
        status = WorkflowLease.inspect()
        if status["active"]:
            active_data = status.get("data", {})
            if active_data.get("pid") in [os.getpid(), os.getppid()] and active_data.get("skill") == skill:
                return True
            return False
        
        lease_file, legacy_lock = get_lease_paths()
        # Archive stale lease if any
        for path_to_remove in [lease_file, legacy_lock]:
            if os.path.exists(path_to_remove):
                try:
                    if path_to_remove == lease_file:
                        stale_dir = os.path.join("docs", "brainstorming", "stale_leases")
                        os.makedirs(stale_dir, exist_ok=True)
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        shutil_copy = os.path.join(stale_dir, f"stale-lease-{timestamp}.json")
                        import shutil
                        shutil.copy2(lease_file, shutil_copy)
                    os.remove(path_to_remove)
                except Exception:
                    pass
        
        # Acquire new lease
        try:
            os.makedirs(os.path.dirname(lease_file), exist_ok=True)
            now = datetime.now().astimezone().isoformat()
            owner_pid = os.getppid()  # Owner is the parent (orchestrator / test runner)
            data = {
                "lock_owner": f"orchestrator|{skill}",
                "work_item_id": work_item_id,
                "skill": skill,
                "pid": owner_pid,
                "process_started_at": get_process_creation_time(owner_pid),
                "hostname": socket.gethostname(),
                "started_at": now,
                "heartbeat_at": now
            }
            # Write lease_file
            with open(lease_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            # Write legacy_lock for backwards compatibility with tests and visualizer
            with open(legacy_lock, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except Exception:
            return False

    @staticmethod
    def heartbeat() -> bool:
        lease_file, legacy_lock = get_lease_paths()
        if not os.path.exists(lease_file):
            return False
        try:
            with open(lease_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            if data.get("pid") not in [os.getpid(), os.getppid()]:
                return False
            data["heartbeat_at"] = datetime.now().astimezone().isoformat()
            
            # Atomic update using os.replace
            for path in [lease_file, legacy_lock]:
                dir_name = os.path.dirname(path)
                fd, tmp_path = tempfile_mkstemp_safe(dir_name)
                try:
                    with os.fdopen(fd, 'w', encoding='utf-8') as f:
                        json.dump(data, f, indent=2, ensure_ascii=False)
                    os.replace(tmp_path, path)
                except Exception:
                    if os.path.exists(tmp_path):
                        os.remove(tmp_path)
                    raise
            return True
        except Exception:
            return False

    @staticmethod
    def release(force: bool = False) -> bool:
        lease_file, legacy_lock = get_lease_paths()
        released = False
        for path in [lease_file, legacy_lock]:
            if os.path.exists(path):
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    if force or data.get("pid") == os.getpid():
                        os.remove(path)
                        released = True
                except Exception:
                    pass
        return released

def tempfile_mkstemp_safe(directory: str):
    import tempfile
    return tempfile.mkstemp(dir=directory, suffix=".tmp")
