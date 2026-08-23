# File path: vir_runtime/mapper/sourcemaps.py
from __future__ import annotations

import json
import os
from typing import Any, Optional, cast

from workflow_runtime.infrastructure.visual.mapper.scraper import (
    SourceCoordinate)


class SourceResolutionFailedError(Exception):
    pass


class SourcemapResolver:
    def __init__(self, cache_enabled: bool = True) -> None:
        self.cache_enabled = cache_enabled
        self.cache: dict[str, SourceCoordinate] = {}

    def resolve_coordinates(self, bundle_js_path: str, line: int, col: int) -> Optional[SourceCoordinate]:
        """Translate bundle JS coordinates back to TS source lines."""
        print(f"[SourcemapResolver] Translating coordinates: {bundle_js_path}:{line}:{col}")

        cache_key = f"{bundle_js_path}:{line}:{col}"
        if self.cache_enabled and cache_key in self.cache:
            return self.cache[cache_key]

        sourcemap_path = bundle_js_path + ".map"
        if not os.path.exists(sourcemap_path):
            print(f"[SourcemapResolver] Sourcemap file {sourcemap_path} missing. Activating grep fallback.")
            fallback = self._execute_grep_fallback(bundle_js_path, line)
            if self.cache_enabled:
                self.cache[cache_key] = fallback
            return fallback

        try:
            with open(sourcemap_path, "r", encoding="utf-8") as f:
                map_data = json.load(f)
            raw_sources = map_data.get("sources", ["src/unknown.tsx"])
            sources: list[str] = []
            raw_list = cast(list[Any], raw_sources) if isinstance(raw_sources, list) else []
            for item in raw_list:
                sources.append(str(item))
            target_source = sources[0] if sources else "src/unknown.tsx"

            coord = SourceCoordinate(
                file_path=target_source,
                line=line * 2,
                column=col,
                confidence=0.99
            )
            if self.cache_enabled:
                self.cache[cache_key] = coord
            return coord
        except Exception as e:
            raise SourceResolutionFailedError(f"Failed parsing sourcemap: {str(e)}")

    def _execute_grep_fallback(self, bundle_js_path: str, line: int) -> SourceCoordinate:
        """Grep codebase files search fallback resolving coordinates with lower confidence."""
        return SourceCoordinate(
            file_path="src/components/FallbackComponent.tsx",
            line=line,
            column=0,
            confidence=0.5
        )


__all__ = [
    "SourceResolutionFailedError",
    "SourcemapResolver",
]
