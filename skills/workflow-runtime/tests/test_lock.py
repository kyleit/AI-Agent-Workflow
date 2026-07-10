import unittest
import os
import json
import sys
import subprocess
from datetime import datetime

class TestExclusiveLock(unittest.TestCase):
    def setUp(self):
        self.lock_file = os.path.join(".agents", "runtime", "workflow.lock")
        if os.path.exists(self.lock_file):
            try:
                os.remove(self.lock_file)
            except Exception:
                pass
                
    def tearDown(self):
        if os.path.exists(self.lock_file):
            try:
                os.remove(self.lock_file)
            except Exception:
                pass

    def run_cli(self, args):
        cmd = [sys.executable, ".agents/skills/workflow-runtime/scripts/workflow_runtime.py"] + args
        res = subprocess.run(cmd, capture_output=True, text=True)
        return res

    def test_lock_created_on_start(self):
        res = self.run_cli(["start", "--skill", "test-skill", "--command", "test-cmd", "--step", "step-1"])
        self.assertEqual(res.returncode, 0)
        self.assertTrue(os.path.exists(self.lock_file))
        with open(self.lock_file, "r") as f:
            data = json.load(f)
        self.assertEqual(data["skill"], "test-skill")
        self.assertIn("orchestrator|test-skill", data["lock_owner"])
        self.assertIn("started_at", data)
        self.assertIn("heartbeat_at", data)

    def test_lock_collision_blocks(self):
        os.makedirs(os.path.dirname(self.lock_file), exist_ok=True)
        with open(self.lock_file, "w") as f:
            json.dump({
                "lock_owner": "orchestrator|other-skill",
                "work_item_id": "unknown",
                "skill": "other-skill",
                "pid": 1234,
                "started_at": datetime.now().astimezone().isoformat(),
                "heartbeat_at": datetime.now().astimezone().isoformat()
            }, f)
            
        res = self.run_cli(["start", "--skill", "test-skill", "--command", "test-cmd", "--step", "step-1"])
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("Another workflow is already running.", res.stderr)
        self.assertIn("Do not continue.", res.stderr)

    def test_lock_released_on_complete(self):
        self.run_cli(["start", "--skill", "test-skill", "--command", "test-cmd", "--step", "step-1"])
        self.assertTrue(os.path.exists(self.lock_file))
        res = self.run_cli(["complete", "--step", "complete-step"])
        self.assertEqual(res.returncode, 0)
        self.assertFalse(os.path.exists(self.lock_file))

    def test_lock_released_on_fail(self):
        self.run_cli(["start", "--skill", "test-skill", "--command", "test-cmd", "--step", "step-1"])
        self.assertTrue(os.path.exists(self.lock_file))
        res = self.run_cli(["fail", "--step", "fail-step"])
        self.assertEqual(res.returncode, 0)
        self.assertFalse(os.path.exists(self.lock_file))

    def test_state_diagnose(self):
        if os.path.exists(self.lock_file):
            os.remove(self.lock_file)
        res = self.run_cli(["state", "diagnose"])
        self.assertEqual(res.returncode, 0)
        data = json.loads(res.stdout.strip())
        self.assertEqual(data["active_task"], "None")
        self.assertEqual(data["lock_owner"], "None")

        self.run_cli(["start", "--skill", "test-skill", "--command", "test-cmd", "--step", "step-1"])
        res2 = self.run_cli(["state", "diagnose"])
        data2 = json.loads(res2.stdout.strip())
        self.assertEqual(data2["lock_owner"], "test-skill")
        self.assertIn("test-skill", data2["active_task"])

if __name__ == "__main__":
    unittest.main()
