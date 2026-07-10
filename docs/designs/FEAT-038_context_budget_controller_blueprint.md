<!-- File path: docs/designs/FEAT-038_context_budget_controller_blueprint.md -->

---
feature_id: FEAT-038
feature_name: Context Budget Controller
status: reviewed
stage: blueprint
created_at: 2026-07-09
updated_at: 2026-07-09
previous_artifact: ../plans/FEAT-038_context_budget_controller_plan.md
next_artifact: [Implementation (Source Code)](../../)
---

# Technical Blueprint & Implementation Contract – Context Budget Controller

## 0. Baseline Context & References
- **Memory Baseline**: Các tệp tin cấu hình ngân sách và lịch sử request của AIWF.
- **Inspected Source Files**:
  - `skills/workflow-runtime/scripts/db.py`
  - `skills/workflow-runtime/scripts/workflow_runtime.py`
  - `extensions/visualizer/resources/webview.html`

---

## 1. File-by-File Analysis & Proposed Mutations

| File Path | Operation | Responsibility | Dependency | Impact & Risk |
| :--- | :--- | :--- | :--- | :--- |
| `skills/workflow-runtime/scripts/budget_controller.py` | `NEW` | Định nghĩa các chính sách cảnh báo, chặn request bảo vệ khẩn cấp, xếp hạng và kích hoạt 10 chiến lược tối ưu hóa. | None | Thấp. |
| `skills/workflow-runtime/scripts/db.py` | `MODIFY` | Tạo bảng SQLite `budget_policies`, `budget_history` và các hàm lưu/lấy trạng thái ngân sách. | `budget_controller.py` | Thấp. |
| `skills/workflow-runtime/scripts/workflow_runtime.py` | `MODIFY` | Cung cấp CLI subcommands `usage budget status`, `usage budget history`, `usage budget optimize`. | `db.py`, `budget_controller.py` | Thấp. |
| `extensions/visualizer/resources/webview.html` | `MODIFY` | Tab **Budget Controller** quản trị ngưỡng cảnh báo phần trăm, chuyển chế độ Auto/Manual, hiển thị lịch sử tối ưu. | None | Thấp. |
| `extensions/visualizer/src/extension.ts` | `MODIFY` | Tích hợp APIs giao tiếp CLI quản lý ngân sách. | None | Thấp. |

---

## 2. Interface Contracts

### Public Interface Contracts:
1. **CLI API subcommands**:
   - `python workflow_runtime.py usage budget status --format json`
   - `python workflow_runtime.py usage budget history --format json`
   - `python workflow_runtime.py usage budget optimize --strategy <name> --format json`

2. **SQLite Database Schema**:
   ```sql
   CREATE TABLE IF NOT EXISTS budget_policies (
       id INTEGER PRIMARY KEY AUTOINCREMENT,
       provider TEXT NOT NULL UNIQUE,
       model TEXT NOT NULL,
       soft_warning_pct REAL NOT NULL DEFAULT 50.0,
       high_usage_pct REAL NOT NULL DEFAULT 70.0,
       critical_usage_pct REAL NOT NULL DEFAULT 85.0,
       emergency_pct REAL NOT NULL DEFAULT 95.0
   );
   
   CREATE TABLE IF NOT EXISTS budget_history (
       id INTEGER PRIMARY KEY AUTOINCREMENT,
       timestamp TEXT NOT NULL,
       conversation_id TEXT NOT NULL,
       predicted_tokens INTEGER NOT NULL,
       policy_triggered TEXT NOT NULL,
       strategy_applied TEXT NOT NULL,
       tokens_saved INTEGER NOT NULL,
       cost_saved REAL NOT NULL,
       status TEXT NOT NULL
   );
   ```

---

## 3. Implementation Checklist
- [ ] Triển khai chính sách kiểm duyệt và 10 chiến lược tối ưu trong `budget_controller.py`.
- [ ] Bổ sung cấu trúc bảng di trú SQLite trong `db.py`.
- [ ] Tích hợp dòng lệnh CLI `budget` trong `workflow_runtime.py`.
- [ ] Thiết kế Tab quản trị trực quan Budget Controller trong `webview.html`.
- [ ] Đóng gói và biên dịch Extension bằng `node build.js` và `npm run compile`.
- [ ] Viết unittest `test_budget_controller.py`.
