<!-- File path: docs/designs/FEAT-035_token_diff_analysis_blueprint.md -->

---
feature_id: FEAT-035
feature_name: Token Diff Analysis
status: reviewed
stage: blueprint
created_at: 2026-07-09
updated_at: 2026-07-09
previous_artifact: ../plans/FEAT-035_token_diff_analysis_plan.md
next_artifact: [Implementation (Source Code)](../../)
---

# Technical Blueprint & Implementation Contract – Token Diff Analysis

## 0. Baseline Context & References
- **Memory Baseline**: Tận dụng cơ sở dữ liệu SQLite `project_runtime.db` với bảng `provider_requests` chứa breakdown chi tiết của từng bước LLM.
- **RAG Query Summaries**: SQLite làm Single Source of Truth cho toàn bộ dữ liệu.
- **Inspected Source Files**:
  - `skills/workflow-runtime/scripts/db.py`
  - `skills/workflow-runtime/scripts/workflow_runtime.py`
  - `extensions/visualizer/resources/webview.html`

---

## 1. File-by-File Analysis & Proposed Mutations

| File Path | Operation | Responsibility | Dependency | Impact & Risk |
| :--- | :--- | :--- | :--- | :--- |
| `skills/workflow-runtime/scripts/diff_engine.py` | `NEW` | Phép toán hiệu số so sánh hai Breakdown JSON của request A và B. | None | Rất thấp. Module mới cô lập. |
| `skills/workflow-runtime/scripts/db.py` | `MODIFY` | Di trú thêm bảng `token_diffs`, chỉ mục, và hàm lưu/lấy dữ liệu diff. | `diff_engine.py` | Thấp. Cần bảo vệ dữ liệu cũ. |
| `skills/workflow-runtime/scripts/workflow_runtime.py` | `MODIFY` | Bổ sung câu lệnh CLI `usage diff` để trả về JSON hoặc định dạng bảng. | `db.py` | Thấp. Chỉ mở rộng CLI parser. |
| `extensions/visualizer/resources/webview.html` | `MODIFY` | Tích hợp tab Token Diff Card, biểu đồ Waterfall/Delta và tính năng so sánh tùy chọn. | `extension.ts` | Thấp. Cần tối ưu CSS hiển thị. |
| `extensions/visualizer/src/extension.ts` | `MODIFY` | Bổ sung hàm API `getTokenDiff` gọi CLI Python bất đồng bộ. | None | Thấp. |

---

## 2. Target Folder Structure
```text
.
├── docs
│   ├── designs
│   │   └── FEAT-035_token_diff_analysis_blueprint.md
│   └── plans
│       └── FEAT-035_token_diff_analysis_plan.md
├── extensions
│   └── visualizer
│       ├── resources
│       │   └── webview.html
│       └── src
│           ├── extension.ts
│           └── webviewHtml.ts
└── skills
    └── workflow-runtime
        ├── scripts
        │   ├── db.py
        │   ├── diff_engine.py
        │   └── workflow_runtime.py
        └── tests
            └── test_diff_engine.py
```

---

## 3. Interface Contracts (Public & Internal)

### Public Interface Contracts:
1. **CLI Command**:
   - `python workflow_runtime.py usage diff <req_a> <req_b>`: Trả về JSON so sánh giữa Request A và B.
   - `python workflow_runtime.py usage diff --latest`: So sánh tự động giữa Request mới nhất và liền trước.

2. **SQLite Database Schema**:
   ```sql
   CREATE TABLE IF NOT EXISTS token_diffs (
       request_id TEXT PRIMARY KEY,
       prev_request_id TEXT,
       conversation_id TEXT NOT NULL,
       net_change_tokens INTEGER NOT NULL,
       percentage_change REAL NOT NULL,
       added_tokens INTEGER NOT NULL,
       removed_tokens INTEGER NOT NULL,
       diff_breakdown_json TEXT NOT NULL,
       timestamp TEXT NOT NULL,
       FOREIGN KEY(request_id) REFERENCES provider_requests(request_id)
   );
   CREATE INDEX IF NOT EXISTS idx_diffs_conversation_id ON token_diffs(conversation_id);
   ```

3. **Diff Breakdown Schema (JSON representation)**:
   ```json
   {
     "previous_request_id": "req_1",
     "current_request_id": "req_2",
     "net_change_tokens": 263000,
     "percentage_change": 106.48,
     "added_tokens": 263000,
     "removed_tokens": 0,
     "categories": {
       "Blueprints": {
         "previous": 0,
         "current": 118000,
         "delta": 118000,
         "percentage": 100.0
       },
       "Conversation History": {
         "previous": 0,
         "current": 52000,
         "delta": 52000,
         "percentage": 100.0
       }
     }
   }
   ```

---

## 4. Algorithms & Logic Specifications

### Diff Calculation Logic (`diff_engine.py`):
```python
def calculate_diff(breakdown_a: dict, breakdown_b: dict) -> dict:
    # breakdown_a: previous state, breakdown_b: current state
    cats_a = {item["category"]: item["tokens"] for item in breakdown_a.get("breakdown", [])}
    cats_b = {item["category"]: item["tokens"] for item in breakdown_b.get("breakdown", [])}
    
    all_categories = set(cats_a.keys()).union(set(cats_b.keys()))
    
    diff_cats = {}
    added = 0
    removed = 0
    
    for cat in all_categories:
        prev = cats_a.get(cat, 0)
        curr = cats_b.get(cat, 0)
        delta = curr - prev
        
        if delta > 0:
            added += delta
        else:
            removed += abs(delta)
            
        pct = round((delta / max(1, prev)) * 100, 2)
        diff_cats[cat] = {
            "previous": prev,
            "current": curr,
            "delta": delta,
            "percentage": pct
        }
        
    net = added - removed
    prev_total = sum(cats_a.values())
    net_pct = round((net / max(1, prev_total)) * 100, 2)
    
    return {
        "net_change_tokens": net,
        "percentage_change": net_pct,
        "added_tokens": added,
        "removed_tokens": removed,
        "categories": diff_cats
    }
```

---

## 5. Validation and Safety Constraints
- Tránh chia cho 0 khi phần trăm thay đổi của danh mục rỗng trước đó bằng cách đặt `max(1, prev)`.
- Ràng buộc khóa ngoại `FOREIGN KEY(request_id) REFERENCES provider_requests(request_id)` bảo toàn tính toàn vẹn dữ liệu.

---

## 6. Backward Compatibility & Migration Mapping
Bảng di trú `token_diffs` độc lập hoàn toàn, không sửa cấu trúc bảng `provider_requests` cũ, đảm bảo tương thích ngược 100%.

---

## 7. Implementation Checklist
- [ ] Triển khai `skills/workflow-runtime/scripts/diff_engine.py`.
- [ ] Nâng cấp `skills/workflow-runtime/scripts/db.py` với bảng di trú `token_diffs` và hàm lưu/lấy dữ liệu.
- [ ] Bổ sung lệnh CLI `usage diff` trong `skills/workflow-runtime/scripts/workflow_runtime.py`.
- [ ] Mở rộng `extension.ts` để gọi CLI và bắn sự kiện diff về Webview.
- [ ] Thiết kế Token Diff Panel trên `webview.html`.
- [ ] Chạy `node build.js` và `npm run compile`.
- [ ] Viết bộ test `skills/workflow-runtime/tests/test_diff_engine.py` và chạy xác thực.

---

## 8. Acceptance Criteria & Test Mapping

| Requirement ID | Requirement Description | Expected Result | Verification Method | Unit/Integration Test Target |
| :--- | :--- | :--- | :--- | :--- |
| `REQ-001` | Tính toán hiệu số | Trả về sai biệt +/- chính xác từng danh mục | Chạy bộ unittest | `test_diff_engine.py:test_calculate_diff` |
| `REQ-002` | SQLite Persistence | Lưu trữ và không trùng lặp bản ghi diff | Chạy bộ unittest | `test_diff_engine.py:test_db_persistence` |
| `REQ-003` | CLI diff command | Lệnh `usage diff` hiển thị dạng JSON đúng chuẩn | Chạy thử dòng lệnh | `test_diff_engine.py` |

---

## 9. Disallowed Outputs Validation
- [x] Không dùng đường dẫn tuyệt đối hoặc `file://` trong thiết kế.
- [x] Không sử dụng các từ viết tắt `TBD` hoặc placeholder rỗng.
