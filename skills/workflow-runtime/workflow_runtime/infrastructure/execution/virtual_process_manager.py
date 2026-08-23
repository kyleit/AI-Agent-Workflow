from __future__ import annotations

import os
import signal
import subprocess
import time
from typing import Any, cast


class VirtualProcessManager:
    """
    FEAT-101: Virtual Process Manager
    Manages child processes, signals (SIGSTOP, SIGCONT, SIGKILL), and prevents host leaks.
    """
    def __init__(self) -> None:
        self.process_table: dict[int, dict[str, Any]] = {}
        self.next_vpid: int = 1000

    def spawn(self, args: list[str], cwd: str = ".") -> int:
        vpid = self.next_vpid
        self.next_vpid += 1

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
        proc = cast(subprocess.Popen[str], proc_data["proc"])

        if proc.poll() is not None:
            proc_data["status"] = "TERMINATED"
            return False

        try:
            pid = int(cast(int, proc_data["pid"]))
            if sig == "SIGSTOP":
                if os.name != 'nt':
                    sigstop = getattr(signal, "SIGSTOP", None)
                    if sigstop is not None:
                        os.kill(pid, sigstop)
                proc_data["status"] = "SUSPENDED"
            elif sig == "SIGCONT":
                if os.name != 'nt':
                    sigcont = getattr(signal, "SIGCONT", None)
                    if sigcont is not None:
                        os.kill(pid, sigcont)
                proc_data["status"] = "RUNNING"
            elif sig == "SIGKILL":
                proc.kill()
                proc_data["status"] = "TERMINATED"
            return True
        except OSError:
            return False

    def reap(self, vpid: int) -> dict[str, Any] | None:
        if vpid not in self.process_table:
            return None

        proc_data = self.process_table[vpid]
        proc = cast(subprocess.Popen[str], proc_data["proc"])

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


__all__ = ["VirtualProcessManager"]
