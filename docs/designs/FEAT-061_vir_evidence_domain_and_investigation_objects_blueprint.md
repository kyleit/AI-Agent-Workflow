<!-- File path: docs/designs/FEAT-061_vir_evidence_domain_and_investigation_objects_blueprint.md -->

---
feature_id: FEAT-061
feature_name: Visual Intelligence Runtime — Evidence Domain & Investigation Objects
status: reviewed
stage: blueprint
created_at: 2026-07-12
updated_at: 2026-07-12
previous_artifact: ../plans/FEAT-061_vir_evidence_domain_and_investigation_objects_plan.md
next_artifact: [Implementation (Source Code)](../../)
---

# Technical Design Blueprint & Implementation Contract – Evidence Domain & Investigation Objects

## 0. Baseline Context & References
- **Memory Baseline**: Memory of evidence schemas and database table relations.
- **RAG Query Summaries**: Evidence entities map to SQLite tables initialized in Phase 1, using asyncio locks to ensure write safety.
- **Inspected Source Files**:
  - [FEAT-061 Plan](file:///e:/AgentsProject/docs/plans/FEAT-061_vir_evidence_domain_and_investigation_objects_plan.md)

---

## 1. File-by-File Analysis & Proposed Mutations

| File Path | Operation | Responsibility | Dependency | Impact & Risk |
| :--- | :--- | :--- | :--- | :--- |
| `vir_runtime/domain/evidence.py` | Create | Define immutable Evidence dataclass schema structure (frozen=True) | None | High. Core entity contract. |
| `vir_runtime/domain/evidence_engine.py` | Create | Manage runtime collection and queries of evidence streams | `evidence.py` | High. Aggregates bus data. |
| `vir_runtime/domain/investigation.py` | Create | Define structural features and states of active investigations | `evidence.py` | Medium. Manages hypotheses data. |
| `vir_runtime/domain/db_schema.sql` | Create | Define table schemas representing investigations and evidence | None | High. SQLite database foundation. |
| `vir_runtime/domain/confidence.py` | Create | Calculate session confidence scores from multiple evidence records | None | Low. Confidence math calculator. |
| `vir_runtime/domain/timeline.py` | Create | Form sequential chronological history tracks of events | `evidence.py` | Low. Output formatter. |
| `vir_runtime/domain/correlator.py` | Create | Map logs or network exceptions to visual DOM target elements | `evidence.py` | Medium. Connects console to DOM nodes. |

---

## 2. Target Folder Structure
```text
vir_runtime/
└── domain/
    ├── confidence.py
    ├── correlator.py
    ├── db_schema.sql
    ├── evidence.py
    ├── evidence_engine.py
    ├── investigation.py
    └── timeline.py
```

---

## 3. Complete Class & Module Design

### 3.1 Evidence (Dataclass)
- **Class / Module Name**: `vir_runtime.domain.evidence.Evidence`
  - **Responsibilities**: Represent a single immutable sensory finding.
  - **Constructor Parameters**:
    - `evidence_id: str` (UUID)
    - `source_agent: str`
    - `classification: str` (e.g. `visual`, `network`, `console`)
    - `payload: Dict[str, Any]`
    - `timestamp: float`
    - `linked_evidence_ids: List[str]`

### 3.2 EvidenceEngine
- **Class / Module Name**: `vir_runtime.domain.evidence_engine.EvidenceEngine`
  - **Responsibilities**: Subscribe to topic `vir.evidence.new`, save records to SQLite table, provide query APIs.
  - **Constructor Parameters**:
    - `db_path: str`
  - **Public Methods**:
    - `async def add_evidence(evidence: Evidence) -> None`
    - `async def query_evidence(filter_criteria: Dict[str, Any]) -> List[Evidence]`
  - **Dependencies**: `vir_runtime.domain.evidence`

### 3.3 Investigation (Dataclass)
- **Class / Module Name**: `vir_runtime.domain.investigation.Investigation`
  - **Responsibilities**: Represent a session investigation lifecycle, tracking hypotheses and active symptoms.
  - **Properties**:
    - `investigation_id: str`
    - `feature_id: str`
    - `status: str` (OPEN | HYPOTHESIZING | VERIFYING | RESOLVED)
    - `symptoms: List[str]`
    - `hypotheses: List[Dict[str, Any]]`

---

## 4. Detailed Interface Contracts

- **API Signature**: `async def add_evidence(evidence: Evidence) -> None`
  - **Parameters**:
    - `evidence` (valid immutable Evidence instance object)
  - **Return Types**: None.
  - **Exceptions**:
    - `InvalidEvidencePayloadError` - If payload fails validator schema checks.

---

## 5. Configuration Schema

- **Target Schema**:
```yaml
evidence:
  database_path: ".agents/visual-runtime/vir_state.db"
  auto_cleanup_days: 90
```

---

## 6. Database & Storage Design
- **Tables**:
  - `vir_evidence`:
    - `evidence_id` (TEXT, Primary Key, UUID)
    - `source_agent` (TEXT)
    - `classification` (TEXT)
    - `payload` (TEXT, JSON string)
    - `timestamp` (REAL)
  - `vir_investigations`:
    - `investigation_id` (TEXT, Primary Key)
    - `status` (TEXT)
    - `feature_id` (TEXT)

---

## 7. Cache Architecture
- **In-Memory Evidence Cache**:
  - Local dictionary caches the past 200 evidence objects in memory for high-speed correlation checks.

---

## 8. Error Model

- **Exception Class**: `ContradictionDetectedError`
  - **Trigger Condition**: Add evidence event contradicts current Digital Twin state properties.
  - **Recovery Strategy**: Create anomaly records, lower investigation confidence scores, and flag warning.
  - **Logging Requirements**: WARNING log referencing the conflicting UUID codes.

---

## 9. Skill Integration Contracts
- None.

---

## 10. CLI & Runtime Contracts
- None.

---

## 11. Sequence Flows

- **Evidence Storage & Correlation Flow**:
  1. Observer fires `Evidence` to Event Bus.
  2. `EvidenceEngine` receives payload and writes to SQLite database.
  3. `EvidenceCorrelator` maps network exceptions to DOM bounding coordinates.
  4. Timeline updater appends event.

---

## 12. Security & Safety
- **SQL Injection Prevention**: All database inserts use SQL placeholder parameters (`?`), protecting against untrusted inputs inside payload dicts.

---

## 13. Complete Test Matrix

| Requirement ID | Test Type | Test File Target | Mapped Component | Verification Assertion |
| :--- | :--- | :--- | :--- | :--- |
| `FR-03` | Unit Test | `tests/unit/test_immutability.py` | `evidence.py` | `self.assertRaises(AttributeError)` |
| `FR-14` | Unit Test | `tests/unit/test_confidence_aggregate.py` | `confidence.py` | `self.assertEqual(score, 0.85)` |

---

## 14. Requirement Traceability Matrix
- `FR-03` -> Task 1.3 -> Class `Evidence` -> `evidence.py` -> `test_immutability.py` -> Verified.
- `FR-14` -> Task 1.11 -> Class `ConfidenceCalculator` -> `confidence.py` -> `test_confidence_aggregate.py` -> Verified.

---

## 15. File-Level Implementation Contracts
- **File**: `vir_runtime/domain/correlator.py`
  - **Purpose**: Map console outputs to DOM visual coordinate elements.
  - **Owner**: Coder
  - **Inputs / Outputs / Dependencies**: Depends on DOM bounding box parameters.
