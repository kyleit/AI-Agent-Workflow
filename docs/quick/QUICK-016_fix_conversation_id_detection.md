<!-- File path: docs/quick/QUICK-016_fix_conversation_id_detection.md -->
---
artifact_type: quick-feature-spec
feature_id: QUICK-016
workflow: quick-feature
status: pending
---
# Mini Feature Specification – Fix Conversation ID Detection and Context Usage Reset

## 1. Feature Goal
Khắc phục hành vi của `initialize-workflow` và `resume-workflow` sao cho khi một cuộc trò chuyện IDE/chat mới bắt đầu, runtime sẽ phát hiện sự thay đổi của conversation ID và tự động cập nhật lại `.agents/.session.json` trước khi tính toán context usage, từ đó đảm bảo ước lượng token được tính toán trên tệp transcript chính xác.

## 2. Scope

- **In Scope**:
  - Tự động phát hiện conversation ID hoạt động hiện tại (qua biến môi trường `ANTIGRAVITY_SOURCE_METADATA`).
  - Khi bắt đầu `initialize-workflow` hoặc `resume-workflow`:
    - Đọc trạng thái từ `session` (hoặc Split State files).
    - So sánh `conversation_id` hiện tại và trong trạng thái đã lưu.
    - Nếu thay đổi: cập nhật `conversation_id`, đặt lại và tính toán lại `context_usage` dựa trên tệp transcript của cuộc trò chuyện mới, thêm log chuyển đổi cuộc trò chuyện.
    - Bảo toàn toàn bộ các trường trạng thái workflow khác (`checkpoint`, `status`, `current_skill`, `current_command`, `current_step`, `work_item`, `git`, `version`, `memory`, `rag`, `suggested_next_skill`, `suggested_next_command`).
  - Sử dụng cơ chế ghi tệp nguyên tử (atomic write) thông qua tệp `.tmp` và đổi tên.
  - Xử lý an toàn khi tệp transcript chưa tồn tại hoặc bị thiếu (fallback về 0/unknown và ghi warning).
  - Cập nhật tài liệu Skill liên quan.
  - Bổ sung bộ unit tests đầy đủ.

- **Out of Scope**:
  - Không thay đổi thiết kế lưu trữ của Split State (Pure Split State vẫn được duy trì).
  - Không tự động dọn dẹp hoặc xóa bỏ lịch sử hội thoại cũ ngoài việc cập nhật trạng thái hoạt động.
