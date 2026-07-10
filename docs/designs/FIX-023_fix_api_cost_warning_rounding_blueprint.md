<!-- File path: docs/designs/FIX-023_fix_api_cost_warning_rounding_blueprint.md -->
---
artifact_type: blueprint
issue_id: FIX-023
workflow: quick-fix
status: draft
---
# Technical Design Blueprint – Adjust API Cost Warning Thresholds and Round Cost Values

## 1. Proposed Code Changes

### [workflow_runtime.py](file:///Volumes/Kyle/AgentsProject/skills/workflow-runtime/scripts/workflow_runtime.py)
- **Operation**: MODIFY
- **Responsibility**: Centralized CLI tool logic. Updates default cost thresholds.
- **Changes**: Update `cost_thresholds` dictionary default values in the telemetry config schema (line 134-137) to:
  ```python
  "cost_thresholds": {
      "warning_usd": 50.0,
      "critical_usd": 100.0
  }
  ```

### [.agents/skills/workflow-runtime/scripts/workflow_runtime.py](file:///Volumes/Kyle/AgentsProject/.agents/skills/workflow-runtime/scripts/workflow_runtime.py)
- **Operation**: MODIFY
- **Responsibility**: Copied workspace CLI runtime controller. Matches the root CLI tool changes.
- **Changes**: Match the updates to default cost thresholds (line 134-137).

### [webview.html](file:///Volumes/Kyle/AgentsProject/extensions/visualizer/resources/webview.html)
- **Operation**: MODIFY
- **Responsibility**: Webview frontend template rendering logic.
- **Changes**:
  - Update local fallback `costThresholds` defaults to `warning_usd: 50.0, critical_usd: 100.0` (line 3367).
  - Use `formatCost(accCost)` instead of `accCost.toFixed(4)` inside costAlertMsgs pushes (lines 3443, 3446).
  - Use `formatCost(duplicateSavings)` instead of `duplicateSavings.toFixed(4)` inside redundant reads alert (line 3450).

## 2. Target Folder Structure
No directory structure changes.

## 3. Interface & Data Contracts
No API/CLI interface signature changes. Default values returned in active-session JSON telemetry payloads are altered.

## 4. Algorithms & Key Logic
- The condition checks:
  - `accCost >= costThresholds.critical_usd` (now triggers at $100.0 USD)
  - `accCost >= costThresholds.warning_usd` (now triggers at $50.0 USD)
- String formatting:
  - `Total cost is <strong>${formatCost(accCost)} USD</strong>` formats to two decimal places (e.g. `$16.60 USD` instead of `$16.5963 USD`).

## 5. Validation Rules
None.

## 6. Implementation Checklist
- [ ] Update `skills/workflow-runtime/scripts/workflow_runtime.py` default thresholds.
- [ ] Update `.agents/skills/workflow-runtime/scripts/workflow_runtime.py` default thresholds.
- [ ] Update `extensions/visualizer/resources/webview.html` thresholds and formatting code.
- [ ] Run `make package-vscode` to compile TS and webview.
- [ ] Run `install_extension.sh` to update VS Code local extension directory.

## 7. Verification & Test Plan
- **Acceptance Assertions**:
  - *REQ-001*: Cost warning does not display at `$16.60` (as it is below `$50.0`).
  - *REQ-002*: All cost alerts in the webview format values to 2 decimal places.
