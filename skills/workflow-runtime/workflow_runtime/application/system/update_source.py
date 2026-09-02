from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
from workflow_runtime.application.system.source_upgrade import (
    DEFAULT_REPOSITORY_URL,
    RepositorySnapshot,
    SourceUpgradeService,
    UpgradeRequest,
    UpgradeResult,
    handle_update_source,
)


class SourceRepositoryService(SourceUpgradeService):
    """Compatibility adapter for older callers of the source update service."""

    def __init__(self, source_path: str = ".", remote: str = "origin", branch: str = "main") -> None:
        super().__init__(source_path, remote, DEFAULT_REPOSITORY_URL, branch)
        self.remote = remote

    def check_status(self, auto_init: bool = False, repo_url: str = DEFAULT_REPOSITORY_URL, releases_only: bool = True) -> dict[str, Any]:
        del auto_init, releases_only
        self.repository_url = repo_url
        snapshot = self.inspect()
        return {
            "status": "success",
            "source_path": snapshot.source_path,
            "branch": snapshot.branch,
            "upstream": snapshot.target_ref,
            "commit": snapshot.head_commit,
            "remote_commit": snapshot.target_commit,
            "is_dirty": snapshot.is_dirty,
            "is_detached": snapshot.is_detached,
            "is_up_to_date": snapshot.target_exists and snapshot.ahead == 0 and snapshot.behind == 0,
            "is_behind": snapshot.behind > 0,
            "is_ahead": snapshot.ahead > 0 and snapshot.behind == 0,
            "is_diverged": snapshot.ahead > 0 and snapshot.behind > 0,
        }

    def fetch_updates(self) -> bool:
        return self.fetch()[0]

    def pull_ff(self, releases_only: bool = True) -> bool:
        del releases_only
        request = UpgradeRequest(str(self.source_path), self.repository_url, self.remote_name, self.branch, None, False, False, True, False)
        return self.execute(request).status == "success"


@dataclass(frozen=True)
class ProjectUpdateResult:
    path: str
    status: str
    version: str | None = None
    changed_artifacts: tuple[str, ...] = ()
    failure: str | None = None


@dataclass(frozen=True)
class UpdateResult:
    status: str
    projects: tuple[ProjectUpdateResult, ...] = ()
    warnings: tuple[str, ...] = ()

    def payload(self) -> dict[str, object]:
        return {
            "status": self.status,
            "projects": [
                {
                    "path": item.path,
                    "status": item.status,
                    "version": item.version,
                    "changed_artifacts": list(item.changed_artifacts),
                    "failure": item.failure,
                }
                for item in self.projects
            ],
            "warnings": list(self.warnings),
        }


def update_projects(projects: list[Path] | tuple[Path, ...], force: bool = False) -> UpdateResult:
    """Legacy result helper retained for registry callers and older agents."""
    results: list[ProjectUpdateResult] = []
    for project in projects:
        path = Path(project)
        if not path.exists() or not path.is_dir():
            results.append(ProjectUpdateResult(str(path), "missing", failure="project_directory_missing"))
            continue
        results.append(ProjectUpdateResult(str(path), "ready" if force else "skipped"))
    status = "failure" if any(item.status == "missing" for item in results) else "success"
    return UpdateResult(status, tuple(results))


__all__ = [
    "DEFAULT_REPOSITORY_URL",
    "ProjectUpdateResult",
    "RepositorySnapshot",
    "SourceRepositoryService",
    "SourceUpgradeService",
    "UpdateResult",
    "UpgradeRequest",
    "UpgradeResult",
    "handle_update_source",
    "update_projects",
]
