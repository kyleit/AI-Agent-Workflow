<!-- File path: docs/plans/FEAT-030_fix_incorrect_context_warning_logic_plan.md -->

---
feature_id: FEAT-030
feature_name: Fix Incorrect Context Warning Logic
status: reviewed
stage: planning
created_at: 2026-07-08
updated_at: 2026-07-08
previous_artifact: ../brainstorming/FEAT-030_fix_incorrect_context_warning_logic.md
next_artifact: ../designs/FEAT-030_fix_incorrect_context_warning_logic_blueprint.md
---

# FEAT-030: Fix Incorrect Context Warning Logic

## Objective
- Thay thế thuật toán cảnh báo Context cứng (ngưỡng 160K tokens) bằng thuật toán động dựa trên tỷ lệ phần trăm động so với giới hạn của mô hình (limit_tokens).
- Đưa các cấu hình ngưỡng (thresholds) vào tệp cấu hình dự án `workflow.config.json`.
- Phân tách rõ ràng hai loại cảnh báo: Context Capacity (Dung lượng Context hiện tại) và Cost/Efficiency (Hiệu suất chi phí).

## Scope
### Included
- Sửa đổi cấu hình dự án:
  - Thêm khối cấu hình `telemetry` vào [workflow.config.json](file:///e:/AgentsProject/.agents/workflow.config.json) và tệp template.
- Sửa đổi Python Runtime:
  - Cập nhật [workflow_runtime.py](file:///e:/AgentsProject/.agents/skills/workflow-runtime/scripts/workflow_runtime.py) và [workflow_runtime.py (gốc)](file:///e:/AgentsProject/skills/workflow-runtime/scripts/workflow_runtime.py) để nạp cấu hình telemetry và lưu vào trạng thái session.
  - Cập nhật [state_sync.py](file:///e:/AgentsProject/.agents/skills/workflow-runtime/scripts/state_sync.py) để ghi/đọc trường `telemetry_config` từ `runtime.json`.
- Sửa đổi Visualizer Webview:
  - Cập nhật [webview.html](file:///e:/AgentsProject/extensions/visualizer/resources/webview.html) để đọc `telemetry_config` và hiển thị cảnh báo phân tách động (Context & Chi phí độc lập).
  - Tự động biên dịch sang `webviewHtml.ts` và build lại Visualizer Extension.
- Viết Unit Tests:
  - Bổ sung các test case trong [test_runtime.py](file:///e:/AgentsProject/.agents/skills/workflow-runtime/tests/test_runtime.py) giả lập các mức phần trăm (12%, 45%, 61%, 79%, 81%, 95%, 99%) và trường hợp chi phí cao để xác nhận thông điệp cảnh báo chính xác.

### Excluded
- Không thay đổi thiết kế chung hay giao diện CSS của Visualizer Panel (chỉ chỉnh sửa phần logic hiển thị thông điệp cảnh báo).

## Project Impact
- **Configuration**: Thay đổi schema của `workflow.config.json`.
- **Backend Runtime**: Đồng bộ trạng thái telemetry qua file JSON trạng thái.
- **VS Code Extension**: Đóng gói phiên bản Extension mới với tệp HTML biên dịch mới.

## Dependencies
- Cần biên dịch `node build.js` và `npm run compile` sau khi sửa `webview.html`.
- Biên dịch gói VSIX mới để cài đặt kiểm thử.

## Risks
- **Risk**: Nếu tệp cấu hình dự án bị thiếu trường `telemetry`, có thể gây lỗi nạp trạng thái hoặc crash.
- **Mitigation**: Thiết lập bộ giá trị fallback mặc định an toàn cho mọi ngưỡng cảnh báo cả ở phía Backend và Frontend.

## Acceptance Criteria
- [ ] Mức phần trăm ngữ cảnh <60% hiển thị trạng thái Healthy kèm dung lượng ước tính còn lại.
- [ ] Các mức ngữ cảnh khác (60-80%: Warning, 80-95%: High, >95%: Critical) hiển thị đúng thông điệp theo ngữ cảnh động.
- [ ] Cảnh báo chi phí hoặc hiệu năng hiển thị độc lập trong alert box riêng mà không bị ghi nhãn là "Context High".
- [ ] Toàn bộ unit tests mới chạy thành công.

## Deliverables
- Bản cập nhật `workflow.config.json` và code runtime.
- Bản cập nhật `webview.html` và file VSIX mới được đóng gói.
- Tập kiểm thử mới được bổ sung vào `test_runtime.py`.

## Recommended Next Skill
/blueprint
