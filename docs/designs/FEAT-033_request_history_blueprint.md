<!-- File path: docs/designs/FEAT-033_request_history_blueprint.md -->

---
feature_id: FEAT-033
feature_name: Request History System
status: reviewed
stage: blueprint
created_at: 2026-07-09
updated_at: 2026-07-09
previous_artifact: ../plans/FEAT-033_request_history_plan.md
next_artifact: [Implementation (Source Code)](../../)
---

# Technical Blueprint & Implementation Contract – Request History

## 0. Baseline Context & References
- **Memory Baseline**: Đọc trực tiếp từ SQLite `project_runtime.db`. Trạng thái lưu trữ dữ liệu fresh, có bảng `usage_records` ghi nhận thông số tổng hợp.
- **RAG Query Summaries**: Cơ sở dữ liệu SQLite làm Single Source of Truth cho toàn bộ dữ liệu runtime của dự án.
- **Inspected Source Files**:
  - `skills/workflow-runtime/scripts/db.py` (Lớp và hàm kết nối database SQLite, tạo bảng và lưu trữ).
  - `skills/workflow-runtime/scripts/workflow_runtime.py` (CLI chính quản lý tiến trình).
  - `extensions/visualizer/src/extension.ts` (Lớp Webview Provider nhận/gửi dữ liệu).
  - `extensions/visualizer/resources/webview.html` (Giao diện hiển thị).

---

## 1. File-by-File Analysis & Proposed Mutations

| File Path | Operation | Responsibility | Dependency | Impact & Risk |
| :--- | :--- | :--- | :--- | :--- |
| `skills/workflow-runtime/scripts/db.py` | `MODIFY` | Thêm hàm di trú và tạo bảng `provider_requests`. Thêm hàm `save_provider_request` để ghi lại lịch sử gọi LLM. Cập nhật hàm `get_provider_requests` hỗ trợ lọc khoảng thời gian (`start_time`/`end_time`). | `sqlite3` | Thấp. Dữ liệu cũ được bảo toàn tuyệt đối nhờ cơ chế kiểm tra sự tồn tại của bảng. |
| `skills/workflow-runtime/scripts/workflow_runtime.py` | `MODIFY` | Khai báo nhóm lệnh CLI mới `usage requests` hỗ trợ lọc và sắp xếp. Bổ sung bộ lọc khoảng thời gian `--start-time` và `--end-time`. Tích hợp parser dữ liệu từ SQLite. | `db.py`, `breakdown_engine.py` | Thấp. Lệnh CLI mới không làm thay đổi luồng điều khiển hiện tại. |
| `extensions/visualizer/src/extension.ts` | `MODIFY` | Nạp danh sách provider requests và chi tiết kèm context breakdown từ DB để gửi sang Webview. | `db.py` | Thấp. Visualizer sẽ đọc trực tiếp từ DB. |
| `extensions/visualizer/resources/webview.html` | `MODIFY` | Thêm tab/panel Request History bên dưới phần telemetry, hiển thị bảng timeline và panel Detail View của request được chọn. | `webview.html` | Thấp. Sử dụng CSS và HTML thuần, không dùng framework bên ngoài. |
| `scratch/test_visualizer.html` | `MODIFY` | Cập nhật simulator UI và mock data để Ba có thể preview trực quan trên trình duyệt. | `test_visualizer.html` | Thấp. Chỉ ảnh hưởng đến môi trường test. |

---

## 2. Target Folder Structure
```text
.
├── .agents
│   ├── project_runtime.db
│   └── state
│       └── usage.json
├── docs
│   ├── brainstorming
│   │   └── FEAT-033_request_history.md
│   ├── designs
│   │   └── FEAT-033_request_history_blueprint.md
│   └── plans
│       └── FEAT-033_request_history_plan.md
├── extensions
│   └── visualizer
│       ├── resources
│       │   └── webview.html
│       └── src
│           ├── extension.ts
│           └── webviewHtml.ts
├── scratch
│   └── test_visualizer.html
└── skills
    └── workflow-runtime
        ├── scripts
        │   ├── db.py
        │   └── workflow_runtime.py
        └── tests
            └── test_request_history.py
```

---

## 3. Interface Contracts (Public & Internal)

### Public Interface Contracts
- **CLI Command Syntax**:
  - Xem danh sách request: `python skills/workflow-runtime/scripts/workflow_runtime.py usage requests [--workflow <id>] [--project <id>] [--top-cost <n>] [--top-input <n>] [--start-time <iso8601>] [--end-time <iso8601>]`
  - Xem chi tiết 1 request: `python skills/workflow-runtime/scripts/workflow_runtime.py usage request --id <request_id>`
- **Database Schema**:
  Bảng `provider_requests`:
  ```sql
  CREATE TABLE IF NOT EXISTS provider_requests (
      request_id TEXT PRIMARY KEY,
      workflow_id TEXT NOT NULL,
      conversation_id TEXT NOT NULL,
      project_id TEXT NOT NULL,
      skill_name TEXT NOT NULL,
      command_name TEXT NOT NULL,
      model TEXT NOT NULL,
      provider TEXT NOT NULL,
      timestamp TEXT NOT NULL,
      duration REAL NOT NULL,
      input_tokens INTEGER NOT NULL,
      output_tokens INTEGER NOT NULL,
      cache_tokens INTEGER NOT NULL,
      thinking_tokens INTEGER NOT NULL,
      total_tokens INTEGER NOT NULL,
      cost_usd REAL NOT NULL,
      tool_call_count INTEGER NOT NULL,
      workspace_read_count INTEGER NOT NULL,
      memory_hit_count INTEGER NOT NULL,
      rag_hit_count INTEGER NOT NULL,
      context_usage_percentage REAL NOT NULL,
      context_limit_tokens INTEGER NOT NULL,
      context_breakdown_json TEXT, -- Cấu trúc JSON chi tiết breakdown tại request đó
      status TEXT NOT NULL, -- success / failed / cancelled
      error_summary TEXT
  );
  ```
  **Indices**:
  * `idx_requests_project_id` trên `project_id`
  * `idx_requests_workflow_id` trên `workflow_id`
  * `idx_requests_conversation_id` trên `conversation_id`
  * `idx_requests_created_at` trên `timestamp`
  * `idx_requests_total_tokens` trên `total_tokens`
  * `idx_requests_cost_usd` trên `cost_usd`

### Internal Component Contracts
- **`db.py` Function**:
  ```python
  def save_provider_request(request_data: dict) -> None
  def get_provider_requests(filters: dict, sort_by: str = "timestamp", desc: bool = True, limit: int = None) -> list[dict]
  def get_provider_request_detail(request_id: str) -> dict
  ```

---

## 4. Algorithms & Logic Specifications

### Ghi nhận và chống trùng lặp request:
Mỗi khi hệ thống thực hiện gọi một provider LLM, một đối tượng `request_data` sẽ được tạo ra với `request_id` sinh ra từ hash của các thuộc tính bất biến của request đó (hoặc UUID định danh duy nhất truyền vào từ framework).
```python
# Lệnh lưu trữ an toàn:
cursor.execute("""
    INSERT OR IGNORE INTO provider_requests (
        request_id, workflow_id, conversation_id, project_id, skill_name, command_name,
        model, provider, timestamp, duration, input_tokens, output_tokens, cache_tokens,
        thinking_tokens, total_tokens, cost_usd, tool_call_count, workspace_read_count,
        memory_hit_count, rag_hit_count, context_usage_percentage, context_limit_tokens,
        context_breakdown_json, status, error_summary
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""", record)
```
Nếu có sự kiện sync/chạy lại ghi nhận cùng một `request_id`, DB sẽ tự động bỏ qua (`INSERT OR IGNORE`) ngăn ngừa trùng lặp.

---

## 5. State Machine & Transitions
Hệ thống không thay đổi sơ đồ trạng thái chung của workflow, chỉ cập nhật trạng thái của từng request (`success`, `failed`, `cancelled`).

---

## 6. Validation and Safety Constraints
- Cột `context_breakdown_json` phải lưu trữ chuỗi JSON hợp lệ.
- Ràng buộc giá trị trường `status` phải nằm trong tập hợp: `['success', 'failed', 'cancelled']`.

---

## 7. Backward Compatibility & Migration Mapping
Bảng `usage_records` hiện tại được giữ nguyên vẹn để tương thích ngược. Bảng `provider_requests` được thêm mới hoàn toàn, không gây ảnh hưởng đến dữ liệu cũ.

---

## 8. Implementation Checklist
- [ ] Bổ sung cơ chế tạo bảng `provider_requests` và chỉ mục trong `db.py`.
- [ ] Viết hàm `save_provider_request` và các hàm query lọc/sắp xếp trong `db.py`.
- [ ] Thêm lệnh CLI `usage requests` và `usage request` trong `workflow_runtime.py`.
- [ ] Tích hợp cơ chế tự động trích xuất thông tin request để lưu trữ trong backend sync.
- [ ] Cập nhật Webview Provider trong `extension.ts` để đọc và gửi danh sách requests qua Webview.
- [ ] Thiết kế panel Request History timeline và detail view dạng collapsible trong `webview.html`.
- [ ] Viết bộ test kiểm thử tự động `test_request_history.py`.

---

## 9. Acceptance Criteria & Test Mapping

| Requirement ID | Requirement Description | Expected Result | Verification Method | Unit/Integration Test Target |
| :--- | :--- | :--- | :--- | :--- |
| `REQ-001` | Tạo bảng & chỉ mục SQLite thành công | Bảng được tạo, dữ liệu cũ giữ nguyên | Chạy python inspect_db.py | `test_request_history.py:test_database_migration` |
| `REQ-002` | Không trùng lặp khi chạy lại sync | Bản ghi tồn tại chính xác 1 lần | Ghi đè cùng ID nhiều lần | `test_request_history.py:test_prevent_duplicates` |
| `REQ-003` | Sắp xếp dữ liệu theo Cost | Dữ liệu trả về đúng thứ tự giảm dần | Gọi API / CLI sort | `test_request_history.py:test_sorting_by_cost` |
| `REQ-004` | Lọc dữ liệu theo Skill | Chỉ hiển thị các request của skill chỉ định | Gọi API / CLI filter | `test_request_history.py:test_filtering_by_skill` |
| `REQ-005` | UI hiển thị Timeline & Detail | Giao diện nạp đầy đủ thông tin, hiển thị breakdown tương ứng | Mở Visualizer Extension | Kiểm thử thủ công qua Simulator |

---

## 10. Disallowed Outputs Validation
- [x] Không dùng đường dẫn tuyệt đối hoặc `file://` trong thiết kế.
- [x] Không sử dụng các từ viết tắt `TBD` hoặc placeholder rỗng.
- [x] Ràng buộc `permission_mode` an toàn: `sandbox`, `full_access`.
