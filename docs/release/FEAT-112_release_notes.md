# Release Notes — FEAT-112 Resident Orchestrator Service (v6.11.0)

Bản ghi nhận các nâng cấp cốt lõi trong phiên bản v6.11.0.

## 1. Nâng cấp cốt lõi
- **Resident Daemon Mode**: Tự động trú đóng ngầm thông qua `aiwf daemon`.
- **Command Inbox phi block**: Xếp hàng phi đồng bộ chỉ lệnh, phản hồi lệnh trạng thái < 100ms khi Subagent đang bận.
- **Dynamic Team Planner**: Co giãn số lượng Subagents dựa trên độ phức tạp của DAG và tự động giải phóng workers khi idle nhàn rỗi.
- **WebSocket Visualizer**: Đồng bộ hóa sơ đồ cây tác nhân động thời gian thực.
