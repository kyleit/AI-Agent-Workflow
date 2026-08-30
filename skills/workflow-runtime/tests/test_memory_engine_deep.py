import os
from workflow_runtime.infrastructure.memory.filesystem import get_project_files
from workflow_runtime.infrastructure.memory.analyzer import ProjectAnalyzer
from workflow_runtime.infrastructure.memory.markdown_writer import (
    generate_project_summary,
    write_architecture_overview,
    write_architecture_components,
    write_architecture_data_flows,
)


def test_filesystem_ignore_rules():
    files = get_project_files(".")
    for f in files:
        assert not f.startswith("_to_delete/")
        assert not f.startswith("artifacts/")
        assert not f.startswith("python-runtime-dev/")
        assert not f.startswith(".agents/tmp/")


def test_analyzer_detects_modules():
    analyzer = ProjectAnalyzer(".")
    modules = analyzer.analyze_modules()
    assert isinstance(modules, list)
    assert len(modules) > 0
    mod_paths = [m["path"] for m in modules]
    assert "skills/workflow-runtime" in mod_paths or "skills" in mod_paths or any("skills" in p for p in mod_paths)


def test_deep_markdown_writers(tmp_path):
    info = {
        "project_name": "test-project",
        "description": "A deep memory test project",
        "languages": ["Python", "TypeScript"],
        "modules": [{"name": "Runtime", "path": "skills/workflow-runtime", "purpose": "Core engine", "details": "Active"}],
        "databases": [{"type": "SQLite", "path": "test.db", "purpose": "Local store"}],
        "infrastructure": [{"type": "Docker", "purpose": "Containers", "details": "Local"}],
        "build_commands": [{"name": "pytest", "command": "pytest"}]
    }

    summary = generate_project_summary(info)
    assert "test-project" in summary
    assert "Modular Multi-Tier Architecture" in summary
    assert "SQLite" in summary
    assert "Docker" in summary

    overview_file = tmp_path / "overview.md"
    write_architecture_overview(str(overview_file), info)
    assert overview_file.exists()
    assert "Runtime" in overview_file.read_text(encoding="utf-8")

    components_file = tmp_path / "components.md"
    write_architecture_components(str(components_file), info)
    assert components_file.exists()
    assert "Runtime" in components_file.read_text(encoding="utf-8")

    data_flows_file = tmp_path / "data-flows.md"
    write_architecture_data_flows(str(data_flows_file))
    assert data_flows_file.exists()
