"""Module entrypoint: `python -m malo <select|run> ...`."""

from __future__ import annotations

import sys
from pathlib import Path

_PACKAGE_ROOT = Path(__file__).resolve().parent.parent
if str(_PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(_PACKAGE_ROOT))

from malo.presentation.cli import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
