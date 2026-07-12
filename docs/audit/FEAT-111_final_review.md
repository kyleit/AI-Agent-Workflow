# Independent Architecture Audit — FEAT-111 Hierarchical Multi-Agent Runtime

Báo cáo kiểm toán kiến trúc độc lập trước khi phát hành (Release).

## 1. Kết quả kiểm toán độc lập các cấu phần cốt lõi

### Main Orchestrator & isolated workers
- **Main Orchestrator**: Chạy tiến trình điều phối trung tâm thông qua `hierarchical_runtime.py`, lắng nghe hộp thư lệnh phi đồng bộ `command_inbox`.
- **Subagents**: Chạy trong môi trường cách ly (isolated workers) thông qua ThreadPoolExecutor và subprocesses giả lập. Các Subagent không tiếp nhận trực tiếp chỉ thị người dùng và chỉ tương tác thông qua Orchestrator.

### Quản lý trạng thái duy nhất (Single Source of Truth)
- Hệ thống duy trì trạng thái phiên chạy tập trung tại thư mục `.agents/state/` qua các tệp tin `agents.json`, `tasks.json`, `locks.json`, và `authorization.json`.
- Xác minh: Không phát sinh bất kỳ tệp tin `.agents/.session.json` nào. Nguồn trạng thái cũ đã bị xoá bỏ hoàn toàn.

### Vòng đời uỷ quyền thời gian thực (Authorization Lifecycle)
- Trạng thái uỷ quyền trong `authorization.json` được chuyển đổi chính xác sang trạng thái `expired` ngay sau khi phiên chạy tự động kết thúc hoặc thất bại.
- Thời gian đóng được ghi nhận tại `terminated_at`.

### Phân quyền (Capability Enforcement)
- `CapabilityEngine` chặn đứng các hành động ngoài phạm vi (commit, push, release) của Subagents dựa trên vai trò.

### Bộ lập lịch song song thực sự (Parallel Scheduler)
- Triển khai lập lịch song song thực sự bằng `ThreadPoolExecutor` của Python, nạp các tác vụ không phụ thuộc nhau (ví dụ: TASK-004 Backend và TASK-005 Frontend) vào thực thi đồng thời.
