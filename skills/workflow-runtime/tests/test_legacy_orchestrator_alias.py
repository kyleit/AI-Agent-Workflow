# test_legacy_orchestrator_alias.py
import os
import sys
import unittest
import argparse
from unittest.mock import patch

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts")))
from workflow_runtime import do_orchestrator

class TestLegacyOrchestratorAlias(unittest.TestCase):
    @patch("workflow_runtime.do_workflow")
    def test_legacy_run_redirection(self, mock_do_workflow):
        args = argparse.Namespace()
        args.subaction = "run"
        args.work_item = "FEAT-404"
        args.work_item_opt = None
        args.work_item_id = None
        
        do_orchestrator(args)
        self.assertTrue(mock_do_workflow.called)
        
    def test_legacy_resident_daemon_error(self):
        args = argparse.Namespace()
        args.subaction = "start"
        args.work_item = "FEAT-404"
        args.work_item_opt = None
        args.work_item_id = None
        
        with self.assertRaises(SystemExit) as cm:
            do_orchestrator(args)
        self.assertEqual(cm.exception.code, 1)

if __name__ == "__main__":
    unittest.main()
