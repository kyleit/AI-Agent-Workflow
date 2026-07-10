<!-- File path: docs/issues/FIX-011_prevent_session_drift_on_memory_sync.md -->
---
artifact_type: fix-spec
issue_id: FIX-011
workflow: quick-fix
status: pending
---
# Fix Specification – Prevent Session Drift on Memory Sync

## 1. Issue Description
Khi chạy lệnh cập nhật bộ nhớ (`cli.py update`), quy trình này tự động gọi hàm `session_start` và `session_complete` với `checkpoint=2` để cập nhật trạng thái tiến trình của kỹ năng `project-memory-update`. Tuy nhiên, nếu lệnh này chạy ngầm hoặc chạy phụ trợ khi người dùng đang ở một bước/checkpoint khác có mức cao hơn (ví dụ: đang code ở checkpoint 5), các hàm này vẫn ghi đè trực tiếp checkpoint hiện tại về `2`, khiến công cụ hiển thị (visualizer) bị nhảy lùi tiến trình về bước 2, rồi sau đó mới nhảy tiến trở lại bước hiện tại khi các quy trình khác hoạt động. Việc nhảy bước này gây khó chịu và không phản ánh đúng tiến trình thực tế của workflow.

## 2. Scope
- **In Scope**:
  - Chỉnh sửa các hàm hỗ trợ cập nhật phiên làm việc trong `runtime/scripts/project_memory/common.py` (`session_start`, `session_step`, `session_complete`, `session_fail`).
  - Kiểm tra nếu `current_skill` hiện tại trong session khác với skill được gọi (`project-memory-update` hoặc `project-memory-bootstrap`), thì bỏ quan việc ghi đè các trường điều hướng quy trình (checkpoint, status, current_skill, current_command, current_step, suggested_next_skill, suggested_next_command).
  - Vẫn cho phép cập nhật thông tin về sức khỏe ngữ cảnh (context health/memory/RAG/Git) thông qua hàm `update_context_health` trong `session_complete` để đảm bảo dữ liệu mới nhất được đồng bộ.
- **Out of Scope**:
  - Không thay đổi bất kỳ logic cốt lõi nào của CLI cập nhật bộ nhớ (`cli.py`, `update.py`).
  - Không thay đổi cấu trúc dữ liệu của tệp phiên làm việc `.agents/.session.json`.
