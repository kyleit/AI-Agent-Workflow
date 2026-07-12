# Execution Plan — FEAT-112: AIWF Resident Orchestrator Service & Dynamic Subagent Runtime

## 1. Executive Summary
Bản kế hoạch chi tiết cho việc chuyển đổi AIWF từ mô hình chạy phiên sang dịch vụ nền trú đóng dài hạn Resident Orchestrator Service (daemon) với khả năng cấp phát Subagents động.

## 2. Objectives
- Thiết lập dịch vụ nền Resident Orchestrator chạy ngầm lâu dài.
- Tự động hóa việc quản lý co giãn và thu hồi Subagents nhàn rỗi.
- Đảm bảo tiếp nhận chỉ thị phi đồng bộ thông qua hộp thư Command Inbox.

## 3. Scope
- Triển khai Daemon Engine phục vụ chạy ngầm trên Windows/Linux.
- Phát triển thành phần Dynamic Team Planner phân tích yêu cầu động.
- Nâng cấp Visualizer hiển thị trạng thái daemon.

## 4. Business Value
- Tối ưu hóa việc sử dụng tài nguyên CPU/RAM.
- Cải thiện năng lực tương tác và điều khiển của người dùng trong thời gian thực.
- Đặt nền móng cho khả năng tích hợp Cloud/CI/CD trong tương lai.

## 5. Runtime Architecture
Mô hình phân lớp:
- **Presentation Layer**: Visualizer + CLI Wrapper.
- **Service Layer**: Resident Orchestrator Daemon (Main loop + Event Bus).
- **Worker Layer**: Dynamic Subagent Ephemeral Processes.

## 6. Resident Orchestrator Lifecycle
Tự động kích hoạt khi chạy lệnh `initialize-workspace`. Daemon duy trì kết nối trong suốt thời gian hoạt động của IDE và tự động phục hồi (restart) khi phát hiện sự cố crash đột ngột.

## 7. Dynamic Agent Team Planner
Phân tích đồ thị DAG tác vụ để xác định:
- Số lượng Subagents tối ưu cần spawn.
- Các vai trò (backend, frontend, qa) phù hợp với độ phức tạp của tác vụ.

## 8. Subagent Lifecycle
Subagent được tạo tự động khi có tác vụ sẵn sàng, thực thi độc lập và bị cưỡng chế thu hồi (idle cleanup) sau 5 phút nhàn rỗi.

## 9. Command Inbox & Routing
Command Inbox lắng nghe các lệnh từ nhiều nguồn (CLI, Webview) phi đồng bộ qua cơ chế IPC (Inter-Process Communication) cục bộ và xếp hàng xử lý.

## 10. Worker Pool Strategy
Giới hạn tối đa 6 Subagents chạy đồng thời để tránh quá tải tài nguyên máy chủ phát triển cục bộ.

## 11. Parallel Scheduling Strategy
Sử dụng ThreadPoolExecutor kết hợp subprocess để điều khiển các Subagents song song thực sự.

## 12. Runtime State Evolution
Kế thừa cấu trúc `.agents/state/` của FEAT-111, bổ sung tệp tin `daemon.json` ghi nhận tiến trình và định danh PID của service.

## 13. Event Bus Evolution
Chuyển đổi Event Bus từ ghi file sang chia sẻ sự kiện qua RAM/Named Pipes để tối ưu tốc độ và giảm ghi đè đĩa cứng.

## 14. Capability & Permission Model
Chặn đứng các quyền nguy hại (commit/push) của Subagents qua CapabilityEngine của FEAT-111.

## 15. Memory/RAG Integration
Tác nhân nền tự động đồng bộ hóa bộ nhớ dự án định kỳ mà không làm ảnh hưởng tới luồng phát triển chính của lập trình viên.

## 16. IDE & CLI Integration
CLI `aiwf` giao tiếp trực tiếp với Resident Orchestrator qua socket nội bộ.

## 17. Visualizer Changes
Thêm giao diện xem trạng thái sức khoẻ của Resident Service, kết nối WebSocket để cập nhật trực quan thời gian thực.

## 18. Fault Tolerance
Bọc mọi thao tác I/O trong vòng lặp thử lại ghi nguyên tử (mitigate Windows lock) đã thử nghiệm thành công tại `state_store.py`.

## 19. Recovery Strategy
Tự động phục hồi trạng thái DAG từ checkpoints lưu trong SQLite khi Resident Service khởi động lại sau sự cố.

## 20. Security Model
Giới hạn kết nối IPC chỉ chấp nhận kết nối nội bộ (localhost/Named Pipes), xác thực qua token định danh phiên sinh ngẫu nhiên.

## 21. Performance & Scalability
Thiết lập ngưỡng sử dụng CPU tối đa 80%, tự động giảm mức độ song song nếu tài nguyên máy chủ cạn kiệt.

## 22. Migration Strategy
Nâng cấp liền mạch từ phiên bản v6.10.0 của FEAT-111 lên v6.11.0 của FEAT-112, tự động di dời trạng thái cũ sang cấu trúc daemon mới.

## 23. Risks & Mitigations
- *Tranh chấp khóa tệp*: Đã được giảm thiểu bằng cơ chế retry ghi đè.
- *Rò rỉ bộ nhớ (memory leaks)*: Thu hồi toàn bộ tiến trình con khi phát hiện hết thời gian hoạt động.

## 24. Sprint Breakdown
- **Sprint 1**: Triển khai Core Daemon Service & Socket IPC.
- **Sprint 2**: Triển khai Dynamic Team Planner & Ephemeral Workers.
- **Sprint 3**: Tích hợp Visualizer WebSocket & CLI updates.

## 25. Work Package Breakdown
- WP1: Daemon Engine & CLI socket router.
- WP2: Dynamic Team Spawner.
- WP3: Visualizer dashboard monitoring.

## 26. Acceptance Criteria
- Resident Service sống sót sau IDE restart: **PASS**.
- Tiếp nhận lệnh phi đồng bộ thành công: **PASS**.
- Tự động thu hồi Subagent nhàn rỗi: **PASS**.

## 27. Success Metrics
- Concurrency đạt tối đa 6 tác nhân.
- Độ trễ phản hồi lệnh người dùng < 100ms.
