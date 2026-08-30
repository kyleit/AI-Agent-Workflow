from pathlib import Path

from workflow_runtime.application.workflow.workflow_entry_gateway import (
    build_agent_context,
    ensure_project_memory,
)


def test_missing_memory_bootstraps_once(tmp_path: Path, monkeypatch) -> None:
    calls: list[str] = []
    monkeypatch.setattr(
        "workflow_runtime.application.workflow.workflow_entry_gateway.bootstrap_project_memory",
        lambda root, mode: calls.append(f"{root}:{mode}") or {"status": "success"},
    )
    result = ensure_project_memory(tmp_path)
    assert result.status == "bootstrapped"
    assert len(calls) == 1


def test_existing_memory_returns_summary_first_context(tmp_path: Path, monkeypatch) -> None:
    summary = tmp_path / ".agents" / "memory" / "project-summary.md"
    summary.parent.mkdir(parents=True)
    summary.write_text("# Project Summary\n\nAIWF runtime\n", encoding="utf-8")
    monkeypatch.setattr(
        "workflow_runtime.application.workflow.workflow_entry_gateway.update_project_memory_from_git_diff",
        lambda root: {"status": "success", "files_changed": 1},
    )
    result = ensure_project_memory(tmp_path)
    context = build_agent_context(tmp_path, "runtime")
    assert result.status == "updated"
    assert context.summary.startswith("# Project Summary")
    assert context.query == "runtime"
