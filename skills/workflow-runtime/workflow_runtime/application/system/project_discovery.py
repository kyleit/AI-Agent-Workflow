# project_discovery.py
from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime
from typing import Any, cast

from workflow_runtime.application.ports.locator import InfrastructureLocator

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "memory"))


def build_visual_contract(frameworks: list[str]) -> dict[str, Any]:
    """Return the AI-facing visual contract for the detected UI technology."""
    names = {str(framework).strip().lower() for framework in frameworks}
    frontend_names = {
        "react", "vue", "svelte", "sveltekit", "next.js", "nuxt", "angular", "vite"
    }
    desktop_names = {"wails", "tauri", "electron"}
    mobile_names = {"flutter", "react native"}
    if names & frontend_names:
        kind, reason = "frontend", "Detected frontend UI framework"
    elif names & desktop_names:
        kind, reason = "desktop", "Detected desktop webview framework"
    elif names & mobile_names:
        kind, reason = "mobile", "Detected mobile UI framework"
    else:
        return {
            "required": False,
            "type": "none",
            "reason": "No UI framework detected",
            "e2e_required": False,
            "mode": "none",
            "viewport_order": ["mobile", "desktop", "tablet"],
            "viewports": {"mobile": [375, 390], "desktop": [1440, 1920], "tablet": [768, 820]},
            "completion_gate": "not_required",
        }
    return {
        "required": True,
        "type": kind,
        "reason": reason,
        "e2e_required": True,
        "mode": "real-browser",
        "viewport_order": ["mobile", "desktop", "tablet"],
        "viewports": {"mobile": [375, 390], "desktop": [1440, 1920], "tablet": [768, 820]},
        "completion_gate": "required",
    }


def run_discovery() -> dict[str, Any]:
    os.makedirs(".agents", exist_ok=True)

    scanner_cls: Any = getattr(InfrastructureLocator, "ProjectScanner", None)
    scanner: Any = scanner_cls() if callable(scanner_cls) else None
    analyzer = InfrastructureLocator.ProjectAnalyzer()

    detect_lang_fn: Any = getattr(scanner, "detect_languages", None)
    raw_languages: Any = detect_lang_fn() if callable(detect_lang_fn) else []
    languages: list[str] = [str(l) for l in cast(list[Any], raw_languages)] if isinstance(raw_languages, list) else []

    detect_fw_fn: Any = getattr(scanner, "detect_frameworks", None)
    raw_frameworks: Any = detect_fw_fn(languages) if callable(detect_fw_fn) else []
    frameworks: list[str] = [str(f) for f in cast(list[Any], raw_frameworks)] if isinstance(raw_frameworks, list) else []

    analyzer.analyze_modules()

    raw_db_info: Any = analyzer.get_database_info()
    databases: list[str] = [str(cast(dict[str, Any], db).get("type", "")) for db in cast(list[Any], raw_db_info) if isinstance(db, dict)] if isinstance(raw_db_info, list) else []

    detect_build_fn: Any = getattr(scanner, "detect_build_commands", None)
    raw_build_cmds: Any = detect_build_fn() if callable(detect_build_fn) else []
    build_cmds: list[dict[str, Any]] = [cast(dict[str, Any], cmd) for cmd in cast(list[Any], raw_build_cmds) if isinstance(cmd, dict)] if isinstance(raw_build_cmds, list) else []

    pkg_managers: list[str] = []
    if os.path.exists("package.json"):
        pkg_managers.append("npm")
    if os.path.exists("pnpm-lock.yaml"):
        pkg_managers.append("pnpm")
    if os.path.exists("yarn.lock"):
        pkg_managers.append("yarn")
    if not pkg_managers:
        pkg_managers = ["unknown"]

    test_tools: list[str] = []
    if "Python" in languages:
        test_tools.append("pytest")
    if "Go" in languages:
        test_tools.append("go test")
    if "Node.js" in frameworks or "React" in frameworks or "Svelte" in frameworks:
        test_tools.append("vitest")
    if not test_tools:
        test_tools = ["none"]

    quality_gates: list[str] = ["build", "lint"]
    if test_tools != ["none"]:
        quality_gates.append("test")

    ui_frameworks = ["React", "Vue", "Svelte", "SvelteKit", "Next.js", "Nuxt", "Angular", "Vite"]
    detected_ui = [fw for fw in ui_frameworks if fw in frameworks]
    visual_debug = build_visual_contract(frameworks)
    if visual_debug["required"]:
        quality_gates.append("visual_debug")

    recommended_workflow: list[dict[str, Any]] = [
        { "name": "Workspace Initialization", "skill": "initialize-workflow", "command": "init", "agent": "architect", "logs": ["> Scanning workspace structure...", "> Loading project rules & policies", "> Checking Git environment status"] },
        { "name": "Memory & Environment Load", "skill": "project-memory-update", "command": "memory-sync", "agent": "architect", "logs": ["> Scanning file system modifications...", "> Syncing RAG search vectors", "> Memory index updated successfully"] },
        { "name": "Architecture Analysis", "skill": "brainstorming", "command": "brainstorm", "agent": "planner", "logs": ["> Discovering system requirements...", "> Checking constraint validation", "> Readiness score: 85/100"] },
        { "name": "Implementation Plan", "skill": "planning-prompt-to-plan", "command": "plan", "agent": "planner", "logs": ["> Generating project implementation plan...", "> Estimating complexity & risks", "> Defining verification checklists"] },
        { "name": "Technical Blueprint", "skill": "plan-to-blueprint", "command": "blueprint", "agent": "architect", "logs": ["> Generating technical design specifications...", "> Writing module dependencies and schemas", "> Designing class signatures and APIs"] },
        { "name": "Code Generation", "skill": "blueprint-to-implementation", "command": "implement", "agent": "coder", "logs": ["> Generating logic modifications...", "> Editing source code files", "> Applying incremental code diffs"] },
        { "name": "Quality Debugging", "skill": "implementation-to-debug", "command": "debug", "agent": "coder", "logs": ["> Compiling the codebase...", "> Running linters and formatting code", "> Fixing failing test cases and improving logs"] }
    ]

    if bool(visual_debug.get("required")):
        vtype = str(visual_debug.get("type", ""))
        recommended_workflow.append({
            "name": "Frontend Visual Debug" if vtype == "frontend" else "UI Visual Debug",
            "skill": "frontend-visual-debug",
            "command": "visual-debug",
            "agent": "frontend-qa",
            "logs": ["> Opening browser...", "> Inspecting layout..."],
            "conditional": vtype
        })

    recommended_workflow.extend([
        { "name": "Feature Verification", "skill": "debug-to-verify", "command": "verify", "agent": "reviewer", "logs": ["> Reviewing blueprint compliance...", "> Testing acceptance criteria and performance", "> Performing final code audits and security checks"] },
        { "name": "Release & Documentation", "skill": "implementation-to-release", "command": "release", "agent": "release-manager", "logs": ["> Bumping package version...", "> Generating change logs", "> Committing & pushing to git repository"] }
    ])

    profile: dict[str, Any] = {
        "project_id": os.path.basename(os.getcwd()),
        "detected_at": datetime.now().astimezone().isoformat(),
        "languages": [l.lower() for l in languages],
        "frameworks": [f.lower() for f in frameworks],
        "platforms": ["web" if "Node.js" in frameworks or detected_ui else "cli"],
        "package_managers": pkg_managers,
        "build_tools": [str(cmd.get("name", "")).lower() for cmd in build_cmds] or ["none"],
        "test_tools": test_tools,
        "lint_tools": ["eslint"] if "Node.js" in frameworks else ["ruff"],
        "format_tools": ["prettier"] if "Node.js" in frameworks else ["black"],
        "typecheck_tools": ["typescript"] if "TypeScript" in languages else ["none"],
        "databases": databases or ["none"],
        "infra": ["none"],
        "quality_gates": quality_gates,
        "visual_debug": visual_debug,
        "visual_e2e": dict(visual_debug),
        "recommended_workflow": recommended_workflow
    }

    profile_path = os.path.join(".agents", "project-profile.json")
    with open(profile_path, "w", encoding="utf-8") as f:
        json.dump(profile, f, indent=2, ensure_ascii=False)

    release_config_path = os.path.join(".agents", "release.config.json")
    files_written: list[str] = [profile_path]
    if not os.path.exists(release_config_path):
        version_file = "MANIFEST.json"
        if os.path.exists("package.json"):
            version_file = "package.json"
        elif os.path.exists("pyproject.toml"):
            version_file = "pyproject.toml"
        elif os.path.exists("setup.py"):
            version_file = "setup.py"
        elif os.path.exists("cargo.toml"):
            version_file = "cargo.toml"
        elif os.path.exists("go.mod"):
            version_file = "go.mod"

        release_config: dict[str, Any] = {
            "project_type": "single",
            "modules": [
                {
                    "name": "core",
                    "path": ".",
                    "version_file": version_file,
                    "changelog_file": "CHANGELOG.md"
                }
            ],
            "default_branch": "main",
            "remote_name": "origin"
        }

        try:
            git_res = subprocess.run(["git", "symbolic-ref", "--short", "HEAD"], capture_output=True, text=True)
            if git_res.returncode == 0 and git_res.stdout.strip():
                release_config["default_branch"] = git_res.stdout.strip()
        except Exception:
            pass

        with open(release_config_path, "w", encoding="utf-8") as f:
            json.dump(release_config, f, indent=2, ensure_ascii=False)
        files_written.append(release_config_path)

    workflow_config_path = os.path.join(".agents", "workflow.config.json")
    if not os.path.exists(workflow_config_path):
        workflow_template_path = os.path.join(".agents", "templates", "workflow.config.json.template")
        workflow_config: dict[str, Any] | None = None
        if os.path.exists(workflow_template_path):
            try:
                with open(workflow_template_path, "r", encoding="utf-8") as tf:
                    loaded = json.load(tf)
                    if isinstance(loaded, dict):
                        workflow_config = cast(dict[str, Any], loaded)
            except Exception:
                pass

        if not workflow_config:
            workflow_config = {
                "project_name": "example-project",
                "git_flow": {
                    "development_branch": "main",
                    "release_branch": "main",
                    "sync_method": "merge",
                    "extra_push_branches": []
                },
                "release_pipeline": {
                    "steps": ["bump_version", "update_changelog", "git_commit", "git_tag", "custom_commands", "git_push"],
                    "custom_commands": {
                        "core": ["echo 'Chạy lệnh build/test cho module core ở đây!'"],
                        "global": ["echo 'Chạy lệnh release global ở đây!'"]
                    }
                }
            }

        workflow_config["project_name"] = os.path.basename(os.getcwd())
        try:
            git_res = subprocess.run(["git", "symbolic-ref", "--short", "HEAD"], capture_output=True, text=True)
            if git_res.returncode == 0 and git_res.stdout.strip():
                branch = git_res.stdout.strip()
                raw_git_flow = workflow_config.get("git_flow")
                if isinstance(raw_git_flow, dict):
                    git_flow = cast(dict[str, Any], raw_git_flow)
                    git_flow["development_branch"] = branch
                    git_flow["release_branch"] = branch
        except Exception:
            pass

        with open(workflow_config_path, "w", encoding="utf-8") as f:
            json.dump(workflow_config, f, indent=2, ensure_ascii=False)
        files_written.append(workflow_config_path)

    return {
        "status": "success",
        "command": "discover",
        "summary": f"Technologies detected: Languages={languages}, Frameworks={frameworks}.",
        "warnings": [],
        "files_read": [],
        "files_written": files_written,
        "next_skill": "project-memory-bootstrap"
    }


__all__ = ["build_visual_contract", "run_discovery"]
