<!-- File path: docs/plans/FEAT-001_workflow_adr_refactoring_plan.md -->

# Kế hoạch triển khai - Tái cấu trúc Workflow sang định dạng FEAT-001 và tích hợp ADR

Chào Ba, đây là bản kế hoạch lưu trong dự án để thực hiện tái cấu trúc toàn bộ AI Engineering Workflow sang định dạng `FEAT-001` thống nhất và bổ sung hỗ trợ Architecture Decision Record (ADR).

## 1. Tổng quan
Thay đổi cấu trúc lưu trữ tài liệu sang mô hình tối giản: `brainstorming/`, `plans/`, `designs/`, `adr/`. Loại bỏ các thư mục phụ khác. Đồng bộ hóa toàn bộ 13 Skill và tạo mới Skill `create-adr` để ghi nhận các quyết định kiến trúc quan trọng một cách độc lập.

## 2. Thay đổi chi tiết
* **Định dạng Feature ID**: Sử dụng mã dạng `FEAT-XXX` (ví dụ: `FEAT-001`).
* **Skill `create-adr`**: Sinh file `docs/adr/ADR-XXX_title.md` với mã ADR độc lập quét từ `docs/adr/`.
* **Skill `plan-to-blueprint`**: Tích hợp phần đánh giá ADR bắt buộc nhưng không tự sinh file.
* **Skill `blueprint-to-implementation`**: Kiểm tra chéo sự hiện diện của ADR nếu bản thiết kế yêu cầu.
* **Skill `implementation-to-release`**: Cập nhật trực tiếp `CHANGELOG.md` thay vì viết file release riêng.
* **Các Skill quản lý Memory & RAG**: Giới hạn phạm vi quét tài liệu vào 4 thư mục cốt lõi trên.
* **Repository Metadata & AGENTS.md**: Cập nhật tài liệu hướng dẫn và tệp cấu hình manifest đồng bộ.

## 3. Kế hoạch dọn dẹp
- Xóa các thư mục `docs/releases/` và `docs/archive/` không còn sử dụng.

## 4. Kế hoạch kiểm tra
- Đọc lại thủ công tất cả các tệp tin để đảm bảo tính nhất quán.
- Chạy lệnh xác thực JSON đối với `MANIFEST.json`.
