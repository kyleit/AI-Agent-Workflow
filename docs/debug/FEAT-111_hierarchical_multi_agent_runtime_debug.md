# Debug Report — FEAT-111 Hierarchical Multi-Agent Runtime

## 1. Xử lý xung đột nhập gói (Import conflict on hyphen folders)
- *Triệu chứng*: Khi viết unit test import `skills.workflow-runtime.scripts.hierarchical_runtime` xảy ra lỗi cú pháp Python do thư mục `workflow-runtime` chứa dấu gạch ngang `-`.
- *Khắc phục*: Sử dụng `sys.path.insert` động trong file test để chèn trực tiếp đường dẫn thư mục `scripts/` vào đầu danh sách tìm kiếm package của Python, giúp thực hiện `from hierarchical_runtime import ...` trực tiếp và sạch sẽ.

## 2. Windows Atomic-write file locking contention
- *Triệu chứng*: `PermissionError: [WinError 5] Access is denied` phát sinh khi chạy song song ghi dữ liệu trạng thái trên Windows.
- *Khắc phục*: Tích hợp vòng lặp thử lại tối đa 10 lần với khoảng nghỉ ngẫu nhiên 50ms giữa mỗi lần ghi đè nguyên tử trong `hierarchical_runtime.py`, giải quyết triệt để tranh chấp khóa file từ các IDE/OS file watchers.
