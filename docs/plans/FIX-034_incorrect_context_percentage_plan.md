<!-- File path: docs/plans/FIX-034_incorrect_context_percentage_plan.md -->

---
feature_id: FIX-034
feature_name: Incorrect Active Context Percentage
status: reviewed
stage: planning
created_at: 2026-07-09
updated_at: 2026-07-09
previous_artifact: ../brainstorming/FIX-034_incorrect_context_percentage.md
next_artifact: ../designs/FIX-034_incorrect_context_percentage_blueprint.md
---

# FIX-034: Incorrect Active Context Percentage

## Objective
- **Business Objective**: Sửa chữa sự sai lệch toán học trên biểu đồ và nhãn hiển thị Active Context Window của Visualizer dashboard. Đảm bảo số lượng token hoạt động hiển thị khớp chuẩn xác với phần trăm tương ứng trên công thức `active_tokens / limit_tokens`.
- **Expected Outcome**: Nhãn hiển thị chính xác lượng token hoạt động thực tế (ví dụ: `828.7K / 2.0M active tokens` -> `41.4%`), loại bỏ hoàn toàn hiển thị sai lệch dạng `363.1M / 2.0M active tokens` -> `37.1%`.

## Scope

### Included
- Sửa gán biến của `session["context_usage"]["total_tokens"]` trong `workflow_runtime.py` thành `usage.get("active_tokens", 0)`.
- Sửa fallback biến `activeTotal` trong `webview.html` để ưu tiên `wf.active_tokens`.
- Bảo đảm tính nhất quán toán học của progress bar, nhãn phần trăm và logic cảnh báo (warning logic).

### Excluded
- Không thay đổi cách đo lường hay thuật toán đếm token trong tệp `context.py`.
- Không chạm vào logic lưu trữ lịch sử request của FEAT-033.

## Project Impact
- **Backend CLI**: `workflow_runtime.py` (sửa đổi gán biến `context_usage` để đồng bộ đúng biến active).
- **Frontend Extension**: `webview.html` (cập nhật cách phân giải biến hiển thị token hoạt động).

## Dependencies
- Phép đo lường token hoạt động của `context.py` hoạt động bình thường.

## Risks
- Không có rủi ro hệ thống đáng kể nào do đây chỉ là sửa đổi luồng dữ liệu hiển thị (binding flow).

## Acceptance Criteria
- [ ] Phần trăm hiển thị trong card Active Context bằng chính xác `active_tokens / limit_tokens` (sai số <= 0.1%).
- [ ] Số lượng token hiển thị đúng định dạng (K/M) của active tokens, không hiển thị tổng lũy kế (total accumulated tokens).

## Deliverables
- Sửa đổi mã nguồn backend `workflow_runtime.py`.
- Sửa đổi mã nguồn giao diện `webview.html`.
- Biên dịch lại Webview HTML sang `webviewHtml.ts`.
- Bộ unit test kiểm tra tính nhất quán toán học.

## Estimated Complexity
- **Low**: Chỉ sửa luồng gán dữ liệu và binding biến hiển thị.

## Recommended Blueprint Focus
- Tập trung vào chi tiết sửa đổi các đoạn gán biến và fallback binding trong cả Python và HTML để đảm bảo an toàn, không làm đứt gãy tính tương thích ngược với các phiên bản session cũ.

## Recommended Next Skill
/blueprint
