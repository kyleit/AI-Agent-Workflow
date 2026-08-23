from __future__ import annotations

from workflow_runtime.presentation.cli.registry import CommandRegistry


def build_registry() -> CommandRegistry:
    """
    Build and return a fully-populated CommandRegistry.
    All 21 command modules are imported and registered here.
    """
    from . import agent_commands  # analysis-agent
    from . import \
        config_commands  # config, permission(+permissions), rules, registry
    from . import dependency_commands  # deps, dependency, merge, conflict
    from . import docs_commands  # cleanup, migrate(+migration)
    from . import execution_commands  # execution, runtime
    from . import init_command  # init
    from . import knowledge_commands  # knowledge, search
    from . import memory_commands  # memory, env, mail
    from . import provider_command  # provider
    from . import \
        session_commands  # start, step, complete, fail, heartbeat, status, resume, lock
    from . import session_meta_commands  # session
    from . import \
        system_commands  # api-server, doctor, notify, debug, verify, release
    from . import task_commands  # task, blueprint, suggest, compact,
    from . import telegram_commands  # telegram
    from . import testing_commands  # test
    from . import ui_commands  # prompt, input, choice
    from . import update_commands  # update, update-source
    from . import usage_command  # usage
    from . import validation_commands  # validate, context, state
    from . import visual_commands  # visual (+vir, +var)
    from . import \
        workflow_commands  # routing, discover, classify, orchestrator(+orchestrate); work-item, project, implement; workflow, active-workflow, coordinator, dispatch,

    _modules = [
        session_commands,
        init_command,
        validation_commands,
        usage_command,
        session_meta_commands,
        workflow_commands,
        task_commands,
        dependency_commands,
        config_commands,
        execution_commands,
        agent_commands,
        ui_commands,
        memory_commands,
        knowledge_commands,
        visual_commands,
        telegram_commands,
        provider_command,
        docs_commands,
        system_commands,
        update_commands,
        testing_commands,
    ]

    registry = CommandRegistry()
    for module in _modules:
        for cmd in module.all_commands():
            registry.register(cmd)
    return registry
