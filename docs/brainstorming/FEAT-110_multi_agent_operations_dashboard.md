# Brainstorming — FEAT-110 Multi-Agent Operations Dashboard and Recovery Center

## 1. Problem Statement
Trình mô phỏng Orchestrator V2 quản lý nhiều tác nhân chạy song song và phụ thuộc nhau dưới mô hình đồ thị DAG. Khi xảy ra xung đột khóa tài nguyên (locks), mất tín hiệu (heartbeat timeout), lỗi kiểm thử cục bộ hoặc chuyển giao (handoffs) bất thành, người dùng cần một giao diện trực quan thời gian thực để:
- Xem tiến độ toàn bộ Objective và danh sách Agent tham gia.
- Theo dõi các tác vụ bị chặn (blocked), thất bại hoặc đang hồi phục.
- Kích hoạt phục hồi thủ công (resume run, retry task, release lock, restore checkpoint).

## 2. Design Thinking
- **Trực quan hóa đồ thị**: Sử dụng dạng sơ đồ/danh sách có thụt đầu dòng (hoặc biểu đồ cây phụ thuộc) phân biệt rõ ràng trạng thái ready, running, completed, failed, blocked, cancelled.
- **Trung tâm khôi phục**: Cho phép bấm nút phục hồi, thực hiện gọi lệnh CLI `workflow_runtime.py orchestrator action` để ghi đè dữ liệu trạng thái một cách an toàn.
- **Bảo vệ toàn vẹn**: Không cho phép báo cáo hoàn thành giả khi đồ thị vẫn còn chứa tác vụ bắt buộc chưa hoàn thành.

## 3. UI Aesthetics
- Thiết kế tích hợp hoàn hảo vào hệ thống theme nền tối (dark mode) của Visualizer Companion:
  - Nền kính mờ (`backdrop-filter: blur`).
  - Viền neon tương ứng với trạng thái (Green cho passed, Red cho failed/integrity error, Amber cho running/ready).
  - Nút bấm tinh gọn, có bo góc và đổ bóng nhẹ.
