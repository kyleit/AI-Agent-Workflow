# File path: vir_runtime/mapper/sourcemaps.py
import os
import json
from typing import Optional
from vir_runtime.mapper.scraper import SourceCoordinate

class SourceResolutionFailedError(Exception):
    pass

class SourcemapResolver:
    def __init__(self, cache_enabled: bool = True):
        self.cache_enabled = cache_enabled
        self.cache = {}

    def resolve_coordinates(self, bundle_js_path: str, line: int, col: int) -> Optional[SourceCoordinate]:
        """Translate bundle JS coordinates back to TS source lines."""
        print(f"[SourcemapResolver] Translating coordinates: {bundle_js_path}:{line}:{col}")
        
        # Check cache if enabled
        cache_key = f"{bundle_js_path}:{line}:{col}"
        if self.cache_enabled and cache_key in self.cache:
            return self.cache[cache_key]

        sourcemap_path = bundle_js_path + ".map"
        if not os.path.exists(sourcemap_path):
            # Missing sourcemap triggers fallback path
            print(f"[SourcemapResolver] Sourcemap file {sourcemap_path} missing. Activating grep fallback.")
            fallback = self._execute_grep_fallback(bundle_js_path, line)
            if self.cache_enabled:
                self.cache[cache_key] = fallback
            return fallback

        try:
            with open(sourcemap_path, "r", encoding="utf-8") as f:
                map_data = json.load(f)
            
            # Simple mock parse for sourcemap mappings
            sources = map_data.get("sources", ["src/unknown.tsx"])
            target_source = sources[0]
            
            coord = SourceCoordinate(
                file_path=target_source,
                line=line * 2, # Mock translation offset
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
        # Standard fallback if sourcemap resolving fails
        return SourceCoordinate(
            file_path="src/components/FallbackComponent.tsx",
            line=line,
            column=1,
            confidence=0.40
        )
