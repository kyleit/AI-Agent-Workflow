"""Consolidated Python Runtime for AIWF Framework."""

__version__: str = "0.1.0"


# Keep the historical package-level entrypoints importable without importing
# the entire CLI during package initialization. This matters for IDE plugins
# and legacy agents that still use ``from workflow_runtime import ...``.
_COMPAT_EXPORTS = {
    "requires_approval": "workflow_runtime.presentation.cli.workflow_runtime",
    "do_workflow": "workflow_runtime.presentation.cli.workflow_runtime",
    "do_orchestrator": "workflow_runtime.presentation.cli.workflow_runtime",
    "WorkflowObservatoryHTTPHandler": "workflow_runtime.presentation.cli.commands._impl.system.observatory_handler",
    "do_choice": "workflow_runtime.presentation.cli.commands._impl.ui.ui_prompts",
    "do_init": "workflow_runtime.presentation.cli.commands._impl.session.session_init",
    "RuntimeInputGate": "workflow_runtime.presentation.cli.workflow_runtime_shared",
    "ForbiddenAISourceError": "workflow_runtime.shared.errors",
    "InvalidResumeTokenError": "workflow_runtime.shared.errors",
    "do_test_action": "workflow_runtime.presentation.cli.commands._impl.agent.test_runner",
    "do_runtime_action": "workflow_runtime.presentation.cli.commands._impl.system.runtime_bus",
}


def __getattr__(name: str):
    module_name = _COMPAT_EXPORTS.get(name)
    if module_name is None:
        raise AttributeError(name)
    from importlib import import_module

    value = getattr(import_module(module_name), name)
    globals()[name] = value
    return value


__all__ = ["__version__", *_COMPAT_EXPORTS]
