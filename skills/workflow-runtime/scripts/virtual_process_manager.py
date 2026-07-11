# virtual_process_manager.py
import os
import signal
import subprocess
import time

class VirtualProcessManager:
    """
    FEAT-101: Virtual Process Manager
    Manages child processes, signals (SIGSTOP, SIGCONT, SIGKILL), and prevents host leaks.
    """
    def __init__(self):
        self.process_table = {}
        self.next_vpid = 1000

    def spawn(self, args: list[str], cwd: str = ".") -> int:
        vpid = self.next_vpid
        self.next_vpid += 1
        
        # Start subprocess safely
        proc = subprocess.Popen(
            args,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        self.process_table[vpid] = {
            "proc": proc,
            "pid": proc.pid,
            "args": args,
            "status": "RUNNING",
            "start_time": time.time()
        }
        return vpid

    def send_signal(self, vpid: int, sig: str) -> bool:
        if vpid not in self.process_table:
            return False
        
        proc_data = self.process_table[vpid]
        proc = proc_data["proc"]
        
        # Check if process is already dead
        if proc.poll() is not None:
            proc_data["status"] = "TERMINATED"
            return False
            
        try:
            if sig == "SIGSTOP":
                if os.name == 'nt':
                    # Windows lacks SIGSTOP, mock it or suspend thread if possible
                    # (In Python/Windows, we can mock transition)
                    pass
                else:
                    os.kill(proc.pid, signal.SIGSTOP)
                proc_data["status"] = "SUSPENDED"
            elif sig == "SIGCONT":
                if os.name == 'nt':
                    pass
                else:
                    os.kill(proc.pid, signal.SIGCONT)
                proc_data["status"] = "RUNNING"
            elif sig == "SIGKILL":
                proc.kill()
                proc_data["status"] = "TERMINATED"
            return True
        except OSError:
            return False

    def reap(self, vpid: int) -> dict | None:
        if vpid not in self.process_table:
            return None
            
        proc_data = self.process_table[vpid]
        proc = proc_data["proc"]
        
        exit_code = proc.poll()
        if exit_code is not None:
            proc_data["status"] = "TERMINATED"
            proc_data["exit_code"] = exit_code
            stdout, stderr = proc.communicate()
            proc_data["stdout"] = stdout
            proc_data["stderr"] = stderr
            
        return proc_data

    def cleanup_all(self) -> None:
        for vpid in list(self.process_table.keys()):
            self.send_signal(vpid, "SIGKILL")
            self.reap(vpid)
