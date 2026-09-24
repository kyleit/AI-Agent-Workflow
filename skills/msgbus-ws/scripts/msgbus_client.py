#!/usr/bin/env python3
"""msgbus-ws client entrypoint (thin).

Reads host/port/token/from/e2ee-key from env MSGBUS_HOST/PORT/TOKEN/FROM/E2EE_KEY
(CLI flags override). See the `msgbusws/client/` package for the implementation.

Subcommands include diagnostics plus autonomous Agent worker lifecycle commands.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from msgbusws.client import commands as C  # noqa: E402
from msgbusws.client import agent_worker as A  # noqa: E402
from msgbusws.client.config import load_config  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="msgbus_client", description="msgbus-ws client (REST + WebSocket + tus + E2EE)")
    parser.add_argument("--host")
    parser.add_argument("--port", type=int)
    parser.add_argument("--token")
    parser.add_argument("--from", dest="sender")
    parser.add_argument("--e2ee-key", dest="e2ee_key")
    parser.add_argument("--capabilities", help="comma-separated agent capabilities")
    parser.add_argument("--avatar", help="short avatar mark shown in the AI office")
    parser.add_argument("--identity", help="agent role or professional identity")
    parser.add_argument("--soul", help="agent mission and working style")
    parser.add_argument("--machine", help="machine name shown in the AI office")
    parser.add_argument("--platform", help="operating system shown in the AI office")
    parser.add_argument("--tls", action="store_true", help="use https + wss (domain behind TLS)")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("init", help="save connection profile to ~/.aiwf/msgbus.json")
    sub.add_parser("health")
    p_send = sub.add_parser("send")
    p_send.add_argument("text")
    p_send.add_argument("--to")
    p_recv = sub.add_parser("recv")
    p_recv.add_argument("--since", type=int, default=0)
    sub.add_parser("list")
    p_up = sub.add_parser("upload")
    p_up.add_argument("path")
    p_up.add_argument("--to")
    p_down = sub.add_parser("download")
    p_down.add_argument("name")
    p_down.add_argument("--out")
    p_listen = sub.add_parser("listen")
    p_listen.add_argument("--since", type=int, default=0)
    p_join = sub.add_parser("join", help="alias for listen (uses saved profile)")
    p_join.add_argument("--since", type=int, default=0)
    p_ws = sub.add_parser("ws-send")
    p_ws.add_argument("text")
    p_ws.add_argument("--to")
    p_run = sub.add_parser("agent-run", help="run the durable autonomous Agent listener")
    p_run.add_argument("--since", type=int, default=0)
    p_run.add_argument("--heartbeat", type=float, default=15.0)
    p_run.add_argument("--state-dir")
    p_next = sub.add_parser("agent-next", help="claim the next queued assignment")
    p_next.add_argument("--wait", type=float, default=0.0)
    p_next.add_argument("--state-dir")
    p_status = sub.add_parser("agent-status", help="print local worker state")
    p_status.add_argument("--state-dir")
    p_task = sub.add_parser("task-update", help="report task progress to the coordinator")
    p_task.add_argument("task_id")
    p_task.add_argument("status", choices=["running", "completed", "failed", "cancelled"])
    p_task.add_argument("--output", default="")
    p_task.add_argument("--state-dir")
    return parser


_DISPATCH = {
    "init": C.cmd_init,
    "health": C.cmd_health,
    "send": C.cmd_send,
    "recv": C.cmd_recv,
    "list": C.cmd_list,
    "upload": C.cmd_upload,
    "download": C.cmd_download,
    "listen": C.cmd_listen,
    "join": C.cmd_listen,
    "ws-send": C.cmd_ws_send,
    "agent-run": A.cmd_agent_run,
    "agent-next": A.cmd_agent_next,
    "agent-status": A.cmd_agent_status,
    "task-update": A.cmd_task_update,
}


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    config = load_config(args)
    _DISPATCH[args.command](config, args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
