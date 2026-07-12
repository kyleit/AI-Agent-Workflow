# Brainstorming — FEAT-114: Resident Orchestrator CLI

## 1. Executive Summary
Đề xuất thiết kế và tích hợp bộ lệnh điều khiển Trình điều phối trú đóng (Resident Orchestrator CLI) như một nhóm lệnh cấp một (`aiwf orchestrator`) trong giao diện dòng lệnh AIWF CLI. Nhóm lệnh này sẽ tái sử dụng và kết nối trực tiếp với Runtime API v1 hiện có để cung cấp đầy đủ khả năng quản lý tiến trình, giám sát sức khoẻ, truy vấn tác vụ/tài nguyên và phân tích nhật ký vận hành.

## 2. Background & Current Limitations

### Background
Hệ thống Runtime Foundation đã hoàn thiện các tính năng cốt lõi bao gồm:
- FEAT-111: Hierarchical Multi-Agent Runtime (Lập lịch phân cấp)
- FEAT-112: Resident Orchestrator Service (Dịch vụ chạy ngầm trú đóng)
- FEAT-113: Resident Runtime Manager (Trình giám sát tự chữa lành Watchdog)
- Runtime API v1 (Giao diện lập trình API v1)

### Current Limitations
- **Thiếu giao diện dòng lệnh**: CLI `aiwf` hiện tại chưa hỗ trợ điều khiển hay xem trạng thái của Resident Orchestrator một cách chính thống. Các lệnh như `aiwf orchestrator` chưa được định nghĩa hoặc phơi bày trong menu trợ giúp (`--help`).
- **Giao diện Visualizer chưa đồng bộ hoàn toàn**: Visualizer cần một điểm truy cập thông tin vận hành thống nhất qua CLI để hiển thị trạng thái động của hệ thống thay vì phải đọc trực tiếp các file JSON thô trên đĩa, từ đó tránh trùng lặp mã nguồn logic.
- **Tích hợp khởi tạo chưa khép kín**: Sau khi chạy `initialize-workspace`, chưa có luồng tự động kiểm tra/khởi động/kết nối (attach) Resident Orchestrator và hiển thị bảng thông tin tóm tắt khởi động.

## 3. Business Value
- Tăng cường trải nghiệm nhà phát triển và đơn giản hoá việc vận hành hệ thống AIWF.
- Hỗ trợ tốt hơn cho việc tích hợp vào các kịch bản CI/CD, tự động hoá kiểm thử và giám sát không giám sát.
- Đảm bảo tính nhất quán dữ liệu giữa CLI, Visualizer Extension và Runtime Services.

## 4. Functional Requirements

### Lifecyle Commands (Quản lý Vòng đời)
- `aiwf orchestrator start`: Khởi chạy Resident Orchestrator ngầm (daemon) nếu chưa chạy.
- `aiwf orchestrator stop`: Dừng Resident Orchestrator một cách an toàn.
- `aiwf orchestrator restart`: Tắt và khởi chạy lại dịch vụ Resident Orchestrator.
- `aiwf orchestrator attach`: Đăng ký session làm việc hiện hành vào Orchestrator đang hoạt động.
- `aiwf orchestrator detach`: Hủy đăng ký session khỏi Orchestrator đang hoạt động mà không tắt dịch vụ daemon.

### Monitoring & Observability Commands (Giám sát và Quan sát)
- `aiwf orchestrator status`: Hiển thị thông tin tổng quan (Status, PID, Workspace, Uptime, API Version, Watchdog status, v.v.).
- `aiwf orchestrator health`: Kiểm tra tài nguyên (CPU, Memory, Active Workflows/Agents, Event Bus status, Scheduler, Worker Pool).
- `aiwf orchestrator agents`: Liệt kê thông tin chi tiết các Agents đang hoạt động (ID, Type, Parent, Status, CPU, RAM, Start time).
- `aiwf orchestrator workflows`: Hiển thị thông tin danh sách workflows (Work Item ID, Status, Checkpoint, Progress, Assigned Agents).
- `aiwf orchestrator graph`: Hiển thị đồ thị định hướng không chu trình (DAG) của các tác vụ dưới dạng JSON hoặc biểu diễn cây trực quan.
- `aiwf orchestrator queue`: Hiển thị chi tiết hàng đợi tác vụ (pending, running, blocked, completed).
- `aiwf orchestrator locks`: Hiển thị thông tin các tài nguyên đang bị khóa ghi chéo tiến trình.
- `aiwf orchestrator timeline`: Hiển thị dòng sự kiện lịch sử vận hành theo thứ tự thời gian.
- `aiwf orchestrator metrics`: Báo cáo chỉ số hiệu suất (throughput, avg task duration, retry/recovery counter, concurrency peak).
- `aiwf orchestrator logs`: Truy xuất và lọc logs theo các chiều: level, agent, workflow, work-item, orchestrator, runtime.

### Workspace Initialization Integration
Tự động kích hoạt sau khi `aiwf init` chạy:
- Khởi động Orchestrator nếu chưa chạy.
- Kết nối (Attach) nếu đang chạy.
- In ra startup summary.

## 5. Non-functional Requirements
- **Performance**: Phản hồi lệnh người dùng < 200ms bằng cách tối ưu hoá đọc các tệp trạng thái cache tại `.agents/state/`.
- **Security**: Tuân thủ triệt để mô hình sandbox, không thực hiện các lệnh nguy hại ngoài localhost.
- **Dry-run & Clean-up**: Mọi tiến trình con được sinh ra phải được thu hồi an toàn khi CLI dừng hoặc gặp sự cố.

## 6. Risks & Mitigations
- **Windows File Lock**: Xung đột tranh chấp truy cập đồng thời vào `daemon.json` hoặc `manager.json` giữa CLI và Watchdog.
  - *Giảm thiểu*: Sử dụng cơ chế ghi nguyên tử có sẵn trong `state_store.py` / `session.py` (vòng lặp thử lại tối đa 10 lần).

## 7. Migration & Visualizer Integration
- Tích hợp 100% các lệnh mới vào CLI wrapper `aiwf.ps1` và `aiwf` (bash).
- Giao diện Visualizer Webview sẽ đồng bộ với dữ liệu API thu thập bởi CLI để cập nhật biểu đồ động.

```text
Recommendation:
READY FOR PLANNING
```
