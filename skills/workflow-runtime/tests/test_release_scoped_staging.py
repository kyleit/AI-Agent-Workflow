from __future__ import annotations

from pathlib import Path

from tools.aiwf_release import gitsteps


def test_release_scope_rejects_traversal_and_normalizes_paths(tmp_path: Path) -> None:
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "app.py").write_text("ok\n", encoding="utf-8")

    assert gitsteps.validate_repo_relative_scope(tmp_path, ["./src\\app.py"]) == ["src/app.py"]
    try:
        gitsteps.validate_repo_relative_scope(tmp_path, ["../outside.py"])
    except gitsteps.GitError as exc:
        assert "repository-relative" in str(exc)
    else:
        raise AssertionError("path traversal must be rejected")


def test_repo_release_dry_run_has_no_add_all(tmp_path: Path) -> None:
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "app.py").write_text("ok\n", encoding="utf-8")
    result = gitsteps.repo_release(
        tmp_path, ".", "v1.0.1", "test release", "origin", "main", True, True,
        files=["src/app.py"],
    )
    assert result["files"] == ["src/app.py"]
    assert not any("add -A" in line for line in result["logs"])
    assert any("git add -- src/app.py" in line for line in result["logs"])
