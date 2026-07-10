<!-- File path: docs/plans/FEAT-027_token_accounting_fix_plan.md -->

---
feature_id: FEAT-027
feature_name: Investigate and Fix AIWF Runtime Token Accounting
status: reviewed
stage: planning
created_at: 2026-07-08
updated_at: 2026-07-08
previous_artifact: ../brainstorming/FEAT-027_token_accounting_fix.md
next_artifact: ../designs/FEAT-027_token_accounting_fix_blueprint.md
---

# FEAT-027: Investigate and Fix AIWF Runtime Token Accounting

## Objective
- To resolve the incorrect and impossible token values reported on the visualizer dashboard by correcting the transcript parsing logic, aligning session schema states, and implementing database validation and repair utilities.
- Success is defined as:
  - Active Context represents only the active request's prompt size (in tokens).
  - Accumulated Input/Output/Cost/Request counts are mathematically consistent and increment accurately request-by-request.
  - Telemetry operations are idempotent under refreshes, restarts, and workflow resumes.

## Scope
### Included
- Correction of token estimation rules in the transcript parsing module.
- Alignment of the runtime state synchronization payload structure with dashboard view expectations.
- Migration and normalization scripts to repair existing database records containing inflated token counts.
- Integration of a CLI-based diagnostic mode displaying raw, parsed, stored, and displayed statistics.
- Automated simulation test suite validating token counts across 1, 10, and 100 requests.

### Excluded
- Re-designing the Visualizer Webview UI layout or styling assets.
- Changing the database engine from SQLite to another database provider.
- Implementing billing or payment gateways for token consumption.

## Project Impact
- **Modules**: Core workflow runtime controller, session manager, and analytics aggregator.
- **Database**: `project_runtime.db` and global SQLite databases (`usage_records` table).
- **APIs/CLI**: New diagnostic subaction interface in the workflow runtime CLI.
- **UI**: Visualizer sidebar panel will automatically render correct, aligned token values.

## Dependencies
- Valid SQLite database structures.
- Active workflow session logs (`transcript.jsonl` files) inside the `.gemini/antigravity-ide/brain/` workspace.

## Risks
- **Risk**: Database normalization query might cause performance lock or corrupt legacy histories.
  - **Mitigation**: Safeguard migrations with try-except blocks, execute backups prior to changes, and validate queries under isolated transaction wrappers.
- **Risk**: Active context window calculation drift when different models or tokenizers are utilized.
  - **Mitigation**: Establish standard character-to-token ratio metrics (e.g. 1 token = ~3 characters) with model-specific fallback defaults.

## Acceptance Criteria
- [ ] Active context window is restricted to the current active request's token count.
- [ ] The CLI `release report` and visualizer panel report accurate accumulated request counts.
- [ ] Storing, serializing, and syncing telemetry data is fully idempotent.
- [ ] Existing inflated database rows are normalized and corrected.
- [ ] Command line diagnostic utility runs successfully, outputting all pipeline stages of token accounting.

## Deliverables
- Corrected transcript parser module.
- Standardized analytics synchronization engine.
- SQLite database normalization/repair script.
- CLI diagnostic mode.
- Automated verification tests and reports.

## Estimated Complexity
- **Low**: The modifications are contained to the Python runtime files and database query scripts. No UI framework or styling modifications are required.

## Recommended Blueprint Focus
- Focus on the strict definition of text generation step types (`PLANNER_RESPONSE`, `ASK_QUESTION`) within the transcript log parser.
- Focus on transaction safety during database normalization execution.
- Focus on mock-based simulation test assertions verifying correctness over sequential API calls.

## Recommended Next Skill
/blueprint
