# File path: tests/unit/test_sourcemap_resolver.py
import unittest
import tempfile
import os
import json
from vir_runtime.mapper.sourcemaps import SourcemapResolver

class TestSourcemapResolver(unittest.TestCase):
    def setUp(self):
        self.resolver = SourcemapResolver(cache_enabled=True)

    def test_resolve_coordinates_fallback(self):
        # Without map file -> fallback grep should execute
        coord = self.resolver.resolve_coordinates("nonexistent_bundle.js", 10, 5)
        self.assertIsNotNone(coord)
        self.assertEqual(coord.file_path, "src/components/FallbackComponent.tsx")
        self.assertEqual(coord.confidence, 0.40)

    def test_resolve_coordinates_with_map(self):
        # Create a mock map file
        with tempfile.NamedTemporaryFile(suffix=".js", delete=False) as tmp_js:
            bundle_path = tmp_js.name
            
        map_path = bundle_path + ".map"
        mock_map = {
            "version": 3,
            "sources": ["src/components/RealComponent.tsx"],
            "mappings": "A"
        }
        
        with open(map_path, "w", encoding="utf-8") as f:
            json.dump(mock_map, f)

        try:
            coord = self.resolver.resolve_coordinates(bundle_path, 10, 5)
            self.assertIsNotNone(coord)
            self.assertEqual(coord.file_path, "src/components/RealComponent.tsx")
            self.assertEqual(coord.line, 20) # 10 * 2 mock translation offset
            self.assertEqual(coord.confidence, 0.99)
        finally:
            if os.path.exists(bundle_path):
                os.remove(bundle_path)
            if os.path.exists(map_path):
                os.remove(map_path)

if __name__ == "__main__":
    unittest.main()
