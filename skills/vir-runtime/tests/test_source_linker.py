# File path: tests/unit/test_source_linker.py
import unittest
from vir_runtime.mapper.scraper import SourceLinker

class TestSourceLinker(unittest.TestCase):
    def test_resolve_coordinates_button(self):
        linker = SourceLinker(block_node_modules=True)
        coords = linker.resolve_source_coordinates("button#submit")
        
        self.assertEqual(len(coords), 1)
        self.assertEqual(coords[0].file_path, "src/components/Button.tsx")
        self.assertEqual(coords[0].line, 42)
        self.assertGreater(coords[0].confidence, 0.90)

    def test_resolve_coordinates_fallback(self):
        linker = SourceLinker(block_node_modules=True)
        coords = linker.resolve_source_coordinates("div.unknown-selector")
        
        self.assertEqual(len(coords), 1)
        self.assertEqual(coords[0].file_path, "src/App.tsx")
        self.assertEqual(coords[0].confidence, 0.50)

if __name__ == "__main__":
    unittest.main()
