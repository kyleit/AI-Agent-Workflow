<!-- File path: docs/plans/FEAT-002_installer_scripts_plan.md -->

# Kế hoạch triển khai - Sinh các bộ công cụ cài đặt (Installer) và quản lý gói nâng cấp

Chào Ba, đây là bản kế hoạch lưu trong dự án để triển khai các script cài đặt và quản lý phiên bản (`install.sh`, `install.ps1`, `update.sh`, `uninstall.sh`, `MANIFEST.json`) cho repository AI Skill Framework.

## 1. Mục tiêu
Repository phải hoạt động như một gói cài đặt độc lập (Package) thay vì chỉ là các file tài liệu đơn thuần. Các script sẽ giúp triển khai, đồng bộ nâng cấp hoặc gỡ cài đặt các runtime files (`AI_RULES.md`, `MANIFEST.json`, `skills/`, `templates/`) vào thư mục `.agents/` của bất kỳ dự án Git nào.

## 2. Các tệp tin cần sinh và sửa đổi
- **MANIFEST.json**: Mở rộng metadata làm Single Source of Truth cho các script.
- **install.sh**: Bộ cài đặt cho Linux/macOS.
- **install.ps1**: Bộ cài đặt cho Windows PowerShell và PowerShell Core.
- **update.sh**: Script cập nhật/đồng bộ các thay đổi của Skill.
- **uninstall.sh**: Script gỡ cài đặt an toàn (chỉ xóa file của framework).
- **AI_RULES.md**: Tạo ra bằng cách sao chép từ `AGENTS.md`.
- **templates/.gitkeep** và **examples/.gitkeep**: Tạo thư mục rỗng để đồng bộ cấu trúc.

## 3. Kế hoạch kiểm tra
- Chạy thử nghiệm lệnh cài đặt `.\install.ps1` ngay trên một thư mục thử nghiệm.
- Kiểm tra tính idempotent và xử lý lỗi của các script.
