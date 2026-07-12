# Technical Design Blueprint — FEAT-114: Resident Orchestrator CLI

## 1. Executive Summary
Bản thiết kế chi tiết tích hợp `aiwf orchestrator` CLI vào AIWF Platform.

## 2. CLI Command Specifications

### 2.1 start / stop / restart
- `start`: 
  - Khởi động daemon thông qua việc sinh tiến trình nền chạy `hierarchical_runtime.py --daemon` (nếu chưa chạy).
  - Tự động tạo file `.agents/state/daemon.json` ghi PID.
- `stop`:
  - Đọc PID từ `daemon.json`. Nếu tiến trình tồn tại, dùng `psutil` hoặc `os.kill` để dừng tiến trình daemon.
  - Đồng thời dọn dẹp file `daemon.json` và giải phóng khóa.
- `restart`:
  - Thực thi tuần tự `stop` và `start`.

### 2.2 status
- Đọc thông tin từ:
  - `.agents/state/daemon.json` -> Trạng thái hoạt động (RUNNING / STOPPED), PID, Started At.
  - `.agents/state/manager.json` -> Trạng thái Watchdog/Runtime Manager (RUNNING / STOPPED).
  - `.agents/state/context.json` -> Phiên bản API, Workspace, Attach Mode, Resident Mode.
- Output Format:
  ```text
  Resident Orchestrator

  Status: [RUNNING/STOPPED]
  PID: [PID]
  Workspace: [Workspace Name]
  Resident: true
  Heartbeat: [duration] ago
  Runtime API: v1
  Runtime Manager: [RUNNING/STOPPED]
  ```

### 2.3 health
- Đo thông tin tài nguyên máy cục bộ qua `psutil` (CPU, Memory).
- Đếm số lượng từ trạng thái:
  - Active Workflows (số lượng item trong `active-work-items.json` hoặc `workflow.json`).
  - Active Agents (số lượng agent bận/rảnh trong `agents.json`).
  - Queue Length (số lượng inbox cmd trong `queue.json`).
  - Locks (đếm mục trong `locks.json`).
- Kết xuất dưới dạng bản tin trạng thái sức khỏe tổng quan.

### 2.4 attach / detach
- `attach`: Ghi nhận cờ `attach_mode: true` vào cấu hình phiên hoạt động trong `context.json`.
- `detach`: Ghi nhận cờ `attach_mode: false` vào cấu hình phiên hoạt động.

### 2.5 agents / workflows / graph / queue / locks / timeline
- Liệt kê trực tiếp nội dung tương ứng của các file trạng thái dưới định dạng văn bản trực quan hoặc JSON tùy chọn.
  - `agents`: đọc `agents.json`. Hiển thị: Agent ID, Type, Parent, Current Task, Status, Started, CPU, Memory.
  - `workflows`: đọc `active-work-items.json` và `workflow.json`. Hiển thị: Work Item, Workflow ID, Parent Workflow, Status, Checkpoint, Assigned Agents, Progress.
  - `graph`: đọc `task_graph.json` và hiển thị cấu trúc DAG hoặc JSON.
  - `queue`: đọc `queue.json` hoặc hàng đợi tác vụ.
  - `locks`: đọc `locks.json` hiển thị các khóa đang giữ bởi các tác nhân.
  - `timeline`: đọc `timeline.jsonl` hiển thị chuỗi sự kiện.

### 2.6 metrics
- Đọc lịch sử chạy và hiệu suất từ `usage.json` và `timeline.jsonl`.
- Tính toán: Throughput, Average Task Duration, Retry Count, Recovery Count, Parallelism, Peak Concurrency, Total Agents Spawned, Total Workflows.

### 2.7 logs
- Đọc file logs vận hành. Hỗ trợ các bộ lọc `--level`, `--agent`, `--workflow`, `--work-item`, `--orchestrator`, `--runtime`.

## 3. Initialize Workspace Integration
Cập nhật `do_init` trong `workflow_runtime.py`:
- Sau khi khởi tạo xong session, tự động gọi hàm `ensure_daemon_running()` và in ra startup summary:
  ```text
  Resident Orchestrator: [RUNNING/STOPPED]
  Mode: [Attached/Detached]
  PID: [PID]
  Heartbeat: [OK/FAIL]
  Runtime Manager: [RUNNING/STOPPED]
  ```

## 4. Visualizer Integration
Visualizer sử dụng lệnh `aiwf orchestrator` để lấy dữ liệu thay vì tự ý phân tích file thô.

```text
Recommendation:
BLUEPRINT APPROVED
```
