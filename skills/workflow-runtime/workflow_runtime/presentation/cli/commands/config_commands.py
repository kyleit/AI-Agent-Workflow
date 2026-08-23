from __future__ import annotations

from typing import Any

"""Commands: config, permission(+permissions), rules, registry"""

import argparse

from workflow_runtime.presentation.cli.command_interface import CommandMeta


class ConfigCommand:
    def meta(self) -> CommandMeta:
        return CommandMeta(
            "config",
            category="config",
            help="Check and bootstrap AIWF runtime services configuration",
            requires_lock=True,
        )

    def add_parser(self, subparsers: Any) -> argparse.ArgumentParser:
        p = subparsers.add_parser("config", help=self.meta().help)
        p.add_argument("--check-only", action="store_true", help="Only report configuration status")
        p.add_argument("--no-start", action="store_true", help="Do not start runtime services")
        sub = p.add_subparsers(dest="subaction")
        sub.add_parser("show",     help="Show current config")
        sub.add_parser("validate", help="Validate config file")
        sub.add_parser("reset",    help="Reset to defaults")
        g = sub.add_parser("get", help="Get a config key")
        g.add_argument("key")
        s = sub.add_parser("set", help="Set a config key")
        s.add_argument("key")
        s.add_argument("value")
        self._parser = p
        return p

    def parse(self, argv: list[str]) -> argparse.Namespace: return self._parser.parse_args(argv)

    def run(self, args: argparse.Namespace) -> None:
        from workflow_runtime.presentation.cli.commands._impl.config.config_manager import \
            do_config_action
        do_config_action(args)

    def print_help(self) -> None: self._parser.print_help()


class PermissionCommand:
    def meta(self) -> CommandMeta:
        return CommandMeta(
            "permission",
            aliases=["permissions"],
            category="config",
            help="Manage agent permissions and authorization rules",
        )

    def add_parser(self, subparsers: Any) -> argparse.ArgumentParser:
        p = subparsers.add_parser(
            "permission",
            aliases=["permissions"],
            help=self.meta().help,
        )
        sub = p.add_subparsers(dest="subaction")
        sub.add_parser("list",   help="List all permissions")
        sub.add_parser("status", help="Current permission mode")
        g = sub.add_parser("grant",  help="Grant a permission")
        g.add_argument("--agent"); g.add_argument("--action")
        r = sub.add_parser("revoke", help="Revoke a permission")
        r.add_argument("--agent"); r.add_argument("--action")
        self._parser = p
        return p

    def parse(self, argv: list[str]) -> argparse.Namespace: return self._parser.parse_args(argv)

    def run(self, args: argparse.Namespace) -> None:
        from workflow_runtime.presentation.cli.workflow_runtime import \
            do_permission
        do_permission(args)

    def print_help(self) -> None: self._parser.print_help()


class RulesCommand:
    def meta(self) -> CommandMeta:
        return CommandMeta(
            "rules",
            category="config",
            help="Show active AI_RULES.md and AGENTS.md policies",
        )

    def add_parser(self, subparsers: Any) -> argparse.ArgumentParser:
        p = subparsers.add_parser("rules", help=self.meta().help)
        sub = p.add_subparsers(dest="subaction")
        sub.add_parser("status")
        self._parser = p
        return p

    def parse(self, argv: list[str]) -> argparse.Namespace: return self._parser.parse_args(argv)

    def run(self, args: argparse.Namespace) -> None:
        # Default to 'status' if no subaction given
        if not getattr(args, 'subaction', None):
            args.subaction = 'status'
        from workflow_runtime.presentation.cli.workflow_runtime import \
            do_rules_action
        do_rules_action(args)

    def print_help(self) -> None: self._parser.print_help()


class RegistryCommand:
    def meta(self) -> CommandMeta:
        return CommandMeta(
            "registry",
            category="config",
            help="Manage AIWF project registry (register, list, doctor)",
        )

    def add_parser(self, subparsers: Any) -> argparse.ArgumentParser:
        p = subparsers.add_parser("registry", help=self.meta().help)
        p.add_argument("--format", choices=["json", "table", "text"], default="table")
        sub = p.add_subparsers(dest="subaction")

        # register
        reg = sub.add_parser("register", help="Register current (or given) directory as an AIWF project")
        reg.add_argument("path", nargs="?", default=".", help="Project path (default: current dir)")
        reg.add_argument("--force", action="store_true", help="Re-register even if already registered")
        reg.add_argument("--source", default="manual", help="Registration source tag")
        reg.add_argument("--framework-root", default=None)

        # unregister
        un = sub.add_parser("unregister", help="Remove a project from the registry")
        un.add_argument("path", nargs="?", default=".", help="Project path to remove")

        # list
        sub.add_parser("list", help="List all registered projects")

        # doctor
        sub.add_parser("doctor", help="Check registry health (missing paths, stale entries)")

        # cleanup
        sub.add_parser("cleanup", help="Remove stale/missing projects from registry")

        self._parser = p
        return p

    def parse(self, argv: list[str]) -> argparse.Namespace: return self._parser.parse_args(argv)

    def run(self, args: argparse.Namespace) -> None:
        from workflow_runtime.presentation.cli.workflow_runtime import \
            do_registry
        do_registry(args)

    def print_help(self) -> None: self._parser.print_help()


def all_commands() -> list[object]:
    return [ConfigCommand(), PermissionCommand(), RulesCommand(), RegistryCommand()]
