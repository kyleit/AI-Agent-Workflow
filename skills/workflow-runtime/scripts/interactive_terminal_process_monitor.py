# interactive_terminal_process_monitor.py
import sys
import subprocess
import threading

class InteractiveTerminalMonitor:
    """
    FEAT-100: Interactive Terminal & Process Monitor
    Monitors long-running background processes and captures stdout/stderr.
    """
    def __init__(self):
        self.log_buffer = []

    def run_interactive(self, args: list[str], input_str: str = "") -> str:
        proc = subprocess.Popen(
            args,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        stdout, stderr = proc.communicate(input=input_str)
        self.log_buffer.extend(stdout.splitlines())
        self.log_buffer.extend(stderr.splitlines())
        return stdout
