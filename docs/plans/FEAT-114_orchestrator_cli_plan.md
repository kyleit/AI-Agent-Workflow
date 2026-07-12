# Execution Plan — FEAT-114: Resident Orchestrator CLI

## 1. Executive Summary
Kế hoạch triển khai tích hợp nhóm lệnh `orchestrator` vào bộ công cụ giao diện dòng lệnh `aiwf` nhằm cung cấp giao diện quản lý đầy đủ cho Resident Orchestrator. 

## 2. Objectives
- Tích hợp nhóm lệnh `orchestrator` làm CLI chính thức.
- Tái sử dụng Runtime API v1 hiện hành để truy vấn trạng thái tiến trình, agents, workflows, graph, logs và metrics.
- Cập nhật các bộ CLI wrappers (`bootstrap.ps1`, `bootstrap.sh`) để phơi bày và định tuyến lệnh chính xác.
- Đảm bảo cơ chế tự động chạy/attach sau khi `initialize-workspace` hoàn tất.
- Tránh trùng lặp logic trạng thái giữa Visualizer và CLI.

## 3. Scope
- **CLI Command parser in Python**: Cập nhật `workflow_runtime.py` với các lệnh, tham số và phân tích kết quả của `orchestrator`.
- **CLI wrappers**: Cập nhật `bootstrap.ps1` và `bootstrap.sh`.
- **Automated Tests**: Viết kiểm thử tự động cho tất cả các nhóm lệnh `orchestrator`.
- **Verification & Debug docs**: Viết báo cáo thẩm định và phân tích chẩn đoán lỗi.

## 4. Proposed Architecture & CLI mapping
CLI `aiwf orchestrator <subcommand>` sẽ định tuyến trực tiếp vào hàm `do_orchestrator` trong `workflow_runtime.py`. Dữ liệu sẽ được truy vấn và định dạng từ cấu trúc thư mục trạng thái `.agents/state/`.

Mỗi lệnh sẽ đọc thông tin tương ứng:
- `start`: Khởi chạy daemon.
- `stop`: Ghi trạng thái `stopped` hoặc kill tiến trình daemon/watchdog.
- `restart`: Thực thi dừng và chạy lại daemon.
- `status`: Xem `daemon.json`, `manager.json`, `context.json`.
- `health`: Đọc CPU/RAM qua `psutil` (giống Watchdog) và thống kê nhanh trạng thái queue/agents.
- `attach` / `detach`: Cập nhật cấu hình attach session trong `context.json`.
- `agents`: Xem `agents.json`.
- `workflows`: Xem `workflow.json` và `active-work-items.json`.
- `graph`: Xem `task_graph.json`.
- `queue`: Xem `queue.json` hoặc trạng thái tasks.
- `locks`: Xem `locks.json`.
- `timeline`: Xem `timeline.jsonl`.
- `metrics`: Đọc thông tin thống kê từ `usage.json` / `timeline.jsonl`.
- `logs`: Đọc và lọc logs từ thư mục `.agents/runtime/` hoặc `.agents/state/` logs.

## 5. Work Packages
- **WP1: CLI Parser & Wrappers (Coded)**: Thiết lập bộ định tuyến CLI hoàn chỉnh.
- **WP2: Orchestrator Subcommands Implementation**: Hoàn thiện logic xử lý dữ liệu và in ra giao diện tiêu chuẩn cho 16 commands.
- **WP3: Initialize Integration**: Cập nhật `do_init` để tự động start/attach.
- **WP4: Automated Testing**: Thiết lập bộ suite kiểm thử hoàn chỉnh cho mọi command.

## 6. Verification Plan
- Chạy `aiwf orchestrator --help` để xác minh phơi bày thành công.
- Thực thi tất cả 16 commands thủ công và tự động.
- Kiểm thử giả lập trạng thái daemon sập/chạy để xác minh attach/start hoạt động đúng.

```text
Recommendation:
READY FOR ARCHITECTURE/DESIGN
```
