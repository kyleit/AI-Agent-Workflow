<!-- File path: docs/issues/FIX-023_fix_api_cost_warning_rounding.md -->
---
artifact_type: fix-spec
issue_id: FIX-023
workflow: quick-fix
status: pending
---
# Fix Specification – Adjust API Cost Warning Thresholds and Round Cost Values

## 1. Issue Description
- **Cost Alert Inefficiency**: The extension currently warns users about "High accumulated API cost" at a threshold of `$10.0` USD. This warning triggers too early (e.g. at `$16` USD) and is considered annoying/unnecessary under normal AI workflow cost bounds.
- **Precision Issue**: The warning display uses 4 decimal places (`toFixed(4)`), showing values like `$16.5963 USD` instead of clean rounded numbers.

## 2. Scope
- **In Scope**:
  - Raise default warning threshold from `$10.0` USD to `$50.0` USD, and critical threshold from `$50.0` USD to `$100.0` USD in `workflow_runtime.py` and `webview.html`.
  - Refactor UI cost alert messages to format cost values to 2 decimal places using `formatCost()` function or `toFixed(2)` instead of `toFixed(4)`.
  - Refactor redundant reads savings display to use 2 decimal places.
- **Out of Scope**:
  - Changing token pricing models.
  - Resetting project database.
