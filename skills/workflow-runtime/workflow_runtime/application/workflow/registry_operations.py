"""
workflow_runtime/application/workflow/registry_operations.py

Registry diagnostic, cleanup, and batch update operations for AIWF project registry.
"""
from __future__ import annotations

import platform
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, cast

from workflow_runtime.application.workflow.aiwf_registry import (
    is_aiwf_installed,
    load_registry,
    normalize_project_record,
    read_installed_aiwf_version,
    save_registry_atomic,
)


def doctor_registry() -> dict[str, Any]:
    """Check existence and AIWF state of all registered projects."""
    registry = load_registry()
    report_details: list[dict[str, Any]] = []
    active_count: int = 0
    missing_count: int = 0
    report: dict[str, Any] = {
        "registry_path": str(
            __import__(
                "workflow_runtime.application.workflow.aiwf_registry",
                fromlist=["get_registry_path"],
            ).get_registry_path()
        ),
        "total_registered": len(registry["projects"]),
        "active": 0,
        "missing": 0,
        "details": report_details,
    }

    changed = False
    normalized_projects: list[dict[str, Any]] = []
    projects_list = cast(list[dict[str, Any]], registry.get("projects", []))
    for p in projects_list:
        p, record_changed = normalize_project_record(p)
        normalized_projects.append(p)
        changed = changed or record_changed
        p_path = Path(p.get("path") or ".")
        p_status = p.get("status") or "active"
        issues: list[str] = []

        if not p_path.exists():
            p_status = "missing"
            issues.append("Project folder not found on disk")
        elif not is_aiwf_installed(p_path):
            issues.append("Missing .agents/ workspace skills installation")

        if p_status != p.get("status"):
            p["status"] = p_status
            changed = True

        if p_status == "active":
            installed_version = read_installed_aiwf_version(p_path)
            if (
                installed_version != "unknown"
                and installed_version != p.get("aiwf_version")
            ):
                p["aiwf_version"] = installed_version
                changed = True

        if p_status == "active":
            active_count += 1
        else:
            missing_count += 1

        report_details.append(
            {
                "name": p.get("name") or p_path.name,
                "path": p.get("path") or ".",
                "status": p_status,
                "aiwf_version": p.get("aiwf_version", "unknown"),
                "issues": issues,
            }
        )

    report["active"] = active_count
    report["missing"] = missing_count
    if changed:
        registry["projects"] = normalized_projects
        save_registry_atomic(registry)

    return report


def cleanup_registry() -> dict[str, Any]:
    """Remove all invalid or non-existent project paths from registry."""
    registry = load_registry()
    projects_list = cast(list[dict[str, Any]], registry.get("projects", []))
    initial_len = len(projects_list)

    valid_projects: list[dict[str, Any]] = []
    removed: list[str] = []
    projects_list = cast(list[dict[str, Any]], registry.get("projects", []))
    for p in projects_list:
        p_path = Path(p["path"])
        if p_path.exists():
            valid_projects.append(p)
        else:
            removed.append(p["path"])

    if len(valid_projects) < initial_len:
        registry["projects"] = valid_projects
        save_registry_atomic(registry)

    return {
        "total_removed": len(removed),
        "removed_paths": removed,
        "remaining": len(valid_projects),
    }


def update_all_projects() -> dict[str, Any]:
    """Update all active registered projects sequentially, handling individual errors."""
    registry = load_registry()

    summary_details: list[dict[str, Any]] = []
    updated_count: int = 0
    skipped_count: int = 0
    failed_count: int = 0
    missing_count: int = 0
    summary: dict[str, Any] = {
        "total": len(registry["projects"]),
        "updated": 0,
        "skipped": 0,
        "failed": 0,
        "missing": 0,
        "details": summary_details,
    }

    # Locate global update.sh script relative to runtime tool path
    script_dir = Path(__file__).resolve().parent
    framework_root = registry.get("framework_root")
    if framework_root and Path(framework_root).exists():
        root_dir = Path(framework_root)
    else:
        search_roots = [script_dir, *script_dir.parents]
        found_root = next(
            (
                curr
                for curr in search_roots
                if (curr / "update.sh").exists() or (curr / "update.ps1").exists()
            ),
            None,
        )
        root_dir = found_root if found_root else script_dir.parents[2]

    update_script_sh = root_dir / "update.sh"
    update_script_ps = root_dir / "update.ps1"

    changed = False
    projects_list = cast(list[dict[str, Any]], registry.get("projects", []))
    for p in projects_list:
        p_path = Path(p["path"])

        # Check path existence
        if not p_path.exists():
            p["status"] = "missing"
            changed = True
            missing_count += 1
            summary_details.append(
                {
                    "path": p["path"],
                    "status": "failed",
                    "reason": "Project path not found on disk",
                }
            )
            continue

        # Run local script to update the target project
        success = False
        reason = ""
        system = platform.system()

        try:
            if system == "Windows":
                # Execute PowerShell script
                if update_script_ps.exists():
                    # PowerShell named switch params use -Flag (single dash), NOT --flag
                    cmd = [
                        "powershell.exe",
                        "-ExecutionPolicy",
                        "Bypass",
                        "-File",
                        str(update_script_ps),
                        "-Force",
                    ]
                    # We pass CWD as the project path because update script targets project root
                    subprocess.run(
                        cmd,
                        cwd=str(p_path),
                        capture_output=True,
                        text=True,
                        check=True,
                    )
                    success = True
                else:
                    reason = "update.ps1 script not found in framework root"
            else:
                # Unix systems
                if update_script_sh.exists():
                    cmd = ["/usr/bin/env", "bash", str(update_script_sh), "--force"]
                    subprocess.run(
                        cmd,
                        cwd=str(p_path),
                        capture_output=True,
                        text=True,
                        check=True,
                    )
                    success = True
                else:
                    reason = "update.sh script not found in framework root"
        except subprocess.CalledProcessError as e:
            reason = (
                f"Update script exited with code {e.returncode}. "
                f"Error: {e.stderr.strip()}"
            )
        except Exception as exc:
            reason = f"Execution error: {exc}"

        if success:
            updated_count += 1
            p["last_updated_at"] = datetime.now().astimezone().isoformat()
            p["last_seen_at"] = p["last_updated_at"]
            p["status"] = "active"
            changed = True
            summary_details.append(
                {
                    "path": p["path"],
                    "status": "success",
                    "reason": "Updated successfully",
                }
            )
        else:
            failed_count += 1
            summary_details.append(
                {"path": p["path"], "status": "failed", "reason": reason}
            )

    summary["updated"] = updated_count
    summary["skipped"] = skipped_count
    summary["failed"] = failed_count
    summary["missing"] = missing_count
    if changed:
        save_registry_atomic(registry)

    return summary
