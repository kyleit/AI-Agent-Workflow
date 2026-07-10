<!-- File path: docs/plans/001_refactor_idea_to_planning_prompt.md -->

# Kế hoạch triển khai - Tái cấu trúc idea-to-planning-prompt thành Interactive Requirement Discovery Skill

Chào Ba, đây là kế hoạch chi tiết lưu trữ trong dự án để tái cấu trúc skill `idea-to-planning-prompt` thành quy trình khám phá yêu cầu tương tác.

## Tổng quan
Tái cấu trúc skill chuyển đổi ý tưởng ban đầu thành file prompt lập kế hoạch bằng cách áp dụng quy trình khám phá yêu cầu gồm 10 phase tương tác, đánh giá chất lượng yêu cầu bằng điểm số sẵn sàng (Readiness Score).

## Thay đổi đề xuất
Sửa đổi tệp tin `skills/idea-to-planning-prompt/SKILL.md` để hướng dẫn AI thực hiện:
- Phase 1 – Requirement Discovery: Xác định vấn đề, đối tượng sử dụng, kết quả mong đợi.
- Phase 2 – Requirement Analysis: Phân tích chi tiết chức năng, phi chức năng, luật nghiệp vụ, ràng buộc kỹ thuật, UX.
- Phase 3 – Project Context: Đọc Project Memory trước khi đặt câu hỏi.
- Phase 4 – Impact Analysis: Phân tích vùng ảnh hưởng của thay đổi.
- Phase 5 – Gap Analysis: Đánh giá độ thiếu hụt thông tin.
- Phase 6 – Risk Identification: Nhận diện rủi ro tiềm ẩn.
- Phase 7 – Requirement Readiness Score: Đánh giá điểm sẵn sàng (ngưỡng 85).
- Phase 8 – Clarification Questions: Gom nhóm câu hỏi, dừng chờ Ba trả lời nếu < 85.
- Phase 9 – Requirement Validation: Xác thực lần cuối trước khi sinh output.
- Phase 10 – Generate Planning Prompt: Sinh file `plans/prompts/<feature>-planning-prompt.md`.

## Kế hoạch kiểm tra
- Kiểm tra thủ công nội dung tệp tin `skills/idea-to-planning-prompt/SKILL.md` sau khi chỉnh sửa.
