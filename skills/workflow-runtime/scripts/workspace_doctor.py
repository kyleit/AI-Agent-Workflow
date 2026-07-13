import os
import sys
import json
import subprocess
import re

def get_tool_version(cmd: list) -> str:
    try:
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        out = res.stdout.strip()
        if not out:
            out = res.stderr.strip()
        return out.splitlines()[0] if out else "unknown"
    except Exception:
        return "not installed"

def check_virtual_env() -> str:
    # Check VIRTUAL_ENV env var first
    if "VIRTUAL_ENV" in os.environ:
        return os.environ["VIRTUAL_ENV"]
    # Check common virtual env folder locations
    for folder in [".venv", "venv", "env", ".env"]:
        if os.path.exists(folder) and os.path.isdir(folder):
            return os.path.abspath(folder)
    return "none"

def check_docker_daemon() -> bool:
    try:
        res = subprocess.run(["docker", "info"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=2)
        return res.returncode == 0
    except Exception:
        return False

def detect_project_stack(workspace_root: str) -> tuple[str, list[str], list[str]]:
    languages = []
    frameworks = []
    project_type = "unknown"
    
    # 1. Detect Go Project
    if os.path.exists(os.path.join(workspace_root, "go.mod")):
        languages.append("Go")
        project_type = "golang"
        
    # 2. Detect Python Project
    if os.path.exists(os.path.join(workspace_root, "pyproject.toml")) or os.path.exists(os.path.join(workspace_root, "requirements.txt")) or os.path.exists(os.path.join(workspace_root, "setup.py")):
        languages.append("Python")
        if project_type == "unknown":
            project_type = "python"
            
    # 3. Detect Node Project
    if os.path.exists(os.path.join(workspace_root, "package.json")):
        languages.append("JavaScript")
        if os.path.exists(os.path.join(workspace_root, "tsconfig.json")):
            languages.append("TypeScript")
        if project_type == "unknown":
            project_type = "node"
            
    # 4. Detect Wails Project
    if os.path.exists(os.path.join(workspace_root, "wails.json")):
        frameworks.append("Wails")
        project_type = "wails"
        
    # Standard clean architecture / fallback check
    if os.path.exists(os.path.join(workspace_root, "skills")):
        frameworks.append("AIWF")
        
    if not languages:
        languages = ["Python"]  # fallback default
    if project_type == "unknown":
        project_type = "python"
        
    return project_type, languages, frameworks

def main():
    workspace_root = "."
    if len(sys.argv) > 1:
        workspace_root = sys.argv[1]
        
    issues = []
    recommendations = []
    
    # 1. Project stack detection
    project_type, languages, frameworks = detect_project_stack(workspace_root)
    
    # 2. Environment check
    os_name = sys.platform
    virtual_env = check_virtual_env()
    
    # 3. Toolchain capability checks
    # Python
    py_ver = sys.version.split()[0]
    python_tool = {
        "installed": True,
        "version": py_ver
    }
    if virtual_env == "none":
        recommendations.append("Recommend creating a Python virtual environment (.venv) for library isolation.")
        
    # Git
    git_ver_raw = get_tool_version(["git", "--version"])
    is_git = git_ver_raw != "not installed"
    git_ver = git_ver_raw.replace("git version ", "") if is_git else "N/A"
    
    is_repo = False
    git_branch = "unknown"
    if is_git:
        try:
            is_repo = subprocess.run(["git", "rev-parse", "--is-inside-work-tree"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=workspace_root).stdout.decode().strip() == "true"
            if is_repo:
                git_branch = subprocess.run(["git", "branch", "--show-current"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=workspace_root).stdout.decode().strip()
        except Exception:
            pass
    else:
        issues.append("Git is not installed or not available on PATH.")
        
    git_tool = {
        "installed": is_git,
        "version": git_ver,
        "is_repository": is_repo,
        "branch": git_branch
    }
    
    # Golang
    go_ver_raw = get_tool_version(["go", "version"])
    is_go = go_ver_raw != "not installed"
    go_ver = "N/A"
    go_compat = "N/A"
    
    if is_go:
        m = re.search(r"go(\d+\.\d+\.?\d*)", go_ver_raw)
        if m:
            go_ver = m.group(1)
            
        # Check compatibility with go.mod
        go_mod_path = os.path.join(workspace_root, "go.mod")
        if os.path.exists(go_mod_path):
            try:
                with open(go_mod_path, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip().startswith("go "):
                            go_compat = line.strip().split()[1]
                            break
            except Exception:
                pass
    elif project_type == "golang" or project_type == "wails":
        issues.append("Golang is required but not installed.")
        
    golang_tool = {
        "installed": is_go,
        "version": go_ver,
        "compat": go_compat
    }
    
    # Node
    node_ver_raw = get_tool_version(["node", "--version"])
    is_node = node_ver_raw != "not installed"
    node_ver = node_ver_raw.replace("v", "") if is_node else "N/A"
    
    pkg_manager = "none"
    if is_node:
        if os.path.exists(os.path.join(workspace_root, "pnpm-lock.yaml")):
            pkg_manager = "pnpm"
        elif os.path.exists(os.path.join(workspace_root, "yarn.lock")):
            pkg_manager = "yarn"
        elif os.path.exists(os.path.join(workspace_root, "package-lock.json")):
            pkg_manager = "npm"
        else:
            pkg_manager = "npm"
    elif project_type == "node":
        issues.append("Node.js is required but not installed.")
        
    node_tool = {
        "installed": is_node,
        "version": node_ver,
        "package_manager": pkg_manager
    }
    
    # Docker
    docker_ver_raw = get_tool_version(["docker", "--version"])
    is_docker = docker_ver_raw != "not installed"
    docker_running = False
    if is_docker:
        docker_running = check_docker_daemon()
    else:
        recommendations.append("Docker is not installed. Containers are unavailable.")
        
    docker_tool = {
        "installed": is_docker,
        "daemon_running": docker_running
    }
    
    # Wails
    wails_ver_raw = get_tool_version(["wails", "version"])
    is_wails = wails_ver_raw != "not installed"
    wails_ver = wails_ver_raw.replace("v", "") if is_wails else "N/A"
    if not is_wails and project_type == "wails":
        issues.append("Wails CLI is required but not installed.")
        
    wails_tool = {
        "installed": is_wails,
        "version": wails_ver
    }
    
    # 4. AIWF Internal Validation
    # Permissions
    perm_path = os.path.join(workspace_root, ".agents", "config", "permissions.json")
    perm_exists = os.path.exists(perm_path)
    perm_init = False
    perm_mode = "none"
    if perm_exists:
        try:
            with open(perm_path, "r", encoding="utf-8") as f:
                pdata = json.load(f)
                perm_init = pdata.get("initialized") is True
                perm_mode = pdata.get("mode", "none")
        except Exception:
            issues.append("Failed to parse permissions.json.")
    else:
        issues.append("permissions.json config file is missing.")
        recommendations.append("Run 'python workflow_runtime.py permissions init' to initialize permissions.")
        
    # Runtime
    state_dir = os.path.join(workspace_root, ".agents", "state")
    config_dir = os.path.join(workspace_root, ".agents", "config")
    
    # Skills
    registry_path = os.path.join(workspace_root, ".agents", "skills", "registry.json")
    registry_exists = os.path.exists(registry_path)
    skills_count = 0
    if registry_exists:
        try:
            with open(registry_path, "r", encoding="utf-8") as f:
                skills_data = json.load(f)
                skills_count = len(skills_data) if isinstance(skills_data, dict) else 0
        except Exception:
            issues.append("Failed to parse skills registry.json.")
    else:
        issues.append("Skills registry.json is missing.")
        
    # Workflow
    wf_config_path = os.path.join(workspace_root, ".agents", "workflow.config.json")
    wf_config_exists = os.path.exists(wf_config_path)
    if not wf_config_exists:
        # Fallback check
        wf_config_path_2 = os.path.join(workspace_root, ".agents", "config", "workflow.config.json")
        wf_config_exists = os.path.exists(wf_config_path_2)
        
    supervisor_avail = False
    try:
        import importlib
        sys.path.insert(0, os.path.join(workspace_root, "skills", "workflow-runtime", "scripts"))
        _ = importlib.import_module("workflow_supervisor")
        _ = importlib.import_module("skill_router")
        supervisor_avail = True
    except Exception:
        issues.append("Workflow Supervisor / Skill Router modules cannot be loaded.")
        
    # 5. Status evaluation
    is_ready = len(issues) == 0 and perm_init and supervisor_avail
    status = "READY" if is_ready else "FAIL"
    
    report = {
        "status": status,
        "workspace": {
            "path": os.path.abspath(workspace_root),
            "project_type": project_type,
            "languages": languages,
            "frameworks": frameworks
        },
        "environment": {
            "os": os_name,
            "virtual_env": virtual_env
        },
        "toolchain": {
            "python": python_tool,
            "golang": golang_tool,
            "node": node_tool,
            "git": git_tool,
            "docker": docker_tool,
            "wails": wails_tool
        },
        "runtime": {
            "api_version": "v1",
            "state_dir_exists": os.path.exists(state_dir),
            "config_dir_exists": os.path.exists(config_dir)
        },
        "permissions": {
            "permissions_json_exists": perm_exists,
            "initialized": perm_init,
            "mode": perm_mode
        },
        "skills": {
            "registry_exists": registry_exists,
            "skills_count": skills_count
        },
        "workflow": {
            "config_exists": wf_config_exists,
            "supervisor_available": supervisor_avail
        },
        "issues": issues,
        "recommendations": recommendations
    }
    
    print(json.dumps(report, indent=2))
    sys.exit(0 if status == "READY" else 1)

def check_permissions(workspace_root: str) -> str:
    perm_path = os.path.join(workspace_root, ".agents", "config", "permissions.json")
    if os.path.exists(perm_path):
        try:
            with open(perm_path, "r", encoding="utf-8") as f:
                pdata = json.load(f)
                if pdata.get("initialized") is True:
                    return "PASS"
        except Exception:
            pass
    return "FAIL"

def check_skills(workspace_root: str) -> str:
    registry_path = os.path.join(workspace_root, ".agents", "skills", "registry.json")
    if os.path.exists(registry_path):
        try:
            with open(registry_path, "r", encoding="utf-8") as f:
                sdata = json.load(f)
                if isinstance(sdata, dict):
                    return "PASS"
        except Exception:
            pass
    return "FAIL"

def check_supervisor(workspace_root: str) -> str:
    try:
        import importlib
        sys.path.insert(0, os.path.join(workspace_root, "skills", "workflow-runtime", "scripts"))
        _ = importlib.import_module("workflow_supervisor")
        _ = importlib.import_module("skill_router")
        return "READY"
    except Exception:
        return "FAIL"

def get_runtime_mode(workspace_root: str) -> str:
    _ = workspace_root
    return "session"



if __name__ == "__main__":
    main()

