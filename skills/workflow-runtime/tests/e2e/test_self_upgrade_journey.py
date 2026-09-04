from __future__ import annotations

import subprocess
from pathlib import Path

from workflow_runtime.application.system.source_upgrade import (
    SourceUpgradeService,
    UpgradeRequest,
)


def _git(cwd: Path, *args: str) -> str:
    result = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=True)
    return result.stdout.strip()


def _source_with_remote(tmp_path: Path) -> tuple[Path, Path]:
    remote = tmp_path / "remote.git"
    source = tmp_path / "source"
    _git(tmp_path, "init", "--bare", str(remote))
    source.mkdir()
    _git(source, "init", "-b", "main")
    _git(source, "config", "user.email", "aiwf-test@example.invalid")
    _git(source, "config", "user.name", "AIWF Test")
    (source / "README.md").write_text("v1\n", encoding="utf-8")
    _git(source, "add", "README.md")
    _git(source, "commit", "-m", "initial")
    _git(source, "remote", "add", "upstream", str(remote))
    _git(source, "push", "-u", "upstream", "main")
    return source, remote


def test_source_upgrade_blocks_dirty_source_without_mutation(tmp_path: Path) -> None:
    source, remote = _source_with_remote(tmp_path)
    (source / "README.md").write_text("local change\n", encoding="utf-8")
    service = SourceUpgradeService(str(source), "upstream", str(remote), "main")

    result = service.execute(UpgradeRequest(
        source_path=str(source),
        repository_url=str(remote),
        remote_name="upstream",
        branch="main",
        tag=None,
        check=False,
        dry_run=False,
        yes=True,
        json_output=True,
    ))

    assert result.status == "blocked"
    assert result.code == "DIRTY_SOURCE_BLOCKED"
    assert (source / "README.md").read_text(encoding="utf-8") == "local change\n"


def test_source_upgrade_blocks_diverged_source_without_mutation(tmp_path: Path) -> None:
    source, remote = _source_with_remote(tmp_path)
    (source / "README.md").write_text("local commit\n", encoding="utf-8")
    _git(source, "add", "README.md")
    _git(source, "commit", "-m", "local change")

    remote_work = tmp_path / "remote-work"
    _git(tmp_path, "clone", str(remote), str(remote_work))
    _git(remote_work, "config", "user.email", "aiwf-test@example.invalid")
    _git(remote_work, "config", "user.name", "AIWF Test")
    (remote_work / "README.md").write_text("remote commit\n", encoding="utf-8")
    _git(remote_work, "add", "README.md")
    _git(remote_work, "commit", "-m", "remote change")
    _git(remote_work, "push", "origin", "main")

    service = SourceUpgradeService(str(source), "upstream", str(remote), "main")
    result = service.execute(UpgradeRequest(
        source_path=str(source),
        repository_url=str(remote),
        remote_name="upstream",
        branch="main",
        tag=None,
        check=False,
        dry_run=False,
        yes=True,
        json_output=True,
    ))

    assert result.status == "blocked"
    assert result.code == "DIVERGED_SOURCE_BLOCKED"
    assert (source / "README.md").read_text(encoding="utf-8") == "local commit\n"


def test_source_upgrade_fast_forwards_clean_source(tmp_path: Path) -> None:
    source, remote = _source_with_remote(tmp_path)
    remote_work = tmp_path / "remote-work"
    _git(tmp_path, "clone", str(remote), str(remote_work))
    _git(remote_work, "config", "user.email", "aiwf-test@example.invalid")
    _git(remote_work, "config", "user.name", "AIWF Test")
    (remote_work / "README.md").write_text("v2\n", encoding="utf-8")
    _git(remote_work, "add", "README.md")
    _git(remote_work, "commit", "-m", "second")
    _git(remote_work, "push", "origin", "main")
    service = SourceUpgradeService(str(source), "upstream", str(remote), "main")

    result = service.execute(UpgradeRequest(
        source_path=str(source),
        repository_url=str(remote),
        remote_name="upstream",
        branch="main",
        tag=None,
        check=False,
        dry_run=False,
        yes=True,
        json_output=True,
    ))

    assert result.status == "success"
    assert result.code == "UPDATED"
    assert result.mutation is True
    assert (source / "README.md").read_text(encoding="utf-8") == "v2\n"


def test_source_upgrade_allows_dirty_preflight_without_mutation(tmp_path: Path) -> None:
    source, remote = _source_with_remote(tmp_path)
    (source / "README.md").write_text("local change\n", encoding="utf-8")
    service = SourceUpgradeService(str(source), "upstream", str(remote), "main")

    result = service.execute(UpgradeRequest(
        source_path=str(source),
        repository_url=str(remote),
        remote_name="upstream",
        branch="main",
        tag=None,
        check=True,
        dry_run=False,
        yes=False,
        json_output=True,
        allow_dirty=True,
    ))

    assert result.status == "success"
    assert result.code == "DIRTY_SOURCE_INSPECTED"
    assert result.mutation is False
    assert (source / "README.md").read_text(encoding="utf-8") == "local change\n"
