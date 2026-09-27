#!/usr/bin/env python3
"""MsgBus client entrypoint for transport, durable events and agent tasks."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from msgbusws.client import agent_worker as A  # noqa: E402
from msgbusws.client import commands as C  # noqa: E402
from msgbusws.client.config import load_config  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="msgbus_client", description="MsgBus REST, WebSocket, files and durable events")
    parser.add_argument("--host")
    parser.add_argument("--port", type=int)
    parser.add_argument("--token")
    parser.add_argument("--from", dest="sender")
    parser.add_argument("--e2ee-key", dest="e2ee_key")
    parser.add_argument("--capabilities")
    parser.add_argument("--avatar")
    parser.add_argument("--identity")
    parser.add_argument("--soul")
    parser.add_argument("--machine")
    parser.add_argument("--platform")
    parser.add_argument("--project")
    parser.add_argument("--conversation-id")
    parser.add_argument("--role")
    tls = parser.add_mutually_exclusive_group()
    tls.add_argument("--tls", dest="tls", action="store_true")
    tls.add_argument("--no-tls", dest="tls", action="store_false")
    parser.set_defaults(tls=None)
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("init", help="save project settings to .agents/msgbus.json")
    sub.add_parser("health")
    send = sub.add_parser("send")
    send.add_argument("text")
    send.add_argument("--to")
    recv = sub.add_parser("recv")
    recv.add_argument("--since", type=int, default=0)
    sub.add_parser("list")
    upload = sub.add_parser("upload")
    upload.add_argument("path")
    upload.add_argument("--to")
    download = sub.add_parser("download")
    download.add_argument("name")
    download.add_argument("--out")
    listen = sub.add_parser("listen")
    listen.add_argument("--since", type=int, default=0)
    join = sub.add_parser("join", help="alias for listen")
    join.add_argument("--since", type=int, default=0)
    ws_send = sub.add_parser("ws-send")
    ws_send.add_argument("text")
    ws_send.add_argument("--to")

    for command in ("daemon", "agent-run"):
        run = sub.add_parser(command, help="run one persistent conversation listener")
        run.add_argument("--since", type=int, default=0)
        run.add_argument("--heartbeat", type=float, default=15.0)
        run.add_argument("--state-dir")
        run.add_argument("--silent", action="store_true")
    pop = sub.add_parser("pop-event", help="claim one durable local event without opening a socket")
    pop.add_argument("--wait", type=float, default=0.0)
    pop.add_argument("--lease", type=float, default=60.0)
    pop.add_argument("--state-dir")
    for command, help_text in (("ack-event", "acknowledge successful native delivery"),
                               ("release-event", "release a failed native delivery for retry")):
        event = sub.add_parser(command, help=help_text)
        event.add_argument("receipt")
        event.add_argument("--state-dir")
    next_task = sub.add_parser("agent-next")
    next_task.add_argument("--wait", type=float, default=0.0)
    next_task.add_argument("--state-dir")
    status = sub.add_parser("agent-status")
    status.add_argument("--state-dir")
    task = sub.add_parser("task-update")
    task.add_argument("task_id")
    task.add_argument("status", choices=["running", "completed", "failed", "cancelled"])
    task.add_argument("--output", default="")
    task.add_argument("--state-dir")
    return parser


_DISPATCH = {
    "init": C.cmd_init, "health": C.cmd_health, "send": C.cmd_send,
    "recv": C.cmd_recv, "list": C.cmd_list, "upload": C.cmd_upload,
    "download": C.cmd_download, "listen": C.cmd_listen, "join": C.cmd_listen,
    "ws-send": C.cmd_ws_send, "daemon": A.cmd_agent_run,
    "agent-run": A.cmd_agent_run, "pop-event": A.cmd_pop_event,
    "ack-event": A.cmd_ack_event, "release-event": A.cmd_release_event,
    "agent-next": A.cmd_agent_next, "agent-status": A.cmd_agent_status,
    "task-update": A.cmd_task_update,
}


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    _DISPATCH[args.command](load_config(args), args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
