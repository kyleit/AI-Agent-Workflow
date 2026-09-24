"""Module entrypoint: `python -m loop_engine <load|decide|persist> ...`.

Ensures the package root (the `scripts/` directory) is importable when the
module is executed directly, then delegates to the presentation CLI.
"""

from __future__ import annotations

import sys
from pathlib import Path

_PACKAGE_ROOT = Path(__file__).resolve().parent.parent
if str(_PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(_PACKAGE_ROOT))

from loop_engine.presentation.cli import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
