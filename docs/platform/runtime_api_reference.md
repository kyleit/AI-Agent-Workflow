# AIWF Runtime API v1 Reference

Tài liệu tham chiếu chi tiết các API giao tiếp của Runtime.

## 1. Giao diện điều phối (Orchestrator RPC)
- **Phương thức**: `submit_command`
  - *Payload*: `{"command": "tên_lệnh", "args": {}}`
  - *Kết quả*: `{"status": "success | error"}`

## 2. Giao diện sự kiện (Event Bus JSON)
- **Cấu trúc sự kiện**:
  - `event_type`: Loại sự kiện (ví dụ: `task_started`).
  - `timestamp`: Định dạng ISO 8601.
  - `payload`: Thông số đi kèm.
