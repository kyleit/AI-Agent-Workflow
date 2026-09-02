from __future__ import annotations

from workflow_runtime.presentation.cli.commands import build_registry


def test_global_source_aliases_share_the_update_source_handler() -> None:
    registry = build_registry()
    registry.build_parser()

    assert registry._commands["self-upgrade"] is registry._commands["update-source"]
    assert registry._commands["upgrade"] is registry._commands["update-source"]


def test_coordinator_handler_import_is_resolvable() -> None:
    from workflow_runtime.presentation.cli.workflow_command_handlers import handle_coordinator

    assert callable(handle_coordinator)
