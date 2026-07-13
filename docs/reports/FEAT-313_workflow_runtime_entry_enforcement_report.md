# FEAT-313 Workflow Runtime Entry Enforcement Report

This report documents the design, implementation, and verification of the mandatory Workflow Runtime Entry Gateway enforcement under feature **FEAT-313**.

## 1. Old Execution Flow vs New Execution Flow

### Old Execution Flow
Previously, AI agents simulated the workflow execution internally in the LLM. The agent would analyze user queries, suggest manual CLI triggers (e.g. telling the user to run `/brainstorm` or `workflow_runtime.py start`), and directly edit workspace files.
```text
User Request ──> LLM reads skills ──> LLM simulates workflow ──> LLM edits code or prints CLI commands
```
This approach suffered from:
- Lack of execution logs and audit trails.
- Potential bypass of the core AIWF guardrails and safety gates.
- Simulation drift where the actual tool environment state didn't match the agent's internal model.

### New Execution Flow
Every engineering request (such as feature requests, bug fixes, refactoring, migrations, etc.) MUST execute through the unified `workflow_runtime.py` gateway. Normal chat/informational queries remain bypassed to direct LLM response.
```text
User Request
    │
    ▼
workflow_runtime.py workflow submit "<request>"
    │
    ▼ (Intent & Workflow Validation)
WorkflowEntryGateway.handle_request()
    │
    ▼ (Automatic Context Setup: FEAT-xxx, standard-development, brainstorming)
Workflow Supervisor / Skill Router
    │
    ▼ (Execution of Brainstorming Skill)
Automatic Artifact Generation (docs/brainstorming/FEAT-xxx_*.md)
```

---

## 2. Entry Point Design

The entry point is controlled by `WorkflowEntryGateway` which is integrated directly into `workflow_runtime.py workflow submit`.

When a natural language query is submitted:
1. **Intent Classification**: The gateway analyzes engineering keywords to determine if the query represents an engineering action (`feature_request`, `bug_fix`, `refactoring`, `migrations`, `architecture_changes`, `implementation_tasks`) or a simple chat query (`chat`).
2. **Context Creation**: If it's an engineering action, the gateway automatically assigns a sequential `FEAT-xxx` ID by scanning `docs/` directories, configures the `.session.json` context, and updates the core state files (`workflow.json`, `context.json`, `runtime.json`).
3. **Log & Trace**: Trace events are automatically appended to `.agents/state/events.jsonl` to record the entire pipeline start.
4. **Standard Output**: The command prints a standardized JSON response:
   ```json
   {
     "intent": "feature_request",
     "workflow": "standard-development",
     "status": "CREATED"
   }
   ```

---

## 3. Tool Boundary Design

Direct execution of code-modifying tools (like `write_file`, `replace_file_content`) outside of a managed workflow is strictly blocked.

The validation is enforced at two levels:
1. **ToolExecutor (`external_executor.py`)**: Checks if the workspace has a valid `.session.json` with `execution_mode == "workflow"` and a valid `workflow_id` (or corresponding environment variables `AIWF_EXECUTION_MODE` and `AIWF_WORKFLOW_ID` set). If not, raises `PermissionError("EXECUTION_BLOCKED")`.
2. **ExecutionManager (`execution_manager.py`)**: Checks environment context before spawning any sub-processes, returning `valid = False, msg = "EXECUTION_BLOCKED"` on failure.

---

## 4. Tests

We created `skills/workflow-runtime/tests/unit/test_workflow_runtime_entry_enforcement.py` to verify the entry gateway enforcement rules:
- **`test_natural_language_request`**: Verifies that submitting `"Add Google OAuth login"` correctly triggers intent classification, populates session state, emits all lifecycle trace events (`workflow.request.received`, `workflow.created`, `workflow.started`, `skill.selected`, `skill.started`), and allows automatic artifact generation in `docs/brainstorming/`.
- **`test_direct_execution_attempt`**: Verifies that attempts to invoke tools without workflow environment context are blocked with `EXECUTION_BLOCKED`.
- **`test_skill_execution_chain`**: Verifies the automatic routing from `brainstorming` to subsequent SDLC phases.

---

## 5. Migration & Backwards Compatibility Impact

1. **State Directory**: Event log file path is migrated from `.agents/state/events/events.jsonl` to the unified `.agents/state/events.jsonl` root file path to conform with frontend visualizer extension integration.
2. **Backward Compatibility**: Chat-based/informational requests (e.g. "Explain Go interfaces") remain untouched and bypass the gate safely without requiring any workflow context.
3. **IDE / Extension Integration**: VS Code extension integrations must execute `workflow submit` rather than querying the LLM directly for engineering actions, ensuring full compliance.
