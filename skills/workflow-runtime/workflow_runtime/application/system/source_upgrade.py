from __future__ import annotations

import json
import os
import re
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


DEFAULT_REPOSITORY_URL = "https://github.com/kyleit/AI-Agent-Workflow.git"


@dataclass(frozen=True)
class RepositorySnapshot:
    source_path: str
    remote_name: str
    remote_url: str
    branch: str
    target_ref: str
    head_commit: str
    target_commit: str
    ahead: int
    behind: int
    is_dirty: bool
    dirty_paths: list[str]
    is_detached: bool
    target_exists: bool


@dataclass(frozen=True)
class UpgradeRequest:
    source_path: str | None
    repository_url: str
    remote_name: str
    branch: str
    tag: str | None
    check: bool
    dry_run: bool
    yes: bool
    json_output: bool


@dataclass(frozen=True)
class UpgradeResult:
    schema_version: str
    command: str
    status: str
    code: str
    source_path: str
    remote_name: str
    repository_url: str
    target_ref: str
    before_commit: str | None
    after_commit: str | None
    mutation: bool
    changed_artifacts: list[str]
    warnings: list[str]
    next_action: str | None
    failure: str | None

    def payload(self) -> dict[str, Any]:
        return asdict(self)


class SourceUpgradeService:
    def __init__(self, source_path: str, remote_name: str, repository_url: str, branch: str) -> None:
        self.source_path = str(Path(source_path).expanduser().resolve())
        self.remote_name = remote_name or "aiwf-github"
        self.repository_url = repository_url or DEFAULT_REPOSITORY_URL
        self.branch = branch or "main"

    def _run_git(self, args: list[str]) -> tuple[int, str, str]:
        try:
            result = subprocess.run(
                ["git", *args],
                cwd=self.source_path,
                capture_output=True,
                text=True,
                check=False,
            )
        except OSError as exc:
            return 127, "", str(exc)
        return result.returncode, result.stdout.strip(), result.stderr.strip()

    def _remote_url(self, name: str) -> str:
        code, output, _ = self._run_git(["remote", "get-url", name])
        return output if code == 0 else ""

    @staticmethod
    def _is_github(url: str) -> bool:
        return bool(re.search(r"(?:^|@|://)github\.com(?::|/)", url, re.IGNORECASE))

    def inspect(self, tag: str | None = None) -> RepositorySnapshot:
        remote_url = self._remote_url(self.remote_name)
        target_ref = (
            f"refs/remotes/{self.remote_name}/aiwf-tags/{tag}"
            if tag else f"{self.remote_name}/{self.branch}"
        )
        code_head, head, _ = self._run_git(["rev-parse", "HEAD"])
        code_target, target, _ = self._run_git(["rev-parse", target_ref])
        code_branch, branch, _ = self._run_git(["branch", "--show-current"])
        code_symbolic, symbolic, _ = self._run_git(["symbolic-ref", "-q", "HEAD"])
        status_code, status_output, _ = self._run_git(["status", "--porcelain", "--untracked-files=all"])
        dirty_paths = [line[3:].strip() for line in status_output.splitlines() if len(line) >= 3]
        ahead = behind = 0
        if code_target == 0 and code_head == 0:
            code_count, count, _ = self._run_git(["rev-list", "--left-right", "--count", f"HEAD...{target_ref}"])
            if code_count == 0:
                parts = count.split()
                if len(parts) == 2:
                    ahead, behind = int(parts[0]), int(parts[1])
        is_detached = code_symbolic != 0 or not symbolic
        current_branch = branch if code_branch == 0 and branch else "HEAD (detached)"
        return RepositorySnapshot(
            source_path=self.source_path,
            remote_name=self.remote_name,
            remote_url=remote_url,
            branch=current_branch,
            target_ref=target_ref,
            head_commit=head if code_head == 0 else "",
            target_commit=target if code_target == 0 else "",
            ahead=ahead,
            behind=behind,
            is_dirty=bool(dirty_paths) or status_code != 0,
            dirty_paths=dirty_paths,
            is_detached=is_detached,
            target_exists=code_target == 0,
        )

    def ensure_remote(self) -> tuple[bool, str | None]:
        code, remotes, error = self._run_git(["remote"])
        if code != 0:
            return False, error or "SOURCE_REPOSITORY_INVALID"
        names = set(remotes.splitlines())
        if self.remote_name in names:
            url = self._remote_url(self.remote_name)
            if url and (self.remote_name != "origin" or self._is_github(url)):
                return False, url
            if self.remote_name == "origin":
                for candidate in sorted(names):
                    candidate_url = self._remote_url(candidate)
                    if self._is_github(candidate_url):
                        self.remote_name = candidate
                        return False, candidate_url
                self.remote_name = "aiwf-github"
                if self.remote_name in names:
                    return False, self._remote_url(self.remote_name)
            else:
                return False, url or "REMOTE_URL_MISSING"
        if self.remote_name == "origin":
            for candidate in sorted(names):
                candidate_url = self._remote_url(candidate)
                if self._is_github(candidate_url):
                    self.remote_name = candidate
                    return False, candidate_url
            self.remote_name = "aiwf-github"
            if self.remote_name in names:
                return False, self._remote_url(self.remote_name)
        add_code, _, add_error = self._run_git(["remote", "add", self.remote_name, self.repository_url])
        if add_code != 0:
            return False, add_error or "REMOTE_CONFIG_FAILED"
        return True, self.repository_url

    def fetch(self, tag: str | None = None) -> tuple[bool, str]:
        # Fetch only the requested branch/tag into a remote-tracking ref. A
        # blanket --tags fetch can fail when a local tag has the same name as
        # a remote tag; local release tags must never be clobbered by update.
        if tag:
            refspec = f"refs/tags/{tag}:refs/remotes/{self.remote_name}/aiwf-tags/{tag}"
            args = ["fetch", "--no-tags", self.remote_name, refspec]
        else:
            args = ["fetch", "--prune", "--no-tags", self.remote_name, self.branch]
        code, _, error = self._run_git(args)
        return code == 0, error

    def execute(self, request: UpgradeRequest) -> UpgradeResult:
        empty = ""
        if not Path(self.source_path, ".git").exists():
            return self._result("failure", "SOURCE_REPOSITORY_INVALID", empty, empty, False, "Source path is not a Git repository.")
        _, remote_value = self.ensure_remote()
        if remote_value and self._is_github(remote_value):
            self.repository_url = remote_value
        fetched, fetch_error = self.fetch(request.tag)
        if not fetched:
            return self._result("failure", "REMOTE_FETCH_FAILED", empty, empty, False, fetch_error or "Remote fetch failed.")
        snapshot = self.inspect(request.tag)
        if not snapshot.target_exists:
            return self._result("failure", "TARGET_REF_NOT_FOUND", snapshot.head_commit, None, False, snapshot.target_ref)
        if snapshot.is_dirty:
            return self._result("blocked", "DIRTY_SOURCE_BLOCKED", snapshot.head_commit, snapshot.target_commit, False, "Local tracked or untracked changes exist.", snapshot)
        if snapshot.is_detached and not request.tag:
            return self._result("blocked", "DETACHED_SOURCE_BLOCKED", snapshot.head_commit, snapshot.target_commit, False, "Source HEAD is detached.", snapshot)
        if snapshot.ahead and snapshot.behind:
            return self._result("blocked", "DIVERGED_SOURCE_BLOCKED", snapshot.head_commit, snapshot.target_commit, False, "Local and remote histories diverged.", snapshot)
        if snapshot.ahead and not snapshot.behind:
            return self._result("success", "LOCAL_AHEAD", snapshot.head_commit, snapshot.head_commit, False, None, snapshot)
        if not snapshot.behind:
            return self._result("success", "UP_TO_DATE", snapshot.head_commit, snapshot.head_commit, False, None, snapshot)
        if request.check:
            return self._result("update_available", "UPDATE_AVAILABLE", snapshot.head_commit, snapshot.target_commit, False, None, snapshot)
        if request.dry_run:
            return self._result("success", "DRY_RUN", snapshot.head_commit, snapshot.target_commit, False, None, snapshot)
        if not request.yes:
            return self._result("blocked", "UPGRADE_APPROVAL_REQUIRED", snapshot.head_commit, snapshot.target_commit, False, "Use --yes after the preflight result is reviewed.", snapshot)
        if request.tag:
            command = ["checkout", "--detach", f"refs/remotes/{self.remote_name}/aiwf-tags/{request.tag}"]
        else:
            command = ["pull", "--ff-only", self.remote_name, self.branch]
        code, _, error = self._run_git(command)
        if code != 0:
            return self._result("failure", "FAST_FORWARD_FAILED", snapshot.head_commit, None, False, error or "Git update failed.", snapshot)
        after = self.inspect(request.tag)
        if after.head_commit != snapshot.target_commit:
            return self._result("failure", "SOURCE_CHANGED_DURING_PREFLIGHT", snapshot.head_commit, after.head_commit, True, "Post-update commit does not match the preflight target.", after)
        return self._result("success", "UPDATED", snapshot.head_commit, after.head_commit, True, None, after)

    def _result(
        self,
        status: str,
        code: str,
        before: str | None,
        after: str | None,
        mutation: bool,
        failure: str | None,
        snapshot: RepositorySnapshot | None = None,
    ) -> UpgradeResult:
        target_ref = snapshot.target_ref if snapshot else f"{self.remote_name}/{self.branch}"
        next_action = None
        if code == "UPDATE_AVAILABLE":
            next_action = "self-upgrade --yes --json"
        elif code in {"DIRTY_SOURCE_BLOCKED", "DIVERGED_SOURCE_BLOCKED", "DETACHED_SOURCE_BLOCKED"}:
            next_action = "review source repository state, then retry"
        return UpgradeResult(
            schema_version="aiwf.source-upgrade.v1",
            command="self-upgrade",
            status=status,
            code=code,
            source_path=self.source_path,
            remote_name=self.remote_name,
            repository_url=self.repository_url,
            target_ref=target_ref,
            before_commit=before or None,
            after_commit=after or None,
            mutation=mutation,
            changed_artifacts=["source repository"] if mutation else [],
            warnings=[],
            next_action=next_action,
            failure=failure,
        )


def result_exit_code(result: UpgradeResult) -> int:
    return {"success": 0, "update_available": 2, "blocked": 3, "failure": 4}.get(result.status, 4)


def request_from_args(args: Any) -> UpgradeRequest:
    source_path = getattr(args, "source_path", None) or os.environ.get("AIWF_SOURCE_PATH") or os.environ.get("AIWF_FRAMEWORK_ROOT") or "."
    repository_url = getattr(args, "url", None) or os.environ.get("AIWF_SOURCE_REPOSITORY_URL") or DEFAULT_REPOSITORY_URL
    remote_name = getattr(args, "remote", None) or os.environ.get("AIWF_SOURCE_REMOTE") or "origin"
    branch = getattr(args, "branch", None) or os.environ.get("AIWF_SOURCE_BRANCH") or "main"
    tag = getattr(args, "tag", None) or os.environ.get("AIWF_SOURCE_TAG")
    return UpgradeRequest(
        source_path=str(source_path),
        repository_url=str(repository_url),
        remote_name=str(remote_name),
        branch=str(branch),
        tag=str(tag) if tag else None,
        check=bool(getattr(args, "check", False)),
        dry_run=bool(getattr(args, "dry_run", False)),
        yes=bool(getattr(args, "yes", False)),
        json_output=bool(getattr(args, "json", False)),
    )


def handle_update_source(args: Any) -> int:
    request = request_from_args(args)
    service = SourceUpgradeService(request.source_path or ".", request.remote_name, request.repository_url, request.branch)
    result = service.execute(request)
    if request.json_output:
        print(json.dumps(result.payload(), ensure_ascii=False, separators=(",", ":")))
    else:
        print(f"AIWF source update: {result.code}")
        print(f"Source: {result.source_path}")
        if result.failure:
            print(f"Reason: {result.failure}")
    return result_exit_code(result)


__all__ = [
    "DEFAULT_REPOSITORY_URL",
    "RepositorySnapshot",
    "SourceUpgradeService",
    "UpgradeRequest",
    "UpgradeResult",
    "handle_update_source",
    "request_from_args",
    "result_exit_code",
]
