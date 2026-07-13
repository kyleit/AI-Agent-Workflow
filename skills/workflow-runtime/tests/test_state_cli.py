"""
test_state_cli.py — FEAT-050 Task 2.3 CLI Integration Tests (TC-01)
Tests all 9 state sub-commands via subprocess (black-box CLI testing).
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

SCRIPT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "scripts", "workflow_runtime.py")
)


def run_state(subcommand: list[str], cwd: str) -> tuple[int, dict]:
    """Run `workflow_runtime.py state <subcommand>` and return (exit_code, json_output)."""
    cmd = [sys.executable, SCRIPT, "state"] + subcommand
    result = subprocess.run(
        cmd, capture_output=True, text=True, cwd=cwd, timeout=30
    )
    try:
        data = json.loads(result.stdout or result.stderr or "{}")
    except json.JSONDecodeError:
        data = {"raw": result.stdout or result.stderr}
    return result.returncode, data


class StateCLITests(unittest.TestCase):
    """CLI black-box tests for FEAT-050 Task 2.3 state sub-commands."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="state_cli_test_")
        # Create minimal .agents/state structure
        self.state_dir = os.path.join(self.tmpdir, ".agents", "state")
        os.makedirs(self.state_dir, exist_ok=True)
        for fname in ["workflow.json", "runtime.json", "context.json",
                       "approvals.json", "usage.json", "agents.json"]:
            path = os.path.join(self.state_dir, fname)
            with open(path, "w") as f:
                json.dump({"_source": fname, "status": "ok"}, f)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    # TC-01: state status returns healthy JSON
    def test_state_status_returns_json(self):
        code, data = run_state(["status"], self.tmpdir)
        self.assertEqual(code, 0)
        self.assertIn("status", data)
        self.assertIn(data["status"], ["healthy", "uninitialized", "out_of_sync"])

    # TC-02: state validate passes on valid JSON files
    def test_state_validate_passes(self):
        code, data = run_state(["validate"], self.tmpdir)
        self.assertEqual(code, 0)
        self.assertEqual(data["status"], "success")
        self.assertIsInstance(data.get("errors", []), list)

    # TC-03: state validate fails on corrupted file
    def test_state_validate_fails_on_corrupt(self):
        bad_file = os.path.join(self.state_dir, "workflow.json")
        with open(bad_file, "w") as f:
            f.write("{INVALID JSON}")
        code, data = run_state(["validate"], self.tmpdir)
        self.assertEqual(code, 1)
        self.assertEqual(data["status"], "failed")
        self.assertTrue(len(data.get("errors", [])) > 0)

    # TC-04: state snapshot creates backup directory with files
    def test_state_snapshot_creates_backup(self):
        code, data = run_state(["snapshot"], self.tmpdir)
        self.assertEqual(code, 0)
        self.assertEqual(data["status"], "success")
        self.assertIn("backup_path", data)
        backup_path = data["backup_path"]
        self.assertTrue(os.path.isdir(backup_path), f"Backup dir missing: {backup_path}")
        backed_up = data.get("files_backed_up", [])
        self.assertGreater(len(backed_up), 0)

    # TC-05: state migrate produces migration-report.json
    def test_state_migrate_writes_report(self):
        code, data = run_state(["migrate"], self.tmpdir)
        # migrate may exit 0 or 1 depending on errors, but should always write a report
        report_path = os.path.join(
            self.tmpdir, ".agents", "state", "recovery", "state-migration-report.json"
        )
        self.assertTrue(
            os.path.exists(report_path),
            f"Migration report not found at {report_path}"
        )
        with open(report_path) as f:
            report = json.load(f)
        self.assertIn("status", report)
        self.assertIn("migrated_files", report)

    # TC-06: state aggregate returns dashboard + legacy_snapshot paths
    def test_state_aggregate_returns_paths(self):
        code, data = run_state(["aggregate"], self.tmpdir)
        self.assertEqual(code, 0, f"aggregate failed: {data}")
        self.assertEqual(data["status"], "success")
        self.assertIn("dashboard", data)
        # dashboard file must exist
        dashboard_path = data["dashboard"]
        self.assertTrue(
            os.path.exists(dashboard_path),
            f"dashboard.json not created at {dashboard_path}"
        )

    # TC-07: state emit WorkflowInitialized creates event in events.jsonl
    def test_state_emit_creates_event(self):
        code, data = run_state(
            ["emit", "--type", "WorkflowInitialized", "--payload", '{"feature_id": "FEAT-TEST"}'],
            self.tmpdir,
        )
        self.assertEqual(code, 0, f"emit failed: {data}")
        self.assertEqual(data["status"], "success")
        self.assertIn("event_id", data)
        self.assertEqual(data["event_type"], "WorkflowInitialized")
        # Check events.jsonl was written
        events_path = os.path.join(self.tmpdir, ".agents", "state", "events", "events.jsonl")
        self.assertTrue(os.path.exists(events_path), "events.jsonl not found")
        with open(events_path) as f:
            lines = [json.loads(l) for l in f if l.strip()]
        self.assertTrue(any(e.get("event_type") == "WorkflowInitialized" for e in lines))

    # TC-08: state emit with missing --type exits 1
    def test_state_emit_missing_type_fails(self):
        result = subprocess.run(
            [sys.executable, SCRIPT, "state", "emit", "--payload", "{}"],
            capture_output=True, text=True, cwd=self.tmpdir, timeout=10
        )
        # argparse will error before our handler is reached — exit non-zero
        self.assertNotEqual(result.returncode, 0)

    # TC-09: state doctor returns health JSON
    def test_state_doctor_returns_health(self):
        code, data = run_state(["doctor"], self.tmpdir)
        # Exit code 0 (healthy/warning) or 1 (error); either way, JSON must have "status"
        self.assertIn("status", data)
        self.assertIn(data["status"], ["healthy", "warning", "degraded", "error"])
        self.assertIn("checks", data)
        self.assertIn("errors", data)


if __name__ == "__main__":
    unittest.main()
