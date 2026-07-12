# Brainstorming — FEAT-113: Resident Runtime Manager

## 1. Executive Summary
Đề xuất thiết kế Resident Runtime Manager - lớp điều hành hệ thống bên trên Resident Orchestrator đóng vai trò là một người quản trị và tự chữa lành (Self-Healing Supervisor) cho toàn bộ vòng đời của runtime.

## 2. Background & Current Limitations

### Background
FEAT-111 và FEAT-112 đã triển khai thành công Resident Orchestrator chạy ngầm lâu dài. Tuy nhiên, kiến trúc hiện hành vẫn thiếu một thực thể quản trị và bảo vệ độc lập cho chính bản thân tiến trình orchestrator.

### Current Limitations
- **Không có Watchdog**: Nếu Resident Orchestrator bị treo (deadlock) hoặc sập, không có cơ chế bên ngoài nào để phát hiện và khởi động lại.
- **Không có bộ quản trị tự chữa lành (Self-Healing)**: Lỗi tiến trình ngầm không được tự động cô lập và khôi phục trạng thái.
- **Không có khả năng co giãn thích ứng (Adaptive scaling)**: Hệ thống chưa thể điều tiết mức độ concurrency dựa trên tài nguyên CPU/RAM thực tế.
- **Thiếu giám sát sức khoẻ**: Chưa có bảng điều khiển tình trạng hoạt động (health status) thời gian thực của daemon.
- **Không có trình quản lý nâng cấp động (Upgrade coordinator)**: Việc nâng cấp runtime yêu cầu can thiệp thủ công từ phía người dùng thay vì hot-reload an toàn.
- **Thiếu bộ thống kê vận hành (Telemetry)**: Thiếu dữ liệu đo lường tập trung về hiệu suất sử dụng API, token và độ trễ phản hồi.

## 3. Business Value
- Nâng cao tính bền bỉ của hệ thống AIWF lên cấp độ Enterprise.
- Tự động hóa hoàn toàn vận hành chéo nền tảng mà không cần người dùng can thiệp kỹ thuật.
- Tiết kiệm chi phí vận hành đám mây thông qua quản lý tài nguyên hiệu quả.

## 4. Functional Requirements

### Mandatory (Bắt buộc)
- Watchdog Service giám sát sự tồn tại của Resident Orchestrator qua heartbeat.
- Tự động restart Resident Orchestrator khi phát hiện crash.
- Thu hồi triệt để zombie/orphaned processes của Subagents.

### Recommended (Khuyên dùng)
- Tự động điều chỉnh `concurrency_limit` thích ứng với RAM/CPU hiện thời.
- Hot-reload an toàn khi cập nhật phiên bản runtime mới.

### Future (Tương lai)
- Tích hợp dịch vụ chạy trong Container / Kubernetes.
- Hỗ trợ phân tán công việc (distributed runtimes).

## 5. Non-functional Requirements
- **Reliability (Độ tin cậy)**: Hoạt động giám sát không được tự tạo lỗi hoặc làm ảnh hưởng tới hiệu năng của không gian làm việc.
- **Observability (Độ trực quan)**: Xuất bản dữ liệu JSON telemetry định kỳ để Visualizer Webview có thể vẽ biểu đồ tài nguyên thời gian thực.
- **Security (An ninh)**: Watchdog chạy nội bộ và không mở thêm cổng dịch vụ ngoài.

## 6. Runtime Components
- **Watchdog Engine**: Tiến trình giám sát siêu mỏng (super-lightweight supervisor process).
- **Resource Governor**: Bộ thu thập tài nguyên hệ thống qua `psutil`.
- **Upgrade Coordinator**: Quản lý hot-swap mã nguồn của daemon.

## 7. Risks & Mitigations
- **Infinite restart loops (Vòng lặp khởi động vô hạn)**: Xảy ra nếu lỗi xuất hiện ngay khi start daemon.
  - *Giảm thiểu*: Thiết lập cơ chế Backoff (thử lại tối đa 3 lần, giãn cách thời gian tăng dần).
- **Split-brain scenarios (Kịch bản phân liệt)**: Nhiều watchdog cùng chạy tranh giành điều khiển.
  - *Giảm thiểu*: Khoá tệp tin duy nhất tại `.agents/state/manager.lock`.

## 8. Migration Strategy
Nâng cấp tương thích ngược hoàn toàn với cấu trúc trạng thái của FEAT-112.

## 9. Success Criteria & Readiness Score
- **Readiness Score**: 98/100
- **Success Criteria**: Watchdog khôi phục Resident Orchestrator < 2 giây sau khi cưỡng chế kill tiến trình.

```text
Recommendation:
READY FOR PLANNING
```
