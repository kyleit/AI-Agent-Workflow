# tia_engine.py
import os
import subprocess
import sys

SOURCE_TO_TEST_MAP = {
    "agent_routing.py": ["test_routing.py"],
    "aiwf_registry.py": ["test_registry.py"],
    "analytics_engine.py": ["test_breakdown.py"],
    "approval_gate.py": ["test_phase_completion_gate.py"],
    "artifact_validator.py": ["test_catalog.py"],
    "artifact_writer.py": ["test_catalog.py"],
    "benchmark_init_flow.py": ["test_smoke.py"],
    "breakdown_engine.py": ["test_breakdown.py"],
    "budget_controller.py": ["test_budget_controller.py"],
    "checkpoint.py": ["test_runtime.py"],
    "context.py": ["test_request_history.py", "test_runtime.py"],
    "context_rebuilder.py": ["test_context_rebuilder.py"],
    "db.py": ["test_permissions.py", "test_state_engine.py", "test_request_history.py", "test_lock.py"],
    "dependency_resolver.py": ["test_deps_fix.py"],
    "diff_engine.py": ["test_diff_engine.py"],
    "drift.py": ["test_runtime.py"],
    "environment_health.py": ["test_runtime.py"],
    "fingerprint.py": ["test_runtime.py"],
    "forecaster.py": ["test_forecaster.py"],
    "heartbeat.py": ["test_runtime.py"],
    "insights_engine.py": ["test_insights_engine.py"],
    "lease.py": ["test_lock.py", "test_runtime.py"],
    "optimizer.py": ["test_optimizer.py"],
    "patch_skill_requirements.py": ["test_deps_fix.py"],
    "permission_mode.py": ["test_permissions.py"],
    "project_discovery.py": ["test_project_memory.py"],
    "release_manager.py": ["test_script_first.py"],
    "session.py": ["test_permissions.py", "test_state_engine.py", "test_runtime.py"],
    "skill_classifier.py": ["test_script_first.py"],
    "state_store.py": ["test_state_engine.py", "test_runtime.py"],
    "state_sync.py": ["test_state_engine.py", "test_agents_merge.py"],
    "task_orchestrator.py": ["test_next_ready_task.py", "test_task_dependency_graph.py", "test_task_state_machine.py"],
    "tia_engine.py": ["test_smoke.py"],
    "utils.py": ["test_smoke.py"],
    "validation_runner.py": ["test_script_first.py"],
    "validator.py": ["test_lightweight_initialize.py"],
    "workflow_runtime.py": ["test_lightweight_initialize.py", "test_runtime.py", "test_permissions.py"],
    "workflow_state.py": ["test_script_first.py"],
    "cache.py": ["test_cache.py"],
    "obsidian_resolver.py": ["test_knowledge_runtime.py"],
    "qdrant_client.py": ["test_qmd.py"],
    "analyzer.py": ["test_knowledge_runtime.py"],
    "api.py": ["test_runtime_api.py", "test_knowledge_runtime.py"],
    "index.py": ["test_knowledge_runtime.py"],
    "provider_manager.py": ["test_provider_manager.py"],
    "base.py": ["test_provider_manager.py"],
    "markdown.py": ["test_provider_manager.py"],
    "obsidian.py": ["test_provider_manager.py"],
    "sqlite.py": ["test_provider_manager.py"],
    "vector.py": ["test_provider_manager.py"],
    "bootstrap.py": ["test_project_memory.py"],
    "cli.py": ["test_project_memory.py"],
    "common.py": ["test_project_memory.py"],
    "config.py": ["test_project_memory.py"],
    "dependency_graph.py": ["test_project_memory.py"],
    "filesystem.py": ["test_project_memory.py"],
    "git_diff.py": ["test_project_memory.py"],
    "json_writer.py": ["test_project_memory.py"],
    "keyword_index.py": ["test_project_memory.py"],
    "markdown_writer.py": ["test_project_memory.py"],
    "parser.py": ["test_project_memory.py"],
    "scanner.py": ["test_project_memory.py"],
    "search.py": ["test_project_memory.py"],
    "sqlite_writer.py": ["test_project_memory.py"],
    "update.py": ["test_project_memory.py"],
    "vector_manifest.py": ["test_project_memory.py"]
}

class TestImpactResolver:
    def __init__(self, workspace_root: str = "."):
        self.workspace_root = os.path.abspath(workspace_root)

    def get_git_changed_files(self) -> list[str]:
        changed = set()
        try:
            # 1. Uncommitted changes
            out = subprocess.check_output(
                ["git", "status", "--porcelain"],
                cwd=self.workspace_root,
                stderr=subprocess.DEVNULL
            ).decode("utf-8")
            for line in out.splitlines():
                if len(line) > 3:
                    path = line[3:].strip()
                    changed.add(path)
            
            # 2. Changes in latest commit (HEAD)
            out_head = subprocess.check_output(
                ["git", "diff", "--name-only", "HEAD~1", "HEAD"],
                cwd=self.workspace_root,
                stderr=subprocess.DEVNULL
            ).decode("utf-8")
            for line in out_head.splitlines():
                if line.strip():
                    changed.add(line.strip())
        except Exception:
            pass
        return list(changed)

    def resolve_affected_tests(self, changed_files: list[str]) -> list[str]:
        # Always include smoke tests
        affected = {
            "skills/workflow-runtime/tests/smoke/test_smoke.py",
            "skills/knowledge-runtime/tests/smoke/test_runtime_api.py"
        }
        
        # Filter changed files to ignore public_export and .agents
        filtered_changes = []
        for f in changed_files:
            norm_f = f.replace("\\", "/").strip()
            if norm_f.startswith(("public_export/", ".agents/", "tools/")):
                continue
            filtered_changes.append(norm_f)
            
        if not filtered_changes:
            return list(affected)
            
        # Check if only doc files changed
        doc_extensions = (".md", ".json", ".txt", ".png", ".jpg", ".sh", ".ps1")
        if all(f.endswith(doc_extensions) for f in filtered_changes):
            return list(affected)
            
        for norm_f in filtered_changes:
            name = os.path.basename(norm_f)
            
            # If a test file itself changes, run it
            if name.startswith("test_") and name.endswith(".py"):
                affected.add(norm_f)
                continue
                
            # Map source changes
            if name in SOURCE_TO_TEST_MAP:
                for test_name in SOURCE_TO_TEST_MAP[name]:
                    found = False
                    for test_dir in ["skills/workflow-runtime/tests", "skills/knowledge-runtime/tests"]:
                        target_dir = os.path.join(self.workspace_root, test_dir)
                        if os.path.exists(target_dir):
                            for root, _, files in os.walk(target_dir):
                                if test_name in files:
                                    rel_path = os.path.relpath(os.path.join(root, test_name), self.workspace_root)
                                    affected.add(rel_path.replace("\\", "/"))
                                    found = True
                    if not found:
                        affected.add(f"skills/workflow-runtime/tests/unit/{test_name}")
                        
        return list(affected)


def validate_test_architecture(workspace_root: str = ".") -> dict:
    errors = []
    workspace_root = os.path.abspath(workspace_root)
    
    # 1. Approved directories
    approved_dirs = {"smoke", "unit", "integration", "concurrency", "e2e", "stateful", "performance"}
    
    test_files = [] # Tuples of (filepath, basename, parent_dir_name)
    found_test_basenames = set()
    duplicate_basenames = set()
    
    # Find all test files
    for skill_name in ["workflow-runtime", "knowledge-runtime"]:
        tests_path = os.path.join(workspace_root, "skills", skill_name, "tests")
        if os.path.exists(tests_path):
            for root, dirs, files in os.walk(tests_path):
                # Skip __pycache__
                if "__pycache__" in dirs:
                    dirs.remove("__pycache__")
                for file in files:
                    if file.startswith("test_") and file.endswith(".py"):
                        filepath = os.path.join(root, file)
                        parent_dir = os.path.basename(root)
                        test_files.append((filepath, file, parent_dir))
                        if file in found_test_basenames:
                            duplicate_basenames.add(file)
                        found_test_basenames.add(file)
                        
    # Check duplicate tests
    if duplicate_basenames:
        for dup in duplicate_basenames:
            errors.append(f"Duplicate test file name exists: {dup}")
            
    # Check directory and category markers
    for filepath, file, parent_dir in test_files:
        if parent_dir not in approved_dirs:
            errors.append(f"Test file is outside approved folders: {os.path.relpath(filepath, workspace_root)} (parent: '{parent_dir}')")
            continue
            
        # Check pytest marker
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            expected_marker = f"pytest.mark.{parent_dir}"
            if expected_marker not in content and f"pytestmark = pytest.mark.{parent_dir}" not in content:
                errors.append(f"Test file lacks expected marker '@pytest.mark.{parent_dir}': {os.path.relpath(filepath, workspace_root)}")
        except Exception as e:
            errors.append(f"Failed to read test file {file}: {e}")
            
    # Check obsolete mappings
    for src, tests in SOURCE_TO_TEST_MAP.items():
        for test in tests:
            if test not in found_test_basenames:
                errors.append(f"Obsolete mapping: {src} maps to non-existent test file '{test}'")
                
    # Check source file mapping
    # Scan workflow-runtime/scripts and knowledge-runtime/scripts
    source_files = []
    for skill_name in ["workflow-runtime", "knowledge-runtime"]:
        scripts_path = os.path.join(workspace_root, "skills", skill_name, "scripts")
        if os.path.exists(scripts_path):
            for root, dirs, files in os.walk(scripts_path):
                if "__pycache__" in dirs:
                    dirs.remove("__pycache__")
                for file in files:
                    if file.endswith(".py") and file != "__init__.py":
                        # For subfolders, include subpath if needed or just basename
                        source_files.append(file)
                        
    for src in source_files:
        if src not in SOURCE_TO_TEST_MAP:
            errors.append(f"Source file has no impact mapping: {src}")
            
    if errors:
        return {"status": "failure", "errors": errors}
    return {"status": "success", "errors": []}
