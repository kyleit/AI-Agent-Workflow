# conftest.py
import os
import sys
import shutil
import tempfile
import pytest
import subprocess

ORIG_CWD = os.getcwd()

# Global patch of subprocess.run to rewrite relative paths of workflow_runtime.py
# to absolute paths from the original workspace root.
_orig_subprocess_run = subprocess.run

def _patched_subprocess_run(*args, **kwargs):
    if args and isinstance(args[0], list):
        cmd = list(args[0])
        for i, val in enumerate(cmd):
            if "workflow_runtime.py" in val and not os.path.isabs(val):
                # Rewrite to absolute path in original workspace
                cmd[i] = os.path.abspath(os.path.join(ORIG_CWD, "skills", "workflow-runtime", "scripts", "workflow_runtime.py"))
        # Force inheritance of environment variables
        env = kwargs.get("env", os.environ).copy()
        env["PYTHONPATH"] = ORIG_CWD + os.pathsep + os.path.join(ORIG_CWD, "skills", "workflow-runtime", "scripts") + os.pathsep + env.get("PYTHONPATH", "")
        env["AIWF_RUNTIME_MODE"] = "normal"
        env["AIWF_DISABLE_STATE_WRITES"] = "false"
        kwargs["env"] = env
        return _orig_subprocess_run(cmd, *args[1:], **kwargs)
    return _orig_subprocess_run(*args, **kwargs)

subprocess.run = _patched_subprocess_run

@pytest.fixture(autouse=True, scope="function")
def isolated_workspace():
    # 1. Create a unique isolated root directory under OS temp
    temp_workspace = tempfile.mkdtemp(prefix="aiwf-test-ws-")
    
    # 2. Replicate the necessary .agents folder structure
    src_agents = os.path.abspath(os.path.join(ORIG_CWD, ".agents"))
    dst_agents = os.path.join(temp_workspace, ".agents")
    
    if os.path.exists(src_agents):
        os.makedirs(dst_agents, exist_ok=True)
        for item in os.listdir(src_agents):
            s = os.path.join(src_agents, item)
            d = os.path.join(dst_agents, item)
            # Skip states, locks, and history database to ensure a clean slate
            if item in ["state", "runtime", "memory-state.json", "history.db"]:
                continue
            try:
                if os.path.isdir(s):
                    shutil.copytree(s, d, dirs_exist_ok=True)
                else:
                    shutil.copy2(s, d)
            except Exception:
                pass
                
    # Replicate root agents, skills, and templates folders for test execution dependencies
    for root_dir in ["agents", "skills", "templates"]:
        src_dir = os.path.join(ORIG_CWD, root_dir)
        if os.path.exists(src_dir):
            try:
                shutil.copytree(src_dir, os.path.join(temp_workspace, root_dir), dirs_exist_ok=True)
            except Exception:
                pass
                
    # Copy root scripts and manifests needed by installers/tests
    for root_file in ["install.ps1", "install.sh", "update.ps1", "update.sh", "AGENTS.md", "AI_RULES.md", "MANIFEST.json"]:
        src_file = os.path.join(ORIG_CWD, root_file)
        if os.path.exists(src_file):
            try:
                shutil.copy2(src_file, os.path.join(temp_workspace, root_file))
            except Exception:
                pass
                
    # 3. Change directory to the isolated workspace
    os.chdir(temp_workspace)
    
    # Add script path to sys.path so test imports resolved from memory work
    sys.path.insert(0, os.path.join(ORIG_CWD, "skills", "workflow-runtime", "scripts"))
    
    # Reset state store singleton to force re-initialization relative to new CWD
    try:
        from state_store import reset_state_store
        reset_state_store(None)
    except Exception:
        pass
    
    yield temp_workspace
    
    # Restore original CWD and clean up sys.path
    os.chdir(ORIG_CWD)
    if os.path.join(ORIG_CWD, "skills", "workflow-runtime", "scripts") in sys.path:
        sys.path.remove(os.path.join(ORIG_CWD, "skills", "workflow-runtime", "scripts"))
        
    # Clean up isolated state folder
    try:
        shutil.rmtree(temp_workspace, ignore_errors=True)
    except Exception:
        pass
