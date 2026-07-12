# Execution Plan — FEAT-113: Resident Runtime Manager

## 1. Executive Summary
Bản kế hoạch chi tiết triển khai lớp quản trị tự chữa lành Resident Runtime Manager (Watchdog/Supervisor) bên trên Resident Orchestrator.

## 2. Objectives
- Triển khai tiến trình Watchdog Engine để bảo vệ và tự động phục hồi Orchestrator Daemon.
- Thống kê dữ liệu telemetry về RAM/CPU sử dụng động.
- Quản lý co giãn thích ứng (adaptive concurrency) và hot-reload an toàn.

## 3. Business Value
- Tăng cường khả năng tự chữa lành (Self-Healing) chéo nền tảng cho runtime.
- Hỗ trợ giám sát trực quan tài nguyên nâng cao chéo phiên chạy.

## 4. Scope
- Thiết kế Watchdog Engine.
- Nâng cấp Resource Governor giám sát CPU/RAM qua `psutil`.
- Tích hợp telemetry xuất bản dữ liệu về Visualizer.

## 5. Runtime Manager Architecture
Watchdog là một tiến trình siêu nhẹ chạy độc lập, định kỳ giao tiếp với Resident Orchestrator để kiểm tra sức khỏe và khởi động lại nếu sập.

## 6. Runtime Lifecycle
Tự động kích hoạt khi daemon chạy và tự tắt khi daemon tắt an toàn.

## 7. Watchdog Strategy
Quét heartbeat định kỳ mỗi 5 giây. Nếu quá 15 giây không phản hồi, watchdog cưỡng chế tắt tiến trình daemon cũ và khởi tạo tiến trình mới.

## 8. Health Monitoring
Giám sát tình trạng sống của cổng WebSocket, tệp tin trạng thái daemon, và Named Pipes.

## 9. Auto-Restart Policy
Cho phép tự động restart tối đa 3 lần liên tục. Nếu lỗi vẫn tiếp tục, chuyển trạng thái sang `blocked` và cảnh báo người dùng.

## 10. Crash Recovery
Nạp checkpoint gần nhất từ SQLite để khôi phục trạng thái DAG và các Subagents đang bận.

## 11. Worker Supervision
Kiểm soát PID của các Subagents, tự động gửi tín hiệu thu hồi (zombie process cleanup) khi tiến trình cha gặp sự cố.

## 12. Resource Monitoring
Đo lượng RAM/CPU tiêu thụ thực tế để cảnh báo nếu vượt ngưỡng 90%.

## 13. Adaptive Concurrency
Nếu CPU sử dụng > 80%, tự động giảm `concurrency_limit` từ 6 xuống 3 để bảo toàn tài nguyên máy chủ phát triển.

## 14. Runtime Upgrade Strategy
Khi phát hiện mã nguồn mới, quản lý tắt an toàn các ephemeral workers, hoán đổi mã nguồn (hot-swap) và khởi động lại daemon.

## 15. Plugin Lifecycle Management
Cấp phát, đăng ký và giải phóng các plugins mở rộng động.

## 16. Metrics & Telemetry
Lưu trữ thông số số lượng token tiêu thụ, chi phí API, và thời gian chạy trung bình chéo phiên chạy.

## 17. Diagnostics
Chạy lệnh chẩn đoán tự động các cổng giao tiếp và quyền truy cập thư mục.

## 18. Alerting
Đẩy cảnh báo trực tiếp về Visualizer Webview khi phát hiện rò rỉ bộ nhớ hoặc xung đột khóa file kéo dài.

## 19. Multi-client Coordination
Đồng bộ hóa kênh Named Pipes để điều tiết yêu cầu từ nhiều cửa sổ IDE đồng thời.

## 20. Security Model
Bảo vệ bằng session token sinh ngẫu nhiên chéo Named Pipes cục bộ.

## 21. Scalability
Đảm bảo quản lý hiệu quả tối đa 12 Subagents đồng thời trên máy cục bộ.

## 22. Migration Strategy
Nâng cấp liền mạch từ bản v6.11.0 lên v6.12.0.

## 23. Risks & Mitigations
Tránh lặp khởi động vô hạn bằng cách sử dụng bộ đếm cooldown.

## 24. Sprint Breakdown
- **Sprint 1**: Triển khai Watchdog Engine & Heartbeat Monitor.
- **Sprint 2**: Triển khai Adaptive Concurrency & Resource Governor.
- **Sprint 3**: Tích hợp Visualizer dashboard metrics.

## 25. Work Packages
- WP1: Watchdog daemon process.
- WP2: Resource monitor integration.
- WP3: Telemetry socket events.

## 26. Acceptance Criteria
- Tự phục hồi Orchestrator Daemon thành công: **PASS**.
- Cắt giảm concurrency động khi quá tải CPU: **PASS**.

## 27. Success Metrics
- CPU overhead của watchdog < 1%.
