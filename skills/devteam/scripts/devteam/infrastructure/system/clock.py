"""SystemClock — wall-clock ISO-8601 timestamps with local offset."""

from __future__ import annotations

import datetime


class SystemClock:
    def now_iso(self) -> str:
        return datetime.datetime.now().astimezone().isoformat()
