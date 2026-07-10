<!-- docs/brainstorming/FEAT-027_token_accounting_fix.md -->

---
feature_id: FEAT-027
feature_name: Investigate and Fix AIWF Runtime Token Accounting
status: draft
stage: brainstorming
created_at: 2026-07-08
updated_at: 2026-07-08
previous_artifact: None
next_artifact: ../plans/FEAT-027_token_accounting_fix_plan.md
---

# Master Requirement Document – Investigate and Fix AIWF Runtime Token Accounting

## 1. Feature ID & Name
- **Feature ID**: FEAT-027
- **Feature Name**: Investigate and Fix AIWF Runtime Token Accounting

## 2. Original Idea
Investigate and Fix AIWF Runtime Token Accounting:
Perform a complete root-cause investigation of the AIWF Runtime token accounting system and fix any incorrect calculations.
The dashboard reports impossible values such as:
- Active Context: 239.4M / 2.0M (2177%)
- Requests: 1
- Accumulated Input: 239M
- Project Usage: billions of tokens after only a small amount of work

## 3. Business Problem
- **Problem**: The AIWF dashboard displays highly inflated and mathematically impossible token metrics. Active context is displayed as cumulative session totals, the total request count defaults to 1, and the aggregated project-level usage displays billions of tokens after minimal activity.
- **Why it matters**: Developers cannot trust the telemetry data regarding model context size, token efficiency, or financial costs. This impairs budget planning, rate-limit safety checks, and performance optimizations.
- **Who is affected**: Developers and QA Engineers monitoring LLM token usage and budget consumption.
- **Expected outcome**: Correct, precise, and idempotent token telemetry on the dashboard. The Active Context represents only the active conversation size, the request count matches actual LLM queries, and project totals are accurate.

## 4. Requirement Discovery
- **Functional Requirements**:
  - FR-01: Filter LLM prompt requests in the parser so only actual text generation steps (`PLANNER_RESPONSE` and `ASK_QUESTION`) increment input token counts. Tool execution steps (`VIEW_FILE`, `RUN_COMMAND`, etc.) must not trigger new prompt input additions.
  - FR-02: Align the runtime session schema to write a structured `workflow_usage_summary` (containing `active_context` and `accumulated_usage` keys) matching the visualizer's expectations.
  - FR-03: Implement a SQLite database normalization routine or migration query to recalculate or fix existing legacy/inflated rows.
  - FR-04: Implement a detailed CLI diagnostic mode showing the full raw, parsed, stored, and displayed values to verify token calculation pipelines.
- **Non-functional Requirements**:
  - NFR-01: Idempotency - Repeated syncs, restarts, or UI refreshes must not double-count or alter session statistics.
  - NFR-02: Zero-overhead log parsing to prevent visualizer lag.
- **Technical Constraints**:
  - TC-01: Must read and parse the transcript log file (`transcript.jsonl`) correctly without modifying its format.
  - TC-02: Maintain schema compatibility with `project_runtime.db` structure.

## 5. Clarification Questions & Answers
| Question | Answer |
|---|---|
| Should we keep the old database records or wipe them? | We should keep them but write a routine to normalize them (e.g. recalculating them using the corrected transcript parsing logic if their log files exist, or scaling them down if not). |
| How should request counts be calculated? | Exactly increment by 1 for each step of type `PLANNER_RESPONSE` or `ASK_QUESTION` where `source == "MODEL"`. |

## 6. Requirement Readiness Score
- **Score**: 100/100
- **Status**: Ready ≥ 85

## 7. Existing Project Context
- **Memory Source**: [project-summary.md](file://./.agents/project-summary.md) and RAG references.
- **Existing Architecture Summary**: Token accounting uses a local Python engine (`context.py`, `analytics_engine.py`) to parse conversation transcripts and synchronizes to local and global SQLite databases (`db.py`). The VS Code extension reads the `.session.json` state file to update its panel webview.

## 8. Existing Modules & Services
| Module/Service | Location | Relevance |
|---|---|---|
| Transcript Parser | [.agents/skills/workflow-runtime/scripts/context.py](file://./.agents/skills/workflow-runtime/scripts/context.py) | Needs updated logic for text generation filters. |
| Telemetry Engine | [.agents/skills/workflow-runtime/scripts/analytics_engine.py](file://./.agents/skills/workflow-runtime/scripts/analytics_engine.py) | Computes and saves the structured payload. |
| SQLite Database | [.agents/skills/workflow-runtime/scripts/db.py](file://./.agents/skills/workflow-runtime/scripts/db.py) | Manages tables, records, summaries, and needs a cleanup routine. |
| CLI Entrypoint | [.agents/skills/workflow-runtime/scripts/workflow_runtime.py](file://./.agents/skills/workflow-runtime/scripts/workflow_runtime.py) | Executes the syncs and needs updated diagnostic subaction. |
| Visualizer Webview | [extensions/visualizer/resources/webview.html](file://./extensions/visualizer/resources/webview.html) | Passive renderer showing token usage. |

## 9. Solution Options Evaluated

### Option A: Telemetry Engine Restructuring & DB Cleanup (Recommended)
- **Overview**: Correct the parser logic in `context.py` to target only `PLANNER_RESPONSE` and `ASK_QUESTION`. Integrate `update_analytics` inside `workflow_runtime.py` to write the structured data object on every session update. Write a script/migration inside `db.py` to normalize legacy rows.
- **Architecture**:
  - `context.py`: Filters `source == 'MODEL'` with generation types.
  - `workflow_runtime.py`: Feeds structured payload to `.session.json` and updates the CLI `diagnose` subcommand.
  - `db.py`: Recalculates legacy database values.
- **Advantages**:
  - Solves the problem at the root.
  - Re-aligns the UI expectations with backend payloads.
  - Fixes the historical charts and aggregates completely.
- **Disadvantages**:
  - Requires changes in several files.
- **Complexity**: Low
- **Risk**: Low
- **Performance**: High
- **Compatibility**: High
- **Future Scalability**: High

### Option B: Flat Schema Emulation (Backend Only)
- **Overview**: Settle on the flat schema. Hack the visualizer to handle the flat keys directly and avoid restructuring.
- **Advantages**: No changes to visualizer files needed.
- **Disadvantages**: Limits dashboard customization and future telemetry growth.

## 10. Solution Comparison Table
| Criteria | Option A | Option B |
|---|---|---|
| Complexity | Low | Very Low |
| Risk | Low | Low |
| Performance | High | High |
| Maintainability | High | Medium |
| Compatibility | High | High |
| Future Scalability | High | Low |
| Development Cost | Low | Low |

## 11. Selected Solution
- **Choice**: Option A — Telemetry Engine Restructuring & DB Cleanup
- **Why Selected**: It fixes both the math errors (double-counting) and the rendering flaws (active vs accumulated mismatch) while maintaining high codebase quality and scalability.
- **Trade-offs Accepted**: Requires updates across three backend runtime files, but all are well-contained.
- **Technical Debt**: None.
- **Risk Mitigation**: Verify calculations with extensive simulation scenarios (1, 10, 100 requests).

## 12. Risks & Assumptions
- **Risks**:
  - R-01: Legacy DB data formatting issues → Mitigate by validating the row count and safely wrapping SQL execution in try-except blocks.
- **Assumptions**:
  - A-01: The visualizer extension successfully reads `.session.json` containing the updated structured keys.

## 13. Acceptance Criteria
- [ ] Active context window is ONLY the size of the current active request (not cumulative).
- [ ] The CLI `release report` and webview display correct request counts (not stuck at 1).
- [ ] Storing and sync routines are fully idempotent (no double-counting on reload or UI refresh).
- [ ] Database contains corrected sums without legacy duplication.
- [ ] CLI command `workflow_runtime.py usage diagnose` shows a comprehensive breakdown: Raw vs Parsed vs Stored vs Displayed.

---

## 14. Final Planning Prompt

### Purpose
Self-contained prompt for the `brainstorming-to-plan` Skill.

### Problem Statement
The token accounting system returns highly inflated counts (up to billions of tokens) and incorrectly maps cumulative total tokens to the active context window in the dashboard.

### Objectives & Selected Solution
Implement Option A:
- Modify `context.py` parser filter.
- Update `workflow_runtime.py` to call `update_analytics` for state serialization.
- Correct `db.py` to fix historical records.
- Implement CLI `diagnose` subaction.
- Run automated unit tests verifying calculations.

### Verification Checklist
- [ ] docs/plans/FEAT-027_token_accounting_fix_plan.md generated and approved
- [ ] docs/designs/FEAT-027_token_accounting_fix_blueprint.md generated and approved
