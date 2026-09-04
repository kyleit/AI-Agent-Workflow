from __future__ import annotations

import json
from argparse import Namespace
from pathlib import Path

from workflow_runtime.application.system.global_inventory import (
    GlobalInstallationInventory,
)
from workflow_runtime.application.system.project_sync import ProjectSyncPlanner
from workflow_runtime.application.system.project_bridge import (
    ensure_project_bridge,
    migrate_project_to_global,
    rollback_project_bridge,
    validate_project_bridge,
)
from workflow_runtime.application.system.global_installation.resolver import resolve_global_source
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


def test_global_source_resolver_rejects_current_project_fallback(tmp_path: Path, monkeypatch) -> None:
    project = tmp_path / "project"
    (project / ".git").mkdir(parents=True)
    (project / "AI_RULES.md").write_text("rules", encoding="utf-8")
    monkeypatch.setenv("AIWF_FRAMEWORK_ROOT", str(project))

    assert resolve_global_source(project) is None


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


def test_frontend_project_plan_adds_visual_skills_only_when_profile_requires_them(tmp_path: Path) -> None:
    global_root = tmp_path / "global"
    (global_root / "skills" / "frontend-design").mkdir(parents=True)
    (global_root / "skills" / "frontend-visual-debug").mkdir(parents=True)
    (global_root / "skills" / "blueprint-to-implementation").mkdir(parents=True)
    (global_root / "skills" / "debug-to-verify").mkdir(parents=True)
    (global_root / "skills" / "test-execution-governance").mkdir(parents=True)
    (global_root / "AI_RULES.md").write_text("rules", encoding="utf-8")
    (global_root / "MANIFEST.json").write_text(json.dumps({"version": "6.26.0"}), encoding="utf-8")
    project = tmp_path / "project"
    (project / ".agents").mkdir(parents=True)
    (project / ".agents" / "project-profile.json").write_text(
        json.dumps({"visual_debug": {"e2e_required": True}}), encoding="utf-8"
    )

    snapshot = GlobalInstallationInventory(root=global_root).inspect()
    plan = ProjectSyncPlanner().plan(project, snapshot)

    assert "skills/frontend-design" in plan.required_assets
    assert "skills/frontend-visual-debug" in plan.missing_assets


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


def test_new_project_bridge_uses_global_assets_without_copying_framework_tree(tmp_path: Path) -> None:
    global_root = tmp_path / "global"
    (global_root / "skills" / "aiwf").mkdir(parents=True)
    (global_root / "AI_RULES.md").write_text("global rules", encoding="utf-8")
    (global_root / "MANIFEST.json").write_text(json.dumps({"version": "6.26.0"}), encoding="utf-8")
    project = tmp_path / "project"
    (project / ".git").mkdir(parents=True)

    bridge = ensure_project_bridge(project, global_root)
    assert bridge.bridge_mode == "global_link"
    assert (project / ".agents" / "project.json").is_file()
    assert (project / ".agents" / "runtime-link.json").is_file()
    assert not (project / ".agents" / "skills").exists()
    valid, reason, loaded = validate_project_bridge(project)
    assert (valid, reason) == (True, "READY")
    assert loaded is not None and loaded.project_id == bridge.project_id

    snapshot = GlobalInstallationInventory(root=global_root).inspect()
    plan = ProjectSyncPlanner().plan(project, snapshot)
    assert plan.reason == "GLOBAL_BRIDGE_METADATA_ONLY"
    assert plan.missing_assets == []
    assert ProjectSyncPlanner().sync(plan, snapshot) == []


def test_legacy_project_migration_is_reversible_and_keeps_copied_assets(tmp_path: Path) -> None:
    global_root = tmp_path / "global"
    global_root.mkdir()
    (global_root / "MANIFEST.json").write_text(json.dumps({"version": "6.26.0"}), encoding="utf-8")
    project = tmp_path / "project"
    (project / ".git").mkdir(parents=True)
    (project / ".agents" / "skills").mkdir(parents=True)
    copied = project / ".agents" / "skills" / "custom.md"
    copied.write_text("project-owned", encoding="utf-8")

    bridge, backup = migrate_project_to_global(project, global_root)
    assert bridge.bridge_mode == "global_link"
    assert copied.read_text(encoding="utf-8") == "project-owned"
    assert backup.endswith("project-bridge-before-global.json")

    rolled_back = rollback_project_bridge(project)
    assert rolled_back is not None and rolled_back.bridge_mode == "legacy_copy"
    assert copied.read_text(encoding="utf-8") == "project-owned"
