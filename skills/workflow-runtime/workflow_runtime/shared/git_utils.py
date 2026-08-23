import subprocess
from typing import Any

from workflow_runtime.shared.version_detector import \
    detect_project_version_cached


def get_git_info() -> dict[str, Any]:
    """
    Run exactly the 3 allowed git commands to detect current branch and status.
    git describe --tags is REMOVED per FEAT-050.
    """
    info = {
        "is_git_repository": False,
        "branch": "unknown",
        "working_tree": "clean",
        "default_branch": "main",
        "latest_tag": "",  # No longer populated — use detect_project_version_cached()
    }

    # Check git repository
    try:
        res = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, check=True, timeout=5,
        )
        if "true" in res.stdout.strip():
            info["is_git_repository"] = True
    except (subprocess.SubprocessError, FileNotFoundError, subprocess.TimeoutExpired, PermissionError):
        return info

    if info["is_git_repository"]:
        # Get active branch
        try:
            res_branch = subprocess.run(
                ["git", "branch", "--show-current"],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                text=True, timeout=5,
            )
            info["branch"] = res_branch.stdout.strip() or "detached"
        except (subprocess.SubprocessError, subprocess.TimeoutExpired):
            pass

        # Get git status
        try:
            res_status = subprocess.run(
                ["git", "status", "--short"],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                text=True, timeout=5,
            )
            if res_status.stdout.strip():
                info["working_tree"] = "dirty"
        except (subprocess.SubprocessError, subprocess.TimeoutExpired):
            pass

        # NOTE: git describe --tags is REMOVED per FEAT-050 blueprint.
        # Use detect_project_version_cached() for version info.

    return info


def get_version_info() -> dict[str, Any]:
    """
    Deprecated: scans manifest files. Use detect_project_version_cached() instead.
    Kept for backwards compatibility with existing callers — reads .agents/MANIFEST.json only.
    Does NOT run git describe --tags per FEAT-050.
    """
    return detect_project_version_cached()

