"""Put the malo package (and loop_engine) on sys.path for tests."""

from __future__ import annotations

import os
import sys

_SCRIPTS = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts"))
_LOOP = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "loop-controller", "scripts")
)
for path in (_SCRIPTS, _LOOP):
    if path not in sys.path:
        sys.path.insert(0, path)
