<!-- File path: docs/designs/FEAT-040_autonomous_optimization_engine_blueprint.md -->

---
feature_id: FEAT-040
feature_name: Autonomous Runtime Optimization Engine
status: reviewed
stage: blueprint
created_at: 2026-07-09
updated_at: 2026-07-09
previous_artifact: ../plans/FEAT-040_autonomous_optimization_engine_plan.md
next_artifact: [Implementation (Source Code)](../../)
---

# Technical Blueprint & Implementation Contract – Autonomous Runtime Optimization Engine

## 0. Baseline Context & References
- **Memory Baseline**: Các tệp tin cấu hình tối ưu hóa tự động và lịch sử học của AIWF.
- **Inspected Source Files**:
  - `skills/workflow-runtime/scripts/db.py`
  - `skills/workflow-runtime/scripts/workflow_runtime.py`
  - `extensions/visualizer/resources/webview.html`

---

## 1. File-by-File Analysis & Proposed Mutations

| File Path | Operation | Responsibility | Dependency | Impact & Risk |
| :--- | :--- | :--- | :--- | :--- |
| `skills/workflow-runtime/scripts/optimizer.py` | `NEW` | Phân tích lịch sử tokens/cost, tính toán ROI tiết kiệm và hỗ trợ chế độ Benchmark Mode. | None | Thấp. |
| `skills/workflow-runtime/scripts/db.py` | `MODIFY` | Tạo bảng SQLite `optimization_feedback`, `benchmark_reports` và `policy_configurations`. | `optimizer.py` | Thấp. |
| `skills/workflow-runtime/scripts/workflow_runtime.py` | `MODIFY` | Tích hợp subcommands CLI `usage optimize --optimize-subaction`. | `db.py`, `optimizer.py` | Thấp. |
| `extensions/visualizer/resources/webview.html` | `MODIFY` | Tab **Optimization Center** hiển thị biểu đồ ROI, leaderboard và bộ cấu hình chính sách. | None | Thấp. |
| `extensions/visualizer/src/extension.ts` | `MODIFY` | Tích hợp APIs giao tiếp CLI quản lý chính sách và xuất báo cáo Benchmark. | None | Thấp. |

---

## 2. Interface Contracts

### Public Interface Contracts:
1. **CLI API subcommands**:
   - `python workflow_runtime.py usage optimize --optimize-subaction analyze --format json`
   - `python workflow_runtime.py usage optimize --optimize-subaction benchmark --format json`
   - `python workflow_runtime.py usage optimize --optimize-subaction policies --strategy <policy_name> --format json`

2. **SQLite Database Schema**:
   ```sql
   CREATE TABLE IF NOT EXISTS optimization_feedback (
       id INTEGER PRIMARY KEY AUTOINCREMENT,
       timestamp TEXT NOT NULL,
       conversation_id TEXT NOT NULL,
       metric_name TEXT NOT NULL,
       metric_value REAL NOT NULL,
       savings_usd REAL NOT NULL
   );
   
   CREATE TABLE IF NOT EXISTS benchmark_reports (
       id INTEGER PRIMARY KEY AUTOINCREMENT,
       timestamp TEXT NOT NULL,
       original_input_tokens INTEGER NOT NULL,
       optimized_input_tokens INTEGER NOT NULL,
       original_cost REAL NOT NULL,
       optimized_cost REAL NOT NULL
   );
   
   CREATE TABLE IF NOT EXISTS policy_configurations (
       id INTEGER PRIMARY KEY AUTOINCREMENT,
       policy_name TEXT NOT NULL UNIQUE,
       context_rebuild_enabled INTEGER NOT NULL DEFAULT 1,
       cache_enabled INTEGER NOT NULL DEFAULT 1,
       compression_pct REAL NOT NULL DEFAULT 85.0
   );
   ```

---

## 3. Implementation Checklist
- [ ] Xây dựng bộ máy học phân tích và chấm điểm tối ưu trong `optimizer.py`.
- [ ] Bổ sung các bảng di trú SQLite trong `db.py`.
- [ ] Cung cấp các dòng lệnh CLI `optimize` trong `workflow_runtime.py`.
- [ ] Thiết kế Tab quản trị Optimization Center trong `webview.html`.
- [ ] Đóng gói và biên dịch Extension bằng `node build.js` và `npm run compile`.
- [ ] Viết unittest `test_optimizer.py`.
