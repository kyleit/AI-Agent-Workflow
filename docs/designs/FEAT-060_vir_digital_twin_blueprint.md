<!-- File path: docs/designs/FEAT-060_vir_digital_twin_blueprint.md -->

---
feature_id: FEAT-060
feature_name: Visual Intelligence Runtime — Digital Twin & Application State Model
status: reviewed
stage: blueprint
created_at: 2026-07-12
updated_at: 2026-07-12
previous_artifact: ../plans/FEAT-060_vir_digital_twin_plan.md
next_artifact: [Implementation (Source Code)](../../)
---

# Technical Design Blueprint & Implementation Contract – Digital Twin & Application State Model

## 0. Baseline Context & References
- **Memory Baseline**: Memory of state synchronization layouts and schema serialization routines.
- **RAG Query Summaries**: Digital Twin relies on the `AsyncEventBus` and `SQLite` modules declared in Phase 1 to persist states and dispatch update events.
- **Inspected Source Files**:
  - [FEAT-060 Plan](file:///e:/AgentsProject/docs/plans/FEAT-060_vir_digital_twin_plan.md)

---

## 1. File-by-File Analysis & Proposed Mutations

| File Path | Operation | Responsibility | Dependency | Impact & Risk |
| :--- | :--- | :--- | :--- | :--- |
| `vir_runtime/domain/twin.py` | Modify | Expand Digital Twin schemas structure to define all 11 dimension fields | None | High. System state core definition. |
| `vir_runtime/twin/consistency.py` | Create | Detect and flag contradictions across twin dimensions dynamically | `twin.py` | High. Contradiction engine foundation. |
| `vir_runtime/twin/history.py` | Create | Maintain a circular buffer of the past 50 updates per dimension | `twin.py` | Low. Stores historical runs. |
| `vir_runtime/twin/persistence.py` | Create | Manage SQLite serialization and database sync loops | `twin.py` | Medium. Persists twin updates. |
| `vir_runtime/twin/query.py` | Create | Provide clean read APIs for agents to consult the twin state | `twin.py` | Low. Exposes query interfaces. |
| `vir_runtime/twin/stale_monitor.py` | Create | Track update latency timestamps and raise alerts on expired properties | `twin.py` | Low. Audits data staleness. |

---

## 2. Target Folder Structure
```text
vir_runtime/
├── domain/
│   └── twin.py
└── twin/
    ├── consistency.py
    ├── history.py
    ├── persistence.py
    ├── query.py
    └── stale_monitor.py
```

---

## 3. Complete Class & Module Design

### 3.1 DigitalTwinManager
- **Class / Module Name**: `vir_runtime.twin.persistence.DigitalTwinManager`
  - **Responsibilities**: Load twin properties from database, update dimensions thread-safely using lock interfaces, trigger database updates.
  - **Constructor Parameters**:
    - `db_path: str`
  - **Public Methods**:
    - `async def update_dimension(dimension: str, value: Dict[str, Any]) -> None`
    - `async def get_dimension_value(dimension: str) -> Dict[str, Any]`
  - **Internal Methods**:
    - `async def _save_to_db(dimension: str, value: Dict[str, Any]) -> None`
  - **Dependencies**: `asyncio.Lock`, `vir_runtime.twin.history`

### 3.2 ConsistencyValidator
- **Class / Module Name**: `vir_runtime.twin.consistency.ConsistencyValidator`
  - **Responsibilities**: Apply structural contradiction checks across different dimension payloads.
  - **Constructor Parameters**: None.
  - **Public Methods**:
    - `def validate_consistency(dimensions: Dict[str, Dict[str, Any]]) -> List[Contradiction]`
  - **Internal Methods**:
    - `def _check_auth_vs_network(dimensions: Dict[str, Dict[str, Any]]) -> Optional[Contradiction]`

---

## 4. Detailed Interface Contracts

- **API Signature**: `async def update_dimension(dimension: str, value: Dict[str, Any]) -> None`
  - **Parameters**:
    - `dimension` (string matching one of the 11 dimensions, e.g. `visual`, `network`, `dom`)
    - `value` (payload dictionary containing property keys and updated values)
  - **Return Types**: None.
  - **Exceptions**:
    - `InvalidDimensionError` - If dimension key name is unmapped.
    - `UpdateConcurrencyLockError` - If locking waits exceed timeouts.

---

## 5. Configuration Schema

- **Target Schema**:
```yaml
twin:
  dimensions:
    active_dimensions: ["visual", "dom", "network", "auth", "route", "accessibility", "performance"]
  history_limit: 50
  staleness_timeout_seconds: 30
```

---

## 6. Database & Storage Design
- **Tables**:
  - `vir_digital_twin`:
    - `dimension_name` (TEXT, Primary Key)
    - `payload` (TEXT, JSON string)
    - `updated_at` (TEXT, ISO-8601)

---

## 7. Cache Architecture
- **Twin Properties Memory Cache**:
  - Local dictionary in `DigitalTwinManager` stores the latest state in RAM for immediate query lookups, avoiding SQLite hits.

---

## 8. Error Model

- **Exception Class**: `ContradictionDetectedError`
  - **Trigger Condition**: Consistency validator detects conflict between visual states and network response codes.
  - **Recovery Strategy**: Publish alert event to Event Bus, decrease local session confidence score, resume flow.
  - **Logging Requirements**: WARNING log highlighting conflicting fields.

---

## 9. Skill Integration Contracts
- None.

---

## 10. CLI & Runtime Contracts
- None.

---

## 11. Sequence Flows

- **State Update & Consistency Loop**:
  1. Observer fires `vir.sensory.network` update.
  2. `DigitalTwinManager` acquires lock for `network` dimension.
  3. Memory dictionary updated; SQLite save triggered.
  4. Lock released.
  5. `ConsistencyValidator` performs cross checks on dimensions.
  6. Inconsistencies found; `twin.inconsistency.detected` event published.

---

## 12. Security & Safety
- **Lock Deadlock prevention**: Lock acquisition timeout limits are configured to 2.0 seconds, resolving conflicts if handlers block execution trees.

---

## 13. Complete Test Matrix

| Requirement ID | Test Type | Test File Target | Mapped Component | Verification Assertion |
| :--- | :--- | :--- | :--- | :--- |
| `FR-01` | Unit Test | `tests/unit/test_twin_dimensions.py` | `twin.py` | `self.assertIn("visual", twin_data)` |
| `FR-03` | Unit Test | `tests/unit/test_consistency_rules.py` | `consistency.py` | `self.assertTrue(len(contradictions) > 0)` |

---

## 14. Requirement Traceability Matrix
- `FR-01` -> Task 1.1 -> Class `VIRDigitalTwin` -> `twin.py` -> `test_twin_dimensions.py` -> Verified.
- `FR-03` -> Task 1.3 -> Class `ConsistencyValidator` -> `consistency.py` -> `test_consistency_rules.py` -> Verified.

---

## 15. File-Level Implementation Contracts
- **File**: `vir_runtime/twin/consistency.py`
  - **Purpose**: Contradiction logic processor.
  - **Owner**: Architect
  - **Inputs / Outputs / Dependencies**: Depends on rules loaded from layouts configurations.
