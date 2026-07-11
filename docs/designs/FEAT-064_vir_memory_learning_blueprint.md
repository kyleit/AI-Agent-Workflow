<!-- File path: docs/designs/FEAT-064_vir_memory_learning_blueprint.md -->

---
feature_id: FEAT-064
feature_name: Visual Intelligence Runtime — Memory Architecture & Continuous Learning
status: reviewed
stage: blueprint
created_at: 2026-07-12
updated_at: 2026-07-12
previous_artifact: ../plans/FEAT-064_vir_memory_learning_plan.md
next_artifact: [Implementation (Source Code)](../../)
---

# Technical Design Blueprint & Implementation Contract – Memory Architecture & Continuous Learning

## 0. Baseline Context & References
- **Memory Baseline**: Memory of vector databases schemas, SQLite transaction models, and continuous learning feedback weights.
- **RAG Query Summaries**: Memory Engine leverages local `SQLite` files defined in Phase 3 to index baselines and manage agent memory pools.
- **Inspected Source Files**:
  - [FEAT-064 Plan](file:///e:/AgentsProject/docs/plans/FEAT-064_vir_memory_architecture_and_continuous_learning_plan.md)

---

## 1. File-by-File Analysis & Proposed Mutations

| File Path | Operation | Responsibility | Dependency | Impact & Risk |
| :--- | :--- | :--- | :--- | :--- |
| `vir_runtime/memory/adapter.py` | Create | Abstract class defining MemoryAdapter storage API boundaries | None | High. Backbone of all persistence storage modules. |
| `vir_runtime/memory/sqlite_db.py` | Create | Manage SQLite session transaction pools, enabling WAL mode | `adapter.py` | High. Core database manager. |
| `vir_runtime/memory/qdrant_db.py` | Create | Connect and query Qdrant collection vectors for semantic search | `adapter.py` | Medium. Connects semantic memory layers. |
| `vir_runtime/memory/agent_memory.py` | Create | Handle Short-term, Working, and SQLite Long-term memory syncs | `sqlite_db.py` | High. Manages agent memory states. |
| `vir_runtime/memory/baselines.py` | Create | Manage visual baseline captures, indexing, versions, and gates | `sqlite_db.py` | High. Baseline checker controller. |
| `vir_runtime/memory/fingerprint.py` | Create | Generate deterministic hashes of page layouts DOM structures | None | Low. Generates fingerprint signatures. |
| `vir_runtime/memory/learning.py` | Create | Extract LearningOutcomes, generate vectors, and sync to Obsidian | `qdrant_db.py` | Medium. Continuously learns from bugs. |

---

## 2. Target Folder Structure
```text
vir_runtime/
└── memory/
    ├── adapter.py
    ├── baselines.py
    ├── fingerprint.py
    ├── learning.py
    ├── qdrant_db.py
    ├── sqlite_db.py
    └── agent_memory.py
```

---

## 3. Complete Class & Module Design

### 3.1 MemoryAdapter (Abstract Class)
- **Class / Module Name**: `vir_runtime.memory.adapter.MemoryAdapter`
  - **Responsibilities**: Declare storage method contracts (save, retrieve, delete) for files, database rows, and vectors.
  - **Public Methods**:
    - `async def store_binary(category: str, key: str, data: bytes) -> str`
    - `async def query_metadata(sql: str, params: tuple) -> List[tuple]`
    - `async def find_similar_vectors(embedding: List[float], limit: int) -> List[Dict[str, Any]]`

### 3.2 BaselineManager
- **Class / Module Name**: `vir_runtime.memory.baselines.BaselineManager`
  - **Responsibilities**: Save baseline screenshots, check pixels regression bounds, classify regression severity, and trigger human approval gates.
  - **Constructor Parameters**:
    - `sqlite_db: SQLiteDatabase`
  - **Public Methods**:
    - `async def get_active_baseline(feature_id: str, route: str, viewport: str) -> Optional[bytes]`
    - `async def check_regression(current_png: bytes, baseline_png: bytes) -> str`
    - `async def promote_new_baseline(feature_id: str, route: str, viewport: str, data: bytes) -> None`

### 3.3 LearningEngine
- **Class / Module Name**: `vir_runtime.memory.learning.LearningEngine`
  - **Responsibilities**: Parse `LearningOutcome` attributes on session end, query OpenAI/Gemini embeddings, store in Qdrant collections, promote outcomes.
  - **Constructor Parameters**:
    - `qdrant_db: QdrantDatabase`
  - **Public Methods**:
    - `async def process_investigation_close(session_details: Dict[str, Any]) -> None`

---

## 4. Detailed Interface Contracts

- **API Signature**: `async def check_regression(current_png: bytes, baseline_png: bytes) -> str`
  - **Parameters**:
    - `current_png` (captured viewport image bytes)
    - `baseline_png` (stored baseline template image bytes)
  - **Return Types**: Returns a string status code (`NO_CHANGE`, `MINOR_SHIFT`, `VISUAL_REGRESSION`, or `CRITICAL_REGRESSION`).
  - **Exceptions**:
    - `BaselineCorruptedError` - If baseline file contains empty binary records.

---

## 5. Configuration Schema

- **Target Schema (`memory.yaml`)**:
```yaml
memory:
  sqlite:
    wal_mode: true
    connection_timeout_seconds: 5
  qdrant:
    url: "http://localhost:6333"
    collection: "vir_visual_memory"
  baselines:
    max_auto_update_diff_percent: 5.0
    require_human_gate_diff_percent: 30.0
```

---

## 6. Database & Storage Design
- **Tables**:
  - `vir_baselines`:
    - `baseline_id` (TEXT, Primary Key)
    - `feature_id` (TEXT)
    - `page_route` (TEXT)
    - `viewport` (TEXT)
    - `git_commit` (TEXT)
    - `file_path` (TEXT)
    - `updated_at` (TEXT)

---

## 7. Cache Architecture
- **DOM Fingerprints Cache**:
  - Memory mapping table caches DOM structures hashes to avoid running regression calculations if page layouts haven't mutated.

---

## 8. Error Model

- **Exception Class**: `BaselineUpdateBlockedError`
  - **Trigger Condition**: Diff ratio of new baseline exceeds 30% without human gate authorization confirmation.
  - **Recovery Strategy**: Raise warning, block PASS status, preserve current baseline images.
  - **Logging Requirements**: WARNING log referencing the target feature ID.

---

## 9. Skill Integration Contracts
- None.

---

## 10. CLI & Runtime Contracts
- None.

---

## 11. Sequence Flows

- **Continuous Learning Flow**:
  1. `ThinkingPipeline` transitions investigation status to `RESOLVED`.
  2. `LearningEngine` parses session logs, creating `LearningOutcome` objects.
  3. Out-of-bounds check runs: outcomes confidence > 0.8.
  4. Outcomes promoted to Knowledge Runtime; vector embedded and posted to Qdrant collection.
  5. Obsidian Markdown report exported.
  6. Feedback loops run: agent authority weights boosted inside configs.

---

## 12. Security & Safety
- **Vector boundaries validation**: Raw screenshot binary data is strictly blocked from posting to Qdrant collections, saving only layout coordinates references to prevent leak of private application UI details.

---

## 13. Complete Test Matrix

| Requirement ID | Test Type | Test File Target | Mapped Component | Verification Assertion |
| :--- | :--- | :--- | :--- | :--- |
| `FR-11` | Unit Test | `tests/unit/test_baseline_versions.py` | `baselines.py` | `self.assertEqual(active_path, target_path)` |
| `FR-14` | Unit Test | `tests/unit/test_baseline_veto_gate.py` | `baselines.py` | `self.assertRaises(BaselineUpdateBlockedError)` |

---

## 14. Requirement Traceability Matrix
- `FR-11` -> Task 1.11 -> Class `BaselineManager` -> `baselines.py` -> `test_baseline_versions.py` -> Verified.
- `FR-14` -> Task 1.15 -> Class `BaselineManager` -> `baselines.py` -> `test_baseline_veto_gate.py` -> Verified.

---

## 15. File-Level Implementation Contracts
- **File**: `vir_runtime/memory/learning.py`
  - **Purpose**: LearningOutcome packaging and Obsidian exporter routine.
  - **Owner**: Coder
  - **Inputs / Outputs / Dependencies**: Depends on Qdrant database clients libraries.
