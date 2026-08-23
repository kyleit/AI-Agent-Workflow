# conftest.py -- QUICK-038: standardized to python -m workflow_runtime entry point
import os
import sys
import shutil
import tempfile
import subprocess
import pytest

ORIG_CWD = os.getcwd()

# Absolute path to skills/workflow-runtime (where workflow_runtime package lives)
# conftest.py is at: skills/workflow-runtime/tests/conftest.py
# so the package root is two levels up from tests/
_CONFTEST_DIR = os.path.dirname(os.path.abspath(__file__))
_RUNTIME_PKG_ROOT = os.path.abspath(os.path.join(_CONFTEST_DIR, ".."))


def run_cli(
    *args: str,
    cwd: str | None = None,
    capture_output: bool = True,
    text: bool = True,
    env: dict | None = None,
    **kwargs,
) -> subprocess.CompletedProcess:
    """Run `python -m workflow_runtime <args>` as subprocess.

    PYTHONPATH is automatically set to `skills/workflow-runtime`
    (resolved relative to this conftest.py) so the module is resolvable
    regardless of where pytest is launched from.
    """
    base_env = os.environ.copy()
    base_env["PYTHONPATH"] = _RUNTIME_PKG_ROOT + os.pathsep + base_env.get("PYTHONPATH", "")
    if env:
        base_env.update(env)
    return subprocess.run(
        [sys.executable, "-m", "workflow_runtime", *args],
        cwd=cwd or os.getcwd(),
        capture_output=capture_output,
        text=text,
        env=base_env,
        **kwargs,
    )


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

    # Reset state store singleton to force re-initialization relative to new CWD
    try:
        from workflow_runtime.infrastructure.session.session import reset_state_store
        reset_state_store(None)
    except Exception:
        pass

    yield temp_workspace

    # Restore original CWD
    os.chdir(ORIG_CWD)

    # Clean up isolated state folder
    try:
        shutil.rmtree(temp_workspace, ignore_errors=True)
    except Exception:
        pass
