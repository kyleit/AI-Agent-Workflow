from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Any

from workflow_runtime.application.command_contract import CommandResult, NextAction, emit_result
from workflow_runtime.application.system.global_inventory import GlobalInstallationInventory
from workflow_runtime.application.system.project_sync import ProjectSyncPlanner
from workflow_runtime.application.system.source_upgrade import (
    DEFAULT_REPOSITORY_URL,
    SourceUpgradeService,
    UpgradeRequest,
)


def _framework_root() -> Path:
    configured = os.environ.get("AIWF_FRAMEWORK_ROOT")
    if configured and Path(configured).exists():
        return Path(configured).resolve()
    probe = Path(__file__).resolve()
    for parent in probe.parents:
        if (parent / "MANIFEST.json").exists() and (parent / "update.ps1").exists():
            return parent
    return Path.cwd().resolve()


def _project_path() -> Path:
    cwd = Path.cwd().resolve()
    if (cwd / ".agents").is_dir():
        return cwd
    return cwd


def _source_request(args: argparse.Namespace, root: Path, *, execute: bool) -> UpgradeRequest:
    return UpgradeRequest(
        source_path=str(root),
        repository_url=os.environ.get("AIWF_SOURCE_REPOSITORY_URL", DEFAULT_REPOSITORY_URL),
        remote_name=os.environ.get("AIWF_SOURCE_REMOTE", "origin"),
        branch=os.environ.get("AIWF_SOURCE_BRANCH", "main"),
        tag=None,
        check=bool(getattr(args, "check", False)),
        dry_run=bool(getattr(args, "dry_run", False)),
        yes=execute or bool(getattr(args, "yes", False)) or bool(getattr(args, "force", False)),
        json_output=bool(getattr(args, "json", False)),
    )


def _global_update(args: argparse.Namespace, root: Path) -> dict[str, Any]:
    request = _source_request(args, root, execute=True)
    service = SourceUpgradeService(root.as_posix(), request.remote_name, request.repository_url, request.branch)
    return service.execute(request).payload()


def _sync_projects(args: argparse.Namespace, snapshot: Any, projects: list[dict[str, Any]]) -> list[dict[str, Any]]:
    planner = ProjectSyncPlanner()
    details: list[dict[str, Any]] = []
    for record in projects:
        path = Path(str(record.get("path") or ".")).expanduser()
        if not path.exists():
            details.append({"path": str(path), "status": "missing", "reason": "PROJECT_PATH_NOT_FOUND"})
            continue
        plan = planner.plan(path, snapshot)
        dry_run = bool(getattr(args, "dry_run", False) or getattr(args, "check", False))
        changed = planner.sync(plan, snapshot, dry_run=dry_run)
        details.append({
            "path": str(path.resolve()),
            "status": "updated" if changed else "skipped",
            "required_assets": plan.required_assets,
            "missing_assets": plan.missing_assets,
            "changed_assets": plan.changed_assets,
            "skipped_assets": plan.skipped_assets,
            "applied_files": changed,
            "reason": plan.reason,
        })
    return details


def _result(args: argparse.Namespace, status: str, summary: str, data: dict[str, Any], *, findings: tuple[str, ...] = ()) -> int:
    if bool(getattr(args, "json", False)):
        return emit_result(CommandResult(
            command="update",
            status=status,
            summary=summary,
            data=data,
            blocking_findings=findings,
            side_effects=tuple(data.get("side_effects", [])),
            next_action=NextAction(command="doctor" if status == "success" else "review update result", required=status != "success"),
        ), sys.stdout)
    print(summary)
    if findings and status == "blocked":
        print("Blocked: " + ", ".join(findings), file=sys.stderr)
        return 3
    return 0 if status == "success" else 4


def do_update(args: argparse.Namespace) -> int:
    update_all = bool(getattr(args, "all", False)) or getattr(args, "action", None) == "all"
    update_current = bool(getattr(args, "current", False))
    if not update_all and not update_current:
        update_current = True
    root = _framework_root()
    inventory = GlobalInstallationInventory(root).inspect()

    if update_all:
        global_result = _global_update(args, root)
        if global_result.get("status") not in {"success", "update_available"}:
            code = str(global_result.get("code") or "GLOBAL_UPDATE_FAILED")
            return _result(args, "blocked" if code.endswith("_BLOCKED") or code == "UPGRADE_APPROVAL_REQUIRED" else "failure", "Global framework update did not complete.", {"scope": "all", "global": global_result, "projects": []}, findings=(code,))
        inventory = GlobalInstallationInventory(root).inspect()
        from workflow_runtime.application.workflow import aiwf_registry
        project_details = _sync_projects(args, inventory, aiwf_registry.list_projects())
        failed = [item for item in project_details if item.get("status") == "missing"]
        status = "failure" if failed else "success"
        return _result(args, status, "Global-first update-all completed." if not failed else "Global-first update-all completed with project failures.", {
            "scope": "all",
            "global": global_result,
            "projects": project_details,
            "side_effects": [item["path"] for item in project_details if item.get("status") == "updated"],
        }, findings=("PROJECT_PATH_NOT_FOUND",) if failed else ())

    project = _project_path()
    plan = ProjectSyncPlanner().plan(project, inventory)
    changed = ProjectSyncPlanner().sync(plan, inventory, dry_run=bool(getattr(args, "dry_run", False) or getattr(args, "check", False)))
    status = "success" if inventory.available else "blocked"
    return _result(args, status, "Current project minimal update completed." if inventory.available else "Global installation is unavailable; current project was not mutated.", {
        "scope": "current",
        "global": {
            "available": inventory.available,
            "source_path": inventory.source_path,
            "version": inventory.version,
        },
        "projects": [{
            "path": str(project),
            "required_assets": plan.required_assets,
            "missing_assets": plan.missing_assets,
            "changed_assets": plan.changed_assets,
            "skipped_assets": plan.skipped_assets,
            "applied_files": changed,
            "reason": plan.reason,
        }],
        "side_effects": changed,
    }, findings=("GLOBAL_INSTALLATION_UNAVAILABLE",) if not inventory.available else ())


__all__ = ["do_update"]
