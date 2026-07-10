<!-- File path: docs/plans/FEAT-003_global_cli_bootstrap_plan.md -->

# Kế hoạch triển khai - Bộ cài đặt toàn cục và CLI aiwf đa nền tảng

Chào Ba, đây là bản kế hoạch lưu trong dự án để triển khai hệ thống CLI toàn cục `aiwf` và bộ cài đặt một lần (Bootstrap) chạy trên Windows, macOS và Linux.

## 1. Mục tiêu
Người dùng có thể cài đặt framework toàn cục chỉ bằng một lệnh duy nhất:
- Unix: `./bootstrap.sh`
- Windows: `.\bootstrap.ps1` hoặc `bootstrap.bat`

Sau khi cài đặt, người dùng có thể mở bất kỳ terminal nào trong bất kỳ dự án nào và chạy:
- `aiwf install`
- `aiwf update`
- `aiwf uninstall`
- `aiwf doctor`
- `aiwf version`

## 2. Các tệp tin cần tạo mới
- **bootstrap.sh**: Trình cài đặt toàn cục cho Unix/Shell.
- **bootstrap.ps1**: Trình cài đặt toàn cục cho Windows/PowerShell.
- **bootstrap.bat**: File batch CMD chuyển tiếp cuộc gọi sang PowerShell bootstrap.
- **doctor.sh** & **doctor.ps1**: Chẩn đoán tính toàn vẹn của cài đặt.
- **version.sh** & **version.ps1**: Báo cáo chi tiết phiên bản và đường dẫn của CLI.
- **update.ps1** & **uninstall.ps1**: Tương thích PowerShell trên Windows.

## 3. Kế hoạch kiểm tra
- Chạy thử `.\bootstrap.ps1` để đăng ký PATH.
- Kiểm tra chéo hoạt động của `aiwf` từ thư mục tạm thời ngoài dự án.
