# FEAT-315 Antigravity AIWF Workflow Runtime Tool Adapter Report

This report documents the architecture, implementation, tool contracts, security model, and testing verification results for feature **FEAT-315**.

---

## 1. Architecture

We integrated **Antigravity IDE** with the **AIWF Workflow Runtime** using a unified Gateway Tool Adapter pattern. This prevents direct workspace file changes by the LLM agent without an active workflow context, enforcing absolute traceability and safety gates compliance.

```text
    Antigravity IDE
          │
          ▼ (Tools Interface / MCP)
    AntigravityGatewayAdapter
          │
          ▼ (Injects source='antigravity', session_id, execution_mode)
    WorkflowEntryGateway.handle_request()
          │
          ▼
    Workflow Supervisor ──> Skill Router ──> Agents / Sandboxed Tools
```

---

## 2. Tool Contracts & Gateway Integration

### Exposed Tool Interface

- **`aiwf_submit_workflow(task: str, session_id?: str)`**:
  - Automatically bootstraps the session (if needed) using `SessionBootstrapGuard`.
  - Routes the request through `WorkflowEntryGateway`.
  - Excludes general chat/informational requests (`BYPASS` pathway).
  - Returns a standard JSON representation:
    ```json
    {
      "workflow_id": "FEAT-313",
      "status": "STARTED",
      "phase": "brainstorming"
    }
    ```
- **`aiwf_workflow_status(workflow_id: str)`**: Checks status and active phase.
- **`aiwf_workflow_agents(workflow_id: str)`**: Retrieves allocated agent configuration.
- **`aiwf_workflow_timeline(workflow_id: str)`**: Aggregates event history from `events.jsonl`.
- **`aiwf_workflow_follow(workflow_id: str, last_event_id: int)`**: Streams newly appended logs.

---

## 3. Security & Execution Block Model

Direct execution of workspace modification tools is gated at two levels:

1. **ToolExecutor Boundary**: Intercepts tool calls and throws `PermissionError("EXECUTION_BLOCKED")` if the local session does not have `execution_mode == "workflow"` and a valid `workflow_id` set (unless in explicit testing environment).
2. **AI Rules Constraint**: Mandatory rule added to `AI_RULES.md` stating that any code-modifying agent action MUST start with a call to `aiwf_submit_workflow()`.

---

## 4. Test Verification Results

We verified the integration using `test_antigravity_workflow_adapter.py`:

- **`test_feature_request_flow`**: Validated that submitting `"Add Google OAuth login"` correctly initializes session metadata, injects `"source": "antigravity"`, creates the required bootstrapping artifact (`docs/brainstorming/FEAT-313.md`), and returns standard JSON.
- **`test_direct_coding_block`**: Validated that direct tool calls outside of a managed workflow throw `EXECUTION_BLOCKED` and raise security violations.
- **`test_session_reuse`**: Validated that subsequent engineering requests reuse the existing initialized session instead of forcing a restart.

**All integration tests passed successfully.**

```text
============================== 3 passed in 2.08s ===============================
```

---

## 5. MCP Server Configuration

The MCP server adapter is exposed via `aiwf_mcp_server.py`. It communicates over standard `stdin` / `stdout` using JSON-RPC 2.0.

### Installation & Integration Configuration

Add the following config to your Antigravity IDE MCP settings:

```json
{
  "mcpServers": {
    "aiwf-mcp-server": {
      "command": "python3",
      "args": [
        "skills/workflow-runtime/adapters/aiwf_mcp_server.py"
      ],
      "env": {
        "AIWF_EXECUTION_MODE": "workflow"
      }
    }
  }
}
```

### Tool Invocation Example

**Request (tools/call)**:
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "aiwf_submit_workflow",
    "arguments": {
      "task": "Add Google OAuth login"
    }
  },
  "id": 1
}
```

**Response**:
```json
{
  "jsonrpc": "2.0",
  "result": {
    "content": [
      {
        "type": "text",
        "text": "{\n  \"workflow_id\": \"FEAT-313\",\n  \"status\": \"STARTED\",\n  \"phase\": \"brainstorming\"\n}"
      }
    ]
  },
  "id": 1
}
```
