<!-- docs/brainstorming/FEAT-041_api_usage_calculations_and_ui_redesign.md -->

---
feature_id: FEAT-041
feature_name: API Usage Audit & Budget UI Redesign
status: draft
stage: brainstorming
created_at: 2026-07-09
updated_at: 2026-07-09
previous_artifact: None
next_artifact: ../plans/FEAT-041_api_usage_calculations_and_ui_redesign_plan.md
---

# Master Requirement Document – UI Redesign & API Usage Audit

## 1. Feature ID & Name
- **Feature ID**: FEAT-041
- **Feature Name**: API Usage Audit & Budget UI Redesign

## 2. Original Idea
[Exact user input, unmodified]
Before implementing any UI changes for Phase 6 – Context Budget Controller, you MUST invoke the frontend-design skill.
Do NOT directly modify the dashboard UI without first completing the frontend-design workflow and producing the required design artifacts.

Budget Tab Redesign:
When Phase 6 IS implemented: Replace the placeholder with a complete Budget Controller dashboard.
Include:
- Context Budget Status
- Current Budget Usage
- Remaining Budget
- Predicted Next Request
- Budget Policy
- Optimization Recommendations
- Estimated Savings
- Budget History
- Simulation ("With Optimization" vs "Without Optimization")
- Auto / Manual Optimization Mode

Navigation Improvements:
Review the entire top navigation using the frontend-design skill.
Verify: Naming consistency, Icon consistency, Visual hierarchy, Active state, Empty states, Responsive behavior, Accessibility.

Verify Accumulated API Usage Calculations:
Audit the Accumulated API Usage calculation logic before modifying or extending this section.
Do not assume the displayed values are correct.
Verify that:
- Total Input equals the sum of all provider input tokens.
- Total Output equals the sum of all provider output tokens.
- Cache Usage matches provider cache usage.
- Thinking tokens match provider thinking usage.
- Requests equals the number of unique provider requests.
- Cost equals the provider pricing calculation.

## 3. Business Problem
- **Problem**: Số liệu tích lũy API usage bị hiển thị sai lệch đơn vị, số lượng Requests luôn hiển thị bằng 1, và tab Budget hiện tại chỉ là placeholder chưa có đầy đủ thông tin mô phỏng và cấu hình chính sách.
- **Expected Outcome**: Số liệu hiển thị hoàn toàn trùng khớp giữa DB, CLI và Webview Dashboard; tab Budget hiển thị đầy đủ thông số mô phỏng và chính sách.

## 4. Requirement Discovery
- **Functional Requirements**:
  - FR-01: Chuyển đổi logic tổng hợp số liệu của `get_workflow_summary` sang dạng sum các dòng trong bảng `provider_requests`.
  - FR-02: Thiết kế cấu trúc JSON phản hồi chứa đầy đủ thông tin lồng của `accumulated_usage` và `active_context`.
  - FR-03: Thiết kế lại giao diện tab Budget hiển thị: Trạng thái, dung lượng sử dụng/còn lại, cấu hình chế độ Auto/Manual, bảng mô phỏng With vs Without Optimization.
  - FR-04: Đánh giá và chuẩn hóa giao diện thanh Navigation trên đầu.
- **Non-functional Requirements**:
  - NFR-01: Đảm bảo độ chính xác toán học 100% giữa raw provider requests và dữ liệu tổng hợp.

## 5. Solution Options Evaluated

### Option A: Query-based DB Aggregation + Redesigned Budget Dashboard (Khuyên dùng)
- **Overview**:
  - Đổi câu lệnh SQL trong `get_workflow_summary` để SUM từ bảng `provider_requests` theo `conversation_id`.
  - Cải tiến giao diện tab Budget trong `webview.html` để vẽ sơ đồ ngân sách, giả lập With vs Without Optimization và nút gạt Auto/Manual Mode.
- **Advantages**: Khắc phục triệt để lỗi sai lệch số liệu và cải thiện trải nghiệm người dùng theo đúng nguyên tắc UX.
- **Complexity**: Medium

### Option B: Giữ nguyên cách parse từ transcript và bổ sung thủ công số requests
- **Disadvantages**: Vẫn dễ gặp lỗi bất đồng bộ số liệu nếu tệp transcript ghi nhận chậm.

## 6. Selected Solution
- **Choice**: Option A — Query-based DB Aggregation + Redesigned Budget Dashboard

## 7. Acceptance Criteria
- [ ] Số lượng requests đếm chính xác số dòng trong `provider_requests`.
- [ ] Tổng cost USD bằng tổng cost của tất cả requests.
- [ ] Giao diện tab Budget hiển thị đầy đủ thông tin mô phỏng và chế độ tự động tối ưu hóa.
