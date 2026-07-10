---
artifact_type: fix-spec
issue_id: FIX-019
workflow: quick-fix
status: pending
---
# Fix Specification – Reset Usage Statistics on Init

## 1. Issue Description
Khi chạy lệnh khởi tạo lại session (`initialize-workflow` hoặc `init`), hệ thống lưu thống kê mã thông báo (token usage statistics) trong cơ sở dữ liệu `project_runtime.db` cho cuộc hội thoại hiện tại. Tuy nhiên, nếu lần chạy trước đó đã tích lũy một lượng lớn token (ví dụ: trước khi transcript bị cắt ngắn hoặc dọn dẹp), hàm `save_usage_to_dbs` trong `db.py` sẽ ngăn việc cập nhật thống kê mới nếu lượng token mới nhỏ hơn lượng token đã lưu trước đó (`new_total <= existing_total`). Điều này dẫn đến việc số liệu thống kê sử dụng trên giao diện Visualizer Dashboard bị kẹt ở giá trị cũ rất lớn và không thể cập nhật/thiết lập lại.

## 2. Scope
- **In Scope**:
  - Sửa đổi điều kiện lọc trong `save_usage_to_dbs` tại `.agents/skills/workflow-runtime/scripts/db.py` để bỏ qua kiểm tra `new_total <= existing_total` khi lệnh thực thi là `init` (khởi tạo lại).
- **Out of Scope**:
  - Không thay đổi các chức năng khác của cơ sở dữ liệu hoặc logic tính toán token trong `context.py`.
  - Không can thiệp vào cách hiển thị của Visualizer Webview.
