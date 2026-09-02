from __future__ import annotations

from pathlib import Path

from workflow_runtime.application.verification.validation_runner import (
    resolve_validation_scope,
)
from workflow_runtime.infrastructure.memory.update import parse_new_lessons
from workflow_runtime.infrastructure.memory.vector_manifest import stable_chunk_id
from workflow_runtime.infrastructure.memory.context_manifest import (
    build_project_context_manifest,
    manifest_freshness,
    write_context_manifest,
)


def test_stable_chunk_id_is_deterministic_and_content_bound() -> None:
    first = stable_chunk_id(".agents/memory/project-summary.md", "overview", "runtime")
    second = stable_chunk_id(".agents/memory/project-summary.md", "overview", "runtime")
    changed = stable_chunk_id(".agents/memory/project-summary.md", "overview", "changed")

    assert first == second
    assert first != changed
    assert "XXX" not in first


def test_memory_lesson_parser_does_not_create_placeholder_ids(tmp_path: Path) -> None:
    issue = tmp_path / "docs" / "features" / "project-memory" / "note.md"
    issue.parent.mkdir(parents=True)
    issue.write_text("# Notes\n\n## 1. Issue\nA note without an issue identity.\n", encoding="utf-8")

    assert parse_new_lessons(str(issue)) == []


def test_validation_scope_uses_nested_go_module(tmp_path: Path) -> None:
    desktop = tmp_path / "desktop"
    desktop.mkdir()
    (desktop / "go.mod").write_text("module example.test/app\n\ngo 1.22\n", encoding="utf-8")

    scope = resolve_validation_scope(str(tmp_path))

    assert scope.project_type == "go"
    assert Path(scope.working_directory) == desktop
    assert scope.build_command[:2] == ("go", "vet")


def test_context_manifest_rejects_changed_source(tmp_path: Path) -> None:
    source = tmp_path / "src" / "entry.py"
    source.parent.mkdir()
    source.write_text("VALUE = 1\n", encoding="utf-8")
    summary = tmp_path / "docs" / "summary.md"
    summary.parent.mkdir()
    summary.write_text("# Summary\n", encoding="utf-8")
    manifest_path = tmp_path / ".agents" / "memory" / "project-context.json"
    manifest = build_project_context_manifest(
        tmp_path,
        project_id="test-project",
        summary_path="docs/summary.md",
        architecture_paths=(),
        entrypoints=("src/entry.py",),
        active_constraints=(),
        known_blockers=(),
        index_revision="test-index",
        retrieval_hints=("entry",),
        generated_at="2026-09-02T00:00:00+00:00",
    )
    write_context_manifest(manifest_path, manifest)

    assert manifest_freshness(tmp_path, manifest.to_dict()) == "CURRENT"
    source.write_text("VALUE = 2\n", encoding="utf-8")
    assert manifest_freshness(tmp_path, manifest.to_dict()) == "STALE"
