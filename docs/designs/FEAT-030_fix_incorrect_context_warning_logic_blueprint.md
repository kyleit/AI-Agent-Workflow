<!-- File path: docs/designs/FEAT-030_fix_incorrect_context_warning_logic_blueprint.md -->

---
feature_id: FEAT-030
feature_name: Fix Incorrect Context Warning Logic
status: reviewed
stage: blueprint
created_at: 2026-07-08
updated_at: 2026-07-08
previous_artifact: ../plans/FEAT-030_fix_incorrect_context_warning_logic_plan.md
next_artifact: [Implementation (Source Code)](../../)
---

# Technical Blueprint & Implementation Contract – Fix Incorrect Context Warning Logic

## 0. Baseline Context & References
- **Memory Baseline**: Memory Status is FRESH. Memory Confidence is High. Memory source matches [project-summary.md](file:///e:/AgentsProject/.agents/memory/project-summary.md).
- **RAG Queries**: Context Warning Threshold logic.
- **Inspected Source Files**:
  - `extensions/visualizer/resources/webview.html`
  - `.agents/workflow.config.json`
  - `.agents/skills/workflow-runtime/scripts/state_sync.py`
  - `.agents/skills/workflow-runtime/scripts/workflow_runtime.py`

## 1. File-by-File Analysis & Proposed Mutations

| File Path | Operation | Responsibility | Dependency | Impact & Risk |
| :--- | :--- | :--- | :--- | :--- |
| `.agents/workflow.config.json` | MODIFY | Khai báo cấu hình `telemetry` chứa các ngưỡng động. | JSON | Không có rủi ro. |
| `templates/workflow.config.json.template` | MODIFY | Đồng bộ tệp template cấu hình. | JSON | Không có rủi ro. |
| `skills/workflow-runtime/scripts/workflow_runtime.py` | MODIFY | Đọc cấu hình telemetry từ `workflow.config.json` và lưu vào `session["telemetry_config"]`. | `session.py` | Thấp. |
| `.agents/skills/workflow-runtime/scripts/workflow_runtime.py` | MODIFY | Cập nhật đồng bộ tệp runtime hoạt động. | `session.py` | Thấp. |
| `skills/workflow-runtime/scripts/state_sync.py` | MODIFY | Lưu và tải `telemetry_config` từ tệp `runtime.json`. | JSON | Thấp. |
| `.agents/skills/workflow-runtime/scripts/state_sync.py` | MODIFY | Cập nhật đồng bộ tệp hoạt động. | JSON | Thấp. |
| `extensions/visualizer/resources/webview.html` | MODIFY | Cập nhật logic Javascript để đọc ngưỡng cấu hình, phân tách cảnh báo dung lượng context và chi phí. | HTML/JS | Cực thấp. |
| `skills/workflow-runtime/tests/test_runtime.py` | MODIFY | Viết test case giả lập các ngưỡng phần trăm và chi phí. | `unittest` | Thấp. |
| `.agents/skills/workflow-runtime/tests/test_runtime.py` | MODIFY | Cập nhật đồng bộ tệp unit test. | `unittest` | Thấp. |

## 2. Target Folder Structure
Cấu trúc thư mục không thay đổi.

## 3. Interface & Data Contracts
### Cấu hình `telemetry` mới trong `workflow.config.json`
```json
  "telemetry": {
    "context_thresholds": {
      "warning": 60,
      "high": 80,
      "critical": 95
    },
    "cost_thresholds": {
      "warning_usd": 10.0,
      "critical_usd": 50.0
    }
  }
```

### JSON Schema in `runtime.json`
```json
  "telemetry_config": {
    "context_thresholds": {
      "warning": 60,
      "high": 80,
      "critical": 95
    },
    "cost_thresholds": {
      "warning_usd": 10.0,
      "critical_usd": 50.0
    }
  }
```

## 4. Algorithms & Key Logic
### Phân tích trạng thái Context
1. Lấy `activePercentage` từ trạng thái phiên.
2. So sánh với cấu hình telemetry nhận được từ `data.telemetry_config`:
   - `activePercentage >= critical` -> Trạng thái **Critical**.
   - `activePercentage >= high` -> Trạng thái **High**.
   - `activePercentage >= warning` -> Trạng thái **Warning (Moderate)**.
   - Ngược lại -> Trạng thái **Healthy**.

### So sánh và Hiển thị trong Webview
Hộp thông báo `alertText` sẽ chứa một mảng các cảnh báo được ghép lại bởi ký tự xuống dòng `<br/>`:
- Cảnh báo dung lượng ngữ cảnh dựa trên trạng thái ở trên (bao gồm cả trạng thái Healthy hiển thị số token còn lại).
- Cảnh báo chi phí dựa trên so sánh số USD thực tế với ngưỡng cấu hình.
- Cảnh báo hiệu suất I/O và số lượt đọc file trùng lặp.

## 5. State Machine & Transitions
Không có thay đổi về máy trạng thái SDLC.

## 6. Validation Rules
- Sử dụng fallback mặc định nếu tệp cấu hình không chứa đầy đủ các khóa telemetry.

## 7. Implementation Checklist
- [ ] Thêm cấu hình telemetry vào `.agents/workflow.config.json` và `templates/workflow.config.json.template`.
- [ ] Sửa đổi `workflow_runtime.py` cục bộ và hoạt động để gán `session["telemetry_config"]`.
- [ ] Sửa đổi `state_sync.py` cục bộ và hoạt động để đọc/ghi `telemetry_config` từ `runtime.json`.
- [ ] Sửa đổi `webview.html` để cập nhật hiển thị UX.
- [ ] Biên dịch `webview.html` sang `webviewHtml.ts` và chạy `npm run compile`.
- [ ] Viết unit test cho các mức phần trăm và phân tách chi phí trong `test_runtime.py`.
- [ ] Chạy và đảm bảo các bài test đều PASS.

## 8. Verification & Test Plan
### Unit Tests Target
Thêm hàm `test_telemetry_thresholds_and_warning_logic` trong `TestRuntimeEngine` kiểm chứng:
- Mức 12% và 45% -> Context = Healthy, cost = Healthy.
- Mức 61% -> Context = Warning (Moderate).
- Mức 79% -> Context = Warning.
- Mức 81% -> Context = High.
- Mức 95% -> Context = Critical.
- Mức 99% -> Context = Critical.
- Trường hợp context = 12% nhưng chi phí = $15.0 USD (vượt ngưỡng warning $10.0 USD) -> Context = Healthy, Cost = Warning.
