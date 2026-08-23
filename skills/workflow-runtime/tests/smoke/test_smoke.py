# test_smoke.py
import unittest
import sys
import os
import subprocess
import pytest
from tests.conftest import run_cli

pytestmark = [pytest.mark.unit, pytest.mark.smoke]


@pytest.mark.smoke
class TestSmokeSuite(unittest.TestCase):
    def test_cli_help(self):
        # Verify running CLI via -m doesn't crash and exits with code 0
        res = run_cli("--help")
        self.assertEqual(res.returncode, 0, f"CLI help failed:\n{res.stderr}")
        self.assertIn("AI Workflow Runtime Engine CLI", res.stdout)

    def test_config_loading(self):
        # Verify session configuration loads successfully (returns a dict)
        from workflow_runtime.infrastructure.session.session import load_session
        config = load_session()
        self.assertIsInstance(config, dict)
