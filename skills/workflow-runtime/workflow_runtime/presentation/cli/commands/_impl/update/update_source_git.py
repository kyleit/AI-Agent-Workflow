from __future__ import annotations

import argparse
import os
import subprocess
import sys
from typing import Any, cast

from workflow_runtime.presentation.cli.commands._impl.update.update_source_core import (
    RUNTIME_LAST_REQUEST_PATH, RUNTIME_REQUEST_PATH, RUNTIME_RESPONSE_PATH,
    audit_workflow_document_quality, capture_release_metadata_hashes,
    capture_tree_contents, capture_tree_hashes, diff_tree_hashes,
    has_release_metadata_changes, has_workflow_documentation_changes,
    has_workflow_report_changes, prepare_agy_prompt_and_mode, read_json_file,
    resolve_runtime_working_dir, restore_tree_contents, runtime_bus_response,
    sanitize_artifact_tree, write_json_file_atomic)


def execute_runtime_bus_request(payload: dict[str, Any]) -> dict[str, Any]:
    """Execute one allowlisted runtime command-bus request."""
    if payload.get("type") != "RUNTIME_COMMAND":
        raise ValueError("runtime request type must be RUNTIME_COMMAND")

    command = str(payload.get("command", "")).strip()
    idempotency_key = str(payload.get("idempotency_key", "")).strip()
    args_raw = payload.get("args")
    if not isinstance(args_raw, dict):
        raise ValueError("runtime request args must be a JSON object")
    args: dict[str, Any] = cast(dict[str, Any], args_raw)
    if not idempotency_key:
        raise ValueError("runtime request requires idempotency_key")

    if command == "deps.resolve":
        skill = str(args.get("skill", "")).strip()
        if not skill:
            raise ValueError("deps.resolve requires args.skill")
        from workflow_runtime.application.dependency.dependency_resolver import (
            parse_requirements, resolve_requirements)
        reqs = parse_requirements(skill)
        ctx = resolve_requirements(skill, reqs)
        return runtime_bus_response(
            "OK",
            command,
            idempotency_key,
            f"Resolved {len(ctx.resolved)} dependencies for '{skill}'.",
            {
                "skill": skill,
                "dependencies_path": ".agents/state/runtime/dependencies.json",
                "warnings": ctx.warnings,
            },
        )

    if command == "git.status":
        branch = subprocess.run(
            ["git", "branch", "--show-current"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        status = subprocess.run(
            ["git", "status", "--short"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        if branch.returncode != 0 or status.returncode != 0:
            raise ValueError((branch.stderr or status.stderr or "git status failed").strip())
        return runtime_bus_response(
            "OK",
            command,
            idempotency_key,
            "Read git branch and short status.",
            {
                "branch": branch.stdout.strip(),
                "status_short": status.stdout.splitlines(),
            },
        )

    if command == "git.add":
        raw_files = args.get("files") or ["."]
        files: list[str] = [str(raw_files)] if isinstance(raw_files, str) else [str(f) for f in cast(list[Any], raw_files)]
        proc = subprocess.run(
            ["git", "add"] + files,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        if proc.returncode != 0:
            raise ValueError((proc.stderr or "git add failed").strip())
        return runtime_bus_response(
            "OK",
            command,
            idempotency_key,
            f"Staged {len(files)} files/paths via git add.",
            {"files": files, "output": proc.stdout.strip()},
        )

    if command == "git.commit":
        message = str(args.get("message", "")).strip()
        if not message:
            raise ValueError("git.commit requires args.message")
        proc = subprocess.run(
            ["git", "commit", "-m", message],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        if proc.returncode != 0:
            raise ValueError((proc.stderr or proc.stdout or "git commit failed").strip())
        return runtime_bus_response(
            "OK",
            command,
            idempotency_key,
            f"Created git commit: {message}",
            {"output": proc.stdout.strip()},
        )

    if command == "git.diff":
        proc = subprocess.run(
            ["git", "diff", "--shortstat"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        return runtime_bus_response(
            "OK",
            command,
            idempotency_key,
            "Read git diff shortstat.",
            {"shortstat": proc.stdout.strip()},
        )

    if command == "agy.run":
        prompt = str(args.get("prompt", "")).strip()
        if not prompt:
            raise ValueError("agy.run requires args.prompt")

        cmd = ["agy", "--dangerously-skip-permissions"]
        model = str(args.get("model", "gemini-3.6-flash-high")).strip()
        if model:
            cmd.extend(["--model", model])
        effort = str(args.get("effort", "high")).strip()
        if effort:
            cmd.extend(["--effort", effort])
        work_dir = str(resolve_runtime_working_dir())
        raw_p, raw_m = prepare_agy_prompt_and_mode(prompt)
        prompt = str(raw_p)
        mode = str(raw_m)
        aiwf_guard_applied = True
        if mode:
            cmd.extend(["--mode", mode])
        if conversation := str(args.get("conversation", "")).strip():
            cmd.extend(["--conversation", conversation])
        project = str(args.get("project", ".")).strip() or "."
        add_dir = project if os.path.isabs(project) else os.path.abspath(os.path.join(work_dir, project))
        cmd.extend(["--add-dir", add_dir])
        print_timeout = str(args.get("print_timeout", "10m")).strip() or "10m"
        cmd.extend(["--print-timeout", print_timeout, "--print", prompt])
        timeout_seconds = int(str(args.get("timeout_seconds", 900)))
        protected_roots = ("skills", os.path.join(".agents", "skills"))
        mirror_roots = (os.path.join(".agents", "skills"),)
        protect_source_roots = aiwf_guard_applied
        protect_mirror_roots = not bool(args.get("allow_mirror_source_changes", False))
        guarded_hashes_before = capture_tree_hashes(work_dir, protected_roots) if protect_source_roots else {}
        guarded_contents_before = capture_tree_contents(work_dir, protected_roots) if protect_source_roots else {}
        mirror_hashes_before = capture_tree_hashes(work_dir, mirror_roots) if protect_mirror_roots else {}
        mirror_contents_before = capture_tree_contents(work_dir, mirror_roots) if protect_mirror_roots else {}
        docs_hashes_before = capture_tree_hashes(work_dir, ("docs",))
        release_metadata_before = capture_release_metadata_hashes(work_dir)

        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
            encoding="utf-8",
            timeout=timeout_seconds,
            cwd=work_dir,
        )
        if proc.returncode != 0:
            raise ValueError((proc.stderr or proc.stdout or "agy failed").strip())
        sanitized_artifacts = sanitize_artifact_tree(work_dir, ("docs",))
        docs_hashes_after = capture_tree_hashes(work_dir, ("docs",))
        if protect_mirror_roots:
            mirror_changes = diff_tree_hashes(
                mirror_hashes_before,
                capture_tree_hashes(work_dir, mirror_roots),
            )
            if mirror_changes:
                restore_tree_contents(work_dir, mirror_roots, mirror_contents_before)
                changed_preview = ", ".join(mirror_changes[:20])
                suffix = "" if len(mirror_changes) <= 20 else f", ... +{len(mirror_changes) - 20} more"
                raise ValueError(
                    "AIWF guarded AGY run attempted forbidden installed mirror changes under .agents/skills/. "
                    "Edit source skills/ or use the explicit runtime mirror/export path instead: "
                    f"{changed_preview}{suffix}"
                )
        if protect_source_roots:
            guarded_changes = diff_tree_hashes(
                guarded_hashes_before,
                capture_tree_hashes(work_dir, protected_roots),
            )
            if guarded_changes:
                restore_tree_contents(work_dir, protected_roots, guarded_contents_before)
                changed_preview = ", ".join(guarded_changes[:20])
                suffix = "" if len(guarded_changes) <= 20 else f", ... +{len(guarded_changes) - 20} more"
                raise ValueError(
                    "AIWF guarded AGY run attempted source or mirror changes before blueprint approval: "
                    f"{changed_preview}{suffix}"
                )
        documentation_required = bool(args.get("require_documentation") or aiwf_guard_applied)
        if documentation_required and not has_workflow_documentation_changes(docs_hashes_before, docs_hashes_after):
            excerpt = (proc.stdout or proc.stderr or "").strip()[:4000]
            raise ValueError(
                "agy.run completed without creating or updating workflow documentation under docs/. "
                f"Output excerpt: {excerpt}"
            )
        changed_docs = diff_tree_hashes(docs_hashes_before, docs_hashes_after)
        if bool(args.get("require_report")):
            if not has_workflow_report_changes(changed_docs):
                excerpt = (proc.stdout or proc.stderr or "").strip()[:4000]
                raise ValueError(
                    "agy.run completed without creating or updating a workflow report. "
                    f"Output excerpt: {excerpt}"
                )
        if bool(args.get("require_release_artifacts")):
            release_metadata_after = capture_release_metadata_hashes(work_dir)
            if not has_release_metadata_changes(release_metadata_before, release_metadata_after):
                excerpt = (proc.stdout or proc.stderr or "").strip()[:4000]
                raise ValueError(
                    "agy.run completed without updating release metadata "
                    "(CHANGELOG.md, MANIFEST.json, package.json, or pyproject.toml). "
                    f"Output excerpt: {excerpt}"
                )
            if not has_workflow_report_changes(changed_docs):
                excerpt = (proc.stdout or proc.stderr or "").strip()[:4000]
                raise ValueError(
                    "agy.run completed without creating or updating a release workflow report under docs/. "
                    f"Output excerpt: {excerpt}"
                )
        if bool(args.get("require_blueprint_quality")):
            quality_res = audit_workflow_document_quality(work_dir)
            raw_issues = quality_res.get("issues")
            quality_issues: list[str] = cast(list[str], raw_issues) if isinstance(raw_issues, list) else []
            if quality_issues:
                issue_preview = "; ".join(quality_issues[:20])
                suffix = "" if len(quality_issues) <= 20 else f"; ... +{len(quality_issues) - 20} more"
                raise ValueError(f"agy.run workflow documentation quality gate failed: {issue_preview}{suffix}")
        return runtime_bus_response(
            "OK",
            command,
            idempotency_key,
            "Executed agy headless run successfully.",
            {
                "output": proc.stdout.strip(),
                "stderr": proc.stderr.strip(),
                "aiwf_guard_applied": aiwf_guard_applied,
                "mode": mode,
                "cwd": os.path.relpath(work_dir, os.getcwd()),
                "docs_changed": diff_tree_hashes(docs_hashes_before, docs_hashes_after),
                "sanitized_artifacts": sanitized_artifacts,
            },
        )

    if command == "export.build":
        cmd = ["make", "export"] if sys.platform != "win32" else ["cmd.exe", "/c", "make export"]
        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        if proc.returncode != 0:
            raise ValueError((proc.stderr or proc.stdout or "make export failed").strip())
        return runtime_bus_response(
            "OK",
            command,
            idempotency_key,
            "Ran make export successfully.",
            {"output": proc.stdout.strip()},
        )

    if command == "mirror.sync":
        from workflow_runtime.presentation.cli.commands._impl.shared_helpers import \
            _run_core_cli_handler  # pyright: ignore[reportPrivateUsage]
        _run_core_cli_handler("handle_export", argparse.Namespace(action="mirror", target="all", check=False, clean=False))
        return runtime_bus_response(
            "OK",
            command,
            idempotency_key,
            "Synchronized skills mirror tree to .agents/skills/.",
            {"exit_code": 0},
        )

    raise ValueError(f"Unknown or unhandled runtime command: {command}")


def process_runtime_bus_once(
    request_path: str = RUNTIME_REQUEST_PATH,
    response_path: str = RUNTIME_RESPONSE_PATH,
    last_request_path: str = RUNTIME_LAST_REQUEST_PATH,
) -> bool:
    if not os.path.exists(request_path):
        return False

    try:
        req = read_json_file(request_path)
    except Exception as exc:
        err_res = runtime_bus_response(
            "ERROR",
            "unknown",
            "unknown",
            f"Failed to parse runtime request file: {exc}",
            error=str(exc),
        )
        write_json_file_atomic(response_path, err_res)
        try:
            os.remove(request_path)
        except OSError:
            pass
        return True

    idempotency_key = str(req.get("idempotency_key", "")).strip() or "unknown"
    command = str(req.get("command", "")).strip() or "unknown"

    try:
        res = execute_runtime_bus_request(req)
        write_json_file_atomic(response_path, res)
        write_json_file_atomic(last_request_path, req)
        return True
    except Exception as exc:
        err_res = runtime_bus_response(
            "ERROR",
            command,
            idempotency_key,
            f"Runtime execution error: {exc}",
            error=str(exc),
        )
        write_json_file_atomic(response_path, err_res)
        write_json_file_atomic(last_request_path, req)
        return True
    finally:
        try:
            os.remove(request_path)
        except OSError:
            pass


__all__ = [
    "execute_runtime_bus_request",
    "process_runtime_bus_once",
]
