<!-- File path: docs/designs/FEAT-036_runtime_insights_advisor_blueprint.md -->

---
feature_id: FEAT-036
feature_name: Runtime Insights & Optimization Advisor
status: reviewed
stage: blueprint
created_at: 2026-07-09
updated_at: 2026-07-09
previous_artifact: ../plans/FEAT-036_runtime_insights_advisor_plan.md
next_artifact: [Implementation (Source Code)](../../)
---

# Technical Blueprint & Implementation Contract – Runtime Insights & Optimization Advisor

## 0. Baseline Context & References
- **Memory Baseline**: Dữ liệu lịch sử request breakdown của các Phase trước trong bảng SQLite `provider_requests` và `token_diffs`.
- **Inspected Source Files**:
  - `skills/workflow-runtime/scripts/db.py`
  - `skills/workflow-runtime/scripts/workflow_runtime.py`
  - `extensions/visualizer/resources/webview.html`

---

## 1. File-by-File Analysis & Proposed Mutations

| File Path | Operation | Responsibility | Dependency | Impact & Risk |
| :--- | :--- | :--- | :--- | :--- |
| `skills/workflow-runtime/scripts/insights_engine.py` | `NEW` | Chứa logic Heuristics Engine chẩn đoán, đề xuất tối ưu hóa và cách tính Efficiency Score. | None | Thấp. Module hoàn toàn độc lập. |
| `skills/workflow-runtime/scripts/db.py` | `MODIFY` | Di trú 2 bảng SQLite `insight_snapshots` và `recommendations`, cùng các hàm CRUD tương ứng. | `insights_engine.py` | Thấp. Cần bảo vệ dữ liệu cũ. |
| `skills/workflow-runtime/scripts/workflow_runtime.py` | `MODIFY` | Tích hợp các subcommands CLI `usage insights`, `usage recommend`, và `usage optimize`. | `db.py`, `insights_engine.py` | Thấp. |
| `extensions/visualizer/resources/webview.html` | `MODIFY` | Thêm tab **Runtime Insights Dashboard**, biểu đồ gauge điểm hiệu năng, danh sách thẻ đề xuất hành động. | `extension.ts` | Thấp. |
| `extensions/visualizer/src/extension.ts` | `MODIFY` | Bổ sung API `getRuntimeInsights` và `acceptRecommendation` gọi CLI Python bất đồng bộ. | None | Thấp. |

---

## 2. Target Folder Structure
```text
.
├── docs
│   ├── designs
│   │   └── FEAT-036_runtime_insights_advisor_blueprint.md
│   └── plans
│       └── FEAT-036_runtime_insights_advisor_plan.md
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
        │   ├── insights_engine.py
        │   └── workflow_runtime.py
        └── tests
            └── test_insights_engine.py
```

---

## 3. Interface Contracts (Public & Internal)

### Public Interface Contracts:
1. **CLI Commands**:
   - `python workflow_runtime.py usage insights`: Trả về JSON báo cáo toàn bộ Insights.
   - `python workflow_runtime.py usage recommend`: Trả về danh sách đề xuất dạng JSON hoặc bảng.
   - `python workflow_runtime.py usage optimize --accept <id>`: Chấp nhận đề xuất có ID cụ thể.
   - `python workflow_runtime.py usage optimize --ignore <id>`: Bỏ qua đề xuất.

2. **SQLite Database Schema**:
   ```sql
   CREATE TABLE IF NOT EXISTS insight_snapshots (
       timestamp TEXT PRIMARY KEY,
       conversation_id TEXT NOT NULL,
       efficiency_score INTEGER NOT NULL,
       avg_tokens INTEGER NOT NULL,
       avg_cost REAL NOT NULL,
       growth_trend TEXT NOT NULL,
       insight_data_json TEXT NOT NULL
   );
   
   CREATE TABLE IF NOT EXISTS recommendations (
       id TEXT PRIMARY KEY,
       conversation_id TEXT NOT NULL,
       type TEXT NOT NULL,
       description TEXT NOT NULL,
       token_savings INTEGER NOT NULL,
       cost_savings REAL NOT NULL,
       priority TEXT NOT NULL,
       confidence REAL NOT NULL,
       status TEXT NOT NULL, -- pending, accepted, ignored
       timestamp TEXT NOT NULL
   );
   ```

---

## 4. Algorithms & Logic Specifications

### Recommendation Generator Logic (`insights_engine.py`):
```python
def run_heuristics(requests: list, conversation_id: str) -> list[dict]:
    recs = []
    
    # 1. Rule: Reduce Conversation History
    total_conv_history = 0
    total_tokens = 0
    for r in requests:
        if r.get("context_breakdown_json"):
            import json
            try:
                cb = json.loads(r["context_breakdown_json"])
                for cat in cb.get("breakdown", []):
                    if cat["category"] == "Conversation History":
                        total_conv_history += cat["tokens"]
                total_tokens += r["total_tokens"]
            except Exception:
                pass
                
    if total_tokens > 0 and (total_conv_history / total_tokens) > 0.60:
        recs.append({
            "type": "Reduce Conversation History",
            "description": "Conversation history accounts for > 60% of context size. Archive older messages to clean context.",
            "token_savings": int(total_conv_history * 0.4),
            "cost_savings": round((total_conv_history * 0.4) * 0.000003, 4),
            "priority": "High",
            "confidence": 0.85
        })
        
    # Additional heuristics: move repeated workspace reads to memory, split blueprints, etc.
    return recs
```

---

## 5. State Machine & Transitions
- Trạng thái của một đề xuất (Recommendation Status):
  `pending` --(Người dùng bấm Accept)--> `accepted`
  `pending` --(Người dùng bấm Ignore)--> `ignored`

---

## 6. Validation and Safety Constraints
- Điểm hiệu năng (Efficiency Score) được giới hạn chặt chẽ trong khoảng `[10, 100]`.
- Mọi ID đề xuất được tạo bằng hàm băm SHA-256 từ mô tả của đề xuất để tránh trùng lặp bản ghi.

---

## 7. Implementation Checklist
- [ ] Định nghĩa logic Heuristic chẩn đoán trong `insights_engine.py`.
- [ ] Cập nhật bảng di trú SQLite trong `db.py`.
- [ ] Thêm các lệnh CLI trong `workflow_runtime.py`.
- [ ] Bổ sung các lệnh API trong `extension.ts`.
- [ ] Xây dựng tab dashboard và thiết kế layout Insights trên `webview.html`.
- [ ] Biên dịch webview bằng `node build.js`.
- [ ] Viết unittest `test_insights_engine.py`.

---

## 8. Acceptance Criteria & Test Mapping

| Requirement ID | Requirement Description | Expected Result | Verification Method | Unit/Integration Test Target |
| :--- | :--- | :--- | :--- | :--- |
| `REQ-001` | Tính toán chỉ số | Heuristics tính toán đúng Efficiency score và savings | Chạy unittest | `test_insights_engine.py:test_insights_calculation` |
| `REQ-002` | SQLite Persistence | Trạng thái đề xuất lưu và lấy chính xác | Chạy unittest | `test_insights_engine.py:test_db_recommendations` |
| `REQ-003` | CLI commands | Lệnh CLI `usage insights` trả về dữ liệu đúng cấu trúc | Gọi CLI kiểm chứng | `test_insights_engine.py` |

---

## 9. Disallowed Outputs Validation
- [x] Không sử dụng đường dẫn tuyệt đối hoặc link `file://`.
- [x] Không sử dụng các từ viết tắt `TBD` hay placeholder rỗng.
