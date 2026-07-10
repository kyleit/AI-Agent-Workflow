<!-- File path: docs/designs/FIX-021_phase6_ui_redesign_and_api_audit_blueprint.md -->
---
artifact_type: blueprint
issue_id: FIX-021
workflow: quick-fix
status: draft
---
# Technical Design Blueprint – Phase 6 UI Redesign and API Usage Audit

## 1. Proposed Code Changes

### [skills/workflow-runtime/scripts/db.py](file:///e:/AgentsProject/skills/workflow-runtime/scripts/db.py) (and [.agents/skills/workflow-runtime/scripts/db.py](file:///e:/AgentsProject/.agents/skills/workflow-runtime/scripts/db.py))
- **Operation**: MODIFY
- **Responsibility**: Prevent duplicate timeline events from logging. Clean up existing duplicates in `timeline_events`.
- **Changes**:
  - In `save_timeline_event(event)`:
    - Add a check at the beginning: if `event.get("request_id")` is provided, query `timeline_events` to check if a record with the same `request_id` already exists. If yes, skip the insertion.
  - In `init_db_schema(conn)`:
    - Run an automatic cleanup query to delete duplicate timeline events:
      `DELETE FROM timeline_events WHERE request_id IS NOT NULL AND id NOT IN (SELECT MIN(id) FROM timeline_events WHERE request_id IS NOT NULL GROUP BY request_id)`

### [skills/workflow-runtime/scripts/workflow_runtime.py](file:///e:/AgentsProject/skills/workflow-runtime/scripts/workflow_runtime.py) (and [.agents/skills/workflow-runtime/scripts/workflow_runtime.py](file:///e:/AgentsProject/.agents/skills/workflow-runtime/scripts/workflow_runtime.py))
- **Operation**: MODIFY
- **Responsibility**: Fix swapped argument positions for `sync_request_history` in CLI commands.
- **Changes**:
  - In the `timeline` subcommand handler (around line 931):
    - Replace `sync_request_history(session.get("project_id"), conv_id)` with `sync_request_history(conv_id, session.get("project_id") or get_project_id())`.
  - In the `forecast` subcommand handler (around line 958):
    - Replace `sync_request_history(session.get("project_id"), conv_id)` with `sync_request_history(conv_id, session.get("project_id") or get_project_id())`.

### [skills/workflow-runtime/scripts/context.py](file:///e:/AgentsProject/skills/workflow-runtime/scripts/context.py)
- **Operation**: MODIFY
- **Responsibility**: Sync with `.agents/skills/workflow-runtime/scripts/context.py` which contains corrected `conversation_id` detection functions.
- **Changes**: Overwrite entire file contents with `.agents/skills/workflow-runtime/scripts/context.py`.

### [skills/workflow-runtime/scripts/workflow_state.py](file:///e:/AgentsProject/skills/workflow-runtime/scripts/workflow_state.py)
- **Operation**: MODIFY
- **Responsibility**: Sync with `.agents/skills/workflow-runtime/scripts/workflow_state.py` which contains corrected context usage update on resume.
- **Changes**: Overwrite entire file contents with `.agents/skills/workflow-runtime/scripts/workflow_state.py`.

### [extensions/visualizer/resources/webview.html](file:///e:/AgentsProject/extensions/visualizer/resources/webview.html)
- **Operation**: MODIFY
- **Responsibility**: Implement premium visual enhancements, responsive tab layout, tab icons, and correct formatting/conversions.
- **Changes**:
  - Update `formatTokens` function:
    - If token count is 1 Billion or more, format as `B` with 2 decimal places.
    - If token count is 1 Million or more, format as `M` with 2 decimal places.
    - If token count is 1 Thousand or more, format as `K` with 1 decimal place.
  - Redesign Navigation tab buttons:
    - Embed custom SVG icons (Workflow, Insights, Timeline, Budget, Context, Optimize).
    - Add styles for active transitions (neon indicator line, hover scale).
    - Ensure tabs bar wraps cleanly or uses a scrollbar layout if horizontal viewport is constrained.

### [extensions/visualizer/src/webviewHtml.ts](file:///e:/AgentsProject/extensions/visualizer/src/webviewHtml.ts)
- **Operation**: MODIFY
- **Responsibility**: Keep compiled TS representation of HTML output in sync.
- **Changes**: Regenerate automatically by running build pipeline (`node build.js` in `extensions/visualizer/`).

## 2. Target Folder Structure
The workspace file layout remains structural and unchanged:
```text
.
├── .agents/
│   └── skills/
│       └── workflow-runtime/
│           └── scripts/
│               ├── context.py
│               ├── db.py
│               ├── workflow_runtime.py
│               └── workflow_state.py
├── skills/
│   └── workflow-runtime/
│       └── scripts/
│           ├── context.py
│           ├── db.py
│           ├── workflow_runtime.py
│           └── workflow_state.py
└── extensions/
    └── visualizer/
        ├── resources/
        │   └── webview.html
        └── src/
            └── webviewHtml.ts
```

## 3. Interface & Data Contracts
No new REST or database contracts are introduced. The standard SQL schema for `timeline_events` remains intact, with duplicate rows cleaned up.

## 4. Key Logic

### Prevent Duplicate timeline_events
```python
if event.get("request_id"):
    cursor.execute(
        "SELECT 1 FROM timeline_events WHERE request_id = ? AND event_type = 'Provider request'",
        (event["request_id"],)
    )
    if cursor.fetchone():
        # Duplicate request event, skip writing
        return
```

### formatTokens JavaScript Refactoring
```javascript
function formatTokens(num) {
    if (num === undefined || num === null) return "0";
    const val = Number(num);
    if (val >= 1000000000) return (val / 1000000000).toFixed(2) + "B";
    if (val >= 1000000) return (val / 1000000).toFixed(2) + "M";
    if (val >= 1000) return (val / 1000).toFixed(1) + "K";
    return val.toString();
}
```

## 5. Verification & Test Plan
- Run python unit tests: `python -m unittest skills/workflow-runtime/tests/test_request_history.py`
- Run custom verification script to verify that:
  1. Swapped CLI arguments execute properly.
  2. `timeline_events` duplicate rows are pruned.
  3. Visualizer parses webview HTML and compiles without syntax errors.
