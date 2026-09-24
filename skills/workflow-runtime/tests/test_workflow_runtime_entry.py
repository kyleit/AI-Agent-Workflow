"""
test_workflow_runtime_entry.py — Unit and integration tests for FEAT-311 Workflow Runtime Entry Command Migration.
"""
import os
import sys
import unittest
import json
import argparse
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts")))

import importlib.util
fixtures_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "fixtures"))
spec = importlib.util.spec_from_file_location("fixtures_conftest", os.path.join(fixtures_dir, "conftest.py"))
if spec and spec.loader:
    fixtures_conftest = importlib.util.module_from_spec(spec)
    sys.modules["fixtures_conftest"] = fixtures_conftest
    spec.loader.exec_module(fixtures_conftest)
    RuntimeTestBase = fixtures_conftest.RuntimeTestBase
else:
    raise ImportError("Could not load fixtures/conftest.py")

from workflow_runtime import do_workflow, do_orchestrator

class WorkflowRuntimeEntryTests(RuntimeTestBase):

    def setUp(self):
        super().setUp()
        from state_path import ensure_dirs
        ensure_dirs(self.workspace)
        
        # Override workspace root for event logger and state path
        self.patch_logger = patch("state_path.get_events_path", return_value=os.path.join(self.workspace, ".agents", "state", "events", "events.jsonl"))
        self.patch_logger.start()

        # `workflow submit` routes through WorkflowEntryGateway("."), so run
        # inside the isolated workspace instead of the real repository.
        self._orig_cwd = os.getcwd()
        os.chdir(self.workspace)

    def tearDown(self):
        os.chdir(self._orig_cwd)
        self.patch_logger.stop()
        super().tearDown()

    def test_workflow_submit_feature(self):
        # Setup argument parser namespace mock
        args = argparse.Namespace()
        args.subaction = "submit"
        args.prompt = "Create a new visual editor interface"

        do_workflow(args)
                
        # Check that state files were created
        wf_path = os.path.join(self.workspace, ".agents", "state", "workflow.json")
        ctx_path = os.path.join(self.workspace, ".agents", "state", "context.json")
        rt_path = os.path.join(self.workspace, ".agents", "state", "runtime.json")
        
        self.assertTrue(os.path.exists(wf_path))
        self.assertTrue(os.path.exists(ctx_path))
        self.assertTrue(os.path.exists(rt_path))
        
        with open(wf_path, "r") as f:
            wf = json.load(f)
        self.assertEqual(wf["active_phase"], "brainstorming")
        # The gateway allocates the next free FEAT id; an empty workspace starts at 001.
        self.assertEqual(wf["work_item"]["id"], "FEAT-001")
        
    def test_workflow_submit_bug_fix(self):
        args = argparse.Namespace()
        args.subaction = "submit"
        args.prompt = "Fix authorization loop bug"

        do_workflow(args)
                
        ctx_path = os.path.join(self.workspace, ".agents", "state", "context.json")
        self.assertTrue(os.path.exists(ctx_path))
        with open(ctx_path, "r") as f:
            ctx = json.load(f)
        
        # Check that authorization allowed_phases is populated
        self.assertIn("brainstorming", ctx["authorization"]["allowed_phases"])
        
    def test_orchestrator_run_redirection(self):
        # Verify orchestrator run redirects to do_workflow submit
        args = argparse.Namespace()
        args.subaction = "run"
        args.work_item_id = "FEAT-111"
        args.work_item_opt = None
        args.work_item = None
        
        # do_orchestrator resolves do_workflow from its own module, not the package facade.
        with patch("workflow_runtime.presentation.cli.commands._impl.workflow.orchestrator.do_workflow") as mock_do_workflow:
            do_orchestrator(args)
            mock_do_workflow.assert_called_once()
            mock_args = mock_do_workflow.call_args[0][0]
            self.assertEqual(mock_args.subaction, "submit")
            self.assertIn("FEAT-111", mock_args.prompt)

if __name__ == "__main__":
    unittest.main()
