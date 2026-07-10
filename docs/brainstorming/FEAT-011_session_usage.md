<!-- docs/brainstorming/FEAT-011_session_usage.md -->

---
feature_id: FEAT-011
feature_name: Update Extension UI with Full Session Token & Cost Metrics
status: draft
stage: brainstorming
created_at: 2026-07-06
updated_at: 2026-07-06
previous_artifact: None
next_artifact: ../plans/FEAT-011_session_usage_plan.md
---

# Master Requirement Document – Session Usage Panel & Metrics in VSCode Visualizer Extension

Bản đặc tả khám phá yêu cầu tích hợp hiển thị chi phí và lượng token của toàn bộ phiên thưa Ba.

## 1. Feature ID & Name
- **Feature ID**: FEAT-011
- **Feature Name**: Update Extension UI with Full Session Token & Cost Metrics

## 2. Original Idea
Bổ sung một khối thông tin "Session Usage" vào Visualizer Sidebar Extension để hiển thị toàn bộ chỉ số về lượng token (đầu vào, đầu ra, bộ nhớ đệm, suy nghĩ, giới hạn) và chi phí ước tính của toàn bộ phiên chạy SDLC, đọc động từ tệp `.session.json`.

## 3. Business Problem
- **Vấn đề**: Hiện tại Visualizer chỉ hiển thị phần trăm dung lượng ngữ cảnh hiện thời một cách chung chung từ ước lượng của frontend. Người dùng không biết được tổng số lượng token thực tế đã tiêu thụ của toàn bộ phiên làm việc là bao nhiêu, và chi phí tài chính tích lũy ước tính là bao nhiêu.
- **Giải pháp**: Hiển thị bảng chi tiết các số liệu tích lũy của toàn bộ session (Total Tokens, Input, Output, Cache, Thinking, Cost USD, Provider, Model, Accuracy, Updated Time) được cập nhật động.

## 4. Requirement Discovery
- **Functional Requirements**:
  - FR-01: Giao diện hiển thị các trường:
    - Total Tokens (Tổng số token tích lũy dạng rút gọn, ví dụ: 235.5K)
    - Input / Output Tokens
    - Cache / Thinking Tokens
    - Context Limit (Giới hạn ngữ cảnh, ví dụ: 2.0M)
    - Usage Percentage (Tỷ lệ phần trăm)
    - Estimated Cost (Chi phí ước tính dạng USD, ví dụ: $0.62)
    - Provider, Model, Accuracy, Last Updated Time
  - FR-02: Thanh tiến trình (Progress bar) tự động đổi màu theo ngưỡng:
    - Dưới 60%: Bình thường (Theme color mặc định)
    - Từ 60% đến 85%: Cảnh báo (Màu vàng/cam)
    - Trên 85%: Nguy cấp (Màu đỏ)
  - FR-03: Hiển thị tooltip giải thích: "These metrics estimate the total token usage and cost for the entire workflow session. Values may be estimated depending on provider support."
  - FR-04: Xử lý an toàn dữ liệu trống (Empty State) hiển thị "Waiting for runtime usage data..." nếu không tìm thấy cấu trúc dữ liệu.
- **Non-functional Requirements**:
  - NFR-01: Không làm hỏng hoặc ảnh hưởng tới tiến trình hiển thị workflow và checkpoints hiện tại.
  - NFR-02: Phù hợp với màu sắc, kích thước và ngôn ngữ giao diện (Theme tokens) của extension.

## 5. Requirement Readiness Score
- **Score**: 100/100
- **Status**: Ready (>= 85)

## 6. Selected Solution
- **Thiết kế giao diện**: Tạo thêm một thẻ mới `<section class="glass usage-card" id="session-usage-card">` nằm ngay dưới tệp session card trong Sidebar Webview, sử dụng các hàm định dạng dữ liệu Javascript để vẽ giao diện động.
