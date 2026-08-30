from pathlib import Path

from workflow_runtime.application.system.update_source import update_projects
from workflow_runtime.presentation.cli.commands import build_registry


def test_update_projects_returns_one_machine_readable_result_per_project(tmp_path: Path) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"
    first.mkdir()
    second.mkdir()
    result = update_projects((first, second), force=True)
    assert result.status == "success"
    assert [item.path for item in result.projects] == [str(first), str(second)]
    assert all(item.status == "ready" for item in result.projects)


def test_update_parser_accepts_agent_batch_switch() -> None:
    registry = build_registry()
    registry.build_parser()
    parsed = registry._commands["update"].parse(["-All", "--json"])
    assert parsed.all is True
    assert parsed.json is True
