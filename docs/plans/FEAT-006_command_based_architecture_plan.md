<!-- File path: docs/plans/FEAT-006_command_based_architecture_plan.md -->

# Kế hoạch triển khai - Thiết kế siêu dữ liệu hướng câu lệnh (Command-Based Architecture)

Chào Ba, đây là bản kế hoạch lưu trong dự án để tái cấu trúc hệ thống siêu dữ liệu (metadata) của các Skill nhằm hỗ trợ việc tương tác dạng câu lệnh `/command` ngắn gọn.

## 1. Mục tiêu
- **Giữ nguyên khả năng tương thích ngược**: Không thay đổi tên thư mục hay định danh Skill (`name`).
- **Giới thiệu hệ thống lệnh rút gọn**: Định nghĩa thuộc tính `command`, `aliases`, `category`, `tags` trực tiếp trong frontmatter của mỗi `SKILL.md` và đồng bộ vào `MANIFEST.json`.
- **Cập nhật tài liệu**: Chuyển toàn bộ tài liệu hướng dẫn và ví dụ sử dụng sang định dạng câu lệnh ngắn (ví dụ: `/workflow`, `/plan`, `/blueprint`, `/implement`).

## 2. Các thay đổi chi tiết
- **skills/**: Sửa đổi frontmatter của tất cả 22 Skill.
- **MANIFEST.json**: Chuyển đổi cấu trúc `skills` thành danh sách các đối tượng chi tiết và bổ sung phân nhóm `categories`.
- **Tài liệu (`README.md`, `SKILLS.md`, `INSTALL.md`, `USAGE.md`)**: Cập nhật toàn bộ các ví dụ và hướng dẫn sử dụng.
- **CHANGELOG.md**: Bumps phiên bản lên 2.6.0.

## 3. Kế hoạch kiểm tra
- Chạy `aiwf doctor` xác thực tính hợp lệ của framework.
- Đảm bảo cú pháp JSON của `MANIFEST.json` chính xác.
