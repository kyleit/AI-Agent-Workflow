# Execution Plan — FEAT-110 Multi-Agent Operations Dashboard and Recovery Center

## 1. Scope and Goals
Triển khai Bảng điều khiển tích hợp trên extension Visualizer Companion hỗ trợ giám sát và khôi phục tiến trình đa tác nhân Orchestrator V2.

## 2. Technical Steps
1. **CLI Engine Extension**:
   - Tích hợp thêm subcommand `orchestrator action` vào `workflow_runtime.py` với các tham số `--action`, `--task-id`, `--lock-id`.
   - Viết các phương thức cập nhật nguyên tử tệp tin trạng thái dưới `.agents/state/orchestrator/`.
2. **VS Code Extension (Backend/IPC)**:
   - Thêm bộ lắng nghe thay đổi đĩa (FileSystemWatcher) trên các tệp tin trong `.agents/state/orchestrator/`.
   - Khai báo trình nhận tin nhắn `GET_ORCHESTRATOR_DATA` để trả về toàn bộ dữ liệu trạng thái.
   - Định nghĩa trình chuyển giao lệnh `ORCHESTRATOR_RECOVERY_ACTION` xuống CLI.
3. **Companion Webview UI**:
   - Thiết lập giao diện tab **Orchestrator** với các panel: Run Overview, Task Dependency Graph, Agent Monitoring, Live Execution Timeline, Active Locks, Checkpoints.
   - Sử dụng các lớp CSS neon glassmorphism thống nhất với hệ thống visualizer hiện tại.
4. **Verification**:
   - Viết test suite kiểm thử đơn vị bằng pytest.
   - Xây dựng tệp kịch bản thực tế 25 tác vụ song song để tạo bằng chứng kiểm thử đầu cuối.
