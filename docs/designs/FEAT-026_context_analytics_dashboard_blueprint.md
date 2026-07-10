<!-- File path: docs/designs/FEAT-026_context_analytics_dashboard_blueprint.md -->

---
feature_id: FEAT-026
feature_name: AIWF Runtime Context Analytics & Optimization Dashboard
status: reviewed
stage: blueprint
created_at: 2026-07-08
updated_at: 2026-07-08
previous_artifact: ../plans/FEAT-026_context_analytics_dashboard_plan.md
next_artifact: [Implementation (Source Code)](../../)
---

# Technical Blueprint & Implementation Contract – AIWF Runtime Context Analytics & Optimization Dashboard

## 0. Baseline Context & References
- **Memory Baseline**: Memory status is FRESH. Workspace profile contains CLI test tools (`pytest`), compile/lint gates (`make`, `ruff`, `black`), and visual debug configured as `none`.
- **RAG Query Summaries**: RAG search query `context analytics` fell back to local keyword matches; verified telemetry files are updated by `state_sync.py` and watched by `extension.ts`.
- **Inspected Source Files**:
  - `extensions/visualizer/src/extension.ts` (Lines 1-608): Watched paths include `.agents/state/*.json`. Estimates token usage from `.agents/state/usage.json`.
  - `extensions/visualizer/resources/webview.html`: Sidebar UI template file.
  - `.agents/skills/workflow-runtime/scripts/session.py` (Lines 1-211): Core load/save session utilities.
  - `.agents/skills/workflow-runtime/scripts/state_sync.py` (Lines 1-241): Synchronizes and aggregates/deconstructs `.session.json` to/from `.agents/state/`.

## 1. File-by-File Analysis & Proposed Mutations

| File Path | Operation | Responsibility | Dependency | Impact & Risk |
| :--- | :--- | :--- | :--- | :--- |
| `skills/workflow-runtime/scripts/analytics_engine.py` | `NEW` | Aggregates and stores historical context analytics in `.agents/runtime/analytics_history.json`. Computes cache hit ratio, input/output ratio, and growth speed. Analyzes duplicate file reads by checking `current_logs` or log inputs for multiple references to static files like `AI_RULES.md`, `AGENTS.md`, and memory files. | Standard Python `json`, `os`, `datetime` libraries. | Low risk. Does not alter core runtime execution. |
| `skills/workflow-runtime/scripts/simulate_analytics.py` | `NEW` | Mock-generates 500 request cycles with different token/cost ratios to validate the calculations in `analytics_engine.py`. | Depends on `analytics_engine.py`. | None. Runs only as a test verification suite. |
| `skills/workflow-runtime/scripts/session.py` | `MODIFY` | Modify `load_session` to perform a schema migration check on memory load. Migrate legacy fields to new sub-structures. | Depends on `state_sync.py`. | Medium risk. Needs to ensure old session files do not cause JSON load errors. |
| `skills/workflow-runtime/scripts/state_sync.py` | `MODIFY` | Expand usage metrics in `aggregate_state` and `deconstruct_state` to sync active context window tokens versus accumulated totals, cost, and efficiency rates. | Depends on `session.py` and sub-state JSON files. | Medium risk. Sub-states must be saved atomically via temporary files to avoid corruption. |
| `skills/workflow-runtime/scripts/workflow_runtime.py` | `MODIFY` | Modify CLI subcommands. Trigger `analytics_engine.py` update at the end of each session-saving command. Add a `release report` subcommand to format the analytics log as a markdown table report. | Depends on `analytics_engine.py` and `session.py`. | Low risk. |
| `extensions/visualizer/resources/webview.html` | `MODIFY` | Reorganize UI grid to separate "Active Context Window" gauge and charts from "Accumulated Session Usage". Add SVG-based line chart for growth history. Render duplicate read recommendations and optimization alerts. | Depends on Visualizer VS Code extension messaging. | Low risk. UI-only modification. |

## 2. Target Folder Structure
```text
.
├── extensions
│   └── visualizer
│       └── resources
│           └── webview.html
└── skills
    └── workflow-runtime
        └── scripts
            ├── analytics_engine.py
            ├── session.py
            ├── simulate_analytics.py
            ├── state_sync.py
            └── workflow_runtime.py
```

## 3. Interface Contracts (Public & Internal)
- **Public Interface Contracts**:
  - *CLI Report Command*:
    `python3 skills/workflow-runtime/scripts/workflow_runtime.py release report`
    Outputs a formatted markdown table summarizing:
    - Active Context size and window usage percentage.
    - Accumulated Input, Output, Cache, and Thinking tokens.
    - Total Accumulated Cost (USD).
    - Efficiency statistics: Cache Hit Ratio, growth rate.
    - Repetitive reads warning alerts.
  - *JSON Schema for `.agents/runtime/analytics_history.json`*:
    An array of request entries:
    ```json
    [
      {
        "timestamp": "string (ISO-8601)",
        "request_number": "integer",
        "active_tokens": "integer",
        "input_tokens": "integer",
        "output_tokens": "integer",
        "cache_tokens": "integer",
        "thinking_tokens": "integer",
        "estimated_cost_usd": "number",
        "duplicate_reads_detected": [
          {
            "file": "string (relative path)",
            "count": "integer",
            "size_bytes": "integer"
          }
        ]
      }
    ]
    ```
  - *Schema extension for `usage.json` and `.session.json`*:
    The `"context_usage"` and `"workflow_usage_summary"` will be restructured to hold:
    ```json
    {
      "active_context": {
        "total_tokens": 12000,
        "limit_tokens": 2000000,
        "percentage": 0.6,
        "input_tokens": 11500,
        "output_tokens": 500,
        "cache_tokens": 8000,
        "thinking_tokens": 0
      },
      "accumulated_usage": {
        "input_tokens": 125000,
        "output_tokens": 5000,
        "cache_tokens": 75000,
        "thinking_tokens": 250,
        "total_tokens": 130000,
        "estimated_cost_usd": 0.195,
        "request_count": 8
      },
      "efficiency": {
        "cache_hit_ratio": 0.6,
        "input_to_output_ratio": 25.0,
        "growth_speed_tokens_per_request": 15000.0,
        "duplicate_read_count": 4,
        "estimated_savings_usd": 0.082
      }
    }
    ```
  - *Backward Compatibility*:
    If `usage.json` is loaded and does not contain `"active_context"`, the migration logic will initialize:
    `active_context` = legacy `"context_usage"` values.
    `accumulated_usage` = legacy `"workflow_usage_summary"` values.
    `efficiency` = default computed values (ratios set to 0.0).
  - *Enum Constraint*:
    For `permission_mode`, only allow: `sandbox`, `full_access`. Never allow `unrestricted`.

- **Internal Component Contracts**:
  - *Module/Class Signatures*:
    - `analytics_engine.py`:
      - `def calculate_metrics(session_data: dict) -> dict`: Computes input/output ratios, cost, and cache rates.
      - `def detect_duplicate_reads(logs: list) -> list`: Scans string lines for repetitive file reads.
      - `def append_to_history(data: dict) -> None`: Appends telemetry history, capping at 100 entries.

- **Extension Changes**:
  - *ViewModel Schema*: Visualizer will expect the aggregated `"context_usage"` with `"active_context"`, `"accumulated_usage"`, and `"efficiency"` nodes.
  - *File Watch Strategy*: Listens to `.agents/state/usage.json` updates and immediately posts an `UPDATE_SESSION` message.
  - *Debounce Behavior*: Updates are debounced with a 200ms timer to prevent UI lag on rapid file changes.
  - *Fallback Order*: Checks `.agents/state/usage.json` first. If missing, falls back to reading `.agents/.session.json`. If both are missing, renders defaults (all counters at 0).
  - *Missing/Corrupted State UI*: Displays a warning alert banner "Usage data unavailable or corrupted".
  - *Partial Refresh Rules*: Only redraws the active context gauges and the analytics charts (using inline SVGs), keeping the checkpoint stepper state intact.

## 4. Algorithms & Logic Specifications
- **Repetitive Read Detection Algorithm**:
  1. Retrieve list of recently read files from RAG metrics or command arguments (or parsing target files logs).
  2. Maintain a file read counts map: `read_counts: dict[str, int]`.
  3. Identify static system files: `AI_RULES.md`, `AGENTS.md`, `project-summary.md`.
  4. For each file read, increment the counter in `read_counts`.
  5. Any file with `count > 1` is marked as a duplicate read.
  6. Calculate estimated cost savings:
     `savings = sum((count - 1) * file_size_bytes * token_cost_per_byte)`.
- **Step-by-step Flow**:
  - Command executes -> telemetry writes active request tokens -> `analytics_engine.py` parses token usage -> appends to `analytics_history.json` (max 100 entries) -> computes aggregate efficiency -> writes `usage.json` -> atomic rename to avoid corruption -> VS Code file watcher detects `usage.json` change -> visualizer re-renders charts.

## 5. State Machine & Transitions
This feature does not introduce new workflow-level checkpoints, but it governs transition within state updates:
- **States**:
  - `idle`: Awaiting command execution.
  - `analyzing`: Command finished, computing metrics.
  - `updating_state`: Writing JSON states atomically.
- **Rollback**: If writing `usage.json.tmp` fails, the engine deletes the temp file and leaves the original `usage.json` unchanged, marking `context_health` as `healthy` or raising a warning log without crashing the CLI.

## 6. Validation and Safety Constraints
- **Input Validation**:
  - Configuration thresholds in `workflow.config.json` under `"token_budget"` must be validated:
    - `"max_active_tokens"`: integer, range [1000, 2000000].
    - `"max_accumulated_cost_usd"`: number, positive.
  - Any out-of-range value will fallback to default values (2,000,000 tokens and 10.0 USD).
- **Safety restriction**:
  - File write operations must remain strictly inside the `.agents/` directory (sandbox check).

## 7. Backward Compatibility & Migration Mapping
| Old Field | New File | New Field | Migration Rule | Recovery Rule |
| :--- | :--- | :--- | :--- | :--- |
| `context_usage` | `.agents/state/usage.json` | `context_usage.active_context` | Copy values of `context_usage` into `context_usage.active_context` | Fallback to original `context_usage` shape if error |
| `workflow_usage_summary` | `.agents/state/usage.json` | `context_usage.accumulated_usage` | Copy values of `workflow_usage_summary` into `context_usage.accumulated_usage` | Fallback to original `workflow_usage_summary` shape |

## 8. Implementation Checklist
- [ ] Create `skills/workflow-runtime/scripts/analytics_engine.py` implementing metric calculation and history logging.
- [ ] Update `skills/workflow-runtime/scripts/session.py` to add session schema migration.
- [ ] Update `skills/workflow-runtime/scripts/state_sync.py` to synchronize active, accumulated, and efficiency nodes.
- [ ] Update `skills/workflow-runtime/scripts/workflow_runtime.py` to trigger analytics and add `release report` subcommand.
- [ ] Create `skills/workflow-runtime/scripts/simulate_analytics.py` validation script.
- [ ] Modify `extensions/visualizer/resources/webview.html` layout to show separation of gauges, SVG charts, and recommendations.
- [ ] Run compile and package commands to verify extension builds correctly.

## 9. Acceptance Criteria & Test Mapping
| Requirement ID | Requirement Description | Expected Result | Verification Method | Unit/Integration Test Target |
| :--- | :--- | :--- | :--- | :--- |
| `REQ-01` | Separation of active vs accumulated usage | Telemetry lists separate `active_context` and `accumulated_usage` | Run `python3 skills/workflow-runtime/scripts/workflow_runtime.py heartbeat` | `skills/workflow-runtime/tests/test_runtime.py::test_analytics_separation` |
| `REQ-02` | Redundant file read detection | System identifies duplicates and calculates cost savings | Run `python3 skills/workflow-runtime/scripts/simulate_analytics.py` | `skills/workflow-runtime/tests/test_runtime.py::test_duplicate_reads` |
| `REQ-03` | Token budget alerts | Warnings display when thresholds are exceeded | Run simulation with thresholds set lower than mock values | `skills/workflow-runtime/tests/test_runtime.py::test_budget_warnings` |
| `REQ-04` | Visual charts and widgets rendering | Webview renders charts using SVG and shows advisor recommendations | Build visualizer and open VS Code sidebar | Manual inspection |

## 10. Disallowed Outputs Validation
- [x] No `file://` or absolute paths used.
- [x] No placeholders like `...` or `etc.` in code/structures.
- [x] No `TBD` or `To Be Determined` placeholders.
- [x] No unsafe permission values (e.g. `unrestricted`).
- [x] No unmapped legacy fields without migration rules.
