from __future__ import annotations

from argparse import Namespace
from pathlib import Path

from workflow_runtime.presentation.cli.commands import build_registry


def test_update_parser_accepts_global_first_agent_flags() -> None:
    registry = build_registry()
    registry.build_parser()
    parsed = registry._commands["update"].parse(["--all", "--check", "--yes", "--json"])

    assert parsed.all is True
    assert parsed.check is True
    assert parsed.yes is True
    assert parsed.json is True


def test_bootstrap_wrapper_routes_top_level_update_to_global_runtime() -> None:
    bootstrap = Path(__file__).parents[2] / ".." / "bootstrap.ps1"
    content = bootstrap.resolve().read_text(encoding="utf-8")

    assert '"--update"' in content
    assert "self-upgrade" in content
    assert "AIWF_FRAMEWORK_ROOT" in content


def test_update_commands_propagate_handler_exit_codes(monkeypatch) -> None:
    monkeypatch.setattr(
        "workflow_runtime.presentation.cli.workflow_runtime.do_update",
        lambda _args: 3,
    )
    monkeypatch.setattr(
        "workflow_runtime.presentation.cli.workflow_runtime.do_update_source",
        lambda _args: 4,
    )

    registry = build_registry()
    registry.build_parser()

    assert registry._commands["update"].run(Namespace()) == 3
    assert registry._commands["update-source"].run(Namespace()) == 4
