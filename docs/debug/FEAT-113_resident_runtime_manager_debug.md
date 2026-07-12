# Debug Report — FEAT-113 Resident Runtime Manager

Báo cáo phân tích chẩn đoán lỗi tiến trình Watchdog Supervisor và kiểm soát điều phối song song.

## 1. Infinite Restart Loop Prevention
- *Triệu chứng*: Khi Resident Orchestrator sập liên tục do lỗi nạp thư viện hoặc thiếu quyền, watchdog tự khởi động lại vô hạn dẫn đến nghẽn CPU.
- *Khắc phục*: Tích hợp bộ đếm giới hạn (tối đa 3 lần khởi động lại liên tiếp). Nếu tiếp tục lỗi, đánh dấu tình trạng sống là `blocked` để chờ người dùng phục hồi hoặc sửa lỗi cấu hình.

## 2. Resource governor precision
- *Triệu chứng*: Việc đo đạc tài nguyên RAM/CPU có độ trễ lớn và thỉnh thoảng ném lỗi truy cập quyền tiến trình con (Access Denied).
- *Khắc phục*: Bọc các thao tác gọi `psutil` trong khối ngoại lệ an toàn và thiết lập giá trị mặc định fallback khi không có đủ thẩm quyền giám sát tiến trình con của hệ điều hành.
