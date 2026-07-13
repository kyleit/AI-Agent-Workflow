# FEAT-314 Session Bootstrap Middleware & Workflow Runtime Auto Initialization Report

This report documents the implementation of the AIWF Session Bootstrap Middleware, ensuring seamless session-based workspace preparation and automatic workflow request execution.

## 1. Architecture Change

Before this implementation, users had to manually run initialization steps (`initialize-workspace` or `aiwf init`) in a new IDE conversation session. If skipped, requests failed with uninitialized states.

We introduced the **`SessionBootstrapGuard`** middleware. This component intercepts every incoming engineering query submitted through `workflow submit`. If it detects the current conversation session is not initialized:
1. It automatically boots up the workspace layout and settings (`initialize-workspace` simulation).
2. It sets and persists the initialization markers.
3. It transparently continues the original user request, avoiding query loss.

---

## 2. State Model

Session bootstrap data is stored and isolated from workflow checkpoints.

### Session State Path
`.agents/state/sessions/{session_id}.json`

### Schema
```json
{
  "session_id": "agy-session-id",
  "initialized": true,
  "initialized_at": "2026-07-13T19:58:13+07:00",
  "workspace_ready": true,
  "runtime_ready": true
}
```

- **Workspace State** (`workspace_ready`): Indicates configuration manifests, permissions, and skill registries are successfully generated.
- **Session State** (`initialized`): Confirms bootstrap middleware completed inside the active conversation.
- **Workflow State**: Manages SDLC feature progress (unaffected by session bootstrap updates).

---

## 3. Execution Flow

The upgraded request execution path:

```text
User Request ("Add Google OAuth login")
      │
      ▼
workflow_runtime.py (workflow submit)
      │
      ▼
SessionBootstrapGuard.handle_request(session_id, request)
      │
      ├─► [initialized == True] ──► Continue original request
      │
      └─► [initialized == False] ─► Run initialize_workspace()
                                         │
                                         ▼
                                    Create scaffolding config/permissions/registries
                                    Set session.initialized = True
                                    Save session state file
                                         │
                                         ▼
                                    Continue original request
      │
      ▼
WorkflowEntryGateway.handle_request()
      │
      ▼
Intent Detection & Workflow Creation (FEAT-xxx)
      │
      ▼
Supervisor starts brainstorming skill
      │
      ▼
Brainstorming artifact auto-generated under docs/brainstorming/
```

---

## 4. Test Results

Unit tests have been compiled under `skills/workflow-runtime/tests/unit/test_session_bootstrap_middleware.py` validating the middleware logic:

```text
skills/workflow-runtime/tests/unit/test_session_bootstrap_middleware.py::test_first_request_initializes PASSED
skills/workflow-runtime/tests/unit/test_session_bootstrap_middleware.py::test_session_isolation PASSED
skills/workflow-runtime/tests/unit/test_session_bootstrap_middleware.py::test_failed_initialization_on_write_error PASSED
skills/workflow-runtime/tests/unit/test_session_bootstrap_middleware.py::test_cli_session_commands PASSED

============================== 4 passed in 1.82s ===============================
```

### Verified Cases:
- **First Request**: Middleware correctly initializes the workspace and persists `"initialized": true` inside the session file.
- **Subsequent Requests**: Auto-initialization is skipped, starting the workflow gateway immediately.
- **Failed Initialization**: Blocks request execution on write failures, returning `SESSION_BOOTSTRAP_FAILED`.
- **Session Isolation**: Session-A and Session-B states are completely decoupled.

---

## 5. Migration Notes & CLI Commands

### New CLI Commands
- `aiwf session status`: Check the active session status.
- `aiwf session initialize`: Force session initialization.
- `aiwf session reset`: Reset the active session initialization flag.

---

## 6. Conclusion
The Session Bootstrap Middleware is ready, ensuring no manual initial commands are required from the user.

```text
AIWF_SESSION_BOOTSTRAP_MIDDLEWARE_READY
```
