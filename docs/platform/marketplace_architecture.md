# AIWF Skill Marketplace Architecture

Thiết kế kiến trúc hệ thống lưu trữ, phân phối và quản lý phiên bản của chợ ứng dụng Skills.

## 1. Cấu trúc đóng gói (Package Format)
Mỗi package của Skill phải chứa:
- Tệp cấu hình `manifest.json`.
- Thư mục mã nguồn `scripts/`.
- Thư mục kiểm thử `tests/`.

## 2. Mô hình phân phối và tin cậy (Trust Model)
- Ký chữ ký số bằng mã hash SHA-256 để xác thực tính toàn vẹn của mã nguồn khi tải về.
