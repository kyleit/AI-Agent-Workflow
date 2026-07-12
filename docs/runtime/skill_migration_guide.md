# Skill Migration Guide — Runtime Foundation v1

Tài liệu hướng dẫn di chuyển các Skills hiện tại sang sử dụng Runtime API v1 thống nhất.

## 1. Loại bỏ Orchestration nội bộ
- **Trước đây**: Mỗi Skill tự khởi tạo một đối tượng điều phối hoặc quản trị tiến trình riêng độc lập.
- **Hiện tại**: Skill bắt buộc phải gọi Client SDK để đăng ký tác vụ và uỷ quyền cho Resident Orchestrator thực thi.

## 2. Các bước chuyển đổi
1. Đọc cấu hình quyền truy cập từ `.agents/state/`.
2. Thay thế các lệnh gọi file `.session.json` bằng cách đọc từ split-state store (`workflow.json`, `agents.json`).
3. Gửi sự kiện trạng thái qua `timeline.jsonl`.
