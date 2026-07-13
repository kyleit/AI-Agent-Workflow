"""
conftest.py — Shared test base for AIWF runtime integration tests.
Provides:
  - RuntimeTestBase: isolated tempdir workspace per test with StatePath patching
  - Fixture loading utilities
  - Auto-cleanup via tearDown()
"""
import os
import sys
import json
import shutil
import tempfile
import unittest

# Ensure scripts/ is on the path for all test files
_SCRIPTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts"))
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

FIXTURES_DIR = os.path.abspath(os.path.dirname(__file__))


class RuntimeTestBase(unittest.TestCase):
    """
    Base class for all AIWF runtime integration tests.
    
    Each test gets:
    - self.workspace: isolated tempdir (automatically cleaned up)
    - self.state_root: .agents/state/ inside workspace
    - AIWF_STATE_ROOT env var set to self.state_root during test
    
    Methods:
    - self.load_fixture(fixture_path): Load a JSON fixture from tests/fixtures/
    - self.copy_fixture_workspace(fixture_name): Copy fixture state into workspace
    - self.make_state_dirs(): Create canonical state subdirectories
    """

    def setUp(self):
        # Create isolated temp workspace
        self.workspace = tempfile.mkdtemp(prefix="aiwf_test_")
        self.state_root = os.path.join(self.workspace, ".agents", "state")
        self.runtime_dir = os.path.join(self.workspace, ".agents", "runtime")

        # Patch AIWF_STATE_ROOT env var to point to this workspace's state
        os.environ["AIWF_STATE_ROOT"] = self.state_root

        # Create minimal directory structure
        os.makedirs(self.state_root, exist_ok=True)
        os.makedirs(self.runtime_dir, exist_ok=True)

    def tearDown(self):
        # Remove AIWF_STATE_ROOT env var patch
        os.environ.pop("AIWF_STATE_ROOT", None)
        # Clean up temp workspace
        shutil.rmtree(self.workspace, ignore_errors=True)

    def load_fixture(self, fixture_path: str) -> dict:
        """
        Load a JSON fixture from tests/fixtures/.
        
        Args:
            fixture_path: Relative path from fixtures/ directory (e.g. 'blueprints/FEAT-999_multi_phase_blueprint.json')
        
        Returns:
            Parsed dict from JSON file.
        
        Raises:
            FileNotFoundError: If fixture file doesn't exist.
        """
        full_path = os.path.join(FIXTURES_DIR, fixture_path)
        if not os.path.exists(full_path):
            raise FileNotFoundError(
                f"Fixture not found: {full_path}\n"
                f"Available fixtures are under: {FIXTURES_DIR}"
            )
        with open(full_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def copy_fixture_workspace(self, fixture_name: str) -> str:
        """
        Copy a fixture state directory into the isolated test workspace.
        Fixture files are always READ from fixtures/; workspace is WRITE destination.
        
        Args:
            fixture_name: Name of state fixture (e.g. 'legacy_session', 'flat_split', 'nested_split')
        
        Returns:
            Path to the copied state root in the workspace.
        """
        fixture_state_dir = os.path.join(FIXTURES_DIR, "state", fixture_name)
        if not os.path.exists(fixture_state_dir):
            raise FileNotFoundError(
                f"State fixture not found: {fixture_state_dir}"
            )
        # Copy fixture state into workspace
        shutil.copytree(
            fixture_state_dir,
            self.workspace,
            dirs_exist_ok=True,
        )
        # Find the new state root
        return self.state_root

    def make_state_dirs(self) -> None:
        """Create all canonical state subdirectories in workspace."""
        for subdir in ["project", "workflow", "runtime", "context", "recovery", "events"]:
            os.makedirs(os.path.join(self.state_root, subdir), exist_ok=True)

    def write_state(self, category: str, data: dict) -> None:
        """
        Write a sub-state JSON file to the workspace.
        Creates subdirectory if needed.
        """
        import json as _json
        subdir = os.path.join(self.state_root, category)
        os.makedirs(subdir, exist_ok=True)
        file_map = {
            "workflow": "workflow.json",
            "runtime": "runtime.json",
            "context": "context.json",
            "project": "profile.json",
            "recovery": "recovery.json",
        }
        filename = file_map.get(category, f"{category}.json")
        path = os.path.join(subdir, filename)
        with open(path, "w", encoding="utf-8") as f:
            _json.dump(data, f, indent=2)

    def read_dashboard(self) -> dict:
        """Load the current dashboard.json from workspace, or {} if missing."""
        import json as _json
        path = os.path.join(self.state_root, "dashboard.json")
        if not os.path.exists(path):
            return {}
        with open(path, "r", encoding="utf-8") as f:
            return _json.load(f)

    def make_ledger_blueprint(
        self,
        feature_id: str = "FEAT-TEST",
        n_phases: int = 2,
        tasks_per_phase: int = 2,
    ) -> dict:
        """
        Generate a minimal blueprint JSON for ledger testing.
        """
        packages = []
        for phase_n in range(1, n_phases + 1):
            for task_n in range(1, tasks_per_phase + 1):
                task_id = f"Task {phase_n}.{task_n}"
                deps = []
                if task_n > 1:
                    deps = [f"Task {phase_n}.{task_n - 1}"]
                elif phase_n > 1:
                    deps = [f"Task {phase_n - 1}.{tasks_per_phase}"]
                packages.append({
                    "task_id": task_id,
                    "module": f"Phase {phase_n}",
                    "write_set": [f"src/module_{phase_n}_{task_n}.py"],
                    "dependencies": deps,
                    "implementation_notes": f"Implement task {task_id}",
                    "verification": f"python -m pytest tests/test_{phase_n}_{task_n}.py",
                    "expected_outputs": [f"src/module_{phase_n}_{task_n}.py"],
                })
        return {
            "feature_id": feature_id,
            "feature_name": f"Test Feature {feature_id}",
            "implementation_packages": packages,
        }
