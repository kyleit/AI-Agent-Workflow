<!-- File path: docs/designs/FEAT-068_vir_runtime_execution_modes_blueprint.md -->

---
feature_id: FEAT-068
feature_name: Visual Intelligence Runtime — Runtime Execution Modes (CLI / IDE / CI / Daemon)
status: reviewed
stage: blueprint
created_at: 2026-07-12
updated_at: 2026-07-12
previous_artifact: ../plans/FEAT-068_vir_execution_modes_plan.md
next_artifact: [Implementation (Source Code)](../../)
---

# Technical Design Blueprint & Implementation Contract – Runtime Execution Modes

## 0. Baseline Context & References
- **Memory Baseline**: Memory of CLI argument parsing structures, NDJSON stream models, and VS Code webview bindings.
- **RAG Query Summaries**: Execution modes wrap the orchestrator pipelines and consume exit code parameters defined in Phase 6.
- **Inspected Source Files**:
  - [FEAT-068 Plan](file:///e:/AgentsProject/docs/plans/FEAT-068_vir_runtime_execution_modes_plan.md)
  - [VS Code Development Rules](file:///e:/AgentsProject/AGENTS.md)

---

## 1. File-by-File Analysis & Proposed Mutations

| File Path | Operation | Responsibility | Dependency | Impact & Risk |
| :--- | :--- | :--- | :--- | :--- |
| `vir_runtime/core/cli.py` | Create | Main CLI argument parser entry point (argparse) | None | High. Interfaces with terminal shells. |
| `vir_runtime/core/ipc.py` | Create | Emit line-delimited JSON (NDJSON) event streams to stdout | None | Medium. Communicates run progress to IDEs. |
| `vir_runtime/core/ci.py` | Create | Handle non-interactive run loops, blocking interactive inputs | None | High. Integrates with release pipelines. |
| `.agents/skills/frontend-visual-debug/SKILL.md` | Modify | Simplify skill internals to delegate calls to VIR CLI (< 100 LOC) | `cli.py` | Medium. Refactors old skill into thin client. |
| `vir_runtime/core/daemon.py` | Create | Asyncio background polling daemon watching DOM changes | None | Low. Background monitoring utility. |
| `extensions/visualizer/resources/webview.html` | Modify | Update panel layout to consume NDJSON events streams | None | High. Visualizer webview panel. |
| `extensions/visualizer/build.js` | Modify | Execute node compiler translating webview.html to webviewHtml.ts | `webview.html` | High. Mandatory compilation pipeline. |

---

## 2. Target Folder Structure
```text
extensions/
└── visualizer/
    ├── build.js
    └── resources/
        └── webview.html
vir_runtime/
└── core/
    ├── cli.py
    ├── daemon.py
    ├── ci.py
    └── ipc.py
```

---

## 3. Complete Class & Module Design

### 3.1 CLIRunner
- **Class / Module Name**: `vir_runtime.core.cli.CLIRunner`
  - **Responsibilities**: Configure arguments (mode, profile, url, headless), parse shell inputs, write ANSI colored progress boards, format summary tables.
  - **Public Methods**:
    - `def main(args: List[str]) -> int` - Main CLI entry point.
  - **Internal Methods**:
    - `def _print_ansi_status(message: str, level: str) -> None`

### 3.2 IPCEmitter
- **Class / Module Name**: `vir_runtime.core.ipc.IPCEmitter`
  - **Responsibilities**: Format stage changes and verdicts as NDJSON envelopes, write to stdout stream, and handle write locks.
  - **Constructor Parameters**:
    - `stream: TextIO` (defaults to sys.stdout)
  - **Public Methods**:
    - `def emit_event(event_type: str, data: Dict[str, Any]) -> None`

---

## 4. Detailed Interface Contracts

- **API Signature**: `def main(args: List[str]) -> int`
  - **Parameters**:
    - `args` (list of strings arguments passed from process shell call)
  - **Return Types**: Returns an integer exit code mapping.
  - **Exceptions**: None. (Exceptions caught internally, returning code 1).

---

## 5. Configuration Schema

- **Target Schema**:
```yaml
execution:
  default_mode: "cli"
  profiles:
    lightweight:
      headless: true
      timeout: 60
    deep:
      headless: false
      timeout: 600
```

---

## 6. Database & Storage Design
- Daemon sessions and log files are saved to SQLite `vir_sessions` indices.

---

## 7. Cache Architecture
- No caching is defined.

---

## 8. Error Model

- **Exception Class**: `InteractivePromptBlocked`
  - **Trigger Condition**: An interactive prompt is called when running in CI mode (`--mode ci`).
  - **Recovery Strategy**: Fail the gate immediately, abort execution, return exit code 2 (`BLOCKED`).
  - **Logging Requirements**: ERROR log stating the source input request details.

---

## 9. Skill Integration Contracts
- **Skill Name**: `frontend-visual-debug`
  - **Purpose**: Enforce a minimal wrapper (< 100 LOC) that forwards target page coordinates and blueprints contexts straight to `python -m vir_runtime.core.cli`.

---

## 10. CLI & Runtime Contracts
- **Subcommands**:
  - `run`: Start active investigation pipeline.
  - `daemon`: Control background polling process (`start` | `stop`).

---

## 11. Sequence Flows

- **IDE IPC Event Stream Flow**:
  1. User clicks "Run Audit" in Visualizer extension sidebar.
  2. Subprocess spawns `python -m vir_runtime.core.cli --mode ide --url ...`.
  3. `IPCEmitter` writes `{ "event": "stage_change", "data": { "stage": "Observe" } }` to stdout.
  4. VS Code extension captures line, parses JSON, and updates webview panel dynamically.
  5. Process exits on verdict.

---

## 12. Security & Safety
- **CI Non-interactive Enforcement**: Command inputs are locked to block shell inject overrides during CI pipeline runs.

---

## 13. Complete Test Matrix

| Requirement ID | Test Type | Test File Target | Mapped Component | Verification Assertion |
| :--- | :--- | :--- | :--- | :--- |
| `FR-15` | Unit Test | `tests/unit/test_cli_args.py` | `cli.py` | `self.assertEqual(config.mode, "ci")` |
| `FR-27` | Unit Test | `tests/unit/test_thin_client_loc.py` | `SKILL.md` | `self.assertLess(loc, 100)` |

---

## 14. Requirement Traceability Matrix
- `FR-15` -> Task 1.10 -> Class `CLIRunner` -> `cli.py` -> `test_cli_args.py` -> Verified.
- `FR-27` -> Task 1.17 -> Skill check -> `SKILL.md` -> `test_thin_client_loc.py` -> Verified.

---

## 15. File-Level Implementation Contracts
- **File**: `extensions/visualizer/resources/webview.html`
  - **Purpose**: VS Code visualizer HTML interface.
  - **Owner**: Coder
  - **Implementation Notes**: **CRITICAL** VS Code extension development rule: Never edit `webviewHtml.ts` directly. Always run `node extensions/visualizer/build.js` compiler script to compile `webview.html` into `webviewHtml.ts` after edits.
