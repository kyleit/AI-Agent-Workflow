<!-- File path: docs/designs/FEAT-037_context_timeline_forecast_blueprint.md -->

---
feature_id: FEAT-037
feature_name: Context Timeline & Predictive Analytics
status: reviewed
stage: blueprint
created_at: 2026-07-09
updated_at: 2026-07-09
previous_artifact: ../plans/FEAT-037_context_timeline_forecast_plan.md
next_artifact: [Implementation (Source Code)](../../)
---

# Technical Blueprint & Implementation Contract – Context Timeline & Predictive Analytics

## 0. Baseline Context & References
- **Memory Baseline**: Dữ liệu sự kiện từ transcript log và dữ liệu tích lũy từ SQLite `provider_requests`.
- **Inspected Source Files**:
  - `skills/workflow-runtime/scripts/db.py`
  - `skills/workflow-runtime/scripts/context.py`
  - `skills/workflow-runtime/scripts/workflow_runtime.py`
  - `extensions/visualizer/resources/webview.html`

---

## 1. File-by-File Analysis & Proposed Mutations

| File Path | Operation | Responsibility | Dependency | Impact & Risk |
| :--- | :--- | :--- | :--- | :--- |
| `skills/workflow-runtime/scripts/forecaster.py` | `NEW` | Thuật toán hồi quy dự báo xu hướng phình to context/cost và tính xác suất cạn kiệt tài nguyên. | None | Thấp. Độc lập hoàn toàn. |
| `skills/workflow-runtime/scripts/db.py` | `MODIFY` | Di trú bảng SQLite `timeline_events` và cung cấp các hàm lưu/lấy sự kiện timeline. | `forecaster.py` | Thấp. |
| `skills/workflow-runtime/scripts/context.py` | `MODIFY` | Tự động phân tích transcript và ghi nhận các mốc sự kiện (Tool call, Skill start, Error, Compress...) vào SQLite. | `db.py` | Thấp. |
| `skills/workflow-runtime/scripts/workflow_runtime.py` | `MODIFY` | Tích hợp subcommands CLI `usage timeline` và `usage forecast`. | `db.py`, `forecaster.py` | Thấp. |
| `extensions/visualizer/resources/webview.html` | `MODIFY` | Thiết kế Tab **Timeline Dashboard** chứa đồ thị SVG xu hướng chi phí/token và danh sách sự kiện thời gian thực. | `extension.ts` | Thấp. |
| `extensions/visualizer/src/extension.ts` | `MODIFY` | Mở rộng API `getTimelineData` để nạp dữ liệu timeline từ CLI. | None | Thấp. |

---

## 2. Interface Contracts

### Public Interface Contracts:
1. **CLI Command API**:
   - `python workflow_runtime.py usage timeline --format json`: Trả về danh sách JSON của mọi sự kiện timeline.
   - `python workflow_runtime.py usage forecast --format json`: Trả về JSON báo cáo dự báo.

2. **SQLite Database Schema**:
   ```sql
   CREATE TABLE IF NOT EXISTS timeline_events (
       id INTEGER PRIMARY KEY AUTOINCREMENT,
       timestamp TEXT NOT NULL,
       conversation_id TEXT NOT NULL,
       event_type TEXT NOT NULL,
       checkpoint INTEGER NOT NULL,
       skill TEXT NOT NULL,
       request_id TEXT,
       active_context INTEGER NOT NULL,
       context_delta INTEGER NOT NULL,
       input_tokens INTEGER NOT NULL,
       output_tokens INTEGER NOT NULL,
       cost REAL NOT NULL,
       duration REAL NOT NULL,
       details_json TEXT NOT NULL
   );
   ```

---

## 3. Algorithms & Logic Specifications

### Predictive Engine Logic (`forecaster.py`):
```python
def make_forecast(events: list, limit=2000000) -> dict:
    if not events:
        return {"probability": "Low", "confidence": "Low", "remaining_requests": 99}
        
    req_events = [e for e in events if e.get("event_type") == "Provider request"]
    if len(req_events) < 2:
        return {"probability": "Low", "confidence": "Low", "remaining_requests": 99}
        
    # Calculate avg growth from delta of last requests
    deltas = [e.get("context_delta", 0) for e in req_events[-3:]]
    avg_growth = sum(deltas) / len(deltas)
    if avg_growth <= 0:
        avg_growth = 35000 # default fallback
        
    latest_ctx = req_events[-1].get("active_context", 0)
    remaining_tokens = limit - latest_ctx
    
    rem_reqs = max(1, int(remaining_tokens / avg_growth))
    
    if remaining_tokens < 200000:
        prob = "Critical"
        conf = "High"
    elif remaining_tokens < 500000:
        prob = "High"
        conf = "High"
    elif remaining_tokens < 1000000:
        prob = "Medium"
        conf = "Medium"
    else:
        prob = "Low"
        conf = "Medium"
        
    return {
        "exhaustion_probability": prob,
        "confidence_level": conf,
        "remaining_requests": rem_reqs,
        "predicted_next_context": latest_ctx + avg_growth,
        "estimated_cost_to_complete": round(rem_reqs * 0.045, 4)
    }
```

---

## 4. Implementation Checklist
- [ ] Xây dựng thuật toán dự báo hồi quy trong `forecaster.py`.
- [ ] Thêm bảng di trú SQLite `timeline_events` trong `db.py`.
- [ ] Intercept ghi nhận sự kiện timeline trong `context.py`.
- [ ] Tích hợp dòng lệnh CLI trong `workflow_runtime.py`.
- [ ] Mở rộng backend API gọi CLI của Visualizer Extension trong `extension.ts`.
- [ ] Thiết kế Tab Dashboard Timeline trực quan vẽ SVG charts trong `webview.html`.
- [ ] Chạy `node build.js` và `npm run compile`.
- [ ] Viết unittest `test_forecaster.py`.
