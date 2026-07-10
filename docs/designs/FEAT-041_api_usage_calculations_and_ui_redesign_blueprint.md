<!-- File path: docs/designs/FEAT-041_api_usage_calculations_and_ui_redesign_blueprint.md -->

---
feature_id: FEAT-041
feature_name: API Usage Audit & Budget UI Redesign
status: reviewed
stage: blueprint
created_at: 2026-07-09
updated_at: 2026-07-09
previous_artifact: ../plans/FEAT-041_api_usage_calculations_and_ui_redesign_plan.md
next_artifact: [Implementation (Source Code)](../../)
---

# Technical Blueprint & Implementation Contract – API Usage Audit & Budget UI Redesign

## 0. Baseline Context & References
- **Memory Baseline**: Tích hợp trực tiếp các chỉ số đếm từ bảng requests để sửa lỗi requests = 1 và tokens bị nhân ảo.
- **Inspected Source Files**:
  - `skills/workflow-runtime/scripts/db.py`
  - `extensions/visualizer/resources/webview.html`

---

## 1. File-by-File Analysis & Proposed Mutations

| File Path | Operation | Responsibility | Dependency | Impact & Risk |
| :--- | :--- | :--- | :--- | :--- |
| `skills/workflow-runtime/scripts/db.py` | `MODIFY` | Chuyển đổi logic các hàm `get_workflow_summary`, `get_project_summary`, `get_global_summary` sang tổng hợp trực tiếp từ bảng `provider_requests`. | None | Trung bình. Cần đảm bảo cơ chế fallback hoạt động tốt khi DB trống. |
| `extensions/visualizer/resources/webview.html` | `MODIFY` | Thiết kế lại giao diện tab Budget hiển thị: Trạng thái, dung lượng sử dụng, ngân sách còn lại, mô phỏng With vs Without Optimization, và nút chọn Auto/Manual Mode. | None | Thấp. |

---

## 2. Interface Contracts

### Public Interface Contracts:
1. **get_workflow_summary return format**:
   ```python
   {
       "provider": str,
       "model": str,
       "active_context": {
           "total_tokens": int,
           "limit_tokens": int,
           "percentage": float
       },
       "accumulated_usage": {
           "input_tokens": int,
           "output_tokens": int,
           "cache_tokens": int,
           "thinking_tokens": int,
           "total_tokens": int,
           "estimated_cost_usd": float,
           "request_count": int
       },
       "efficiency": {
           "cache_hit_ratio": float,
           "input_to_output_ratio": float
       }
   }
   ```

2. **Budget Tab UI Components**:
   - `budget-remaining-bar`: Thanh tiến trình hiển thị phần trăm ngân sách còn lại.
   - `budget-mode-selector`: Nút chuyển đổi Auto vs Manual Mode.
   - `budget-simulation-comparison`: Bản so sánh thông số giả lập With vs Without.

---

## 3. Implementation Checklist
- [ ] Chuyển đổi logic SQL tổng hợp trong `db.py` sang đếm trực tiếp từ `provider_requests`.
- [ ] Loại bỏ hoặc làm sạch logic nhân ảo trong `normalize_database_records`.
- [ ] Thiết kế lại giao diện tab Budget trong `webview.html` đáp ứng đầy đủ yêu cầu UX/UI.
- [ ] Biên dịch lại webview bằng `node build.js` và `npm run compile`.
- [ ] Viết unittest kiểm chứng đếm chính xác số requests và tích lũy.
