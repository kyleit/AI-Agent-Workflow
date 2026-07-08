# project_discovery.py
import os
import json
from datetime import datetime
import sys

# Add memory/ directory to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "memory"))

from memory.scanner import ProjectScanner
from memory.analyzer import ProjectAnalyzer

def run_discovery() -> dict:
    os.makedirs(".agents", exist_ok=True)
    
    scanner = ProjectScanner()
    analyzer = ProjectAnalyzer()
    
    languages = scanner.detect_languages()
    frameworks = scanner.detect_frameworks(languages)
    modules = analyzer.analyze_modules()
    databases = [db["type"] for db in analyzer.get_database_info()]
    build_cmds = scanner.detect_build_commands()
    
    # Simple maps
    pkg_managers = []
    if os.path.exists("package.json"):
        pkg_managers.append("npm")
    if os.path.exists("pnpm-lock.yaml"):
        pkg_managers.append("pnpm")
    if os.path.exists("yarn.lock"):
        pkg_managers.append("yarn")
    if not pkg_managers:
        pkg_managers = ["unknown"]
        
    test_tools = []
    if "Python" in languages:
        test_tools.append("pytest")
    if "Go" in languages:
        test_tools.append("go test")
    if "Node.js" in frameworks or "React" in frameworks or "Svelte" in frameworks:
        test_tools.append("vitest")
    if not test_tools:
        test_tools = ["none"]
        
    # Setup quality gates
    quality_gates = ["build", "lint"]
    if test_tools != ["none"]:
        quality_gates.append("test")
        
    visual_debug = {
        "required": False,
        "type": "none",
        "reason": "No UI framework detected"
    }
    
    # Visual debug check
    ui_frameworks = ["React", "Vue", "Svelte", "SvelteKit", "Next.js", "Nuxt", "Angular", "Vite"]
    detected_ui = [fw for fw in ui_frameworks if fw in frameworks]
    if detected_ui:
        visual_debug = {
            "required": True,
            "type": "frontend",
            "reason": f"Detected frontend UI framework: {detected_ui[0]}"
        }
        quality_gates.append("visual_debug")
    elif any(fw in frameworks for fw in ["Wails", "Tauri", "Electron"]):
        visual_debug = {
            "required": True,
            "type": "desktop",
            "reason": "Detected Wails/Tauri/Electron Desktop Framework"
        }
        quality_gates.append("visual_debug")
    elif any(fw in frameworks for fw in ["Flutter", "React Native"]):
        visual_debug = {
            "required": True,
            "type": "mobile",
            "reason": "Detected mobile framework"
        }
        quality_gates.append("visual_debug")
        
    # Build recommended workflow list
    recommended_workflow = [
        { "name": "Workspace Initialization", "skill": "initialize-workflow", "command": "init", "agent": "architect", "logs": ["> Scanning workspace structure...", "> Loading project rules & policies", "> Checking Git environment status"] },
        { "name": "Memory & Environment Load", "skill": "project-memory-update", "command": "memory-sync", "agent": "architect", "logs": ["> Scanning file system modifications...", "> Syncing RAG search vectors", "> Memory index updated successfully"] },
        { "name": "Architecture Analysis", "skill": "brainstorming", "command": "brainstorm", "agent": "planner", "logs": ["> Discovering system requirements...", "> Checking constraint validation", "> Readiness score: 85/100"] },
        { "name": "Implementation Plan", "skill": "planning-prompt-to-plan", "command": "plan", "agent": "planner", "logs": ["> Generating project implementation plan...", "> Estimating complexity & risks", "> Defining verification checklists"] },
        { "name": "Technical Blueprint", "skill": "plan-to-blueprint", "command": "blueprint", "agent": "architect", "logs": ["> Generating technical design specifications...", "> Writing module dependencies and schemas", "> Designing class signatures and APIs"] },
        { "name": "Code Generation", "skill": "blueprint-to-implementation", "command": "implement", "agent": "coder", "logs": ["> Generating logic modifications...", "> Editing source code files", "> Applying incremental code diffs"] },
        { "name": "Quality Debugging", "skill": "implementation-to-debug", "command": "debug", "agent": "coder", "logs": ["> Compiling the codebase...", "> Running linters and formatting code", "> Fixing failing test cases and improving logs"] }
    ]
    
    if visual_debug["required"]:
        recommended_workflow.append({
            "name": "Frontend Visual Debug" if visual_debug["type"] == "frontend" else "UI Visual Debug",
            "skill": "frontend-visual-debug",
            "command": "visual-debug",
            "agent": "frontend-qa",
            "logs": ["> Opening browser...", "> Inspecting layout..."],
            "conditional": visual_debug["type"]
        })
        
    recommended_workflow.extend([
        { "name": "Feature Verification", "skill": "debug-to-verify", "command": "verify", "agent": "reviewer", "logs": ["> Reviewing blueprint compliance...", "> Testing acceptance criteria and performance", "> Performing final code audits and security checks"] },
        { "name": "Release & Documentation", "skill": "implementation-to-release", "command": "release", "agent": "release-manager", "logs": ["> Bumping package version...", "> Generating change logs", "> Committing & pushing to git repository"] }
    ])
    
    profile = {
        "project_id": os.path.basename(os.getcwd()),
        "detected_at": datetime.now().astimezone().isoformat(),
        "languages": [l.lower() for l in languages],
        "frameworks": [f.lower() for f in frameworks],
        "platforms": ["web" if "Node.js" in frameworks or detected_ui else "cli"],
        "package_managers": pkg_managers,
        "build_tools": [cmd["name"].lower() for cmd in build_cmds] or ["none"],
        "test_tools": test_tools,
        "lint_tools": ["eslint"] if "Node.js" in frameworks else ["ruff"],
        "format_tools": ["prettier"] if "Node.js" in frameworks else ["black"],
        "typecheck_tools": ["typescript"] if "TypeScript" in languages else ["none"],
        "databases": databases or ["none"],
        "infra": ["none"],
        "quality_gates": quality_gates,
        "visual_debug": visual_debug,
        "recommended_workflow": recommended_workflow
    }
    
    profile_path = os.path.join(".agents", "project-profile.json")
    with open(profile_path, "w", encoding="utf-8") as f:
        json.dump(profile, f, indent=2, ensure_ascii=False)
        
    return {
        "status": "success",
        "command": "discover",
        "summary": f"Technologies detected: Languages={languages}, Frameworks={frameworks}.",
        "warnings": [],
        "files_read": [],
        "files_written": [profile_path],
        "next_skill": "project-memory-bootstrap"
    }
