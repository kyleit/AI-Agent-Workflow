# File path: tests/unit/test_cli.py
import unittest
from vir_runtime.core.cli import CLIRunner, InteractivePromptBlocked

class TestCLIRunner(unittest.TestCase):
    def setUp(self):
        self.runner = CLIRunner()

    def test_cli_success(self):
        code = self.runner.main(["--mode", "cli", "--feature-id", "FEAT-001"])
        self.assertEqual(code, 0)

    def test_cli_help(self):
        # argparse exit code for help is usually 0 on python >= 3.9 but runner captures SystemExit
        code = self.runner.main(["--help"])
        self.assertEqual(code, 1)

    def test_cli_blocked_in_ci(self):
        with self.assertRaises(InteractivePromptBlocked):
            self.runner.main(["--mode", "cli", "--ci"])

if __name__ == "__main__":
    unittest.main()
