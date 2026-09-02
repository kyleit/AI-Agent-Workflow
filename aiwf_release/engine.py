"""Pipeline executor: runs the declared release steps in order and writes a
tamper-evident release receipt the git pre-push backstop verifies."""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
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
    plan = versioning.compute_next(root, cfg["version"], override_part)
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
    }

    receipt["gates"] = _preflight(root, cfg, plan, dry)

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
            r = gitsteps.repo_release(root, step["path"], tag, msg, remote, branch, force, dry)
            receipt["repos"].append({k: r[k] for k in ("path", "tag", "sha")})
            receipt["steps"].append({"step": name, "path": step["path"], "tag": tag})
        else:
            raise ReleaseError(f"unknown step: {name}")

    receipt["finished_at"] = _now_iso()
    # Never write a receipt on dry-run: a receipt authorizes a real tag push via
    # the pre-push backstop, so a dry-run must not create one.
    receipt["receipt_file"] = "(dry-run — not written)" if dry else _write_receipt(root, cfg, receipt)
    return receipt
