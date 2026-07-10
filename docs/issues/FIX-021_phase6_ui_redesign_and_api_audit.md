<!-- File path: docs/issues/FIX-021_phase6_ui_redesign_and_api_audit.md -->
---
artifact_type: fix-spec
issue_id: FIX-021
workflow: quick-fix
status: pending
---
# Fix Specification – Phase 6 UI Redesign and API Usage Audit

## 1. Issue Description
This fix addresses two core concerns in the companion visualizer panel and workflow runtime:
1. **Visualizer UI Redesign (Phase 6)**: The Budget panel and navigation tabs have visual inconsistencies, lacking premium styling, proper tab icons, and a cohesive design system. Furthermore, we must ensure navigation is fully responsive and elegant.
2. **Accumulated API Usage Audit**: The database currently logs duplicate records in `timeline_events` on every workflow step, leading to inflated token aggregation values over time. Additionally, the forecast/timeline CLI subcommands fail during manual invocation due to swapped arguments (`conversation_id` vs `project_id`). Formatting functions also lack support for B (Billions) and correct decimal representation.

## 2. Scope
- **In Scope**:
  - Update `skills/workflow-runtime/scripts/db.py` (and `.agents` copy) to prevent inserting duplicate `request_id` values in `timeline_events`.
  - Fix swapped parameter positions in `skills/workflow-runtime/scripts/workflow_runtime.py` (and `.agents` copy) for `sync_request_history` calls.
  - Implement a DB cleanup mechanism or query to remove pre-existing duplicates from `timeline_events` table in `project_runtime.db`.
  - Sync outdated root scripts (`context.py`, `workflow_state.py`) with their correct counterpart copies in `.agents/`.
  - Enhance `extensions/visualizer/resources/webview.html` layout:
    - Add SVG icons to navigation tab buttons.
    - Update `formatTokens` to support B (Billions), 2 decimal places for M/B and 1 decimal place for K.
    - Polish dashboard spacing, alignment, and hover transitions.
  - Compile the new UI to `extensions/visualizer/src/webviewHtml.ts` by running `node build.js` in the visualizer directory.
- **Out of Scope**:
  - Database schema restructuring (no table deletion or changing column names).
  - Implementation of new optimization algorithms or policies in `optimizer.py` or `budget_controller.py`.
