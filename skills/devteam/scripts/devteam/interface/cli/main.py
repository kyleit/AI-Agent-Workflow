"""CLI dispatch — argparse -> composition root -> JSON stdout."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict

from ...application.dto import SendMailRequest
from ...domain.errors import DevTeamError, ErrorCode
from ..composition import build_container
from .json_output import err, ok


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="devteam", description="DevTeam multi-session orchestration")
    ap.add_argument("--root", default=None, help="repo root (default: git toplevel)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_init = sub.add_parser("init", help="detect roster / scaffold team")
    p_init.add_argument("--apply", action="store_true", help="write files (default: preview only)")

    sub.add_parser("board", help="render seat status board")

    p_seat = sub.add_parser("seat", help="seat lifecycle")
    seat_sub = p_seat.add_subparsers(dest="sub", required=True)
    p_enter = seat_sub.add_parser("enter", help="take a seat (resume-aware)")
    p_enter.add_argument("slug")
    p_enter.add_argument("--session", default="")
    p_leave = seat_sub.add_parser("leave", help="write seat-state handoff")
    p_leave.add_argument("slug")
    p_leave.add_argument("--session", default="")
    p_leave.add_argument("--field", action="append", default=[], metavar="k=v")

    p_mail = sub.add_parser("mailbox", help="mailbox send/poll")
    mail_sub = p_mail.add_subparsers(dest="sub", required=True)
    p_send = mail_sub.add_parser("send")
    p_send.add_argument("--to", required=True)
    p_send.add_argument("--type", required=True)
    p_send.add_argument("--json", required=True, dest="payload")
    p_send.add_argument("--from", dest="frm", default="seat-leader")
    p_poll = mail_sub.add_parser("poll")
    p_poll.add_argument("slug")
    p_poll.add_argument("--no-advance", action="store_true")

    p_setup = sub.add_parser("setup", help="one-shot: install engine + adapters (+ mcp, +configs)")
    p_setup.add_argument("--write-configs", action="store_true", help="register MCP in Claude/Codex/Antigravity (§15 owner approval)")
    p_setup.add_argument("--mcp", action="store_true", help="also pip install the mcp package")
    sub.add_parser("doctor", help="health-check the install + wiring")

    p_lock = sub.add_parser("lock", help="cross-seat resource locks")
    lock_sub = p_lock.add_subparsers(dest="sub", required=True)
    p_acq = lock_sub.add_parser("acquire")
    p_acq.add_argument("path")
    p_acq.add_argument("--seat", required=True)
    p_acq.add_argument("--note", default="")
    p_acq.add_argument("--ttl", type=int, default=0, help="seconds until auto-expiry (0 = none)")
    p_acq.add_argument("--force", action="store_true")
    p_rel = lock_sub.add_parser("release")
    p_rel.add_argument("path")
    p_rel.add_argument("--seat", required=True)
    p_rel.add_argument("--force", action="store_true")
    lock_sub.add_parser("list")
    p_chk = lock_sub.add_parser("check")
    p_chk.add_argument("path")
    return ap


def main(argv: list[str]) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.cmd == "setup":
            from ...infrastructure.install.setup import run_setup
            return ok({"setup": run_setup(args.root, args.write_configs, args.mcp)})
        if args.cmd == "doctor":
            from ...infrastructure.install.doctor import run_doctor
            return ok({"doctor": run_doctor(args.root)})
        c = build_container(args.root)
        if args.cmd == "init":
            return ok({"result": asdict(c.init.execute(apply=args.apply))})
        if args.cmd == "board":
            return ok({"board": c.board.execute()})
        if args.cmd == "seat" and args.sub == "enter":
            return ok({"result": asdict(c.enter.execute(args.slug, args.session))})
        if args.cmd == "seat" and args.sub == "leave":
            fields = _parse_fields(args.field)
            path = c.leave.execute(args.slug, fields, args.session)
            return ok({"seat_state": path})
        if args.cmd == "mailbox" and args.sub == "send":
            payload = json.loads(args.payload)
            env = c.send.execute(SendMailRequest(args.to, args.type, payload, args.frm))
            return ok({"sent": env.to_dict()})
        if args.cmd == "mailbox" and args.sub == "poll":
            got = c.poll.execute(args.slug, advance=not args.no_advance)
            return ok({"messages": [e.to_dict() for e in got]})
        if args.cmd == "lock" and args.sub == "acquire":
            return ok(c.acquire_lock.execute(args.path, args.seat, args.note, args.ttl, args.force))
        if args.cmd == "lock" and args.sub == "release":
            return ok(c.release_lock.execute(args.path, args.seat, args.force))
        if args.cmd == "lock" and args.sub == "list":
            return ok({"locks": c.list_locks.execute()})
        if args.cmd == "lock" and args.sub == "check":
            return ok(c.list_locks.check(args.path))
    except DevTeamError as e:
        return err(e)
    except json.JSONDecodeError as e:
        return err(DevTeamError(ErrorCode.SCHEMA_INVALID, f"--json is not valid JSON: {e}"))
    except Exception as e:  # noqa: BLE001 — surfaced as JSON INTERNAL body
        return err(e)
    return err(DevTeamError(ErrorCode.INTERNAL, "unhandled command"))


def _parse_fields(pairs: list[str]) -> dict:
    out: dict[str, str] = {}
    for kv in pairs:
        if "=" not in kv:
            raise DevTeamError(ErrorCode.SCHEMA_INVALID, f"--field must be k=v, got {kv!r}")
        k, v = kv.split("=", 1)
        out[k.strip()] = v
    return out
