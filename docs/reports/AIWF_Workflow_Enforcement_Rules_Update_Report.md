# AIWF Workflow First Enforcement Rules Update Report

This report documents the upgrades made to the AI Engineering Workflow Framework (AIWF) to strictly enforce the **Workflow Supervisor** lifecycle and prevent direct coding bypasses.

---

## Changed Rules & Global Policies

We have updated the canonical [AI_RULES.md](file://./AI_RULES.md), root [AGENTS.md](file://./AGENTS.md), and workspace [AGENTS.md](file://./.agents/AGENTS.md) with **Section 27: Workflow First Enforcement Policy**.

The primary additions include:
1. **Mandatory Workflow Entry Gate**: Engineering requests must enter via the Workflow Supervisor.
2. **Strict Code Modification Controls**: AI is blocked from editing files, modifying configurations, running builds, or running tests before required workflow phases are approved.
3. **Skill Lifecycle Mapping**: Every SDLC phase is strictly mapped to a registered AIWF skill.
4. **Artifact Checkpoints**: Plans, specs, and blueprints are verified at checkpoints. Missing artifacts set the status to `BLOCKED`.
5. **State Separation**: Decoupling workspace status (`READY`) from individual feature workflow states.
6. **Approval Gates**: Enforcing manual confirmations exclusively at Planning, Blueprint, and Release gates, while other phases run autonomously.
7. **AI Response Behavior**: Intent detection must be logged and output before modification begins.
8. **Workflow Trace**: Diagnostic event sequences are outputted to `events.jsonl` under `.agents/state/events/`.

---

## Verification & Validation Results

We created a test suite [test_workflow_enforcement.py](file://./skills/workflow-runtime/tests/test_workflow_enforcement.py) to validate these rules.

### Test Cases Covered:
- **`test_workflow_trigger_enforcement`**: Verifies that requests trigger trace events (`workflow.request.received` and `workflow.started`) written in events log.
- **`test_brainstorming_runs_before_implementation`**: Ensures implementation is blocked when checkpoint level is not reached.
- **`test_required_artifacts_exist`**: Ensures missing blueprint artifact results in a `BLOCKED` state.
- **`test_direct_coding_blocked`**: Validates code modifications are blocked without blueprint approval.
- **`test_workspace_workflow_state_separated`**: Confirms workspace readiness status is decoupled from the feature workflow state.

---

## Migration & Compatibility Impact

- **Resident Orchestrator Deprecation**: The legacy Resident Orchestrator daemon is now officially deprecated. Lightweight Session Runtime + Workflow Supervisor is the default.
- **Bypass Prevention**: Any direct coding attempt without an approved spec/blueprint is automatically intercepted and blocked by the compiler & runtime engine.

## Final Status
```text
AIWF_WORKFLOW_ENFORCEMENT_READY
```
