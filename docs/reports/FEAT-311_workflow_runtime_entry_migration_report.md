# Architectural Report - FEAT-311 Workflow Runtime Entry Command Migration

## 1. Executive Summary

This report documents the architectural migration of the AI Engineering Workflow Framework (AIWF) execution entry point from the legacy resident orchestrator model to the unified Session-based Workflow Runtime model.

The primary objective is to enforce that every engineering task enters through `workflow_runtime.py`, establishing a consistent entry API across all integrations (IDE, CLI, and Extensions).

## 2. Target Architecture

The workflow runtime has been redesigned to route all execution requests through `workflow_runtime.py` as follows:

```
IDE / Extension / CLI
        |
        +---> workflow_runtime.py (do_workflow)
                    |
                    +---> Workflow Supervisor
                                |
                                +---> Intent Router
                                           |
                                           +---> Skill Router
                                                      |
                                                      +---> Core/Specialist Agents
```

Under this architecture:
- Direct execution via legacy commands is deprecated.
- The `orchestrator run` command internally redirects to the new `workflow submit` entrypoint.
- Lifecycles, states, and event logs are standardized.

## 3. Implemented Components

### 3.1. Unified Entry Gateway (`do_workflow`)
The `workflow` command in `workflow_runtime.py` has been fully extended with the following subcommands:
- `submit`: Auto-detects the next feature ID (`FEAT-XXX`), parses intent, initializes the session state (`workflow.json`, `context.json`, `runtime.json`), and emits lifecycle events.
- `start`: Starts the workflow lifecycle by registering the workflow started event.
- `status`: Outputs the active workflow state.
- `follow`: Follows the runtime step progression.
- `agents`: Prints the list of active agents assigned to the workflow.
- `timeline`: Lists chronological events recorded in the append-only log.
- `cancel`: Cancels the active workflow by updating the resume state.
- `resume`: Continues the workflow by calling `do_resume_action`.

### 3.2. Compatibility Redirection
The legacy `orchestrator run` command has been converted into a compatibility layer. Calling `orchestrator run` prints a deprecation warning and internally invokes the `workflow submit` pipeline to prevent direct workflow bypass.

### 3.3. Standardized Event Types
The append-only event logger (`event_logger.py`) was updated to recognize and validate the `workflow.created` event type, completing the registration of standard gateway lifecycle events.

## 4. Verification & Testing

Verification is conducted using behavioral unit and integration tests located in:
`skills/workflow-runtime/tests/test_workflow_runtime_entry.py`

This ensures that the redirect logic, subcommand parsing, event emission, and status outputs meet the requirements of the v3.2 Mini Spec guidelines.
