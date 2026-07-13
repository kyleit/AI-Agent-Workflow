<!-- File path: docs/designs/FEAT-055_project_context_isolation_blueprint.md -->

---
feature_id: FEAT-055
feature_name: Project Context Isolation System
status: reviewed
stage: blueprint
created_at: 2026-07-10
updated_at: 2026-07-10
previous_artifact: ../plans/FEAT-055_project_context_isolation_plan.md
next_artifact: [Implementation (Source Code)](../../)
---

# Technical Design Blueprint & Implementation Contract – Project Context Isolation System

## 0. Baseline Context & References
- **Memory Baseline**: Bộ nhớ dự án hiện tại lưu thông tin trong thư mục `.agents/memory/` và có `memory.config.json` chỉ định collection vector. Lịch sử hội thoại của AI được lưu trữ tập trung tại `<appDataDir>/brain/<conversation-id>/.system_generated/logs/transcript.jsonl`.
- **RAG Query Summaries**: `project-rag-search` thực hiện tìm kiếm vector không lọc theo project_id dẫn đến nguy cơ tải ngữ cảnh chéo giữa các thư mục dự án khác nhau.
- **Inspected Source Files**:
  - `skills/workflow-runtime/scripts/workflow_runtime.py`
  - `skills/project-rag-search/scripts/search_client.py` (giả lập đường dẫn chứa RAG API)
  - `extensions/visualizer/resources/webview.html`

## 1. File-by-File Analysis & Proposed Mutations
| File Path | Operation | Responsibility | Dependency | Impact & Risk |
| :--- | :--- | :--- | :--- | :--- |
| `skills/workflow-runtime/scripts/context_firewall.py` | NEW | Tạo mới lớp `ContextFirewall` chứa logic lọc 10 bước và quản lý danh sách từ chối | None | Trung bình - Ranh giới lọc phải bao phủ chính xác để tránh chặn nhầm file hợp lệ |
| `skills/workflow-runtime/scripts/workflow_runtime.py` | MODIFY | Tích hợp Context Firewall vào cơ chế nạp lịch sử chat và session; cách ly tệp SQLite | context_firewall.py | Cao - Cần đảm bảo tính toàn vẹn của tệp session cũ |
| `skills/project-rag-search/scripts/search_client.py` | MODIFY | Bổ sung các tham số lọc dự án (`project_id`, `vector_collection`) vào truy vấn vector | None | Vừa - Phụ thuộc vào cấu hình trường dữ liệu trong Qdrant |
| `extensions/visualizer/resources/webview.html` | MODIFY | Thiết kế bảng hiển thị thông tin cách ly ngữ cảnh, số lượng file bị chặn và trạng thái Firewall | None | Thấp - Chỉ ảnh hưởng tới UI dashboard |

## 2. Target Folder Structure
```text
.
├── extensions
│   └── visualizer
│       └── resources
│           └── webview.html
└── skills
    ├── project-rag-search
    │   └── scripts
    │       └── search_client.py
    └── workflow-runtime
        ├── scripts
        │   ├── context_firewall.py
        │   └── workflow_runtime.py
        └── tests
            └── test_context_firewall.py
```

## 3. Complete Class & Module Design
- **Class Name**: `ContextFirewall`
  - **Responsibilities**: Thực thi tường lửa ngữ cảnh, từ chối nạp mọi thông tin nằm ngoài phạm vi hoạt động của dự án hiện tại.
  - **Constructor Parameters**:
    - `project_scope` (dict, chứa các thuộc tính `project_id`, `workspace_root`, `git_root`, `vector_collection`)
  - **Public Methods**:
    - `validate_context_path(file_path: str) -> bool`: Kiểm tra xem một đường dẫn file có thuộc phạm vi cho phép không.
    - `filter_rag_results(results: list) -> list`: Lọc danh sách kết quả RAG, loại bỏ các mục lệch `project_id`.
    - `validate_conversation(history: list, active_project_id: str) -> bool`: Xác thực lịch sử chat. Trả về `False` nếu phát hiện hội thoại thuộc dự án khác.
  - **Internal Methods**:
    - `_is_sub_path(parent: str, child: str) -> bool`: Kiểm tra xem đường dẫn child có thuộc thư mục parent hay không.
  - **Dependencies**: Module `os`, `pathlib`.
  - **Extension Points**: Có thể mở rộng để hỗ trợ các quy tắc loại trừ (wildcards) tùy chọn cấu hình từ `workflow.config.json`.

## 4. Detailed Interface Contracts
- **API Signature**: `validate_context_path(file_path: str) -> bool`
  - **Parameters**: `file_path` (str, đường dẫn tuyệt đối hoặc tương đối của tệp cần đọc)
  - **Return Types**: `bool` (True nếu tệp thuộc dự án hiện tại, False nếu bị chặn chéo)
  - **Exceptions**: `ProjectContextViolationError` ném ra khi cố ý truy cập trái phép.

## 5. Configuration Schema
- Thêm trường `project_scope` vào session:
  ```json
  "project_scope": {
    "project_id": "string",
    "workspace_root": "string",
    "git_root": "string",
    "memory_root": "string",
    "vector_collection": "string",
    "sqlite_database": "string",
    "allow_cross_project_context": "boolean"
  }
  ```

## 6. Database & Storage Design
- Cách ly cơ sở dữ liệu SQLite: Cơ sở dữ liệu SQLite của runtime (`project_runtime.db`) sẽ được lưu trữ trực tiếp trong thư mục `.agents/state/{project_id}.db` thay vì dùng chung một tệp toàn cục.
- Quy tắc di trú: Khi khởi tạo, nếu có tệp DB cũ tại gốc, runtime sẽ di tản dữ liệu sang tệp DB theo mã dự án mới.

## 7. Cache Architecture
- Không áp dụng.

## 8. Error Model
- **Exception Class**: `ProjectContextViolationError`
  - **Trigger Condition**: Phát hiện dữ liệu từ dự án chéo xâm nhập vào ngữ cảnh.
  - **Recovery Strategy**: Hủy bỏ phiên nạp dữ liệu đó, xuất cảnh báo mismatch ra console và Visualizer.

## 9. Skill Integration Contracts
- **Skill project-rag-search**: Hàm `search()` bắt buộc phải chèn trường lọc `filter: {"project_id": active_project_id}` vào payload truy vấn Qdrant để lọc trực tiếp từ cơ sở dữ liệu vector.

## 10. CLI & Runtime Contracts
- Không bổ sung lệnh CLI mới. Trình Firewall được kích hoạt tự động ở background khi runtime khởi chạy.

## 11. Sequence Flows
- **Firewall Validation Flow**:
  1. Skill gọi hàm đọc file hoặc truy vấn RAG.
  2. Yêu cầu đi qua `ContextFirewall.validate_context_path()`.
  3. Lọc đường dẫn: Đối chiếu với `workspace_root` và `git_root`.
  4. Nếu hợp lệ -> Trả kết quả cho Skill chạy tiếp.
  5. Nếu vi phạm -> Loại bỏ -> Tăng đếm `rejected_context_count` trong session -> Cảnh báo mismatch.

## 12. Security & Safety
- **Path Escape Prevention**: Ngăn chặn hoàn toàn các chuỗi thoát hiểm như `../../` để đọc ghi bên ngoài không gian làm việc.
- **Strict Default Deny**: Mặc định từ chối nạp chéo trừ khi cấu hình `allow_cross_project_context=true`.

## 13. Complete Test Matrix
| Requirement ID | Test Type | Test File Target | Mapped Component | Verification Assertion |
| :--- | :--- | :--- | :--- | :--- |
| FR-02 | Unit Test | `skills/workflow-runtime/tests/test_context_firewall.py` | `context_firewall.py` | `self.assertFalse(firewall.validate_context_path("/etc/passwd"))` |
| FR-04 | Unit Test | `skills/workflow-runtime/tests/test_context_firewall.py` | `context_firewall.py` | `self.assertFalse(firewall.validate_conversation(other_history))` |
| FR-05 | Integration Test | `skills/workflow-runtime/tests/test_context_firewall.py` | `search_client.py` | `self.assertEqual(query_payload.filter.project_id, "active_id")` |

## 14. Requirement Traceability Matrix
- `FR-02` -> Task 1.2 -> Lớp `ContextFirewall` -> `context_firewall.py` -> `test_context_firewall.py` -> Verified -> Released.
- `FR-05` -> Task 1.5 -> Skill RAG search -> `search_client.py` -> `test_context_firewall.py` -> Verified -> Released.

## 15. File-Level Implementation Contracts
- **File**: `skills/workflow-runtime/scripts/context_firewall.py`
  - **Purpose**: Lớp trung tâm thực thi tường lửa ngữ cảnh dự án.
  - **Owner**: Coder.
  - **Inputs / Outputs**: Kiểm tra đường dẫn và dữ liệu nạp vào; trả về cờ hợp lệ.
  - **Risks**: Hiệu năng kiểm tra đường dẫn có thể bị chậm nếu kiểm tra đệ quy đĩa. -> Cách giảm thiểu: Sử dụng cache đường dẫn tuyệt đối (absolute path resolving cache) trong bộ nhớ RAM.
