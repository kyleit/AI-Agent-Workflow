"""Git side-effect steps: multi-repo/submodule release in a fixed order."""

from __future__ import annotations

import subprocess
from pathlib import Path


class GitError(Exception):
    pass


def _run(cwd: Path, args: list[str], dry: bool) -> str:
    printable = "git " + " ".join(args)
    if dry:
        return f"[dry-run] ({cwd}) {printable}"
    out = subprocess.run(["git", *args], cwd=str(cwd), capture_output=True, text=True)
    if out.returncode != 0:
        raise GitError(f"({cwd}) {printable}\n{out.stderr.strip()}")
    return out.stdout.strip()


def current_branch(root: Path) -> str:
    return subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=str(root),
        capture_output=True, text=True,
    ).stdout.strip()


def is_clean(root: Path) -> bool:
    out = subprocess.run(
        ["git", "status", "--porcelain"], cwd=str(root),
        capture_output=True, text=True,
    ).stdout.strip()
    return out == ""


def is_release_ready(root: Path) -> bool:
    """Allow a clean tree or an explicitly staged release snapshot.

    A staged snapshot is the Agent-friendly handoff: every intended change is
    already selected, with no unstaged or untracked file left for the release
    pipeline to accidentally absorb.
    """
    status = subprocess.run(
        ["git", "status", "--porcelain=v1", "--untracked-files=all"],
        cwd=str(root), capture_output=True, text=True,
    ).stdout.splitlines()
    if any(line.startswith("??") for line in status):
        return False
    unstaged = subprocess.run(
        ["git", "diff", "--quiet"], cwd=str(root)
    ).returncode
    return unstaged == 0


def head_sha(root: Path) -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=str(root),
        capture_output=True, text=True,
    ).stdout.strip()


def _normalise_relative(value: str) -> str:
    value = value.replace("\\", "/")
    while value.startswith("./"):
        value = value[2:]
    return value


def validate_repo_relative_scope(repo: Path, files: list[str], *, allow_empty: bool = False) -> list[str]:
    """Validate and normalise an explicit release scope for one repository."""
    repo = repo.resolve()
    result: set[str] = set()
    for raw in files:
        if not isinstance(raw, str) or not raw.strip():
            continue
        relative = _normalise_relative(raw.strip())
        candidate = (repo / relative).resolve()
        if Path(relative).is_absolute() or relative == ".." or relative.startswith("../"):
            raise GitError(f"release scope must be repository-relative: {raw}")
        if repo != candidate and repo not in candidate.parents:
            raise GitError(f"release scope escapes repository: {raw}")
        if not candidate.exists():
            raise GitError(f"release scope path does not exist: {raw}")
        result.add(relative)
    if not result and not allow_empty:
        raise GitError("release scope is empty")
    return sorted(result)


def staged_files(repo: Path) -> list[str]:
    out = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
        cwd=str(repo), capture_output=True, text=True,
    )
    return sorted({_normalise_relative(line.strip()) for line in out.stdout.splitlines() if line.strip()})


def dirty_files(repo: Path) -> list[str]:
    """Return tracked and untracked project files without parsing porcelain columns."""
    tracked = subprocess.run(
        ["git", "diff", "--name-only", "HEAD"],
        cwd=str(repo), capture_output=True, text=True,
    )
    untracked = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard"],
        cwd=str(repo), capture_output=True, text=True,
    )
    return sorted({
        _normalise_relative(line.strip())
        for line in (tracked.stdout + "\n" + untracked.stdout).splitlines()
        if line.strip()
    })


def is_ignored(repo: Path, relative: str) -> bool:
    """Return whether Git would reject the path as ignored during staging."""
    result = subprocess.run(
        ["git", "check-ignore", "--no-index", "--quiet", "--", relative],
        cwd=str(repo), capture_output=True,
    )
    return result.returncode == 0


def stage_submodule_pointer(root: Path, sub_path: str, dry: bool) -> str:
    return _run(root, ["add", sub_path], dry)


def repo_release(
    root: Path,
    path: str,
    tag: str,
    message: str,
    remote: str,
    branch: str,
    force: bool,
    dry: bool,
    files: list[str] | None = None,
) -> dict:
    """Release only an explicit file scope, then commit, tag, and push."""
    repo = (root / path).resolve()
    logs: list[str] = []
    if files is None:
        raise GitError("release scope must be explicit")
    safe_files = validate_repo_relative_scope(repo, files, allow_empty=True)
    existing_staged = set(staged_files(repo)) if not dry else set()
    outside = sorted(existing_staged - set(safe_files))
    if outside:
        logs.append(_run(repo, ["reset", "--", *outside], dry))
    if safe_files:
        logs.append(_run(repo, ["add", "--", *safe_files], dry))
    else:
        logs.append(f"({repo}) nothing selected for staging")

    # commit only if there is something staged
    if dry:
        logs.append(f"[dry-run] ({repo}) git commit -m {message!r}")
    else:
        staged = subprocess.run(
            ["git", "diff", "--cached", "--quiet"], cwd=str(repo)
        ).returncode
        if staged != 0:  # 1 => there are staged changes
            logs.append(_run(repo, ["commit", "-m", message], dry))
        else:
            logs.append(f"({repo}) nothing to commit")

    tag_args = ["tag", "-f", tag] if force else ["tag", tag]
    logs.append(_run(repo, tag_args, dry))
    push_branch = ["push", "-u", remote, branch] + (["--force"] if force else [])
    logs.append(_run(repo, push_branch, dry))
    push_tag = ["push", remote, tag] + (["--force"] if force else [])
    logs.append(_run(repo, push_tag, dry))

    return {
        "path": path,
        "tag": tag,
        "sha": None if dry else head_sha(repo),
        "files": safe_files,
        "logs": logs,
    }
