from __future__ import annotations

import hashlib
import json
import shutil
from dataclasses import dataclass
from pathlib import Path

from workflow_runtime.application.system.global_inventory import (
    GlobalInstallationInventory,
    GlobalInstallationSnapshot,
)


@dataclass(frozen=True)
class ProjectSyncPlan:
    project_path: str
    global_available: bool
    required_assets: list[str]
    missing_assets: list[str]
    changed_assets: list[str]
    skipped_assets: list[str]
    reason: str


def _hash_path(path: Path) -> str:
    digest = hashlib.sha256()
    if path.is_file():
        digest.update(path.read_bytes())
    elif path.is_dir():
        for child in sorted(item for item in path.rglob("*") if item.is_file()):
            digest.update(child.relative_to(path).as_posix().encode("utf-8"))
            digest.update(child.read_bytes())
    return digest.hexdigest()


def _manifest(project: Path) -> dict[str, object]:
    path = project / ".agents" / "MANIFEST.json"
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return {}
    return value if isinstance(value, dict) else {}


class ProjectSyncPlanner:
    def plan(self, project_path: Path | str, snapshot: GlobalInstallationSnapshot) -> ProjectSyncPlan:
        project = Path(project_path).expanduser().resolve()
        data = _manifest(project)
        raw_required = data.get("required_assets")
        required = [str(item) for item in raw_required if isinstance(item, str)] if isinstance(raw_required, list) else list(snapshot.required_runtime_assets)
        raw_optional = data.get("optional_assets")
        optional = [str(item) for item in raw_optional if isinstance(item, str)] if isinstance(raw_optional, list) else []
        if not snapshot.available or not snapshot.source_path:
            return ProjectSyncPlan(str(project), False, required, [], [], optional, "GLOBAL_INSTALLATION_UNAVAILABLE")
        root = Path(snapshot.source_path)
        missing: list[str] = []
        changed: list[str] = []
        for asset in required:
            source = GlobalInstallationInventory._asset_source(root, asset)
            target = project / ".agents" / asset
            if not source.exists():
                missing.append(asset)
            elif not target.exists():
                missing.append(asset)
            elif _hash_path(source) != _hash_path(target):
                changed.append(asset)
        return ProjectSyncPlan(
            str(project),
            True,
            required,
            missing,
            changed,
            optional,
            "REQUIRED_ASSET_DELTA" if missing or changed else "CURRENT",
        )

    def sync(self, plan: ProjectSyncPlan, snapshot: GlobalInstallationSnapshot, dry_run: bool = False) -> list[str]:
        if dry_run or not snapshot.available or not snapshot.source_path:
            return []
        root = Path(snapshot.source_path)
        project = Path(plan.project_path)
        changed: list[str] = []
        for asset in [*plan.missing_assets, *plan.changed_assets]:
            source = GlobalInstallationInventory._asset_source(root, asset)
            target = project / ".agents" / asset
            if not source.exists():
                continue
            if source.is_dir():
                for child in source.rglob("*"):
                    if not child.is_file():
                        continue
                    destination = target / child.relative_to(source)
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    if not destination.exists() or destination.read_bytes() != child.read_bytes():
                        shutil.copy2(child, destination)
                        changed.append(destination.relative_to(project).as_posix())
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                if not target.exists() or target.read_bytes() != source.read_bytes():
                    shutil.copy2(source, target)
                    changed.append(target.relative_to(project).as_posix())
        return changed


__all__ = ["ProjectSyncPlan", "ProjectSyncPlanner"]
