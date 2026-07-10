<!-- File path: docs/plans/003_workflow_refactoring_plan.md -->

# Kế hoạch triển khai - Tái cấu trúc Workflow theo định dạng hướng tính năng (Feature-Based)

Chào Ba, đây là bản kế hoạch lưu trong dự án để thực hiện tái cấu trúc cấu trúc thư mục tài liệu và các Skill thành mô hình hướng tính năng (Feature-Based).

## Phân tích hiện trạng
Hiện tại các tệp tin prompt, kế hoạch (plan) và bản thiết kế (blueprint) đang sử dụng hệ thống số thứ tự độc lập hoặc không nhất quán. Điều này gây khó khăn cho việc liên kết và theo dõi tính năng xuyên suốt các pha của SDLC.

## Giải pháp đề xuất
1. **Thay đổi cấu trúc tài liệu**:
   - Chuyển `plans/prompts/` hoặc `docs/prompts/` thành `docs/brainstorming/`.
   - Lưu trữ bản thiết kế chi tiết (blueprint) tại `docs/designs/` thay vì `docs/plans/designs/`.
   - Lưu trữ báo cáo phát hành tại `docs/releases/`.
   - Lưu trữ biên bản quyết định kiến trúc tại `docs/adr/`.
2. **Quy tắc Feature ID**:
   - Sử dụng một mã số Feature ID duy nhất (ví dụ: `001`, `002`...) xuyên suốt vòng đời.
   - Feature ID được xác định duy nhất bằng cách quét thư mục `docs/brainstorming/`.
3. **Cập nhật các AI Skill**:
   - `software-development-workflow`: Theo dõi trạng thái thông qua Feature ID và đề xuất Skill tiếp theo dựa trên sự hiện diện chéo của các tệp tin cùng ID.
   - `idea-to-planning-prompt`: Ghi đầu ra vào `docs/brainstorming/` dạng `<feature_id>_<feature_name>.md`.
   - `planning-prompt-to-plan`: Đọc từ `docs/brainstorming/` và ghi vào `docs/plans/` dưới dạng `<feature_id>_<feature_name>_plan.md`.
   - `plan-to-blueprint`: Ghi vào `docs/designs/` dưới dạng `<feature_id>_<feature_name>_blueprint.md`.
   - `implementation-to-release`: Ghi vào `docs/releases/` dưới dạng `<feature_id>_<feature_name>_release.md`.
4. **Tính khả theo (Traceability)**:
   - Tích hợp bảng thông tin Traceability và liên kết tương đối giữa các tệp tin trong cùng một tính năng.

## Kế hoạch kiểm tra
- Đọc lại thủ công tất cả các tệp tin Skill đã cập nhật để đảm bảo tính đúng đắn của logic Feature ID.
- Kiểm tra tính tương thích và liên kết tương đối giữa các tài liệu.
