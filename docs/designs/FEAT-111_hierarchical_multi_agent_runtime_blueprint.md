# Technical Blueprint — FEAT-111 Hierarchical Multi-Agent Runtime

Chi tiết kiến trúc và đặc tả tích hợp cho hệ thống đa tác nhân phân cấp.

## 1. IPC & Communication Protocol
Orchestrator giao tiếp với Subagents bằng giao thức JSON-RPC qua `sys.stdin`/`sys.stdout` của tiến trình con:
* **Request Format**:
  ```json
  {"jsonrpc": "2.0", "method": "execute_task", "params": {"task_id": "TASK-001", "code": "..."}, "id": 1}
  ```
* **Response Format**:
  ```json
  {"jsonrpc": "2.0", "result": {"status": "success", "output": "..."}, "id": 1}
  ```

## 2. Process Isolation & Resource Limits
- Mỗi Subagent chạy bằng lệnh `python skills/workflow-runtime/scripts/subagent_worker.py` với biến môi trường tách biệt hoàn toàn.
- Sử dụng thư viện `psutil` để giám sát CPU/Memory tiêu thụ của tiến trình con.

## 3. Dynamic Task Graph (DAG) Engine
- Đồ thị tác vụ được phân tích dựa trên phụ thuộc (dependencies) khai báo.
- Scheduler thực thi song song bất kỳ cụm tác vụ nào không có phụ thuộc lẫn nhau bằng cách đẩy vào ThreadPoolExecutor quản lý hàng đợi.

## 4. Visualizer Panel Details
Bổ sung cấu trúc hiển thị trên tab **Orchestrator**:
- **Agent Tree**: Vẽ đồ thị dạng cây biểu diễn liên kết cha-con giữa Orchestrator và các Subagents đang hoạt động.
- **Locks & Heartbeats Grid**: Bảng liệt kê các file đang khóa và dấu hiệu sống (heartbeat timestamps) của từng Worker process.

## 5. Platform Runtime Foundation Promotion
- FEAT-111 được đóng gói thành một lớp runtime dùng chung cho toàn bộ các skills trong hệ thống.
- Các skill như `implementation`, `debug`, `verify`, `release`, `VIR` và `VAR` sẽ ủy thác và gọi thực thi thông qua Hierarchical Multi-Agent Runtime thay vì tự xây dựng cơ chế điều phối riêng lẻ.

## 6. Extended Authorization Lifecycle
- Mỗi phiên ủy quyền sẽ chứa thông tin vòng đời đầy đủ bao gồm: `authorization_id`, `authorization_scope`, `authorization_status` ("active" hoặc "expired"), `created_at`, `expires_when` và `terminated_at`.
- Khi luồng thực thi đạt trạng thái hoàn thành hoặc thất bại (terminal state), `authorization_status` sẽ chuyển sang `"expired"` và ghi nhận thời điểm đóng ở `terminated_at`. Mọi lượt chạy tiếp theo bắt buộc phải có mã ủy quyền mới.
