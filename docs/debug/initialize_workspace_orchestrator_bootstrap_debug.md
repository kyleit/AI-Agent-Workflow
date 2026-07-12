# Debug Log — initialize-workspace Resident Orchestrator Bootstrap

Báo cáo phân tích và chẩn đoán sự cố khởi tạo/kết nối Trình điều phối trú đóng trong quá trình chạy `initialize-workspace`.

## 1. Nhật ký chẩn đoán lỗi
- **Sự cố**: Sau khi chạy `initialize-workspace`, trạng thái của Resident Orchestrator không được đăng ký đầy đủ theo các cấu trúc chuẩn của Runtime API v1 (`orchestrator.json`, `runtime-manager.json`, v.v.). Trình điều phối chạy nhưng không tự động ghi nhận thông tin liveness của manager và heartbeat.
- **Nguyên nhân**:
  1. `do_init` chỉ gọi lệnh khởi động daemon thông thường mà chưa thực thi đăng ký các thông tin trạng thái đầy đủ.
  2. Thiếu cơ chế phân biệt trạng thái khởi chạy lần đầu (`started`) và lần thứ hai (`attached`).
  3. Cấu trúc tệp `agents.json` toàn cục chưa phản ánh đúng định dạng yêu cầu của Phase 3.

## 2. Các điểm khắc phục đề xuất
- Cập nhật luồng `ensure_daemon_running` để lưu lại kết quả start-or-attach và ghi trạng thái chính xác.
- Bổ sung logic ghi ghi tệp tin trạng thái chuẩn (`runtime.json`, `orchestrator.json`, `runtime-manager.json`, `agents.json`, `workflows.json`, `timeline.jsonl`) trực tiếp trong vòng lặp của `HierarchicalRuntime` để bảo đảm cập nhật heartbeat liên tục.
