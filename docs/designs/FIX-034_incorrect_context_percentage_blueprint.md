<!-- File path: docs/designs/FIX-034_incorrect_context_percentage_blueprint.md -->

---
feature_id: FIX-034
feature_name: Incorrect Active Context Percentage
status: reviewed
stage: blueprint
created_at: 2026-07-09
updated_at: 2026-07-09
previous_artifact: ../plans/FIX-034_incorrect_context_percentage_plan.md
next_artifact: [Implementation (Source Code)](../../)
---

# Technical Blueprint & Implementation Contract – Incorrect Active Context Percentage

## 0. Baseline Context & References
- **Memory Baseline**: Đọc trực tiếp từ SQLite `project_runtime.db`. Trạng thái lưu trữ dữ liệu fresh, có bảng `usage_records` ghi nhận thông số tổng hợp.
- **RAG Query Summaries**: Cơ sở dữ liệu SQLite làm Single Source of Truth cho toàn bộ dữ liệu runtime của dự án.
- **Inspected Source Files**:
  - `skills/workflow-runtime/scripts/workflow_runtime.py` (Chứa logic tạo session context_usage).
  - `extensions/visualizer/resources/webview.html` (Chứa logic binding hiển thị token hoạt động).

---

## 1. File-by-File Analysis & Proposed Mutations

| File Path | Operation | Responsibility | Dependency | Impact & Risk |
| :--- | :--- | :--- | :--- | :--- |
| `skills/workflow-runtime/scripts/workflow_runtime.py` | `MODIFY` | Thay đổi `"total_tokens": usage.get("total_tokens", 0)` thành `"total_tokens": usage.get("active_tokens", 0)` trong khối khởi tạo `session["context_usage"]`. | `context.py` | Rất thấp. Giúp truyền tải đúng lượng token active. |
| `extensions/visualizer/resources/webview.html` | `MODIFY` | Cập nhật `activeTotal` để prioritze lấy từ `wf.active_tokens` trước khi fallback sang `wf.total_tokens`. | None | Rất thấp. Cải thiện độ chính xác hiển thị. |

---

## 2. Target Folder Structure
```text
.
├── docs
│   ├── brainstorming
│   │   └── FIX-034_incorrect_context_percentage.md
│   ├── designs
│   │   └── FIX-034_incorrect_context_percentage_blueprint.md
│   └── plans
│       └── FIX-034_incorrect_context_percentage_plan.md
├── extensions
│   └── visualizer
│       └── resources
│           └── webview.html
└── skills
    └── workflow-runtime
        ├── scripts
        │   └── workflow_runtime.py
        └── tests
            └── test_mathematical_percentage.py
```

---

## 3. Interface Contracts (Public & Internal)

### Data Schema (backward-compatible context_usage object):
```json
{
  "context_usage": {
    "total_tokens": 828671, // active_tokens thay vì total_tokens lũy kế
    "limit_tokens": 2000000,
    "percentage": 41.43
  }
}
```

---

## 4. Algorithms & Logic Specifications
Phép tính phần trăm Active Context duy nhất trên toàn hệ thống được kiểm soát ở backend:
$$\text{percentage} = \frac{\text{active\_tokens}}{\text{limit\_tokens}} \times 100$$
Giao diện frontend chỉ đọc trực tiếp trường `percentage` được tính từ backend, đảm bảo không có tính toán trùng lặp hay phân kỳ giá trị.

---

## 5. State Machine & Transitions
Không thay đổi state machine.

---

## 6. Validation and Safety Constraints
- Tránh chia cho 0 bằng cách bảo vệ limit_tokens > 0.
- Giới hạn phần trăm hiển thị trong khoảng `[0, 100]`.

---

## 7. Backward Compatibility & Migration Mapping
Duy trì cấu trúc phẳng cũ để tránh xung đột với các phiên bản extension cũ. Chỉ cập nhật giá trị số lượng token hoạt động vào khóa `total_tokens` của `context_usage` để giữ tính tương thích tuyệt đối.

---

## 8. Implementation Checklist
- [ ] Thay đổi `total_tokens` thành `active_tokens` trong `workflow_runtime.py`.
- [ ] Cập nhật fallback logic của `activeTotal` trong `webview.html` để ưu tiên `wf.active_tokens`.
- [ ] Chạy lệnh `node build.js` để biên dịch lại giao diện.
- [ ] Viết bộ test kiểm thử tự động xác thực các trường hợp tính toán phần trăm toán học.

---

## 9. Acceptance Criteria & Test Mapping

| Requirement ID | Requirement Description | Expected Result | Verification Method | Unit/Integration Test Target |
| :--- | :--- | :--- | :--- | :--- |
| `REQ-001` | Sửa gán biến backend | `session["context_usage"]["total_tokens"]` chứa active_tokens | Chạy test case tự động | `test_mathematical_percentage.py` |
| `REQ-002` | Sửa binding frontend | UI hiển thị chính xác token hoạt động khớp phần trăm | Mở Webview sidebar | Kiểm thử trực quan |

---

## 10. Disallowed Outputs Validation
- [x] Không dùng đường dẫn tuyệt đối hoặc `file://` trong thiết kế.
- [x] Không sử dụng các từ viết tắt `TBD` hoặc placeholder rỗng.
