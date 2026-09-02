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
) -> dict:
    """add -A, commit (skip if nothing to commit), tag, push branch + tag."""
    repo = (root / path).resolve()
    logs: list[str] = []
    logs.append(_run(repo, ["add", "-A"], dry))

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
        "logs": logs,
    }
