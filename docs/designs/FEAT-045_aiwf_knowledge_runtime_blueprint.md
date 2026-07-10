<!-- File path: docs/designs/FEAT-045_aiwf_knowledge_runtime_blueprint.md -->

---
feature_id: FEAT-045
feature_name: AIWF Knowledge Runtime
status: reviewed
stage: blueprint
created_at: 2026-07-09
updated_at: 2026-07-09
previous_artifact: ../plans/FEAT-045_aiwf_knowledge_runtime_plan.md
next_artifact: [Implementation (Source Code)](../../)
---

# Technical Design Blueprint & Implementation Contract – AIWF Knowledge Runtime

## 0. Baseline Context & References
- **Memory Baseline**: FRESH — Đã nạp từ tệp `project-summary.md` và `memory-state.json`.
- **JSON Plan Resource**: Nạp trực tiếp từ `docs/plans/FEAT-045_aiwf_knowledge_runtime_plan.json`.
- **Inspected Source Files**:
  - `skills/project-rag-search/scripts/search.py`
  - `skills/project-memory-bootstrap/scripts/keyword_index.py`

## 1. File-by-File Analysis & Proposed Mutations
| File Path | Operation (Create/Modify/Delete/Rename) | Responsibility | Dependency | Impact & Risk |
| :--- | :--- | :--- | :--- | :--- |
| `skills/knowledge-runtime/scripts/knowledge_runtime/__init__.py` | Create | Khởi tạo gói python `knowledge_runtime`. | Không | Thấp |
| `skills/knowledge-runtime/scripts/knowledge_runtime/api.py` | Create | Expose API chính và định tuyến tìm kiếm. | `BaseProvider` | Cao |
| `skills/knowledge-runtime/scripts/knowledge_runtime/providers/base.py` | Create | Abstract base class `BaseProvider`. | Không | Thấp |
| `skills/knowledge-runtime/scripts/knowledge_runtime/providers/markdown.py` | Create | Markdown Provider đọc/lập chỉ mục MD workspace. | `BaseProvider` | Thấp |
| `skills/knowledge-runtime/scripts/knowledge_runtime/providers/sqlite.py` | Create | SQLite Provider lưu trữ chỉ mục và cache. | `BaseProvider` | Trung bình |
| `skills/knowledge-runtime/scripts/knowledge_runtime/providers/vector.py` | Create | VectorDB Provider kết nối Qdrant REST. | `BaseProvider` | Trung bình |
| `skills/knowledge-runtime/scripts/knowledge_runtime/providers/obsidian.py` | Create | Obsidian Provider kết nối REST Obsidian. | `BaseProvider` | Trung bình |
| `skills/knowledge-runtime/scripts/knowledge_runtime/cache.py` | Create | Cache Layer cục bộ & invalidation. | Không | Thấp |
| `skills/knowledge-runtime/scripts/knowledge_runtime/index.py` | Create | Backlinks indexer & Lessons learned parser. | Không | Trung bình |
| `skills/knowledge-runtime/scripts/knowledge_runtime/analyzer.py` | Create | Quality Analyzer phát hiện lỗi tri thức. | Không | Thấp |

## 2. Target Folder Structure
```text
.
└── skills
    └── knowledge-runtime
        └── scripts
            └── knowledge_runtime
                ├── __init__.py
                ├── api.py
                ├── cache.py
                ├── index.py
                ├── analyzer.py
                └── providers
                    ├── __init__.py
                    ├── base.py
                    ├── markdown.py
                    ├── sqlite.py
                    ├── vector.py
                    └── obsidian.py
```

## 3. Complete Class Contracts

### Class `KnowledgeAPI`
- **Responsibilities**: Giao diện cổng chính cung cấp API tìm kiếm ngữ nghĩa, keyword và backlinks cho hệ thống.
- **Constructor**: `def __init__(self, config_path: str = ".agents/memory.config.json")`
- **Public Methods**:
  - `def search(self, query: str, limit: int = 5) -> list[dict]` (Visibility: public)
  - `def read(self, path: str) -> str` (Visibility: public)
  - `def save(self, path: str, content: str) -> bool` (Visibility: public)
- **Internal Methods**:
  - `def _load_provider(self) -> BaseProvider` (Visibility: internal)
- **Dependencies**: `BaseProvider`, `CacheManager`.
- **Lifecycle & State Ownership**: Khởi tạo cùng phiên làm việc của đại lý. Quản lý trạng thái kết nối của Provider hiện hành.

### Class `BaseProvider`
- **Responsibilities**: Định nghĩa giao diện chung cho các nhà cung cấp tri thức.
- **Constructor**: `def __init__(self)`
- **Public Methods**:
  - `def search(self, query: str, limit: int = 5) -> list[dict]`
  - `def read(self, path: str) -> str`
  - `def save(self, path: str, content: str) -> bool`
- **Internal Methods**: None
- **Dependencies**: None
- **Extension Points**: Mọi Provider mới (ví dụ như PostgresProvider sau này) bắt buộc kế thừa từ `BaseProvider`.

### Class `MarkdownProvider(BaseProvider)`
- **Responsibilities**: Thực thi tìm kiếm từ khóa cục bộ và đọc file markdown thô trong workspace.
- **Constructor**: `def __init__(self, workspace_root: str = ".")`
- **Public Methods**: Override `search()`, `read()`, `save()`.
- **Internal Methods**:
  - `def _scan_workspace(self) -> list[str]`
- **Dependencies**: Thư viện hệ thống `os`, `fnmatch`.

### Class `SQLiteProvider(BaseProvider)`
- **Responsibilities**: Quản lý lưu trữ cache và lập chỉ mục FTS5 cho Markdown trong SQLite.
- **Constructor**: `def __init__(self, db_path: str = ".agents/state/knowledge.db")`
- **Public Methods**: Override `search()`, `read()`, `save()`.
- **Internal Methods**:
  - `def _init_db(self) -> None`
- **Dependencies**: `sqlite3`

### Class `VectorDBProvider(BaseProvider)`
- **Responsibilities**: Kết nối và thực thi truy vấn vector ngữ nghĩa đến Qdrant DB.
- **Constructor**: `def __init__(self, host: str = "localhost", port: int = 6333)`
- **Public Methods**: Override `search()`, `read()`, `save()`.
- **Internal Methods**:
  - `def _request(self, endpoint: str, payload: dict) -> dict`
- **Dependencies**: HTTP client `urllib.request`.

### Class `ObsidianProvider(BaseProvider)`
- **Responsibilities**: Kết nối Obsidian REST Local API đồng bộ backlinks.
- **Constructor**: `def __init__(self, port: int = 27124, token: str = "")`
- **Public Methods**: Override `search()`, `read()`, `save()`.
- **Internal Methods**: None
- **Dependencies**: HTTP client `urllib.request`.

### Class `CacheManager`
- **Responsibilities**: Quản lý JSON cache đệm cục bộ và invalidation.
- **Constructor**: `def __init__(self, ttl: int = 600)`
- **Public Methods**:
  - `def get(self, key: str) -> list[dict] | None`
  - `def set(self, key: str, value: list[dict]) -> None`
  - `def invalidate_all(self) -> None`
- **Internal Methods**: None
- **Dependencies**: None

### Class `KnowledgeIndexer`
- **Responsibilities**: Phân tích cú pháp và lập chỉ mục backlinks, lessons thô thành đồ thị.
- **Constructor**: `def __init__(self)`
- **Public Methods**:
  - `def build_graph(self) -> dict`
  - `def extract_lessons(self, text: str) -> list[str]`
- **Internal Methods**: None
- **Dependencies**: `re`

### Class `QualityAnalyzer`
- **Responsibilities**: Phân tích chất lượng các tài liệu tri thức (tìm tệp tin mồ côi, liên kết hỏng).
- **Constructor**: `def __init__(self)`
- **Public Methods**:
  - `def check_orphans(self) -> list[str]`
  - `def check_broken_links(self) -> list[dict]`
- **Internal Methods**: None
- **Dependencies**: `KnowledgeIndexer`

## 4. Detailed Interface Contracts
- **API Signature**: `def search(query: str, limit: int = 5) -> list[dict]`
  - **Parameters**: `query` (str, required), `limit` (int, default=5, min=1, max=100)
  - **Return Types**: `list[dict]` (mảng các kết quả khớp, mỗi kết quả chứa `path`, `snippet`, `score`).
  - **Exceptions**: `ValueError` (nếu query rỗng), `ProviderUnavailableException` (nếu provider bị lỗi mạng).
  - **Validation Rules**: Query không được chứa ký tự độc hại.
  - **Compatibility Notes**: Giữ nguyên tham số cấu hình tương thích ngược với RAG Search cũ.

## 5. Configuration Schema
- **Current Schema**: Không có schema cũ.
- **Target Schema**: `.agents/memory.config.json`
  ```json
  {
    "active_provider": "markdown",
    "cache_enabled": true,
    "cache_ttl": 600,
    "sqlite": {
      "db_path": ".agents/state/knowledge.db"
    }
  }
  ```
- **Migration Rules**: Khởi tạo mặc định nếu tệp cấu hình không tồn tại.

## 6. Database & Storage Design
- **Tables**:
  - `cache`: `(key TEXT PRIMARY KEY, value TEXT, expires_at INTEGER)`
  - `backlinks`: `(source TEXT, target TEXT, PRIMARY KEY (source, target))`
- **Indexes**: `idx_cache_expires` on `cache(expires_at)`
- **Relationships / Constraints**: Không có khóa ngoại phức tạp.
- **Migration & Rollback**: Tự động chạy lệnh SQL DDL `CREATE TABLE` khi cài đặt. Rollback bằng cách xóa tệp SQLite.
- **Expected Growth & Maintenance**: Cache được tự động dọn dẹp định kỳ khi CLI khởi chạy. Kích thước dự kiến < 10MB sau 1 tháng.

## 7. Cache Architecture
- **Cache Keys**: Hash SHA-256 của chuỗi truy vấn kết hợp limit.
- **Invalidation Rules**: Cache tự động hết hạn khi quá TTL. Bất kỳ lệnh ghi file nào cũng invalid toàn bộ cache để tránh dữ liệu cũ (stale data).
- **TTL**: Mặc định 600s.
- **Hash Strategy**: SHA-256 hex digest.
- **Warmup & Cleanup**: Warmup bằng cách nạp trước các file Markdown quan trọng của dự án.

## 8. Error Model
- **Exception Class**: `ProviderUnavailableException`
  - **Trigger Condition**: Lỗi kết nối HTTP tới Qdrant/Obsidian.
  - **Recovery Strategy**: Cảnh báo hệ thống và tự động fallback về `MarkdownProvider` cục bộ.
  - **Retry Policy**: Tối đa 2 lần thử lại, cách nhau 500ms.
  - **Logging**: Log Warning ghi stacktrace và nguyên nhân.

## 9. Skill Integration Contracts
- **Affected Skills**: `brainstorming`, `planning`, `blueprint`
  - **Before Hooks**: Kiểm tra tính khả dụng của API tri thức.
  - **After Hooks**: Cập nhật chỉ mục backlinks nếu tệp tri thức thay đổi.
  - **Runtime Calls**: Thay thế việc đọc file trực tiếp bằng cuộc gọi API `knowledge.search()`.

## 10. CLI & Runtime Contracts
- **Command Syntax**: `python workflow_runtime.py knowledge search "<query>"`
  - **Arguments**: `<query>` (chuỗi tìm kiếm)
  - **Outputs**: Trả về chuỗi kết quả định dạng JSON.
  - **Exit Codes**: 0 (thành công), 1 (lỗi tham số hoặc lỗi chạy chính).

## 11. Sequence Flows
- **Normal Execution Flow**:
  Client gọi `search()` -> Trả kết quả từ JSON cache.
- **Cache Miss Flow**:
  Client gọi `search()` -> Cache miss -> Provider thô quét file SQLite/Markdown -> Cập nhật cache -> Trả kết quả.
- **Provider Unavailable Flow**:
  Gọi Qdrant thất bại -> Bắt lỗi `ProviderUnavailableException` -> Tự động chuyển đổi sang MarkdownProvider cục bộ -> Trả kết quả.

## 12. Security & Safety
- **Workspace Boundary**: Chỉ được phép đọc/ghi các file nằm dưới thư mục workspace `.`.
- **Path Validation**: Sử dụng `os.path.abspath` để chuẩn hóa đường dẫn và kiểm tra sandbox.
- **Write Restrictions**: Cấm ghi đè tệp cấu hình của hệ thống.

## 13. Complete Test Matrix
| Requirement ID | Test Type | Test File Target | Mapped Component | Verification Assertion |
| :--- | :--- | :--- | :--- | :--- |
| `FR-01` | Unit Test | `skills/workflow-runtime/tests/test_api.py` | `KnowledgeAPI` | `self.assertIsNotNone(...)` |
| `FR-02` | Unit Test | `skills/workflow-runtime/tests/test_providers.py` | `MarkdownProvider` | `self.assertTrue(...)` |
| `FR-05` | Unit Test | `skills/workflow-runtime/tests/test_cache.py` | `CacheManager` | `self.assertEqual(...)` |

## 14. Requirement Traceability Matrix
- `FR-01` -> Task 1.1 -> Class `KnowledgeAPI` -> `api.py` -> `test_api.py` -> Verified -> Released.
- `FR-02` -> Task 1.2 -> Class `MarkdownProvider` -> `markdown.py` -> `test_providers.py` -> Verified -> Released.
- `FR-05` -> Task 1.3 -> Class `SQLiteProvider` & `CacheManager` -> `sqlite.py`/`cache.py` -> `test_cache.py` -> Verified -> Released.

## 15. File-Level Implementation Contracts
- **File**: `skills/knowledge-runtime/scripts/knowledge_runtime/api.py`
  - **Purpose**: Expose API chính và quản lý cache.
  - **Owner**: Architect
  - **Inputs**: Query, limit.
  - **Outputs**: Mảng JSON kết quả tri thức.
  - **Risks**: Gặp timeout nếu không cấu hình cache TTL hợp lý.
