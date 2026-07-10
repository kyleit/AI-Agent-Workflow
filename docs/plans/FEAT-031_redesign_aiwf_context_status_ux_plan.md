<!-- File path: docs/plans/FEAT-031_redesign_aiwf_context_status_ux_plan.md -->

---
feature_id: FEAT-031
feature_name: Redesign AIWF Context Status UX
status: reviewed
stage: planning
created_at: 2026-07-08
updated_at: 2026-07-08
previous_artifact: ../brainstorming/FEAT-031_redesign_aiwf_context_status_ux.md
next_artifact: ../designs/FEAT-031_redesign_aiwf_context_status_ux_blueprint.md
---

# FEAT-031: Redesign AIWF Context Status UX

## Objective
- Thiết kế lại hoàn toàn giao diện Telemetry phía Footer của Visualizer thành 3 card riêng biệt: **Context Analytics**, **API Usage**, và **Efficiency Analysis**.
- Phân biệt rõ ràng trạng thái **Healthy** (xanh lục, dùng biểu tượng 🟢, ẩn hộp cảnh báo hoặc dùng thẻ trung tính) với các trạng thái cảnh báo **Warning/High/Critical** (icon 🟡/🟠/🔴, có hộp cảnh báo chuyên biệt).
- Đảm bảo toàn bộ theme của cảnh báo (màu chữ, màu nền, màu viền, icon) và các ngưỡng chi phí/phần trăm được nạp động từ tệp cấu hình và có thể cấu hình hóa dễ dàng.

## Scope
### Included
- Cấu hình theme/style trong [.agents/workflow.config.json](file:///e:/AgentsProject/.agents/workflow.config.json) và tệp template.
- Cập nhật backend runtime (`workflow_runtime.py` và `state_sync.py`) để đồng bộ khối cấu hình style này qua `runtime.json`.
- Thiết kế lại bố cục DOM trong [webview.html](file:///e:/AgentsProject/extensions/visualizer/resources/webview.html) thành 3 khối card độc lập:
  - `Context Analytics Card`: Giám sát giới hạn context, tỷ lệ %, dung lượng còn lại, sparkline và trạng thái Context.
  - `API Usage Card`: Tổng Input, Output, Cache, Thinking tokens, số Requests, tổng chi phí USD.
  - `Efficiency Analysis Card`: Tỷ lệ I/O, Cache Hit, Memory/RAG Hit, số lượt đọc trùng lặp, ước tính tiết kiệm và cảnh báo chi phí.
- Tải cấu hình style động trong Javascript để vẽ hộp cảnh báo và badge trạng thái theo đúng theme đã cấu hình.
- Biên dịch lại Webview Extension và đóng gói VSIX mới.
- Viết Unit Tests kiểm tra cấu hình style động.

### Excluded
- Không làm thay đổi giao diện Sidebar Stepper ở phần trên.

## Dependencies
- Phải chạy `node build.js` để biên dịch `webview.html` sang `webviewHtml.ts`.
- Cần biên dịch gói VSIX mới để thử nghiệm cài đặt trực tiếp.

## Risks
- **Risk**: Emoji có thể hiển thị khác nhau trên các hệ điều hành cũ.
- **Mitigation**: Kết hợp dùng mã màu CSS mạnh mẽ và viền neon bóng bẩy đi kèm để biểu thị mức độ nghiêm trọng rõ ràng.

## Acceptance Criteria
- [ ] Giao diện được tách thành 3 card riêng biệt.
- [ ] Trạng thái Healthy của Context hiển thị màu xanh lục với icon 🟢, không sử dụng hộp cảnh báo màu vàng cảnh báo.
- [ ] Chỉ hiển thị alert box của Context khi tỷ lệ vượt quá ngưỡng Warning (60%).
- [ ] Cảnh báo chi phí tích lũy hiển thị độc lập tại card Efficiency Analysis.
- [ ] Toàn bộ unit tests chạy thành công.

## Recommended Next Skill
/blueprint
