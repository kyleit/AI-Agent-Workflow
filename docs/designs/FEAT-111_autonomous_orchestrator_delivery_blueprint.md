# Technical Blueprint — FEAT-111 Autonomous Orchestrator Delivery

## 1. Bounded Authorization Payload (Model B)
Cơ chế uỷ quyền lưu trữ tại `.agents/state/authorization.json` chứa các khoá:
- `authorization_id`: Mã định danh uỷ quyền duy nhất.
- `mode`: Bắt buộc là `autonomous_delivery`.
- `work_item_id`: Bằng chứng mã công việc (ví dụ: `FEAT-111`).
- `allow_file_create`/`allow_file_modify`: Cho phép sửa đổi tệp tin trong scope.
- `allow_commit`/`allow_push`/`allow_release`: Luôn là `false`.

## 2. Phân rã tác vụ tự động (Automatic DAG)
Đồ thị 25 tác vụ phát triển tự động kết nối qua:
- `TASK-001` đến `TASK-005`: Discovery & Planning.
- `TASK-006` đến `TASK-015`: Design & Implementation (Hỗ trợ chạy song song nhóm backend/frontend).
- `TASK-016` đến `TASK-020`: Unit/Integration/E2E Testing & Debugging.
- `TASK-021` đến `TASK-025`: Compliance Verification & Final Review Gate.

## 3. Khôi phục & Ghi nhận Defects tự động
- Khi phát hiện lỗi hoặc thiếu chữ ký xác thực (Evidence check fail), bộ điều phối tự động tạo một defect record tại `.agents/state/orchestrator/defects.json`.
- Tự động gọi Debug Agent thực hiện sửa đổi trong allowed scope và kích hoạt thử lại (retry) tối đa 3 lần mà không làm gián đoạn luồng hoặc hỏi người dùng.
