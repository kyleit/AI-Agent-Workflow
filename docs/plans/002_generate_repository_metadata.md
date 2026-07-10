<!-- File path: docs/plans/002_generate_repository_metadata.md -->

# Kế hoạch triển khai - Sinh siêu dữ liệu (Metadata) và tài liệu cài đặt cho Repository

Chào Ba, đây là bản kế hoạch lưu trong dự án để thực hiện sinh các tệp tin cấu hình và tài liệu ở cấp độ repository (README.md, SKILLS.md, INSTALL.md, MANIFEST.json, CHANGELOG.md, LICENSE).

## Thay đổi đề xuất
Tạo mới các tệp tin tại thư mục gốc của repository:
1. **README.md**: Tổng quan dự án, tính năng, cấu trúc thư mục, luồng làm việc, phiên bản, hướng dẫn Quick Start và cách thức đóng góp.
2. **SKILLS.md**: Index toàn bộ 13 Skill của dự án, mỗi Skill có mục đích, input, output, ranh giới, trạng thái và dependencies.
3. **INSTALL.md**: Hướng dẫn cài đặt (Copy, Symlink, Submodule), nâng cấp, cấu trúc đề xuất trong dự án đích (`.agents/skills/`).
4. **MANIFEST.json**: Metadata máy đọc chứa thông tin các skill, phiên bản tối thiểu hỗ trợ, thứ tự quy trình, v.v.
5. **CHANGELOG.md**: Nhật ký thay đổi định dạng Keep a Changelog.
6. **LICENSE**: Giấy phép MIT License.

## Ràng buộc
- Tuyệt đối KHÔNG chỉnh sửa bất kỳ Skill nào hiện có trong thư mục `skills/`.
- Không tạo mã nguồn thực thi hay logic hệ thống cụ thể.

## Kế hoạch kiểm tra
- Đọc lại thủ công tất cả tài liệu được sinh ra để đảm bảo không bị sai sót thông tin.
- Kiểm tra tính hợp lệ JSON của tệp `MANIFEST.json`.
