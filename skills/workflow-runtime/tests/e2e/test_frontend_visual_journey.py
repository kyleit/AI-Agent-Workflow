from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from workflow_runtime.application.verification.frontend_e2e_gate import run_frontend_e2e
from workflow_runtime.presentation.cli.registry import _resolve_aiwf_project_root
from workflow_runtime.presentation.cli.commands.visual_commands import VisualCommand
from workflow_runtime.application.workflow.workflow_entry_gateway import WorkflowEntryGateway
from workflow_runtime.presentation.cli.bootstrap import bootstrap_di

pytestmark = pytest.mark.e2e


def test_visual_e2e_command_is_agent_facing():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")
    VisualCommand().add_parser(subparsers)

    args = parser.parse_args(
        [
            "visual",
            "e2e",
            "--url",
            "http://127.0.0.1:5173",
            "--feature-id",
            "FEAT-606",
        ]
    )

    assert args.subcommand == "e2e"
    assert args.route == "/"
    assert args.max_iterations == 8


def test_real_browser_runs_mobile_desktop_tablet_and_writes_hashes(tmp_path):
    pytest.importorskip("playwright")
    page = (
        "data:text/html,<meta name='viewport' content='width=device-width'>"
        "<style>body{margin:0}button{min-width:44px;min-height:44px}</style>"
        "<main><h1>AIWF</h1><button>Continue</button></main>"
    )

    result = run_frontend_e2e(page, "FEAT-E2E", workspace_root=tmp_path)

    assert result["status"] == "PASS", result
    manifest = json.loads(
        (tmp_path / "docs" / "aiwf-runs" / "FEAT-E2E" / "08-visual" / "frontend-e2e.json").read_text(
            encoding="utf-8"
        )
    )
    assert manifest["viewport_order"] == ["mobile", "desktop", "tablet"]
    assert len(manifest["iterations"][-1]["screenshot_hashes"]) == 6


def test_cli_workspace_resolution_does_not_capture_external_workspace(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        "workflow_runtime.presentation.cli.registry._is_aiwf_project_root",
        lambda path: Path(path) == tmp_path,
    )

    assert Path(_resolve_aiwf_project_root()) == tmp_path


def test_blank_nested_workspace_wins_over_parent_project(tmp_path, monkeypatch):
    (tmp_path / ".agents").mkdir()
    (tmp_path / ".agents" / "AI_RULES.md").write_text("parent", encoding="utf-8")
    blank = tmp_path / "accounts" / "temp" / "blank-project"
    (blank / ".agents").mkdir(parents=True)
    (blank / ".agents" / "project.config.json").write_text("{}", encoding="utf-8")

    monkeypatch.chdir(blank)

    assert Path(_resolve_aiwf_project_root()) == blank


def test_uninitialized_nested_workspace_stays_current(tmp_path, monkeypatch):
    (tmp_path / ".git").mkdir()
    blank = tmp_path / "nested" / "blank"
    blank.mkdir(parents=True)

    monkeypatch.chdir(blank)

    assert Path(_resolve_aiwf_project_root()) == blank


def test_init_explicit_path_changes_into_target(tmp_path, monkeypatch):
    target = tmp_path / "blank-target"
    target.mkdir()
    monkeypatch.chdir(tmp_path)

    from workflow_runtime.presentation.cli.commands import build_registry

    registry = build_registry()
    assert registry.execute(
        "init", str(target), "--non-interactive", "--no-git", "--quiet"
    ) == 0
    assert (target / ".agents" / "project.config.json").exists()
    assert not (tmp_path / ".agents" / "project.config.json").exists()


def test_blank_workspace_discovery_creates_profile(tmp_path):
    bootstrap_di()
    result = WorkflowEntryGateway(str(tmp_path)).discover_project_profile()

    assert result["status"] == "success"
    assert result["profile"]["visual_debug"]["e2e_required"] is False
    assert (tmp_path / ".agents" / "project-profile.json").exists()
