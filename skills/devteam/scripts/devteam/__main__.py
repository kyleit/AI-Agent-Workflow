"""`python -m devteam` entry point — delegates to the CLI delivery layer."""

from __future__ import annotations

import sys

from .interface.cli.main import main

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
