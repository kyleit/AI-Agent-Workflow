"""AIWF install scope helper (SPIKE prototype).

Cross-platform, dependency-free. Both install.sh and install.ps1 shell into this
to keep scope-detection and managed-block logic identical (single source).

Subcommands:
    detect   --assume-global? --full?         -> prints "minimal" | "full" (project mode)
    marker-write --version V --home H --agents a,b,c
    marker-remove
    render-block --mode full|stub --home H
    apply-block  --file F --mode full|stub --home H

Marker: ~/.agents/aiwf-global.json (schema aiwf.global-install/1).
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import cast

BEGIN = "<!-- AIWF:RULES:BEGIN -->"
END = "<!-- AIWF:RULES:END -->"
MARKER_SCHEMA = "aiwf.global-install/1"


def home_agents() -> Path:
    return Path.home() / ".agents"


def marker_path() -> Path:
    return home_agents() / "aiwf-global.json"


def _full_block() -> str:
    return (
        f"{BEGIN}\n"
        "# AI Engineering Workflow Agents\n\n"
        "Every AI agent working inside this project **MUST** follow the AI Workflow Framework.\n\n"
        "Load and follow all policies in `AI_RULES.md` (the single source of truth), and use the\n"
        "workflow resources under `.agents/skills/`, `.agents/runtime/`, `.agents/templates/`.\n"
        "Never bypass approval gates or other framework policies.\n"
        f"{END}"
    )


def _stub_block(home: str) -> str:
    home_disp = home or "~/.agents"
    return (
        f"{BEGIN}\n"
        "# AI Engineering Workflow Agents (project stub)\n\n"
        f"AIWF is installed GLOBALLY on this machine ({home_disp}; marker: "
        f"{home_disp}/aiwf-global.json).\n"
        "To avoid duplicating rules into every prompt, this project ships only project-local\n"
        "state, config, and hooks. Follow the GLOBAL `AI_RULES.md` and skills; this project adds\n"
        "only: `.agents/state`, `.agents/config` (agent-registry), project memory, and the\n"
        "auto-route + source-write-gate hooks.\n"
        f"{END}"
    )


def render_block(mode: str, home: str) -> str:
    return _stub_block(home) if mode == "stub" else _full_block()


def apply_block(file_path: Path, block: str) -> None:
    """Idempotently install `block` between the markers (create/replace/normalize)."""
    if not file_path.exists():
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(block + "\n", encoding="utf-8", newline="")
        return
    content = file_path.read_text(encoding="utf-8")
    has_begin = BEGIN in content
    has_end = END in content
    if has_begin and has_end:
        # Use a replacement FUNCTION, not a string: `block` may contain backslashes
        # (e.g. a Windows home path like C:\Users\...\.agents) which re.sub would
        # otherwise interpret as escape sequences ("bad escape \U").
        new_content = re.sub(
            re.escape(BEGIN) + r".*?" + re.escape(END),
            lambda _m: block,
            content,
            flags=re.DOTALL,
        )
    elif has_begin:
        # Orphaned BEGIN (no END): the block region is broken; drop from BEGIN to EOF.
        clean = content[: content.index(BEGIN)].strip()
        new_content = (clean + "\n\n" + block) if clean else block
    elif has_end:
        # Orphaned END (no BEGIN): drop everything up to and including END.
        clean = content[content.index(END) + len(END):].strip()
        new_content = (clean + "\n\n" + block) if clean else block
    else:
        trimmed = content.strip()
        new_content = block if not trimmed else trimmed + "\n\n" + block
    file_path.write_text(new_content, encoding="utf-8", newline="")


def remove_block(file_path: Path) -> bool:
    """Remove the managed AIWF block from a file (used by global uninstall).

    Returns True if the file was modified. Leaves surrounding user content intact.
    """
    if not file_path.exists():
        return False
    content = file_path.read_text(encoding="utf-8")
    if BEGIN not in content and END not in content:
        return False
    if BEGIN in content and END in content:
        new_content = re.sub(
            re.escape(BEGIN) + r".*?" + re.escape(END), "", content, flags=re.DOTALL
        )
    elif BEGIN in content:
        new_content = content[: content.index(BEGIN)]
    else:
        new_content = content[content.index(END) + len(END):]
    file_path.write_text(new_content.strip() + "\n", encoding="utf-8", newline="")
    return True


def detect(assume_global: bool, full: bool) -> str:
    if full:
        return "full"
    if assume_global or marker_path().exists():
        return "minimal"
    return "full"


def marker_write(version: str, home: str, agents: list[str]) -> None:
    data = {
        "schema": MARKER_SCHEMA,
        "version": version,
        "installed_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "agents": agents,
        "home_root": home,
        "provides": ["rules", "skills", "policies", "profiles", "contracts", "templates"],
    }
    p = marker_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8", newline="")


def marker_remove() -> None:
    p = marker_path()
    if p.exists():
        p.unlink()


# Shared-payload dirs under a project's .agents that a global install supersedes.
_SHARED_DIRS = ("agents", "runtime", "contracts", "policies", "profiles")
# Shared files (relative to project root) a global install supersedes.
_SHARED_FILES_ROOT = ("AI_RULES.md",)
_SHARED_FILES_AGENTS = ("AI_RULES.md", "SKILLS.md")


def _rmtree(path: Path) -> bool:
    if not path.exists():
        return False
    import shutil

    if path.is_dir():
        shutil.rmtree(path, ignore_errors=True)
    else:
        path.unlink()
    return True


def slim_project(root: Path, skill_dir: str, template_dir: str) -> list[str]:
    """Reclaim a full project install into minimal: remove the shared payload that
    the global install provides, and downgrade the managed block to the stub.

    Returns the list of removed paths (project-relative) for logging.
    """
    removed: list[str] = []
    agents_dir = root / ".agents"

    for d in (skill_dir, template_dir, *_SHARED_DIRS):
        if _rmtree(agents_dir / d):
            removed.append(f".agents/{d}")
    for f in _SHARED_FILES_AGENTS:
        if _rmtree(agents_dir / f):
            removed.append(f".agents/{f}")
    for f in _SHARED_FILES_ROOT:
        if _rmtree(root / f):
            removed.append(f)

    stub = render_block("stub", str(home_agents()))
    apply_block(root / "AGENTS.md", stub)
    removed.append("AGENTS.md(block->stub)")
    if agents_dir.exists():
        apply_block(agents_dir / "AGENTS.md", stub)
        removed.append(".agents/AGENTS.md(block->stub)")
    return removed


def _get_str(args: argparse.Namespace, name: str) -> str:
    """Typed boundary over argparse.Namespace (isolates Any to one place)."""
    value = cast(object, getattr(args, name, None))
    return value if isinstance(value, str) else ""


def _get_bool(args: argparse.Namespace, name: str) -> bool:
    return cast(object, getattr(args, name, None)) is True


def main() -> int:
    parser = argparse.ArgumentParser(prog="aiwf_scope")
    sub = parser.add_subparsers(dest="cmd", required=True)

    d = sub.add_parser("detect")
    _ = d.add_argument("--assume-global", action="store_true")
    _ = d.add_argument("--full", action="store_true")

    mw = sub.add_parser("marker-write")
    _ = mw.add_argument("--version", required=True)
    _ = mw.add_argument("--home", required=True)
    _ = mw.add_argument("--agents", default="claude,codex,antigravity")

    _ = sub.add_parser("marker-remove")

    rb = sub.add_parser("render-block")
    _ = rb.add_argument("--mode", choices=["full", "stub"], required=True)
    _ = rb.add_argument("--home", default="")

    ab = sub.add_parser("apply-block")
    _ = ab.add_argument("--file", required=True)
    _ = ab.add_argument("--mode", choices=["full", "stub"], required=True)
    _ = ab.add_argument("--home", default="")

    sp = sub.add_parser("slim-project")
    _ = sp.add_argument("--root", required=True)
    _ = sp.add_argument("--skill-dir", default="skills")
    _ = sp.add_argument("--template-dir", default="templates")

    rmb = sub.add_parser("remove-block")
    _ = rmb.add_argument("--file", required=True)

    args = parser.parse_args()
    cmd = _get_str(args, "cmd")
    if cmd == "detect":
        print(detect(_get_bool(args, "assume_global"), _get_bool(args, "full")))
        return 0
    if cmd == "marker-write":
        agents = [a.strip() for a in _get_str(args, "agents").split(",") if a.strip()]
        marker_write(_get_str(args, "version"), _get_str(args, "home"), agents)
        return 0
    if cmd == "marker-remove":
        marker_remove()
        return 0
    if cmd == "render-block":
        print(render_block(_get_str(args, "mode"), _get_str(args, "home")))
        return 0
    if cmd == "apply-block":
        block = render_block(_get_str(args, "mode"), _get_str(args, "home"))
        apply_block(Path(_get_str(args, "file")), block)
        return 0
    if cmd == "remove-block":
        _ = remove_block(Path(_get_str(args, "file")))
        return 0
    if cmd == "slim-project":
        removed = slim_project(
            Path(_get_str(args, "root")),
            _get_str(args, "skill_dir"),
            _get_str(args, "template_dir"),
        )
        for item in removed:
            print(item)
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
