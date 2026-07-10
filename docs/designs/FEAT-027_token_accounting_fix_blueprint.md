<!-- File path: docs/designs/FEAT-027_token_accounting_fix_blueprint.md -->

---
feature_id: FEAT-027
feature_name: Investigate and Fix AIWF Runtime Token Accounting
status: reviewed
stage: blueprint
created_at: 2026-07-08
updated_at: 2026-07-08
previous_artifact: ../plans/FEAT-027_token_accounting_fix_plan.md
next_artifact: [Implementation (Source Code)](../../)
---

# Technical Blueprint & Implementation Contract – Investigate and Fix AIWF Runtime Token Accounting

## 0. Baseline Context & References
- **Memory Baseline**: Based on [project-summary.md](file://./.agents/project-summary.md), the system tracks session usage via local transcript logs (`transcript.jsonl`) and persists metrics to local SQLite databases.
- **Inspected Source Files**:
  - `.agents/skills/workflow-runtime/scripts/context.py`
  - `.agents/skills/workflow-runtime/scripts/db.py`
  - `.agents/skills/workflow-runtime/scripts/workflow_runtime.py`
  - `.agents/skills/workflow-runtime/scripts/analytics_engine.py`
  - `extensions/visualizer/resources/webview.html`

## 1. File-by-File Analysis & Proposed Mutations

| File Path | Operation | Responsibility | Dependency | Impact & Risk |
| :--- | :--- | :--- | :--- | :--- |
| `.agents/skills/workflow-runtime/scripts/context.py` | `MODIFY` | Update the transcript parser `parse_transcript` to filter model actions by generation types (`PLANNER_RESPONSE` and `ASK_QUESTION`). Restructure character-to-token fallback estimations to match actual single request size instead of cumulative counts. | None | Low risk. Accurate token counts across all sessions. |
| `.agents/skills/workflow-runtime/scripts/workflow_runtime.py` | `MODIFY` | Update `update_context_health` to call `update_analytics(session, ".")` from the analytics engine. This serializes structured telemetry payloads (with `active_context` and `accumulated_usage` keys) directly to `.session.json`. Update the `diagnose` subcommand under `do_usage` to print raw vs parsed vs stored vs displayed token details. | `.agents/skills/workflow-runtime/scripts/analytics_engine.py` | Low risk. Resolves the visualizer dashboard flat-schema rendering fallback bug. |
| `.agents/skills/workflow-runtime/scripts/db.py` | `MODIFY` | Add a database normalization routine `normalize_database_records(db_path)` that reads the SQLite file, loops through active logs, and recalculates database rows based on the corrected `parse_transcript` algorithm. Expose it via CLI. | `.agents/skills/workflow-runtime/scripts/context.py` | Low risk. Automatically scales down/corrects prior inflated sessions. |
| `.agents/skills/workflow-runtime/tests/test_runtime.py` | `MODIFY` | Add unit tests validating: 1 request token calculations, 10 request token growth progression, and session database write idempotency. | `.agents/skills/workflow-runtime/scripts/context.py` | Low risk. Ensures test pipeline validates math changes. |

## 2. Target Folder Structure
```text
.
├── .agents
│   ├── AGENTS.md
│   ├── AI_RULES.md
│   ├── project_runtime.db
│   ├── state
│   │   ├── rules.json
│   │   └── context.json
│   └── skills
│       └── workflow-runtime
│           ├── SKILL.md
│           ├── scripts
│           │   ├── analytics_engine.py
│           │   ├── context.py
│           │   ├── db.py
│           │   ├── session.py
│           │   ├── project_discovery.py
│           │   ├── release_manager.py
│           │   ├── state_sync.py
│           │   └── workflow_runtime.py
│           └── tests
│               └── test_runtime.py
├── docs
│   ├── brainstorming
│   │   ├── FEAT-026_context_analytics_dashboard.md
│   │   └── FEAT-027_token_accounting_fix.md
│   ├── plans
│   │   └── FEAT-027_token_accounting_fix_plan.md
│   └── designs
│       └── FEAT-027_token_accounting_fix_blueprint.md
├── extensions
│   └── visualizer
│       ├── resources
│       │   └── webview.html
│       └── src
│           └── extension.ts
└── task.md
```

## 3. Interface Contracts (Public & Internal)
- **Public Interface Contracts**:
  - *CLI Command Syntax*: 
    - `python3 .agents/skills/workflow-runtime/scripts/workflow_runtime.py usage diagnose`
      - Options: None.
      - Output: Prints a text block displaying Raw provider usage stats, Parsed usage from engine, Stored database row values, and Aggregated/Displayed summaries.
    - `python3 .agents/skills/workflow-runtime/scripts/workflow_runtime.py usage normalize`
      - Options: None.
      - Output: Cleans up the SQLite databases by recalculating and rewriting history rows based on corrected parser logic.
  - *Backward Compatibility*:
    - The session payload written to `.session.json` maintains the legacy flat fields (`total_tokens`, `input_tokens`, etc.) at the root of `workflow_usage_summary` for compatibility, but injects the structured `active_context` and `accumulated_usage` dictionaries inside it.
  - *Enum Constraint*:
    - `permission_mode` must only accept `sandbox` and `full_access` (validated in `session.py`).

- **Internal Component Contracts**:
  - `parse_transcript(log_file: str) -> dict` in `context.py`:
    - Returns calculated flat dictionary or `{}`.
  - `normalize_database_records(db_path: str) -> None` in `db.py`:
    - Safely executes transactions on SQLite to overwrite existing records with recalculated accurate tokens.

## 4. Algorithms & Logic Specifications
### Accurate Input Token Calculation
The parser iterates over lines in `transcript.jsonl`.
- `requests_count` increments by 1 for each line satisfying `line.get("source") == "MODEL" and line.get("type") in ["PLANNER_RESPONSE", "ASK_QUESTION"]`.
- `total_input_chars` accumulates `current_history_chars` ONLY on these model request generations.
- Tool responses and command outputs (lines where `source != "MODEL"` or `type not in ["PLANNER_RESPONSE", "ASK_QUESTION"]`) are added to `current_history_chars` but DO NOT trigger input token accumulation.

### Database Normalization Logic
Inside `db.py`:
```python
def normalize_database_records(db_path: str) -> None:
    # 1. Connect to SQLite database
    # 2. SELECT conversation_id FROM usage_records
    # 3. For each conversation_id:
    #    a. Resolve its transcript.jsonl path under ~/.gemini/antigravity-ide/brain/
    #    b. If the log exists, run parse_transcript(log_path) to get accurate tokens.
    #    c. If not, divide the database row's token count by 10 (as a safe default correction factor).
    #    d. UPDATE usage_records with correct values.
```

## 5. State Machine & Transitions
This feature does not alter the workflow state transitions. State resumes/rollbacks remain governed by `session.py` checkpoint levels.

## 6. Validation and Safety Constraints
- **Input Validation**: All parsed transcript rows are validated via `json.loads` within try-except blocks.
- **Directory Restrictions**: SQLite database operations verify directory permissions prior to read/write transactions.

## 7. Backward Compatibility & Migration Mapping
No fields are renamed or deleted. Backward compatibility is maintained.

## 8. Implementation Checklist
- [ ] Modify `parse_transcript` in `context.py` to filter by generation types.
- [ ] Update `update_context_health` in `workflow_runtime.py` to call `update_analytics`.
- [ ] Add `normalize_database_records` function to `db.py`.
- [ ] Expose `normalize` and `diagnose` subactions under the CLI `usage` parser.
- [ ] Add verification test cases in `test_runtime.py`.

## 9. Acceptance Criteria & Test Mapping

| Requirement ID | Requirement Description | Expected Result | Verification Method | Unit/Integration Test Target |
| :--- | :--- | :--- | :--- | :--- |
| `REQ-001` | Filter LLM requests in parser | Input tokens are calculated only on planner/user response steps | Run simulation tests | `test_runtime.py` -> `test_accurate_token_estimation` |
| `REQ-002` | Structured payload integration | session contains structured `active_context` | Check `.session.json` keys | `test_runtime.py` -> `test_structured_payload` |
| `REQ-003` | SQLite DB Normalization | SQLite rows reflect recalculated token totals | Run `usage normalize` CLI | `test_runtime.py` -> `test_database_normalization` |
| `REQ-004` | CLI Diagnostic Mode | Displays a comparative table of token metrics | Run `usage diagnose` CLI | Manual verification |

## 10. Disallowed Outputs Validation
- [x] No `file://` or absolute paths used.
- [x] No placeholders like `...` or `etc.` in code/structures.
- [x] No `TBD` or `To Be Determined` placeholders.
- [x] No unsafe permission values.
- [x] No unmapped legacy fields.
