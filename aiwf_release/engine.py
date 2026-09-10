"""Pipeline executor: runs the declared release steps in order and writes a
tamper-evident release receipt the git pre-push backstop verifies."""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any

from . import changelog as cl
from . import gitsteps, versioning


class ReleaseError(Exception):
    pass


def _now_iso() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat()


def _today() -> str:
    return _dt.date.today().isoformat()


def _read_json(path: Path) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return None


def _active_work_item(root: Path) -> str | None:
    state = _read_json(root / ".agents" / "state" / "workflow.json")
    if not isinstance(state, dict):
        return None
    work_item = state.get("work_item")
    return str(state.get("active_workflow") or (work_item or {}).get("id") or "") or None


def _normalise_scope(values: object) -> set[str]:
    if not isinstance(values, list):
        return set()
    result: set[str] = set()
    for value in values:
        if not isinstance(value, str) or not value.strip():
            continue
        relative = value.strip().replace("\\", "/")
        while relative.startswith("./"):
            relative = relative[2:]
        if relative.startswith("/") or relative == ".." or relative.startswith("../"):
            continue
        result.add(relative)
    return result


def _declared_scope(root: Path, work_item: str | None) -> set[str]:
    """Read the implementation changeset that the AIWF writer produced."""
    if not work_item:
        return set()
    base = root / "docs" / "aiwf-runs" / work_item / "06-implementation"
    result: set[str] = set()
    changeset = _read_json(base / "source-document-changeset.json")
    if isinstance(changeset, dict):
        result.update(_normalise_scope(changeset.get("source_files")))
        result.update(_normalise_scope(changeset.get("document_files")))
    changed = base / "changed-files.md"
    if changed.is_file():
        text = changed.read_text(encoding="utf-8", errors="replace")
        result.update(_normalise_scope(re.findall(r"`([^`]+)`", text)))
    override = _read_json(root / ".agents" / "state" / "release" / "scope.json")
    if isinstance(override, dict) and override.get("work_item") in (None, work_item):
        result.update(_normalise_scope(override.get("scope")))
    return result


def _scope_digest(root: Path, scope: set[str]) -> str:
    digest = hashlib.sha256()
    for relative in sorted(scope):
        path = root / relative
        if not path.is_file():
            raise ReleaseError(f"release scope path is not a file: {relative}")
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(hashlib.sha256(path.read_bytes()).digest())
        digest.update(b"\n")
    return digest.hexdigest()


def _evidence_path(root: Path, work_item: str, kind: str) -> str | None:
    candidates = [
        root / "docs" / kind / f"{work_item}_{'debug' if kind == 'debug' else 'verify'}.md",
        root / "docs" / "features" / "workflow-runtime" / kind / f"{work_item}_{'debug' if kind == 'debug' else 'verify'}.md",
    ]
    for path in candidates:
        if path.is_file():
            return path.relative_to(root).as_posix()
    return None


def _blueprint_path(root: Path, work_item: str) -> str | None:
    approval = _read_json(root / ".agents" / "state" / "work-items" / work_item / "approvals.json")
    if isinstance(approval, dict):
        blueprint = approval.get("blueprint")
        if isinstance(blueprint, dict) and isinstance(blueprint.get("path"), str):
            path = root / blueprint["path"]
            if path.is_file():
                return path.relative_to(root).as_posix()
    matches = sorted(root.glob(f"docs/features/**/blueprints/{work_item}_*.md"))
    return matches[0].relative_to(root).as_posix() if matches else None


def resolve_release_scope(root: Path, cfg: dict, baseline: set[str]) -> dict[str, Any]:
    """Return only work-item files plus release metadata, excluding existing WIP."""
    work_item = _active_work_item(root)
    declared = _declared_scope(root, work_item)
    current = set(gitsteps.dirty_files(root))
    selected = {
        path for path in declared
        if path in current
        and path != "public_export"
        and not gitsteps.is_ignored(root, path)
    }
    version_files = {cfg["version"]["source_of_truth"].split("#", 1)[0]}
    version_files.update(ref.split("#", 1)[0] for ref in cfg["version"].get("files", []))
    changelog = cfg.get("changelog", {}).get("dev")
    if isinstance(changelog, dict) and changelog.get("path"):
        version_files.add(str(changelog["path"]))
    selected.update(path for path in version_files if path in current)
    selected = {path for path in selected if (root / path).is_file()}
    if not selected:
        raise ReleaseError(
            "release scope is empty; complete the active work-item changeset or provide "
            ".agents/state/release/scope.json"
        )
    excluded = sorted(current - selected - {"public_export"})
    return {
        "work_item": work_item,
        "selected": sorted(selected),
        "excluded_wip": excluded,
        "declared": sorted(declared),
    }


def _write_release_authorization(
    root: Path,
    version: str,
    scope: set[str],
    dry: bool,
) -> dict[str, Any]:
    work_item = _active_work_item(root)
    if not work_item:
        raise ReleaseError("release authorization requires an active AIWF work item")
    blueprint = _blueprint_path(root, work_item)
    debug = _evidence_path(root, work_item, "debug")
    verification = _evidence_path(root, work_item, "verification")
    if not blueprint or not debug or not verification:
        raise ReleaseError("release authorization requires Blueprint, PASS debug, and PASS verification evidence")
    authorization: dict[str, Any] = {
        "schema": "aiwf.release-authorization.v1",
        "authorized": True,
        "operation": "release",
        "work_item": work_item,
        "version": version,
        "blueprint_path": blueprint,
        "blueprint_sha256": hashlib.sha256((root / blueprint).read_bytes()).hexdigest(),
        "debug_path": debug,
        "verification_path": verification,
        "scope": sorted(scope),
        "scope_sha256": _scope_digest(root, scope),
        "issued_at": _now_iso(),
        "expires_at": (_dt.datetime.now(_dt.timezone.utc) + _dt.timedelta(minutes=30)).isoformat(),
    }
    if not dry:
        destination = root / ".agents" / "state" / "release" / "authorization.json"
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(authorization, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return authorization


def _consume_release_authorization(root: Path) -> None:
    path = root / ".agents" / "state" / "release" / "authorization.json"
    try:
        path.unlink()
    except FileNotFoundError:
        pass


def _resume_or_compute(root: Path, cfg: dict, override_part: str | None) -> dict:
    current = versioning.read_version(root, cfg["version"]["source_of_truth"])
    receipt_path = root / cfg.get("receipt_dir", ".agents/state/release") / f"{current}.json"
    receipt = _read_json(receipt_path)
    if isinstance(receipt, dict) and not receipt.get("finished_at") and receipt.get("version") == current:
        tag_exists = subprocess.run(
            ["git", "rev-parse", "--verify", f"refs/tags/v{current}"],
            cwd=str(root), capture_output=True, text=True,
        ).returncode == 0
        if not tag_exists:
            return {
                "current": receipt.get("previous_version", current),
                "next": current,
                "part": receipt.get("bump_part", "patch"),
                "source": cfg["version"]["source_of_truth"],
                "resumed": True,
            }
    plan = versioning.compute_next(root, cfg["version"], override_part)
    plan["resumed"] = False
    return plan


def _run_cmd(cwd: Path, cmd: str, dry: bool) -> str:
    if dry:
        return f"[dry-run] {cmd}"
    out = subprocess.run(cmd, cwd=str(cwd), shell=True, capture_output=True, text=True)
    if out.returncode != 0:
        raise ReleaseError(f"command failed: {cmd}\n{(out.stderr or out.stdout).strip()}")
    return (out.stdout or "").strip()


def _preflight(root: Path, cfg: dict, plan: dict, dry: bool) -> list[dict]:
    results: list[dict] = []
    branch = gitsteps.current_branch(root)
    want = cfg.get("default_branch", "main")
    if branch != want:
        raise ReleaseError(f"preflight: on branch '{branch}', expected '{want}'")
    results.append({"gate": "branch", "ok": True, "detail": branch})

    tree_state = "dry-run"
    if not dry:
        # The release command is the Agent-facing snapshot boundary.  It owns
        # staging through repo_release; users and IDE agents must not be sent
        # away to run git add manually before release can continue.
        tree_state = "auto-snapshot" if not gitsteps.is_clean(root) else "clean"
    results.append({"gate": "clean-tree", "ok": True, "detail": tree_state})

    # version consistency across all files (current values must match source)
    cur = versioning.read_version(root, cfg["version"]["source_of_truth"])
    for ref in cfg["version"]["files"]:
        v = versioning.read_version(root, ref)
        if v != cur:
            raise ReleaseError(f"preflight: version mismatch {ref}={v} != {cur}")
    results.append({"gate": "version-consistency", "ok": True, "detail": cur})

    for g in cfg.get("gates", {}).get("preflight", []):
        _run_cmd(root, g["cmd"], dry)
        results.append({"gate": g.get("name", g["cmd"]), "ok": True})
    return results


def _do_changelog(root: Path, cfg: dict, version: str, dry: bool) -> list[str]:
    tag = versioning.last_tag(root)
    items = cl.collect(root, tag)
    written: list[str] = []
    ch = cfg.get("changelog", {})
    dev = ch.get("dev")
    if dev:
        entry = cl.render(version, _today(), items, dev.get("include", "all"))
        if not dry:
            written.append(cl.prepend(root, dev["path"], entry))
        else:
            written.append(f"[dry-run] dev changelog {dev['path']}\n{entry}")
    prod = ch.get("product")
    if prod:
        entry = cl.render(version, _today(), items, prod.get("include", ["feat", "fix", "perf"]))
        if not dry:
            written.append(cl.prepend(root, prod["path"], entry))
        else:
            written.append(f"[dry-run] product changelog {prod['path']}\n{entry}")
    return written


def _write_receipt(root: Path, cfg: dict, receipt: dict) -> str:
    rel_dir = cfg.get("receipt_dir", ".agents/state/release")
    d = root / rel_dir
    d.mkdir(parents=True, exist_ok=True)
    body = json.dumps(receipt, indent=2, sort_keys=True)
    receipt["content_sha256"] = hashlib.sha256(body.encode("utf-8")).hexdigest()
    dest = d / f"{receipt['version']}.json"
    dest.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    return str(dest.relative_to(root))


def run(root: Path, cfg: dict, override_part: str | None, dry: bool) -> dict:
    plan = _resume_or_compute(root, cfg, override_part)
    version = plan["next"]
    remote = cfg.get("remote_name", "origin")
    branch = cfg.get("default_branch", "main")
    tagname = f"v{version}"

    receipt: dict[str, Any] = {
        "version": version,
        "previous_version": plan["current"],
        "bump_part": plan["part"],
        "branch": branch,
        "started_at": _now_iso(),
        "dry_run": dry,
        "steps": [],
        "repos": [],
        "gates": [],
        "changelogs": [],
        "resumed": bool(plan.get("resumed")),
        "release_scope": {},
    }

    receipt["gates"] = _preflight(root, cfg, plan, dry)
    baseline_by_repo = {".": set(gitsteps.dirty_files(root))}
    for step in cfg["pipeline"]:
        if step.get("step") == "repo-release" and step.get("path") not in baseline_by_repo:
            repo = (root / step["path"]).resolve()
            if repo.is_dir():
                baseline_by_repo[step["path"]] = set(gitsteps.dirty_files(repo))

    # Pre-write receipt before running release pipeline so that pre-push hook can verify it
    if not dry:
        _write_receipt(root, cfg, receipt)

    for step in cfg["pipeline"]:
        name = step["step"]
        if name == "bump-version":
            files = []
            if not dry:
                for ref in cfg["version"]["files"]:
                    files.append(versioning.write_version(root, ref, version))
            receipt["steps"].append({"step": name, "version": version, "files": files})
        elif name == "changelog":
            receipt["changelogs"] = _do_changelog(root, cfg, version, dry)
            receipt["steps"].append({"step": name})
        elif name in ("run", "gate"):
            out = _run_cmd(root, step["cmd"], dry)
            receipt["steps"].append({"step": name, "cmd": step["cmd"], "output": out[:2000]})
        elif name == "submodule-pointer":
            gitsteps.stage_submodule_pointer(root, step["path"], dry)
            receipt["steps"].append({"step": name, "path": step["path"]})
        elif name == "repo-release":
            tag = step.get("tag", "v{version}").replace("{version}", version)
            msg = step.get("message", f"chore(release): {tag}").replace("{version}", version)
            force = bool(step.get("force", True))
            repo_path = (root / step["path"]).resolve()
            if step["path"] == ".":
                scope_info = resolve_release_scope(root, cfg, baseline_by_repo["."])
                root_scope = set(scope_info["selected"])
                if "public_export" in gitsteps.dirty_files(root):
                    root_scope.add("public_export")
                source_scope = {path for path in root_scope if (root / path).is_file()}
                authorization = _write_release_authorization(root, version, source_scope, dry)
                scope_info["authorization"] = {
                    "work_item": authorization["work_item"],
                    "scope_sha256": authorization["scope_sha256"],
                    "expires_at": authorization["expires_at"],
                }
                receipt["release_scope"] = scope_info
                files = sorted(root_scope)
            else:
                before = baseline_by_repo.get(step["path"], set())
                files = sorted(set(gitsteps.dirty_files(repo_path)) - before)
            r = gitsteps.repo_release(root, step["path"], tag, msg, remote, branch, force, dry, files=files)
            if step["path"] == "." and not dry:
                _consume_release_authorization(root)
            receipt["repos"].append({k: r[k] for k in ("path", "tag", "sha")})
            receipt["steps"].append({"step": name, "path": step["path"], "tag": tag, "files": r["files"]})
        else:
            raise ReleaseError(f"unknown step: {name}")

    receipt["finished_at"] = _now_iso()
    # Never write a receipt on dry-run: a receipt authorizes a real tag push via
    # the pre-push backstop, so a dry-run must not create one.
    receipt["receipt_file"] = "(dry-run — not written)" if dry else _write_receipt(root, cfg, receipt)
    return receipt
