# AIWF Runtime API v1 Specification

Định nghĩa chính thức cho các giao diện lập trình thuộc lớp nền tảng Runtime Foundation v1.

## 1. Resident Orchestrator API
- **Mục đích**: Cung cấp giao diện gửi lệnh phát triển và nhận kết quả điều phối từ daemon.
- **Mẫu hợp đồng**:
  - Gửi lệnh: `OrchestratorClient.send_command(cmd: str) -> bool`
  - Nhận trạng thái DAG: `OrchestratorClient.get_tasks() -> dict`

## 2. Event Bus API
- **Mục đích**: Gửi và nhận các sự kiện thay đổi trạng thái chéo tiến trình.
- **Mẫu hợp đồng**:
  - Pub: `EventBus.publish(event_type: str, payload: dict)`
  - Sub: `EventBus.subscribe(event_type: str, callback: callable)`

## 3. Lock API
- **Mục đích**: Ngăn ngừa xung đột ghi đĩa đồng thời.
- **Mẫu hợp đồng**:
  - Acquire lock: `LockManager.acquire(resource_path: str, agent_id: str) -> bool`
  - Release lock: `LockManager.release(resource_path: str, agent_id: str)`
