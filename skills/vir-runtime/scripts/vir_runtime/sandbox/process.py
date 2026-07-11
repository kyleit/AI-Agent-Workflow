# File path: vir_runtime/sandbox/process.py
import subprocess
import os

try:
    import psutil
except ImportError:
    psutil = None

class WindowsProcessManager:
    @staticmethod
    def terminate_process_tree(pid: int) -> None:
        """Force terminate a process and all its child processes recursively."""
        if psutil:
            try:
                parent = psutil.Process(pid)
                children = parent.children(recursive=True)
                for child in children:
                    try:
                        child.terminate()
                    except psutil.NoSuchProcess:
                        pass
                
                # Wait a brief moment for children to terminate, then force kill
                gone, alive = psutil.wait_procs(children, timeout=3)
                for alive_proc in alive:
                    try:
                        alive_proc.kill()
                    except psutil.NoSuchProcess:
                        pass
                
                # Finally, terminate the parent
                try:
                    parent.terminate()
                    parent.wait(timeout=3)
                except (psutil.NoSuchProcess, psutil.TimeoutExpired):
                    try:
                        parent.kill()
                    except psutil.NoSuchProcess:
                        pass
            except psutil.NoSuchProcess:
                pass
        else:
            # Fallback using Windows taskkill command
            print("[WindowsProcessManager] psutil not available. Falling back to taskkill.")
            try:
                subprocess.run(
                    ["taskkill", "/F", "/T", "/PID", str(pid)],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=False
                )
            except Exception as e:
                print(f"[WindowsProcessManager] Fallback taskkill failed: {e}")
