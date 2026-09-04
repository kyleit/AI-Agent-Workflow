"""
Entry point for: python -m workflow_runtime <subcommand> [args] [--key=value ...]

Dispatch via CommandRegistry:
  No args / --help  -> registry.help()
  help <cmd>        -> registry.help("cmd")
  <subcommand>      -> registry.execute(subcommand, *rest)

For programmatic use:
  from workflow_runtime.presentation.cli.commands import build_registry
  registry = build_registry()
  registry.execute("memory", action="bootstrap")
  registry.execute("visual", "capture", port=9222)
  registry.help("telegram")
"""
from __future__ import annotations

import sys
from collections.abc import Sequence

if sys.version_info < (3, 11):
    sys.exit("Error: AIWF requires Python 3.11 or newer.")


def main(argv: Sequence[str] | None = None) -> int:
    from workflow_runtime.presentation.cli.bootstrap import bootstrap_di
    from workflow_runtime.presentation.cli.commands import build_registry

    bootstrap_di()
    registry = build_registry()

    args_list: list[str] = list(argv) if argv is not None else sys.argv[1:]

    if args_list and args_list[0] in ("--version", "-V", "version"):
        from workflow_runtime.shared.version_detector import detect_framework_version
        version = detect_framework_version()
        print(f"aiwf {version['version']}")
        return 0

    # No args or --help -> top-level help
    if not args_list or args_list[0] in ("--help", "-h"):
        registry.help()
        return 0

    subcommand, *rest = args_list

    # "help <cmd>" -> subcommand detail help
    if subcommand == "help":
        registry.help(rest[0] if rest else None)
        return 0

    # Normal dispatch: rest is positional argv for the command
    return registry.execute(subcommand, *rest)


if __name__ == "__main__":
    sys.exit(main())


def build_parser():
    """Compat helper used by runbook generation."""
    from workflow_runtime.presentation.cli.bootstrap import bootstrap_di
    from workflow_runtime.presentation.cli.commands import build_registry

    bootstrap_di()
    registry = build_registry()
    return registry.build_parser()
