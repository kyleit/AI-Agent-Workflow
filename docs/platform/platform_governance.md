# AIWF Platform Governance Policy

Chính sách bảo vệ và quản lý vận hành nền tảng v1.

## 1. Nguyên tắc đóng băng API v1
- Không cho phép chỉnh sửa phá vỡ chữ ký hàm hiện tại của SDK v1.
- Không tự ý thêm bớt các subcommands CLI làm thay đổi hành vi mặc định của IDE.

## 2. Nguyên tắc an toàn thực thi
- Watchdog Supervisor có thẩm quyền cao nhất để cưỡng chế dừng các tiến trình con Subagents vi phạm phạm vi khoá tài nguyên ghi.
