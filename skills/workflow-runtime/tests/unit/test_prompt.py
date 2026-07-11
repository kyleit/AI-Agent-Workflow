# test_prompt.py
import pytest
pytestmark = pytest.mark.unit

import unittest
import os
import sys
import io
from unittest.mock import patch

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "scripts"))

from utils import prompt_select

class TestInteractivePrompts(unittest.TestCase):
    @patch("sys.stdin", io.StringIO("1\n"))
    @patch.dict(os.environ, {"TEST_PROMPT": "1"})
    def test_numeric_index_selection(self):
        res = prompt_select("Choose option:", ["A", "B", "C"], default="C")
        self.assertEqual(res, "A")

    @patch("sys.stdin", io.StringIO("B\n"))
    @patch.dict(os.environ, {"TEST_PROMPT": "1"})
    def test_exact_text_selection(self):
        res = prompt_select("Choose option:", ["A", "B", "C"], default="C")
        self.assertEqual(res, "B")

    @patch("sys.stdin", io.StringIO("\n"))
    @patch.dict(os.environ, {"TEST_PROMPT": "1"})
    def test_fallback_to_default_when_empty_stdin(self):
        res = prompt_select("Choose option:", ["A", "B", "C"], default="C")
        self.assertEqual(res, "C")

    @patch("sys.stdin", io.StringIO("invalid_input\n"))
    @patch.dict(os.environ, {"TEST_PROMPT": "1"})
    def test_invalid_input_returns_original_or_default(self):
        res = prompt_select("Choose option:", ["A", "B", "C"], default="C")
        self.assertEqual(res, "invalid_input")

    @patch("sys.stdin", io.StringIO(""))
    @patch.dict(os.environ, {"TEST_PROMPT": "1"})
    def test_empty_stdin_eof_returns_default(self):
        res = prompt_select("Choose option:", ["A", "B", "C"], default="B")
        self.assertEqual(res, "B")

    def test_testing_env_fallback_without_stdin(self):
        with patch.dict(os.environ, {"TESTING": "1"}):
            # Without TEST_PROMPT=1, should bypass select block
            res = prompt_select("Choose option:", ["A", "B", "C"], default="C")
            self.assertEqual(res, "C")

if __name__ == "__main__":
    unittest.main()
