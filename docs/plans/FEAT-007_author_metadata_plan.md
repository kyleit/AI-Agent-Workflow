<!-- File path: docs/plans/FEAT-007_author_metadata_plan.md -->

# Kế hoạch triển khai - Tích hợp siêu dữ liệu tác giả (Author Metadata) vào hệ thống Skill

Chào Ba, đây là bản kế hoạch lưu trong dự án để chuẩn hóa và tích hợp thông tin tác giả vào các Skill, Manifest và README.md.

## 1. Mục tiêu
- **Chuẩn hóa thông tin tác giả**: Cập nhật siêu dữ liệu tác giả Kyle Dang (`kyleit@klexpress.net`) đồng bộ ở 22 Skill.
- **Manifest là chân lý gốc**: Cấu hình thông tin tác giả ở `MANIFEST.json` và liên kết thông tin tác giả ở `README.md`.
- **Ràng buộc quy tắc**: Ngăn chặn Agent tự ý thêm chữ ký vào mã nguồn hay tài liệu sinh ra.

## 2. Các thay đổi chi tiết
- **skills/**: Cập nhật frontmatter của tất cả 22 Skill.
- **MANIFEST.json**: Thêm khóa `"author"` và bump version lên `2.7.0`.
- **README.md**: Thêm chương giới thiệu Tác giả.
- **AI_RULES.md**: Thêm quy định cấm chữ ký tự động vào Section 7 (Documentation Policy).
- **CHANGELOG.md**: Bumps phiên bản lên 2.7.0.

## 3. Kế hoạch kiểm tra
- Chạy `aiwf doctor` kiểm tra tính tương thích.
- Đảm bảo cú pháp JSON của `MANIFEST.json` chính xác.
