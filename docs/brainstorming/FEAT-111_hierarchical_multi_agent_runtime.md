# Requirement Discovery — FEAT-111 Hierarchical Multi-Agent Runtime

## 1. Problem Statement
Hiện tại, các luồng thực thi trong framework phần lớn mang tính tuần tự và yêu cầu tương tác cao, hạn chế khả năng chạy nền (daemon mode) và quản lý song song các tác nhân chuyên biệt (Subagents). Để xây dựng một hệ thống phát triển phần mềm tự động ổn định và hiệu quả, chúng ta cần triển khai mô hình phân cấp Multi-Agent Runtime.

## 2. Requirements & Technical Specifications
* **Hierarchical Agent Runtime**: 
  - Một Orchestrator làm tác nhân chính điều phối.
  - Các Subagents đóng vai trò Worker chạy độc lập.
* **Worker Process Isolation**: Mỗi Subagent chạy trong một tiến trình cách ly hoàn toàn, giao tiếp qua Event Bus/IPC.
* **Parallel Scheduler**: Lập lịch thực thi đồng thời các tác vụ độc lập trong đồ thị tác vụ.
* **Capability-based Permission**: Giới hạn quyền hạn của Subagents (không có quyền commit/push/release).
* **Robustness & Recovery**:
  - Heartbeat Manager phát hiện Subagent stale.
  - Lock Manager quản lý truy cập đồng thời vào file/resources.
  - Checkpoint & Recovery lưu trữ trạng thái tại `.agents/state/checkpoints/` để phục hồi khi lỗi.
* **Live Visualizer Integration**: Tích hợp hiển thị trạng thái động của các tác nhân, nhóm song song, locks và heartbeats lên giao diện visualizer.
