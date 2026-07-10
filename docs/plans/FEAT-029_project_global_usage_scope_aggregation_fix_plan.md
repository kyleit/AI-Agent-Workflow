<!-- File path: docs/plans/FEAT-029_project_global_usage_scope_aggregation_fix_plan.md -->

---
feature_id: FEAT-029
feature_name: Project/Global Usage Scope Aggregation Fix
status: reviewed
stage: planning
created_at: 2026-07-08
updated_at: 2026-07-08
previous_artifact: ../brainstorming/FEAT-029_project_global_usage_scope_aggregation_fix.md
next_artifact: ../designs/FEAT-029_project_global_usage_scope_aggregation_fix_blueprint.md
---

# FEAT-029: Project/Global Usage Scope Aggregation Fix

## Objective
- Cô lập phạm vi thống kê lượng token của Dự án (Project Usage) và Toàn cầu (Global Usage) để tránh hiển thị các số liệu khổng lồ giống nhau.
- Đảm bảo cơ chế đồng bộ hóa số liệu (usage sync) là idempotent (không cộng dồn hay trùng lặp bản ghi cho cùng một phiên làm việc).
- Dọn dẹp/Tính toán lại dữ liệu rác lịch sử bị phình to trong tệp cơ sở dữ liệu `project_runtime.db` và `global_runtime.db` để khôi phục tính chính xác của Dashboard hiển thị.

## Scope
### Included
- Refactor tệp [db.py](file:///e:/AgentsProject/.agents/skills/workflow-runtime/scripts/db.py):
  - Thay đổi hàm `get_project_summary()` để chấp nhận và lọc dữ liệu theo `project_id`.
  - Bổ sung cơ chế chống ghi đè/trùng lặp bản ghi (Idempotency) trong `save_usage_to_dbs()`.
  - Cập nhật hàm `normalize_database_records()` để chuẩn hóa/đặt lại dữ liệu lịch sử bị phình to về giá trị thực tế của phiên hội thoại (từ log transcript).
- Refactor [workflow_runtime.py](file:///e:/AgentsProject/.agents/skills/workflow-runtime/scripts/workflow_runtime.py):
  - Lấy `project_id` từ session/cấu hình dự án và truyền vào hàm truy vấn Project Summary.
  - Cập nhật lệnh CLI `usage diagnose` hiển thị chi tiết so sánh các nguồn dữ liệu.
- Viết các test đơn vị kiểm tra:
  - Khả năng lọc chính xác số liệu Project A vs Project B.
  - Tính idempotent khi đồng bộ liên tục.
  - Khả năng dọn dẹp các dòng rác dữ liệu cũ lịch sử.

### Excluded
- Không chỉnh sửa giao diện HTML/CSS của Visualizer. UI chỉ hoạt động như một passive renderer hiển thị dữ liệu JSON được gửi từ extension.
- Không thay đổi cấu trúc bảng `usage_records` (giữ nguyên schema SQLite để duy trì tương thích).

## Project Impact
- **Modules & Services**:
  - `workflow-runtime` CLI & Database helper: Sửa đổi cách truy vấn và dọn dẹp dữ liệu.
- **VS Code Extension**: Đọc dữ liệu JSON cập nhật và gửi lên Panel.
- **Database**: Cập nhật lại các dòng dữ liệu bị phình to trong `project_runtime.db` và `global_runtime.db`.

## Dependencies
- Phải có khả năng truy cập và sửa đổi các file database của dự án và global.
- Các unit tests của `test_runtime.py` phải ở trạng thái vượt qua trước khi sửa đổi.

## Risks
- **Risk**: Quá trình di trú/dọn dẹp dữ liệu lịch sử có thể mất thời gian nếu số lượng bản ghi cực lớn, hoặc lỗi nếu tệp tin log transcript của cuộc hội thoại cũ không còn tồn tại trên đĩa.
- **Mitigation**: Trong hàm dọn dẹp, nếu không tìm thấy tệp transcript, ta sẽ dựa trên thuật toán ước lượng an toàn (ví dụ: giới hạn số liệu về mức trung bình hợp lý hoặc dựa trên cơ sở dữ liệu lịch sử) chứ không crash tiến trình.

## Acceptance Criteria
- [ ] Chạy lệnh `aiwf usage sync` nhiều lần liên tiếp không làm tăng lượng Project/Global Usage (Idempotency).
- [ ] Số liệu của Project Usage chỉ tính toán trên các bản ghi thuộc `project_id` hiện tại, không cộng dồn bản ghi của các dự án khác trong database global.
- [ ] Các dòng dữ liệu lịch sử bị phình to (283M tokens) được đưa về giá trị thực tế sau khi chạy lệnh chuẩn hóa database.
- [ ] CLI `usage diagnose` chạy thành công và báo cáo chính xác sự so sánh dữ liệu.
- [ ] Toàn bộ unit tests mới và cũ đều PASS.

## Deliverables
- Bản cập nhật cho [db.py](file:///e:/AgentsProject/.agents/skills/workflow-runtime/scripts/db.py) và [workflow_runtime.py](file:///e:/AgentsProject/.agents/skills/workflow-runtime/scripts/workflow_runtime.py).
- Các unit tests bổ sung trong `test_runtime.py` để kiểm chứng logic lọc project, idempotency và dọn dẹp dữ liệu rác.

## Estimated Complexity
- **Medium**: Cần viết logic di trú/chuẩn hóa dữ liệu cẩn thận và thực hiện kiểm thử trên nhiều kịch bản đa dự án (multi-project).

## Recommended Blueprint Focus
- Tập trung thiết kế câu lệnh SQL truy vấn tổng hợp của Project lọc chính xác `project_id`.
- Thiết kế thuật toán chuẩn hóa dữ liệu cũ trong `db.py` bằng cách quét thư mục transcript (`~/.gemini/antigravity-ide/brain/<conversation-id>/.system_generated/logs/transcript.jsonl`) để phân tích lại số lượng token thực tế và cập nhật lại bản ghi cũ tương ứng.

## Recommended Next Skill
/blueprint
