#!/usr/bin/env python3
"""AIWF Source-Write Gate — deterministic, tool-agnostic enforcement core.

This module is the single source of truth for deciding whether a change to a
SOURCE code file is authorized under the AIWF workflow. It is invoked by:

  * Git ``pre-commit`` / ``pre-push`` hooks  (universal, every AI/tool)
  * Claude Code ``PreToolUse`` hook          (edit-time, Claude only)

Authorization rule (deterministic — no model involved):
  A source file change is allowed ONLY IF a fresh authorization exists at
  ``.agents/state/source-write-authorization.json`` that:
    1. has ``authorized == true``
    2. names the CURRENTLY active work item (``.agents/state/workflow.json``)
    3. references a blueprint doc that physically exists on disk
    4. is not expired (optional ``expires_at``)

  The legacy ``approvals.json`` blueprint flag is intentionally NOT trusted on
  its own because it can go stale (e.g. an old approved FEAT-405 would
  otherwise unlock every future edit).

Escape hatch: set env ``AIWF_BYPASS=1`` (logged) for emergencies / bootstrap.

No third-party dependencies — stdlib only.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

# --- Configuration ----------------------------------------------------------

# File extensions considered "source code" (lowercase, with leading dot).
SOURCE_EXTS = {
    ".py", ".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx", ".go", ".rs",
    ".rb", ".php", ".java", ".c", ".cc", ".cpp", ".h", ".hpp", ".cs",
    ".css", ".scss", ".sass", ".html", ".htm", ".vue", ".svelte", ".sql",
    ".ps1", ".psm1", ".sh", ".bash", ".zsh", ".kt", ".swift",
}

# Path prefixes (repo-relative, posix) that are NEVER gated:
#  - mirrors (.agents, public_export) — generated, edits belong in source
#  - docs / markdown — the workflow documents themselves
#  - the enforcement tooling itself (so it can be committed/bootstrapped)
#  - scratch / build / vendored output
EXCLUDED_PREFIXES = (
    ".agents/",
    "public_export/",
    "docs/",
    ".git/",
    ".claude/",
    "skills/strict-code-block-gate/",
    "tools/githooks/",
    "tools/aiwf-hooks/",
    "node_modules/",
    "__pycache__/",
    ".vscode/",
    "scratch/",
    "tmp/",
    "test-results/",
    "screenshots/",
    "artifacts/",
    "interactive-docs/",
    "desktop/",
)

AUTH_REL = ".agents/state/source-write-authorization.json"
WORKFLOW_REL = ".agents/state/workflow.json"
APPROVALS_REL = ".agents/state/approvals.json"
CODE_BLOCK_GATE_STATE_REL = ".agents/state/code-block-gate.json"
AIWF_MARKER_REL = ".agents/AI_RULES.md"  # presence => this is an AIWF project


# --- Helpers ----------------------------------------------------------------

def repo_root(start: Path | None = None) -> Path | None:
    probe = (start or Path.cwd()).resolve()
    if (
        (probe / ".agents" / "AI_RULES.md").is_file()
        or (probe / "AI_RULES.md").is_file()
        or (probe / ".agents" / "project.config.json").is_file()
    ):
        return probe
    # An uninitialized workspace must remain local even when nested in a
    # parent Git checkout. Hooks should be inert until that workspace opts in.
    if not (probe / ".git").exists():
        return probe
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=str(probe),
            capture_output=True, text=True, check=True,
        )
        return Path(out.stdout.strip())
    except Exception:
        return None


def is_aiwf_project(root: Path) -> bool:
    return (
        (root / AIWF_MARKER_REL).exists()
        or (root / "AI_RULES.md").exists()
        or (root / ".agents" / "project.config.json").exists()
    )


def _rel_posix(root: Path, path: str) -> str:
    p = Path(path)
    try:
        rel = p.resolve().relative_to(root.resolve())
    except Exception:
        # Already relative or outside root — normalise separators.
        rel = Path(str(path).replace("\\", "/"))
    return rel.as_posix()


def is_source_file(root: Path, path: str) -> bool:
    rel = _rel_posix(root, path)
    if any(rel == "" or rel.startswith(pref) for pref in EXCLUDED_PREFIXES):
        return False
    if rel.lower().endswith(".md"):
        return False
    return Path(rel).suffix.lower() in SOURCE_EXTS


def _read_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return None


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def active_work_item(root: Path) -> str | None:
    data = _read_json(root / WORKFLOW_REL)
    if not isinstance(data, dict):
        return None
    return data.get("active_workflow") or (data.get("work_item") or {}).get("id")


def _now() -> _dt.datetime:
    return _dt.datetime.now(_dt.timezone.utc)


def _parse_iso(s: str) -> _dt.datetime | None:
    try:
        return _dt.datetime.fromisoformat(s)
    except Exception:
        return None


# Workflow phases at/after which source writes are permitted (blueprint has
# been approved and the workflow has entered implementation).
IMPLEMENTATION_PHASES = {
    "implementation", "implementing", "implement",
    "debug", "debugging",
    "verify", "verification", "verifying",
    "release", "releasing",
}


def _explicit_authorization(root: Path) -> tuple[bool | None, str]:
    """Optional explicit override file. Returns (True/False/None, reason).

    None => no explicit file present (fall back to state-derived check).
    """
    auth = _read_json(root / AUTH_REL)
    if not isinstance(auth, dict):
        return None, ""
    if not auth.get("authorized"):
        return False, "explicit authorization present but authorized=false"
    active = active_work_item(root)
    auth_wi = auth.get("work_item")
    if active and auth_wi and auth_wi != active:
        return False, f"explicit authorization is for {auth_wi} but active work item is {active}"
    bp = auth.get("blueprint_path")
    if not bp or not (root / bp).exists():
        return False, f"explicit authorization blueprint missing: {bp}"
    exp = auth.get("expires_at")
    if exp:
        dt = _parse_iso(exp)
        if dt and dt < _now():
            return False, f"explicit authorization expired at {exp}"
    return True, f"explicit authorization for {auth_wi} (blueprint: {bp})"


def _state_authorization(root: Path) -> tuple[bool, str]:
    """Derive authorization automatically from AIWF workflow state.

    No one runs a command: approving the blueprint (which advances the
    workflow into an implementation phase and records the approval) unlocks
    source writes on its own. Bound to the active work item to avoid a stale
    approval unlocking a different task.
    """
    wf = _read_json(root / WORKFLOW_REL)
    if not isinstance(wf, dict):
        return False, "no workflow.json — run /aiwf to start a workflow"
    runtime = _read_json(root / ".agents" / "state" / "runtime.json") or {}
    status = str(wf.get("status") or runtime.get("status") or "").upper()
    if status not in ("IN_PROGRESS", "ACTIVE", "WAITING_INPUT"):
        return False, f"no active workflow (status={status or 'missing'})"

    active = active_work_item(root)
    phase = str(wf.get("active_phase") or wf.get("phase") or "").lower()
    if phase not in IMPLEMENTATION_PHASES:
        return False, (
            f"workflow phase '{phase or 'unknown'}' is before implementation — "
            "generate and APPROVE the Technical Blueprint first (/aiwf)"
        )

    approval_path = root / APPROVALS_REL
    if active:
        scoped_path = root / ".agents" / "state" / "work-items" / str(active) / "approvals.json"
        if scoped_path.exists():
            approval_path = scoped_path
    ap = _read_json(approval_path) or {}
    bp = ap.get("blueprint") if isinstance(ap, dict) else None
    if not isinstance(bp, dict) or not bp.get("approved"):
        return False, f"blueprint not approved in {approval_path.relative_to(root).as_posix()}"
    path = bp.get("path")
    if not path:
        return False, f"{approval_path.relative_to(root).as_posix()} blueprint has no path"
    if not (root / path).exists():
        return False, f"approved blueprint doc not found on disk: {path}"

    # Bind the approval to the active work item so a stale approval (e.g. an old
    # FEAT-405) cannot unlock edits for a different active item.
    if active and active not in str(path):
        return False, (
            f"approved blueprint '{path}' is not for active work item {active} "
            "(stale approval) — re-approve a blueprint for this work item"
        )

    gate_ok, gate_reason = _code_block_gate_authorization(root, active, str(path))
    if not gate_ok:
        return False, gate_reason

    return True, f"authorized via state: {active} phase={phase} (blueprint: {path})"


def _code_block_gate_authorization(root: Path, active: str | None, blueprint_path: str) -> tuple[bool, str]:
    """Require the canonical strict CODE_BLOCK_GATE result before source writes."""
    blueprint_abs = root / blueprint_path
    try:
        frontmatter = blueprint_abs.read_text(encoding="utf-8").split("---", 2)
    except OSError as exc:
        return False, f"cannot read approved blueprint '{blueprint_path}': {exc}"
    if len(frontmatter) >= 2:
        for line in frontmatter[1].splitlines():
            key, separator, value = line.partition(":")
            if separator and key.strip().lower() == "code_block_gate":
                if value.strip().upper() in {"NOT_APPLICABLE", "N/A", "NONE"}:
                    return True, f"strict CODE_BLOCK_GATE not applicable ({blueprint_path})"
                break

    candidates = [root / CODE_BLOCK_GATE_STATE_REL]
    if active:
        candidates.append(root / "docs" / "aiwf-runs" / active / "05-blueprint" / "code-block-gate.json")

    existing = [path for path in candidates if path.exists()]
    if not existing:
        return False, "missing canonical code-block-gate.json — run strict-code-block-gate for the approved Blueprint"

    try:
        blueprint_hash = _sha256_file(blueprint_abs)
    except OSError as exc:
        return False, f"cannot hash approved blueprint '{blueprint_path}': {exc}"

    reasons: list[str] = []
    for gate_path in existing:
        result = _read_json(gate_path)
        if not isinstance(result, dict):
            reasons.append(f"{gate_path}: invalid JSON")
            continue
        decision = str(result.get("decision") or result.get("status") or "").upper()
        if decision != "PASS":
            reasons.append(f"{gate_path}: decision is {decision or 'missing'}, expected PASS")
            continue
        if result.get("authority") not in (None, "strict-code-block-gate"):
            reasons.append(f"{gate_path}: authority is not strict-code-block-gate")
            continue
        result_blueprint = str(result.get("blueprint_path") or blueprint_path)
        if result_blueprint.replace("\\", "/") != blueprint_path.replace("\\", "/"):
            reasons.append(f"{gate_path}: blueprint_path does not match approved blueprint")
            continue
        result_hash = result.get("blueprint_full_sha256") or result.get("blueprint_artifact_hash")
        if result_hash != blueprint_hash:
            reasons.append(f"{gate_path}: blueprint hash is stale")
            continue
        blocked = result.get("blocking_findings") or []
        if blocked:
            reasons.append(f"{gate_path}: blocking_findings is not empty")
            continue
        for key in ("per_code_block", "profile_results"):
            bad = [
                item for item in result.get(key, [])
                if str(item.get("status", "")).upper() in ("FAIL", "BLOCKED")
            ]
            if bad:
                reasons.append(f"{gate_path}: {key} contains FAIL/BLOCKED")
                break
        else:
            return True, f"strict CODE_BLOCK_GATE PASS ({gate_path.relative_to(root)})"

    return False, "strict CODE_BLOCK_GATE not valid: " + "; ".join(reasons)


def authorization_status(root: Path) -> tuple[bool, str]:
    """Return (authorized, reason).

    Primary path: derive automatically from workflow state (no manual step).
    An explicit override file, if present, takes precedence (emergency/bootstrap).
    """
    explicit, reason = _explicit_authorization(root)
    if explicit is True:
        return True, reason
    if explicit is False:
        return False, reason
    return _state_authorization(root)


# --- Commands ---------------------------------------------------------------

BLOCK_BANNER = (
    "\n"
    "==================================================================\n"
    " AIWF SOURCE-WRITE GATE — BLOCKED\n"
    "==================================================================\n"
)

HELP_TEXT = (
    "  Source code may not change until the AIWF workflow has produced an\n"
    "  APPROVED Technical Blueprint for the active work item.\n\n"
    "  The AI agent (not the user) must do this:\n"
    "    1. Run /aiwf <request>  (initialize-workflow -> coordinator -> spec\n"
    "       -> blueprint). No manual commands needed.\n"
    "    2. Have the user approve the blueprint (Blueprint Approval Gate).\n"
    "    3. The workflow then records the approval and enters the\n"
    "       implementation phase -> this gate UNLOCKS automatically.\n\n"
    "  The gate reads workflow state; nobody runs a command to unlock.\n"
    "  Emergency bypass (logged, agent/CI only): AIWF_BYPASS=1.\n"
)


def _staged_files(root: Path) -> list[str]:
    out = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
        cwd=str(root), capture_output=True, text=True,
    )
    return [ln for ln in out.stdout.splitlines() if ln.strip()]


def _bypassed() -> bool:
    return os.environ.get("AIWF_BYPASS", "") not in ("", "0", "false", "False")


def cmd_check_git(_args) -> int:
    root = repo_root()
    if not root or not is_aiwf_project(root):
        return 0  # not an AIWF project -> do not interfere
    src = [f for f in _staged_files(root) if is_source_file(root, f)]
    if not src:
        return 0  # docs-only / non-source commit is always fine
    if _bypassed():
        sys.stderr.write("[aiwf-gate] AIWF_BYPASS=1 — source-write gate skipped.\n")
        return 0
    ok, reason = authorization_status(root)
    if ok:
        return 0
    sys.stderr.write(BLOCK_BANNER)
    sys.stderr.write(f"  Reason: {reason}\n\n")
    sys.stderr.write("  Staged source files:\n")
    for f in src:
        sys.stderr.write(f"    - {f}\n")
    sys.stderr.write("\n" + HELP_TEXT)
    sys.stderr.write("==================================================================\n")
    return 1


def _git_lines(root: Path, args: list[str]) -> list[str]:
    try:
        result = subprocess.run(
            ["git", *args], cwd=str(root), capture_output=True, text=True, check=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return []
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def _outgoing_commits(root: Path, local_sha: str, remote_sha: str) -> list[str]:
    zero = "0" * 40
    if not local_sha or local_sha == zero:
        return []
    if not remote_sha or remote_sha == zero:
        return _git_lines(root, ["rev-list", "--reverse", local_sha])
    return _git_lines(root, ["rev-list", "--reverse", f"{remote_sha}..{local_sha}"])


def _commit_parents(root: Path, commit_sha: str) -> list[str]:
    lines = _git_lines(root, ["rev-list", "--parents", "-n", "1", commit_sha])
    return lines[0].split()[1:] if lines else []


def _commit_touches_file(root: Path, commit_sha: str, file_path: str, *, merge: bool = False) -> bool:
    args = ["diff-tree", "--root", "--no-commit-id", "--name-only", "-r"]
    if merge:
        args.append("-m")
    args.extend([commit_sha, "--", file_path])
    return _rel_posix(root, file_path) in {
        _rel_posix(root, value) for value in _git_lines(root, args)
    }


def _authorization_receipts(root: Path) -> list[object]:
    """Load only machine receipts from the two canonical audit locations."""
    values: list[object] = []
    locations = (root / ".agents" / "state" / "audit", root / "docs" / "aiwf-runs")
    for directory in locations:
        if not directory.is_dir():
            continue
        for path in directory.rglob("*"):
            if path.suffix.lower() not in {".json", ".jsonl"} or not path.is_file():
                continue
            try:
                if path.suffix.lower() == ".jsonl":
                    values.extend(json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip())
                else:
                    values.append(json.loads(path.read_text(encoding="utf-8")))
            except (OSError, ValueError, TypeError):
                continue
    return values


def _receipt_authorizes(value: object, commit_sha: str, active_work_item: str | None) -> bool:
    if isinstance(value, list):
        return any(_receipt_authorizes(item, commit_sha, active_work_item) for item in value)
    if not isinstance(value, dict):
        return False
    nested = any(
        _receipt_authorizes(value[key], commit_sha, active_work_item)
        for key in ("receipt", "authorization", "approval", "result", "items", "records")
        if key in value
    )
    if nested:
        return True
    sha_keys = ("commit_sha", "commitSha", "commit", "sha", "head_sha", "headSha")
    recorded = {str(value[key]).lower() for key in sha_keys if value.get(key)}
    if commit_sha.lower() not in recorded:
        return False
    item = value.get("work_item_id", value.get("workflow_id", value.get("workItemId")))
    if active_work_item and item and str(item) != active_work_item:
        return False
    marker = " ".join(str(value.get(key, "")) for key in ("status", "decision", "result", "outcome")).lower()
    return bool(value.get("authorized") is True or value.get("approved") is True or value.get("completed") is True or any(
        token in marker for token in ("authorized", "approved", "completed", "success", "pass", "released")
    ))


def _is_commit_or_history_authorized(
    root: Path,
    file_path: str,
    local_sha: str,
    remote_sha: str,
) -> bool:
    """Authorize a pushed file only through its exact outgoing commit history."""
    active = active_work_item(root)
    receipts = _authorization_receipts(root)
    for commit_sha in _outgoing_commits(root, local_sha, remote_sha):
        parents = _commit_parents(root, commit_sha)
        if len(parents) > 1:
            branch_commits = set()
            for parent in parents:
                branch_commits.update(_git_lines(root, ["rev-list", "--not", *[p for p in parents if p != parent], parent]))
            if not any(
                _commit_touches_file(root, branch, file_path) and
                any(_receipt_authorizes(receipt, branch, active) for receipt in receipts)
                for branch in branch_commits
            ):
                continue
            return True
        if _commit_touches_file(root, commit_sha, file_path) and any(
            _receipt_authorizes(receipt, commit_sha, active) for receipt in receipts
        ):
            return True
    return False


def cmd_check_files(_args) -> int:
    """Check ``local_sha<TAB>remote_sha<TAB>file`` records from pre-push."""
    root = repo_root()
    if not root or not is_aiwf_project(root):
        return 0
    records = []
    for line in sys.stdin.read().splitlines():
        fields = line.split("\t", 2)
        if len(fields) == 3:
            local_sha, remote_sha, file_path = (field.strip() for field in fields)
        else:
            local_sha, remote_sha, file_path = "", "", line.strip()
        if file_path and is_source_file(root, file_path):
            records.append((local_sha, remote_sha, file_path))
    src = sorted({file_path for _, _, file_path in records})
    if not src:
        return 0
    if _bypassed():
        sys.stderr.write("[aiwf-gate] AIWF_BYPASS set — push gate skipped.\n")
        return 0
    ok, reason = authorization_status(root)
    if ok:
        return 0

    unauthorized = sorted({
        file_path for local_sha, remote_sha, file_path in records
        if not local_sha or not _is_commit_or_history_authorized(root, file_path, local_sha, remote_sha)
    })

    if not unauthorized:
        return 0

    sys.stderr.write(BLOCK_BANNER)
    sys.stderr.write(f"  Reason: {reason}\n\n")
    sys.stderr.write("  Unauthorized source files in the push:\n")
    for f in unauthorized:
        sys.stderr.write(f"    - {f}\n")
    sys.stderr.write("\n" + HELP_TEXT)
    sys.stderr.write("==================================================================\n")
    return 1


def _receipt_dir(root: Path) -> Path:
    cfg = None
    for c in (root / "release.config.json", root / ".agents" / "release.config.json"):
        cfg = _read_json(c)
        if isinstance(cfg, dict):
            break
    rel = (cfg or {}).get("receipt_dir", ".agents/state/release")
    return root / rel


def cmd_check_release_tags(_args) -> int:
    """Block pushing a v* tag that has no release receipt (pre-push backstop).

    stdin: git pre-push lines '<local ref> <local sha> <remote ref> <remote sha>'.
    A release must go through `python tools/release.py` (which writes the receipt).
    """
    root = repo_root()
    if not root or not is_aiwf_project(root):
        return 0
    if _bypassed():
        return 0
    import re as _re
    rdir = _receipt_dir(root)
    missing: list[str] = []
    for line in sys.stdin.read().splitlines():
        parts = line.split()
        if not parts:
            continue
        local_ref = parts[0]
        m = _re.match(r"^refs/tags/v(\d+\.\d+\.\d+)$", local_ref)
        if not m:
            continue
        version = m.group(1)
        if not (rdir / f"{version}.json").exists():
            missing.append(f"v{version}")
    if not missing:
        return 0
    sys.stderr.write(BLOCK_BANNER.replace("SOURCE-WRITE GATE", "RELEASE GATE"))
    sys.stderr.write("  Release tag push blocked — no release receipt found.\n")
    sys.stderr.write(f"  Tags: {', '.join(missing)}\n")
    sys.stderr.write(f"  Expected receipt in: {rdir.relative_to(root)}/<version>.json\n\n")
    sys.stderr.write("  Run the release through the orchestrator instead:\n")
    sys.stderr.write("    python tools/release.py     # installed projects: python .agents/release.py ; or: make release\n")
    sys.stderr.write("  It runs gates in order and writes the receipt that unlocks the push.\n")
    sys.stderr.write("  Emergency bypass (logged): AIWF_BYPASS=1.\n")
    sys.stderr.write("==================================================================\n")
    return 1


def cmd_check_file(args) -> int:
    root = repo_root()
    if not root or not is_aiwf_project(root):
        return 0
    if not is_source_file(root, args.path):
        return 0
    if _bypassed():
        return 0
    ok, reason = authorization_status(root)
    if ok:
        return 0
    sys.stderr.write(BLOCK_BANNER)
    sys.stderr.write(f"  Blocked edit: {args.path}\n")
    sys.stderr.write(f"  Reason: {reason}\n\n")
    sys.stderr.write(HELP_TEXT)
    sys.stderr.write("==================================================================\n")
    return 1


def cmd_authorize(args) -> int:
    root = repo_root()
    if not root:
        sys.stderr.write("[aiwf-gate] not a git repo\n")
        return 1
    wi = args.work_item or active_work_item(root)
    if not wi:
        sys.stderr.write("[aiwf-gate] cannot resolve work item (pass --work-item)\n")
        return 1
    if not (root / args.blueprint).exists():
        sys.stderr.write(f"[aiwf-gate] blueprint not found: {args.blueprint}\n")
        return 1
    payload = {
        "work_item": wi,
        "authorized": True,
        "blueprint_path": args.blueprint,
        "approved_by": args.by,
        "approved_at": _now().isoformat(),
    }
    if args.ttl_hours:
        payload["expires_at"] = (_now() + _dt.timedelta(hours=args.ttl_hours)).isoformat()
    dest = root / AUTH_REL
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"[aiwf-gate] authorized source writes for {wi} (blueprint: {args.blueprint})")
    return 0


def cmd_revoke(_args) -> int:
    root = repo_root()
    if not root:
        return 1
    dest = root / AUTH_REL
    if dest.exists():
        dest.unlink()
        print("[aiwf-gate] source-write authorization revoked.")
    else:
        print("[aiwf-gate] no active authorization.")
    return 0


def cmd_status(_args) -> int:
    root = repo_root()
    if not root:
        print("not a git repo")
        return 1
    print(f"repo:          {root}")
    print(f"aiwf project:  {is_aiwf_project(root)}")
    print(f"active item:   {active_work_item(root)}")
    ok, reason = authorization_status(root)
    print(f"authorized:    {ok}")
    print(f"reason:        {reason}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="aiwf_gate", description="AIWF source-write gate")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("check-git", help="check staged files (pre-commit)").set_defaults(fn=cmd_check_git)
    sub.add_parser("check-files", help="check newline-separated files from stdin (pre-push)").set_defaults(fn=cmd_check_files)
    sub.add_parser("check-release-tags", help="block v* tag push without a release receipt (pre-push)").set_defaults(fn=cmd_check_release_tags)
    cf = sub.add_parser("check-file", help="check one file (edit-time hook)")
    cf.add_argument("path")
    cf.set_defaults(fn=cmd_check_file)
    az = sub.add_parser("authorize", help="grant source-write authorization")
    az.add_argument("--work-item", default=None)
    az.add_argument("--blueprint", required=True)
    az.add_argument("--by", default="user")
    az.add_argument("--ttl-hours", type=float, default=0)
    az.set_defaults(fn=cmd_authorize)
    sub.add_parser("revoke", help="revoke authorization").set_defaults(fn=cmd_revoke)
    sub.add_parser("status", help="show gate status").set_defaults(fn=cmd_status)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    raise SystemExit(main())
