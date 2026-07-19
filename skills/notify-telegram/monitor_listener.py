# skills/notify-telegram/monitor_listener.py
import os
import sys
import time
import json
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

if sys.platform == "win32":
    py_dir = os.path.dirname(sys.executable)
    if py_dir not in os.environ.get("PATH", ""):
        os.environ["PATH"] = py_dir + os.pathsep + os.environ.get("PATH", "")
    try:
        os.add_dll_directory(py_dir)
    except Exception:
        pass


# Resolve project name and slug aligned with projects.json
project_name = os.path.basename(os.path.abspath("."))
try:
    # 1. Resolve registry path
    import platform
    system = platform.system()
    reg_dir = Path.home() / ".config" / "aiwf"
    if system == "Windows":
        appdata = os.environ.get("APPDATA")
        if appdata:
            reg_dir = Path(appdata) / "aiwf"
    elif system == "Darwin":
        reg_dir = Path.home() / "Library" / "Application Support" / "aiwf"
    
    reg_path = reg_dir / "projects.json"
    if reg_path.exists():
        with open(reg_path, "r", encoding="utf-8") as f:
            registry = json.load(f)
        curr_abs = str(Path(".").resolve()).lower()
        for p in registry.get("projects", []):
            if str(Path(p["path"]).resolve()).lower() == curr_abs:
                project_name = p["name"]
                break
except Exception:
    pass
        
project_slug = project_name.replace("-", "_").lower()
global_inbox = Path.home() / ".aiwf" / project_slug / "inbox.json"
local_inbox = Path("scratch") / "telegram-inbox.json"

print(f"Monitoring global inbox: {global_inbox}", flush=True)

# Give it a moment to initialize
time.sleep(1)

# Get initial state of the global inbox file
last_mtime = 0
last_size = 0


while True:
    if global_inbox.exists():
        try:
            stat = global_inbox.stat()
            mtime = stat.st_mtime
            size = stat.st_size
            
            # If the file is modified or newly created
            if mtime != last_mtime or size != last_size or last_mtime == 0:
                print("Change detected in global inbox. Copying to local workspace...", flush=True)
                
                # Read from global
                with open(global_inbox, "r", encoding="utf-8") as f:
                    content = f.read()
                    
                # Write to local inbox
                local_inbox.parent.mkdir(parents=True, exist_ok=True)
                with open(local_inbox, "w", encoding="utf-8") as f:
                    f.write(content)
                    
                # Clean up global inbox to avoid double-processing
                try:
                    global_inbox.unlink()
                except Exception:
                    pass
        except Exception as e:
            print(f"Error checking global inbox: {e}", file=sys.stderr)
            
    time.sleep(2)
