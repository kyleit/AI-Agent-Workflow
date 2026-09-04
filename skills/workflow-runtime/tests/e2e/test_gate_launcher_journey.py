from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[4] / "tools" / "aiwf-hooks"))

from aiwf_gate_launcher import find_project_root, locate_gate


def test_bridge_project_resolves_global_gate_without_tools_copy(tmp_path: Path) -> None:
    project = tmp_path / "project"
    global_root = tmp_path / "global"
    (project / ".agents").mkdir(parents=True)
    (global_root / "tools" / "aiwf-hooks").mkdir(parents=True)
    gate = global_root / "tools" / "aiwf-hooks" / "aiwf_gate.py"
    gate.write_text("# gate\n", encoding="utf-8")

    assert locate_gate(project, global_root) == gate.resolve()


def test_blank_workspace_root_wins_over_parent_git_project(tmp_path: Path) -> None:
    (tmp_path / ".git").mkdir()
    blank = tmp_path / "nested" / "blank"
    (blank / ".agents").mkdir(parents=True)
    (blank / ".agents" / "project.config.json").write_text("{}", encoding="utf-8")

    assert find_project_root(blank) == blank.resolve()


def test_uninitialized_workspace_stays_current_over_parent_git_project(tmp_path: Path) -> None:
    (tmp_path / ".git").mkdir()
    blank = tmp_path / "nested" / "blank"
    blank.mkdir(parents=True)

    assert find_project_root(blank) == blank.resolve()
