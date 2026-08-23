#!/usr/bin/env python3
"""msgbus-ws relay server entrypoint (thin).

Standard library only. See the `msgbusws/` package for the Clean-Architecture
implementation (domain / application / infrastructure / interface).

Usage:
  python msgbus_server.py --port 8787 --token secret --store ~/.aiwf/msgbus --bind 0.0.0.0
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from msgbusws.interface.server_app import create_server  # noqa: E402


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="msgbus-ws relay server (REST + WebSocket + tus)")
    parser.add_argument("--port", type=int, default=int(os.environ.get("MSGBUS_PORT", "8787")))
    parser.add_argument("--token", default=os.environ.get("MSGBUS_TOKEN", "changeme"))
    parser.add_argument("--store", default=os.environ.get("MSGBUS_STORE", str(Path.home() / ".aiwf" / "msgbus")))
    parser.add_argument("--bind", default=os.environ.get("MSGBUS_BIND", "0.0.0.0"))
    args = parser.parse_args(argv)

    store = Path(args.store).expanduser().resolve()
    httpd = create_server(args.bind, args.port, store, args.token)
    sys.stderr.write(f"[msgbus] listening on {args.bind}:{args.port} store={store}\n")
    sys.stderr.flush()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        sys.stderr.write("\n[msgbus] shutting down\n")
    finally:
        httpd.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
