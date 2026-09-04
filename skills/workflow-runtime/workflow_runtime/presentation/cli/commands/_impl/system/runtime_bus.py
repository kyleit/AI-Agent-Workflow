from __future__ import annotations

import argparse
import json
import os
import sys
from workflow_runtime.infrastructure.session.session_lock import (
    DEFAULT_RUNTIME_POLICY, get_runtime_policy_path, load_runtime_policy,
    validate_runtime_policy, write_runtime_policy)
from workflow_runtime.presentation.cli.commands._impl.session.session_meta import (
    do_runtime_bus)
from workflow_runtime.presentation.cli.commands._impl.provider.provider_data import (
    enable_runtime_bus_autostart,
    disable_runtime_bus_autostart,
    is_runtime_bus_autostart_enabled,
    restart_runtime_bus_daemon,
    runtime_bus_autostart_diagnostics,
    start_runtime_bus_daemon as _start_runtime_bus_daemon,
    stop_runtime_bus_daemon as _stop_runtime_bus_daemon,
)


def do_runtime_action(args: argparse.Namespace) -> int:
    subaction = getattr(args, 'action', None) or getattr(args, 'subaction', None)
    if subaction in {"start", "stop", "restart", "reload", "status", "enable", "disable", "process", "daemon"}:
        do_runtime_bus(args)
        return 0

    if subaction != "policy":
        print(f"Unknown runtime subaction: {subaction}", file=sys.stderr)
        sys.exit(1)

    policy_action = getattr(args, "policy_action", None)

    if not policy_action:
        try:
            policy = load_runtime_policy(validate=True)
            print(json.dumps(policy, indent=2))
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    elif policy_action == "validate":
        path = get_runtime_policy_path()
        if not os.path.exists(path):
            print("Error: runtime-policy.json does not exist. Run 'aiwf init' first to generate it.", file=sys.stderr)
            sys.exit(1)

        try:
            with open(path, "r", encoding="utf-8") as f:
                policy = json.load(f)
            ok, err = validate_runtime_policy(policy)
            if not ok:
                print(f"Validation FAILED: {err}", file=sys.stderr)
                sys.exit(1)
            print("Validation PASSED: runtime-policy.json conforms to the schema.")
        except Exception as e:
            print(f"Validation FAILED: {e}", file=sys.stderr)
            sys.exit(1)

    elif policy_action == "reset":
        try:
            write_runtime_policy(DEFAULT_RUNTIME_POLICY)
            print("Successfully reset runtime-policy.json to default values.")
        except Exception as e:
            print(f"Error resetting runtime-policy.json: {e}", file=sys.stderr)
            sys.exit(1)
    return 0


def get_runtime_bus_status() -> str:
    """Return current runtime bus status string."""
    from workflow_runtime.infrastructure.persistence.runtime_daemon_state import RuntimeDaemonState
    return str(RuntimeDaemonState().inspect().get("state", "STOPPED"))


def start_runtime_bus_daemon() -> tuple[bool, int | None, str]:
    """Start the runtime bus daemon. Returns (success, pid, message)."""
    return _start_runtime_bus_daemon()


def stop_runtime_bus_daemon() -> bool:
    """Stop the runtime bus daemon. Returns True if stopped."""
    stopped, _pid = _stop_runtime_bus_daemon()
    return stopped


__all__ = [
    "do_runtime_action",
    "get_runtime_bus_status",
    "start_runtime_bus_daemon",
    "stop_runtime_bus_daemon",
    "enable_runtime_bus_autostart",
    "disable_runtime_bus_autostart",
    "is_runtime_bus_autostart_enabled",
    "restart_runtime_bus_daemon",
    "runtime_bus_autostart_diagnostics",
]
