<!-- File path: docs/designs/FEAT-059_vir_hearing_engine_and_touch_engine_blueprint.md -->

---
feature_id: FEAT-059
feature_name: Visual Intelligence Runtime — Hearing Engine & Touch Engine
status: reviewed
stage: blueprint
created_at: 2026-07-12
updated_at: 2026-07-12
previous_artifact: ../plans/FEAT-059_vir_hearing_engine_and_touch_engine_plan.md
next_artifact: [Implementation (Source Code)](../../)
---

# Technical Design Blueprint & Implementation Contract – Hearing Engine & Touch Engine

## 0. Baseline Context & References
- **Memory Baseline**: Memory of Playwright console hooks, network response interception models, and mouse movement paths algorithms.
- **RAG Query Summaries**: Sensory observations route events to `AsyncEventBus` topics using schemas defined in Phase 1.
- **Inspected Source Files**:
  - [FEAT-059 Plan](file:///e:/AgentsProject/docs/plans/FEAT-059_vir_hearing_engine_and_touch_engine_plan.md)

---

## 1. File-by-File Analysis & Proposed Mutations

| File Path | Operation | Responsibility | Dependency | Impact & Risk |
| :--- | :--- | :--- | :--- | :--- |
| `vir_runtime/sensory/hearing/console.py` | Create | Capture console warning, error, info logs | None | Low. Connects console listeners. |
| `vir_runtime/sensory/hearing/exceptions.py` | Create | Intercept JavaScript unhandled exceptions and promise rejections | None | Medium. Captures crash events. |
| `vir_runtime/sensory/hearing/network.py` | Create | Capture, intercept, and inspect network traffic request/response objects | None | High. Monitors API transport layers. |
| `vir_runtime/sensory/hearing/lifecycle.py` | Create | Monitor DOM load checkpoints and SPA history state changes | None | Low. Tracks URL navigation markers. |
| `vir_runtime/sensory/hearing/correlation.py` | Create | Filter and group sensory alerts within time windows (Observations Groups) | None | Medium. Correlates event timelines. |
| `vir_runtime/sensory/touch/deterministic.py` | Create | Dispatch Mode A target interactions (exact clicks, key entries) | None | High. Core action executor. |
| `vir_runtime/sensory/touch/human_sim.py` | Create | Dispatch Mode B fuzzy interactions (mouse curves, human click delay delays) | None | High. Exploratory action model. |
| `vir_runtime/sensory/touch/dead_click.py` | Create | Detect interactions that trigger zero DOM/CSS layout variations | None | Medium. Flags dead links. |
| `vir_runtime/sensory/touch/recorder.py` | Create | Output user actions array logs to target JSON replay paths | None | Low. Saves execution trails. |

---

## 2. Target Folder Structure
```text
vir_runtime/
└── sensory/
    ├── hearing/
    │   ├── console.py
    │   ├── correlation.py
    │   ├── exceptions.py
    │   ├── lifecycle.py
    │   └── network.py
    └── touch/
        ├── dead_click.py
        ├── deterministic.py
        ├── human_sim.py
        └── recorder.py
```

---

## 3. Complete Class & Module Design

### 3.1 HearingEngine
- **Class / Module Name**: `vir_runtime.sensory.hearing.HearingEngine`
  - **Responsibilities**: Attach event listeners to CDP console, exception, and network request pipelines, publishing findings.
  - **Constructor Parameters**:
    - `bus: AsyncEventBus`
    - `adapter: BrowserAdapter`
  - **Public Methods**:
    - `async def start_listening() -> None`
    - `async def stop_listening() -> None`
  - **Dependencies**: `console`, `exceptions`, `network`, `lifecycle`

### 3.2 TouchEngine
- **Class / Module Name**: `vir_runtime.sensory.touch.TouchEngine`
  - **Responsibilities**: Execute user journeys on the target viewport. Supports deterministic (Mode A) and simulated human (Mode B) interactions.
  - **Constructor Parameters**:
    - `adapter: BrowserAdapter`
    - `seed: int` - Pointer seed value for Mode B.
  - **Public Methods**:
    - `async def execute_action(action: Dict[str, Any], mode: str = "A") -> None`
    - `def export_replay_log(path: str) -> None`
  - **Dependencies**: `deterministic`, `human_sim`, `dead_click`, `recorder`

---

## 4. Detailed Interface Contracts

- **API Signature**: `async def execute_action(action: Dict[str, Any], mode: str = "A") -> None`
  - **Parameters**:
    - `action` (dict layout specifying click/hover details: `{"type": "click", "selector": "#btn"}`)
    - `mode` (`A` or `B`)
  - **Return Types**: None.
  - **Exceptions**:
    - `InteractionTargetNotFoundError` - If element selector is missing from page viewport.
    - `ActionBlockedError` - If click overlaps other target nodes.

---

## 5. Configuration Schema

- **Target Schema**:
```yaml
sensory:
  hearing:
    console_log_levels: ["error", "warning"]
    correlation_window_ms: 250
  touch:
    default_mode: "A"
    human_speed_delay_multiplier: 1.2
```

---

## 6. Database & Storage Design
- Captured console errors and network exceptions are stored in the SQLite `vir_evidence` table (Phase 3).

---

## 7. Cache Architecture
- **Temporal Event Cache**:
  - Memory collection storing logs within the active 250ms window to bundle cascading warnings.

---

## 8. Error Model

- **Exception Class**: `DeadClickDetected`
  - **Trigger Condition**: Element clicked but zero mutations occur in DOM sub-trees or scroll layouts.
  - **Recovery Strategy**: Flag warning, log coordinates in replay, proceed with exploration.
  - **Logging Requirements**: WARNING log highlighting element CSS selectors.

---

## 9. Skill Integration Contracts
- None.

---

## 10. CLI & Runtime Contracts
- None.

---

## 11. Sequence Flows

- **Touch Interaction & Verification Flow**:
  1. `TouchEngine` receives target click selector dictionary.
  2. Before layout state captured by `HearingEngine`.
  3. Action fired (Mode A or B).
  4. After layout state checked.
  5. `DeadClickDetector` evaluates structural difference.
  6. Action details saved to replay log.

---

## 12. Security & Safety
- **Mouse coordinates containment**: Mouse path paths are constrained to fit strictly within the page viewport dimensions, preventing mouse escapes.

---

## 13. Complete Test Matrix

| Requirement ID | Test Type | Test File Target | Mapped Component | Verification Assertion |
| :--- | :--- | :--- | :--- | :--- |
| `FR-01` | Unit Test | `tests/unit/test_console_capture.py` | `console.py` | `self.assertEqual(len(captured_logs), 1)` |
| `FR-21` | Unit Test | `tests/unit/test_dead_click.py` | `dead_click.py` | `self.assertTrue(is_dead_click)` |

---

## 14. Requirement Traceability Matrix
- `FR-01` -> Task 1.1 -> Class `ConsoleCapturer` -> `console.py` -> `test_console_capture.py` -> Verified.
- `FR-21` -> Task 1.10 -> Class `DeadClickDetector` -> `dead_click.py` -> `test_dead_click.py` -> Verified.

---

## 15. File-Level Implementation Contracts
- **File**: `vir_runtime/sensory/touch/human_sim.py`
  - **Purpose**: Mouse curve and human speed delay algorithms.
  - **Owner**: Coder
  - **Inputs / Outputs / Dependencies**: Depends on numpy or mathematical helper functions.
