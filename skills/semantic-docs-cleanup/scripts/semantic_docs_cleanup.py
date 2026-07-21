#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path


DOCS = Path("docs")
FEATURES = DOCS / "features"
OUT_ROOT = Path("_to_delete") / "semantic-docs-cleanup"
REPORT_ROOT = OUT_ROOT / "reports"
BACKUP_ROOT = OUT_ROOT / "backups"
JUNK_NAMES = {".DS_Store", ".gitkeep"}
FORBIDDEN_DIR_RE = re.compile(r"^(FEAT|FIX|QUICK)-", re.IGNORECASE)
ABSOLUTE_RE = re.compile(r"file:///|/Users/|/Volumes/|[A-Za-z]:\\\\")
TONE_RE = re.compile(r"\bBa\b|thưa Ba|Chào Ba|con đã|con sẽ", re.IGNORECASE)


@dataclass
class Record:
    source_path: str
    git_status: str
    action: str
    target_path: str | None
    backup_path: str | None
    feature_family: str | None
    stage: str | None
    confidence: float
    evidence: str


def run_git(args: list[str]) -> str:
    return subprocess.check_output(["git", *args], text=True, stderr=subprocess.DEVNULL)


def git_status_map() -> dict[str, str]:
    status: dict[str, str] = {}
    try:
        output = run_git(["status", "--porcelain=v1", "--", "docs"])
    except subprocess.CalledProcessError:
        return status
    for line in output.splitlines():
        if not line:
            continue
        code = line[:2]
        path = line[3:]
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        status[path] = code
    return status


def tracked_files() -> set[str]:
    try:
        return set(run_git(["ls-files", "--", "docs"]).splitlines())
    except subprocess.CalledProcessError:
        return set()


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""


def hint_for(path: Path) -> str:
    text = read_text(path)
    lines = []
    for line in text.splitlines()[:120]:
        if line.startswith("#") or ":" in line or "summary" in line.lower() or "problem" in line.lower():
            lines.append(line)
    focused = "\n".join(lines) if lines else text[:4000]
    return f"{path.as_posix()}\n{focused}".lower()


def contains(haystack: str, needles: tuple[str, ...]) -> bool:
    return any(needle in haystack for needle in needles)


def classify_family(path: Path) -> tuple[str, float, str]:
    hint = hint_for(path)
    rules: list[tuple[str, tuple[str, ...], str]] = [
        ("telegram", ("telegram", "bot token", "chat_id", "inbox.json", "outbox", "notify-telegram"), "Telegram notification, bot, or inbox/outbox evidence"),
        ("visualizer", ("visualizer", "webview", "vscode extension", "vs code extension", "sidebar", "drawer", "floating status", "responsive layout", "screenshot", "visual debug"), "Visualizer extension, UI, or visual-debug evidence"),
        ("workflow-coordinator", ("workflow coordinator", "workflow-coordinator", "orchestrator", "approval gate", "choice protocol", "multi-agent", "multi_agent", "agent routing", "planner", "coder", "qa", "qc"), "Workflow orchestration, routing, or approval evidence"),
        ("workflow-runtime", ("workflow runtime", "workflow-runtime", "runtime engine", "session", "checkpoint", "token", "provider", "state", "lock", "daemon", "runtime bus", "aiwf cli", "workspace"), "Runtime, session, checkpoint, provider, or state evidence"),
        ("project-memory", ("project memory", "project-memory", "obsidian", "rag", "knowledge runtime", "memory-first", "memory first", "context summary"), "Memory, RAG, Obsidian, or knowledge-runtime evidence"),
        ("release-public-export", ("public_export", "public export", "release", "changelog", "version", "install", "upgrade", "rollback", "package", "publish"), "Release, export, changelog, or packaging evidence"),
        ("documentation-governance", ("documentation", "docs/", "blueprint-governance", "program-governance", "implementation-governance", "bp-contract", "bp-gov", "template", "style guide", "compliance"), "Documentation governance, templates, or compliance evidence"),
        ("cloud-local-hybrid", ("cloud-local", "cloud local", "cloud_", "fleet", "control plane", "distributed scheduler", "multi-region", "disaster recovery", "api gateway"), "Cloud-local hybrid, fleet, or control-plane evidence"),
        ("vir", ("vir_", "vir ", "visual intelligence", "vision engine", "hearing engine", "touch engine", "digital twin", "evidence domain", "visual-to-source"), "VIR visual intelligence runtime evidence"),
        ("framework-architecture", ("architecture", "adr", "policy", "compatibility", "contract", "framework", "aiwf v2", "program "), "Framework architecture, ADR, policy, or contract evidence"),
    ]
    for family, needles, evidence in rules:
        if contains(hint, needles):
            return family, 0.95, evidence
    return "framework-architecture", 0.80, "Low-confidence fallback; manual review recommended"


def classify_stage(path: Path) -> tuple[str, float, str]:
    parts = path.parts
    top = parts[1] if len(parts) > 1 else ""
    name = path.name.lower()
    if top == "brainstorming":
        return "brainstorming", 0.99, "Source directory is docs/brainstorming"
    if top in {"plans", "planning"}:
        return "plans", 0.99, "Source directory is a planning stage"
    if top in {"blueprints", "designs", "architecture"}:
        if "review" in name:
            return "reviews", 0.95, "Blueprint/design source with review filename"
        if any(word in name for word in ("report", "audit", "certification", "readiness")):
            return "reports", 0.95, "Blueprint/design source with report filename"
        if "plan" in name and "blueprint" not in name:
            return "plans", 0.95, "Blueprint/design source with planning filename"
        return "blueprints", 0.99, "Source directory is blueprint/design/architecture"
    mapping = {
        "issues": "issues",
        "quick": "quick",
        "debug": "debug",
        "verification": "verification",
        "reports": "reports",
        "audit": "reports",
        "reviews": "reviews",
        "architecture-reviews": "architecture-reviews",
        "adr": "adr",
        "release": "releases",
        "releases": "releases",
        "templates": "templates",
        "prompts": "prompts",
        "migration": "migration",
        "archive": "archive",
    }
    if top in mapping:
        return mapping[top], 0.99, f"Source directory maps to {mapping[top]}"
    if top in {"blueprint-governance", "program-governance", "implementation-governance"}:
        return "governance", 0.99, "Source directory is governance"
    if top in {"documentation", "guides", "runtime", "platform"}:
        return "docs", 0.95, "Source directory is general documentation"
    if "roadmap" in name:
        return "roadmaps", 0.98, "Filename contains roadmap"
    if "report" in name:
        return "reports", 0.95, "Filename contains report"
    return "docs", 0.90, "Default general documentation stage"


def parse_overrides(values: list[str]) -> dict[str, tuple[str, str]]:
    overrides: dict[str, tuple[str, str]] = {}
    for value in values:
        if "=" not in value or ":" not in value:
            raise SystemExit(f"Invalid override: {value}. Expected path=family:stage")
        path, target = value.split("=", 1)
        family, stage = target.split(":", 1)
        overrides[path] = (family, stage)
    return overrides


def unique_target(path: Path, family: str, stage: str) -> Path:
    target = FEATURES / family / stage / path.name
    if not target.exists():
        return target
    stem, suffix = path.stem, path.suffix
    index = 2
    while True:
        candidate = FEATURES / family / stage / f"{stem}_{index}{suffix}"
        if not candidate.exists():
            return candidate
        index += 1


def backup(path: Path, timestamp: str) -> Path:
    target = BACKUP_ROOT / timestamp / path
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, target)
    return target


def iter_legacy_files() -> list[Path]:
    if not DOCS.exists():
        return []
    return sorted(
        p for p in DOCS.rglob("*")
        if p.is_file() and len(p.parts) >= 2 and p.parts[:2] != ("docs", "features")
    )


def inventory(overrides: dict[str, tuple[str, str]], timestamp: str) -> list[Record]:
    status = git_status_map()
    tracked = tracked_files()
    records: list[Record] = []
    for path in iter_legacy_files():
        rel = path.as_posix()
        git_status = status.get(rel, "CLEAN" if rel in tracked else "UNTRACKED")
        if git_status != "CLEAN":
            records.append(Record(rel, git_status, "SKIP_WIP", None, None, None, None, 1.0, "Modified, staged, or untracked file is protected"))
            continue
        if path.name in JUNK_NAMES:
            records.append(Record(rel, git_status, "DELETE_JUNK", None, (BACKUP_ROOT / timestamp / path).as_posix(), None, None, 1.0, "Legacy junk placeholder"))
            continue
        if rel in overrides:
            family, stage = overrides[rel]
            confidence = 1.0
            evidence = "Explicit operator override"
        else:
            family, family_conf, family_evidence = classify_family(path)
            stage, stage_conf, stage_evidence = classify_stage(path)
            confidence = min(family_conf, stage_conf)
            evidence = f"{family_evidence}; {stage_evidence}"
        if confidence < 0.90:
            records.append(Record(rel, git_status, "NEEDS_REVIEW", None, None, family, stage, confidence, evidence))
            continue
        target = unique_target(path, family, stage)
        records.append(Record(rel, git_status, "MOVE", target.as_posix(), (BACKUP_ROOT / timestamp / path).as_posix(), family, stage, confidence, evidence))
    return records


def apply_records(records: list[Record], timestamp: str) -> list[str]:
    removed_dirs: list[str] = []
    for record in records:
        path = Path(record.source_path)
        if record.action == "MOVE" and record.target_path:
            backup(path, timestamp)
            target = Path(record.target_path)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(path.as_posix(), target.as_posix())
            readme = FEATURES / str(record.feature_family) / "README.md"
            if not readme.exists():
                readme.write_text(f"# {record.feature_family}\n\nSemantic documentation index for `{record.feature_family}`.\n", encoding="utf-8")
        elif record.action == "DELETE_JUNK":
            backup(path, timestamp)
            path.unlink()
    for directory in sorted((p for p in DOCS.rglob("*") if p.is_dir()), key=lambda p: len(p.parts), reverse=True):
        if directory == FEATURES or directory.parts[:2] == ("docs", "features"):
            continue
        try:
            if not any(directory.iterdir()):
                removed_dirs.append(directory.as_posix())
                directory.rmdir()
        except OSError:
            pass
    return removed_dirs


def validate(records: list[Record] | None = None) -> tuple[bool, list[str]]:
    failures: list[str] = []
    status = git_status_map()
    tracked = tracked_files()
    for path in iter_legacy_files():
        rel = path.as_posix()
        if rel in tracked and status.get(rel, "CLEAN") == "CLEAN":
            failures.append(f"Clean tracked legacy file remains: {rel}")
    for directory in FEATURES.rglob("*") if FEATURES.exists() else []:
        if directory.is_dir() and FORBIDDEN_DIR_RE.match(directory.name):
            failures.append(f"Forbidden ID-derived directory: {directory.as_posix()}")
    if records:
        for record in records:
            if record.action in {"MOVE", "DELETE_JUNK"} and record.backup_path and not Path(record.backup_path).exists():
                failures.append(f"Missing backup: {record.backup_path}")
            if record.action == "MOVE" and record.target_path and not Path(record.target_path).exists():
                failures.append(f"Missing moved target: {record.target_path}")
    return not failures, failures


def write_reports(records: list[Record], removed_dirs: list[str], timestamp: str, mode: str, failures: list[str]) -> None:
    REPORT_ROOT.mkdir(parents=True, exist_ok=True)
    inv_path = REPORT_ROOT / f"{timestamp}_inventory.json"
    plan_path = REPORT_ROOT / f"{timestamp}_plan.json"
    report_path = REPORT_ROOT / f"{timestamp}_report.md"
    review_path = REPORT_ROOT / f"{timestamp}_review.md"
    payload = [asdict(record) for record in records]
    inv_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    plan_path.write_text(json.dumps([asdict(r) for r in records if r.action in {"MOVE", "DELETE_JUNK"}], indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    counts = Counter(record.action for record in records)
    families = Counter(record.feature_family for record in records if record.feature_family)
    status = "PASS" if not failures else "FAIL"
    report = [
        "# Semantic Docs Cleanup Report",
        "",
        f"- Mode: {mode}",
        f"- Result: {status}",
        f"- Move candidates/applied: {counts.get('MOVE', 0)}",
        f"- Junk delete candidates/applied: {counts.get('DELETE_JUNK', 0)}",
        f"- WIP skipped: {counts.get('SKIP_WIP', 0)}",
        f"- Needs review: {counts.get('NEEDS_REVIEW', 0)}",
        f"- Empty directories removed: {len(removed_dirs)}",
        "",
        "## By Feature Family",
        "",
    ]
    for family, count in sorted(families.items()):
        report.append(f"- {family}: {count}")
    report.extend(["", "## Remaining WIP / Needs Review", ""])
    for record in records:
        if record.action in {"SKIP_WIP", "NEEDS_REVIEW"}:
            report.append(f"- {record.action}: {record.source_path} ({record.evidence})")
    if failures:
        report.extend(["", "## Failures", ""])
        report.extend(f"- {failure}" for failure in failures)
    report_path.write_text("\n".join(report) + "\n", encoding="utf-8")

    review = [
        "# Semantic Docs Cleanup Review",
        "",
        f"- Result: {status}",
        f"- Clean tracked legacy files outside docs/features: {'0' if not any(f.startswith('Clean tracked legacy file remains:') for f in failures) else 'FAIL'}",
        f"- Forbidden ID-derived directories: {'0' if not any(f.startswith('Forbidden ID-derived directory:') for f in failures) else 'FAIL'}",
        f"- Backup and target verification: {'PASS' if not any('Missing backup' in f or 'Missing moved target' in f for f in failures) else 'FAIL'}",
        "- Path/tone compliance: PASS",
        "",
    ]
    text_to_scan = "\n".join(report + review)
    if ABSOLUTE_RE.search(text_to_scan) or TONE_RE.search(text_to_scan):
        review[-2] = "- Path/tone compliance: FAIL"
    review_path.write_text("\n".join(review), encoding="utf-8")
    print(json.dumps({"result": status, "mode": mode, "counts": counts, "report": report_path.as_posix(), "review": review_path.as_posix()}, indent=2, default=dict))


def main() -> int:
    parser = argparse.ArgumentParser(description="Clean docs into semantic feature-family folders.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--dry-run", action="store_true", help="Generate inventory and plan without changing docs.")
    group.add_argument("--apply", action="store_true", help="Apply safe migration and cleanup.")
    group.add_argument("--validate-only", action="store_true", help="Validate current docs state only.")
    parser.add_argument("--override", action="append", default=[], help="Override classification: docs/path.md=family:stage")
    args = parser.parse_args()

    os.chdir(Path.cwd())
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    overrides = parse_overrides(args.override)

    if args.validate_only:
        ok, failures = validate(None)
        write_reports([], [], timestamp, "validate-only", failures)
        return 0 if ok else 1

    records = inventory(overrides, timestamp)
    removed_dirs: list[str] = []
    if args.apply:
        removed_dirs = apply_records(records, timestamp)
        ok, failures = validate(records)
        mode = "apply"
    else:
        ok = True
        failures = []
        mode = "dry-run"
    write_reports(records, removed_dirs, timestamp, mode, failures)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
