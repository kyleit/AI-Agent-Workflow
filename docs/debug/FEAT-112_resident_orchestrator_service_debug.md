# Debug Report — FEAT-112 Resident Orchestrator Service

Báo cáo phân tích sửa lỗi và chẩn đoán kiến trúc của tiến trình Resident Daemon Service.

## 1. Kiểm soát Windows File Access Contention
- *Triệu chứng*: Khi nhiều subagents và tiến trình daemon chạy nền cùng cập nhật dữ liệu trạng thái thông qua lớp `state_store.py`, hệ điều hành Windows ném lỗi `PermissionError [WinError 5] Access is denied` do file lock tranh chấp.
- *Khắc phục*: Triển khai vòng lặp thử lại ghi nguyên tử (10 lần, delay 50ms) trong cả phương thức `set` và `flush` của lớp `state_store.py`, bảo đảm trạng thái ghi nguyên tử hoạt động trơn tru dưới môi trường Windows.

## 2. Dynamic Spawner Isolation
- *Triệu chứng*: Ephemeral subagents khi spawn qua `subprocess.Popen` thỉnh thoảng bị kẹt ngầm (zombie processes) nếu daemon bị cưỡng bức tắt.
- *Khắc phục*: Heartbeat Manager tự động rà quét và gửi tín hiệu giải phóng tiến trình định kỳ mỗi 30 giây cho tất cả các tiến trình con có PID được đăng ký.
