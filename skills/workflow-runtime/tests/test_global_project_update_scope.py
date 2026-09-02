from __future__ import annotations

import json
from argparse import Namespace
from pathlib import Path

from workflow_runtime.application.system.global_inventory import (
    GlobalInstallationInventory,
)
from workflow_runtime.application.system.project_sync import ProjectSyncPlanner
from workflow_runtime.presentation.cli.commands._impl.update import update_framework


def test_inventory_prefers_explicit_global_root(tmp_path: Path, monkeypatch) -> None:
    global_root = tmp_path / "global"
    (global_root / "skills" / "runtime-required").mkdir(parents=True)
    (global_root / "AI_RULES.md").write_text("rules", encoding="utf-8")
    (global_root / "MANIFEST.json").write_text(
        json.dumps({"version": "6.26.0"}), encoding="utf-8"
    )
    monkeypatch.setenv("AIWF_GLOBAL_ROOT", str(global_root))

    snapshot = GlobalInstallationInventory().inspect()

    assert snapshot.available is True
    assert snapshot.source_path == str(global_root)
    assert snapshot.version == "6.26.0"


def test_project_plan_contains_only_required_delta(tmp_path: Path) -> None:
    project = tmp_path / "project"
    (project / ".agents").mkdir(parents=True)
    (project / ".agents" / "MANIFEST.json").write_text(
        json.dumps({
            "required_assets": ["AI_RULES.md", "skills/runtime-required"],
            "optional_assets": ["skills/unused"],
        }),
        encoding="utf-8",
    )
    snapshot = GlobalInstallationInventory(
        root=project,
    ).inspect()

    plan = ProjectSyncPlanner().plan(project, snapshot)

    assert "AI_RULES.md" in plan.required_assets
    assert "skills/runtime-required" in plan.missing_assets
    assert "skills/unused" in plan.skipped_assets


def test_update_all_runs_global_once_before_registered_project_plans(tmp_path: Path, monkeypatch, capsys) -> None:
    global_root = tmp_path / "global"
    (global_root / "skills" / "runtime-required").mkdir(parents=True)
    (global_root / "AI_RULES.md").write_text("rules", encoding="utf-8")
    (global_root / "MANIFEST.json").write_text(
        json.dumps({"version": "6.26.0", "required_assets": ["AI_RULES.md"]}),
        encoding="utf-8",
    )
    project = tmp_path / "project"
    (project / ".agents").mkdir(parents=True)
    (project / ".agents" / "MANIFEST.json").write_text(
        json.dumps({"required_assets": ["AI_RULES.md"]}), encoding="utf-8"
    )
    monkeypatch.setenv("AIWF_FRAMEWORK_ROOT", str(global_root))
    monkeypatch.setattr(update_framework, "_global_update", lambda args, root: {"status": "success", "code": "UP_TO_DATE"})
    monkeypatch.setattr(
        "workflow_runtime.application.workflow.aiwf_registry.list_projects",
        lambda: [{"path": str(project)}],
    )

    exit_code = update_framework.do_update(Namespace(all=True, current=False, check=True, yes=True, json=True, dry_run=True, force=False))
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["data"]["scope"] == "all"
    assert payload["data"]["global"]["code"] == "UP_TO_DATE"
    assert payload["data"]["projects"][0]["path"] == str(project.resolve())
