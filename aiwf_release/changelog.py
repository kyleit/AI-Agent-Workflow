"""Generate dev (full) and product (filtered) changelogs from git history."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

CC_RE = re.compile(
    r"^(?P<type>[a-zA-Z]+)(?P<scope>\(([^)]*)\))?(?P<bang>!)?:\s*(?P<desc>.+)$"
)

TYPE_TITLES = {
    "feat": "Features",
    "fix": "Bug Fixes",
    "perf": "Performance",
    "refactor": "Refactoring",
    "docs": "Documentation",
    "test": "Tests",
    "build": "Build",
    "ci": "CI",
    "chore": "Chores",
    "style": "Style",
    "other": "Other",
}


def _git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=str(root), capture_output=True, text=True
    ).stdout.strip()


def collect(root: Path, since_tag: str | None) -> list[dict]:
    """Return [{type, scope, desc, hash}] for commits since tag."""
    rng = f"{since_tag}..HEAD" if since_tag else "HEAD"
    out = _git(root, "log", rng, "--no-merges", "--pretty=%h%x1f%s")
    items: list[dict] = []
    for line in out.splitlines():
        if "\x1f" not in line:
            continue
        h, subj = line.split("\x1f", 1)
        m = CC_RE.match(subj.strip())
        if m:
            items.append({
                "type": m.group("type").lower(),
                "scope": (m.group("scope") or "").strip("()"),
                "desc": m.group("desc").strip(),
                "hash": h,
            })
        else:
            items.append({"type": "other", "scope": "", "desc": subj.strip(), "hash": h})
    return items


def _group(items: list[dict], include) -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = {}
    for it in items:
        t = it["type"]
        if include != "all" and t not in include:
            continue
        grouped.setdefault(t if t in TYPE_TITLES else "other", []).append(it)
    return grouped


def render(version: str, date: str, items: list[dict], include) -> str:
    grouped = _group(items, include)
    lines = [f"## v{version} - {date}", ""]
    if not grouped:
        lines += ["_No user-facing changes._", ""]
    for t in TYPE_TITLES:
        if t not in grouped:
            continue
        lines.append(f"### {TYPE_TITLES[t]}")
        for it in grouped[t]:
            scope = f"**{it['scope']}**: " if it["scope"] else ""
            lines.append(f"- {scope}{it['desc']} ({it['hash']})")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def prepend(root: Path, rel_path: str, entry: str, title: str = "# Changelog") -> str:
    """Insert entry below the top-level title (create file if missing)."""
    p = root / rel_path
    p.parent.mkdir(parents=True, exist_ok=True)
    if not p.exists():
        p.write_text(f"{title}\n\n{entry}\n", encoding="utf-8")
        return rel_path
    content = p.read_text(encoding="utf-8")
    lines = content.splitlines()
    insert_at = 0
    for i, ln in enumerate(lines):
        if ln.startswith("# "):
            insert_at = i + 1
            break
    head = "\n".join(lines[:insert_at])
    tail = "\n".join(lines[insert_at:])
    new = f"{head}\n\n{entry}\n{tail}".rstrip() + "\n"
    p.write_text(new, encoding="utf-8")
    return rel_path
