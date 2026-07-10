<!-- File path: docs/plans/FEAT-009_refactor_workflow_skills_plan.md -->

---
artifact_type: plan
feature_id: FEAT-009
workflow: standard
status: draft
created_at: 2026-07-06
updated_at: 2026-07-06
previous_artifact: ../brainstorming/FEAT-009_refactor_workflow_skills.md
next_artifact: ../designs/FEAT-009_refactor_workflow_skills_blueprint.md
---

# Project Plan – Refactor AI Workflow Skills

Bản kế hoạch quản lý dự án tối ưu hóa token và cấu trúc lại hệ thống kỹ năng thưa Ba.

## 1. Mục tiêu dự án
*   **Mục tiêu chính**: Cắt giảm khoảng 40%–60% kích thước các tệp kỹ năng (`SKILL.md`) bằng cách chuyển toàn bộ nội dung hướng dẫn chính sách bị trùng lặp sang tài liệu tập trung [AI_RULES.md](../../AI_RULES.md).
*   **Mục tiêu chất lượng**: Đảm bảo 100% không làm thay đổi luồng hoạt động, thứ tự checkpoint và khả năng tương thích của tệp `.session.json` với công cụ hiển thị (Visualizer extension).

## 2. Phạm vi thực hiện (Scope & Boundaries)
*   **Nằm trong phạm vi**:
    *   26 thư mục kỹ năng nằm trong thư mục nguồn `skills/` của dự án.
    *   Đồng bộ hóa các thay đổi sang thư mục `.agents/skills/`.
    *   Giữ lại các mô tả cụ thể về đầu vào, đầu ra, các mốc checkpoint và các hướng dẫn logic lõi của riêng từng kỹ năng.
*   **Nằm ngoài phạm vi**:
    *   Không thay đổi hoặc thiết kế lại quy trình làm việc của dự án (Workflow SDLC).
    *   Không sửa đổi bất kỳ mã nguồn ứng dụng hay logic nghiệp vụ nào của extension.
    *   Không sửa đổi cơ chế ghi nhận tệp cấu hình phiên chạy nguyên tử.

## 3. Các đầu mục công việc & Giai đoạn (Tasks & Milestones)
*   **Giai đoạn 1: Thiết kế Bản vẽ Kỹ thuật (Technical Blueprint)**
    *   Xác định cấu trúc rút gọn chuẩn cho mỗi `SKILL.md`.
    *   Xác định cách tích hợp tham chiếu liên kết đến `AI_RULES.md`.
*   **Giai đoạn 2: Triển khai Cấu trúc lại (Refactoring Execution)**
    *   Tiến hành cập nhật 26 tệp `SKILL.md` trong thư mục `skills/` theo chuẩn mới.
    *   Đồng bộ hóa mã nguồn sang `.agents/skills/` sử dụng công cụ cài đặt có sẵn.
*   **Giai đoạn 3: Kiểm duyệt chất lượng (Quality Gates & Verification)**
    *   Chạy kiểm tra sức khỏe của workspace bằng `doctor.ps1`.
    *   Kiểm tra khả năng phân tích cú pháp của các kỹ năng sau khi rút gọn.

## 4. Rủi ro & Giải pháp giảm thiểu (Risks & Mitigations)
*   **Rủi ro 1: Rút gọn quá mức làm giảm chất lượng suy luận của mô hình (Context Drift)**
    *   *Giảm thiểu*: Giữ lại đầy đủ các từ khóa hành vi mạnh như `MUST`, `SHALL`, `REQUIRED`, `STOP` và các kiểm tra điều kiện thất bại trong phần hướng dẫn của từng kỹ năng.
*   **Rủi ro 2: Sai lệch dữ liệu `.session.json` phá vỡ giao diện Visualizer**
    *   *Giảm thiểu*: Giữ nguyên lược đồ JSON và các mốc checkpoint không đổi.

## 5. Kế hoạch kiểm duyệt chất lượng (Verification Plan)
*   [ ] Chạy `powershell .\update.ps1 -Force` thành công.
*   [ ] Chạy `powershell .\doctor.ps1` báo cáo thành công với 0 lỗi.
*   [ ] Ước tính và so sánh tổng dung lượng thư mục `skills/` trước và sau khi refactor.
