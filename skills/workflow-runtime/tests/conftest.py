# conftest.py
import os
import sys
import shutil
import tempfile
import pytest
import subprocess
import signal
import warnings

# Filter line buffering runtime warnings in binary mode
warnings.filterwarnings("ignore", category=RuntimeWarning, message="line buffering.*")

ORIG_CWD = os.getcwd()
_spawned_processes = []
_orig_Popen = subprocess.Popen

def kill_process_tree(pid: int):
    try:
        import psutil
        parent = psutil.Process(pid)
        for child in parent.children(recursive=True):
            try:
                child.kill()
            except Exception:
                pass
        try:
            parent.kill()
        except Exception:
            pass
    except Exception:
        try:
            if os.name == 'nt':
                subprocess.run(['taskkill', '/F', '/T', '/PID', str(pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                os.kill(pid, signal.SIGKILL)
        except Exception:
            pass

class PatchedPopen(_orig_Popen):
    def __init__(self, args, **kwargs):
        if isinstance(args, list):
            args = list(args)
            for i, val in enumerate(args):
                if "workflow_runtime.py" in val and not os.path.isabs(val):
                    args[i] = os.path.abspath(os.path.join(ORIG_CWD, "skills", "workflow-runtime", "scripts", "workflow_runtime.py"))
        
        env = kwargs.get("env", os.environ).copy()
        env["PYTHONPATH"] = ORIG_CWD + os.pathsep + os.path.join(ORIG_CWD, "skills", "workflow-runtime", "scripts") + os.pathsep + env.get("PYTHONPATH", "")
        env["AIWF_RUNTIME_MODE"] = "normal"
        env["AIWF_DISABLE_STATE_WRITES"] = "false"
        env.pop("AIWF_STATE_ROOT", None)
        env.pop("AIWF_PERMISSION_CONFIG_ROOT", None)
        kwargs["env"] = env
        
        super().__init__(args, **kwargs)
        _spawned_processes.append(self)

subprocess.Popen = PatchedPopen

@pytest.fixture(autouse=True, scope="function")
def isolated_workspace():
    temp_workspace = tempfile.mkdtemp(prefix="aiwf-test-ws-")
    
    src_agents = os.path.abspath(os.path.join(ORIG_CWD, ".agents"))
    dst_agents = os.path.join(temp_workspace, ".agents")
    
    if os.path.exists(src_agents):
        os.makedirs(dst_agents, exist_ok=True)
        for item in os.listdir(src_agents):
            s = os.path.join(src_agents, item)
            d = os.path.join(dst_agents, item)
            if item in ["state", "runtime", "config", "memory-state.json", "history.db"]:
                continue
            try:
                if os.path.isdir(s):
                    shutil.copytree(s, d, dirs_exist_ok=True)
                else:
                    shutil.copy2(s, d)
            except Exception:
                pass
                
    for root_dir in ["agents", "skills", "templates"]:
        src_dir = os.path.join(ORIG_CWD, root_dir)
        if os.path.exists(src_dir):
            try:
                shutil.copytree(src_dir, os.path.join(temp_workspace, root_dir), dirs_exist_ok=True)
            except Exception:
                pass
                
    for root_file in ["install.ps1", "install.sh", "update.ps1", "update.sh", "AGENTS.md", "AI_RULES.md", "MANIFEST.json"]:
        src_file = os.path.join(ORIG_CWD, root_file)
        if os.path.exists(src_file):
            try:
                shutil.copy2(src_file, os.path.join(temp_workspace, root_file))
            except Exception:
                pass
                
    os.chdir(temp_workspace)
    sys.path.insert(0, os.path.join(ORIG_CWD, "skills", "workflow-runtime", "scripts"))
    
    try:
        from state_store import reset_state_store
        reset_state_store(None)
    except Exception:
        pass

    orig_env = {
        "AIWF_STATE_ROOT": os.environ.get("AIWF_STATE_ROOT"),
        "AIWF_PERMISSION_CONFIG_ROOT": os.environ.get("AIWF_PERMISSION_CONFIG_ROOT"),
        "AIWF_TESTING_PERMISSIONS": os.environ.get("AIWF_TESTING_PERMISSIONS")
    }
    
    os.environ.pop("AIWF_STATE_ROOT", None)
    os.environ.pop("AIWF_PERMISSION_CONFIG_ROOT", None)
    os.environ.pop("AIWF_TESTING_PERMISSIONS", None)
    
    yield temp_workspace
    
    os.chdir(ORIG_CWD)
    if os.path.join(ORIG_CWD, "skills", "workflow-runtime", "scripts") in sys.path:
        sys.path.remove(os.path.join(ORIG_CWD, "skills", "workflow-runtime", "scripts"))
        
    for proc in _spawned_processes:
        if proc.poll() is None:
            try:
                kill_process_tree(proc.pid)
            except Exception:
                pass
    _spawned_processes.clear()

    for k, v in orig_env.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v
            
    try:
        shutil.rmtree(temp_workspace, ignore_errors=True)
    except Exception:
        pass
