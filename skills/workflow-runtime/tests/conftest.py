# conftest.py -- QUICK-038: standardized to python -m workflow_runtime entry point
import os
import sys
import shutil
import tempfile
import subprocess
import importlib.util
import pytest

ORIG_CWD = os.getcwd()

# Absolute path to skills/workflow-runtime (where workflow_runtime package lives)
# conftest.py is at: skills/workflow-runtime/tests/conftest.py
# so the package root is two levels up from tests/
_CONFTEST_DIR = os.path.dirname(os.path.abspath(__file__))
_RUNTIME_PKG_ROOT = os.path.abspath(os.path.join(_CONFTEST_DIR, ".."))

# The runtime was migrated from a flat module layout to a package layout, but
# older tests still import the former module names. Registering these aliases
# at collection time keeps those tests executable without weakening production
# imports or adding legacy directories to PYTHONPATH.
_LEGACY_MODULE_ALIASES = {
    "session_core": "workflow_runtime.infrastructure.session.session_core",
    "event_store": "workflow_runtime.infrastructure.persistence.event_store",
    "logical_agent": "workflow_runtime.domain.agent.logical_agent",
    "logical_scheduler": "workflow_runtime.application.workflow.logical_scheduler",
    "external_executor": "workflow_runtime.application.use_cases.external_executor",
    "permission_boundary": "workflow_runtime.domain.security.permission_boundary",
    "websocket_server": "workflow_runtime.infrastructure.network.websocket_server",
    "runtime_sdk": "workflow_runtime.application.api.runtime_sdk",
    "session": "workflow_runtime.infrastructure.session.session",
    "event_logger": "workflow_runtime.infrastructure.events.event_logger",
    "event_reducer": "workflow_runtime.infrastructure.events.event_reducer",
    "state_path": "workflow_runtime.infrastructure.session.state_path",
    "atomic_writer": "workflow_runtime.infrastructure.filesystem.atomic_writer",
    "db": "workflow_runtime.infrastructure.persistence.db",
    "skill_router": "workflow_runtime.application.skills.skill_router",
    "skill_migration": "workflow_runtime.application.skills.skill_migration",
    "sandbox_container_execution_provider": "workflow_runtime.infrastructure.execution.sandbox_container_execution_provider",
    "validation_runtime_engine": "workflow_runtime.application.verification.validation_runtime_engine",
    "virtual_filesystem_overlay": "workflow_runtime.infrastructure.filesystem.virtual_filesystem_overlay",
    "compatibility_adapter": "workflow_runtime.infrastructure.compatibility.compatibility_adapter",
    "token_scheduler_context_compressor": "workflow_runtime.application.analysis.token_scheduler_context_compressor",
    "evidence_gate_engine": "workflow_runtime.application.verification.evidence_gate_engine",
    "auto_transition_controller": "workflow_runtime.application.workflow.auto_transition_controller",
    "workflow_state_machine": "workflow_runtime.application.workflow.workflow_state_machine",
    "agent_dispatcher": "workflow_runtime.application.agent.agent_dispatcher",
    "workflow_supervisor": "workflow_runtime.application.workflow.workflow_supervisor",
    "workspace_context_isolation": "workflow_runtime.domain.security.workspace_context_isolation",
    "transaction_rollback_state_reversion": "workflow_runtime.domain.security.transaction_rollback_state_reversion",
    "runtime_infrastructure_observability": "workflow_runtime.infrastructure.events.runtime_infrastructure_observability",
    "secure_cryptographic_token_authorization": "workflow_runtime.domain.security.secure_cryptographic_token_authorization",
    "session_bootstrap_guard": "workflow_runtime.infrastructure.session.session_bootstrap_guard",
    "provider_data": "workflow_runtime.presentation.cli.commands._impl.provider.provider_data",
    "update_source": "workflow_runtime.application.system.update_source",
    "validator": "workflow_runtime.application.verification.validator",
    "context_engine": "workflow_runtime.application.analysis.context_engine",
    "code_size_governor": "workflow_runtime.application.workflow.code_size_governor",
    "task_orchestrator": "workflow_runtime.application.use_cases.task_orchestrator",
    "task_graph_engine": "workflow_runtime.application.workflow.task_graph_engine",
    "workflow_entry_gateway": "workflow_runtime.application.workflow.workflow_entry_gateway",
    "execution_manager": "workflow_runtime.application.use_cases.execution_manager",
    "capacity_controller": "workflow_runtime.infrastructure.execution.capacity_controller",
    "checkpoint": "workflow_runtime.infrastructure.persistence.checkpoint",
    "state_store": "workflow_runtime.infrastructure.session.state_store",
    "state_sync": "workflow_runtime.infrastructure.session.state_sync",
    "post_release_lifecycle": "workflow_runtime.application.workflow.post_release_lifecycle",
    "aiwf_registry": "workflow_runtime.application.workflow.aiwf_registry",
    "utils": "workflow_runtime.shared.utils",
    "normalizer": "workflow_runtime.shared.normalizer",
    "agent_routing": "workflow_runtime.domain.agent.agent_routing",
    "drift": "workflow_runtime.shared.drift",
    "heartbeat": "workflow_runtime.infrastructure.events.heartbeat",
    "cli_runner": "workflow_runtime.application.use_cases.cli_runner",
    "confidence_gate": "workflow_runtime.application.verification.confidence_gate",
    "artifact_governance": "workflow_runtime.application.docs.artifact_governance",
    "connectors": "workflow_runtime.infrastructure.connectors",
    "fingerprint": "workflow_runtime.application.analysis.fingerprint",
    "fingerprint_engine": "workflow_runtime.application.analysis.fingerprint_engine",
    "safe_multi_agent_writes": "workflow_runtime.application.security.safe_multi_agent_writes",
    "test_enforcer": "workflow_runtime.application.verification.test_enforcer",
    "cost_engine": "workflow_runtime.application.analytics.cost_engine",
    "usage_validator": "workflow_runtime.application.verification.usage_validator",
    "validation_runner": "workflow_runtime.application.verification.validation_runner",
    "context": "workflow_runtime.domain.core.context",
    "breakdown_engine": "workflow_runtime.application.analysis.breakdown_engine",
    "compatibility_migration_adapter": "workflow_runtime.infrastructure.compatibility.compatibility_migration_adapter",
    "cost_optimizer_model_router": "workflow_runtime.application.analytics.cost_optimizer_model_router",
    "dependency_resolver": "workflow_runtime.application.dependency.dependency_resolver",
    "diff_engine": "workflow_runtime.application.analysis.diff_engine",
    "forecaster": "workflow_runtime.application.analytics.forecaster",
    "global_knowledge_graph": "workflow_runtime.application.analysis.global_knowledge_graph",
    "insights_engine": "workflow_runtime.application.analytics.insights_engine",
    "optimizer": "workflow_runtime.application.analytics.optimizer",
    "plugin_marketplace_engine": "workflow_runtime.application.plugins.plugin_marketplace_engine",
    "remote_execution_federation_platform": "workflow_runtime.infrastructure.execution.remote_execution_federation_platform",
    "telegram_daemon": "workflow_runtime.infrastructure.telegram.daemon",
    "ast_incremental_parser_engine": "workflow_runtime.application.analysis.ast_incremental_parser_engine",
    "context_compressor_engine": "workflow_runtime.application.analysis.context_compressor_engine",
    "context_rebuilder": "workflow_runtime.application.analysis.context_rebuilder",
    "test_coordinator": "workflow_runtime.application.verification.test_coordinator",
    "coordinator": "workflow_runtime.application.workflow.coordinator_compat",
    "budget_controller": "workflow_runtime.application.analytics.budget_controller",
    "autonomous_orchestrator": "workflow_runtime.application.use_cases.autonomous_orchestrator",
    "transcript_engine": "workflow_runtime.application.docs.transcript_engine",
    "analytics_engine": "workflow_runtime.application.analytics.analytics_engine",
}

for _legacy_name, _canonical_name in _LEGACY_MODULE_ALIASES.items():
    try:
        sys.modules.setdefault(_legacy_name, __import__(_canonical_name, fromlist=["*"]))
    except Exception:
        # A failing optional import remains visible as a real collection error;
        # this shim must never turn a broken module into a false pass.
        pass

# Legacy integration tests import RuntimeTestBase from the test-root conftest.
# Keep that import stable while the shared base remains in fixtures/conftest.py.
_FIXTURE_CONFTEST = os.path.join(_CONFTEST_DIR, "fixtures", "conftest.py")
_fixture_spec = importlib.util.spec_from_file_location("aiwf_test_fixtures_conftest", _FIXTURE_CONFTEST)
if _fixture_spec and _fixture_spec.loader:
    _fixture_module = importlib.util.module_from_spec(_fixture_spec)
    _fixture_spec.loader.exec_module(_fixture_module)
    RuntimeTestBase = _fixture_module.RuntimeTestBase


def run_cli(
    *args: str,
    cwd: str | None = None,
    capture_output: bool = True,
    text: bool = True,
    env: dict | None = None,
    **kwargs,
) -> subprocess.CompletedProcess:
    """Run `python -m workflow_runtime <args>` as subprocess.

    PYTHONPATH is automatically set to `skills/workflow-runtime`
    (resolved relative to this conftest.py) so the module is resolvable
    regardless of where pytest is launched from.
    """
    if len(args) == 1 and isinstance(args[0], (list, tuple)):
        args = tuple(str(item) for item in args[0])
    base_env = os.environ.copy()
    base_env["PYTHONPATH"] = _RUNTIME_PKG_ROOT + os.pathsep + base_env.get("PYTHONPATH", "")
    if env:
        base_env.update(env)
    return subprocess.run(
        [sys.executable, "-m", "workflow_runtime", *args],
        cwd=cwd or os.getcwd(),
        capture_output=capture_output,
        text=text,
        env=base_env,
        **kwargs,
    )


@pytest.fixture(autouse=True, scope="function")
def isolated_workspace():
    previous_state_root = os.environ.pop("AIWF_STATE_ROOT", None)
    # 1. Create a unique isolated root directory under OS temp
    temp_workspace = tempfile.mkdtemp(prefix="aiwf-test-ws-")

    # 2. Replicate the necessary .agents folder structure
    src_agents = os.path.abspath(os.path.join(ORIG_CWD, ".agents"))
    dst_agents = os.path.join(temp_workspace, ".agents")

    if os.path.exists(src_agents):
        os.makedirs(dst_agents, exist_ok=True)
        for item in os.listdir(src_agents):
            s = os.path.join(src_agents, item)
            d = os.path.join(dst_agents, item)
            # Skip states, locks, and history database to ensure a clean slate
            if item in ["state", "runtime", "memory-state.json", "history.db"]:
                continue
            try:
                if os.path.isdir(s):
                    shutil.copytree(s, d, dirs_exist_ok=True)
                else:
                    shutil.copy2(s, d)
            except Exception:
                pass

    # Replicate root agents, skills, and templates folders for test execution dependencies
    for root_dir in ["agents", "skills", "templates"]:
        src_dir = os.path.join(ORIG_CWD, root_dir)
        if os.path.exists(src_dir):
            try:
                shutil.copytree(src_dir, os.path.join(temp_workspace, root_dir), dirs_exist_ok=True)
            except Exception:
                pass

    # Copy root scripts and manifests needed by installers/tests
    for root_file in ["install.ps1", "install.sh", "update.ps1", "update.sh", "AGENTS.md", "AI_RULES.md", "MANIFEST.json"]:
        src_file = os.path.join(ORIG_CWD, root_file)
        if os.path.exists(src_file):
            try:
                shutil.copy2(src_file, os.path.join(temp_workspace, root_file))
            except Exception:
                pass

    # 3. Change directory to the isolated workspace
    os.chdir(temp_workspace)

    # Reset state store singleton to force re-initialization relative to new CWD
    try:
        from workflow_runtime.infrastructure.session.session import reset_state_store
        reset_state_store(None)
    except Exception:
        pass

    yield temp_workspace

    # Restore original CWD
    os.chdir(ORIG_CWD)

    # Clean up isolated state folder
    try:
        shutil.rmtree(temp_workspace, ignore_errors=True)
    except Exception:
        pass
    if previous_state_root is not None:
        os.environ["AIWF_STATE_ROOT"] = previous_state_root
