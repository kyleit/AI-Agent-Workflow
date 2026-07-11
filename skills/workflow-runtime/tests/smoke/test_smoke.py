# test_smoke.py
import unittest
import sys
import os
import subprocess
import pytest
pytestmark = pytest.mark.smoke
pytestmark = [pytest.mark.unit, pytest.mark.smoke]


@pytest.mark.smoke
class TestSmokeSuite(unittest.TestCase):
    def test_imports(self):
        # Verify basic imports resolve correctly
        import workflow_runtime
        import db
        import session
        import validator
        self.assertIsNotNone(workflow_runtime)
        self.assertIsNotNone(db)

    def test_cli_help(self):
        # Verify running CLI tool help doesn't crash and exits with code 0
        cli_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "scripts", "workflow_runtime.py"))
        try:
            out = subprocess.check_output([sys.executable, cli_path, "--help"], stderr=subprocess.STDOUT)
            self.assertIn(b"AI Workflow Runtime Engine CLI", out)
        except subprocess.CalledProcessError as e:
            self.fail(f"CLI help failed with exit code {e.returncode}: {e.output.decode()}")

    def test_config_loading(self):
        # Verify session configuration loads successfully (returns a dict)
        import session as sess
        config = sess.load_session()
        self.assertIsInstance(config, dict)
