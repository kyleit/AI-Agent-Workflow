<!-- File path: docs/issues/FIX-012_auto_sync_conversation_id.md -->
---
artifact_type: fix-spec
issue_id: FIX-012
workflow: quick-fix
status: pending
---
# Fix Specification – Auto-Sync Conversation ID on Rollover

## 1. Issue Description
Khi người dùng thực hiện Compact và chuyển sang cuộc hội thoại mới (new conversation), tệp `.agents/.session.json` trên ổ cứng vẫn giữ nguyên `conversation_id` cũ. Điều này khiến thuật toán tính toán lượng token sử dụng không tìm thấy file transcript log tương ứng và rơi vào chế độ ước lượng dự phòng (Fallback Estimation) dựa trên số checkpoint. Ở checkpoint 10, kết quả ước lượng luôn là 85% (1.7M / 2M tokens), tạo ra các cảnh báo rollover giả và hiển thị sai lệch trên Dashboard Visualizer.

## 2. Scope
- **In Scope**:
  - Trích xuất tự động `conversationId` từ biến môi trường `ANTIGRAVITY_SOURCE_METADATA` trong hàm `update_context_health` của [workflow_runtime.py](file:///Volumes/Kyle/AgentsProject/skills/workflow-runtime/scripts/workflow_runtime.py).
  - Cập nhật và ghi đè giá trị này trực tiếp vào `session["conversation_id"]` để đồng bộ hóa kịp thời sang file `.session.json` bất cứ khi nào bất kỳ thao tác nào của runtime được gọi.
  - Sử dụng kiểu dữ liệu an toàn `cast(dict[str, object], ...)` để loại bỏ các cảnh báo cảnh báo lints từ `basedpyright`.
- **Out of Scope**:
  - Sửa đổi cơ chế tính toán token của `context.py`.
  - Thay đổi giao diện hiển thị webview của Visualizer extension.
