"""
workflow_runtime/presentation/cli/runtime_command_handlers.py

CLI command handlers for AIWF runtime system, configuration, dependencies, releases, and diagnostics.
"""
from __future__ import annotations

import argparse
import sys


def handle_runtime(args: argparse.Namespace) -> int:
    from workflow_runtime.presentation.cli.commands._impl.system.runtime_bus import (
        do_runtime_action)
    return do_runtime_action(args)


def handle_init(args: argparse.Namespace) -> int:
    from workflow_runtime.presentation.cli.commands._impl.session.session_init import (
        do_init)
    return do_init(args)


def handle_config(args: argparse.Namespace) -> int:
    from workflow_runtime.presentation.cli.commands._impl.config.config_manager import (
        do_config_action)
    return do_config_action(args)


def handle_runbook(args: argparse.Namespace) -> int:
    from workflow_runtime.presentation.cli.runbook_generator import (
        generate_and_save_runbook)
    generate_and_save_runbook()
    return 0


def handle_deps(args: argparse.Namespace) -> int:
    from workflow_runtime.presentation.cli.commands._impl.dependency_handler import (
        do_deps)
    return do_deps(args)


def handle_permissions(args: argparse.Namespace) -> int:
    from workflow_runtime.presentation.cli.commands._impl.config.config_manager import (
        do_permission)
    return do_permission(args)


def handle_migration(args: argparse.Namespace) -> int:
    from workflow_runtime.presentation.cli.commands._impl.docs_migration import (
        do_migration_action)
    return do_migration_action(args)


def handle_validate(args: argparse.Namespace) -> int:
    """Validate session checkpoint and workspace integrity."""
    from workflow_runtime.presentation.cli.commands._impl.system.system_health import (
        do_validate)
    return do_validate(args)


def handle_release(args: argparse.Namespace) -> int:
    from workflow_runtime.presentation.cli.commands._impl.system.system_health import (
        do_release_action)
    return do_release_action(args)


def handle_doctor(args: argparse.Namespace) -> int:
    """Run workspace/framework diagnostics."""
    try:
        from workflow_runtime.application.system import workspace_doctor
        argv = ["doctor"]
        if getattr(args, "fix", False):
            argv.append("--fix")
        old_argv = sys.argv
        sys.argv = argv
        result = workspace_doctor.main()
        sys.argv = old_argv
        return int(result) if result is not None else 0
    except Exception as e:
        print(f"[ERROR] doctor: {e}", file=sys.stderr)
        return 1


__all__ = [
    "handle_runtime",
    "handle_init",
    "handle_config",
    "handle_runbook",
    "handle_deps",
    "handle_permissions",
    "handle_migration",
    "handle_validate",
    "handle_release",
    "handle_doctor",
]
