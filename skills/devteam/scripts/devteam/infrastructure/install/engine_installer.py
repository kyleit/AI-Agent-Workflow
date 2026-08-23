"""EngineInstaller — copy the engine package to the global machine home.

Global home: $AIWF_HOME/devteam or ~/.aiwf/devteam. Idempotent; safe to re-run.
"""

from __future__ import annotations

import os
import shutil
import sysconfig

from ... import __version__


def global_home() -> str:
    base = os.environ.get("AIWF_HOME") or os.path.join(os.path.expanduser("~"), ".aiwf")
    return os.path.join(base, "devteam")


def _engine_source() -> str:
    # this file: .../devteam/infrastructure/install/engine_installer.py
    # engine package root = .../devteam
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def install_engine(force: bool = False) -> dict:
    src = _engine_source()  # the `devteam` package directory
    dest_root = global_home()
    engine_dir = os.path.join(dest_root, "engine")           # goes on sys.path
    dest_pkg = os.path.join(engine_dir, "devteam")           # preserves package name
    if os.path.exists(dest_pkg):
        if not force:
            return {"installed": False, "reason": "already present", "path": dest_pkg}
        shutil.rmtree(dest_pkg)
    shutil.copytree(
        src,
        dest_pkg,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "tests"),
    )
    os.makedirs(dest_root, exist_ok=True)
    with open(os.path.join(dest_root, "VERSION"), "w", encoding="utf-8") as f:
        f.write(__version__ + "\n")
    mcp = _install_mcp_server(dest_root)
    pth = _write_path_file(engine_dir)
    return {
        "installed": True,
        "path": dest_pkg,
        "engine_path": engine_dir,
        "mcp_server": mcp,
        "pth_file": pth,
        "version": __version__,
    }


def _write_path_file(engine_dir: str) -> str | None:
    """Drop a .pth in site-packages so `python -m devteam` works anywhere.

    Reversible: delete the file to undo. Best-effort — returns None if the
    site-packages dir is not writable.
    """
    try:
        site_dir = sysconfig.get_path("purelib")
        if not site_dir or not os.path.isdir(site_dir):
            return None
        pth = os.path.join(site_dir, "devteam-engine.pth")
        with open(pth, "w", encoding="utf-8") as f:
            f.write(engine_dir + "\n")
        return pth
    except OSError:
        return None


def _install_mcp_server(dest_root: str) -> str:
    """Copy the MCP delivery (server.py + README) next to the engine."""
    # engine source .../devteam ; its parent .../scripts ; skill root .../skills/devteam
    pkg = _engine_source()
    skill_root = os.path.dirname(os.path.dirname(pkg))  # .../skills/devteam
    src_mcp = os.path.join(skill_root, "mcp")
    dest_mcp = os.path.join(dest_root, "mcp")
    os.makedirs(dest_mcp, exist_ok=True)
    for name in ("server.py", "README.md"):
        src = os.path.join(src_mcp, name)
        if os.path.exists(src):
            shutil.copyfile(src, os.path.join(dest_mcp, name))
    return os.path.join(dest_mcp, "server.py")
