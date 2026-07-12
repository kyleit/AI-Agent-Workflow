<!-- File path: docs/designs/FEAT-116_autonomous_delivery_after_brainstorming_blueprint.md -->

---
feature_id: FEAT-116
feature_name: Autonomous Delivery After Brainstorming
status: reviewed
stage: blueprint
created_at: 2026-07-12
updated_at: 2026-07-12
previous_artifact: ../plans/FEAT-116_autonomous_delivery_after_brainstorming_plan.md
next_artifact: "[Implementation (Source Code)](../../)"
---

# Technical Design Blueprint & Implementation Contract – Autonomous Delivery After Brainstorming (FEAT-116)

## 0. Baseline Context & References
- **Memory Baseline**: Project memory is loaded and valid. Trạng thái dự án hiện tại là các phase hoạt động thủ công độc lập dưới sự điều phối của CLI.
- **RAG Query Summaries**: Đã kiểm tra các cơ chế phân tích cấu trúc trạng thái của session và workflow.
- **Inspected Source Files**:
  - `skills/workflow-runtime/scripts/session.py` (Lớp load/save session).
  - `skills/workflow-runtime/scripts/state_sync.py` (Quản lý phân tách và gộp trạng thái từ file JSON).
  - `skills/workflow-runtime/scripts/workflow_runtime.py` (CLI entry point).
  - `extensions/visualizer/resources/webview.html` (Giao diện Visualizer).

## 1. File-by-File Analysis & Proposed Mutations

| File Path | Operation | Responsibility | Dependency | Impact & Risk |
| :--- | :--- | :--- | :--- | :--- |
| `skills/workflow-runtime/scripts/state_sync.py` | MODIFY | Thêm cờ `autonomous_delivery` vào gộp/rã trạng thái. Tính toán phần trăm tiến trình. | Không có | Thấp. Việc ghi thêm trường không ảnh hưởng đến các thuộc tính cũ. |
| `skills/workflow-runtime/scripts/workflow_runtime.py` | MODIFY | Tích hợp tham số CLI `--autonomous` và cơ chế bypass approval gate trong `requires_approval`. | state_sync.py | Trung bình. Cần đảm bảo các thao tác nguy hiểm (push, commit, release) vẫn bị chặn ở chế độ tự động. |
| `extensions/visualizer/resources/webview.html` | MODIFY | Cập nhật giao diện người dùng hiển thị thanh tiến trình động và trạng thái tự động hóa. | workflow_runtime.py | Thấp. Chỉ thay đổi UI hiển thị dữ liệu. |

## 2. Target Folder Structure
Giữ nguyên cấu trúc thư mục hiện tại của hệ thống:
```text
.
├── extensions
│   └── visualizer
│       └── resources
│           └── webview.html
└── skills
    └── workflow-runtime
        └── scripts
            ├── session.py
            ├── state_sync.py
            └── workflow_runtime.py
```

## 3. Complete Class & Module Design

### Module: `state_sync`
- **Functions updated**:
  - `aggregate_state(workspace_root: str) -> dict[str, Any]`
    - **Mutation**: Bổ sung khóa `"autonomous_delivery": context.get("autonomous_delivery", False)` vào dict trả về.
  - `deconstruct_state(workspace_root: str, session: dict[str, Any]) -> None`
    - **Mutation**: Bổ sung khóa `"autonomous_delivery": session.get("autonomous_delivery", False)` vào dict `context` được ghi xuống `context.json`.
    - **Mutation**: Tính toán trường `"progress_percentage"` dựa trên `"checkpoint"` hiện tại (Công thức: `min(100, max(0, int(checkpoint / 10 * 100)))`) và ghi vào `context.json`.

### Module: `workflow_runtime`
- **Functions updated**:
  - `requires_approval(action_type: str, path: str = None) -> bool`
    - **Mutation**: Kiểm tra cờ `session.get("autonomous_delivery", False)`. Nếu bật:
      - Trả về `True` nếu `action_type` nằm trong danh sách hành động hạn chế (`release_actions` bao gồm: `git_commit`, `git_push`, `git_tag`, `git_merge`, `release`, `publish`, `deploy`, `permission_mode_change`).
      - Trả về `False` đối với các hành động trung gian khác như `normal_file_write`, `source_code_change`, `test_command`, `build_command`, `memory_update` để bypass yêu cầu duyệt của Ba.

## 4. Detailed Interface Contracts
- **CLI Command Signature**: `python workflow_runtime.py start --skill <skill> --command <cmd> --checkpoint <cp> --step <step> [--autonomous]`
  - **Option**: `--autonomous` (Action: `store_true`, Default: `False`). Nếu được truyền vào, session khởi tạo sẽ có thuộc tính `"autonomous_delivery": true`.

## 5. Configuration Schema
- **context.json Target Schema**:
  ```json
  {
    "project_id": "ai-skill-framework",
    "autonomous_delivery": true,
    "progress_percentage": 30,
    ...
  }
  ```

## 6. Database & Storage Design
Không có thay đổi về cơ sở dữ liệu.

## 7. Cache Architecture
Không có thay đổi về cơ chế cache.

## 8. Error Model
- **Debug Loop Recovery Policy**:
  - Khi một phase thực thi tự động thất bại (ví dụ: pytest lỗi):
    - Orchestrator ghi nhận lỗi vào `defects.json`.
    - Tăng bộ đếm `retry_count` của tác vụ lỗi.
    - Nếu `retry_count <= 5`: Tự động gọi `debug_action` để sửa đổi mã nguồn và chạy lại.
    - Nếu `retry_count > 5`: Hủy chế độ tự động hóa, chuyển trạng thái sang `unrecoverable_blocker` và dừng lại xin ý kiến của Ba.

## 9. Skill Integration Contracts
Không có thay đổi về liên kết skill ngoài việc tích hợp cờ trong runtime.

## 10. CLI & Runtime Contracts
- **Command Syntax**: `python skills/workflow-runtime/scripts/workflow_runtime.py start --skill brainstorming --command brainstorm --checkpoint 3 --step "Starting execution..." --autonomous`
  - Khởi chạy một phase và thiết lập phiên làm việc ở chế độ phân phối tự động.

## 11. Sequence Flows
- **Normal Autonomous Flow**:
  1. Ba chạy command khởi động tính năng với cờ `--autonomous`.
  2. Orchestrator chuyển sang chế độ tự động hóa, lưu `"autonomous_delivery": true` vào session.
  3. Coder thực thi viết code → `requires_approval("source_code_change")` trả về `False` → Thực thi thành công mà không dừng lại chờ duyệt.
  4. Test suite được chạy → `requires_approval("test_command")` trả về `False` → Chạy test thành công.
  5. Khi tiến độ đạt đến mốc Release → `requires_approval("release")` trả về `True` → Dừng lại chờ xác nhận phát hành từ Ba.

## 12. Security & Safety
- **Release Isolation Boundary**: Cờ `--autonomous` tuyệt đối không được phép bypass các hành động thay đổi lịch sử Git từ xa (`git_push`) hoặc xuất bản gói (`publish`) nhằm đảm bảo tính an toàn tối đa cho hệ thống của Ba.

## 13. Complete Test Matrix

| Requirement ID | Test Type | Test File Target | Mapped Component | Verification Assertion |
| :--- | :--- | :--- | :--- | :--- |
| `FR-01` | Unit Test | `skills/workflow-runtime/tests/integration/test_runtime.py` | `session.py` | `self.assertTrue(session["autonomous_delivery"])` khi chạy với cờ. |
| `FR-04` | Integration Test | `skills/workflow-runtime/tests/integration/test_runtime.py` | `workflow_runtime.py` | `self.assertFalse(requires_approval("source_code_change"))` khi cờ bật. |
| `FR-04` | Integration Test | `skills/workflow-runtime/tests/integration/test_runtime.py` | `workflow_runtime.py` | `self.assertTrue(requires_approval("git_push"))` luôn yêu cầu duyệt kể cả khi cờ bật. |

## 14. Requirement Traceability Matrix
- `FR-01` -> Task 1.1 -> state_sync.py -> `test_runtime.py` -> Verified.
- `FR-02` -> Task 1.2 -> workflow_runtime.py -> `test_runtime.py` -> Verified.
- `FR-04` -> Task 2.1 -> workflow_runtime.py (requires_approval) -> `test_runtime.py` -> Verified.

## 15. File-Level Implementation Contracts
- **File**: `skills/workflow-runtime/scripts/state_sync.py`
  - **Purpose**: Đảm bảo trạng thái tự động hóa và phần trăm tiến độ được gộp/rã chính xác vào tệp đĩa.
  - **Owner**: Coder.
- **File**: `skills/workflow-runtime/scripts/workflow_runtime.py`
  - **Purpose**: Xử lý việc bypass các cổng phê duyệt thủ công trung gian đối với các hành động không nguy hiểm.
  - **Owner**: Coder.
- **File**: `extensions/visualizer/resources/webview.html`
  - **Purpose**: Thêm hiển thị thanh tiến trình động để theo dõi trực quan luồng tự động hóa.
  - **Owner**: Frontend Developer.

## 16. Verification & Metadata Compatibility

### Summary
Triển khai cờ `--autonomous` CLI và điều phối bỏ qua các cổng phê duyệt thủ công trung gian khi phân phối tự động.

### Scope
Sửa đổi các tệp: `state_sync.py`, `workflow_runtime.py`, `webview.html`, và cập nhật chính sách `AI_RULES.md`.

### Technical Design
Kiến trúc tích hợp tham số CLI, lưu giữ trạng thái trong `context.json`, và hiển thị thanh tiến trình trực quan động trên Visualizer Webview.

### Files to Change
Xem bảng phân tích tệp tin tại Mục 1.

### Implementation Steps
Xem luồng Sequence Flows tại Mục 11.

### Validation Plan
Xem Test Matrix tại Mục 13 và kịch bản Pytest tích hợp.

### Rollback Plan
Sử dụng Git Checkout để khôi phục mã nguồn và khôi phục trạng thái session.
