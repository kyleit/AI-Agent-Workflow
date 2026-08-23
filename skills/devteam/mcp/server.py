"""DevTeam MCP server — typed tool wrapper over the engine (delivery layer).

Exposes six tools to any MCP-capable agent (Claude Code, Codex CLI, Antigravity):
  init, seat_enter, seat_leave, mailbox_send, mailbox_poll, board.

No business logic lives here — every tool builds the composition root and calls a
use case, returning the engine's structured result. Requires the optional ``mcp``
package (``pip install mcp``); the engine itself has no third-party dependency.
"""

from __future__ import annotations

import functools
import os
import sys
from dataclasses import asdict


def _bootstrap_engine_path() -> str:
    """Locate the `devteam` engine package and put it on sys.path."""
    candidates = []
    env = os.environ.get("AIWF_DEVTEAM_ENGINE")
    if env:
        candidates.append(env)
    home = os.environ.get("AIWF_HOME") or os.path.join(os.path.expanduser("~"), ".aiwf")
    candidates.append(os.path.join(home, "devteam", "engine"))
    here = os.path.dirname(os.path.abspath(__file__))          # .../skills/devteam/mcp
    candidates.append(os.path.join(os.path.dirname(here), "scripts"))  # repo source
    for c in candidates:
        if c and os.path.isdir(os.path.join(c, "devteam")):
            if c not in sys.path:
                sys.path.insert(0, c)
            return c
    raise SystemExit("[devteam-mcp] engine package not found; run the installer")


_bootstrap_engine_path()

from devteam.application.dto import SendMailRequest  # noqa: E402
from devteam.domain.errors import DevTeamError  # noqa: E402
from devteam.interface.composition import build_container  # noqa: E402

try:  # mcp 1.x
    from mcp.server.fastmcp import FastMCP as _ServerClass
except ImportError:
    try:  # mcp 2.x
        from mcp.server.mcpserver import MCPServer as _ServerClass
    except ImportError as exc:  # pragma: no cover - optional dependency
        raise SystemExit(
            "[devteam-mcp] the 'mcp' package is required to run the server: pip install mcp"
        ) from exc

mcp = _ServerClass("devteam")


def _guard(fn):
    @functools.wraps(fn)  # preserve signature so the SDK derives the tool schema
    def wrapped(*args, **kwargs):
        try:
            return {"ok": True, **fn(*args, **kwargs)}
        except DevTeamError as e:
            return e.to_json()
        except Exception as e:  # noqa: BLE001
            return {"ok": False, "error": {"code": "INTERNAL", "message": str(e), "details": {}}}
    return wrapped


@mcp.tool()
@_guard
def init(apply: bool = False, root: str | None = None) -> dict:
    """Detect the roster / scaffold the team (preview unless apply=True)."""
    return {"result": asdict(build_container(root).init.execute(apply=apply))}


@mcp.tool()
@_guard
def seat_enter(slug: str, session: str = "", root: str | None = None) -> dict:
    """Take a seat (resume-aware): charter + NEXT STEP NOW + new mail + git status."""
    return {"result": asdict(build_container(root).enter.execute(slug, session))}


@mcp.tool()
@_guard
def seat_leave(slug: str, fields: dict | None = None, session: str = "", root: str | None = None) -> dict:
    """Write the living seat-state handoff so any session can resume."""
    path = build_container(root).leave.execute(slug, fields or {}, session)
    return {"seat_state": path}


@mcp.tool()
@_guard
def mailbox_send(to: str, type: str, payload: dict | None = None, frm: str = "seat-leader", root: str | None = None) -> dict:
    """Append a validated envelope to a seat inbox."""
    env = build_container(root).send.execute(SendMailRequest(to, type, payload or {}, frm))
    return {"sent": env.to_dict()}


@mcp.tool()
@_guard
def mailbox_poll(slug: str, advance: bool = True, root: str | None = None) -> dict:
    """Return unread envelopes and advance the cursor (exactly-once)."""
    got = build_container(root).poll.execute(slug, advance=advance)
    return {"messages": [e.to_dict() for e in got]}


@mcp.tool()
@_guard
def board(root: str | None = None) -> dict:
    """Render the seat status board (incl. active locks)."""
    return {"board": build_container(root).board.execute()}


@mcp.tool()
@_guard
def lock_acquire(path: str, seat: str, note: str = "", ttl: int = 0, force: bool = False, root: str | None = None) -> dict:
    """Acquire an exclusive cross-seat lock on a resource path (raises on conflict)."""
    return build_container(root).acquire_lock.execute(path, seat, note, ttl, force)


@mcp.tool()
@_guard
def lock_release(path: str, seat: str, force: bool = False, root: str | None = None) -> dict:
    """Release a lock held by the seat (force to steal-release)."""
    return build_container(root).release_lock.execute(path, seat, force)


@mcp.tool()
@_guard
def lock_list(root: str | None = None) -> dict:
    """List active locks."""
    return {"locks": build_container(root).list_locks.execute()}


@mcp.tool()
@_guard
def lock_check(path: str, root: str | None = None) -> dict:
    """Check whether a path is currently locked and by whom."""
    return build_container(root).list_locks.check(path)


if __name__ == "__main__":
    mcp.run()
