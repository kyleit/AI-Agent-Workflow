<!-- File path: docs/designs/FEAT-039_smart_context_rebuilder_blueprint.md -->

---
feature_id: FEAT-039
feature_name: Smart Context Rebuilder
status: reviewed
stage: blueprint
created_at: 2026-07-09
updated_at: 2026-07-09
previous_artifact: ../plans/FEAT-039_smart_context_rebuilder_plan.md
next_artifact: [Implementation (Source Code)](../../)
---

# Technical Blueprint & Implementation Contract – Smart Context Rebuilder

## 0. Baseline Context & References
- **Memory Baseline**: Các tệp tin cấu hình ngữ cảnh và bộ cache của AIWF.
- **Inspected Source Files**:
  - `skills/workflow-runtime/scripts/db.py`
  - `skills/workflow-runtime/scripts/workflow_runtime.py`
  - `extensions/visualizer/resources/webview.html`

---

## 1. File-by-File Analysis & Proposed Mutations

| File Path | Operation | Responsibility | Dependency | Impact & Risk |
| :--- | :--- | :--- | :--- | :--- |
| `skills/workflow-runtime/scripts/context_rebuilder.py` | `NEW` | Định nghĩa bộ máy ráp ngữ cảnh tối ưu, loại bỏ tin nhắn thừa, tính toán mã băm SHA256 để quản lý cache rules/blueprints. | None | Thấp. |
| `skills/workflow-runtime/scripts/db.py` | `MODIFY` | Tạo bảng SQLite `context_bundles` và `cache_metadata` để lưu thông số cache và lịch sử ráp. | `context_rebuilder.py` | Thấp. |
| `skills/workflow-runtime/scripts/workflow_runtime.py` | `MODIFY` | Tích hợp các subcommands CLI `usage context preview`, `usage context cache`, `usage context rebuild`. | `db.py`, `context_rebuilder.py` | Thấp. |
| `extensions/visualizer/resources/webview.html` | `MODIFY` | Tab **Context Rebuilder** hiển thị biểu đồ so sánh dung lượng (Before vs After), thống kê hit/miss và danh sách Include/Skip. | None | Thấp. |
| `extensions/visualizer/src/extension.ts` | `MODIFY` | Tích hợp APIs giao tiếp CLI quản lý ráp ngữ cảnh và cache. | None | Thấp. |

---

## 2. Interface Contracts

### Public Interface Contracts:
1. **CLI API subcommands**:
   - `python workflow_runtime.py usage context preview --format json`
   - `python workflow_runtime.py usage context rebuild --format json`
   - `python workflow_runtime.py usage context cache --format json`

2. **SQLite Database Schema**:
   ```sql
   CREATE TABLE IF NOT EXISTS cache_metadata (
       id INTEGER PRIMARY KEY AUTOINCREMENT,
       source_path TEXT NOT NULL UNIQUE,
       source_hash TEXT NOT NULL,
       summary_content TEXT NOT NULL,
       updated_at TEXT NOT NULL
   );
   
   CREATE TABLE IF NOT EXISTS context_bundles (
       id INTEGER PRIMARY KEY AUTOINCREMENT,
       conversation_id TEXT NOT NULL,
       timestamp TEXT NOT NULL,
       original_tokens INTEGER NOT NULL,
       rebuilt_tokens INTEGER NOT NULL,
       tokens_saved INTEGER NOT NULL,
       included_sources TEXT NOT NULL,
       skipped_sources TEXT NOT NULL
   );
   ```

---

## 3. Implementation Checklist
- [ ] Xây dựng thuật toán ráp ngữ cảnh tối giản và nén thông tin trong `context_rebuilder.py`.
- [ ] Thêm di trú schema SQLite trong `db.py`.
- [ ] Tích hợp các dòng lệnh CLI `context` trong `workflow_runtime.py`.
- [ ] Thiết kế Tab quản trị Smart Context Rebuilder trong `webview.html`.
- [ ] Đóng gói và biên dịch Extension bằng `node build.js` và `npm run compile`.
- [ ] Viết unittest `test_context_rebuilder.py`.
