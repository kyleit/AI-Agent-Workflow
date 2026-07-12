# AIWF Operator Manual

Sách hướng dẫn vận hành hệ thống dành cho quản trị viên và kỹ sư hệ thống.

## 1. Quản lý trạng thái Daemon
- Khởi động daemon thủ công (Chế độ debug): `python skills/workflow-runtime/scripts/hierarchical_runtime.py --daemon`
- Kiểm tra nhịp tim và trạng thái sống: Đọc nội dung tệp tin [.agents/state/daemon.json](file:///.agents/state/daemon.json).

## 2. Khắc phục sự cố nhanh
Khi xảy ra treo cổng Named Pipes hoặc WebSocket:
1. Kill tiến trình cũ dựa trên PID ghi nhận ở `daemon.json`.
2. Chạy `aiwf init` để watchdog tự động tái sinh tiến trình mới.
