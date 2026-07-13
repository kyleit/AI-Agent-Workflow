"""
FEAT-052: PatchApplier — validate and apply git patches safely.

Rules:
- Never apply without scope validation.
- git apply --check (dry-run) before actual apply.
- Fallback to manual parsing if git unavailable.
- Only modifies workspace files after scope validation passes.
"""

from __future__ import annotations

import os
import re
import subprocess
import tempfile


class PatchConflictError(Exception):
    """Raised when patch touches files outside the declared write_set."""


class PatchApplier:
    """
    Validates patch scope against write_set then applies using git.
    Stateless — no file I/O except reading the patch and applying it.
    """

    def __init__(self, workspace_root: str | None = None):
        self.workspace_root = workspace_root or os.getcwd()

    # ------------------------------------------------------------------
    # validate_patch_scope
    # ------------------------------------------------------------------
    def validate_patch_scope(self, patch_path: str, write_set: list[str]) -> list[str]:
        """
        Parse the patch file and return list of files touched that are
        NOT in the write_set. Empty list means patch is in scope.

        Parameters:
            patch_path: Absolute or relative path to the .patch / .diff file.
            write_set:  List of relative paths the task is allowed to modify.

        Returns:
            List of out-of-scope file paths (empty = all in scope).
        """
        patch_abs = (
            patch_path
            if os.path.isabs(patch_path)
            else os.path.join(self.workspace_root, patch_path)
        )
        if not os.path.exists(patch_abs):
            raise FileNotFoundError(f"Patch file not found: {patch_abs}")

        touched = self._parse_patch_files(patch_abs)
        normalized_write = set(
            p.replace("\\", "/").lstrip("./") for p in write_set
        )
        out_of_scope = [
            f for f in touched
            if f.replace("\\", "/").lstrip("./") not in normalized_write
        ]
        return out_of_scope

    # ------------------------------------------------------------------
    # apply
    # ------------------------------------------------------------------
    def apply(self, task_id: str, patch_path: str, write_set: list[str]) -> dict:
        """
        Validate scope then apply the patch using `git apply`.

        Returns:
            {"status": "applied"|"rejected"|"error", "files_patched": list[str], "error": str|None}
        """
        # 1. Scope validation
        try:
            out_of_scope = self.validate_patch_scope(patch_path, write_set)
        except FileNotFoundError as exc:
            return {"status": "error", "files_patched": [], "error": str(exc)}

        if out_of_scope:
            return {
                "status": "rejected",
                "files_patched": [],
                "error": (
                    f"PatchConflictError: task {task_id} patch touches files "
                    f"outside write_set: {out_of_scope}"
                ),
            }

        patch_abs = (
            patch_path
            if os.path.isabs(patch_path)
            else os.path.join(self.workspace_root, patch_path)
        )
        touched = self._parse_patch_files(patch_abs)

        # 2. Dry-run (--check) first
        dry_run_ok, dry_run_err = self._git_apply(patch_abs, dry_run=True)
        if not dry_run_ok:
            return {
                "status": "rejected",
                "files_patched": [],
                "error": f"git apply --check failed: {dry_run_err}",
            }

        # 3. Actual apply
        ok, err = self._git_apply(patch_abs, dry_run=False)
        if not ok:
            return {
                "status": "error",
                "files_patched": [],
                "error": f"git apply failed: {err}",
            }

        return {"status": "applied", "files_patched": touched, "error": None}

    # ------------------------------------------------------------------
    # rollback_patch
    # ------------------------------------------------------------------
    def rollback_patch(self, patch_path: str) -> bool:
        """
        Reverse-apply the patch using `git apply --reverse`.

        Returns:
            True if rollback succeeded, False otherwise.
        """
        patch_abs = (
            patch_path
            if os.path.isabs(patch_path)
            else os.path.join(self.workspace_root, patch_path)
        )
        ok, _err = self._git_apply(patch_abs, dry_run=False, reverse=True)
        return ok

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _git_apply(
        self,
        patch_abs: str,
        dry_run: bool = False,
        reverse: bool = False,
    ) -> tuple[bool, str]:
        """
        Run `git apply [--check] [--reverse] <patch>`.

        Returns (success: bool, error_message: str).
        Falls back to 'git unavailable' error if git is not in PATH.
        """
        cmd = ["git", "apply"]
        if dry_run:
            cmd.append("--check")
        if reverse:
            cmd.append("--reverse")
        cmd.append(patch_abs)

        try:
            result = subprocess.run(
                cmd,
                cwd=self.workspace_root,
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0:
                return True, ""
            return False, (result.stderr or result.stdout).strip()
        except FileNotFoundError:
            # git not in PATH
            return False, "git executable not found in PATH; cannot apply patch"
        except subprocess.TimeoutExpired:
            return False, "git apply timed out after 30 seconds"

    def _parse_patch_files(self, patch_abs: str) -> list[str]:
        """
        Parse unified diff / git diff headers to extract touched file paths.

        Handles lines like:
            --- a/path/to/file.py
            +++ b/path/to/file.py
            diff --git a/path/to/file.py b/path/to/file.py
        """
        touched: set[str] = set()
        diff_re = re.compile(r"^(?:---|\+\+\+)\s+(?:a/|b/)?(.+)$")
        git_diff_re = re.compile(r"^diff --git a/(.+?) b/(.+)$")

        with open(patch_abs, encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.rstrip()
                # git diff --git header
                m = git_diff_re.match(line)
                if m:
                    touched.add(m.group(2))
                    continue
                # unified diff +++ / --- headers
                m = diff_re.match(line)
                if m:
                    path = m.group(1)
                    # Skip /dev/null
                    if path != "/dev/null":
                        touched.add(path)

        return sorted(touched)
