"""Version inference (Conventional Commits) and version-file read/write."""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

from . import config as cfg_mod

SEMVER_RE = re.compile(r"(\d+)\.(\d+)\.(\d+)")
# Conventional commit header: type(scope)!: subject
CC_RE = re.compile(r"^(?P<type>[a-zA-Z]+)(?P<scope>\([^)]*\))?(?P<bang>!)?:", re.IGNORECASE)


def _git(root: Path, *args: str) -> str:
    out = subprocess.run(
        ["git", *args], cwd=str(root), capture_output=True, text=True
    )
    return out.stdout.strip()


def last_tag(root: Path, pattern: str = "v*") -> str | None:
    tag = _git(root, "describe", "--tags", "--match", pattern, "--abbrev=0")
    return tag or None


def commit_subjects(root: Path, since_tag: str | None) -> list[str]:
    rng = f"{since_tag}..HEAD" if since_tag else "HEAD"
    out = _git(root, "log", rng, "--pretty=%s%x00%b%x1e")
    subjects: list[str] = []
    for rec in out.split("\x1e"):
        rec = rec.strip()
        if not rec:
            continue
        subj = rec.split("\x00", 1)[0].strip()
        body = rec.split("\x00", 1)[1] if "\x00" in rec else ""
        subjects.append(subj + ("\n" + body if body.strip() else ""))
    return subjects


def infer_bump(commit_msgs: list[str]) -> str:
    """major if any breaking, minor if any feat, else patch."""
    bump = "patch"
    for msg in commit_msgs:
        header = msg.splitlines()[0] if msg else ""
        m = CC_RE.match(header)
        breaking = "BREAKING CHANGE" in msg or (m and m.group("bang"))
        if breaking:
            return "major"
        if m and m.group("type").lower() == "feat":
            bump = "minor"
    return bump


def bump_semver(version: str, part: str) -> str:
    m = SEMVER_RE.search(version)
    if not m:
        raise ValueError(f"cannot parse semver from '{version}'")
    major, minor, patch = (int(m.group(i)) for i in (1, 2, 3))
    if part == "major":
        major, minor, patch = major + 1, 0, 0
    elif part == "minor":
        minor, patch = minor + 1, 0
    elif part == "patch":
        patch += 1
    else:
        raise ValueError(f"unknown bump part: {part}")
    return f"{major}.{minor}.{patch}"


def _get_json_key(data: dict, dotted: str):
    cur = data
    for key in dotted.split("."):
        cur = cur[key]
    return cur


def _set_json_key(data: dict, dotted: str, value) -> None:
    keys = dotted.split(".")
    cur = data
    for key in keys[:-1]:
        cur = cur[key]
    cur[keys[-1]] = value


def read_version(root: Path, source_of_truth: str) -> str:
    path_str, key = cfg_mod.parse_file_ref(source_of_truth)
    p = root / path_str
    if key:
        data = json.loads(p.read_text(encoding="utf-8-sig"))
        return str(_get_json_key(data, key))
    # plain text version file
    return SEMVER_RE.search(p.read_text(encoding="utf-8")).group(0)


def write_version(root: Path, file_ref: str, new_version: str) -> str:
    """Write new_version into one version file. Returns the file path written."""
    path_str, key = cfg_mod.parse_file_ref(file_ref)
    p = root / path_str
    if key:
        data = json.loads(p.read_text(encoding="utf-8-sig"))
        _set_json_key(data, key, new_version)
        p.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    else:
        p.write_text(new_version + "\n", encoding="utf-8")
    return path_str


def compute_next(root: Path, version_cfg: dict, override_part: str | None) -> dict:
    """Return {current, next, part, source} without writing anything."""
    current = read_version(root, version_cfg["source_of_truth"])
    if override_part:
        part = override_part
    elif version_cfg.get("strategy") == "manual":
        part = "patch"  # manual with no override -> smallest safe default
    else:
        tag = last_tag(root)
        part = infer_bump(commit_subjects(root, tag))
    return {
        "current": current,
        "next": bump_semver(current, part),
        "part": part,
        "source": version_cfg["source_of_truth"],
    }
