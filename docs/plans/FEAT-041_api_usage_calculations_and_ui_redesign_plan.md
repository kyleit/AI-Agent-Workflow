<!-- File path: docs/plans/FEAT-041_api_usage_calculations_and_ui_redesign_plan.md -->

---
feature_id: FEAT-041
feature_name: API Usage Audit & Budget UI Redesign
status: reviewed
stage: planning
created_at: 2026-07-09
updated_at: 2026-07-09
previous_artifact: ../brainstorming/FEAT-041_api_usage_calculations_and_ui_redesign.md
next_artifact: ../designs/FEAT-041_api_usage_calculations_and_ui_redesign_blueprint.md
---

# FEAT-041: API Usage Audit & Budget UI Redesign

## Objective
- **Business Objective**: Chuẩn hóa toàn bộ số liệu API usage lũy kế đảm bảo tính chính xác 100% bằng cách tổng hợp trực tiếp từ cơ sở dữ liệu `provider_requests` thay vì đọc từ transcript. Đồng thời cải tiến giao diện tab Budget hiển thị thông tin ngân sách thực tế và mô phỏng With vs Without Optimization.
- **Expected Outcome**:
  - API usage lũy kế hiển thị chính xác các chỉ số bao gồm đếm đúng số requests.
  - Tab Budget hiển thị đầy đủ biểu đồ tiến trình sử dụng, ngân sách còn lại, chế độ tối ưu hóa, và lịch sử ngân sách.

## Scope

### Included
- Đổi câu lệnh SQL trong `get_workflow_summary`, `get_project_summary` để tính tổng trực tiếp từ bảng `provider_requests`.
- Thiết lập lại tab Budget và nâng cấp thanh Navigation trên Dashboard Webview.
- Giao tiếp CLI hỗ trợ chế độ cấu hình tự động/thủ công tối ưu hóa.

### Excluded
- Không làm thay đổi logic các model/provider hiện tại của AIWF.

## Risks
- **Risk**: Cơ sở dữ liệu `provider_requests` có thể bị rỗng ở lần chạy đầu tiên.
  - **Mitigation**: Cung cấp cơ chế fallback sử dụng dữ liệu mặc định an toàn.

## Acceptance Criteria
- [ ] Số requests đếm đúng.
- [ ] Tab Budget hiển thị chính xác các trường ngân sách và mô phỏng With vs Without.
- [ ] Giao diện Webview đồng bộ dữ liệu.
