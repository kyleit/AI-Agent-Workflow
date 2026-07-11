<!-- File path: docs/designs/FEAT-053_knowledge_runtime_first_refactor_blueprint.md -->

---
feature_id: FEAT-053
feature_name: Refactor AIWF Knowledge Retrieval to a Runtime-First Architecture
status: reviewed
stage: blueprint
created_at: 2026-07-11
updated_at: 2026-07-11
previous_artifact: ../plans/FEAT-053_knowledge_runtime_first_refactor_plan.md
next_artifact: [Implementation (Source Code)](../../)
---

# Technical Design Blueprint & Implementation Contract – Refactor AIWF Knowledge Retrieval to a Runtime-First Architecture

## 0. Baseline Context & References
- **Memory Baseline**: Memory confidence is High. Local context indicates database optimizations (WAL mode, schema initialization debouncer) have already been successfully applied to speed up execution.
- **RAG Query Summaries**: Existing knowledge retrieval patterns query `project_rag_search`, which relies on local Qdrant vectors and static fallback files.
- **Inspected Source Files**:
  - `skills/workflow-runtime/scripts/db.py` (L47-L80: Schema creation; L299-L349: Provider request insert logic).
  - `skills/workflow-runtime/scripts/context.py` (L236-L450: transcript synchronization loops).

## 1. File-by-File Analysis & Proposed Mutations
| File Path | Operation (Create/Modify/Delete/Rename) | Responsibility | Dependency | Impact & Risk |
| :--- | :--- | :--- | :--- | :--- |
| `skills/knowledge-runtime/scripts/knowledge_runtime.py` | Create | Centralized API orchestrator and entry point | Task 1.1 | Medium - Core retrieval pipeline replacement |
| `skills/workflow-runtime/scripts/db.py` | Modify | Implement schema and logic for QMD SQLite mapping tables | Task 1.2 | Low - Database table additions |
| `skills/knowledge-runtime/scripts/qdrant_client.py` | Create | Semantic Vector DB helper routing point lookups | Task 1.3 | Low - Client class wrapper |
| `skills/knowledge-runtime/scripts/obsidian_resolver.py` | Create | Targeted Markdown section reader | Task 1.4 | Low - File parser |
| `skills/knowledge-runtime/scripts/cache.py` | Create | TTL cache implementation using SQLite key-value fallback | Task 2.1 | Low - In-memory cache helper |
| `skills/workflow-runtime/scripts/workflow_runtime.py` | Modify | Register CLI subcommands `aiwf knowledge ...` | Task 2.2 | Medium - CLI entrypoints |
| `skills/project-rag-search/scripts/project_rag_search.py` | Modify | Port static JSON index search logic to Runtime API | Task 3.1 | High - System search compatibility |

## 2. Target Folder Structure
```text
.
├── skills/
│   ├── knowledge-runtime/
│   │   ├── SKILL.md
│   │   ├── scripts/
│   │   │   ├── knowledge_runtime.py
│   │   │   ├── qdrant_client.py
│   │   │   ├── obsidian_resolver.py
│   │   │   └── cache.py
│   │   └── tests/
│   │       ├── test_runtime_api.py
│   │       ├── test_qmd.py
│   │       └── test_cache.py
│   └── project-rag-search/
│       └── scripts/
│           └── project_rag_search.py
```

## 3. Complete Class & Module Design

### Module: `knowledge_runtime`
- **Class Name**: `KnowledgeRuntime`
  - **Responsibilities**: Orchestrate retrieval pipelines (Semantic -> QMD mapping -> Obsidian Resolver -> Context payload).
  - **Constructor Parameters**:
    - `workspace_root: str` (Defaults to `"."`)
  - **Public Methods**:
    - `def search(self, query: str, limit: int = 10) -> list[dict]`
    - `def lookup_document(self, doc_id: str) -> dict`
    - `def lookup_section(self, doc_id: str, section_title: str) -> str`
    - `def retrieve_context(self, query: str) -> str`
  - **Internal Methods**:
    - `def _semantic_search(self, query: str, limit: int) -> list[str]`
    - `def _filter_qmd(self, point_ids: list[str]) -> list[dict]`
    - `def _resolve_document_content(self, metadata: dict) -> str`
  - **Dependencies**: `QdrantSearchClient`, `QmdRepository`, `ObsidianResolver`, `RuntimeCache`.
  - **Extension Points**: Can be subclassed to override `_semantic_search` for alternative vector providers.

### Module: `qdrant_client`
- **Class Name**: `QdrantSearchClient`
  - **Responsibilities**: Establish local connections to Qdrant service and perform similarity query vector lookups.
  - **Constructor Parameters**:
    - `url: str`
    - `api_key: str = None`
  - **Public Methods**:
    - `def query_points(self, vector: list[float], limit: int = 10) -> list[str]`

### Module: `obsidian_resolver`
- **Class Name**: `ObsidianSectionResolver`
  - **Responsibilities**: Read targeted Markdown documents and extract precise sections matching header paths.
  - **Constructor Parameters**:
    - `vault_path: str`
  - **Public Methods**:
    - `def extract_section(self, file_path: str, heading: str) -> str`

### Module: `cache`
- **Class Name**: `RuntimeCache`
  - **Responsibilities**: Maintain atomic cache read/write mappings for embedding outputs and search payloads.
  - **Constructor Parameters**:
    - `db_path: str`
    - `ttl_seconds: int = 600`
  - **Public Methods**:
    - `def get(self, key: str) -> dict`
    - `def set(self, key: str, value: dict) -> None`
    - `def invalidate(self, key: str) -> None`

## 4. Detailed Interface Contracts
- **Search Signature**: `def search(self, query: str, limit: int = 10) -> list[dict]`
  - **Parameters**: `query` (Must be a non-empty string), `limit` (Must be an integer between 1 and 50, defaults to 10).
  - **Return Types**: `list[dict]` containing metadata keys (project_id, file_path, heading, score).
  - **Exceptions**: `QdrantConnectionError` raised when vector engine is unreachable.
- **Section Extraction Signature**: `def extract_section(self, file_path: str, heading: str) -> str`
  - **Parameters**: `file_path` (Absolute or relative system path), `heading` (Header text match).
  - **Return Types**: `str` representing the markdown block under the heading.
  - **Exceptions**: `FileNotFoundError` raised when document is missing.

## 5. Configuration Schema
- **Current Schema**: Configuration stored on files in `.agents/config/`.
- **Target Schema** (Stored in `permissions.json` or `.agents/config/knowledge.json`):
  ```json
  {
    "qdrant": {
      "host": "localhost",
      "port": 6333,
      "collection_name": "aiwf_knowledge"
    },
    "cache": {
      "enabled": true,
      "ttl_seconds": 600
    }
  }
  ```
- **Migration Rules**: Legacy search params defaults to localhost configuration schemas.

## 6. Database & Storage Design
- **Tables**:
  - `qmd_metadata`:
    - `point_id`: TEXT PRIMARY KEY
    - `project_id`: TEXT NOT NULL
    - `module`: TEXT
    - `feature_id`: TEXT
    - `file_path`: TEXT NOT NULL
    - `section_heading`: TEXT
    - `updated_at`: TEXT NOT NULL
    - `content_hash`: TEXT NOT NULL
- **Indexes**:
  - `idx_qmd_project_module` mapping `(project_id, module)`
- **Relationships / Constraints**: None (flat metadata mapping directory).
- **Migration & Rollback Strategy**: SQL DDL triggers run automatically on schema initialization.

## 7. Cache Architecture
- **Cache Keys**:
  - `kr:query:<query_hash>:<limit>`
  - `kr:doc:<doc_id_hash>`
- **Invalidation Rules**: Cache is invalidated on file changes (detected via content hash mismatches) or manual clear.
- **TTL**: 600 seconds.
- **Hash Strategy**: SHA-256 formatting.

## 8. Error Model
- **Exception Class**: `KnowledgeProviderUnavailableError`
  - **Trigger Condition**: When both SQLite QMD database and Qdrant are offline.
  - **Recovery Strategy**: Failover to local search using static JSON indexes and keyword lookups (Workspace Fallback).
  - **Retry Policy**: 3 retries with 50ms exponential backoff.
  - **Logging Requirements**: Warnings logged under runtime stderr namespaces.

## 9. Skill Integration Contracts
- **Skill Name**: `project-rag-search`
  - **Before Hooks**: Verify local runtime connection is active.
  - **After Hooks**: None.
  - **Runtime Calls**: Route query parameters via `KnowledgeRuntime.retrieve_context(query)`.
  - **Data Exchanged / Outputs**: Input string query -> Output markdown context block.

## 10. CLI & Runtime Contracts
- **Command Syntax**: `python workflow_runtime.py knowledge search --query "<search_string>" [--limit <num>]`
  - **Parameters**: `--query` (string, required), `--limit` (int, optional).
  - **Output**: JSON payload list of context blocks.
  - **Exit Codes**: 0 (success), 1 (missing params or connection failure).

## 11. Sequence Flows
- **Normal Execution Flow**:
  1. Client calls `retrieve_context(query)`.
  2. Runtime queries `RuntimeCache`. Cache hits return data instantly.
  3. Cache miss: Runtime calls Qdrant for semantic Top-K point IDs.
  4. Runtime queries SQLite QMD table to resolve Point IDs to file paths and section headings.
  5. Obsidian Section Resolver extracts content.
  6. Results saved in Cache and returned to Client.
- **Provider Unavailable Flow**:
  1. Semantic client throws `ConnectionRefusedError`.
  2. Runtime initiates Workspace Fallback.
  3. Offline keyword scanner reads static index JSON files and loads context.

## 12. Security & Safety
- **Workspace Boundary**: Sandbox enforcement applies. All resolved path outputs must be resolved inside the project workspace directory limits.
- **Path Validation**: Escape paths (`../`) are parsed and raising `ValueError` if pointing outside workspace root.

## 13. Complete Test Matrix
| Requirement ID | Test Type | Test File Target | Mapped Component | Verification Assertion |
| :--- | :--- | :--- | :--- | :--- |
| `FR-01` | Unit Test | `skills/knowledge-runtime/tests/test_runtime_api.py` | `knowledge_runtime.py` | `self.assertIsNotNone(result)` |
| `FR-02` | Unit Test | `skills/knowledge-runtime/tests/test_qmd.py` | `db.py` | `self.assertEqual(row[0], expected_path)` |
| `FR-05` | Unit Test | `skills/knowledge-runtime/tests/test_cache.py` | `cache.py` | Cache hit returns stale data after TTL threshold. |

## 14. Requirement Traceability Matrix
- `FR-01` -> Task 1.1 -> Class `KnowledgeRuntime` -> `knowledge_runtime.py` -> `test_runtime_api.py` -> Verified -> Released.
- `FR-02` -> Task 1.2 -> Schema `qmd_metadata` -> `db.py` -> `test_qmd.py` -> Verified -> Released.
- `FR-05` -> Task 2.1 -> Class `RuntimeCache` -> `cache.py` -> `test_cache.py` -> Verified -> Released.

## 15. File-Level Implementation Contracts
- **File**: `skills/knowledge-runtime/scripts/knowledge_runtime.py`
  - **Purpose**: Unified orchestrator class resolving queries.
  - **Owner**: Coder.
  - **Inputs / Outputs / Dependencies**: Depends on `qdrant_client.py` and `obsidian_resolver.py`.
- **File**: `skills/workflow-runtime/scripts/db.py`
  - **Purpose**: Schema migrations for QMD tables.
  - **Owner**: Database Developer.
