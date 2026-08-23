from __future__ import annotations

from typing import Any

"""Command: telegram — Global Telegram Shared Daemon"""

import argparse

from workflow_runtime.presentation.cli.command_interface import CommandMeta


class TelegramCommand:
    """
    Global Telegram Shared Daemon: send, start/stop, link, config.

    Usage examples:
      aiwf telegram send --message "hello" --chat-id 123
      aiwf telegram start
      aiwf telegram status
      aiwf telegram link
      aiwf telegram config
      aiwf telegram test
    """

    def meta(self) -> CommandMeta:
        return CommandMeta(
            "telegram",
            aliases=[],
            category="telegram",
            help="Global Telegram Shared Daemon: send, start, stop, link, config",
            requires_lock=True,
        )

    def add_parser(self, subparsers: Any) -> argparse.ArgumentParser:
        p = subparsers.add_parser("telegram", help=self.meta().help)
        sub = p.add_subparsers(dest="subaction", metavar="action")

        # send
        send_p = sub.add_parser("send", help="Send a Telegram message")
        send_p.add_argument("--message", "-m", required=True,
                            help="Message text")
        send_p.add_argument("--chat-id",
                            help="Target chat ID (overrides config)")
        send_p.add_argument("--token",
                            help="Bot token (overrides config)")
        send_p.add_argument("--parse-mode",
                            choices=["HTML", "Markdown"], default="HTML")

        # notify (shorthand)
        notify_p = sub.add_parser("notify",
                                  help="Send notification (alias for send)")
        notify_p.add_argument("--message", "-m", required=True)
        notify_p.add_argument("--level",
                              choices=["info", "warning", "error", "success"],
                              default="info")

        # daemon control
        sub.add_parser("start",   help="Start the Telegram daemon")
        sub.add_parser("stop",    help="Stop the Telegram daemon")
        sub.add_parser("status",  help="Show daemon status")
        sub.add_parser("restart", help="Restart the daemon")

        # account / setup
        sub.add_parser("link",   help="Link Telegram account (interactive)")
        sub.add_parser("config", help="Interactive step-by-step credential setup")
        sub.add_parser("test",   help="Send a test message to verify setup")

        self._parser = p
        return p

    def parse(self, argv: list[str]) -> argparse.Namespace:
        return self._parser.parse_args(argv)

    def run(self, args: argparse.Namespace) -> None:
        from workflow_runtime.presentation.cli.workflow_runtime import \
            do_telegram
        do_telegram(args)

    def print_help(self) -> None:
        self._parser.print_help()


def all_commands() -> list[object]:
    return [TelegramCommand()]