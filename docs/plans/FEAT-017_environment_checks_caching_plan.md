<!-- File path: docs/plans/FEAT-017_environment_checks_caching_plan.md -->

---
feature_id: FEAT-017
feature_name: Environment Checks Caching and Option Selection Policy
status: proposed
stage: planning
created_at: 2026-07-07
updated_at: 2026-07-07
previous_artifact: none
next_artifact: ../designs/FEAT-017_environment_checks_caching_blueprint.md
---

# Implementation Plan - Environment Checks Caching and Option Selection Policy (FEAT-017)

## 1. Goal & Context
Tối ưu hóa thời gian chạy và lượng token tiêu thụ bằng cách lưu bộ nhớ đệm (caching) kết quả kiểm tra công cụ môi trường tại `.agents/runtime/env_cache.json` và chuẩn hóa việc bắt buộc sử dụng công cụ `ask_question` khi brainstorm các phương án cho người dùng.


## 2. Proposed Changes
- **AI_RULES.md**:
  - Thêm phần **17. Environment Tools Checking and Caching Policy** để chuẩn hóa chính sách cache.
  - Thêm phần **18. Option Selection and Decision Making Policy** để bắt buộc sử dụng `ask_question` khi có các danh sách lựa chọn.
- **initialize-workflow SKILL.md**:
  - Cập nhật Step 9 để kiểm tra, đọc từ cache `.agents/runtime/env_cache.json` nếu thời gian chưa quá 24h và ghi đè cache khi kiểm tra đầy đủ.
- **env_cache.json**:
  - Tạo mới tệp lưu trạng thái cache môi trường hiện tại.

## 3. Verification Plan
- Chạy thử quy trình khởi tạo để đảm bảo cấu hình cache hợp lệ.
- Kiểm tra tính tuân thủ của các file sửa đổi.
