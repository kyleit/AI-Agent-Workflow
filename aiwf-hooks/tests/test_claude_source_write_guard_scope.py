"""The Claude edit guard gates this repository's source, nothing outside it.

An absolute target outside the root used to fall through path normalisation
unchanged, so a temp scratchpad ``.py`` was classified as repository source and
blocked whenever no blueprint was approved.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

HOOKS = Path(__file__).resolve().parents[1]
GUARD = HOOKS / "claude_source_write_guard.py"
sys.path.insert(0, str(HOOKS))
import aiwf_gate  # noqa: E402


@pytest.fixture()
def layout(tmp_path: Path) -> tuple[Path, Path]:
    root = tmp_path / "repo"
    (root / ".agents").mkdir(parents=True)
    (root / ".agents" / "AI_RULES.md").write_text("# rules\n", encoding="utf-8")
    (root / "src").mkdir()
    (root / "src" / "app.py").write_text("VALUE = 1\n", encoding="utf-8")
    outside = tmp_path / "scratchpad"
    outside.mkdir()
    (outside / "probe.py").write_text("VALUE = 2\n", encoding="utf-8")
    return root, outside


def _guard(root: Path, file_path: str) -> int:
    env = {key: value for key, value in os.environ.items() if key != "AIWF_BYPASS"}
    payload = {"cwd": str(root), "tool_name": "Write", "tool_input": {"file_path": file_path}}
    result = subprocess.run(
        [sys.executable, str(GUARD)],
        input=json.dumps(payload), capture_output=True, text=True, env=env, cwd=str(root),
    )
    return result.returncode


def test_unauthorized_source_inside_repo_is_blocked(layout: tuple[Path, Path]) -> None:
    root, _outside = layout

    assert _guard(root, str(root / "src" / "app.py")) == 2
    assert _guard(root, "src/app.py") == 2


def test_source_outside_repo_is_not_gated(layout: tuple[Path, Path]) -> None:
    root, outside = layout

    assert _guard(root, str(outside / "probe.py")) == 0
    assert _guard(root, "../scratchpad/probe.py") == 0


def test_symlinks_are_resolved_before_scoping(layout: tuple[Path, Path]) -> None:
    root, outside = layout
    into_repo = outside / "app_link.py"
    into_repo.symlink_to(root / "src" / "app.py")
    aliased_root = outside.parent / "repo_alias"
    aliased_root.symlink_to(root, target_is_directory=True)

    assert _guard(root, str(into_repo)) == 2
    assert _guard(root, str(aliased_root / "src" / "app.py")) == 2


def test_relative_paths_are_repo_relative_not_cwd_relative(
    layout: tuple[Path, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    root, outside = layout
    monkeypatch.chdir(outside)

    assert aiwf_gate.is_source_file(root, "src/app.py") is True
    assert aiwf_gate.is_source_file(root, "docs/guide.py") is False
    assert aiwf_gate.is_source_file(root, str(outside / "probe.py")) is False
