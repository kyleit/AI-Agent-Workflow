# Implementation Plan — FEAT-111 Hierarchical Multi-Agent Runtime

Triển khai cấu trúc chạy đa tác nhân phân cấp bao gồm bộ điều phối trung tâm và các tác nhân con độc lập cách ly tiến trình.

## User Review Required
> [!IMPORTANT]
> Cần Ba phê duyệt cấu trúc IPC và cách thức truyền thông tin giữa các tiến trình Subagents (Sử dụng Subprocess stdin/stdout hay HTTP/gRPC nội bộ).

## Proposed Changes

### Centralized Agent Runtime Component
Triển khai bộ lõi quản lý tiến trình chạy nền, phân rã công việc và điều phối.

#### [NEW] [hierarchical_runtime.py](file:///e:/AgentsProject/skills/workflow-runtime/scripts/hierarchical_runtime.py)
Bộ điều phối tiến trình và IPC để giao phó công việc cho Subagents.

#### [NEW] [worker_pool.py](file:///e:/AgentsProject/skills/workflow-runtime/scripts/worker_pool.py)
Quản lý các Worker process và cách ly môi trường thực thi.

### Visualizer Dashboard Component
Tích hợp giao diện quản trị tác nhân thời gian thực.

#### [MODIFY] [webview.html](file:///e:/AgentsProject/extensions/visualizer/resources/webview.html)
Bổ sung sơ đồ Agent Tree, danh sách Worker Processes, bảng locks và heartbeats.

## Verification Plan

### Automated Tests
- Chạy bộ unit tests mới cho Worker Pool và Scheduler:
  `pytest skills/workflow-runtime/tests/unit/test_hierarchical_runtime.py`

### Manual Verification
- Khởi chạy chương trình điều phối giả lập và quan sát sơ đồ cây tác nhân cập nhật trực tiếp trên giao diện Visualizer.
