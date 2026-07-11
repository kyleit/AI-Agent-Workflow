<!-- File path: docs/designs/FEAT-066_vir_quality_gates_reporting_blueprint.md -->

---
feature_id: FEAT-066
feature_name: Visual Intelligence Runtime — Quality Gates & Reporting System
status: reviewed
stage: blueprint
created_at: 2026-07-12
updated_at: 2026-07-12
previous_artifact: ../plans/FEAT-066_vir_quality_gates_and_reporting_system_plan.md
next_artifact: [Implementation (Source Code)](../../)
---

# Technical Design Blueprint & Implementation Contract – Quality Gates & Reporting System

## 0. Baseline Context & References
- **Memory Baseline**: Memory of report templates schemas and zip packaging scripts.
- **RAG Query Summaries**: Quality Gate consumes `ConsensusRecord` structures defined in Phase 6, outputting results path files inside `docs/verification/` bounds.
- **Inspected Source Files**:
  - [FEAT-066 Plan](file:///e:/AgentsProject/docs/plans/FEAT-066_vir_quality_gates_and_reporting_system_plan.md)

---

## 1. File-by-File Analysis & Proposed Mutations

| File Path | Operation | Responsibility | Dependency | Impact & Risk |
| :--- | :--- | :--- | :--- | :--- |
| `vir_runtime/quality/gate.py` | Create | Evaluate ConsensusRecords against threshold constraints dynamically | None | High. Final verification gate parser. |
| `vir_runtime/quality/exit_codes.py` | Create | Map Quality Gate results (PASS, FAIL, BLOCKED) to CLI exit statuses | `gate.py` | Low. Configures script environments. |
| `vir_runtime/quality/override.py` | Create | Manage human override gates logs and validations | None | Medium. Intercepts CI approvals. |
| `vir_runtime/reporting/engine.py` | Create | Generate MD and JSON reports asynchronously | None | High. Commits findings reports. |
| `.agents/visual-runtime/templates/report.md` | Create | Layout structure definitions for Markdown results templates | None | Low. Static Markdown format rules. |
| `vir_runtime/reporting/telemetry.py` | Create | Record peak system resource metrics (peak RAM, CPU usage) | None | Low. Collects system footprints. |
| `vir_runtime/reporting/packager.py` | Create | Compress screenshots and report files into zip packages | `engine.py` | Medium. Dynamic artifact archiver. |

---

## 2. Target Folder Structure
```text
.agents/
└── visual-runtime/
    └── templates/
        └── report.md
vir_runtime/
├── quality/
│   ├── exit_codes.py
│   ├── gate.py
│   └── override.py
└── reporting/
    ├── engine.py
    ├── packager.py
    └── telemetry.py
```

---

## 3. Complete Class & Module Design

### 3.1 QualityGateEvaluator
- **Class / Module Name**: `vir_runtime.quality.gate.QualityGateEvaluator`
  - **Responsibilities**: Apply thresholds to domain confidence scores, check for active VETOs, resolve final status.
  - **Constructor Parameters**:
    - `thresholds: Dict[str, float]`
  - **Public Methods**:
    - `def evaluate_gate(record: ConsensusRecord) -> str` - Returns `PASS`, `PARTIAL`, `FAIL`, or `BLOCKED`.
  - **Dependencies**: `vir_runtime.quality.exit_codes`

### 3.2 ReportPublisher
- **Class / Module Name**: `vir_runtime.reporting.engine.ReportPublisher`
  - **Responsibilities**: Assemble complete diagnostic arrays, calculate relative file paths for linked images, format SVG timeline charts, write results.
  - **Constructor Parameters**:
    - `template_path: str`
  - **Public Methods**:
    - `async def publish_report(session_details: Dict[str, Any], path_slug: str) -> Tuple[str, str]` - Returns tuple of `(md_path, json_path)`.
  - **Internal Methods**:
    - `def _render_svg_timeline(timeline_events: List[Dict[str, Any]]) -> str`
  - **Dependencies**: `vir_runtime.reporting.telemetry`, `vir_runtime.reporting.packager`

---

## 4. Detailed Interface Contracts

- **API Signature**: `def evaluate_gate(record: ConsensusRecord) -> str`
  - **Parameters**:
    - `record` (ConsensusRecord payload details object)
  - **Return Types**: Returns a string status code (`PASS`, `PARTIAL`, `FAIL`, or `BLOCKED`).
  - **Exceptions**:
    - `InvalidConsensusRecordError` - If input record lacks confidence scores map.

---

## 5. Configuration Schema

- **Target Schema**:
```yaml
quality_gate:
  thresholds:
    visual_regression: 0.90
    accessibility: 1.00
    design: 0.80
  override_allowed: true
```

---

## 6. Database & Storage Design
- Reports list indexes and session overrides history are saved to the `vir_sessions` SQLite tables.

---

## 7. Cache Architecture
- No cache mechanisms defined.

---

## 8. Error Model

- **Exception Class**: `QualityGateException`
  - **Trigger Condition**: Input consensus object is empty or corrupted.
  - **Recovery Strategy**: Force exit status to `BLOCKED`, write alert logs.
  - **Logging Requirements**: ERROR log outlining target feature ID.

---

## 9. Skill Integration Contracts
- None.

---

## 10. CLI & Runtime Contracts
- **Exit Codes**:
  - `0` - PASS or PARTIAL
  - `1` - FAIL
  - `2` - BLOCKED

---

## 11. Sequence Flows

- **Quality Validation & Archiving Flow**:
  1. `QualityGateEvaluator` checks `ConsensusRecord` against thresholds.
  2. Gate result and exit status computed.
  3. `TelemetryCollector` gathers peak RAM/CPU details.
  4. Asynchronous `ReportPublisher` render loop triggered.
  5. SVG charts generated; MD and JSON reports written.
  6. `ZipPackager` compiles session folders.

---

## 12. Security & Safety
- **Report paths validation**: The reporting engine verifies output folders are strictly nested inside `docs/verification/` and `.agents/visual-runtime/` directories, preventing path traversals.

---

## 13. Complete Test Matrix

| Requirement ID | Test Type | Test File Target | Mapped Component | Verification Assertion |
| :--- | :--- | :--- | :--- | :--- |
| `FR-01` | Unit Test | `tests/unit/test_gate_evaluation.py` | `gate.py` | `self.assertEqual(result, "FAIL")` |
| `FR-10` | Unit Test | `tests/unit/test_report_schema.py` | `engine.py` | `self.assertTrue(validate_json_schema(json_data))` |

---

## 14. Requirement Traceability Matrix
- `FR-01` -> Task 1.1 -> Class `QualityGateEvaluator` -> `gate.py` -> `test_gate_evaluation.py` -> Verified.
- `FR-10` -> Task 1.10 -> Class `ReportPublisher` -> `engine.py` -> `test_report_schema.py` -> Verified.

---

## 15. File-Level Implementation Contracts
- **File**: `vir_runtime/reporting/packager.py`
  - **Purpose**: Compile session artifacts into standard ZIP folders.
  - **Owner**: Coder
  - **Inputs / Outputs / Dependencies**: Depends on python `zipfile` standard libraries.
