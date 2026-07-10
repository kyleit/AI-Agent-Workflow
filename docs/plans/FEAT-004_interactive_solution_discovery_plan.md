<!-- File path: docs/plans/FEAT-004_interactive_solution_discovery_plan.md -->

# Kế hoạch triển khai - Nâng cấp idea-to-planning-prompt thành Interactive Solution Discovery

Chào Ba, đây là bản kế hoạch lưu trong dự án để nâng cấp Skill `idea-to-planning-prompt` thành công cụ khám phá giải pháp kỹ thuật tương tác (`Interactive Solution Discovery`).

## 1. Mục tiêu
Thay vì chỉ sinh tài liệu prompt đơn thuần, Skill sẽ đóng vai trò như một **Solution Architect** thực hiện:
- Phân tích ngữ cảnh hệ thống hiện tại qua Project Memory và RAG.
- Đề xuất **2-3 giải pháp kiến trúc khác biệt** rõ rệt về thiết kế.
- So sánh ưu nhược điểm, độ phức tạp, hiệu năng và bảo trì dưới dạng bảng so sánh.
- Đưa ra giải pháp đề xuất kèm theo lập luận kiến trúc rõ ràng.
- Tạm dừng (WAIT FOR USER) để Ba chọn phương án trước khi tạo file yêu cầu master.

## 2. Các thay đổi chi tiết
- **skills/idea-to-planning-prompt/SKILL.md**: Cải tiến luồng hoạt động thành 7 pha, tích hợp các bước so sánh giải pháp và chốt phương án trước khi sinh file.
- **MANIFEST.json** & **SKILLS.md**: Cập nhật mô tả và hướng dẫn sử dụng.
- **CHANGELOG.md**: Nhật ký phát hành phiên bản 1.5.0.

## 3. Kế hoạch kiểm tra
- Kiểm tra tính nhất quán trong mô tả các pha thiết kế giải pháp tương tác.
- Xác thực cú pháp tệp MANIFEST.json.
