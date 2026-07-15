# test_no_absolute_paths.py
import os
import sys
import unittest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts")))
from validator import has_absolute_paths

class TestNoAbsolutePaths(unittest.TestCase):
    def test_has_absolute_paths_unix(self):
        content = "The files are stored in /Users/kyle/workspace/project"
        self.assertTrue(has_absolute_paths(content))
        
    def test_has_absolute_paths_win(self):
        content = "Windows path C:\\Users\\kyle\\workspace"
        self.assertTrue(has_absolute_paths(content))
        
    def test_has_no_absolute_paths(self):
        content = "Use relative path doc/plans/FEAT-404.md"
        self.assertFalse(has_absolute_paths(content))

if __name__ == "__main__":
    unittest.main()
