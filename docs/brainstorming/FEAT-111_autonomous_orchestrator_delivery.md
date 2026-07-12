# Brainstorming — FEAT-111 Autonomous Orchestrator Delivery

## 1. Problem Statement
Trong các đợt phát triển phức tạp, việc dừng lại liên tục để hỏi ý kiến người dùng ("Continue?", "Run tests?", "Verify?") làm giảm tốc độ của luồng làm việc tự động (multi-agent loop). Người dùng cần một chế độ giao phó toàn quyền (autonomous_delivery) trong một phạm vi giới hạn (bounded work item).

## 2. Requirements & UX
- Chế độ thực thi:
  - `interactive`: Giữ nguyên mô hình Model A (Hỏi phê duyệt từng bước).
  - `autonomous_delivery`: Kích hoạt Model B (Uỷ quyền theo phạm vi).
- Phạm vi uỷ quyền:
  - Được phép: Viết artifact, sửa đổi code trong scope, chạy pytest, chạy debug.
  - Bị chặn: Git commits, Git push, Tagging, Release.
- Người dùng chỉ được hỏi xác nhận đúng 2 lần: Lúc bắt đầu cấp quyền và lúc hoàn thành ở Final Review Gate.
