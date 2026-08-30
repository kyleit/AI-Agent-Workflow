from __future__ import annotations

import json
from pathlib import Path

from workflow_runtime.presentation.cli.commands import build_registry
from workflow_runtime.presentation.cli.commands._impl.project_manager import (
    do_implement_action,
)


def _registry():
    registry = build_registry()
    registry.build_parser()
    return registry


def test_start_parser_keeps_command_payload_and_blueprint() -> None:
    parsed = _registry()._commands["start"].parse([
        "--skill", "quick-fix", "--command", "fix", "--checkpoint", "5",
        "--blueprint", "docs/example.md",
    ])

    assert parsed.skill == "quick-fix"
    assert parsed.command == "fix"
    assert parsed.blueprint == "docs/example.md"


def test_blueprint_parser_accepts_path_and_approval() -> None:
    parsed = _registry()._commands["blueprint"].parse([
        "--path", "docs/example.md", "--approve", "--work-item", "FEAT-060",
    ])

    assert parsed.path == "docs/example.md"
    assert parsed.approve is True
    assert parsed.work_item == "FEAT-060"


def test_implement_dry_run_returns_contract_without_side_effects(
    tmp_path: Path, capsys,
) -> None:
    blueprint = tmp_path / "FEAT-060_blueprint.md"
    blueprint.write_text("# Blueprint\n", encoding="utf-8")

    exit_code = do_implement_action(
        type("Args", (), {"blueprint": str(blueprint), "dry_run": True})(),
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 3
    assert payload["schema_version"] == "aiwf.command.v1"
    assert payload["data"]["blueprint"] == str(blueprint)
    assert payload["data"]["phases"]
    assert payload["side_effects"] == []
